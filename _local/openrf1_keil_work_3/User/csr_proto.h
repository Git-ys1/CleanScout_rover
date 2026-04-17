#ifndef CSR_PROTO_H
#define CSR_PROTO_H

#include "csr_board_map.h"
#include "csr_encoder_drv.h"

typedef enum
{
    CSR_CMD_NONE = 0,
    CSR_CMD_W,
    CSR_CMD_M,
    CSR_CMD_E,
    CSR_CMD_D,
    CSR_CMD_R,
    CSR_CMD_X,
    CSR_CMD_STOP
} csr_cmd_type_t;

typedef struct
{
    csr_cmd_type_t type;
    csr_channel_t channel;
    uint8_t reg_target;
    csr_encoder_input_mode_t input_mode;
    csr_encoder_count_mode_t count_mode;
    uint8_t ic_filter;
    int16_t pwm;
    float target_vel[CSR_CHANNEL_COUNT];
} csr_proto_command_t;

void csr_proto_init(uint32_t baudrate);
int csr_proto_poll(csr_proto_command_t *command);
void csr_proto_send_ready(void);
void csr_proto_send_ack(const char *name);
void csr_proto_send_error(const char *reason);
void csr_proto_send_enc(csr_channel_t channel, int32_t count, int32_t delta);
void csr_proto_send_dbg(csr_channel_t channel, uint8_t phase_a, uint8_t phase_b, uint16_t timer_count, int32_t count, int32_t delta);
void csr_proto_send_reg(uint8_t target, const csr_encoder_reg_snapshot_t *snapshot);
void csr_proto_send_vel(const float *rt, const float *tg);
void csr_proto_send_pwm(const int16_t *pwm);

#endif
