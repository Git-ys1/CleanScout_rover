#ifndef CSR_ENCODER_DRV_H
#define CSR_ENCODER_DRV_H

#include "csr_board_map.h"

/* 初始化 TIM5/TIM3/TIM2/TIM4 四路硬件正交编码器接口。 */
void csr_encoder_init(void);

/* 读取最近控制窗口增量并清零硬件计数器。 */
int32_t csr_encoder_read_and_reset(csr_channel_t channel);

/* 查询软件累计值和最近窗口增量，不影响闭环采样。 */
int32_t csr_encoder_peek(csr_channel_t channel);
int32_t csr_encoder_last_delta(csr_channel_t channel);
void csr_encoder_zero(csr_channel_t channel);

/* 返回原始 A/B 相位与当前 TIMx->CNT，仅用于底层诊断。 */
void csr_encoder_debug_snapshot(csr_channel_t channel, uint8_t *phase_a, uint8_t *phase_b, uint16_t *timer_count);

#endif
