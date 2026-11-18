# 数据来源与截取说明（选题 B 样品）

本目录数据全部复制自 Atlas 已提供的模拟小样本，未改数值，未另爬全量，未当作实机采集。

获取记录日期：2026-11-11（Asia/Shanghai）。
口径以 `atlas/选题BC-方法与数据说明.md`、`atlas/samples/样本说明.md` 与 `helix/sensing/data/ASSUMPTIONS.txt` 为准。Helix 页面只作字段与注意事项的格式参考，视觉不复刻其课件风看板。本样品主效是节点产品与数据链路，**不用室外格点做对照展**。

## 1. 室内节点流（模拟，非实机）

- 文件（原样复制）：
  - `raw/stm32_sim_stream_2026-08-03T12_30min.csv`
  - `raw/stm32_sim_stream_2026-08-03T12_30min.jsonl`
  - `raw/stm32_sim_usart_lines_example.txt`
- 来源：Atlas 为选题 B/C 生成的**模拟流**，文件头第一行即为「# 模拟，非实机」。
- SHA256（与 Atlas `样本说明.md` 一致）：
  - CSV `e3479f1d180d9ab79c27948505eace2c85142b0e3c00c0f400457059968916ef`
  - JSONL `e317ca3a29c48a8cbcf93db8138b083930605c046cb625d9cc799699d6a73fa1`
  - USART `4688096b54cea43ccc4cd9f27129bdd2de51cb952431698a7d57e681e1780382`
- 窗口：2026-08-03 12:00:00–12:30:00（Asia/Shanghai），间隔 10 秒，181 个周期，7 个通道。USART 示例为一行一个周期，字段与长表对应。
- 设备占位符：`device_id=stm32-f4zg-sim-01`，`firmware_rev=sim-0.1.0`，`source=simulated`。
- **云电脑没有实物板，未烧录、未实采。** 全部数值为发明的演示值。串口行也不是实机抓包。
- 文件头写明：2026-08-03 12:00 的 Open-Meteo 兰州温湿度气压仅被当作生成时的量级线索。本页不以室外格点作对照主效，故未复制 Open-Meteo CSV。
- 板型：主人已确认是 **正点原子 STM32F407ZGT6 开发板**（2026-11-11）。具体套件与已接传感器仍未见清单；数据为模拟，未实机烧录。
- 传感器品类与总线（BME280 / BH1750 / MQ135 及逻辑总线 I2C1、ADC1）均为推断，不是已核实 BOM 或引脚表。片内温度通道 MCU_TS 是芯片外设（数据手册），但本列仍是模拟值；数据手册写明更适于相对变化，**不能当作室内气温**。
- MQ135 的 `gas_index` 由原始 ADC 按发明系数换算，`quality_flag=uncalibrated_simulated`，**不是标定 ppm**。
- 115200 8N1 是实践习惯，不是已核实的板级设置。
- 本流没有单独的公开数据许可证；它是格式与方法演示，不是开放数据集。

## 2. 为何不用室外对照做主图

选题 C（`../c-sensing/`，「节点与格点」）已经把同一条模拟流与 Open-Meteo 兰州格点对照做成样品。选题 B 补交的是「采集 → 存储 → 分析 → 产品」的套件原型，主效放在节点产品、串口入库与给管理者看的室况，避免做成 C 的第二份对照展。若以后要接公开气象，许可证为 CC BY 4.0，须写明 Weather data by Open-Meteo.com，空气质量还须归属 Copernicus Atmosphere Monitoring Service（CAMS），且格点不是校园测站。

## 3. 衍生文件

- `specimen.js`：把原文结构化，供离线页面读取（通道值至多做显示用四舍五入），并收入全部 USART 示意行。
- 复现：`python3 src/extract_specimen.py`
