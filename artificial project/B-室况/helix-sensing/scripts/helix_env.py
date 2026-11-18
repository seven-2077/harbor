#!/usr/bin/env python3
"""解析 Atlas 提供的 STM32 模拟 USART / 长表 CSV，并读取 Open-Meteo 对照小时值。

USART 一行（与即将对齐的固件 printf 一致），空格分隔的 key=value：

  DEV=stm32-f4zg-sim-01 TS=2026-08-03T12:00:00+08:00 SEQ=0
  BME280_T_C=26.66 BME280_RH_PCT=46.79 BME280_P_HPA=852.61
  BH1750_LUX=273.0 MQ135_ADC=1474 MQ135_INDEX=26.01 MCU_TS_C=33.45 SRC=simulated

这是 Atlas 的模拟格式，不是实机抓到的日志。MQ135_INDEX 不是标定 ppm。
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

SHANGHAI = timezone(timedelta(hours=8), name="Asia/Shanghai")

ATLAS_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "atlas" / "samples"
USART_SAMPLE = ATLAS_DIR / "stm32_sim_usart_lines_example.txt"
CSV_SAMPLE = ATLAS_DIR / "stm32_sim_stream_2026-08-03T12_30min.csv"
WEATHER_SAMPLE = ATLAS_DIR / "openmeteo_lanzhou_weather_2026-08-03_to_2026-08-09.csv"
AIR_SAMPLE = ATLAS_DIR / "openmeteo_lanzhou_air_quality_2026-08-03_to_2026-08-09.csv"

DEVICE = {
    "device_id": "stm32-f4zg-sim-01",
    "label": "模拟室内节点",
    "place": "Atlas 模拟流中的占位设备（不是已安装的实物）",
}

THRESHOLDS = {
    "temp_c_ok": (20.0, 26.0),
    "rh_pct_ok": (40.0, 60.0),
    "lux_study": 300,
}

FLOAT_KEYS = {
    "BME280_T_C": "temp_c",
    "BME280_RH_PCT": "rh_pct",
    "BME280_P_HPA": "pressure_hpa",
    "BH1750_LUX": "lux",
    "MQ135_INDEX": "mq135_index",
    "MCU_TS_C": "mcu_temp_c",
}
INT_KEYS = {
    "SEQ": "seq",
    "MQ135_ADC": "mq135_adc",
}


def parse_usart_line(line: str) -> dict | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    rec: dict = {}
    for tok in line.split():
        if "=" not in tok:
            return None
        k, v = tok.split("=", 1)
        rec[k] = v
    if "DEV" not in rec:
        return None
    out = {
        "device_id": rec.get("DEV"),
        "recv_ts": rec.get("TS") or "",
        "source": rec.get("SRC") or "",
        "raw_line": line,
    }
    for src, dest in FLOAT_KEYS.items():
        if src in rec:
            try:
                out[dest] = float(rec[src])
            except ValueError:
                return None
    for src, dest in INT_KEYS.items():
        if src in rec:
            try:
                out[dest] = int(float(rec[src]))
            except ValueError:
                return None
    return out


def load_usart_log(path: Path | None = None) -> list[dict]:
    path = path or USART_SAMPLE
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            rec = parse_usart_line(line)
            if rec:
                rows.append(rec)
    rows.sort(key=lambda r: (r.get("recv_ts") or "", r.get("seq") or 0))
    return rows


def load_long_csv(path: Path | None = None) -> list[dict]:
    """可选：把 Atlas 长表（每通道一行）折成与 USART 相同的周期记录。"""
    path = path or CSV_SAMPLE
    grouped: dict[tuple, dict] = {}
    with path.open(encoding="utf-8", newline="") as f:
        # skip comments
        sample = ""
        while True:
            pos = f.tell()
            line = f.readline()
            if not line:
                break
            if line.startswith("#") or not line.strip():
                continue
            f.seek(pos)
            break
        reader = csv.DictReader(f)
        for row in reader:
            key = (row.get("timestamp_local") or "", row.get("device_id") or "", row.get("seq") or "")
            rec = grouped.setdefault(key, {
                "device_id": row.get("device_id"),
                "recv_ts": row.get("timestamp_local") or "",
                "seq": int(row["seq"]) if row.get("seq", "").isdigit() else None,
                "source": row.get("source") or "",
            })
            sensor = row.get("sensor_id") or ""
            ch = row.get("channel") or ""
            try:
                val = float(row.get("value") or "")
            except ValueError:
                continue
            if sensor == "BME280" and ch == "temperature":
                rec["temp_c"] = val
            elif sensor == "BME280" and ch == "relative_humidity":
                rec["rh_pct"] = val
            elif sensor == "BME280" and ch == "pressure":
                rec["pressure_hpa"] = val
            elif sensor == "BH1750":
                rec["lux"] = val
            elif sensor == "MQ135" and ch == "gas_adc":
                rec["mq135_adc"] = int(val)
            elif sensor == "MQ135" and ch == "gas_index":
                rec["mq135_index"] = val
            elif sensor == "MCU_TS":
                rec["mcu_temp_c"] = val
    rows = list(grouped.values())
    rows.sort(key=lambda r: (r.get("recv_ts") or "", r.get("seq") or 0))
    return rows


def _openmeteo_table(path: Path) -> tuple[dict, list[dict]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    meta: dict = {}
    # first header block
    if lines and "latitude" in lines[0]:
        keys = next(csv.reader([lines[0]]))
        vals = next(csv.reader([lines[1]])) if len(lines) > 1 else []
        meta = dict(zip(keys, vals))
    header_i = None
    for i, line in enumerate(lines):
        if line.startswith("time,"):
            header_i = i
            break
    if header_i is None:
        return meta, []
    header = next(csv.reader([lines[header_i]]))
    rows = []
    for line in lines[header_i + 1:]:
        if not line.strip():
            continue
        rows.append(dict(zip(header, next(csv.reader([line])))))
    return meta, rows


def load_outdoor_hourly() -> dict:
    wmeta, weather = _openmeteo_table(WEATHER_SAMPLE)
    ameta, air = _openmeteo_table(AIR_SAMPLE)

    def index(rows):
        return {r["time"]: r for r in rows if "time" in r}

    w_by, a_by = index(weather), index(air)
    times = sorted(set(w_by) | set(a_by))
    series = []
    for t in times:
        rec = {"time": t}
        rec.update(w_by.get(t, {}))
        rec.update(a_by.get(t, {}))
        series.append(rec)
    return {
        "license": "Open-Meteo 数据按 Atlas 清单记为 CC BY 4.0。须署名 Open-Meteo。这是模式格点，不是校园气象站实测。",
        "weather_attribution": "Weather data by Open-Meteo.com (https://open-meteo.com/)",
        "weather_meta": wmeta,
        "air_meta": ameta,
        "hourly": series,
    }


def outdoor_at(hourly: dict, local_hour: str) -> dict | None:
    """local_hour 如 2026-08-03T12:00 或带秒/时区的 ISO。"""
    if not local_hour:
        return None
    key = local_hour.replace("+08:00", "")
    if len(key) >= 16:
        key = key[:16]  # YYYY-MM-DDTHH:MM
    if key.endswith(":00") and len(key) == 16:
        hour_key = key
    else:
        hour_key = key[:13] + ":00"
    for row in hourly.get("hourly") or []:
        if (row.get("time") or "").startswith(hour_key):
            return row
    return None


def comfort(row: dict) -> bool:
    t0, t1 = THRESHOLDS["temp_c_ok"]
    h0, h1 = THRESHOLDS["rh_pct_ok"]
    t, h = row.get("temp_c"), row.get("rh_pct")
    if t is None or h is None:
        return False
    return t0 <= t <= t1 and h0 <= h <= h1
