/**
 * 选题 B 固件骨架：按 HELIX-ENV/1 协议周期性输出室内环境样本。
 *
 * 这是可以稍后在实机上接着写驱动、再烧录的骨架，不是一份已经在实机上跑通的程序。
 * 云电脑上没有 STM32 实物，本文件未在目标板上编译、链接、烧录或联调。
 *
 * 板型（2026-11-11 已由主人确认）：
 *   正点原子 STM32F407ZGT6 开发板。具体套件与已接传感器仍未知，未见原理图。
 *
 * 引脚与传感器均为「常见 F407ZGT6 开发板」上的假设，不是从这块正点原子板读出来的：
 *   USART1  PA9=TX, PA10=RX, 115200 8N1     调试/数据口，接 USB 转串口到电脑
 *   I2C1    PB8=SCL, PB9=SDA               假设挂 BME280（温湿度气压）、BH1750（照度）
 *   ADC     另选通道（常见 PA1 一类，须对照原理图）  假设 MQ135 模拟输出；片内温度通道
 *   LED     PF9  推挽输出（部分国产 F407 板的 LED0） 心跳，可选
 *
 * 若实物原理图不同，只改本文件顶部的引脚宏和总线初始化，不要改串口 CSV 字段顺序。
 * 串口行格式见 include/helix_env_protocol.h，必须与 Atlas 模拟 USART 样本一致。
 *
 * 当前 ReadSensors() 返回一组占位值，便于先把 USART 打印跑通；
 * 接上真实驱动后，替换该函数即可，不必改协议。
 */

#include "stm32f4xx_hal.h"
#include "helix_env_protocol.h"

#include <stdio.h>
#include <string.h>

/* ---- 假设的引脚（未见实物原理图，请对照你的板子修改） ---- */
#define UART_TX_PORT   GPIOA
#define UART_TX_PIN    GPIO_PIN_9
#define UART_RX_PORT   GPIOA
#define UART_RX_PIN    GPIO_PIN_10

#define I2C_SCL_PORT   GPIOB
#define I2C_SCL_PIN    GPIO_PIN_8
#define I2C_SDA_PORT   GPIOB
#define I2C_SDA_PIN    GPIO_PIN_9

#define LED_PORT       GPIOF
#define LED_PIN        GPIO_PIN_9

#define DEVICE_ID      HELIX_ENV_DEVICE_ID

UART_HandleTypeDef huart1;
I2C_HandleTypeDef  hi2c1;

typedef struct {
    float temp_c;
    float rh_pct;
    float pressure_hpa;
    float lux;
    unsigned mq135_adc;
    float mq135_index;
    float mcu_temp_c;
} env_sample_t;

static void SystemClock_Config(void);
static void Gpio_Init(void);
static void Usart1_Init(void);
static void I2c1_Init(void);
static void ReadSensors(env_sample_t *out);
static void EmitSample(const env_sample_t *s, uint32_t seq);

/* 重定向 printf 到 USART1 */
int __io_putchar(int ch)
{
    uint8_t c = (uint8_t)ch;
    HAL_UART_Transmit(&huart1, &c, 1, 20);
    return ch;
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    Gpio_Init();
    Usart1_Init();
    I2c1_Init();

    /* 注释行：接入层会忽略。 */
    printf("# STM32 env node DEV=%s (firmware skeleton; sensors not wired in this build)\r\n",
           DEVICE_ID);

    uint32_t seq = 0;
    while (1)
    {
        env_sample_t s;
        ReadSensors(&s);
        EmitSample(&s, seq++);
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
        HAL_Delay(HELIX_ENV_SAMPLE_MS);
    }
}

