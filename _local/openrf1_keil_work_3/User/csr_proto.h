#ifndef CSR_PROTO_H
#define CSR_PROTO_H

#include "csr_board_map.h"

typedef enum
{
    CSR_CMD_NONE = 0,
    CSR_CMD_M,
    CSR_CMD_E,
    CSR_CMD_STOP
} csr_cmd_type_t;

typedef struct
{
    csr_cmd_type_t type;
    csr_channel_t channel;
    int16_t pwm;
} csr_proto_command_t;

void csr_proto_init(uint32_t baudrate);
int csr_proto_poll(csr_proto_command_t *command);
void csr_proto_send_ready(void);
void csr_proto_send_ack(const char *name);
void csr_proto_send_error(const char *reason);
void csr_proto_send_enc(csr_channel_t channel, int32_t count, int32_t delta);

#endif
