#!/usr/bin/env python3
"""Extract a single-line, single-service-day sample from Atlas's MTA subway GTFS.

Source (do not modify values): /workspace/research/bishe-night/atlas/tmp/gtfs_subway
Excerpt: routes 7 and 7X, service_id Weekday (used for service date 2026-11-11).
Writes unmodified GTFS row subsets to data/raw/ and a derived timetable.js.
"""
from __future__ import annotations

import csv
import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path

ATLAS = Path("/workspace/research/bishe-night/atlas/tmp/gtfs_subway")
OUT_RAW = Path("/workspace/research/bishe-night/lumen/data/raw")
OUT_DATA = Path("/workspace/research/bishe-night/lumen/data")
ROUTE_IDS = {"7", "7X"}
SERVICE_ID = "Weekday"
SERVICE_DATE = "2026-11-11"
# Official parent-station spine, westbound local complete sequence (22 stations).
# Eastbound locals in this feed omit 52 St (713) and 69 St (711); that is left as recorded.
SPINE_IDS = [
    "701",  # Flushing-Main St
    "702",  # Mets-Willets Point
    "705",  # 111 St
    "706",  # 103 St-Corona Plaza
    "707",  # Junction Blvd
    "708",  # 90 St-Elmhurst Av
    "709",  # 82 St-Jackson Hts
    "710",  # 74 St-Broadway
    "711",  # 69 St
    "712",  # 61 St-Woodside
    "713",  # 52 St
    "714",  # 46 St-Bliss St
    "715",  # 40 St-Lowery St
    "716",  # 33 St-Rawson St
    "718",  # Queensboro Plaza
    "719",  # Court Sq
    "720",  # Hunters Point Av
    "721",  # Vernon Blvd-Jackson Av
    "723",  # Grand Central-42 St
    "724",  # 5 Av
    "725",  # Times Sq-42 St
    "726",  # 34 St-Hudson Yards
]
# Stations bounding the East River / midtown tunnel gap on this line (no 7 stop between them).
RIVER_EAST = "721"  # Vernon Blvd-Jackson Av (Queens)
RIVER_WEST = "723"  # Grand Central-42 St (Manhattan)
MAIN_SHAPE = "7..S97R"  # complete westbound local shape


def open_gtfs(name: str):
    return open(ATLAS / name, encoding="utf-8-sig", newline="")


def write_subset(name: str, fieldnames, rows):
    OUT_RAW.mkdir(parents=True, exist_ok=True)
    path = OUT_RAW / name
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row[k] for k in fieldnames})
    return path


def parse_hms(t: str) -> int:
    h, m, s = map(int, t.split(":"))
    return h * 3600 + m * 60 + s


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def parent_of(stops, sid: str) -> str:
    s = stops[sid]
    return s["parent_station"] or sid


def project_stations_on_shape(shape_pts, stations):
    """Nearest-vertex chainage along a shape, in meters (accumulated segment lengths)."""
    chain = [0.0]
    for i in range(1, len(shape_pts)):
        a, b = shape_pts[i - 1], shape_pts[i]
        chain.append(chain[-1] + haversine_m(a[0], a[1], b[0], b[1]))
    out = {}
    for sid, st in stations.items():
        best_i, best_d = 0, 1e18
        for i, (lat, lon) in enumerate(shape_pts):
            d = haversine_m(st["lat"], st["lon"], lat, lon)
            if d < best_d:
                best_d, best_i = d, i
        out[sid] = {
            "chainage_m": round(chain[best_i], 1),
            "snap_dist_m": round(best_d, 1),
            "shape_index": best_i,
        }
    return out, chain[-1]


