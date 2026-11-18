/**
 * Atlas / Helix 共用的 STM32 模拟串口文本协议（与 samples 中 USART 行一致）
 *
 * 一行一个采样周期，UTF-8，空格分隔的 key=value，行结束 \r\n。
 * 以 '#' 开头的行是注释，接入层忽略。
 *
 * 示例（来自 Atlas 模拟样本，不是实机日志）：
 * DEV=stm32-f4zg-sim-01 TS=2026-08-03T12:00:00+08:00 SEQ=0
 * BME280_T_C=26.66 BME280_RH_PCT=46.79 BME280_P_HPA=852.61
 * BH1750_LUX=273.0 MQ135_ADC=1474 MQ135_INDEX=26.01 MCU_TS_C=33.45 SRC=simulated
 *
 * 字段：
 *   DEV            节点编号
 *   TS             ISO 8601 时间（建议带时区）。若板端无 RTC，可写 TS=UNSYNCED，由主机打时间戳
 *   SEQ            上电后的样本序号
 *   BME280_T_C     温度 °C
 *   BME280_RH_PCT  相对湿度 %
 *   BME280_P_HPA   气压 hPa
 *   BH1750_LUX     照度 lux
 *   MQ135_ADC      12 位 ADC 原始码（未校准）
 *   MQ135_INDEX    由原始码换算的示意指数，不是标定 ppm
 *   MCU_TS_C       片内温度（更适于相对变化）
 *   SRC            simulated / device 等来源标记
 *
 * 物理层：按常见做法假设 USART1 115200 8N1，PA9=TX、PA10=RX。
 * Atlas 已写明该波特率不是已核实的板级设置。
 */

#ifndef HELIX_ENV_PROTOCOL_H
#define HELIX_ENV_PROTOCOL_H

#define HELIX_ENV_BAUD          115200
#define HELIX_ENV_SAMPLE_MS     10000u  /* Atlas 样本间隔为 10 s */
#define HELIX_ENV_DEVICE_ID     "stm32-f4zg-sim-01"

#endif
