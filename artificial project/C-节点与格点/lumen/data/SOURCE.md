# 数据来源与截取说明（选题 C 样品）

本目录数据全部复制自 Atlas 已提供的官方/模拟小样本，未改数值，未另爬全量，未当作实机采集。

获取记录日期：2026-11-11（Asia/Shanghai）。
口径以 `atlas/选题BC-方法与数据说明.md`、`atlas/samples/样本说明.md` 与 `helix/sensing/data/ASSUMPTIONS.txt` 为准。Helix 页面只作格式与字段参考，视觉不复刻其看板。

## 1. 室内节点流（模拟，非实机）

- 文件（原样复制）：
  - `raw/stm32_sim_stream_2026-08-03T12_30min.csv`
  - `raw/stm32_sim_stream_2026-08-03T12_30min.jsonl`
- 来源：Atlas 为选题 B/C 生成的**模拟流**，文件头第一行即为「# 模拟，非实机」。
- SHA256（与 Atlas `样本说明.md` 一致）：
  - CSV `e3479f1d180d9ab79c27948505eace2c85142b0e3c00c0f400457059968916ef`
  - JSONL `e317ca3a29c48a8cbcf93db8138b083930605c046cb625d9cc799699d6a73fa1`
- 窗口：2026-08-03 12:00:00–12:30:00（Asia/Shanghai），间隔 10 秒，181 个周期，7 个通道。
- 设备占位符：`device_id=stm32-f4zg-sim-01`，`firmware_rev=sim-0.1.0`，`source=simulated`。
- **云电脑没有实物板，未烧录、未实采。** 全部数值为发明的演示值。
- 文件头写明：2026-08-03 12:00 的 Open-Meteo 兰州温度 25.8 °C、相对湿度 49%、气压 852.4 hPa 仅被当作量级线索。因此室内均值与该整点之差，是样品构造结果，不是实测房间效应。
- 板型：主人已确认是 **正点原子 STM32F407ZGT6 开发板**（2026-11-11）。具体套件与已接传感器仍未见清单；数据为模拟，未实机烧录。
- 传感器品类与总线（BME280 / BH1750 / MQ135 及逻辑总线 I2C1、ADC1）均为推断，不是已核实 BOM 或引脚表。片内温度通道 MCU_TS 是芯片外设（数据手册），但本列仍是模拟值；数据手册写明更适于相对变化，**不能当作室内气温**。
- MQ135 的 `gas_index` 由原始 ADC 按发明系数换算，`quality_flag=uncalibrated_simulated`，**不是标定 ppm**，不得与 CAMS 的 μg/m³ 做数值等同比较。
- 本流没有单独的公开数据许可证；它是格式与方法演示，不是开放数据集。

## 2. 室外公开对照（Open-Meteo，模式格点）

- 文件（原样复制）：
  - `raw/openmeteo_lanzhou_weather_2026-08-03_to_2026-08-09.csv`
  - `raw/openmeteo_lanzhou_air_quality_2026-08-03_to_2026-08-09.csv`
- SHA256（与 Atlas 一致）：
  - 气象 `820a9dce5cfea1a06bdee87adde35260ac21a7d63c385c76029f9f0cdf5b98df`
  - 空气质量 `e71471ab39a8d061d830829e4344d1d6e9a33d55ff369c9252c120231242c185`
- 请求点：约 36.06°N, 103.83°E，时区 Asia/Shanghai，2026-08-03 至 2026-08-09，各 168 条小时记录。
- 接口返回格点（不同）：
  - 气象：lat 36.098415, lon 103.89105, elevation 1525 m
  - 空气质量：lat 36.1, lon 103.80002, elevation 1525 m
- **这是兰州市区参考点的模式格点产品，不是兰大校园测站，也不是实测坐标。**
- 许可证：API 数据为 **CC BY 4.0**。须署名，展示处写明 `Weather data by Open-Meteo.com`。空气质量还须归属 **Copernicus Atmosphere Monitoring Service（CAMS）**。CSV 未写模式名称或网格间距，**不能断定具体模式或公里网格**。
- 出处：https://open-meteo.com/ ；空气质量文档 https://open-meteo.com/en/docs/air-quality-api ；历史气象 https://open-meteo.com/en/docs/historical-weather-api ；许可证说明见 Atlas `来源与许可证/Open-Meteo_许可证与条款摘录.md`。
- 免费托管 API 另有非商业与速率限制，与数据的 CC BY 4.0 不是同一层。

## 3. 对照窗口

- 室内只有半小时（12:00–12:30）。室外是 7×24 小时序列。
- **可展示整周室外作为上下文，但对照只能落在重叠的那一小时（2026-08-03 12:00 整点）。** 室外是整点小时值，不是 30 分钟内的连续曲线；本页不以插值假装室外也有 10 秒采样。

## 4. 衍生文件

- `specimen.js`：把原文结构化，供离线页面读取（通道值至多做显示用四舍五入）。计算脚本在本样品目录的 `src/extract_specimen.py`（相对 `data/SOURCE.md` 则为 `../src/extract_specimen.py`，不是选题 A 根目录的 src）。生成时已跑过；复现可用同样原文。