def main():
    # --- identity / calendar files (copy wholesale: small and needed for provenance) ---
    OUT_RAW.mkdir(parents=True, exist_ok=True)
    for name in ("agency.txt", "feed_info.txt", "calendar.txt", "calendar_dates.txt"):
        shutil.copyfile(ATLAS / name, OUT_RAW / name)

    with open_gtfs("routes.txt") as f:
        rdr = csv.DictReader(f)
        route_fields = rdr.fieldnames
        routes = [row for row in rdr if row["route_id"] in ROUTE_IDS]
    write_subset("routes.txt", route_fields, routes)

    with open_gtfs("trips.txt") as f:
        rdr = csv.DictReader(f)
        trip_fields = rdr.fieldnames
        trips = [
            row
            for row in rdr
            if row["route_id"] in ROUTE_IDS and row["service_id"] == SERVICE_ID
        ]
    write_subset("trips.txt", trip_fields, trips)
    trip_by_id = {t["trip_id"]: t for t in trips}
    trip_ids = set(trip_by_id)

    with open_gtfs("stop_times.txt") as f:
        rdr = csv.DictReader(f)
        st_fields = rdr.fieldnames
        stop_times = [row for row in rdr if row["trip_id"] in trip_ids]
    stop_times.sort(key=lambda r: (r["trip_id"], int(r["stop_sequence"])))
    write_subset("stop_times.txt", st_fields, stop_times)

    used_stop_ids = {r["stop_id"] for r in stop_times}
    with open_gtfs("stops.txt") as f:
        rdr = csv.DictReader(f)
        stop_fields = rdr.fieldnames
        all_stops = {row["stop_id"]: row for row in rdr}

    # include raw platform stops and their parent stations
    keep_ids = set(used_stop_ids)
    for sid in list(used_stop_ids):
        p = all_stops[sid].get("parent_station")
        if p:
            keep_ids.add(p)
    for sid in SPINE_IDS:
        keep_ids.add(sid)
    stops_rows = [all_stops[sid] for sid in all_stops if sid in keep_ids]
    write_subset("stops.txt", stop_fields, stops_rows)

    used_shapes = {t["shape_id"] for t in trips if t.get("shape_id")}
    with open_gtfs("shapes.txt") as f:
        rdr = csv.DictReader(f)
        shape_fields = rdr.fieldnames
        shape_rows = [row for row in rdr if row["shape_id"] in used_shapes]
    write_subset("shapes.txt", shape_fields, shape_rows)

    # --- derived structures ---
    parents = {}
    for sid in SPINE_IDS:
        s = all_stops[sid]
        parents[sid] = {
            "id": sid,
            "name": s["stop_name"],
            "lat": float(s["stop_lat"]),
            "lon": float(s["stop_lon"]),
        }

    shapes = defaultdict(list)
    for row in shape_rows:
        shapes[row["shape_id"]].append(
            (
                int(row["shape_pt_sequence"]),
                float(row["shape_pt_lat"]),
                float(row["shape_pt_lon"]),
            )
        )
    for sid in shapes:
        shapes[sid].sort()
        shapes[sid] = [(lat, lon) for _, lat, lon in shapes[sid]]

    main_pts = shapes[MAIN_SHAPE]
    projections, shape_len = project_stations_on_shape(main_pts, parents)

    # chainage should be strictly increasing along the spine; if a snap ever
    # inverts, fall back to cumulative haversine between parent coordinates.
    chainages = [projections[sid]["chainage_m"] for sid in SPINE_IDS]
    if any(b <= a for a, b in zip(chainages, chainages[1:])):
        acc = 0.0
        projections[SPINE_IDS[0]]["chainage_m"] = 0.0
        projections[SPINE_IDS[0]]["method_fallback"] = "haversine_stations"
        for a, b in zip(SPINE_IDS, SPINE_IDS[1:]):
            acc += haversine_m(
                parents[a]["lat"], parents[a]["lon"], parents[b]["lat"], parents[b]["lon"]
            )
            projections[b]["chainage_m"] = round(acc, 1)
            projections[b]["method_fallback"] = "haversine_stations"
        y_method = "fallback_haversine_between_parent_stations"
    else:
        # normalize so Flushing (first spine id, east) is 0, Hudson Yards is max
        # main shape 7..S97R is westbound Flushing -> Hudson Yards, so already that order.
        y_method = "nearest_vertex_on_shape_7..S97R"

    # simplify main shape for the ribbon (every k-th point, always keep ends)
    step = max(1, len(main_pts) // 250)
    ribbon = [{"lat": lat, "lon": lon} for lat, lon in main_pts[::step]]
    if ribbon[-1] != {"lat": main_pts[-1][0], "lon": main_pts[-1][1]}:
        ribbon.append({"lat": main_pts[-1][0], "lon": main_pts[-1][1]})

    by_trip = defaultdict(list)
    for row in stop_times:
        by_trip[row["trip_id"]].append(row)

    derived_trips = []
    tmin, tmax = 10**9, 0
    dwell_n = 0
    skip_52_69_east = 0
    east_locals = 0
    end_to_end = []  # scheduled times Flushing <-> Hudson Yards when both present

    for tid, rows in by_trip.items():
        tmeta = trip_by_id[tid]
        stops_d = []
        for row in rows:
            pid = parent_of(all_stops, row["stop_id"])
            arr = parse_hms(row["arrival_time"])
            dep = parse_hms(row["departure_time"])
            if dep != arr:
                dwell_n += 1
            tmin = min(tmin, arr, dep)
            tmax = max(tmax, arr, dep)
            stops_d.append(
                {
                    "s": pid,
                    "a": arr,
                    "d": dep,
                    "raw": row["stop_id"],
                    "seq": int(row["stop_sequence"]),
                }
            )
        ids = [x["s"] for x in stops_d]
        is_express = tmeta["route_id"] == "7X"
        direction = int(tmeta["direction_id"])  # 0 east to Flushing, 1 west to Hudson Yards
        if direction == 0 and not is_express:
            east_locals += 1
            if "713" not in ids and "711" not in ids:
                skip_52_69_east += 1
        if "701" in ids and "726" in ids:
            a = next(x for x in stops_d if x["s"] == "701")
            b = next(x for x in stops_d if x["s"] == "726")
            if direction == 1:
                start, end = a["d"], b["a"]
            else:
                start, end = b["d"], a["a"]
            end_to_end.append(
                {
                    "route": tmeta["route_id"],
                    "direction": direction,
                    "sec": end - start,
                    "start": start,
                    "end": end,
                }
            )
        derived_trips.append(
            {
                "id": tid,
                "route": tmeta["route_id"],
                "dir": direction,
                "headsign": tmeta["trip_headsign"],
                "shape": tmeta["shape_id"],
                "stops": stops_d,
            }
        )

    # sort trips by origin departure for stable paint order
    derived_trips.sort(key=lambda t: (t["stops"][0]["d"], t["id"]))

    # trips per hour by direction, counted at first departure of each trip
    hours = list(range(0, 26))
    by_hour = {
        "east_local": [0] * 26,
        "east_express": [0] * 26,
        "west_local": [0] * 26,
        "west_express": [0] * 26,
    }
    # also counts at Grand Central (723) departures — a central reference station
    by_hour_gc = {
        "east": [0] * 26,
        "west": [0] * 26,
    }
    headways_gc = {"east": [], "west": []}
    gc_deps = {"east": [], "west": []}

    for t in derived_trips:
        h = t["stops"][0]["d"] // 3600
        if 0 <= h < 26:
            key = ("east" if t["dir"] == 0 else "west") + (
                "_express" if t["route"] == "7X" else "_local"
            )
            by_hour[key][h] += 1
        for s in t["stops"]:
            if s["s"] == "723":
                side = "east" if t["dir"] == 0 else "west"
                hh = s["d"] // 3600
                if 0 <= hh < 26:
                    by_hour_gc[side][hh] += 1
                gc_deps[side].append(s["d"])

    for side in ("east", "west"):
        seq = sorted(gc_deps[side])
        for a, b in zip(seq, seq[1:]):
            headways_gc[side].append(b - a)

    def summarize_times(items):
        if not items:
            return None
        secs = [x["sec"] for x in items]
        return {
            "n": len(secs),
            "min_sec": min(secs),
            "max_sec": max(secs),
            "median_sec": sorted(secs)[len(secs) // 2],
        }

    ete = {
        "west_local": summarize_times(
            [x for x in end_to_end if x["direction"] == 1 and x["route"] == "7"]
        ),
        "west_express": summarize_times(
            [x for x in end_to_end if x["direction"] == 1 and x["route"] == "7X"]
        ),
        "east_local": summarize_times(
            [x for x in end_to_end if x["direction"] == 0 and x["route"] == "7"]
        ),
        "east_express": summarize_times(
            [x for x in end_to_end if x["direction"] == 0 and x["route"] == "7X"]
        ),
    }

    # 7X time window (first/last departure at origin)
    def window(route, d):
        xs = [t["stops"][0]["d"] for t in derived_trips if t["route"] == route and t["dir"] == d]
        if not xs:
            return None
        return {"first_dep": min(xs), "last_dep": max(xs), "n": len(xs)}

    stations_out = []
    for sid in SPINE_IDS:
        p = parents[sid]
        pr = projections[sid]
        stations_out.append(
            {
                "id": sid,
                "name": p["name"],
                "lat": round(p["lat"], 6),
                "lon": round(p["lon"], 6),
                "chainage_m": pr["chainage_m"],
                "snap_dist_m": pr.get("snap_dist_m"),
            }
        )

    # scheduled speed between consecutive spine stations is NOT pre-averaged
    # into a headline number here; the page can compute a hovered segment.

    meta = {
        "specimen": True,
        "not_a_thesis_title": True,
        "title_zh": "时刻的坡度",
        "agency": "MTA New York City Transit",
        "route_ids": ["7", "7X"],
        "route_names": {
            "7": "Flushing Local",
            "7X": "Flushing Express",
        },
        "service_id": SERVICE_ID,
        "service_date": SERVICE_DATE,
        "service_date_note": "2026-11-11 is a Wednesday. In this feed, Weekday service applies from 20261101 to 20270515; calendar_dates.txt has no exception on 20261111.",
        "timezone": "America/New_York",
        "feed_version": None,
        "feed_start_date": None,
        "feed_end_date": None,
        "source_files": "atlas/tmp/gtfs_subway (official MTA regular subway GTFS, filename gtfs_subway.zip)",
        "official_url": "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip",
        "developers_page": "https://www.mta.info/developers",
        "terms_url": "https://www.mta.info/developers/terms-and-conditions",
        "acquired": "2026-11-11",
        "acquired_tz": "Asia/Shanghai",
        "excerpt": "Only routes 7 and 7X, service_id=Weekday, plus the stops and shapes those trips use. Not the full network, not multiple days, not realtime, not ridership.",
        "y_axis": {
            "meaning": "Distance along the line, Flushing-Main St = 0 toward 34 St-Hudson Yards.",
            "method": y_method,
            "shape_id": MAIN_SHAPE,
            "shape_length_m": round(shape_len, 1),
        },
        "direction": {
            "0": "eastbound, trip_headsign Flushing-Main St or Mets-Willets Point",
            "1": "westbound, trip_headsign 34 St-Hudson Yards",
        },
        "river_gap": {
            "east_station": RIVER_EAST,
            "west_station": RIVER_WEST,
            "note": "Design annotation: the span between these two recorded stations crosses the East River according to their coordinates. No 7/7X stop exists between them in this excerpt. Not an official civil-engineering map.",
        },
        "eastbound_local_skips": {
            "stations": ["713", "711"],
            "names": ["52 St", "69 St"],
            "east_local_trips": east_locals,
            "east_local_trips_omitting_both": skip_52_69_east,
            "note": "Observed in stop_times, not inferred. Westbound locals include both stations. Displayed as recorded; not corrected.",
        },
        "time_range_sec": [tmin, tmax],
        "counts": {
            "trips": len(derived_trips),
            "stop_times": len(stop_times),
            "stations_on_spine": len(SPINE_IDS),
            "dwell_encoded_if_arr_neq_dep": dwell_n,
        },
        "end_to_end_scheduled": ete,
        "express_windows": {
            "east": window("7X", 0),
            "west": window("7X", 1),
        },
        "facts_vs_inference": {
            "facts": [
                "Trip paths are polylines of arrival and departure timestamps from stop_times, placed on the station spine.",
                "Where arrival and departure differ, a horizontal segment is the scheduled dwell as encoded in the feed.",
                "Hourly bar counts are trip origin departures, or Grand Central departures, tallied from those timestamps.",
                "Headways at Grand Central are differences between successive departures in the same direction.",
                "End-to-end times use departure at the first terminal and arrival at the last when both 701 and 726 appear on the trip.",
            ],
            "inference_or_design": [
                "Position of a train at an arbitrary scrub time is linear interpolation in time between the two surrounding scheduled points, at constant implied speed. It is not a realtime or measured location.",
                "The East River band is a design annotation based on station coordinates, not an official map layer.",
                "Morning 06:30–09:30 and evening 16:00–19:30 veils are design time-of-day bands, not an official peak definition.",
                "Y-axis chainage is computed from GTFS shapes (nearest vertex) or station coordinates; it is not a posted track mileage.",
                "Chinese UI wording and the specimen title are design, not an official MTA translation or a chosen thesis title.",
            ],
        },
    }

    with open_gtfs("feed_info.txt") as f:
        fi = next(csv.DictReader(f))
        meta["feed_version"] = fi.get("feed_version")
        meta["feed_start_date"] = fi.get("feed_start_date")
        meta["feed_end_date"] = fi.get("feed_end_date")
        meta["feed_publisher_name"] = fi.get("feed_publisher_name")
        meta["feed_publisher_url"] = fi.get("feed_publisher_url")

    computed = {
        "trips_by_hour_origin": by_hour,
        "trips_by_hour_grand_central": by_hour_gc,
        "headways_grand_central_sec": {
            "east": {
                "n": len(headways_gc["east"]),
                "min": min(headways_gc["east"]) if headways_gc["east"] else None,
                "median": sorted(headways_gc["east"])[len(headways_gc["east"]) // 2]
                if headways_gc["east"]
                else None,
                "max": max(headways_gc["east"]) if headways_gc["east"] else None,
            },
            "west": {
                "n": len(headways_gc["west"]),
                "min": min(headways_gc["west"]) if headways_gc["west"] else None,
                "median": sorted(headways_gc["west"])[len(headways_gc["west"]) // 2]
                if headways_gc["west"]
                else None,
                "max": max(headways_gc["west"]) if headways_gc["west"] else None,
            },
        },
    }

    payload = {
        "meta": meta,
        "stations": stations_out,
        "trips": derived_trips,
        "ribbon": ribbon,
        "computed": computed,
    }

    js_path = OUT_DATA / "timetable.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("/* Derived from data/raw GTFS excerpts. See data/SOURCE.md. */\n")
        f.write("window.SPECIMEN = ")
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    # a compact JSON copy for inspection
    with open(OUT_DATA / "timetable.meta.json", "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "computed": computed, "stations": stations_out}, f, ensure_ascii=False, indent=2)

    print("trips", len(derived_trips), "stop_times", len(stop_times))
    print("time", tmin, tmax)
    print("y_method", y_method)
    print("chainage", [projections[s]["chainage_m"] for s in SPINE_IDS])
    print("end_to_end", json.dumps(ete, indent=2))
    print("express windows", window("7X", 0), window("7X", 1))
    print("east locals skip 52/69", skip_52_69_east, "of", east_locals)
    print("js bytes", js_path.stat().st_size)
    print("raw files", sorted(p.name for p in OUT_RAW.iterdir()))


if __name__ == "__main__":
    main()
