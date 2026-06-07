#include "main.h"

/*
 * OpenRF1 底盘运行模式。
 *
 * STOP        ：四路立即停止，控制状态清零；
 * RAW         ：M 命令直接给某一路原始 PWM，仅用于底层诊断；
 * CLOSED_LOOP ：W 命令锁存四轮目标速度，50Hz 增量 PI 持续跟踪。
 */
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

/* 电机执行状态。 */
static int16_t g_raw_pwm[CSR_CHANNEL_COUNT] = {0, 0, 0, 0};
static int16_t g_output_pwm[CSR_CHANNEL_COUNT] = {0, 0, 0, 0};

/*
 * 速度闭环状态。
 *
 * cmd  ：串口 W 命令的原始目标；
 * ramp ：经过加速度限制后，真正交给 PI 的目标；
 * measured/filtered：编码器速度及其低通结果。
 */
static float g_target_vel_cmd[CSR_CHANNEL_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};
static float g_target_vel_ramp[CSR_CHANNEL_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};
static float g_measured_vel[CSR_CHANNEL_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};
static float g_filtered_vel[CSR_CHANNEL_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};

/*
 * 增量 PI 状态。
 *
 * g_pi_output_accum 保存累计 PWM，不是传统位置式 PI 的“积分误差”。
 * 这个命名能避免后续维护者把它误当成 error*dt 再做一次积分。
 */
static float g_pi_output_accum[CSR_CHANNEL_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};
static float g_prev_error[CSR_CHANNEL_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};

/* NAVDBG 使用的诊断缓存。增量 PI 没有独立前馈，因此 ff 始终为 0。 */
static float g_debug_ff_pwm[CSR_CHANNEL_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};
static float g_debug_pid_increment[CSR_CHANNEL_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};
static uint8_t g_debug_saturated[CSR_CHANNEL_COUNT] = {0U, 0U, 0U, 0U};

/*
 * 四个电机型号一致，控制参数保持一致。
 * 数组顺序固定为 CN1/LR、CN2/LF、CN3/RR、CN4/RF。
 */
static const float g_kp[CSR_CHANNEL_COUNT] =
{
    CSR_PI_KP_DEFAULT,
    CSR_PI_KP_DEFAULT,
    CSR_PI_KP_DEFAULT,
    CSR_PI_KP_DEFAULT
};

static const float g_ki[CSR_CHANNEL_COUNT] =
{
    CSR_PI_KI_DEFAULT,
    CSR_PI_KI_DEFAULT,
    CSR_PI_KI_DEFAULT,
    CSR_PI_KI_DEFAULT
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
    return (value < 0.0f) ? -value : value;
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
    return (value >= 0.0f) ? (int16_t)(value + 0.5f) : (int16_t)(value - 0.5f);
}

static void csr_systick_init(void)
{
    SysTick_Config(SystemCoreClock / 1000U);
}

/*
 * CN3 编码器使用 TIM2 全重映射后的 PA15/PB3。
 * 必须在所有 GPIO/编码器初始化之前关闭 JTAG、保留 SWD，才能释放
 * PA15/PB3，同时继续使用 STLink 下载与调试。
 */
static void csr_init_debug_ports(void)
{
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO, ENABLE);
    GPIO_PinRemapConfig(GPIO_Remap_SWJ_JTAGDisable, ENABLE);
}

static void csr_clear_pi_state(void)
{
    uint8_t index;

    for (index = 0; index < CSR_CHANNEL_COUNT; index++)
    {
        g_pi_output_accum[index] = 0.0f;
        g_prev_error[index] = 0.0f;
        g_filtered_vel[index] = 0.0f;
        g_measured_vel[index] = 0.0f;
        g_debug_ff_pwm[index] = 0.0f;
        g_debug_pid_increment[index] = 0.0f;
        g_debug_saturated[index] = 0U;
    }
}

