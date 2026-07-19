#ifndef ARM_HOST_LINK_H
#define ARM_HOST_LINK_H

#include <stdint.h>

void arm_host_link_init(uint32_t baudrate);
int arm_host_link_poll(char *frame, uint16_t frame_size, uint16_t *length, uint32_t now_ms);
int arm_host_link_send_text(const char *text);
void arm_host_link_send_ready_v2(void);
void arm_host_link_send_info_v2(void);
void arm_host_link_send_ack(void);
void arm_host_link_send_error(const char *reason);

uint32_t arm_host_link_rx_overflow_count(void);
uint32_t arm_host_link_tx_overflow_count(void);
uint32_t arm_host_link_bad_frame_count(void);
uint32_t arm_host_link_rx_byte_count(void);
uint32_t arm_host_link_tx_byte_count(void);

#endif
