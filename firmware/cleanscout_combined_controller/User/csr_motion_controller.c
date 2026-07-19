#include "main.h"

typedef enum
{
    CSR_MODE_STOP = 0,
    CSR_MODE_RAW = 1,
    CSR_MODE_CLOSED_LOOP = 2
} csr_control_mode_t;

static csr_control_mode_t g_control_mode;
static uint32_t g_last_command_ms;
static int16_t g_raw_pwm[CSR_CHANNEL_COUNT];
static int16_t g_output_pwm[CSR_CHANNEL_COUNT];
static float g_target_vel_cmd[CSR_CHANNEL_COUNT];
static float g_target_vel_ramp[CSR_CHANNEL_COUNT];
static float g_measured_vel[CSR_CHANNEL_COUNT];
static float g_filtered_vel[CSR_CHANNEL_COUNT];
static float g_incremental_output[CSR_CHANNEL_COUNT];
static float g_prev_error[CSR_CHANNEL_COUNT];
static float g_kp[CSR_CHANNEL_COUNT] = {
    CSR_PI_KP_DEFAULT, CSR_PI_KP_DEFAULT, CSR_PI_KP_DEFAULT, CSR_PI_KP_DEFAULT
};
static float g_ki[CSR_CHANNEL_COUNT] = {
    CSR_PI_KI_DEFAULT, CSR_PI_KI_DEFAULT, CSR_PI_KI_DEFAULT, CSR_PI_KI_DEFAULT
};

static float csr_absf(float value)
{
    return (value < 0.0f) ? -value : value;
}

static float csr_clampf(float value, float minimum, float maximum)
{
    if (value < minimum)
    {
        return minimum;
    }
    if (value > maximum)
    {
        return maximum;
    }
    return value;
}

static int16_t csr_float_to_pwm(float value)
{
    return (value >= 0.0f) ? (int16_t)(value + 0.5f) : (int16_t)(value - 0.5f);
}

static void csr_clear_pi_state(void)
{
    uint8_t index;

    for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
    {
        g_incremental_output[index] = 0.0f;
        g_prev_error[index] = 0.0f;
        g_filtered_vel[index] = 0.0f;
        g_measured_vel[index] = 0.0f;
    }
}

static void csr_clear_velocity_targets(void)
{
    uint8_t index;

    for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
    {
        g_target_vel_cmd[index] = 0.0f;
        g_target_vel_ramp[index] = 0.0f;
    }
}

static void csr_clear_raw_targets(void)
{
    uint8_t index;

    for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
    {
        g_raw_pwm[index] = 0;
    }
}

void csr_motion_controller_stop(void)
{
    uint8_t index;

    csr_clear_velocity_targets();
    csr_clear_raw_targets();
    csr_clear_pi_state();
    for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
    {
        g_output_pwm[index] = 0;
    }
    csr_motor_stop_all();
    g_control_mode = CSR_MODE_STOP;
}

static void csr_apply_raw_outputs(void)
{
    uint8_t index;

    for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
    {
        g_output_pwm[index] = g_raw_pwm[index];
        csr_motor_set((csr_channel_t)index, g_output_pwm[index]);
    }
}

static float csr_measure_speed_mps(csr_channel_t channel)
{
    int32_t delta;

    delta = csr_encoder_read_and_reset(channel);
    return (float)delta * CSR_WHEEL_SPEED_SCALE;
}

static uint8_t csr_target_sign_reversed(float previous, float next)
{
    if ((csr_absf(previous) < 0.0005f) || (csr_absf(next) < 0.0005f))
    {
        return 0U;
    }
    return ((previous > 0.0f) != (next > 0.0f)) ? 1U : 0U;
}

static void csr_reset_channel_pi_state(csr_channel_t channel)
{
    g_incremental_output[channel] = 0.0f;
    g_prev_error[channel] = 0.0f;
    g_output_pwm[channel] = 0;
}

static int16_t csr_compute_closed_loop_pwm(csr_channel_t channel, float target, float measured)
{
    float error;
    float increment;
    float effective_output;

    if (csr_absf(target) < 0.0005f)
    {
        g_incremental_output[channel] = 0.0f;
        g_prev_error[channel] = 0.0f;
        return 0;
    }

    error = target - measured;
    increment = g_kp[channel] * (error - g_prev_error[channel])
              + g_ki[channel] * error * (CSR_CONTROL_PERIOD_MS / 1000.0f);
    g_incremental_output[channel] += increment;
    g_incremental_output[channel] = csr_clampf(
        g_incremental_output[channel],
        -(float)CSR_INPUT_PWM_MAX,
        (float)CSR_INPUT_PWM_MAX
    );
    g_prev_error[channel] = error;
    effective_output = g_incremental_output[channel] * (float)g_csr_motor_dir_sign[channel];
    return csr_float_to_pwm(effective_output);
}

void csr_motion_controller_init(uint32_t now_ms)
{
    csr_motor_init();
    csr_encoder_init();
    csr_motion_controller_stop();
    g_last_command_ms = now_ms;
}

