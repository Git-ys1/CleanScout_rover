#include "main.h"

typedef enum
{
    CSR_MODE_STOP = 0,
    CSR_MODE_RAW = 1,
    CSR_MODE_CLOSED_LOOP = 2
} csr_control_mode_t;

static volatile uint32_t g_csr_ms = 0;
static csr_control_mode_t g_control_mode = CSR_MODE_STOP;

static uint32_t g_last_command_ms = 0;
static uint32_t g_last_control_ms = 0;
static uint32_t g_last_telemetry_ms = 0;

static int16_t g_raw_pwm[CSR_CHANNEL_COUNT] = {0, 0, 0, 0};
static int16_t g_output_pwm[CSR_CHANNEL_COUNT] = {0, 0, 0, 0};

static float g_target_vel[CSR_CHANNEL_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};
static float g_measured_vel[CSR_CHANNEL_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};
static float g_filtered_vel[CSR_CHANNEL_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};
static float g_integral_state[CSR_CHANNEL_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};
static float g_prev_error[CSR_CHANNEL_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};

static float g_kp[CSR_CHANNEL_COUNT] = {
    CSR_PI_KP_DEFAULT,
    CSR_PI_KP_DEFAULT,
    CSR_PI_KP_DEFAULT,
    CSR_PI_KP_DEFAULT
};
static float g_ki[CSR_CHANNEL_COUNT] = {
    CSR_PI_KI_DEFAULT,
    CSR_PI_KI_DEFAULT,
    CSR_PI_KI_DEFAULT,
    CSR_PI_KI_DEFAULT
};
static float g_kd[CSR_CHANNEL_COUNT] = {
    CSR_PI_KD_DEFAULT,
    CSR_PI_KD_DEFAULT,
    CSR_PI_KD_DEFAULT,
    CSR_PI_KD_DEFAULT
};

static uint32_t csr_millis(void)
{
    return g_csr_ms;
}

void SysTick_Handler(void)
{
    g_csr_ms++;
}

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

static int16_t csr_float_to_pwm(float value)
{
    if (value >= 0.0f)
    {
        return (int16_t)(value + 0.5f);
    }
    return (int16_t)(value - 0.5f);
}

static void csr_systick_init(void)
{
    SysTick_Config(SystemCoreClock / 1000U);
}

static void csr_init_debug_ports(void)
{
    csr_encoder_apply_debug_remap();
}

static void csr_clear_pi_state(void)
{
    uint8_t index;

    for (index = 0; index < CSR_CHANNEL_COUNT; index++)
    {
        g_integral_state[index] = 0.0f;
        g_prev_error[index] = 0.0f;
        g_filtered_vel[index] = 0.0f;
        g_measured_vel[index] = 0.0f;
    }
}

static void csr_clear_velocity_targets(void)
{
    uint8_t index;

    for (index = 0; index < CSR_CHANNEL_COUNT; index++)
    {
        g_target_vel[index] = 0.0f;
    }
}

static void csr_clear_raw_targets(void)
{
    uint8_t index;

    for (index = 0; index < CSR_CHANNEL_COUNT; index++)
    {
        g_raw_pwm[index] = 0;
    }
}

static void csr_stop_all(void)
{
    uint8_t index;

    csr_clear_velocity_targets();
    csr_clear_raw_targets();
    csr_clear_pi_state();

    for (index = 0; index < CSR_CHANNEL_COUNT; index++)
    {
        g_output_pwm[index] = 0;
    }

    csr_motor_stop_all();
    g_control_mode = CSR_MODE_STOP;
}

