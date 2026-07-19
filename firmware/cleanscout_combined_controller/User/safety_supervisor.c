#include "main.h"

static uint8_t g_estop_latched;
static uint8_t g_arm_v2_active;
static uint8_t g_arm_watchdog_fired;
static uint8_t g_risk_active;
static uint32_t g_last_arm_activity_ms;
static uint32_t g_risk_event_count;
static uint32_t g_arm_watchdog_count;

void safety_supervisor_init(uint32_t now_ms)
{
    g_estop_latched = 0U;
    g_arm_v2_active = 0U;
    g_arm_watchdog_fired = 0U;
    g_risk_active = 0U;
    g_last_arm_activity_ms = now_ms;
    g_risk_event_count = 0UL;
    g_arm_watchdog_count = 0UL;
}

void safety_supervisor_latch_estop(uint32_t now_ms)
{
    g_estop_latched = 1U;
    csr_motion_controller_stop();
    arm_servo_executor_stop_all(now_ms);
}

uint8_t safety_supervisor_try_clear_estop(uint32_t now_ms)
{
    if (g_estop_latched == 0U)
    {
        return 1U;
    }
    if ((csr_motion_controller_is_stopped() == 0U) ||
        (arm_servo_executor_is_idle(now_ms) == 0U))
    {
        return 0U;
    }
    g_estop_latched = 0U;
    return 1U;
}

uint8_t safety_supervisor_estop_latched(void)
{
    return g_estop_latched;
}

void safety_supervisor_enable_arm_v2(uint32_t now_ms)
{
    g_arm_v2_active = 1U;
    g_arm_watchdog_fired = 0U;
    g_last_arm_activity_ms = now_ms;
}

void safety_supervisor_note_arm_activity(uint32_t now_ms)
{
    if (g_arm_v2_active != 0U)
    {
        g_last_arm_activity_ms = now_ms;
        g_arm_watchdog_fired = 0U;
    }
}

uint8_t safety_supervisor_arm_v2_active(void)
{
    return g_arm_v2_active;
}

void safety_supervisor_tick(uint32_t now_ms)
{
    if ((g_arm_v2_active != 0U) && (g_arm_watchdog_fired == 0U) &&
        ((uint32_t)(now_ms - g_last_arm_activity_ms) > CSR_ARM_SESSION_TIMEOUT_MS))
    {
        arm_servo_executor_stop_all(now_ms);
        arm_host_link_send_error("WATCHDOG");
        g_arm_watchdog_fired = 1U;
        g_arm_v2_active = 0U;
        g_arm_watchdog_count++;
    }
}

void safety_supervisor_monitor_domains(void)
{
    uint8_t risky;

    risky = ((csr_motion_controller_is_moving() != 0U) &&
             (arm_servo_executor_is_expanded() != 0U)) ? 1U : 0U;
    if ((risky != 0U) && (g_risk_active == 0U))
    {
        g_risk_event_count++;
    }
    g_risk_active = risky;
}

uint32_t safety_supervisor_risk_event_count(void)
{
    return g_risk_event_count;
}

uint32_t safety_supervisor_arm_watchdog_count(void)
{
    return g_arm_watchdog_count;
}
