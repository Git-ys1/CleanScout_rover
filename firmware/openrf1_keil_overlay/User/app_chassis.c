#include "app_chassis.h"

#include "app_motor.h"
#include "./Components/y_timer/y_timer.h"

static csr_chassis_state_t g_chassis;

void app_chassis_init(void)
{
    g_chassis.target[0] = 0.0f;
    g_chassis.target[1] = 0.0f;
    g_chassis.target[2] = 0.0f;
    g_chassis.target[3] = 0.0f;
    g_chassis.last_command_ms = millis();
    g_chassis.timeout_ms = 400;

    motor_speed_set(0.0f, 0.0f, 0.0f, 0.0f);
}

void app_chassis_set_targets(float a, float b, float c, float d)
{
    g_chassis.target[0] = a;
    g_chassis.target[1] = b;
    g_chassis.target[2] = c;
    g_chassis.target[3] = d;
    g_chassis.last_command_ms = millis();

    motor_speed_set(a, b, c, d);
}

void app_chassis_stop(void)
{
    g_chassis.target[0] = 0.0f;
    g_chassis.target[1] = 0.0f;
    g_chassis.target[2] = 0.0f;
    g_chassis.target[3] = 0.0f;

    motor_speed_set(0.0f, 0.0f, 0.0f, 0.0f);
}

void app_chassis_tick_20ms(void)
{
    if ((millis() - g_chassis.last_command_ms) > g_chassis.timeout_ms)
    {
        app_chassis_stop();
    }
}

const csr_chassis_state_t *app_chassis_get_state(void)
{
    return &g_chassis;
}
