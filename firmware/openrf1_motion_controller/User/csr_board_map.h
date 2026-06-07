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

/*
 * 下面两项是 C-3.5.0 旧目标斜坡接口保留值。
 * 当前实车版本真正参与控制的加速度值定义在 main.c 的
 * CSR_MAX_ACCEL_MPS2=2.5f。暂不删除此处兼容宏，避免改变已收敛代码。
 */
#define CSR_CONTROL_HZ                  50.0f
#define CSR_WHEEL_ACC_LIMIT_MPS2        0.20f
#define CSR_WHEEL_DV_PER_TICK           (CSR_WHEEL_ACC_LIMIT_MPS2 * ((float)CSR_CONTROL_PERIOD_MS / 1000.0f))

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
#define CSR_EFFECTIVE_PWM_MAX           850
#define CSR_TIM8_PWM_TOP                2000U
#define CSR_PWM_STEP_LIMIT_NAV          10

/*
 * 下列前馈、修正量和积分限幅宏来自上一版控制器，当前增量 PI 主路径
 * 未直接使用。为保持实车版本源代码边界，本轮仅注明，不做删除。
 */
#define CSR_FEEDFORWARD_PWM_AT_0_10_MPS 400.0f
#define CSR_PI_CORRECTION_LIMIT         1000.0f

/*
 * 当前四轮统一增量 PI 参数：
 * delta_pwm = Kp*(error - previous_error) + Ki*error*dt
 */
#define CSR_PI_KP_DEFAULT               200.0f
#define CSR_PI_KI_DEFAULT               2500.0f
#define CSR_PI_KD_DEFAULT               0.0f
#define CSR_PI_INTEGRAL_LIMIT           0.15f
#define CSR_PI_OUTPUT_LIMIT             CSR_PI_CORRECTION_LIMIT

/* 速度一阶低通系数：数值越大越平滑，同时响应延迟也越大。 */
#define CSR_VEL_FILTER_ALPHA            0.35f

/* 实车方向真值，定义位于 csr_board_map.c。 */
extern int8_t g_csr_motor_dir_sign[CSR_CHANNEL_COUNT];
extern int8_t g_csr_encoder_dir_sign[CSR_CHANNEL_COUNT];

const char *csr_channel_name(csr_channel_t channel);
const char *csr_channel_wheel_note(csr_channel_t channel);

#endif
