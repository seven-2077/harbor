# 时刻的坡度

这是 2026-11-11 的科研方向样品，不是已经确定的毕业设计题目。

公开城市轨道交通（或铁路）时空数据的交互式可视化与分析，强调可分析、可交互，而不是纯地图演示。

## 怎么打开

- 可视化页面：用浏览器直接打开 `lumen/index.html`（`file://` 即可）。海报在 `lumen/poster.png` 和 `lumen/poster.pdf`。
- 最小可运行原型：在 `helix/` 目录执行 `python3 -m http.server 8765 --bind 127.0.0.1`，然后打开 http://127.0.0.1:8765/app/ 。不要直接用 `file://` 打开 `helix/app/index.html`，浏览器会拦截 JSON。
- 数据小样本与许可证：`atlas/`。候选说明：`folio/候选方向.md`。

数据来自公开的 MTA GTFS 与客流样本，许可证见 `atlas/来源与许可证/`。
