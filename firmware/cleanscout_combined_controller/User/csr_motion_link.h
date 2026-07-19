#ifndef CSR_MOTION_LINK_H
#define CSR_MOTION_LINK_H

#include "csr_board_map.h"

typedef enum
{
    CSR_CMD_NONE = 0,
    CSR_CMD_W,
    CSR_CMD_M,
    CSR_CMD_E,
    CSR_CMD_D,
    CSR_CMD_STOP,
    CSR_CMD_ESTOP,
    CSR_CMD_CLEAR_ESTOP,
    CSR_CMD_INFO
} csr_cmd_type_t;

typedef struct
{
    csr_cmd_type_t type;
    csr_channel_t channel;
    int16_t pwm;
    float target_vel[CSR_CHANNEL_COUNT];
} csr_motion_command_t;

void csr_motion_link_init(uint32_t baudrate);
int csr_motion_link_poll(csr_motion_command_t *command);

void csr_motion_link_send_ready(void);
void csr_motion_link_send_ack(const char *name);
void csr_motion_link_send_error(const char *reason);
void csr_motion_link_send_info(void);
void csr_motion_link_send_enc(csr_channel_t channel, int32_t count, int32_t delta);
void csr_motion_link_send_dbg(csr_channel_t channel, uint8_t phase_a, uint8_t phase_b, uint16_t timer_count, int32_t count, int32_t delta);
void csr_motion_link_send_vel(const float *rt, const float *tg);
void csr_motion_link_send_pwm(const int16_t *pwm);
void csr_motion_link_send_navdbg(const float *cmd, const float *ramp, const float *rt, const int16_t *out);

uint32_t csr_motion_link_rx_overflow_count(void);
uint32_t csr_motion_link_tx_overflow_count(void);
uint32_t csr_motion_link_bad_frame_count(void);

#endif
