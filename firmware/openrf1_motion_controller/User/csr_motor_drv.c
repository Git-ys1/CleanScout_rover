#include "main.h"

static int16_t g_last_pwm[CSR_CHANNEL_COUNT] = {0};

static void csr_motor_write_raw(csr_channel_t channel, BitAction in1_level, uint16_t compare)
{
    if (compare > CSR_TIM8_PWM_TOP)
    {
        compare = CSR_TIM8_PWM_TOP;
    }

    switch (channel)
    {
    case CSR_CHANNEL_CN1:
        GPIO_WriteBit(GPIOA, GPIO_Pin_8, in1_level);
        TIM_SetCompare1(TIM8, compare);
        break;
    case CSR_CHANNEL_CN2:
        GPIO_WriteBit(GPIOA, GPIO_Pin_11, in1_level);
        TIM_SetCompare2(TIM8, compare);
        break;
    case CSR_CHANNEL_CN3:
        GPIO_WriteBit(GPIOA, GPIO_Pin_12, in1_level);
        TIM_SetCompare3(TIM8, compare);
        break;
    case CSR_CHANNEL_CN4:
        GPIO_WriteBit(GPIOC, GPIO_Pin_10, in1_level);
        TIM_SetCompare4(TIM8, compare);
        break;
    default:
        break;
    }
}

static uint16_t csr_motor_scale_drive(uint16_t magnitude)
{
    if (magnitude == 0U)
    {
        return 0U;
    }

    if (magnitude > CSR_INPUT_PWM_MAX)
    {
        magnitude = CSR_INPUT_PWM_MAX;
    }

    if (magnitude > CSR_TIM8_PWM_TOP)
    {
        magnitude = CSR_TIM8_PWM_TOP;
    }

    return magnitude;
}

static uint16_t csr_motor_normalize_channel_drive(BitAction in1_level, uint16_t drive)
{
    if (drive == 0U)
    {
        return 0U;
    }

    /*
     * 板级实测表明，IN1=RESET 相位的有效占空比斜率与 SET 相位相反：
     * 原始 compare 越小，实际驱动力反而越强。这里统一换算，使控制层
     * 无论正反方向都只需要遵守“PWM 绝对值越大，驱动力越强”。
     */
    if (in1_level == Bit_RESET)
    {
        if (drive >= CSR_RESET_PHASE_OFFSET)
        {
            return 1U;
        }
        return (uint16_t)(CSR_RESET_PHASE_OFFSET - drive);
    }

    return drive;
}

static void csr_motor_apply_unified(csr_channel_t channel, BitAction in1_level, uint16_t magnitude)
{
    uint16_t drive = csr_motor_scale_drive(magnitude);
    drive = csr_motor_normalize_channel_drive(in1_level, drive);

    /*
     * AT8236 当前接线下，非零驱动需要落在 TIM8 高 compare 侧，方向由
     * IN1 电平选择。该转换属于板级真值，禁止在 PID 层重复补偿。
     */
    if (drive != 0U)
    {
        drive = (uint16_t)(CSR_TIM8_PWM_TOP - drive);
    }

    csr_motor_write_raw(channel, in1_level, drive);
}

static void csr_motor_apply_cn1(int16_t signed_pwm)
{
    uint16_t magnitude = (uint16_t)((signed_pwm > 0) ? signed_pwm : -signed_pwm);

    if (signed_pwm == 0)
    {
        csr_motor_stop(CSR_CHANNEL_CN1);
        return;
    }

    /*
     * CN1 H 桥真值：
     * 正 PWM -> IN1=RESET；负 PWM -> IN1=SET。
     * 车体前进语义还会经过 g_csr_motor_dir_sign，不等同于此处正负号。
     */
    if (signed_pwm > 0)
    {
        csr_motor_apply_unified(CSR_CHANNEL_CN1, Bit_RESET, magnitude);
    }
    else
    {
        csr_motor_apply_unified(CSR_CHANNEL_CN1, Bit_SET, magnitude);
    }
}

static void csr_motor_apply_cn2(int16_t signed_pwm)
{
    uint16_t magnitude = (uint16_t)((signed_pwm > 0) ? signed_pwm : -signed_pwm);

    if (signed_pwm == 0)
    {
        csr_motor_stop(CSR_CHANNEL_CN2);
        return;
    }

    /* CN2 H 桥真值：正 PWM -> IN1=SET；负 PWM -> IN1=RESET。 */
    if (signed_pwm > 0)
    {
        csr_motor_apply_unified(CSR_CHANNEL_CN2, Bit_SET, magnitude);
    }
    else
    {
        csr_motor_apply_unified(CSR_CHANNEL_CN2, Bit_RESET, magnitude);
    }
}

static void csr_motor_apply_cn3(int16_t signed_pwm)
{
    uint16_t magnitude = (uint16_t)((signed_pwm > 0) ? signed_pwm : -signed_pwm);

    if (signed_pwm == 0)
    {
        csr_motor_stop(CSR_CHANNEL_CN3);
        return;
    }

    /* CN3 H 桥真值：正 PWM -> IN1=SET；负 PWM -> IN1=RESET。 */
    if (signed_pwm > 0)
    {
        csr_motor_apply_unified(CSR_CHANNEL_CN3, Bit_SET, magnitude);
    }
    else
    {
        csr_motor_apply_unified(CSR_CHANNEL_CN3, Bit_RESET, magnitude);
    }
}