void csr_motion_controller_tick(void)
{
    uint8_t index;
    float raw_velocity;
    float step_limit;

    step_limit = CSR_WHEEL_ACC_LIMIT_MPS2 * (CSR_CONTROL_PERIOD_MS / 1000.0f);
    for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
    {
        raw_velocity = csr_measure_speed_mps((csr_channel_t)index);
        g_filtered_vel[index] = (CSR_VEL_FILTER_ALPHA * g_filtered_vel[index])
                              + ((1.0f - CSR_VEL_FILTER_ALPHA) * raw_velocity);
        g_measured_vel[index] = g_filtered_vel[index];

        if (g_target_vel_cmd[index] > g_target_vel_ramp[index])
        {
            g_target_vel_ramp[index] += step_limit;
            if (g_target_vel_ramp[index] > g_target_vel_cmd[index])
            {
                g_target_vel_ramp[index] = g_target_vel_cmd[index];
            }
        }
        else if (g_target_vel_cmd[index] < g_target_vel_ramp[index])
        {
            g_target_vel_ramp[index] -= step_limit;
            if (g_target_vel_ramp[index] < g_target_vel_cmd[index])
            {
                g_target_vel_ramp[index] = g_target_vel_cmd[index];
            }
        }
    }

    if (g_control_mode != CSR_MODE_CLOSED_LOOP)
    {
        return;
    }

    for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
    {
        g_output_pwm[index] = csr_compute_closed_loop_pwm(
            (csr_channel_t)index,
            g_target_vel_ramp[index],
            g_measured_vel[index]
        );
        csr_motor_set((csr_channel_t)index, g_output_pwm[index]);
    }
}

void csr_motion_controller_handle(const csr_motion_command_t *command, uint32_t now_ms)
{
    uint8_t index;
    int32_t count;
    int32_t delta;
    uint8_t phase_a;
    uint8_t phase_b;
    uint16_t timer_count;

    g_last_command_ms = now_ms;
    switch (command->type)
    {
    case CSR_CMD_W:
        if (g_control_mode != CSR_MODE_CLOSED_LOOP)
        {
            csr_clear_velocity_targets();
            csr_clear_pi_state();
            csr_clear_raw_targets();
        }
        for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
        {
            if (csr_target_sign_reversed(g_target_vel_cmd[index], command->target_vel[index]) != 0U)
            {
                csr_reset_channel_pi_state((csr_channel_t)index);
            }
            g_target_vel_cmd[index] = command->target_vel[index];
        }
        g_control_mode = CSR_MODE_CLOSED_LOOP;
        csr_motion_link_send_ack("W");
        break;

    case CSR_CMD_M:
        if (g_control_mode != CSR_MODE_RAW)
        {
            csr_clear_velocity_targets();
            csr_clear_pi_state();
            csr_clear_raw_targets();
        }
        g_control_mode = CSR_MODE_RAW;
        g_raw_pwm[command->channel] = command->pwm;
        csr_apply_raw_outputs();
        csr_motion_link_send_ack("M");
        break;

    case CSR_CMD_E:
        count = csr_encoder_peek(command->channel);
        delta = csr_encoder_last_delta(command->channel);
        csr_motion_link_send_ack("E");
        csr_motion_link_send_enc(command->channel, count, delta);
        break;

    case CSR_CMD_D:
        count = csr_encoder_peek(command->channel);
        delta = csr_encoder_last_delta(command->channel);
        csr_encoder_debug_snapshot(command->channel, &phase_a, &phase_b, &timer_count);
        csr_motion_link_send_ack("D");
        csr_motion_link_send_dbg(command->channel, phase_a, phase_b, timer_count, count, delta);
        break;

    case CSR_CMD_STOP:
        csr_motion_controller_stop();
        csr_motion_link_send_ack("STOP");
        break;

    default:
        break;
    }
}

void csr_motion_controller_watchdog(uint32_t now_ms)
{
    uint32_t timeout;

    if (g_control_mode == CSR_MODE_STOP)
    {
        return;
    }
    timeout = (g_control_mode == CSR_MODE_CLOSED_LOOP) ? CSR_W_COMMAND_TIMEOUT_MS : CSR_RAW_COMMAND_TIMEOUT_MS;
    if ((uint32_t)(now_ms - g_last_command_ms) > timeout)
    {
        csr_motion_controller_stop();
        g_last_command_ms = now_ms;
    }
}

void csr_motion_controller_telemetry(void)
{
    csr_motion_link_send_vel(g_measured_vel, g_target_vel_cmd);
    csr_motion_link_send_pwm(g_output_pwm);
    csr_motion_link_send_navdbg(g_target_vel_cmd, g_target_vel_ramp, g_measured_vel, g_output_pwm);
}

uint8_t csr_motion_controller_is_stopped(void)
{
    return (g_control_mode == CSR_MODE_STOP) ? 1U : 0U;
}

uint8_t csr_motion_controller_is_moving(void)
{
    uint8_t index;

    for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
    {
        if ((csr_absf(g_target_vel_cmd[index]) > 0.0005f) ||
            (csr_absf(g_target_vel_ramp[index]) > 0.0005f) ||
            (g_output_pwm[index] != 0))
        {
            return 1U;
        }
    }
    return 0U;
}
