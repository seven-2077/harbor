# Atlas 交付入口（给 Helix / Lumen / Kiro）

本目录是科研部 2026-11-11 夜间任务的**数据与方法样品**，不是已选定的毕设题目。三条选题都只是候选。采集时区：Asia/Shanghai（UTC+8）。

| 选题 | 本目录里看什么 | 样品 |
| --- | --- | --- |
| **A** 公开城市轨道交通时空数据的交互式可视化与分析 | 本 README 下文 + `数据清单.md` + `方法路径.md` | `samples/` 中 GTFS、客流 parquet/CSV |
| **B / C** STM32 多传感器采集（及与公开环境数据对照） | `选题BC-方法与数据说明.md` | `samples/` 中模拟采样流、兰州 Open-Meteo 空气质量与气象 |

不要改主人的笔记仓库，不要把其中任何一条写成已定题目。本目录只写入 `atlas/`。`tmp/` 是采集时的草稿（解压、镜像副本），验收以 `samples/`、`来源与许可证/` 和上述说明文件为准。

---

## 选题 A：选了哪些数据、样本在哪、怎么用

主推的是**同一城市、可拼在一起的一组互补数据**（不是两个无关城市）：

1. **空间网络**：纽约大都会运输署（MTA）地铁静态 GTFS（Regular）。官方 zip 已下载到 `samples/gtfs_subway.zip`（5,606,305 字节）。服务日历为 2026-11-01 至 2027-05-15。
2. **时间客流**：MTA Subway Hourly Ridership（官方发布于 data.ny.gov）。全量未整包下载。样品用 2026-08 整月 parquet（第三方 transitlab 按月镜像，源声明为官方表）以及由它派生的一周汇总 CSV。另有 8 行官方 SODA 原样校核文件，证明官方接口可读。

建议 Helix / Lumen **先打开这些文件**即可做最小原型，不必先拉全量：

- 地图与小时曲线：`samples/subway_hourly_ridership_2026-08-03_to_2026-08-09_subway_hourly_totals.csv`（约 5.5 MB，70,148 行，已按小时+车站把票种加总）+ `samples/subway_station_complex_points_from_2026-08_ridership.csv`（424 个复合体点位）。
- 线路与站形：解压 `samples/gtfs_subway.zip`。
- 看原始票种结构：`samples/subway_hourly_ridership_times_sq_611_2026-08-03_raw.csv`。
- 字段、抽样口径、校验和：`samples/样本说明.md`。
- 来源与条款摘录：`来源与许可证/`。

重下脚本：`samples/download_samples.sh`。

### 选题 A 必须知道的限制

- **日历错位（事实）**：当前官方 Regular GTFS 从 2026-11-01 起；客流样品是 2026-08。不要把这份 GTFS 的 `stop_times` 当成 8 月时刻表。车站坐标层仍可作底图，但“8 月与 11 月线网完全相同”只是推断。
- **进站 ≠ 出行**：`ridership` 是进站估计，须按小时+车站把各票种相加；`transfers` 已包含在 `ridership` 里，不可再加。
- **连接键**：客流 `station_complex_id` 对应官方车站表 `complex_id`，再经 `gtfs_stop_id` 接到 GTFS 父站。官方车站全表（`39hk-dx4f`，496 行）今晚已用官方接口读到，但本机对 data.ny.gov 的 curl 为 403，未把转抄件冒充官方原文件放进 samples。请按 `样本说明.md` 自行下载。
- **单机**：周汇总与整月 parquet（约 4.7 MB，pandas 载入约 200 多 MB 内存）适合普通笔记本。不要用 pandas 一次性读入官方全量 CSV（Beginning 2025 官方元数据为 4,740 万行量级）。此类分析一般不需要 GPU；笔记本 8 GB 显存与本任务无关，瓶颈在内存与磁盘。
- **data.ny.gov**：本执行环境对该域 curl 返回 403；WebFetch 可读。换网络后再用官方 SODA。

### 选题 A 许可证注意（不要写成标准 CC 名称）

- GTFS：MTA *data feed terms and conditions*（自定义条款，页标 Updated Mar 13, 2024）。可下载后放到非 MTA 服务器再分发或做应用；可用子集，但不要改写或删除原始取值；不要让应用直接从 MTA 服务器给最终用户供数；不要未经许可使用 MTA 标志/官方地图；不要声称数据准确、完整或实时。摘录见 `来源与许可证/MTA_data_feed_terms_and_conditions摘录.md`。
- 小时客流：发布在 OPEN-NY（data.ny.gov）。**数据集条目级许可证字段未给出**（catalog.data.gov 的 JSON-LD 为 `"license": null`）。门户适用《OPEN-NY Terms of Use》（Last Modified: March 8, 2013），摘录见同目录。不得自行填成 CC-BY。客流月文件若用 transitlab 镜像，成品上同时注明 MTA / data.ny.gov 与 transitlab.nyc。

---

## 选题 B / C 一句话入口

板子已由主人确认为 **正点原子 STM32F407ZGT6 开发板**（2026-11-11）。具体套件名称与已接外设仍未见清单。云电脑上没有板，**没有实机数据**。方法、推荐存储格式、模拟流和一份可下载的公开对照数据见 `选题BC-方法与数据说明.md`。模拟文件头已标明「模拟，非实机」。
