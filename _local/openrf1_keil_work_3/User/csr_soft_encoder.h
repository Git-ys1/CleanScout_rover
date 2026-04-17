#ifndef CSR_SOFT_ENCODER_H
#define CSR_SOFT_ENCODER_H

#include "csr_board_map.h"

void csr_soft_encoder_init(void);
int32_t csr_soft_encoder_read_and_reset(csr_channel_t channel);
int32_t csr_soft_encoder_peek(csr_channel_t channel);
int32_t csr_soft_encoder_last_delta(csr_channel_t channel);
void csr_soft_encoder_zero(csr_channel_t channel);
void csr_soft_encoder_debug_phase(csr_channel_t channel, uint8_t *phase_a, uint8_t *phase_b);

#endif
