#ifndef CSR_MOTOR_DRV_H
#define CSR_MOTOR_DRV_H

#include "csr_board_map.h"

void csr_motor_init(void);
void csr_motor_set(csr_channel_t channel, int16_t signed_pwm);
void csr_motor_stop(csr_channel_t channel);
void csr_motor_stop_all(void);
int16_t csr_motor_last_pwm(csr_channel_t channel);

#endif