static void csr_motor_apply_cn4(int16_t signed_pwm)
{
    uint16_t magnitude = (uint16_t)((signed_pwm > 0) ? signed_pwm : -signed_pwm);

    if (signed_pwm == 0)
    {
        csr_motor_stop(CSR_CHANNEL_CN4);
        return;
    }

    /* CN4 H 桥真值：正 PWM -> IN1=RESET；负 PWM -> IN1=SET。 */
    if (signed_pwm > 0)
    {
        csr_motor_apply_unified(CSR_CHANNEL_CN4, Bit_RESET, magnitude);
    }
    else
    {
        csr_motor_apply_unified(CSR_CHANNEL_CN4, Bit_SET, magnitude);
    }
}

void csr_motor_init(void)
{
    GPIO_InitTypeDef gpio_init;
    TIM_TimeBaseInitTypeDef tim_base_init;
    TIM_OCInitTypeDef tim_oc_init;

    /*
     * TIM8 CH1~CH4 输出四路 PWM；PA8/PA11/PA12/PC10 控制对应 H 桥
     * 的另一输入端。四路共用同一计数周期，保证 PWM 时间基准一致。
     */
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_TIM8 | RCC_APB2Periph_AFIO, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOC, ENABLE);

    GPIO_StructInit(&gpio_init);
    gpio_init.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7 | GPIO_Pin_8 | GPIO_Pin_9;
    gpio_init.GPIO_Mode = GPIO_Mode_AF_PP;
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOC, &gpio_init);

    gpio_init.GPIO_Pin = GPIO_Pin_8 | GPIO_Pin_11 | GPIO_Pin_12;
    gpio_init.GPIO_Mode = GPIO_Mode_Out_PP;
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &gpio_init);

    gpio_init.GPIO_Pin = GPIO_Pin_10;
    gpio_init.GPIO_Mode = GPIO_Mode_Out_PP;
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOC, &gpio_init);

    TIM_OCStructInit(&tim_oc_init);
    tim_oc_init.TIM_OCMode = TIM_OCMode_PWM1;
    tim_oc_init.TIM_OutputState = TIM_OutputState_Enable;
    tim_oc_init.TIM_OCPolarity = TIM_OCPolarity_High;
    tim_oc_init.TIM_Pulse = 0;

    TIM_OC1Init(TIM8, &tim_oc_init);
    TIM_OC2Init(TIM8, &tim_oc_init);
    TIM_OC3Init(TIM8, &tim_oc_init);
    TIM_OC4Init(TIM8, &tim_oc_init);

    TIM_TimeBaseStructInit(&tim_base_init);
    tim_base_init.TIM_ClockDivision = TIM_CKD_DIV1;
    tim_base_init.TIM_CounterMode = TIM_CounterMode_Up;
    tim_base_init.TIM_Period = CSR_TIM8_PWM_TOP;
    tim_base_init.TIM_Prescaler = 1;
    TIM_TimeBaseInit(TIM8, &tim_base_init);
    TIM_Cmd(TIM8, ENABLE);
    TIM_CtrlPWMOutputs(TIM8, ENABLE);

    csr_motor_stop_all();
}

void csr_motor_stop(csr_channel_t channel)
{
    if (channel >= CSR_CHANNEL_COUNT)
    {
        return;
    }

    g_last_pwm[channel] = 0;
    csr_motor_write_raw(channel, Bit_RESET, 0);
}

void csr_motor_stop_all(void)
{
    uint8_t channel;
    for (channel = 0; channel < CSR_CHANNEL_COUNT; channel++)
    {
        csr_motor_stop((csr_channel_t)channel);
    }
}

void csr_motor_set(csr_channel_t channel, int16_t signed_pwm)
{
    if (channel >= CSR_CHANNEL_COUNT)
    {
        return;
    }

    if (signed_pwm > CSR_INPUT_PWM_MAX)
    {
        signed_pwm = CSR_INPUT_PWM_MAX;
    }
    else if (signed_pwm < -CSR_INPUT_PWM_MAX)
    {
        signed_pwm = -CSR_INPUT_PWM_MAX;
    }

    if (signed_pwm == 0)
    {
        csr_motor_stop(channel);
        return;
    }

    switch (channel)
    {
    case CSR_CHANNEL_CN1:
        csr_motor_apply_cn1(signed_pwm);
        break;
    case CSR_CHANNEL_CN2:
        csr_motor_apply_cn2(signed_pwm);
        break;
    case CSR_CHANNEL_CN3:
        csr_motor_apply_cn3(signed_pwm);
        break;
    case CSR_CHANNEL_CN4:
        csr_motor_apply_cn4(signed_pwm);
        break;
    default:
        return;
    }

    g_last_pwm[channel] = signed_pwm;
}

int16_t csr_motor_last_pwm(csr_channel_t channel)
{
    if (channel >= CSR_CHANNEL_COUNT)
    {
        return 0;
    }
    return g_last_pwm[channel];
}
