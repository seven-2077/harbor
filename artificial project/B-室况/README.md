# 室况

这是 2026-11-11 的科研方向样品，不是已经确定的毕业设计题目。

正点原子 STM32F407ZGT6 多传感器采集、数据链路与交互可视化的小原型，形态按校园或室内环境监测套件来想。开发板已确认在本人手里；这里的固件与传感数据都是模拟，没有在实机上烧录或采集。

## 怎么打开

- 可视化页面：用浏览器直接打开 `lumen/index.html`（`file://` 即可）。海报在 `lumen/poster.png` 和 `lumen/poster.pdf`。
- 采集接入原型：在 `helix-sensing/` 目录执行 `python3 scripts/serve.py`，然后打开 http://127.0.0.1:8766/app/ 。
- 可稍后烧录的固件骨架在 `helix-sensing/firmware/`。方法与数据说明：`atlas/选题BC-方法与数据说明.md`。候选说明：`folio/候选方向.md`。

对照用的兰州气象与空气质量来自 Open-Meteo（CC BY 4.0），许可证见 `atlas/来源与许可证/`。

## 项目结构

- `folio/` 候选方向、规范与时间节点、相近文献说明
- `atlas/` 方法与数据说明、STM32 模拟采样与 Open-Meteo 小样本、许可证摘录
- `helix-sensing/` 采集接入原型：`app/` 页面，`scripts/` 启动与模拟流，`firmware/` 可烧录骨架，`data/` 模拟数据
- `lumen/` 可视化页面与海报
