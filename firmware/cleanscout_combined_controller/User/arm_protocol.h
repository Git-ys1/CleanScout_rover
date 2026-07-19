#ifndef ARM_PROTOCOL_H
#define ARM_PROTOCOL_H

#include <stdint.h>

#define ARM_PROTOCOL_MAX_MOVES           6U
#define ARM_PROTOCOL_MAX_FRAME_SIZE      128U

typedef enum
{
    ARM_COMMAND_NONE = 0,
    ARM_COMMAND_MOVE,
    ARM_COMMAND_STOP,
    ARM_COMMAND_QUERY_POSITION,
    ARM_COMMAND_HELLO_V2,
    ARM_COMMAND_INFO,
    ARM_COMMAND_DIAG,
    ARM_COMMAND_PING,
    ARM_COMMAND_ESTOP,
    ARM_COMMAND_CLEAR_ESTOP,
    ARM_COMMAND_UNSUPPORTED
} arm_command_type_t;

typedef enum
{
    ARM_PARSE_OK = 0,
    ARM_PARSE_BAD_FRAME,
    ARM_PARSE_LIMIT,
    ARM_PARSE_UNSUPPORTED
} arm_parse_result_t;

typedef struct
{
    uint8_t servo_id;
    uint16_t pwm;
    uint16_t duration_ms;
} arm_servo_move_t;

typedef struct
{
    arm_command_type_t type;
    uint8_t servo_id;
    uint8_t move_count;
    uint8_t is_group;
    arm_servo_move_t moves[ARM_PROTOCOL_MAX_MOVES];
} arm_protocol_command_t;

arm_parse_result_t arm_protocol_parse(const char *frame, uint16_t length, arm_protocol_command_t *command);
const char *arm_protocol_error_name(arm_parse_result_t result);

#endif
