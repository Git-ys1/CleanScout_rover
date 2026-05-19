#include "app_motor.h"

#include "./Components/y_encoder/y_encoder.h"
#include "./Components/y_motor/y_motor.h"

#define CSR_TARGET_EPSILON_MPS              0.001f
#define CSR_PWM_LIMIT                       900
#define CSR_VELOCITY_FILTER_ALPHA           0.35f
#define CSR_FEEDFORWARD_GAIN_PWM_PER_MPS    3200.0f
#define CSR_FEEDBACK_KP_PWM_PER_MPS         250.0f
#define CSR_FEEDBACK_KI_PWM_PER_MPS         0.0f
#define CSR_INTEGRAL_LIMIT_MPS_S            0.20f

static const int8_t g_drive_sign[4] = {-1, -1, -1, -1};
static const int8_t g_encoder_sign[4] = {-1, -1, -1, -1};
static const int16_t g_min_effective_pwm[4] = {360, 360, 420, 420};

static float g_filtered_velocity[4] = {0.0f, 0.0f, 0.0f, 0.0f};
static float g_integral_term[4] = {0.0f, 0.0f, 0.0f, 0.0f};

static float csr_absf(float value)
{
    if (value < 0.0f)
    {
        return -value;
    }

    return value;
}

static float csr_clampf(float value, float min_value, float max_value)
{
    if (value < min_value)
    {
        return min_value;
    }

    if (value > max_value)
    {
        return max_value;
    }

    return value;
}

static int16_t csr_clamp_pwm(float value)
{
    float clamped = csr_clampf(value, (float)(-CSR_PWM_LIMIT), (float)CSR_PWM_LIMIT);

    if (clamped >= 0.0f)
    {
        return (int16_t)(clamped + 0.5f);
    }

    return (int16_t)(clamped - 0.5f);
}

static void csr_reset_wheel_controller(uint8_t wheel_index)
{
    g_filtered_velocity[wheel_index] = 0.0f;
    g_integral_term[wheel_index] = 0.0f;
}

static int16_t csr_read_encoder_delta(uint8_t wheel_index)
{
    switch (wheel_index)
    {
    case 0:
        return ENCODER_A_GetCounter();
    case 1:
        return ENCODER_B_GetCounter();
    case 2:
        return ENCODER_C_GetCounter();
    default:
        return ENCODER_D_GetCounter();
    }
}

static int16_t csr_compute_physical_pwm(uint8_t wheel_index, float target_mps, float measured_mps)
{
    float target_sign = 0.0f;
    float error = 0.0f;
    float base_pwm = 0.0f;
    float correction_pwm = 0.0f;
    float output_pwm = 0.0f;

    if (csr_absf(target_mps) <= CSR_TARGET_EPSILON_MPS)
    {
        g_integral_term[wheel_index] = 0.0f;
        return 0;
    }

    target_sign = (target_mps >= 0.0f) ? 1.0f : -1.0f;
    error = target_mps - measured_mps;

    g_integral_term[wheel_index] += error * CSR_WHEEL_CONTROL_DT_S;
    g_integral_term[wheel_index] = csr_clampf(
        g_integral_term[wheel_index],
        -CSR_INTEGRAL_LIMIT_MPS_S,
        CSR_INTEGRAL_LIMIT_MPS_S);

    base_pwm = (float)g_min_effective_pwm[wheel_index] +
               csr_absf(target_mps) * CSR_FEEDFORWARD_GAIN_PWM_PER_MPS;
    correction_pwm = error * CSR_FEEDBACK_KP_PWM_PER_MPS +
                     g_integral_term[wheel_index] * CSR_FEEDBACK_KI_PWM_PER_MPS;

    output_pwm = target_sign * base_pwm + correction_pwm;

    if ((target_sign > 0.0f) && (output_pwm < 0.0f))
    {
        output_pwm = 0.0f;
    }
    else if ((target_sign < 0.0f) && (output_pwm > 0.0f))
    {
        output_pwm = 0.0f;
    }

    return csr_clamp_pwm(output_pwm);
}

static void csr_update_wheel_state(uint8_t wheel_index, ROBOT_Wheel *wheel)
{
    int16_t raw_delta = 0;
    int16_t signed_delta = 0;
    float measured_velocity = 0.0f;
    int16_t physical_pwm = 0;
    int16_t driver_pwm = 0;

    raw_delta = csr_read_encoder_delta(wheel_index);
    signed_delta = (int16_t)(raw_delta * g_encoder_sign[wheel_index]);
    measured_velocity = (float)signed_delta * CSR_WHEEL_COUNT_TO_MPS;

    g_filtered_velocity[wheel_index] +=
        (measured_velocity - g_filtered_velocity[wheel_index]) * CSR_VELOCITY_FILTER_ALPHA;

    wheel->CNT_RT = signed_delta;
    wheel->RT = (double)g_filtered_velocity[wheel_index];

    physical_pwm = csr_compute_physical_pwm(wheel_index, wheel->TG, (float)wheel->RT);
    driver_pwm = (int16_t)(physical_pwm * g_drive_sign[wheel_index]);
    wheel->PWM = csr_clamp_pwm((float)driver_pwm);
}

void motor_speed_set(float A, float B, float C, float D)
{
    Wheel_A.TG = A;
    Wheel_B.TG = B;
    Wheel_C.TG = C;
    Wheel_D.TG = D;
}

void app_motor_init(void)
{
    uint8_t index = 0;

    motor_init();
    Encoder_Init();

    Wheel_A.CNT_RT = 0;
    Wheel_B.CNT_RT = 0;
    Wheel_C.CNT_RT = 0;
    Wheel_D.CNT_RT = 0;
    Wheel_A.RT = 0.0;
    Wheel_B.RT = 0.0;
    Wheel_C.RT = 0.0;
    Wheel_D.RT = 0.0;
    Wheel_A.PWM = 0;
    Wheel_B.PWM = 0;
    Wheel_C.PWM = 0;
    Wheel_D.PWM = 0;
    Wheel_A.TG = 0.0f;
    Wheel_B.TG = 0.0f;
    Wheel_C.TG = 0.0f;
    Wheel_D.TG = 0.0f;

    for (index = 0; index < 4; index++)
    {
        csr_reset_wheel_controller(index);
    }
}

void app_motor_run(void)
{
    csr_update_wheel_state(0, &Wheel_A);
    csr_update_wheel_state(1, &Wheel_B);
    csr_update_wheel_state(2, &Wheel_C);
    csr_update_wheel_state(3, &Wheel_D);

    MOTOR_A_SetSpeed(Wheel_A.PWM);
    MOTOR_B_SetSpeed(Wheel_B.PWM);
    MOTOR_C_SetSpeed(Wheel_C.PWM);
    MOTOR_D_SetSpeed(Wheel_D.PWM);
}
