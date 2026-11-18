# 时刻的坡度 — 方向样品

这是一份**方向样品**，不是已经确定的毕业设计题目，也不代表唯一候选。它沿着「公开城市轨道交通（或铁路）时空数据的交互式可视化与分析」做成，用来看见一条完整的数据链路：采集 → 存储 → 计算 → 分析 → 价值。

主件是可交互页面，海报是同一主题的静态展板。作者向：Seven（何谭昕）。设计署名：Lumen。数据以 Atlas 提供的官方公开样本为准。

## 如何打开

单机即可，不依赖网络 CDN。字体、脚本与数据都在本目录。

**推荐：直接用浏览器打开主件**

- 双击 `index.html`，或用浏览器打开该文件（`file://` 即可）。
- 海报原件是 `poster.html`；交付用的锁字静态图是 `poster.png`（以及 `poster.pdf`，若已生成）。

**可选：本地静态服务**（不是必须）

在本目录执行：

```bash
python3 -m http.server 8765
```

然后访问 `http://127.0.0.1:8765/index.html`。

交互：在马雷图上拖曳读取某一时刻；悬停一条斜线查看该趟车的表定到发；点击左侧站名查看该站间隔与 8 月进站量。左右方向键可按分钟移动时间刷。

## 用了哪份数据（来自 Atlas）

未另起数据包。来源细节见 `data/SOURCE.md`。

1. **静态时刻表（主图）**  
   MTA New York City Transit 官方 Regular Subway GTFS。Atlas 文件：`atlas/tmp/gtfs_subway/` 与 `atlas/samples/gtfs_subway.zip`。  
   `feed_version`：`20261028-fall-2026-pick-with-long-term-supplements`（有效期 2026-11-01 至 2027-05-15）。  
   官方入口：https://www.mta.info/developers  
   常用下载地址：https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip  
   **许可证**：MTA data feed terms and conditions（https://www.mta.info/developers/terms-and-conditions）。誊本在 `data/licenses/`。不得使用 MTA 标志、地图或线路符号；本样品未使用。数据按 as-is 提供，不声称准确、完整或及时。  
   **截取**：仅 `7`（Flushing Local）与 `7X`（Flushing Express），`service_id = Weekday`，营运日 **2026-11-11（星期三）**——该日在 Weekday 有效期内且无 calendar_dates 例外。字段值未改写。原文子集在 `data/raw/`。

2. **小时进站量（辅图，日期不同）**  
   MTA Subway Hourly Ridership: Beginning 2025（data.ny.gov / `5wq4-mkjj`）。MTA 数据经 OPEN-NY 发布。Atlas 使用的 8 月完整月文件来自 transitlab.nyc 的按月镜像，再派生 2026-08-03 至 08-09 的车站综合体小时合计，以及 Times Square 综合体 2026-08-03 票种原行。  
   本目录只截取 7 号线 22 站对应综合体。  
   **许可证**：OPEN-NY Terms of Use；该数据集官方概述写明暂无额外使用限制。进站量为估计值，可能修订。  
   **务必分开读**：进站量不是 2026-11-11 的客流，也不可当作本份秋季 GTFS 的当日班次对照。Times Sq、Grand Central 等综合体包含其他线路，不能记作 7 号线独有。不要把 `transfers` 再加进 `ridership`。

获取记录日期：2026-11-11（Asia/Shanghai）。

## 哪些是算出来的，哪些是设计解读

**由数据算出（事实）**

- 马雷图上的每一条斜线：由该趟车 `stop_times` 的到达 / 出发时刻按站序连接。
- 水平短线：仅当到达时刻与出发时刻不同，表示时刻表写出的停站时分。
- 班次密度：按列车始发时刻所在小时计数（分方向，快车再单列叠段）。
- Grand Central 发车间隔：同一方向相邻两次出发时刻之差。
- 两端表定旅行时分：只统计 Flushing-Main St 与 34 St-Hudson Yards 都出现的车次，用始发站出发到终到站到达。
- 7X 开行窗口：该路线、该方向全部车次的最早与最晚始发时刻。
- 东向所有 Local 未写入 52 St、69 St：直接来自站序，未作修正。
- 进站量柱：官方综合体小时 / 日合计，日期为 2026-08-03–08-09。

**推断或设计解读（已在画面标明）**

- 时间刷上的列车位置：相邻表定到发之间的时间线性插值，不是实时定位，也不是实测轨迹。
- 东河带：依据 Vernon Blvd-Jackson Av 与 Grand Central-42 St 的坐标划分，中间无本线车站。不是官方工程图。
- 6:30–9:30、16:00–19:30 的薄纱：设计用的时段示意，不是官方高峰定义。
- 纵轴里程：车站在 shape `7..S97R` 上的最近顶点投影，不是轨旁里程碑。
- 初始时刻 08:30：设计取景，为了落在西向快车窗口内。
- 中文标题、说明与译写：设计文案，不是官方译名，也不是已定题目。

## 字体

本地自宿，可免费商用（SIL Open Font License）：

- IBM Plex Sans（IBM）
- Newsreader（The Newsreader Project Authors）
- Noto Serif SC 子集（Google）

许可证副本在 `data/licenses/`。

## 目录

- `index.html` — 可交互主成品
- `poster.html` — 海报排版原件
- `poster.png` / `poster.pdf` — 锁字静态海报
- `data/` — 小样本、来源说明、衍生数据
- `fonts/` — 本地字体
- `assets/` — 样式与脚本（自制 SVG，无 Chart.js / 默认 Plotly / ECharts 皮肤）
- `review/` — 自查截图
- `src/` — 从 Atlas 原文生成截取与衍生文件的脚本

## 复现截取（可选）

```bash
python3 src/extract_sample.py
python3 src/extract_ridership.py
```

需能读到 Atlas 目录中的 GTFS 与客流样本。
