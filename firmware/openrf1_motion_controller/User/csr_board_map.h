#ifndef CSR_BOARD_MAP_H
#define CSR_BOARD_MAP_H

#include "stm32f10x.h"
#include <stdint.h>

typedef enum
{
    CSR_CHANNEL_CN1 = 0,
    CSR_CHANNEL_CN2 = 1,
    CSR_CHANNEL_CN3 = 2,
    CSR_CHANNEL_CN4 = 3,
    CSR_CHANNEL_COUNT = 4
} csr_channel_t;

/*
 * 四路通道顺序是整个下位机的固定语义：
 * W,a,b,c,d 依次对应 CN1、CN2、CN3、CN4。
 * CN1=左后(LR)，CN2=左前(LF)，CN3=右后(RR)，CN4=右前(RF)。
 * 上层运动学只改变四轮目标的符号组合，不得重新排列这里的通道。
 */
#define CSR_WHEEL_LR                    CSR_CHANNEL_CN1
#define CSR_WHEEL_LF                    CSR_CHANNEL_CN2
#define CSR_WHEEL_RR                    CSR_CHANNEL_CN3
#define CSR_WHEEL_RF                    CSR_CHANNEL_CN4

/* USART2 串口与安全看门狗。 */
#define CSR_PROTO_BAUDRATE              115200UL

#define CSR_RAW_COMMAND_TIMEOUT_MS      2000UL
#define CSR_W_COMMAND_TIMEOUT_MS        250UL

/* 50Hz 闭环控制、10Hz 遥测。 */
#define CSR_CONTROL_PERIOD_MS           20UL
#define CSR_TELEMETRY_PERIOD_MS         100UL

/* 目标轮速斜坡：2.5m/s^2 表示从 0 加速到 0.5m/s 理论需要 0.2 秒。 */
#define CSR_CONTROL_HZ                  50.0f
#define CSR_WHEEL_ACC_LIMIT_MPS2        2.5f

/* 上电自动前进仅用于架空排障，正式运行必须保持为 0。 */
#define CSR_BOOT_FORWARD_TEST_ENABLE    0
#define CSR_BOOT_FORWARD_TEST_SPEED_MPS 0.20f

/*
 * 编码器速度标定：1768 个计数/输出轴一圈，当前轮径 0.06m。
 * 更换电机减速比或轮子直径后必须重新标定这两个值。
 */
#define CSR_WHEEL_RESOLUTION            1768.0f
#define CSR_WHEEL_DIAMETER_M            0.06f
#define CSR_PI_CONST                    3.14159265358979f
#define CSR_WHEEL_SPEED_SCALE           (CSR_PI_CONST * CSR_WHEEL_DIAMETER_M * CSR_CONTROL_HZ / CSR_WHEEL_RESOLUTION)

/* PWM/H 桥范围。TIM8 周期为 2000，控制层有符号输入范围为 ±1000。 */
#define CSR_INPUT_PWM_MAX               1000
#define CSR_TIM8_PWM_TOP                2000U

/*
 * 当前四轮统一增量 PI 参数：
 * delta_pwm = Kp*(error - previous_error) + Ki*error*dt
 */
#define CSR_PI_KP_DEFAULT               200.0f
#define CSR_PI_KI_DEFAULT               2500.0f

/* 速度一阶低通系数：数值越大越平滑，同时响应延迟也越大。 */
#define CSR_VEL_FILTER_ALPHA            0.35f

/* 实车方向真值，定义位于 csr_board_map.c。 */
extern int8_t g_csr_motor_dir_sign[CSR_CHANNEL_COUNT];
extern int8_t g_csr_encoder_dir_sign[CSR_CHANNEL_COUNT];

const char *csr_channel_name(csr_channel_t channel);
const char *csr_channel_wheel_note(csr_channel_t channel);

#endif
