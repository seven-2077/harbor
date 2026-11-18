# 数据来源与截取说明

本目录的数据全部来自 Atlas 已提供的官方公开样本，未另起数据包，未爬取不明授权站点，未使用全量客流。

获取日期（记录）：2026-11-11（Asia/Shanghai）。
原始包来自 Atlas。制作过程中 Atlas 的 `样本说明.md`、`数据清单.md` 与 `来源与许可证/` 已补齐，下列出处已与之核对。请同时参阅那些文件。

## 1. 静态时刻表（主图）

- 机构：MTA New York City Transit
- 产品：官方 Regular Subway GTFS（静态时刻表，不含大部分临时调整；本份 feed_version 含长期补充）
- 官方入口：https://www.mta.info/developers
- 常用官方下载地址：https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip
- 本样品所用文件：Atlas 保存的 `gtfs_subway.zip` / 解压目录 `atlas/tmp/gtfs_subway/`
- `feed_info.txt`：
  - feed_publisher_name：MTA New York City Transit
  - feed_publisher_url：https://www.mta.info/
  - feed_start_date：20261101
  - feed_end_date：20270515
  - feed_version：20261028-fall-2026-pick-with-long-term-supplements
- 许可证：MTA data feed terms and conditions  
  https://www.mta.info/developers/terms-and-conditions  
  更新标注为 Mar 13, 2024。文本誊本见 `licenses/MTA-data-feed-terms-and-conditions.txt`。  
  要点（非正式摘要，以官方页面为准）：数据可供使用与转存；不得声称经 MTA 授权或由 MTA 服务器直接提供；不得声称数据准确、完整或及时；不得修改或删除数据本身，但可以使用部分而非全部数据；不得使用 MTA 标志、地图、符号等知识产权（另需许可）。数据按 as-is 提供。
- 截取范围（`data/raw/` 中的 GTFS 文件）：
  - 仅 route_id 为 `7`（Flushing Local）与 `7X`（Flushing Express）
  - 仅 service_id = `Weekday`
  - 对应营运日 **2026-11-11（星期三）**：该日落在 calendar 的 Weekday 有效期内，且 `calendar_dates.txt` 当日无例外
  - 仅上述车次用到的 `stop_times`、车站（含 parent station）与 shapes
  - 完整复制 `agency.txt`、`feed_info.txt`、`calendar.txt`、`calendar_dates.txt`（文件本身很小，便于核对）
  - 字段值未改写；只是选用子集
- 未使用：实时 GTFS-RT、其他线路、其他服务日、全网 stop_times。

## 2. 小时进站量（辅图，日期不同）

- 产品：MTA Subway Hourly Ridership（Beginning 2025），MTA 发布于 OPEN-NY / data.ny.gov（数据集 5wq4-mkjj）
- 官方页：https://data.ny.gov/Transportation/MTA-Subway-Hourly-Ridership-Beginning-2025/5wq4-mkjj
- Atlas 说明：完整 8 月文件取自第三方按月镜像 transitlab.nyc（声明镜像自官方表），再派生本周汇总；不是官方全量 CSV 的直接切片。
- Atlas 样本：
  - `atlas/samples/subway_hourly_ridership_2026-08.parquet`（transitlab 2026-08 月度原文件）
  - `atlas/samples/subway_hourly_ridership_2026-08-03_to_2026-08-09_subway_hourly_totals.csv`（Atlas 派生：从上述 parquet 抽出 08-03 至 08-09、仅 subway，按小时+综合体汇总票种）
  - `atlas/samples/subway_hourly_ridership_times_sq_611_2026-08-03_raw.csv`（同一 parquet 中 Times Square 综合体单日、票种原行）
- 本目录截取：
  - `raw/ridership_7_complexes_hourly_totals_2026-08-03_to_2026-08-09.csv`：只保留 7 号线 22 个车站所对应的综合体行，数值未改
  - `raw/subway_hourly_ridership_times_sq_611_2026-08-03_raw.csv`：原样复制
- 日期范围：2026-08-03 至 2026-08-09。默认展示 2026-08-03（星期一）。
- **不是** 2026-11-11 的进站量，也不可当作本份秋冬季时刻表当日客流。
- 统计单位：车站综合体（station complex）进站量。Times Sq、Grand Central、5 Av / Bryant Park、74 St-Broadway、Court Sq、Queensboro Plaza 等综合体包含其他线路，不能记作 7 号线独有。
- 许可证：OPEN-NY Terms of Use（非独占、可撤销的使用许可）。该数据集官方概述写明 “Limitations of Data Use: There are no limitations on the data at this time.” 进站量为估计值，官方称与提交董事会的数字相差约在 1% 以内，且可能因迟到交易而修订。

## 3. 衍生文件

- `timetable.js` / `timetable.meta.json`：由上述原文计算得到的可视化用结构，计算方式见主页面与 README。
- 生成脚本：`../src/extract_sample.py`、`../src/extract_ridership.py`。
