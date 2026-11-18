#!/usr/bin/env python3
"""Build data/specimen.js from unchanged Atlas copies in data/raw/.

Does not modify source files. Comfort bands are a design convention, not a standard.
Topic B focuses on the node product and data link; no outdoor comparison series.
"""
from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT_JS = ROOT / "data" / "specimen.js"
OUT_META = ROOT / "data" / "specimen.meta.json"

STM_CSV = RAW / "stm32_sim_stream_2026-08-03T12_30min.csv"
USART = RAW / "stm32_sim_usart_lines_example.txt"

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


def r(v, n):
    return round(float(v), n)


def channel_stats(xs):
    xs = [float(v) for v in xs]
    n = len(xs)
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


def read_commented_csv(path: Path):
    body = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            body.append(line)
    return list(csv.DictReader(body))


def read_usart(path: Path):
    comments = []
    lines = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            raw = line.rstrip("\n")
            if raw.startswith("#") or not raw.strip():
                if raw.startswith("#"):
                    comments.append(raw)
                continue
            lines.append(raw)
    return comments, lines


def main():
    indoor_rows = read_commented_csv(STM_CSV)
    by_seq = {}
    for row in indoor_rows:
        seq = int(row["seq"])
        slot = by_seq.setdefault(seq, {"seq": seq, "time": row["timestamp_local"]})
        slot[row["channel"]] = float(row["value"])
        if "raw_" + row["channel"] not in slot:
            slot["raw_" + row["channel"]] = row["raw_value"]

    seqs = sorted(by_seq)
    times = []
    series = {k: [] for k in CHANNELS}
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
    # first / last 5 min lux counts
    lux_first = sum(1 for v in series["illuminance"][:30] if v >= LUX_MARK)
    lux_last = sum(1 for v in series["illuminance"][-30:] if v >= LUX_MARK)

    comments, usart_lines = read_usart(USART)

    def rnd_series(k, xs):
        dp = 1 if k == "illuminance" else (0 if k == "gas_adc" else 3)
        return [r(v, dp) for v in xs]

    specimen = {
        "meta": {
            "specimen": True,
            "not_a_thesis_title": True,
            "title_zh": "室况",
            "title_en": "A room kit",
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
            "usart_note": "115200 8N1 是实践习惯，不是已核实的板级设置。示意串口行与 CSV/JSONL 同一窗口，非实机抓包。",
            "mq135_caveat": "MQ135 指数未经标定，不是 ppm。",
            "mcu_ts_caveat": "片内温度 MCU_TS 更适于检测相对变化，不能当作室内气温。",
            "no_outdoor_compare": True,
            "acquired": "2026-11-11",
            "acquired_tz": "Asia/Shanghai",
            "source": "Atlas samples; copied unchanged into data/raw/",
        },
        "indoor": {
            "times": times,
            "seq": seqs,
            "series": {k: rnd_series(k, series[k]) for k in CHANNELS},
            "stats": stats,
            "comfort_design": {
                "t_band": [T_BAND[0], T_BAND[1]],
                "rh_band": [RH_BAND[0], RH_BAND[1]],
                "lux_mark": LUX_MARK,
                "t_in_band": t_in,
                "rh_in_band": rh_in,
                "both": both,
                "lux_ge_300": lux_ge,
                "lux_ge_300_first5min": lux_first,
                "lux_ge_300_last5min": lux_last,
                "n": len(seqs),
                "note": "设计口径，常见室内参考：温度 20–26 °C、相对湿度 40–60%、阅读照度 300 lx。不是国家标准，也不是本样品的实测结论。",
            },
        },
        "usart": {
            "header_comments": comments,
            "lines": usart_lines,
            "n": len(usart_lines),
        },
    }

    meta = {
        "title_zh": specimen["meta"]["title_zh"],
        "indoor_window": specimen["meta"]["indoor_window"],
        "indoor_stats": stats,
        "comfort_design_counts": specimen["indoor"]["comfort_design"],
        "usart_n": len(usart_lines),
        "notes": [
            "indoor stream and USART lines are simulated, not captured from a physical board",
            "comfort bands are a design convention, not a national standard",
            "this specimen does not use Open-Meteo as a primary comparison",
        ],
    }

    OUT_JS.write_text(
        "/* Derived from data/raw. Values rounded only for display structure. See SOURCE.md. */\n"
        "window.SPECIMEN = "
        + json.dumps(specimen, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT_JS, "bytes", OUT_JS.stat().st_size)
    print("n", len(seqs), "usart", len(usart_lines))
    print("T", stats["temperature"])
    print("lux", stats["illuminance"], "ge300", lux_ge, "first", lux_first, "last", lux_last)
    print("RH", stats["relative_humidity"], "MCU", stats["mcu_temperature"])


if __name__ == "__main__":
    main()
