#!/usr/bin/env python3
"""选题 B：接入 Atlas 的模拟 STM32 USART/CSV 流，做简单分析，并提供本地看板。

只使用 Python 标准库。看完后请 Ctrl+C 停掉，不要留下占端口进程。
云电脑没有实物板：本服务跑的是模拟样本，实机未验证。
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helix_env import (  # noqa: E402
    DEVICE,
    THRESHOLDS,
    USART_SAMPLE,
    comfort,
    load_outdoor_hourly,
    load_usart_log,
    outdoor_at,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORT = 8766
_ROWS: list[dict] = []
_OUTDOOR: dict = {}


def analyze(rows: list[dict]) -> dict:
    seq = sorted(rows, key=lambda r: (r.get("recv_ts") or "", r.get("seq") or 0))
    latest = seq[-1] if seq else None
    n = len(seq)
    comfortable = sum(1 for r in seq if comfort(r))
    temps = [r["temp_c"] for r in seq if "temp_c" in r]
    indexes = [r["mq135_index"] for r in seq if "mq135_index" in r]
    luxs = [r["lux"] for r in seq if "lux" in r]
    alerts = []
    if latest:
        if not comfort(latest):
            alerts.append({
                "level": "info",
                "device_id": latest["device_id"],
                "recv_ts": latest.get("recv_ts"),
                "text": "温湿度离开本原型舒适参考区（温度 %s°C，湿度 %s%%）。"
                % (latest.get("temp_c"), latest.get("rh_pct")),
            })
        if latest.get("lux") is not None and latest["lux"] < THRESHOLDS["lux_study"]:
            alerts.append({
                "level": "info",
                "device_id": latest["device_id"],
                "recv_ts": latest.get("recv_ts"),
                "text": "照度 %.0f lx，低于本原型采用的室内阅读参考 %s lx（不是学校官方标准）。"
                % (latest["lux"], THRESHOLDS["lux_study"]),
            })
    if indexes:
        span = max(indexes) - min(indexes)
        if span >= 8:
            peak = max(seq, key=lambda r: r.get("mq135_index") or 0)
            alerts.append({
                "level": "info",
                "device_id": DEVICE["device_id"],
                "recv_ts": peak.get("recv_ts"),
                "text": "本窗口 MQ135 示意指数从 %.2f 到 %.2f，仅表示相对变化，不是标定气体浓度。"
                % (min(indexes), max(indexes)),
            })

    outdoor_now = outdoor_at(_OUTDOOR, latest["recv_ts"]) if latest else None
    compare = None
    if latest and outdoor_now:
        def num(row, *keys):
            for k in keys:
                if k in row and row[k] not in ("", None):
                    try:
                        return float(row[k])
                    except (TypeError, ValueError):
                        continue
            return None
        compare = {
            "outdoor_time": outdoor_now.get("time"),
            "note": "室外值来自 Open-Meteo 兰州格点的整点小时（模式数据，不是校园气象站）。室内值来自 Atlas 模拟流。同一本地小时可以对照量级，不能当成同一台仪器的校准。",
            "indoor_temp_c": latest.get("temp_c"),
            "outdoor_temp_c": num(outdoor_now, "temperature_2m (°C)", "temperature_2m"),
            "indoor_rh_pct": latest.get("rh_pct"),
            "outdoor_rh_pct": num(outdoor_now, "relative_humidity_2m (%)", "relative_humidity_2m"),
            "indoor_pressure_hpa": latest.get("pressure_hpa"),
            "outdoor_pressure_hpa": num(outdoor_now, "surface_pressure (hPa)", "surface_pressure"),
        }

    return {
        "generated_at": (latest or {}).get("recv_ts") or "",
        "timezone": "Asia/Shanghai",
        "thresholds": THRESHOLDS,
        "threshold_note": "舒适区与照度参考是本原型采用的常用室内参考，不是学校官方标准，也不是已校准规格。MQ135 指数未标定。",
        "nodes": [{
            "device_id": DEVICE["device_id"],
            "label": DEVICE["label"],
            "place": DEVICE["place"],
            "latest": latest,
            "samples": n,
            "comfort_ratio": (comfortable / n) if n else None,
            "temp_range": None if not temps else {"min": min(temps), "max": max(temps)},
            "mq135_index_range": None if not indexes else {"min": min(indexes), "max": max(indexes)},
            "lux_range": None if not luxs else {"min": min(luxs), "max": max(luxs)},
        }],
        "alerts": alerts,
        "total_samples": n,
        "outdoor_compare": compare,
        "outdoor_license": _OUTDOOR.get("license"),
        "outdoor_attribution": _OUTDOOR.get("weather_attribution"),
    }


def series_for(rows: list[dict]) -> list[dict]:
    keys = [
        "recv_ts", "seq", "temp_c", "rh_pct", "pressure_hpa",
        "lux", "mq135_adc", "mq135_index", "mcu_temp_c",
    ]
    seq = sorted(rows, key=lambda r: (r.get("recv_ts") or "", r.get("seq") or 0))
    return [{k: r.get(k) for k in keys} for r in seq]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            return self._api(parsed)
        if parsed.path in ("/", "/app"):
            self.send_response(302)
            self.send_header("Location", "/app/")
            self.end_headers()
            return
        return super().do_GET()

    def _api(self, parsed):
        path = parsed.path.rstrip("/")
        if path == "/api/meta":
            body = {
                "title": "校园 / 室内环境监测套件",
                "disclaimer": "这是选题 B 的样品原型，三条候选之一，不是已确认的毕设题目。",
                "data_note": "看板主数据是 Atlas 提供的 STM32 模拟 USART/CSV 流（2026-08-03 12:00–12:30，Asia/Shanghai），以及同目录的兰州 Open-Meteo 小时对照。全部为模拟或模式数据。云电脑没有实物板，实机未验证，未烧录。",
                "protocol": "Atlas STM32 模拟 USART（空格分隔 key=value）",
                "baud_note": "Atlas 示例按常见做法标注 115200 8N1，并写明这不是已核实的板级设置。",
                "board_claimed": "STM32F4ZGT6",
                "board_inferred": "STM32F407ZGT6",
                "board_note": "完整型号为按常见命名的推断，未见实物标签，不能写成已核实。",
                "used_atlas_sample": True,
                "atlas_files": [
                    str(USART_SAMPLE.relative_to(ROOT)),
                    "data/raw/atlas/samples/stm32_sim_stream_2026-08-03T12_30min.csv",
                    "data/raw/atlas/samples/openmeteo_lanzhou_weather_2026-08-03_to_2026-08-09.csv",
                    "data/raw/atlas/samples/openmeteo_lanzhou_air_quality_2026-08-03_to_2026-08-09.csv",
                ],
                "timezone": "Asia/Shanghai",
                "nodes": [DEVICE],
                "thresholds": THRESHOLDS,
                "openmeteo_license": _OUTDOOR.get("license"),
                "openmeteo_attribution": _OUTDOOR.get("weather_attribution"),
            }
        elif path == "/api/latest":
            latest = _ROWS[-1] if _ROWS else None
            body = {"latest": {latest["device_id"]: latest} if latest else {}, "n": len(_ROWS)}
        elif path == "/api/summary":
            body = analyze(_ROWS)
        elif path == "/api/series":
            qs = parse_qs(parsed.query)
            device = (qs.get("device") or [DEVICE["device_id"]])[0]
            rows = [r for r in _ROWS if r.get("device_id") == device] or _ROWS
            body = {"device_id": device, "points": series_for(rows)}
        else:
            self.send_error(404, "unknown api")
            return
        raw = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description="选题 B：Atlas 模拟流接入 + 本地看板")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--usart", type=Path, default=USART_SAMPLE)
    args = parser.parse_args()

    global _ROWS, _OUTDOOR
    if not args.usart.exists():
        print("找不到 Atlas 模拟 USART 样本: %s" % args.usart, file=sys.stderr)
        return 1
    _ROWS = load_usart_log(args.usart)
    _OUTDOOR = load_outdoor_hourly()
    print("已载入 Atlas 模拟 USART：%s（%d 条）" % (args.usart, len(_ROWS)))
    print("已载入 Open-Meteo 对照小时序列：%d 条" % len(_OUTDOOR.get("hourly") or []))
    print("数据性质：模拟流 + 公开模式数据。实机未验证。")

    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print("看板: http://127.0.0.1:%d/app/" % args.port)
    print("看完请 Ctrl+C 结束。")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n正在停止…")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
