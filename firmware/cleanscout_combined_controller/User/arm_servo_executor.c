#include "main.h"

#define ARM_QUERY_TIMEOUT_MS             200UL

static uint16_t g_last_pwm[CSR_ARM_SERVO_COUNT];
static uint32_t g_busy_until_ms;
static uint8_t g_query_pending;
static uint8_t g_query_enhanced;
static uint8_t g_query_servo_id;
static uint32_t g_query_deadline_ms;

static void arm_append_move(char *frame, uint16_t frame_size, const arm_servo_move_t *move)
{
    char command[24];

    sprintf(command, "#%03uP%04uT%04u!", (unsigned int)move->servo_id,
            (unsigned int)move->pwm, (unsigned int)move->duration_ms);
    strncat(frame, command, frame_size - strlen(frame) - 1U);
}

static int arm_build_move_frame(const arm_protocol_command_t *command, char *frame, uint16_t frame_size)
{
    uint8_t index;

    frame[0] = '\0';
    if (command->is_group != 0U)
    {
        strcpy(frame, "{");
    }
    for (index = 0U; index < command->move_count; index++)
    {
        arm_append_move(frame, frame_size, &command->moves[index]);
    }
    if (command->is_group != 0U)
    {
        strncat(frame, "}", frame_size - strlen(frame) - 1U);
    }
    return (strlen(frame) < frame_size) ? 1 : 0;
}

void arm_servo_executor_init(void)
{
    uint8_t index;

    for (index = 0U; index < CSR_ARM_SERVO_COUNT; index++)
    {
        g_last_pwm[index] = 1500U;
    }
    g_busy_until_ms = 0UL;
    g_query_pending = 0U;
    g_query_enhanced = 0U;
    g_query_servo_id = 0U;
    g_query_deadline_ms = 0UL;
}

arm_exec_result_t arm_servo_executor_submit(const arm_protocol_command_t *command, uint8_t enhanced_mode, uint32_t now_ms)
{
    char frame[ARM_PROTOCOL_MAX_FRAME_SIZE];
    uint8_t index;
    uint16_t max_duration;

    if ((enhanced_mode != 0U) && (command->type != ARM_COMMAND_STOP) &&
        (arm_servo_executor_is_idle(now_ms) == 0U))
    {
        return ARM_EXEC_BUSY;
    }

    if (command->type == ARM_COMMAND_MOVE)
    {
        if (arm_build_move_frame(command, frame, sizeof(frame)) == 0)
        {
            return ARM_EXEC_LINK_FULL;
        }
        if (arm_servo_bus_send_frame(frame) == 0)
        {
            return ARM_EXEC_LINK_FULL;
        }
        max_duration = 0U;
        for (index = 0U; index < command->move_count; index++)
        {
            g_last_pwm[command->moves[index].servo_id] = command->moves[index].pwm;
            if (command->moves[index].duration_ms > max_duration)
            {
                max_duration = command->moves[index].duration_ms;
            }
        }
        g_busy_until_ms = now_ms + (uint32_t)max_duration;
        return ARM_EXEC_OK;
    }

    if (command->type == ARM_COMMAND_STOP)
    {
        sprintf(frame, "#%03uPDST!", (unsigned int)command->servo_id);
        if (arm_servo_bus_send_frame(frame) == 0)
        {
            return ARM_EXEC_LINK_FULL;
        }
        g_busy_until_ms = now_ms;
        return ARM_EXEC_OK;
    }

    if (command->type == ARM_COMMAND_QUERY_POSITION)
    {
        if (g_query_pending != 0U)
        {
            return ARM_EXEC_BUSY;
        }
        sprintf(frame, "#%03uPRAD!", (unsigned int)command->servo_id);
        if (arm_servo_bus_send_frame(frame) == 0)
        {
            return ARM_EXEC_LINK_FULL;
        }
        g_query_pending = 1U;
        g_query_enhanced = enhanced_mode;
        g_query_servo_id = command->servo_id;
        g_query_deadline_ms = now_ms + ARM_QUERY_TIMEOUT_MS;
        return ARM_EXEC_OK;
    }

    return ARM_EXEC_LINK_FULL;
}

void arm_servo_executor_stop_all(uint32_t now_ms)
{
    char frame[16];
    uint8_t index;

    for (index = 0U; index < CSR_ARM_SERVO_COUNT; index++)
    {
        sprintf(frame, "#%03uPDST!", (unsigned int)index);
        arm_servo_bus_send_frame(frame);
    }
    g_busy_until_ms = now_ms;
    g_query_pending = 0U;
}

void arm_servo_executor_tick(uint32_t now_ms)
{
    char response[64];
    char expected_prefix[8];
    uint16_t length;
    int result;

    result = arm_servo_bus_poll_response(response, sizeof(response), &length, now_ms);
    if (result > 0)
    {
        (void)length;
        if (g_query_pending != 0U)
        {
            sprintf(expected_prefix, "#%03uP", (unsigned int)g_query_servo_id);
            if ((length >= 7U) && (memcmp(response, expected_prefix, 5U) == 0))
            {
                arm_host_link_send_text(response);
                g_query_pending = 0U;
            }
        }
    }
    else if (result < 0)
    {
        if ((g_query_pending != 0U) && (g_query_enhanced != 0U))
        {
            arm_host_link_send_error("BAD_FRAME");
        }
        g_query_pending = 0U;
    }

    if ((g_query_pending != 0U) && ((int32_t)(now_ms - g_query_deadline_ms) >= 0))
    {
        if (g_query_enhanced != 0U)
        {
            arm_host_link_send_error("TIMEOUT");
        }
        g_query_pending = 0U;
    }
}

uint8_t arm_servo_executor_is_idle(uint32_t now_ms)
{
    if ((g_query_pending != 0U) || (arm_servo_bus_is_tx_idle() == 0U))
    {
        return 0U;
    }
    return ((int32_t)(now_ms - g_busy_until_ms) >= 0) ? 1U : 0U;
}

uint8_t arm_servo_executor_is_expanded(void)
{
    uint8_t index;

    for (index = 0U; index < CSR_ARM_SERVO_COUNT; index++)
    {
        if ((g_last_pwm[index] < 1200U) || (g_last_pwm[index] > 1800U))
        {
            return 1U;
        }
    }
    return 0U;
}
