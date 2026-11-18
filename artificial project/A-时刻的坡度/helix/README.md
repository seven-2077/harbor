# 城市轨道交通时空数据 · 最小可运行样品原型

这是选题 A 的样品原型，三条候选之一，**不是已确认的毕设题目**。不要把它当成已经定题的实现。

选题 A：公开城市轨道交通（或铁路）时空数据的交互式可视化与分析。简报 01:45 补充后，轨道交通不再是唯一主推，本目录同时收选题 A，并另开选题 B（见下）。

成果目录：`helix/`

## 本目录里的两份样品（都只是候选）

| 选题 | 路径 | 启动（逐字复制） |
| --- | --- | --- |
| 选题 A · 轨道交通时空数据 | 本目录根下的 `app/`、`scripts/`、`data/` | 见下方「如何启动」：在 helix 根目录执行 `python3 scripts/prepare.py` 后，用 `python3 -m http.server 8765 --bind 127.0.0.1`，打开 http://127.0.0.1:8765/app/ |
| 选题 B · 校园/室内环境监测套件 | [`sensing/`](sensing/README.md) | 见 [sensing/README.md](sensing/README.md)：在 `sensing/` 目录执行 `python3 scripts/serve.py`，打开 http://127.0.0.1:8766/app/ |

两条都不是已确认的毕设题目。选题 B 在云电脑上只有模拟流与固件骨架，**实机未验证**。

---

## 如何启动（已在本盒子上跑通）

环境：Python 3.10+（本盒子验证时为 Python 3.13.5）。只需标准库，不必 `pip install`。

在终端中逐字复制：

```bash
cd helix
python3 scripts/prepare.py
python3 -m http.server 8765 --bind 127.0.0.1
```

浏览器打开：

```text
http://127.0.0.1:8765/app/
```

不要用 `file://` 直接双击 `app/index.html`：浏览器会拦截对 JSON 的读取。必须通过上面的本地 HTTP 服务打开。

验证（另开一个终端，服务保持运行时）：

```bash
curl -sI http://127.0.0.1:8765/app/
curl -sI http://127.0.0.1:8765/app/data/meta.json
curl -sI http://127.0.0.1:8765/app/data/arrivals.json
curl -s http://127.0.0.1:8765/app/data/meta.json | python3 -c "import sys,json; m=json.load(sys.stdin); print(m['disclaimer']); print(m['service_date'], m['source']['license_name'])"
```

看完后，在运行 `http.server` 的那个终端按 `Ctrl+C` 停掉服务，不要留下占端口的进程。

若之后换用 Atlas 提供的 GTFS 小样本（zip 或已解压目录）：

```bash
cd helix
python3 scripts/prepare.py --gtfs /path/to/atlas/sample.zip --service-date 2026-11-11
python3 -m http.server 8765 --bind 127.0.0.1
```

重新下载官方 BART 当前包（permalink 指向「当下版本」，哈希可能变化，下载后需更新 `data/raw/SOURCE.txt`）：

```bash
python3 scripts/download_gtfs.py
python3 scripts/prepare.py
```

---

## 数据来源、许可证、是否用了 Atlas 样本

**没有使用 Atlas 小样本。** 开始做本原型时，`atlas/samples/` 与 `atlas/来源与许可证/` 仍为空（见 `data/raw/SOURCE.txt` 中的时间记录）。按简报允许，改用一份来源清楚、可直接下载的官方静态 GTFS。

