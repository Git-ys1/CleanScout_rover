#include "main.h"

static int16_t g_last_pwm[CSR_CHANNEL_COUNT] = {0};

#define CSR_DRIVE_DOMINANT_MAX 2000U
#define CSR_UNIFIED_DRIVE_MIN 1000U

static const uint16_t g_effective_pwm_min_pos[CSR_CHANNEL_COUNT] = {
    /* Keep all four motors on the same bringup floor. */
    CSR_EFFECTIVE_PWM_MIN,
    CSR_EFFECTIVE_PWM_MIN,
    CSR_EFFECTIVE_PWM_MIN,
    CSR_EFFECTIVE_PWM_MIN
};

static const uint16_t g_effective_pwm_min_neg[CSR_CHANNEL_COUNT] = {
    /* Keep reverse symmetric with forward. */
    CSR_EFFECTIVE_PWM_MIN,
    CSR_EFFECTIVE_PWM_MIN,
    CSR_EFFECTIVE_PWM_MIN,
    CSR_EFFECTIVE_PWM_MIN
};

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

static uint16_t csr_motor_effective_min(csr_channel_t channel, int16_t signed_pwm)
{
    if (channel >= CSR_CHANNEL_COUNT)
    {
        return CSR_EFFECTIVE_PWM_MIN;
    }
    return (signed_pwm >= 0) ? g_effective_pwm_min_pos[channel] : g_effective_pwm_min_neg[channel];
}

static uint16_t csr_motor_scale_drive(uint16_t magnitude)
{
    uint32_t scaled;

    if (magnitude == 0U)
    {
        return 0U;
    }

    if (magnitude > CSR_INPUT_PWM_MAX)
    {
        magnitude = CSR_INPUT_PWM_MAX;
    }

    scaled = CSR_UNIFIED_DRIVE_MIN;
    scaled += ((uint32_t)(magnitude - 1U) * (uint32_t)(CSR_DRIVE_DOMINANT_MAX - CSR_UNIFIED_DRIVE_MIN)) / (uint32_t)(CSR_INPUT_PWM_MAX - 1);

    if (scaled > CSR_TIM8_PWM_TOP)
    {
        scaled = CSR_TIM8_PWM_TOP;
    }

    return (uint16_t)scaled;
}

static void csr_motor_apply_unified(csr_channel_t channel, BitAction in1_level, uint16_t magnitude)
{
    uint16_t drive = csr_motor_scale_drive(magnitude);
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

    /* CN1 truth:
     * +pwm should be the physical "positive" direction,
     * which currently maps to IN1=RESET and IN2 high-dominant.
     * -pwm is the opposite pair.
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

    /* CN2 truth:
     * +pwm -> IN1=SET and IN2 low-dominant
     * -pwm -> opposite pair
     */
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

    /* CN3 aligned truth:
     * +pwm -> unified positive direction
     * -pwm -> unified negative direction
     */
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

    /* CN4 aligned truth:
     * +pwm -> unified positive direction
     * -pwm -> unified negative direction
     */
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
    uint16_t magnitude;

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

    magnitude = (uint16_t)((signed_pwm > 0) ? signed_pwm : -signed_pwm);
    if (magnitude < csr_motor_effective_min(channel, signed_pwm))
    {
        signed_pwm = (signed_pwm > 0) ? (int16_t)csr_motor_effective_min(channel, signed_pwm) : (int16_t)(-csr_motor_effective_min(channel, signed_pwm));
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
