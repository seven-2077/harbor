#!/usr/bin/env python3
"""解析静态 GTFS，输出本原型用的整洁 JSON。

默认读取 data/raw/bart_gtfs.zip（官方 BART 小体量全量包），
截取地铁/轨道线路（route_type 为 0/1/2）以及一个服务日的班次与到站时刻。

只使用 Python 3 标准库，可复现。稍后若 Atlas 提供样本，可：
    python3 scripts/prepare.py --gtfs /path/to/atlas/sample.zip
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import statistics
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GTFS = ROOT / "data" / "raw" / "bart_gtfs.zip"
DEFAULT_OUT = ROOT / "data" / "processed"
APP_DATA = ROOT / "app" / "data"

# GTFS route_type: 0 tram, 1 subway, 2 rail
RAIL_TYPES = {"0", "1", "2"}

# 优先选用的样品服务日：本任务当天（2026-11-11，周三），若该日无服务再自动另选。
PREFERRED_DATE = date(2026, 11, 11)


def read_gtfs_table(source: Path, name: str) -> list[dict]:
    """从 zip 或已解压目录读取一张 GTFS 表。"""
    if source.is_dir():
        path = source / name
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8-sig")
    elif zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as zf:
            # 允许 zip 根目录或单层子目录
            candidates = [i for i in zf.namelist() if i.endswith(name) and not i.endswith("/")]
            if not candidates:
                return []
            # 优先较短路径（根目录下的文件）
            candidates.sort(key=lambda s: (s.count("/"), len(s)))
            raw = zf.read(candidates[0])
        text = raw.decode("utf-8-sig")
    else:
        raise FileNotFoundError(f"找不到 GTFS zip 或目录: {source}")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        rows.append({(k or "").strip(): (v or "").strip() for k, v in row.items()})
    return rows


def parse_yyyymmdd(s: str) -> date:
    return datetime.strptime(s, "%Y%m%d").date()


def parse_gtfs_time(s: str) -> int | None:
    """返回自当天 00:00 起的分钟数，允许 >= 24:00。"""
    if not s:
        return None
    parts = s.split(":")
    if len(parts) < 2:
        return None
    h, m = int(parts[0]), int(parts[1])
    sec = int(parts[2]) if len(parts) > 2 else 0
    return h * 60 + m + (1 if sec >= 30 else 0)


def format_hhmm(minutes: int | None) -> str:
    if minutes is None:
        return ""
    h, m = divmod(int(minutes), 60)
    return f"{h:02d}:{m:02d}"


def active_service_ids(calendar: list[dict], calendar_dates: list[dict], day: date) -> set[str]:
    weekday = day.weekday()  # Mon=0
    keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    field = keys[weekday]
    day_s = day.strftime("%Y%m%d")
    active: set[str] = set()
    for row in calendar:
        sid = row["service_id"]
        start = parse_yyyymmdd(row["start_date"])
        end = parse_yyyymmdd(row["end_date"])
        if start <= day <= end and row.get(field) == "1":
            active.add(sid)
    for row in calendar_dates:
        if row.get("date") != day_s:
            continue
        sid = row["service_id"]
        # 1 added, 2 removed
        if row.get("exception_type") == "1":
            active.add(sid)
        elif row.get("exception_type") == "2":
            active.discard(sid)
    return active


def list_candidate_dates(calendar: list[dict], calendar_dates: list[dict], limit: int = 400) -> list[date]:
    if not calendar:
        return []
    starts = [parse_yyyymmdd(r["start_date"]) for r in calendar]
    ends = [parse_yyyymmdd(r["end_date"]) for r in calendar]
    lo, hi = min(starts), max(ends)
    out = []
    cur = lo
    while cur <= hi and len(out) < limit:
        if active_service_ids(calendar, calendar_dates, cur):
            out.append(cur)
        cur += timedelta(days=1)
    return out


def pick_service_date(calendar, calendar_dates, requested: date | None) -> date:
    if requested and active_service_ids(calendar, calendar_dates, requested):
        return requested
    if active_service_ids(calendar, calendar_dates, PREFERRED_DATE):
        return PREFERRED_DATE
    dates = list_candidate_dates(calendar, calendar_dates)
    if not dates:
        raise RuntimeError("日历中找不到任何有效服务日")
    # 优先普通工作日
    weekdays = [d for d in dates if d.weekday() < 5]
    return weekdays[0] if weekdays else dates[0]


def line_name_from_route(route: dict) -> str:
    short = route.get("route_short_name") or route.get("route_id") or ""
    # BART: "Yellow-S" / "Yellow-N" -> "Yellow"
    if "-" in short and short.split("-", 1)[1] in {"N", "S", "E", "W", "N0", "S0"}:
        return short.split("-", 1)[0]
    long = route.get("route_long_name") or short
    return short or long


def color_hex(s: str, default: str = "#336699") -> str:
    s = (s or "").strip().lstrip("#")
    if len(s) == 6 and all(c in "0123456789abcdefABCDEF" for c in s):
        return f"#{s.upper()}"
    return default


def simplify_line(points: list[list[float]], min_deg: float = 0.00015) -> list[list[float]]:
    """按相邻点最小间距抽稀折线，保留端点。min_deg≈15–20 米。"""
    if len(points) <= 2:
        return points
    kept = [points[0]]
    last = points[0]
    for p in points[1:-1]:
        if math.hypot(p[0] - last[0], p[1] - last[1]) >= min_deg:
            kept.append(p)
            last = p
    kept.append(points[-1])
    return kept


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def copy_to_app(processed: Path) -> None:
    APP_DATA.mkdir(parents=True, exist_ok=True)
    for src in processed.glob("*.json"):
        dest = APP_DATA / src.name
        dest.write_bytes(src.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description="从 GTFS 生成原型用 JSON")
    parser.add_argument("--gtfs", type=Path, default=DEFAULT_GTFS, help="GTFS zip 或解压目录")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="加工结果目录")
    parser.add_argument("--service-date", default="", help="服务日 YYYY-MM-DD 或 YYYYMMDD")
    args = parser.parse_args()

    gtfs = args.gtfs.resolve()
    if not gtfs.exists():
        print(f"找不到 GTFS: {gtfs}", file=sys.stderr)
        return 1

    requested = None
    if args.service_date:
        s = args.service_date.replace("-", "")
        requested = parse_yyyymmdd(s)

    agency = read_gtfs_table(gtfs, "agency.txt")
    feed_info = read_gtfs_table(gtfs, "feed_info.txt")
    routes = read_gtfs_table(gtfs, "routes.txt")
    stops = read_gtfs_table(gtfs, "stops.txt")
    trips = read_gtfs_table(gtfs, "trips.txt")
    stop_times = read_gtfs_table(gtfs, "stop_times.txt")
    calendar = read_gtfs_table(gtfs, "calendar.txt")
    calendar_dates = read_gtfs_table(gtfs, "calendar_dates.txt")
    shapes = read_gtfs_table(gtfs, "shapes.txt")

    rail_routes = [r for r in routes if r.get("route_type") in RAIL_TYPES]
    rail_ids = {r["route_id"] for r in rail_routes}
    skipped_routes = [r for r in routes if r.get("route_type") not in RAIL_TYPES]

    service_day = pick_service_date(calendar, calendar_dates, requested)
    service_ids = active_service_ids(calendar, calendar_dates, service_day)
    day_trips = [t for t in trips if t["route_id"] in rail_ids and t["service_id"] in service_ids]
    trip_ids = {t["trip_id"] for t in day_trips}
    trip_by_id = {t["trip_id"]: t for t in day_trips}

    day_stop_times = [st for st in stop_times if st["trip_id"] in trip_ids]
    # 按 trip, stop_sequence 排序
    def seq(st):
        try:
            return int(st.get("stop_sequence") or 0)
        except ValueError:
            return 0

    day_stop_times.sort(key=lambda st: (st["trip_id"], seq(st)))

    # 站点：优先用地图级父站（location_type=1）；否则用无父级的停靠点。
    parents = [s for s in stops if s.get("location_type") == "1"]
    platforms = [s for s in stops if s.get("location_type") in {"", "0"}]
    entrances_n = sum(1 for s in stops if s.get("location_type") == "2")
    platform_to_parent = {}
    for s in platforms:
        pid = s.get("parent_station") or s["stop_id"]
        platform_to_parent[s["stop_id"]] = pid
        platform_to_parent.setdefault(pid, pid)
    # 也把父站自身映射上
    for s in parents:
        platform_to_parent[s["stop_id"]] = s["stop_id"]

    station_rows = parents if parents else platforms
    stations = []
    station_by_id = {}
    for s in station_rows:
        # 若用 platforms 当车站，跳过已有父站的重复月台
        if not parents and s.get("parent_station"):
            continue
        rec = {
            "id": s["stop_id"],
            "name": s.get("stop_name") or s["stop_id"],
            "lat": float(s["stop_lat"]) if s.get("stop_lat") else None,
            "lon": float(s["stop_lon"]) if s.get("stop_lon") else None,
            "url": s.get("stop_url") or "",
        }
        stations.append(rec)
        station_by_id[rec["id"]] = rec
    stations.sort(key=lambda x: x["name"])

    # 线路分组（同色、同名前缀视为一条线的两个方向）
    lines: dict[str, dict] = {}
    route_to_line: dict[str, str] = {}
    routes_out = []
    for r in rail_routes:
        lid = line_name_from_route(r)
        color = color_hex(r.get("route_color"))
        text_color = color_hex(r.get("route_text_color"), "#FFFFFF")
        route_to_line[r["route_id"]] = lid
        if lid not in lines:
            lines[lid] = {
                "id": lid,
                "name": lid,
                "color": color,
                "text_color": text_color,
                "route_ids": [],
            }
        if r["route_id"] not in lines[lid]["route_ids"]:
            lines[lid]["route_ids"].append(r["route_id"])
        routes_out.append({
            "id": r["route_id"],
            "line_id": lid,
            "short_name": r.get("route_short_name") or r["route_id"],
            "long_name": r.get("route_long_name") or "",
            "color": color,
            "text_color": text_color,
            "route_type": int(r["route_type"]) if r.get("route_type") else None,
        })

    # 形状：按 trip 用到的 shape_id 收集，并抽稀
    used_shapes = {t.get("shape_id") for t in day_trips if t.get("shape_id")}
    shape_pts: dict[str, list] = defaultdict(list)
    for row in shapes:
        sid = row.get("shape_id")
        if used_shapes and sid not in used_shapes:
            continue
        try:
            lat = float(row["shape_pt_lat"])
            lon = float(row["shape_pt_lon"])
            seqn = int(row.get("shape_pt_sequence") or 0)
        except (TypeError, ValueError):
            continue
        shape_pts[sid].append((seqn, lon, lat))  # GeoJSON 为 lon,lat
    shape_coords = {}
    raw_n = 0
    simp_n = 0
    for sid, pts in shape_pts.items():
        pts.sort()
        coords = [[lon, lat] for _, lon, lat in pts]
        raw_n += len(coords)
        simp = simplify_line(coords)
        simp_n += len(simp)
        shape_coords[sid] = simp

    # 每条 route 选一条代表性 shape（当天使用次数最多）
    shape_counts = Counter((t["route_id"], t.get("shape_id")) for t in day_trips if t.get("shape_id"))
    route_shape: dict[str, str] = {}
    for (rid, sid), _n in shape_counts.most_common():
        route_shape.setdefault(rid, sid)

    shapes_out = []
    for r in routes_out:
        sid = route_shape.get(r["id"])
        if not sid or sid not in shape_coords:
            continue
        shapes_out.append({
            "route_id": r["id"],
            "line_id": r["line_id"],
            "color": r["color"],
            "coordinates": shape_coords[sid],
        })

    # 到站：归并到父站
    arrivals_by_station: dict[str, list] = defaultdict(list)
    trips_for_spacetime: dict[str, list] = defaultdict(list)  # trip_id -> list of {station, seq, t}
    first_dep_by_trip: dict[str, int] = {}

    for st in day_stop_times:
        trip = trip_by_id.get(st["trip_id"])
        if not trip:
            continue
        parent = platform_to_parent.get(st["stop_id"]) or st["stop_id"]
        if parent not in station_by_id:
            # 若只有月台坐标、父站未收录，跳过或补录——这里跳过入口类
            continue
        tmin = parse_gtfs_time(st.get("arrival_time") or st.get("departure_time"))
        if tmin is None:
            continue
        dep = parse_gtfs_time(st.get("departure_time") or st.get("arrival_time"))
        lid = route_to_line.get(trip["route_id"], trip["route_id"])
        rec = {
            "t": tmin,
            "hhmm": format_hhmm(tmin),
            "route_id": trip["route_id"],
            "line_id": lid,
            "headsign": trip.get("trip_headsign") or "",
            "direction_id": trip.get("direction_id") or "",
            "trip_id": trip["trip_id"],
        }
        arrivals_by_station[parent].append(rec)
        trips_for_spacetime[trip["trip_id"]].append({
            "station_id": parent,
            "seq": seq(st),
            "t": tmin,
        })
        if dep is not None and trip["trip_id"] not in first_dep_by_trip:
            first_dep_by_trip[trip["trip_id"]] = dep

    for sid, arr in arrivals_by_station.items():
        arr.sort(key=lambda a: (a["t"], a["line_id"], a["route_id"]))
        ts = [a["t"] for a in arr]
        station_by_id[sid]["service_start"] = format_hhmm(min(ts))
        station_by_id[sid]["service_end"] = format_hhmm(max(ts))
        station_by_id[sid]["arrival_count"] = len(arr)
        station_by_id[sid]["line_ids"] = sorted({a["line_id"] for a in arr})

    # 车站输出（不把全部到站时刻内嵌进 stations.json，避免重复；另写 arrivals.json）
    stations_out = []
    for s in stations:
        extra = station_by_id[s["id"]]
        stations_out.append({
            **s,
            "service_start": extra.get("service_start", ""),
            "service_end": extra.get("service_end", ""),
            "arrival_count": extra.get("arrival_count", 0),
            "line_ids": extra.get("line_ids", []),
        })

    arrivals_out = {
        sid: [
            {k: v for k, v in a.items() if k != "trip_id"}  # 页面不需要 trip_id
            for a in arr
        ]
        for sid, arr in arrivals_by_station.items()
    }

    # 分析：各线班次数与行车间隔（按该方向第一站发车时刻的间隔）
    trips_by_route_dir = defaultdict(list)
    for t in day_trips:
        key = (route_to_line.get(t["route_id"], t["route_id"]), t["route_id"], t.get("direction_id") or "0")
        if t["trip_id"] in first_dep_by_trip:
            trips_by_route_dir[key].append(first_dep_by_trip[t["trip_id"]])

    analysis_rows = []
    for (lid, rid, did), times in sorted(trips_by_route_dir.items()):
        times = sorted(times)
        intervals = [b - a for a, b in zip(times, times[1:]) if b - a > 0]
        route_meta = next((r for r in routes_out if r["id"] == rid), {})
        analysis_rows.append({
            "line_id": lid,
            "route_id": rid,
            "route_name": route_meta.get("long_name") or route_meta.get("short_name") or rid,
            "color": route_meta.get("color") or "#336699",
            "direction_id": did,
            "trip_count": len(times),
            "first_dep": format_hhmm(times[0]) if times else "",
            "last_dep": format_hhmm(times[-1]) if times else "",
            "median_headway_min": round(statistics.median(intervals), 1) if intervals else None,
            "mean_headway_min": round(statistics.mean(intervals), 1) if intervals else None,
        })

    # 时空图：每条线每个方向，取当天停站最多的一趟作为站序
    spacetime = []
    trips_grouped = defaultdict(list)
    for t in day_trips:
        lid = route_to_line.get(t["route_id"], t["route_id"])
        trips_grouped[(lid, t.get("direction_id") or "0")].append(t)

    for (lid, did), tlist in sorted(trips_grouped.items()):
        sequences = []
        for t in tlist:
            stops_t = trips_for_spacetime.get(t["trip_id"]) or []
            # 同一站可能因换乘通道重复，按 seq 保留
            sequences.append((len(stops_t), t, stops_t))
        if not sequences:
            continue
        sequences.sort(key=lambda x: -x[0])
        _, ref_trip, ref_stops = sequences[0]
        # 站序：按参考班次，去重父站（首次出现）
        order = []
        seen = set()
        for rec in sorted(ref_stops, key=lambda r: r["seq"]):
            if rec["station_id"] in seen:
                continue
            seen.add(rec["station_id"])
            stn = station_by_id.get(rec["station_id"]) or {}
            order.append({"id": rec["station_id"], "name": stn.get("name") or rec["station_id"]})
        index_of = {s["id"]: i for i, s in enumerate(order)}
        trips_payload = []
        for _n, t, stops_t in sequences:
            points = []
            for rec in sorted(stops_t, key=lambda r: r["seq"]):
                idx = index_of.get(rec["station_id"])
                if idx is None:
                    continue
                points.append({"i": idx, "t": rec["t"]})
            if len(points) < 2:
                continue
            trips_payload.append({
                "headsign": t.get("trip_headsign") or "",
                "route_id": t["route_id"],
                "points": points,
            })
        line_meta = lines.get(lid, {})
        route_meta = next((r for r in routes_out if r["id"] == ref_trip["route_id"]), {})
        spacetime.append({
            "line_id": lid,
            "direction_id": did,
            "label": route_meta.get("long_name") or lid,
            "color": line_meta.get("color") or "#336699",
            "stations": order,
            "trip_count": len(trips_payload),
            "trips": trips_payload,
        })

    agency_name = agency[0]["agency_name"] if agency else ""
    agency_url = agency[0].get("agency_url", "") if agency else ""
    agency_tz = agency[0].get("agency_timezone", "") if agency else ""
    feed_meta = feed_info[0] if feed_info else {}

    meta = {
        "title": "公开城市轨道交通时空数据样品原型",
        "disclaimer": "这是选题 A 的样品原型，三条候选之一，不是已确认的毕设题目。",
        "agency_name": agency_name,
        "agency_url": agency_url,
        "timezone": agency_tz,
        "service_date": service_day.isoformat(),
        "service_date_note": "服务日按 GTFS calendar / calendar_dates 判定；时刻为该时区的计划到站时刻，不是北京时间。超过 24:00 的时刻表示跨过午夜的车次。",
        "source": {
            "name": "BART 官方静态 GTFS（默认样品）",
            "permalink": "https://www.bart.gov/dev/schedules/google_transit.zip",
            "docs": "https://www.bart.gov/schedules/developers/gtfs",
            "license_name": "BART Developer License Agreement",
            "license_url": "https://www.bart.gov/schedules/developers/developer-license-agreement",
            "used_atlas_sample": False,
        },
        "feed_info": feed_meta,
        "feed_info_note": "本份 feed_info.txt 中的 feed_start_date/feed_end_date 与 zip 文件名及 calendar.txt 的日期窗不一致，已按事实记录，服务日判定以 calendar 与 calendar_dates 为准（这是数据观察，不是对官方日期的改写）。",
        "counts": {
            "stations": len(stations_out),
            "rail_routes": len(routes_out),
            "lines": len(lines),
            "trips": len(day_trips),
            "stop_times": len(day_stop_times),
            "shape_points_raw_used": raw_n,
            "shape_points_simplified": simp_n,
            "skipped_non_rail_routes": [r.get("route_short_name") or r["route_id"] for r in skipped_routes],
            "parent_stations": len(parents),
            "platforms": len(platforms),
            "entrances_ignored": entrances_n,
            "service_ids": sorted(service_ids),
        },
        "subset": {
            "kept_route_types": [0, 1, 2],
            "dropped_route_types": "非轨道（如公交接驳 Bus Bridge）",
            "one_service_day": service_day.isoformat(),
        },
    }

    # 若用户显式指向非默认路径（例如日后的 Atlas 样本），在 meta 里标明。
    if gtfs != DEFAULT_GTFS.resolve():
        meta["source"]["name"] = f"外部 GTFS（{gtfs.name}）"
        meta["source"]["path"] = str(gtfs)
        meta["source"]["used_atlas_sample"] = "atlas" in str(gtfs).lower()

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "meta.json", meta)
    write_json(out / "lines.json", {
        "lines": list(lines.values()),
        "routes": routes_out,
    })
    write_json(out / "stations.json", {"stations": stations_out})
    write_json(out / "shapes.json", {"shapes": shapes_out})
    write_json(out / "arrivals.json", {"service_date": service_day.isoformat(), "arrivals": arrivals_out})
    write_json(out / "analysis.json", {"rows": analysis_rows, "spacetime": spacetime})
    copy_to_app(out)

    print(f"GTFS: {gtfs}")
    print(f"服务日: {service_day.isoformat()}  service_ids={sorted(service_ids)}")
    print(f"车站 {len(stations_out)}  线路组 {len(lines)}  轨道route {len(routes_out)}  班次 {len(day_trips)}  到站 {len(day_stop_times)}")
    print(f"已排除非轨道线路: {meta['counts']['skipped_non_rail_routes']}")
    print(f"写出: {out}")
    print(f"同步: {APP_DATA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