| 项 | 内容 |
| --- | --- |
| 数据集 | BART（Bay Area Rapid Transit）官方静态 GTFS |
| 官方 permalink | https://www.bart.gov/dev/schedules/google_transit.zip |
| 本次实际文件 | https://www.bart.gov/sites/default/files/2026-10/google_transit_20260810-20270108_v03.zip |
| 文档 | https://www.bart.gov/schedules/developers/gtfs |
| 检索 / 下载时间 | 2026-11-11 01:40:22（Asia/Shanghai） |
| 原始包 Last-Modified | 2026-10-22 20:39:18 GMT（Asia/Shanghai：2026-10-23 04:39:18） |
| 原始体量 | zip 1,017,584 字节（约 994 KiB）；解压约 5.7 MiB |
| SHA256 | `838bae35002f76c217aa7350ff65e137b5d89c312c28c0a1c43ec32ab1ed6170` |
| 许可证 | [BART Developer License Agreement](https://www.bart.gov/schedules/developers/developer-license-agreement) |
| 许可证要点 | 非独占、有限、可撤销地使用 / 复制 / 再分发；须遵守协议；不得使用官方商标或官方系统图；不得主张对数据的所有权；数据按 as-is 提供。完整条文以官方页面为准。 |

原始 zip 已不足 1 MiB，因此整包保留在 `data/raw/bart_gtfs.zip`，便于核对哈希。加工时另做截取（不是删改原包）：

- 只保留轨道类线路（`route_type` 0/1/2）。本包实际保留 12 条地铁线，排除 2 条公交接驳（BridgeA / BridgeB）。
- 只展开一个服务日：**2026-11-11**（工作日，落在日历窗内，且不是例外日）。
- 地图用 50 个父站；到站时刻由月台归并到父站。

页面与 `data/processed/meta.json` 均标明来源与许可证。本原型未使用 BART 官方标志或官方系统图。

---

## 目录

```text
helix/
  README.md
  requirements.txt          # 声明无第三方依赖
  scripts/prepare.py        # GTFS → JSON，可复现
  scripts/download_gtfs.py  # 按官方 permalink 再下载
  data/raw/bart_gtfs.zip
  data/raw/SOURCE.txt
  data/processed/*.json     # 加工结果
  app/index.html            # 交互页面
  app/app.js
  app/style.css
  app/data/                 # 与 processed 同步的一份，供页面读取
  app/vendor/leaflet/       # 已落地的 Leaflet 1.9.4，不走 CDN
```

---

## 已在盒子上跑通的功能（事实）

下列各项已在本盒子上实际执行，不是推断：

1. `python3 scripts/prepare.py` 成功跑完，写出 `data/processed/` 并同步到 `app/data/`。
2. 加工结果（服务日 2026-11-11）：50 座车站、6 条线路组（Yellow / Orange / Green / Red / Blue / Grey）、12 条轨道 route、1021 趟车、15019 条到站记录。
3. 用 `python3 -m http.server 8765 --bind 127.0.0.1` 从本目录启动后，以 `curl` 确认 `/app/`、`/app/data/meta.json` 等可访问（见下方「本次验证记录」）。验证后已停掉该临时进程。
4. 页面功能已实现并可随上述服务打开：
   - 线路 / 车站地图（本地 Leaflet，无在线底图瓦片，可离线显示折线与车站）。
   - 按线路筛选。
   - 点击车站查看服务时段与当天到站时刻。
   - 分析视图：各线班次数柱状图、行车间隔表、所选线路的时空图（车站顺序 × 时刻）。
   - 页首标明数据来源与许可证，并写明「这是选题 A 的样品原型，三条候选之一，不是已确认的毕设题目」。
   - 若 Leaflet 未加载，车站列表、到站时刻与分析表仍可用。

时刻均为 GTFS 中的 **America/Los_Angeles 计划时刻**，不是北京时间，也不是实时到站。超过 24:00 的时刻表示跨过午夜的车次。

---

## 限制（尚未做，或需要说明的观察）

- **不是定题，也不是完整系统。** 单机、一个服务日、一份小体量官方 GTFS。没有实时 GTFS-RT、没有乘客量、没有集群或 GPU。
- **未接入 Atlas 样本。** 脚本已预留 `--gtfs` 参数，但切换后需要重新检查服务日、线路命名与页面文案中的机构名是否仍适用。纽约地铁等更大体量样本可能要把到站 JSON 再拆细，本原型未做这一步。
- **地图没有街道底图。** 这是有意为之，避免依赖在线瓦片，也避免误用官方系统图。因此这是线路几何 + 车站位置，不是导航图。
- **间隔与时空图是对计划时刻的简单统计。** 行车间隔取该方向第一站发车时刻的间隔；时空图的站序取该方向当天停站最多的一趟作为参考，短交路可能看起来不完整。这不是官方运行图，也不能当成实际运行准点率。
- **已观察到的数据事实（不是本脚本改出来的）：** `feed_info.txt` 的日期窗（2026-01-12 至 2026-08-30）与 zip 文件名 / `calendar.txt`（2026-08-10 至 2027-01-08）不一致，服务日判定以日历为准。另，Yellow-N（route_id=2）当天有 12 趟的 `direction_id` 与该线主体方向不一致，分析表按原始字段分列。
- **页面不是最终视觉设计。** 只要求能用、清晰、标清来源。
- **未写论文或开题报告。**

---

## 本次验证记录

验证时间：见仓库内文件时间戳及下方启动时的当场记录（Asia/Shanghai）。处理脚本与 HTTP 探测的具体命令和输出写在验收过程中，并已将可复制的启动命令固定到本节「如何启动」。