static void csr_clear_velocity_targets(void)
{
    uint8_t index;

    for (index = 0; index < CSR_CHANNEL_COUNT; index++)
    {
        g_target_vel_cmd[index] = 0.0f;
        g_target_vel_ramp[index] = 0.0f;
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

/* 上电自动前进仅用于架空排障，正式配置默认不会编入有效动作。 */
static void csr_start_boot_forward_test(void)
{
#if CSR_BOOT_FORWARD_TEST_ENABLE
    uint8_t index;

    csr_stop_all();
    for (index = 0; index < CSR_CHANNEL_COUNT; index++)
    {
        g_target_vel_cmd[index] = CSR_BOOT_FORWARD_TEST_SPEED_MPS;
    }
    g_control_mode = CSR_MODE_CLOSED_LOOP;
    g_last_command_ms = csr_millis();
#endif
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
    g_pi_output_accum[channel] = 0.0f;
    g_prev_error[channel] = 0.0f;
    g_output_pwm[channel] = 0;
    g_debug_pid_increment[channel] = 0.0f;
    g_debug_saturated[channel] = 0U;
}

static float csr_ramp_target(float current, float target)
{
    const float step_limit = CSR_WHEEL_DV_PER_TICK;

    if (target > current)
    {
        current += step_limit;
        if (current > target)
        {
            current = target;
        }
    }
    else if (target < current)
    {
        current -= step_limit;
        if (current < target)
        {
            current = target;
        }
    }

    return current;
}

/*
 * 增量 PI：
 *   delta_pwm = Kp*(e[k]-e[k-1]) + Ki*e[k]*dt
 *   pwm[k]    = clamp(pwm[k-1] + delta_pwm)
 *
 * 相比“固定大前馈 + 位置式 PI”，该算法在当前机械结构上减少了低速命令
 * 突然跳到大 PWM 的现象。达到 PWM 上限后直接钳位累计输出，避免继续增长。
 */
static int16_t csr_compute_closed_loop_pwm(csr_channel_t channel, float target, float measured)
{
    float error;
    float increment;
    float candidate_output;
    float limited_output;
    float effective_output;
    const float dt = (float)CSR_CONTROL_PERIOD_MS / 1000.0f;

    if (csr_absf(target) < 0.0005f)
    {
        csr_reset_channel_pi_state(channel);
        return 0;
    }

    error = target - measured;
    increment = (g_kp[channel] * (error - g_prev_error[channel]))
              + (g_ki[channel] * error * dt);

    candidate_output = g_pi_output_accum[channel] + increment;
    limited_output = csr_clampf(
        candidate_output,
        -(float)CSR_INPUT_PWM_MAX,
        (float)CSR_INPUT_PWM_MAX
    );

    g_pi_output_accum[channel] = limited_output;
    g_prev_error[channel] = error;
    g_debug_ff_pwm[channel] = 0.0f;
    g_debug_pid_increment[channel] = increment;
    g_debug_saturated[channel] = (candidate_output != limited_output) ? 1U : 0U;

    effective_output = limited_output * (float)g_csr_motor_dir_sign[channel];
    return csr_float_to_pwm(effective_output);
}

static void csr_control_tick(void)
{
    uint8_t index;
    float raw_velocity;

    /*
     * 每个周期都先采集四路编码器，保证 STOP/RAW/CLOSED_LOOP 三种模式下
     * 的 E、D 和遥测数据持续更新。
     */
    for (index = 0; index < CSR_CHANNEL_COUNT; index++)
    {
        raw_velocity = csr_measure_speed_mps((csr_channel_t)index);
        g_filtered_vel[index] =
            (CSR_VEL_FILTER_ALPHA * g_filtered_vel[index])
            + ((1.0f - CSR_VEL_FILTER_ALPHA) * raw_velocity);
        g_measured_vel[index] = g_filtered_vel[index];
        g_target_vel_ramp[index] = csr_ramp_target(
            g_target_vel_ramp[index],
            g_target_vel_cmd[index]
        );
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
        g_output_pwm[index] = csr_compute_closed_loop_pwm(
            (csr_channel_t)index,
            g_target_vel_ramp[index],
            g_measured_vel[index]
        );
        csr_motor_set((csr_channel_t)index, g_output_pwm[index]);
    }
}

static void csr_send_telemetry(void)
{
    /* 保留既有 VEL/PWM 格式，避免破坏树莓派端解析。 */
    csr_proto_send_vel(g_measured_vel, g_target_vel_cmd);
    csr_proto_send_pwm(g_output_pwm);

    /*
     * NAVDBG 中 ff 为 0，corr 字段记录本周期增量 PI 的 delta_pwm。
     * ramp 字段现在与控制器实际使用的目标完全一致。
     */
    csr_proto_send_navdbg(
        g_target_vel_cmd,
        g_target_vel_ramp,
        g_measured_vel,
        g_debug_ff_pwm,
        g_debug_pid_increment,
        g_output_pwm,
        g_debug_saturated
    );
}

static void csr_handle_command(const csr_proto_command_t *command)
{
    uint8_t index;
    int32_t count;
    int32_t delta;
    uint8_t phase_a;
    uint8_t phase_b;
    uint16_t timer_count;

    g_last_command_ms = csr_millis();

    switch (command->type)
    {
    case CSR_CMD_W:
        if (g_control_mode != CSR_MODE_CLOSED_LOOP)
        {
            csr_clear_velocity_targets();
            csr_clear_pi_state();
            csr_clear_raw_targets();
        }

        for (index = 0; index < CSR_CHANNEL_COUNT; index++)
        {
            if (csr_target_sign_reversed(g_target_vel_cmd[index], command->target_vel[index]))
            {
                csr_reset_channel_pi_state((csr_channel_t)index);
            }
            g_target_vel_cmd[index] = command->target_vel[index];
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
#if CSR_BOOT_FORWARD_TEST_ENABLE
    if (g_control_mode == CSR_MODE_CLOSED_LOOP)
    {
        g_last_command_ms = now_ms;
        return;
    }
#else
    if (g_control_mode == CSR_MODE_CLOSED_LOOP)
    {
        if ((uint32_t)(now_ms - g_last_command_ms) > CSR_W_COMMAND_TIMEOUT_MS)
        {
            csr_stop_all();
            g_last_command_ms = now_ms;
        }
        return;
    }
#endif

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

    /* 初始化顺序不可随意调整，JTAG 释放必须早于 CN3 编码器初始化。 */
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
    csr_start_boot_forward_test();

    while (1)
    {
        if (csr_proto_poll(&command) != 0)
        {
            csr_handle_command(&command);
        }

        now_ms = csr_millis();

        /*
         * 正常情况下每 20ms 执行一次。若主循环阻塞超过两个周期，直接
         * 对齐当前时间而不连续补跑，避免短时间连续计算导致 PWM 突跳。
         */
        if ((uint32_t)(now_ms - g_last_control_ms) >= CSR_CONTROL_PERIOD_MS)
        {
            if ((uint32_t)(now_ms - g_last_control_ms) > (CSR_CONTROL_PERIOD_MS * 2UL))
            {
                g_last_control_ms = now_ms;
            }
            else
            {
                g_last_control_ms += CSR_CONTROL_PERIOD_MS;
            }
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
