#!/usr/bin/env python3
"""从 BART 官方固定链接重新下载静态 GTFS，并核对体积。

官方 permalink（会 307 到带版本号的 zip）：
https://www.bart.gov/dev/schedules/google_transit.zip

本环境中部分官网 HTML 页面会返回 403，但上述 zip 可直接下载。
若日后 Atlas 提供带来源说明的小样本，不必再跑本脚本，
改用：python3 scripts/prepare.py --gtfs <Atlas样本目录或zip>
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

PERMALINK = "https://www.bart.gov/dev/schedules/google_transit.zip"
USER_AGENT = "helix-bishe-sample/1.0 (academic prototype; +local offline use)"

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "raw" / "bart_gtfs.zip"


def main() -> int:
    parser = argparse.ArgumentParser(description="下载官方 BART 静态 GTFS")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="保存路径")
    parser.add_argument("--url", default=PERMALINK, help="下载 URL，默认官方 permalink")
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(args.url, headers={"User-Agent": USER_AGENT})
    print(f"GET {args.url}", file=sys.stderr)
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
        final_url = resp.geturl()
        last_mod = resp.headers.get("Last-Modified", "")
    args.out.write_bytes(data)
    print(f"保存: {args.out}")
    print(f"最终 URL: {final_url}")
    print(f"Last-Modified: {last_mod}")
    print(f"字节数: {len(data)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
