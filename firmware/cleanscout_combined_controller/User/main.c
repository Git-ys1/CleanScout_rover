#include "main.h"

static volatile uint32_t g_system_ms;

static uint32_t csr_millis(void)
{
    return g_system_ms;
}

void SysTick_Handler(void)
{
    g_system_ms++;
}

static void csr_systick_init(void)
{
    SysTick_Config(SystemCoreClock / 1000U);
}

static void handle_motion_command(const csr_motion_command_t *command, uint32_t now_ms)
{
    if (command->type == CSR_CMD_ESTOP)
    {
        safety_supervisor_latch_estop(now_ms);
        csr_motion_link_send_ack("ESTOP");
        return;
    }
    if (command->type == CSR_CMD_CLEAR_ESTOP)
    {
        if (safety_supervisor_try_clear_estop(now_ms) != 0U)
        {
            csr_motion_link_send_ack("CLEAR_ESTOP");
        }
        else
        {
            csr_motion_link_send_error("estop_not_clearable");
        }
        return;
    }
    if (command->type == CSR_CMD_INFO)
    {
        csr_motion_link_send_info();
        return;
    }

    if ((safety_supervisor_estop_latched() != 0U) &&
        ((command->type == CSR_CMD_W) || (command->type == CSR_CMD_M)))
    {
        csr_motion_link_send_error("estop_latched");
        return;
    }
    csr_motion_controller_handle(command, now_ms);
}

static void handle_arm_frame(const char *frame, uint16_t length, uint32_t now_ms)
{
    char diag[192];
    char bus_raw[80];
    char hex_byte[4];
    uint8_t bus_bytes[16];
    uint8_t bus_byte_count;
    uint8_t bus_index;
    arm_protocol_command_t command;
    arm_parse_result_t parse_result;
    arm_exec_result_t exec_result;
    uint8_t enhanced;

    parse_result = arm_protocol_parse(frame, length, &command);
    enhanced = safety_supervisor_arm_v2_active();
    if (parse_result != ARM_PARSE_OK)
    {
        arm_host_link_send_error(arm_protocol_error_name(parse_result));
        return;
    }

    if (command.type == ARM_COMMAND_HELLO_V2)
    {
        safety_supervisor_enable_arm_v2(now_ms);
        arm_host_link_send_ready_v2();
        return;
    }
    if (command.type == ARM_COMMAND_INFO)
    {
        safety_supervisor_note_arm_activity(now_ms);
        arm_host_link_send_info_v2();
        return;
    }
    if (command.type == ARM_COMMAND_DIAG)
    {
        safety_supervisor_note_arm_activity(now_ms);
        sprintf(
            diag,
            "@DIAG:HOST_RX=%lu,HOST_TX=%lu,BUS_RX=%lu,BUS_TX=%lu,HOST_OVF=%lu,BUS_OVF=%lu,ESTOP=%u!",
            (unsigned long)arm_host_link_rx_byte_count(),
            (unsigned long)arm_host_link_tx_byte_count(),
            (unsigned long)arm_servo_bus_rx_byte_count(),
            (unsigned long)arm_servo_bus_tx_byte_count(),
            (unsigned long)arm_host_link_rx_overflow_count(),
            (unsigned long)arm_servo_bus_rx_overflow_count(),
            (unsigned int)safety_supervisor_estop_latched()
        );
        arm_host_link_send_text(diag);
        strcpy(bus_raw, "@BUSRAW:");
        bus_byte_count = arm_servo_bus_copy_last_rx(bus_bytes, sizeof(bus_bytes));
        for (bus_index = 0U; bus_index < bus_byte_count; bus_index++)
        {
            sprintf(hex_byte, "%02X", (unsigned int)bus_bytes[bus_index]);
            strncat(bus_raw, hex_byte, sizeof(bus_raw) - strlen(bus_raw) - 1U);
        }
        strncat(bus_raw, "!", sizeof(bus_raw) - strlen(bus_raw) - 1U);
        arm_host_link_send_text(bus_raw);
        return;
    }
    if (command.type == ARM_COMMAND_PING)
    {
        if (enhanced != 0U)
        {
            safety_supervisor_note_arm_activity(now_ms);
            arm_host_link_send_ack();
        }
        else
        {
            arm_host_link_send_error("WATCHDOG");
        }
        return;
    }
    if (command.type == ARM_COMMAND_ESTOP)
    {
        safety_supervisor_latch_estop(now_ms);
        arm_host_link_send_ack();
        return;
    }
    if (command.type == ARM_COMMAND_CLEAR_ESTOP)
    {
        if (safety_supervisor_try_clear_estop(now_ms) != 0U)
        {
            arm_host_link_send_ack();
        }
        else
        {
            arm_host_link_send_error("BUSY");
        }
        return;
    }

    safety_supervisor_note_arm_activity(now_ms);
    if (safety_supervisor_estop_latched() != 0U)
    {
        arm_host_link_send_error("BUSY");
        return;
    }

    exec_result = arm_servo_executor_submit(&command, enhanced, now_ms);
    if (exec_result == ARM_EXEC_OK)
    {
        if (enhanced != 0U)
        {
            arm_host_link_send_ack();
        }
    }
    else if (exec_result == ARM_EXEC_BUSY)
    {
        arm_host_link_send_error("BUSY");
    }
    else
    {
        arm_host_link_send_error("TIMEOUT");
    }
}

int main(void)
{
    csr_motion_command_t motion_command;
    char arm_frame[ARM_PROTOCOL_MAX_FRAME_SIZE];
    uint16_t arm_frame_length;
    uint32_t now_ms;
    uint32_t last_control_ms;
    uint32_t last_telemetry_ms;
    int arm_poll_result;

    board_resource_map_init();
    csr_systick_init();
    now_ms = csr_millis();

    csr_motion_controller_init(now_ms);
    csr_motion_link_init(CSR_MOTION_BAUDRATE);
    arm_host_link_init(CSR_ARM_HOST_BAUDRATE);
    arm_servo_bus_init(CSR_ARM_BUS_BAUDRATE);
    arm_servo_executor_init();
    safety_supervisor_init(now_ms);

    last_control_ms = now_ms;
    last_telemetry_ms = now_ms;
    csr_motion_link_send_ready();

    while (1)
    {
        now_ms = csr_millis();

        safety_supervisor_tick(now_ms);
        csr_motion_controller_watchdog(now_ms);

        if ((uint32_t)(now_ms - last_control_ms) >= CSR_CONTROL_PERIOD_MS)
        {
            if ((uint32_t)(now_ms - last_control_ms) > (CSR_CONTROL_PERIOD_MS * 2UL))
            {
                last_control_ms = now_ms;
            }
            else
            {
                last_control_ms += CSR_CONTROL_PERIOD_MS;
            }
            csr_motion_controller_tick();
        }

        if (csr_motion_link_poll(&motion_command) != 0)
        {
            handle_motion_command(&motion_command, now_ms);
        }

        arm_poll_result = arm_host_link_poll(
            arm_frame,
            sizeof(arm_frame),
            &arm_frame_length,
            now_ms
        );
        if (arm_poll_result > 0)
        {
            handle_arm_frame(arm_frame, arm_frame_length, now_ms);
        }
        else if (arm_poll_result < 0)
        {
            arm_host_link_send_error("BAD_FRAME");
        }

        arm_servo_executor_tick(now_ms);
        safety_supervisor_monitor_domains();

        if ((uint32_t)(now_ms - last_telemetry_ms) >= CSR_TELEMETRY_PERIOD_MS)
        {
            last_telemetry_ms = now_ms;
            csr_motion_controller_telemetry();
        }
    }
}
