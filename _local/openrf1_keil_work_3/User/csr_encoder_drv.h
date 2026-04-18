#ifndef CSR_ENCODER_DRV_H
#define CSR_ENCODER_DRV_H

#include "csr_board_map.h"

void csr_encoder_init(void);
int32_t csr_encoder_read_and_reset(csr_channel_t channel);
int32_t csr_encoder_peek(csr_channel_t channel);
int32_t csr_encoder_last_delta(csr_channel_t channel);
void csr_encoder_zero(csr_channel_t channel);
void csr_encoder_debug_snapshot(csr_channel_t channel, uint8_t *phase_a, uint8_t *phase_b, uint16_t *timer_count);

#endif
