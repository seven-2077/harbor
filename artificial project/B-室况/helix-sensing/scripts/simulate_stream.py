#!/usr/bin/env python3
"""校对 Atlas 模拟 USART 样本能否按协议解析。不重新发明另一套字段。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helix_env import USART_SAMPLE, load_usart_log, parse_usart_line  # noqa: E402


def main() -> int:
    rows = load_usart_log(USART_SAMPLE)
    print("解析 %s ：%d 条" % (USART_SAMPLE, len(rows)))
    if not rows:
        return 1
    print("首条", {k: rows[0].get(k) for k in ("recv_ts", "device_id", "temp_c", "mq135_index")})
    print("末条", {k: rows[-1].get(k) for k in ("recv_ts", "device_id", "temp_c", "mq135_index")})
    # 固件骨架应能打印出与首条相同结构的 key=value 行（数值来自传感器，这里只核格式）
    with USART_SAMPLE.open(encoding="utf-8") as f:
        for line in f:
            rec = parse_usart_line(line)
            if rec:
                print("格式示例:", line.strip())
                break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
