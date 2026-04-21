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
 * C-3.3.1A wheel semantic truth:
 * W,a,b,c,d order remains CN1,CN2,CN3,CN4.
 * CN1 = LR(left rear), CN2 = LF(left front),
 * CN3 = RR(right rear), CN4 = RF(right front).
 */
#define CSR_WHEEL_LR                    CSR_CHANNEL_CN1
#define CSR_WHEEL_LF                    CSR_CHANNEL_CN2
#define CSR_WHEEL_RR                    CSR_CHANNEL_CN3
#define CSR_WHEEL_RF                    CSR_CHANNEL_CN4

#define CSR_PROTO_BAUDRATE              115200UL

#define CSR_RAW_COMMAND_TIMEOUT_MS      2000UL
#define CSR_W_COMMAND_TIMEOUT_MS        250UL
#define CSR_CONTROL_PERIOD_MS           20UL
#define CSR_TELEMETRY_PERIOD_MS         100UL

#define CSR_CONTROL_HZ                  50.0f
#define CSR_WHEEL_RESOLUTION            1560.0f
#define CSR_WHEEL_DIAMETER_M            0.08f
#define CSR_PI_CONST                    3.14159265358979f
#define CSR_WHEEL_SPEED_SCALE           (CSR_PI_CONST * CSR_WHEEL_DIAMETER_M * CSR_CONTROL_HZ / CSR_WHEEL_RESOLUTION)

#define CSR_INPUT_PWM_MAX               1000
#define CSR_EFFECTIVE_PWM_MIN           120
#define CSR_EFFECTIVE_PWM_MAX           700
#define CSR_TIM8_PWM_TOP                2000U

#define CSR_PI_KP_DEFAULT               1200.0f
#define CSR_PI_KI_DEFAULT               80.0f
#define CSR_PI_KD_DEFAULT               0.0f
#define CSR_PI_INTEGRAL_LIMIT           0.30f
#define CSR_PI_OUTPUT_LIMIT             1000.0f
#define CSR_VEL_FILTER_ALPHA            0.50f
#define CSR_PI_PWM_STEP_LIMIT           40

extern int8_t g_csr_motor_dir_sign[CSR_CHANNEL_COUNT];
extern int8_t g_csr_encoder_dir_sign[CSR_CHANNEL_COUNT];

const char *csr_channel_name(csr_channel_t channel);
const char *csr_channel_wheel_note(csr_channel_t channel);

#endif
