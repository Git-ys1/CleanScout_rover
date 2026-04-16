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
    int32_t effective_pwm;
    uint16_t magnitude;
    uint16_t compare;
    BitAction in1_level;

    if (channel >= CSR_CHANNEL_COUNT)
    {
        return;
    }

    effective_pwm = (int32_t)signed_pwm * (int32_t)g_csr_motor_dir_sign[channel];
    if (effective_pwm > CSR_INPUT_PWM_MAX)
    {
        effective_pwm = CSR_INPUT_PWM_MAX;
    }
    else if (effective_pwm < -CSR_INPUT_PWM_MAX)
    {
        effective_pwm = -CSR_INPUT_PWM_MAX;
    }

    if (effective_pwm == 0)
    {
        csr_motor_stop(channel);
        return;
    }

    magnitude = (uint16_t)((effective_pwm > 0) ? effective_pwm : -effective_pwm);
    if (magnitude < CSR_EFFECTIVE_PWM_MIN)
    {
        magnitude = CSR_EFFECTIVE_PWM_MIN;
    }
    if (magnitude > CSR_EFFECTIVE_PWM_MAX)
    {
        magnitude = CSR_EFFECTIVE_PWM_MAX;
    }

    if (effective_pwm > 0)
    {
        compare = magnitude;
        in1_level = Bit_RESET;
    }
    else
    {
        compare = (uint16_t)(CSR_TIM8_PWM_TOP - magnitude);
        in1_level = Bit_SET;
    }

    csr_motor_write_raw(channel, in1_level, compare);

    g_last_pwm[channel] = (int16_t)effective_pwm;
}

int16_t csr_motor_last_pwm(csr_channel_t channel)
{
    if (channel >= CSR_CHANNEL_COUNT)
    {
        return 0;
    }
    return g_last_pwm[channel];
}
