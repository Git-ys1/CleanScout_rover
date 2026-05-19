#include "app_telemetry.h"

#include "app_chassis.h"
#include "./Components/y_motor/y_motor.h"

static uint8_t g_telemetry_divider = 0;

static long scale_to_milli(float value)
{
    if (value >= 0.0f)
    {
        return (long)(value * 1000.0f + 0.5f);
    }

    return (long)(value * 1000.0f - 0.5f);
}

static void print_fixed3(float value)
{
    long milli = scale_to_milli(value);
    long integer = 0;
    long fraction = 0;

    if (milli < 0)
    {
        printf("-");
        milli = -milli;
    }

    integer = milli / 1000;
    fraction = milli % 1000;
    printf("%ld.%03ld", integer, fraction);
}

void app_telemetry_init(void)
{
    g_telemetry_divider = 0;
}

void app_telemetry_tick_20ms(void)
{
    const csr_chassis_state_t *state = app_chassis_get_state();

    g_telemetry_divider++;
    if (g_telemetry_divider < 5)
    {
        return;
    }
    g_telemetry_divider = 0;

    printf("CNT,%d,%d,%d,%d\r\n",
           Wheel_A.CNT_RT,
           Wheel_B.CNT_RT,
           Wheel_C.CNT_RT,
           Wheel_D.CNT_RT);

    printf("VEL,");
    print_fixed3((float)Wheel_A.RT);
    printf(",");
    print_fixed3((float)Wheel_B.RT);
    printf(",");
    print_fixed3((float)Wheel_C.RT);
    printf(",");
    print_fixed3((float)Wheel_D.RT);
    printf(",");
    print_fixed3(state->target[0]);
    printf(",");
    print_fixed3(state->target[1]);
    printf(",");
    print_fixed3(state->target[2]);
    printf(",");
    print_fixed3(state->target[3]);
    printf("\r\n");

    printf("PWM,%d,%d,%d,%d\r\n", Wheel_A.PWM, Wheel_B.PWM, Wheel_C.PWM, Wheel_D.PWM);
}
