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

#define CSR_COMMAND_TIMEOUT_MS      2000UL
#define CSR_PROTO_BAUDRATE          115200UL
#define CSR_INPUT_PWM_MAX           1000
#define CSR_EFFECTIVE_PWM_MIN       300
#define CSR_EFFECTIVE_PWM_MAX       700
#define CSR_TIM8_PWM_TOP            2000U

extern int8_t g_csr_motor_dir_sign[CSR_CHANNEL_COUNT];
extern int8_t g_csr_encoder_dir_sign[CSR_CHANNEL_COUNT];

const char *csr_channel_name(csr_channel_t channel);
const char *csr_channel_wheel_note(csr_channel_t channel);

#endif