static void EmitSample(const env_sample_t *s, uint32_t seq)
{
    /*
     * 与 Atlas 模拟 USART 样本同一套 key=value。
     * 板端若无 RTC：TS=UNSYNCED，由主机在接收时写入时间戳，不要编造时钟。
     * MQ135_INDEX 只是示意指数，不是标定 ppm。
     */
    printf("DEV=%s TS=UNSYNCED SEQ=%lu BME280_T_C=%.2f BME280_RH_PCT=%.2f "
           "BME280_P_HPA=%.2f BH1750_LUX=%.1f MQ135_ADC=%u MQ135_INDEX=%.2f "
           "MCU_TS_C=%.2f SRC=device\r\n",
           DEVICE_ID,
           (unsigned long)seq,
           s->temp_c,
           s->rh_pct,
           s->pressure_hpa,
           s->lux,
           s->mq135_adc,
           s->mq135_index,
           s->mcu_temp_c);
}

static void ReadSensors(env_sample_t *out)
{
    /*
     * TODO（实机）：按 Atlas/本目录假设接入
     *   BME280、BH1750 于 I2C1；MQ135 于 ADC；MCU 内部温度于 ADC。
     * 下面是占位 0，只为先把 USART 行格式打出来。
     * 读失败时保持 0 或上一次有效值，不要编造读数。
     */
    out->temp_c = 0.00f;
    out->rh_pct = 0.0f;
    out->pressure_hpa = 0.0f;
    out->lux = 0.0f;
    out->mq135_adc = 0;
    out->mq135_index = 0.0f;
    out->mcu_temp_c = 0.0f;
}

static void Gpio_Init(void)
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOF_CLK_ENABLE();

    GPIO_InitTypeDef io = {0};

    io.Pin = LED_PIN;
    io.Mode = GPIO_MODE_OUTPUT_PP;
    io.Pull = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);
}

static void Usart1_Init(void)
{
    __HAL_RCC_USART1_CLK_ENABLE();

    GPIO_InitTypeDef io = {0};
    io.Pin = UART_TX_PIN | UART_RX_PIN;
    io.Mode = GPIO_MODE_AF_PP;
    io.Pull = GPIO_PULLUP;
    io.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    io.Alternate = GPIO_AF7_USART1;
    HAL_GPIO_Init(GPIOA, &io);

    huart1.Instance = USART1;
    huart1.Init.BaudRate = HELIX_ENV_BAUD;
    huart1.Init.WordLength = UART_WORDLENGTH_8B;
    huart1.Init.StopBits = UART_STOPBITS_1;
    huart1.Init.Parity = UART_PARITY_NONE;
    huart1.Init.Mode = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    HAL_UART_Init(&huart1);
}

static void I2c1_Init(void)
{
    /* 假设 I2C1 复用到 PB8/PB9（AF4）。若板子引出的是 PB6/PB7，改这里。 */
    __HAL_RCC_I2C1_CLK_ENABLE();

    GPIO_InitTypeDef io = {0};
    io.Pin = I2C_SCL_PIN | I2C_SDA_PIN;
    io.Mode = GPIO_MODE_AF_OD;
    io.Pull = GPIO_PULLUP;
    io.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    io.Alternate = GPIO_AF4_I2C1;
    HAL_GPIO_Init(GPIOB, &io);

    hi2c1.Instance = I2C1;
    hi2c1.Init.ClockSpeed = 100000;
    hi2c1.Init.DutyCycle = I2C_DUTYCYCLE_2;
    hi2c1.Init.OwnAddress1 = 0;
    hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    hi2c1.Init.OwnAddress2 = 0;
    hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
    HAL_I2C_Init(&hi2c1);
}

static void SystemClock_Config(void)
{
    /*
     * 占位：请按你这块板的实际 HSE（常见 8 MHz，也有 25 MHz）填写 RCC。
     * 这里不写死倍频，以免在错误晶振假设下「看似能编过」。
     * 实机工程可先用芯片厂商或开发板例程里的 SystemClock_Config。
     */
    /* SystemClock_Config 应在实机工程中替换为与晶振匹配的版本。 */
}

void SysTick_Handler(void)
{
    HAL_IncTick();
}

void Error_Handler(void)
{
    __disable_irq();
    while (1) { }
}
