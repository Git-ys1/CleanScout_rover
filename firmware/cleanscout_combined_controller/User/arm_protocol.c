#include "arm_protocol.h"
#include "board_resource_map.h"
#include <string.h>

static uint8_t arm_is_digit(char value)
{
    return ((value >= '0') && (value <= '9')) ? 1U : 0U;
}

static int arm_parse_fixed_u16(const char *text, uint8_t digits, uint16_t *value)
{
    uint8_t index;
    uint16_t parsed;

    parsed = 0U;
    for (index = 0U; index < digits; index++)
    {
        if (arm_is_digit(text[index]) == 0U)
        {
            return 0;
        }
        parsed = (uint16_t)(parsed * 10U + (uint16_t)(text[index] - '0'));
    }
    *value = parsed;
    return 1;
}

static arm_parse_result_t arm_parse_id(const char *frame, uint8_t *servo_id)
{
    uint16_t parsed;

    if (arm_parse_fixed_u16(&frame[1], 3U, &parsed) == 0)
    {
        return ARM_PARSE_BAD_FRAME;
    }
    if ((parsed >= CSR_ARM_SERVO_COUNT) || (parsed == 255U))
    {
        return ARM_PARSE_LIMIT;
    }
    *servo_id = (uint8_t)parsed;
    return ARM_PARSE_OK;
}

static arm_parse_result_t arm_parse_move(const char *frame, uint16_t length, arm_servo_move_t *move)
{
    arm_parse_result_t result;
    uint16_t pwm;
    uint16_t duration;

    if ((length != 15U) || (frame[0] != '#') || (frame[4] != 'P') ||
        (frame[9] != 'T') || (frame[14] != '!'))
    {
        return ARM_PARSE_BAD_FRAME;
    }
    result = arm_parse_id(frame, &move->servo_id);
    if (result != ARM_PARSE_OK)
    {
        return result;
    }
    if ((arm_parse_fixed_u16(&frame[5], 4U, &pwm) == 0) ||
        (arm_parse_fixed_u16(&frame[10], 4U, &duration) == 0))
    {
        return ARM_PARSE_BAD_FRAME;
    }
    if ((pwm < CSR_ARM_SERVO_MIN_PWM) || (pwm > CSR_ARM_SERVO_MAX_PWM) || (duration > 9999U))
    {
        return ARM_PARSE_LIMIT;
    }
    move->pwm = pwm;
    move->duration_ms = duration;
    return ARM_PARSE_OK;
}

static arm_parse_result_t arm_parse_single(const char *frame, uint16_t length, arm_protocol_command_t *command)
{
    arm_parse_result_t result;

    if (length == 15U)
    {
        result = arm_parse_move(frame, length, &command->moves[0]);
        if (result == ARM_PARSE_OK)
        {
            command->type = ARM_COMMAND_MOVE;
            command->move_count = 1U;
        }
        return result;
    }

    if ((length != 9U) || (frame[0] != '#') || (frame[4] != 'P') || (frame[8] != '!'))
    {
        return ARM_PARSE_BAD_FRAME;
    }
    result = arm_parse_id(frame, &command->servo_id);
    if (result != ARM_PARSE_OK)
    {
        return result;
    }
    if (memcmp(&frame[5], "DST", 3U) == 0)
    {
        command->type = ARM_COMMAND_STOP;
        return ARM_PARSE_OK;
    }
    if (memcmp(&frame[5], "RAD", 3U) == 0)
    {
        command->type = ARM_COMMAND_QUERY_POSITION;
        return ARM_PARSE_OK;
    }
    return ARM_PARSE_UNSUPPORTED;
}

static arm_parse_result_t arm_parse_group(const char *frame, uint16_t length, arm_protocol_command_t *command)
{
    uint16_t offset;
    uint8_t seen_mask;
    arm_parse_result_t result;
    arm_servo_move_t move;

    if ((length < 17U) || (frame[0] != '{') || (frame[length - 1U] != '}'))
    {
        return ARM_PARSE_BAD_FRAME;
    }
    offset = 1U;
    seen_mask = 0U;
    while (offset < (length - 1U))
    {
        if ((command->move_count >= ARM_PROTOCOL_MAX_MOVES) ||
            ((uint16_t)(length - 1U - offset) < 15U))
        {
            return ARM_PARSE_BAD_FRAME;
        }
        result = arm_parse_move(&frame[offset], 15U, &move);
        if (result != ARM_PARSE_OK)
        {
            return result;
        }
        if ((seen_mask & (uint8_t)(1U << move.servo_id)) != 0U)
        {
            return ARM_PARSE_BAD_FRAME;
        }
        seen_mask = (uint8_t)(seen_mask | (uint8_t)(1U << move.servo_id));
        command->moves[command->move_count] = move;
        command->move_count++;
        offset = (uint16_t)(offset + 15U);
    }
    if (offset != (length - 1U))
    {
        return ARM_PARSE_BAD_FRAME;
    }
    command->type = ARM_COMMAND_MOVE;
    command->is_group = 1U;
    return ARM_PARSE_OK;
}

arm_parse_result_t arm_protocol_parse(const char *frame, uint16_t length, arm_protocol_command_t *command)
{
    memset(command, 0, sizeof(*command));
    if ((frame == 0) || (length == 0U) || (length >= ARM_PROTOCOL_MAX_FRAME_SIZE))
    {
        return ARM_PARSE_BAD_FRAME;
    }

    if (frame[0] == '#')
    {
        return arm_parse_single(frame, length, command);
    }
    if (frame[0] == '{')
    {
        return arm_parse_group(frame, length, command);
    }
    if (frame[0] == '$')
    {
        command->type = ARM_COMMAND_UNSUPPORTED;
        return ARM_PARSE_UNSUPPORTED;
    }
    if (frame[0] != '@')
    {
        return ARM_PARSE_BAD_FRAME;
    }

    if ((length == 14U) && (memcmp(frame, "@HELLO:ARM_V2!", 14U) == 0))
    {
        command->type = ARM_COMMAND_HELLO_V2;
        return ARM_PARSE_OK;
    }
    if ((length == 6U) && (memcmp(frame, "@INFO!", 6U) == 0))
    {
        command->type = ARM_COMMAND_INFO;
        return ARM_PARSE_OK;
    }
    if ((length == 6U) && (memcmp(frame, "@DIAG!", 6U) == 0))
    {
        command->type = ARM_COMMAND_DIAG;
        return ARM_PARSE_OK;
    }
    if ((length == 6U) && (memcmp(frame, "@PING!", 6U) == 0))
    {
        command->type = ARM_COMMAND_PING;
        return ARM_PARSE_OK;
    }
    if ((length == 7U) && (memcmp(frame, "@ESTOP!", 7U) == 0))
    {
        command->type = ARM_COMMAND_ESTOP;
        return ARM_PARSE_OK;
    }
    if ((length == 13U) && (memcmp(frame, "@CLEAR:ESTOP!", 13U) == 0))
    {
        command->type = ARM_COMMAND_CLEAR_ESTOP;
        return ARM_PARSE_OK;
    }
    return ARM_PARSE_UNSUPPORTED;
}

const char *arm_protocol_error_name(arm_parse_result_t result)
{
    if (result == ARM_PARSE_LIMIT)
    {
        return "LIMIT";
    }
    if (result == ARM_PARSE_UNSUPPORTED)
    {
        return "UNSUPPORTED";
    }
    return "BAD_FRAME";
}
