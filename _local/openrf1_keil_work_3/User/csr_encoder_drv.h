#ifndef CSR_ENCODER_DRV_H
#define CSR_ENCODER_DRV_H

#include "csr_board_map.h"

typedef struct
{
    uint32_t mapr_raw;
    uint32_t mapr_effective;
    uint16_t smcr;
    uint16_t ccmr1;
    uint16_t ccer;
    uint16_t cnt;
    uint8_t pin_a_cfg;
    uint8_t pin_b_cfg;
    uint8_t pin_a_level;
    uint8_t pin_b_level;
    uint32_t gpioa_crl;
    uint32_t gpioa_crh;
    uint32_t gpioa_idr;
    uint32_t gpiob_crl;
    uint32_t gpiob_crh;
    uint32_t gpiob_idr;
} csr_encoder_reg_snapshot_t;

void csr_encoder_apply_debug_remap(void);
void csr_encoder_init(void);
int32_t csr_encoder_read_and_reset(csr_channel_t channel);
int32_t csr_encoder_peek(csr_channel_t channel);
int32_t csr_encoder_last_delta(csr_channel_t channel);
void csr_encoder_zero(csr_channel_t channel);
void csr_encoder_debug_snapshot(csr_channel_t channel, uint8_t *phase_a, uint8_t *phase_b, uint16_t *timer_count);
void csr_encoder_reg_snapshot(uint8_t target, csr_encoder_reg_snapshot_t *snapshot);

#endif
