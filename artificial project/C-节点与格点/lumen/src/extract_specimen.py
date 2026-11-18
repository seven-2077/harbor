#!/usr/bin/env python3
"""Build data/specimen.js from the unchanged Atlas copies in data/raw/.

Does not modify source CSVs. Comfort bands are a design convention, not a standard.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT_JS = ROOT / "data" / "specimen.js"
OUT_META = ROOT / "data" / "specimen.meta.json"

STM_CSV = RAW / "stm32_sim_stream_2026-08-03T12_30min.csv"
WX_CSV = RAW / "openmeteo_lanzhou_weather_2026-08-03_to_2026-08-09.csv"
AQ_CSV = RAW / "openmeteo_lanzhou_air_quality_2026-08-03_to_2026-08-09.csv"

CHANNELS = [
    "temperature",
    "relative_humidity",
    "pressure",
    "illuminance",
    "gas_index",
    "gas_adc",
    "mcu_temperature",
]

T_BAND = (20, 26)
RH_BAND = (40, 60)
LUX_MARK = 300


def read_commented_csv(path: Path):
    meta_rows = []
    body = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            body.append(line)
    reader = csv.DictReader(body)
    for row in reader:
        meta_rows.append(row)
    return meta_rows


def read_openmeteo(path: Path):
    with path.open(encoding="utf-8") as f:
        lines = f.read().splitlines()
    # first block: grid header (2 lines), blank, then hourly table
    grid = {}
    i = 0
    header = lines[0].split(",")
    values = lines[1].split(",")
    grid = dict(zip(header, values))
    # find hourly header
    for i, line in enumerate(lines):
        if line.startswith("time,"):
            start = i
            break
    rows = list(csv.DictReader(lines[start:]))
    return grid, rows


def r(v, n):
    return round(float(v), n)


def channel_stats(xs):
    xs = [float(v) for v in xs]
    n = len(xs)
    # first / last 5 minutes at 10 s: 30 samples (00–4:50) and last 30 (25:10–30:00)
    first = xs[:30]
    last = xs[-30:]
    return {
        "n": n,
        "min": r(min(xs), 3),
        "max": r(max(xs), 3),
        "mean": r(sum(xs) / n, 3),
        "median": r(statistics.median(xs), 3),
        "std": r(statistics.pstdev(xs), 3),
        "span": r(max(xs) - min(xs), 3),
        "first5min_mean": r(sum(first) / len(first), 3),
        "last5min_mean": r(sum(last) / len(last), 3),
    }


def main():
    indoor_rows = read_commented_csv(STM_CSV)
    by_seq = {}
    times = []
    series = {k: [] for k in CHANNELS}
    for row in indoor_rows:
        seq = int(row["seq"])
        ch = row["channel"]
        val = float(row["value"])
        slot = by_seq.setdefault(seq, {"seq": seq, "time": row["timestamp_local"]})
        slot[ch] = val
    seqs = sorted(by_seq)
    for seq in seqs:
        slot = by_seq[seq]
        times.append(slot["time"])
        for k in CHANNELS:
            series[k].append(slot[k])

    stats = {k: channel_stats(series[k]) for k in CHANNELS}
    t_in = sum(1 for v in series["temperature"] if T_BAND[0] <= v <= T_BAND[1])
    rh_in = sum(1 for v in series["relative_humidity"] if RH_BAND[0] <= v <= RH_BAND[1])
    both = sum(
        1
        for t, h in zip(series["temperature"], series["relative_humidity"])
        if T_BAND[0] <= t <= T_BAND[1] and RH_BAND[0] <= h <= RH_BAND[1]
    )
    lux_ge = sum(1 for v in series["illuminance"] if v >= LUX_MARK)

    wx_grid, wx_rows = read_openmeteo(WX_CSV)
    aq_grid, aq_rows = read_openmeteo(AQ_CSV)
    aq_by_t = {row["time"]: row for row in aq_rows}

    def hour_rec(w):
        a = aq_by_t[w["time"]]
        return {
            "time": w["time"],
            "t": r(w["temperature_2m (°C)"], 1),
            "rh": r(w["relative_humidity_2m (%)"], 1),
            "precip": r(w["precipitation (mm)"], 2),
            "wind": r(w["wind_speed_10m (km/h)"], 1),
            "p": r(w["surface_pressure (hPa)"], 1),
            "pm25": r(a["pm2_5 (μg/m³)"], 1),
            "pm10": r(a["pm10 (μg/m³)"], 1),
            "o3": r(a["ozone (μg/m³)"], 1),
            "co": r(a["carbon_monoxide (μg/m³)"], 1),
            "no2": r(a["nitrogen_dioxide (μg/m³)"], 1),
            "so2": r(a["sulphur_dioxide (μg/m³)"], 1),
            "uv": r(a["uv_index ()"], 2),
            "eaqi": r(a["european_aqi (EAQI)"], 1),
        }

    hours = [hour_rec(w) for w in wx_rows]
    overlap = next(h for h in hours if h["time"] == "2026-08-03T12:00")

    def mm(key):
        xs = [h[key] for h in hours]
        return {"min": min(xs), "max": max(xs)}

    specimen = {
        "meta": {
            "specimen": True,
            "not_a_thesis_title": True,
            "title_zh": "节点与格点",
            "indoor_is_simulated": True,
            "no_physical_board": True,
            "board_reported": "STM32F4ZGT6",
            "board_inferred": "STM32F407ZGT6",
            "board_note": "完整型号 STM32F407ZGT6 是按常见订货型号的推断，未见实物标签前不得写成已核实。",
            "device_id": "stm32-f4zg-sim-01",
            "firmware_rev": "sim-0.1.0",
            "sensors_inferred": ["BME280", "BH1750", "MQ135", "MCU_TS"],
            "interval_s": 10,
            "indoor_window": {
                "start": times[0],
                "end": times[-1],
                "timezone": "Asia/Shanghai",
                "n_cycles": len(seqs),
            },
            "outdoor_window": {
                "start": hours[0]["time"],
                "end": hours[-1]["time"],
                "timezone": "Asia/Shanghai",
                "n_hours": len(hours),
            },
            "overlap_hour": "2026-08-03T12:00",
            "compare_caveat": "室内数值为发明的演示流，仅松散参考了同日 12:00 室外温湿度气压的量级。半小时均值与格点整点值之差，是样品构造的结果，不是实测房间效应。",
            "mq135_caveat": "MQ135 指数未经标定，不是 ppm，不得与 CAMS 的 μg/m³ 做数值等同比较。",
            "mcu_ts_caveat": "片内温度 MCU_TS 更适于检测相对变化，不能当作室内气温。",
            "grid_caveat": "Open-Meteo 为兰州市区参考点（约 36.06°N, 103.83°E）的模式格点产品，接口还将气象与空气质量吸附到不同格点；不是兰大校园测站，也不是实测坐标。",
            "licenses": {
                "open_meteo_data": "CC BY 4.0",
                "attribution": "Weather data by Open-Meteo.com",
                "air_quality_also": "CAMS",
                "do_not_name_model_or_grid": True,
            },
            "weather_grid": wx_grid,
            "aq_grid": aq_grid,
            "acquired": "2026-11-11",
            "acquired_tz": "Asia/Shanghai",
            "source": "Atlas samples; copied unchanged into data/raw/",
        },
        "indoor": {
            "times": times,
            "seq": seqs,
            "series": {k: [r(v, 3) if k != "illuminance" else r(v, 1) for v in series[k]] for k in CHANNELS},
            "stats": stats,
            "comfort_design": {
                "t_band": [T_BAND[0], T_BAND[1]],
                "rh_band": [RH_BAND[0], RH_BAND[1]],
                "lux_mark": LUX_MARK,
                "t_in_band": t_in,
                "rh_in_band": rh_in,
                "both": both,
                "lux_ge_300": lux_ge,
                "n": len(seqs),
                "note": "设计口径，常见室内参考：温度 20–26 °C、相对湿度 40–60%、阅读照度 300 lx。不是国家标准，也不是本样品的实测结论。",
            },
        },
        "outdoor": {
            "hours": hours,
            "overlap": overlap,
            "week": {"t": mm("t"), "rh": mm("rh"), "p": mm("p"), "pm25": mm("pm25")},
        },
    }

    meta = {
        "title_zh": specimen["meta"]["title_zh"],
        "indoor_window": specimen["meta"]["indoor_window"],
        "outdoor_window": specimen["meta"]["outdoor_window"],
        "overlap_hour": specimen["meta"]["overlap_hour"],
        "indoor_stats": stats,
        "comfort_design_counts": {
            "t_in_band": t_in,
            "rh_in_band": rh_in,
            "both": both,
            "lux_ge_300": lux_ge,
            "n": len(seqs),
        },
        "overlap": overlap,
        "week": specimen["outdoor"]["week"],
        "weather_grid": wx_grid,
        "aq_grid": aq_grid,
        "notes": [
            "indoor stream is simulated, not captured from a physical board",
            "comfort bands are a design convention, not a national standard",
        ],
    }

    OUT_JS.write_text(
        "/* Derived from data/raw. Values rounded only for display structure. See SOURCE.md. */\n"
        "window.SPECIMEN = " + json.dumps(specimen, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT_JS, "and", OUT_META)
    print("indoor n", len(seqs), "hours", len(hours))
    print("T", stats["temperature"])
    print("comfort", t_in, rh_in, lux_ge)


if __name__ == "__main__":
    main()
