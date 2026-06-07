#ifndef CSR_BOARD_MAP_H
#define CSR_BOARD_MAP_H

#include "stm32f10x.h"
#include <stdint.h>

/*
 * OpenRF1 四路底盘通道的唯一编号。
 *
 * 串口 W,a,b,c,d 的参数顺序始终与 CN1~CN4 一致：
 *   CN1 = 左后轮（LR）
 *   CN2 = 左前轮（LF）
 *   CN3 = 右后轮（RR）
 *   CN4 = 右前轮（RF）
 *
 * 上层运动学只能改变四轮目标速度的正负组合，不允许重新解释此顺序。
 */
typedef enum
{
    CSR_CHANNEL_CN1 = 0,
    CSR_CHANNEL_CN2 = 1,
    CSR_CHANNEL_CN3 = 2,
    CSR_CHANNEL_CN4 = 3,
    CSR_CHANNEL_COUNT = 4
} csr_channel_t;

#define CSR_WHEEL_LR                    CSR_CHANNEL_CN1
#define CSR_WHEEL_LF                    CSR_CHANNEL_CN2
#define CSR_WHEEL_RR                    CSR_CHANNEL_CN3
#define CSR_WHEEL_RF                    CSR_CHANNEL_CN4

/* 串口与安全看门狗。 */
#define CSR_PROTO_BAUDRATE              115200UL
#define CSR_RAW_COMMAND_TIMEOUT_MS      2000UL
#define CSR_W_COMMAND_TIMEOUT_MS        250UL

/* 任务调度：闭环 50Hz，遥测 10Hz。 */
#define CSR_CONTROL_PERIOD_MS           20UL
#define CSR_TELEMETRY_PERIOD_MS         100UL
#define CSR_CONTROL_HZ                  50.0f

/*
 * 轮速模型。
 *
 * CSR_WHEEL_RESOLUTION 是当前电机输出轴每圈的编码器计数标定值；
 * CSR_WHEEL_DIAMETER_M 是当前橡胶轮实测直径。两者直接决定 delta 到 m/s
 * 的换算比例，换轮或换减速电机后必须重新核对。
 */
#define CSR_WHEEL_RESOLUTION            1768.0f
#define CSR_WHEEL_DIAMETER_M            0.06f
#define CSR_PI_CONST                    3.14159265358979f
#define CSR_WHEEL_SPEED_SCALE           (CSR_PI_CONST * CSR_WHEEL_DIAMETER_M * CSR_CONTROL_HZ / CSR_WHEEL_RESOLUTION)

/*
 * 目标速度斜坡。
 *
 * 2.5m/s^2 对应每个 20ms 周期最多变化 0.05m/s。该参数来自
 * C-3.6.0 实车参数基线，用来兼顾导航响应和机械冲击。
 */
#define CSR_WHEEL_ACC_LIMIT_MPS2        2.5f
#define CSR_WHEEL_DV_PER_TICK           (CSR_WHEEL_ACC_LIMIT_MPS2 * ((float)CSR_CONTROL_PERIOD_MS / 1000.0f))

/*
 * 增量 PI 参数。
 *
 * 每周期 PWM 增量：
 *   delta_pwm = Kp * (error - previous_error) + Ki * error * dt
 *
 * 四轮使用相同参数，保证控制器语义统一。方向差异只由方向表和 H 桥
 * 真值处理，不通过四套 PID 参数修补。
 */
#define CSR_PI_KP_DEFAULT               200.0f
#define CSR_PI_KI_DEFAULT               2500.0f

/* PWM 与底层 H 桥参数。 */
#define CSR_INPUT_PWM_MAX               1000
#define CSR_TIM8_PWM_TOP                2000U
#define CSR_RESET_PHASE_OFFSET          1100U

/* 速度一阶低通：越小越重视新测量，越大越平滑但延迟更高。 */
#define CSR_VEL_FILTER_ALPHA            0.35f

/*
 * 上电自动前进仅用于架空诊断，正式固件必须保持为 0。
 * 开启后固件会锁存四轮同速目标并绕过 W 指令看门狗。
 */
#define CSR_BOOT_FORWARD_TEST_ENABLE    0
#define CSR_BOOT_FORWARD_TEST_SPEED_MPS 0.20f

/*
 * 方向表是实车接线后的冻结真值：
 * - motor_dir_sign：闭环输出到电机命令的符号修正；
 * - encoder_dir_sign：原始定时器计数到统一车体速度的符号修正。
 */
extern int8_t g_csr_motor_dir_sign[CSR_CHANNEL_COUNT];
extern int8_t g_csr_encoder_dir_sign[CSR_CHANNEL_COUNT];

const char *csr_channel_name(csr_channel_t channel);
const char *csr_channel_wheel_note(csr_channel_t channel);

#endif