static void csr_apply_raw_outputs(void)
{
    uint8_t index;

    for (index = 0; index < CSR_CHANNEL_COUNT; index++)
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

static int16_t csr_slew_pwm(int16_t previous, int16_t desired)
{
    int16_t delta;

    delta = (int16_t)(desired - previous);
    if (delta > CSR_PI_PWM_STEP_LIMIT)
    {
        return (int16_t)(previous + CSR_PI_PWM_STEP_LIMIT);
    }
    if (delta < -CSR_PI_PWM_STEP_LIMIT)
    {
        return (int16_t)(previous - CSR_PI_PWM_STEP_LIMIT);
    }
    return desired;
}

static int16_t csr_compute_closed_loop_pwm(csr_channel_t channel, float target, float measured)
{
    float error;
    float output;
    float effective_output;

    if (csr_absf(target) < 0.0005f)
    {
        g_integral_state[channel] = 0.0f;
        g_prev_error[channel] = 0.0f;
        return 0;
    }

    error = target - measured;
    g_integral_state[channel] += error * (CSR_CONTROL_PERIOD_MS / 1000.0f);
    g_integral_state[channel] = csr_clampf(g_integral_state[channel], -CSR_PI_INTEGRAL_LIMIT, CSR_PI_INTEGRAL_LIMIT);

    output = g_kp[channel] * error;
    output += g_ki[channel] * g_integral_state[channel];
    output += g_kd[channel] * ((error - g_prev_error[channel]) / (CSR_CONTROL_PERIOD_MS / 1000.0f));
    output = csr_clampf(output, -CSR_PI_OUTPUT_LIMIT, CSR_PI_OUTPUT_LIMIT);

    /*
     * Bringup 阶段禁止低速闭环反向刹车。
     * 反向输出会在死区附近造成“前后抖动”，先让控制器靠降 PWM / 停止来减速。
     */
    if ((target > 0.0f) && (output < 0.0f))
    {
        output = 0.0f;
        if (g_integral_state[channel] > 0.0f)
        {
            g_integral_state[channel] *= 0.7f;
        }
    }
    else if ((target < 0.0f) && (output > 0.0f))
    {
        output = 0.0f;
        if (g_integral_state[channel] < 0.0f)
        {
            g_integral_state[channel] *= 0.7f;
        }
    }

    g_prev_error[channel] = error;

    effective_output = output * (float)g_csr_motor_dir_sign[channel];
    return csr_float_to_pwm(effective_output);
}

static void csr_control_tick(void)
{
    uint8_t index;
    float raw_velocity;

    for (index = 0; index < CSR_CHANNEL_COUNT; index++)
    {
        raw_velocity = csr_measure_speed_mps((csr_channel_t)index);
        g_filtered_vel[index] = (CSR_VEL_FILTER_ALPHA * g_filtered_vel[index]) + ((1.0f - CSR_VEL_FILTER_ALPHA) * raw_velocity);
        g_measured_vel[index] = g_filtered_vel[index];
    }

    if (g_control_mode == CSR_MODE_RAW)
    {
        csr_apply_raw_outputs();
        return;
    }

    if (g_control_mode != CSR_MODE_CLOSED_LOOP)
    {
        return;
    }

    for (index = 0; index < CSR_CHANNEL_COUNT; index++)
    {
        g_output_pwm[index] = csr_slew_pwm(
            g_output_pwm[index],
            csr_compute_closed_loop_pwm(
            (csr_channel_t)index,
            g_target_vel[index],
            g_measured_vel[index]
            )
        );
        csr_motor_set((csr_channel_t)index, g_output_pwm[index]);
    }
}

static void csr_send_telemetry(void)
{
    csr_proto_send_vel(g_measured_vel, g_target_vel);
    csr_proto_send_pwm(g_output_pwm);
}

static void csr_handle_command(const csr_proto_command_t *command)
{
    uint8_t index;
    int32_t count;
    int32_t delta;
    uint8_t phase_a;
    uint8_t phase_b;
    uint16_t timer_count;
    int32_t exti_count_a;
    int32_t exti_count_b;
    uint32_t exti_pending;
    csr_encoder_reg_snapshot_t reg_snapshot;

    g_last_command_ms = csr_millis();

    switch (command->type)
    {
    case CSR_CMD_W:
        if (g_control_mode != CSR_MODE_CLOSED_LOOP)
        {
            csr_clear_pi_state();
            csr_clear_raw_targets();
        }

        for (index = 0; index < CSR_CHANNEL_COUNT; index++)
        {
            g_target_vel[index] = command->target_vel[index];
        }

        g_control_mode = CSR_MODE_CLOSED_LOOP;
        csr_proto_send_ack("W");
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
        csr_proto_send_ack("M");
        break;

    case CSR_CMD_E:
        count = csr_encoder_peek(command->channel);
        delta = csr_encoder_last_delta(command->channel);
        csr_proto_send_ack("E");
        csr_proto_send_enc(command->channel, count, delta);
        break;

    case CSR_CMD_D:
        count = csr_encoder_peek(command->channel);
        delta = csr_encoder_last_delta(command->channel);
        csr_encoder_debug_snapshot(command->channel, &phase_a, &phase_b, &timer_count);
        csr_proto_send_ack("D");
        csr_proto_send_dbg(command->channel, phase_a, phase_b, timer_count, count, delta);
        break;

    case CSR_CMD_R:
        csr_encoder_reg_snapshot(command->reg_target, &reg_snapshot);
        csr_proto_send_ack("R");
        csr_proto_send_reg(command->reg_target, &reg_snapshot);
        break;

    case CSR_CMD_X:
        csr_stop_all();
        if (csr_encoder_reconfigure(command->channel, command->input_mode, command->count_mode, command->ic_filter) != 0)
        {
            csr_proto_send_ack("X");
        }
        else
        {
            csr_proto_send_error("x_config");
        }
        break;

    case CSR_CMD_Y:
        csr_stop_all();
        if (csr_encoder_exti_probe_start(command->channel, command->input_mode) != 0)
        {
            csr_proto_send_ack("Y");
        }
        else
        {
            csr_proto_send_error("y_config");
        }
        break;

    case CSR_CMD_Q:
        csr_encoder_exti_snapshot(command->channel, &exti_count_a, &exti_count_b, &phase_a, &phase_b, &exti_pending);
        csr_proto_send_ack("Q");
        csr_proto_send_exti(command->channel, exti_count_a, exti_count_b, phase_a, phase_b, exti_pending);
        break;

    case CSR_CMD_STOP:
        csr_stop_all();
        csr_proto_send_ack("STOP");
        break;

    default:
        break;
    }
}

static void csr_check_watchdog(uint32_t now_ms)
{
    if (g_control_mode == CSR_MODE_CLOSED_LOOP)
    {
        if ((uint32_t)(now_ms - g_last_command_ms) > CSR_W_COMMAND_TIMEOUT_MS)
        {
            csr_stop_all();
            g_last_command_ms = now_ms;
        }
        return;
    }

    if (g_control_mode == CSR_MODE_RAW)
    {
        if ((uint32_t)(now_ms - g_last_command_ms) > CSR_RAW_COMMAND_TIMEOUT_MS)
        {
            csr_stop_all();
            g_last_command_ms = now_ms;
        }
    }
}

int main(void)
{
    csr_proto_command_t command;
    uint32_t now_ms;

    csr_init_debug_ports();
    csr_systick_init();
    csr_motor_init();
    csr_encoder_init();
    csr_proto_init(CSR_PROTO_BAUDRATE);
    csr_stop_all();

    g_last_command_ms = csr_millis();
    g_last_control_ms = g_last_command_ms;
    g_last_telemetry_ms = g_last_command_ms;

    csr_proto_send_ready();

    while (1)
    {
        if (csr_proto_poll(&command) != 0)
        {
            csr_handle_command(&command);
        }

        now_ms = csr_millis();

        while ((uint32_t)(now_ms - g_last_control_ms) >= CSR_CONTROL_PERIOD_MS)
        {
            g_last_control_ms += CSR_CONTROL_PERIOD_MS;
            csr_control_tick();
        }

        if ((uint32_t)(now_ms - g_last_telemetry_ms) >= CSR_TELEMETRY_PERIOD_MS)
        {
            g_last_telemetry_ms = now_ms;
            csr_send_telemetry();
        }

        csr_check_watchdog(now_ms);
    }
}
