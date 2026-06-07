#ifndef CSR_PROTO_H
#define CSR_PROTO_H

#include "csr_board_map.h"

typedef enum
{
    CSR_CMD_NONE = 0,
    CSR_CMD_W,
    CSR_CMD_M,
    CSR_CMD_E,
    CSR_CMD_D,
    CSR_CMD_STOP
} csr_cmd_type_t;

typedef struct
{
    csr_cmd_type_t type;
    csr_channel_t channel;
    int16_t pwm;
    float target_vel[CSR_CHANNEL_COUNT];
} csr_proto_command_t;

/* USART2 115200 8N1 行协议，命令以 \n 或 \r\n 结束。 */
void csr_proto_init(uint32_t baudrate);
int csr_proto_poll(csr_proto_command_t *command);

/* 固定协议输出，树莓派端依赖 VEL/PWM 的字段顺序，修改前必须联动验证。 */
void csr_proto_send_ready(void);
void csr_proto_send_ack(const char *name);
void csr_proto_send_error(const char *reason);
void csr_proto_send_enc(csr_channel_t channel, int32_t count, int32_t delta);
void csr_proto_send_dbg(csr_channel_t channel, uint8_t phase_a, uint8_t phase_b, uint16_t timer_count, int32_t count, int32_t delta);
void csr_proto_send_vel(const float *rt, const float *tg);
void csr_proto_send_pwm(const int16_t *pwm);
void csr_proto_send_navdbg(const float *cmd, const float *ramp, const float *rt, const int16_t *out);

#endif
