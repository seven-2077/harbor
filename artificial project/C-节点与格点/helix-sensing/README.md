# 选题 B · 校园 / 室内环境监测套件（样品）

这是选题 B 的样品原型，三条候选之一，**不是已确认的毕设题目**。

产品形态：在教室或实验室放一个多传感器节点，STM32 按固定协议把温湿度、气压、照度和气体示意指数从串口送出；电脑接入后做本地存储、舒适度分析，并可与公开的室外气象小时值对照。要讲的是「采集 → 存储 → 分析 → 给管理员看的产品」，不是一堆无场景的读数。

**模拟已在本盒子上跑通；实机未验证。** 云电脑上没有这块板，未编译、未烧录、未插真实串口。

成果目录：`helix-sensing/`

---

## 如何启动（已在本盒子上跑通）

环境：Python 3.10+（本盒子验证时为 Python 3.13.5）。只需标准库，不必 `pip install`。

在终端中逐字复制：

```bash
cd helix-sensing
python3 scripts/serve.py
```

浏览器打开：

```text
http://127.0.0.1:8766/app/
```

服务会只读载入本目录拷贝的 Atlas 模拟 USART 样本（原始文件在 `atlas/samples/`，此处未改原文），以及 Open-Meteo 兰州小时对照。

验证（另开一个终端，服务保持运行时）：

```bash
curl -sI http://127.0.0.1:8766/app/
curl -sI http://127.0.0.1:8766/api/meta
curl -s http://127.0.0.1:8766/api/meta | python3 -c "import sys,json; m=json.load(sys.stdin); print(m['disclaimer']); print(m['used_atlas_sample'], m['board_inferred'])"
curl -s http://127.0.0.1:8766/api/latest | python3 -c "import sys,json; d=json.load(sys.stdin); print('n', d['n']); print(list(d['latest']))"
curl -s http://127.0.0.1:8766/api/summary | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['total_samples'], d.get('outdoor_compare',{}).get('outdoor_time'))"
python3 scripts/simulate_stream.py
```

看完后，在运行 `serve.py` 的那个终端按 `Ctrl+C` 停掉服务，不要留下占端口的进程。

选题 A 的启动方式在上一级 [../README.md](../README.md)，端口是 8765，不要和本页的 8766 混用。

---

## 数据来源与许可证

**使用了 Atlas 为选题 B/C 准备的模拟样本**（只读拷贝到 `data/raw/atlas/samples/`，未改 atlas 原文件）。

| 文件 | 性质 |
| --- | --- |
| `stm32_sim_usart_lines_example.txt` | Atlas 模拟 USART 行（看板主数据）。2026-08-03 12:00–12:30（Asia/Shanghai），间隔 10 秒，设备 `stm32-f4zg-sim-01`。文件头标明「模拟，非实机」。 |
| `stm32_sim_stream_2026-08-03T12_30min.csv` / `.jsonl` | 同一窗口的长表 / JSONL，字段相同。 |
| `openmeteo_lanzhou_weather_2026-08-03_to_2026-08-09.csv` | 兰州小时气象，用作室外对照。 |
| `openmeteo_lanzhou_air_quality_2026-08-03_to_2026-08-09.csv` | 兰州小时空气质量（同窗口对照）。 |

Open-Meteo：Atlas《数据清单》记为 **CC BY 4.0**，须署名。页面与接口中写有 “Weather data by Open-Meteo.com”。这是模式格点，不是校园气象站实测。

STM32 流本身是模拟格式示例，没有公开数据许可证；数值是发明的演示值。Atlas 注释写明：2026-08-03 12:00 的 Open-Meteo 温度/湿度/气压只被当作量级线索。

串口行格式（与 `firmware/include/helix_env_protocol.h`、`firmware/src/main.c` 的 `printf` 一致）：

```text
DEV=stm32-f4zg-sim-01 TS=2026-08-03T12:00:00+08:00 SEQ=0 BME280_T_C=26.66 BME280_RH_PCT=46.79 BME280_P_HPA=852.61 BH1750_LUX=273.0 MQ135_ADC=1474 MQ135_INDEX=26.01 MCU_TS_C=33.45 SRC=simulated
```

MQ135_INDEX **不是**标定 ppm。细节见 `data/ASSUMPTIONS.txt`。

---

## 板型：已确认与仍未知

- 已确认：主人于 2026-11-11 说明，这是 **正点原子 STM32F407ZGT6 开发板**。
- 仍未知：具体是哪一套件、已接哪些传感器；未见原理图。引脚与传感器字段仍按常见 F407 开发板 + Atlas 模拟流做假设，须对照该套件再核对。
- 实机未烧录，云电脑上没有这块板。

固件骨架在 `firmware/`，可稍后在有板子的电脑上接着写驱动并烧录。本盒子只提供源码，**不声称已经实机跑通**。

---

## 已在盒子上跑通的功能（事实）

1. `python3 scripts/simulate_stream.py` 能解析 Atlas USART 样本（181 条）。
2. `python3 scripts/serve.py` 在 `127.0.0.1:8766` 提供页面与 `/api/meta`、`/api/latest`、`/api/summary`、`/api/series`；已用 `curl` 确认可访问。验证后停掉服务。
3. 页面可看：产品说明、最新模拟读数、温湿度与气体示意指数/照度曲线、舒适区比例，以及同一小时与 Open-Meteo 兰州格点的量级对照。页首标明模拟、实机未验证、三条候选之一。
4. 固件骨架的打印格式与 Atlas USART 行的 key 集合一致（对照源码，不是实机抓包）。

---

## 限制

- 室内读数全部是模拟。不能当作兰州某教室的实测，也不能当作传感器校准数据。
- 实机未验证：未见到板子丝印，未编译镜像，未烧录，未接 USB 转串口。
- 室外对照是 Open-Meteo 模式格点的整点小时，不是校园站，也不能用来给 MQ135 定标。
- 拷贝样本时 Atlas 的 `选题BC-方法与数据说明.md` 尚未出现在目录中；若稍后补上，应以那份说明为准核对引脚与字段。
- 页面不是最终视觉设计。未写论文，未定题。
