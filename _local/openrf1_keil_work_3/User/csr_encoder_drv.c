#include "main.h"

#define CSR_ENCODER_TIM_PERIOD ((uint16_t)65535)

static int32_t g_encoder_total[CSR_CHANNEL_COUNT] = {0};
static int32_t g_encoder_last_delta[CSR_CHANNEL_COUNT] = {0};

static TIM_TypeDef *csr_encoder_timer(csr_channel_t channel)
{
    switch (channel)
    {
    case CSR_CHANNEL_CN1:
        return TIM5;
    case CSR_CHANNEL_CN2:
        return TIM3;
    case CSR_CHANNEL_CN3:
        return TIM2;
    case CSR_CHANNEL_CN4:
        return TIM4;
    default:
        return 0;
    }
}

static void csr_encoder_init_common(TIM_TypeDef *tim)
{
    TIM_TimeBaseInitTypeDef tim_base_init;
    TIM_ICInitTypeDef tim_ic_init;

    TIM_TimeBaseStructInit(&tim_base_init);
    tim_base_init.TIM_Prescaler = 0;
    tim_base_init.TIM_Period = CSR_ENCODER_TIM_PERIOD;
    tim_base_init.TIM_ClockDivision = TIM_CKD_DIV1;
    tim_base_init.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(tim, &tim_base_init);

    TIM_EncoderInterfaceConfig(tim, TIM_EncoderMode_TI12, TIM_ICPolarity_Rising, TIM_ICPolarity_Rising);

    TIM_ICStructInit(&tim_ic_init);
    tim_ic_init.TIM_ICFilter = 10;
    TIM_ICInit(tim, &tim_ic_init);

    TIM_SetCounter(tim, 0);
    TIM_Cmd(tim, ENABLE);
}

static void csr_encoder_init_cn1(void)
{
    GPIO_InitTypeDef gpio_init;

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM5, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

    gpio_init.GPIO_Pin = GPIO_Pin_0 | GPIO_Pin_1;
    gpio_init.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &gpio_init);

    csr_encoder_init_common(TIM5);
}

static void csr_encoder_init_cn2(void)
{
    GPIO_InitTypeDef gpio_init;

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

    gpio_init.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7;
    gpio_init.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &gpio_init);

    csr_encoder_init_common(TIM3);
}

static void csr_encoder_init_cn3(void)
{
    GPIO_InitTypeDef gpio_init;

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOB | RCC_APB2Periph_AFIO, ENABLE);

    GPIO_PinRemapConfig(GPIO_FullRemap_TIM2, ENABLE);

    gpio_init.GPIO_Pin = GPIO_Pin_15;
    gpio_init.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &gpio_init);

    gpio_init.GPIO_Pin = GPIO_Pin_3;
    GPIO_Init(GPIOB, &gpio_init);

    csr_encoder_init_common(TIM2);
}

static void csr_encoder_init_cn4(void)
{
    GPIO_InitTypeDef gpio_init;

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM4, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);

    gpio_init.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7;
    gpio_init.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOB, &gpio_init);

    csr_encoder_init_common(TIM4);
}

void csr_encoder_init(void)
{
    uint8_t index;

    csr_encoder_init_cn1();
    csr_encoder_init_cn2();
    csr_encoder_init_cn3();
    csr_encoder_init_cn4();

    for (index = 0; index < CSR_CHANNEL_COUNT; index++)
    {
        g_encoder_total[index] = 0;
        g_encoder_last_delta[index] = 0;
    }
}

int32_t csr_encoder_read_and_reset(csr_channel_t channel)
{
    TIM_TypeDef *tim;
    int32_t delta;

    tim = csr_encoder_timer(channel);
    if (tim == 0)
    {
        return 0;
    }

    delta = (int16_t)(tim->CNT);
    tim->CNT = 0;
    delta *= g_csr_encoder_dir_sign[channel];

    g_encoder_last_delta[channel] = delta;
    g_encoder_total[channel] += delta;
    return delta;
}

int32_t csr_encoder_peek(csr_channel_t channel)
{
    if (channel >= CSR_CHANNEL_COUNT)
    {
        return 0;
    }
    return g_encoder_total[channel];
}

int32_t csr_encoder_last_delta(csr_channel_t channel)
{
    if (channel >= CSR_CHANNEL_COUNT)
    {
        return 0;
    }
    return g_encoder_last_delta[channel];
}

void csr_encoder_zero(csr_channel_t channel)
{
    TIM_TypeDef *tim;

    tim = csr_encoder_timer(channel);
    if (tim == 0)
    {
        return;
    }

    tim->CNT = 0;
    g_encoder_total[channel] = 0;
    g_encoder_last_delta[channel] = 0;
}

void csr_encoder_debug_snapshot(csr_channel_t channel, uint8_t *phase_a, uint8_t *phase_b, uint16_t *timer_count)
{
    TIM_TypeDef *tim;

    if (phase_a != 0)
    {
        *phase_a = 0;
    }
    if (phase_b != 0)
    {
        *phase_b = 0;
    }
    if (timer_count != 0)
    {
        *timer_count = 0;
    }

    switch (channel)
    {
    case CSR_CHANNEL_CN1:
        if (phase_a != 0)
        {
            *phase_a = (uint8_t)GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_0);
        }
        if (phase_b != 0)
        {
            *phase_b = (uint8_t)GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_1);
        }
        break;
    case CSR_CHANNEL_CN2:
        if (phase_a != 0)
        {
            *phase_a = (uint8_t)GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_6);
        }
        if (phase_b != 0)
        {
            *phase_b = (uint8_t)GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_7);
        }
        break;
    case CSR_CHANNEL_CN3:
        if (phase_a != 0)
        {
            *phase_a = (uint8_t)GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_15);
        }
        if (phase_b != 0)
        {
            *phase_b = (uint8_t)GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_3);
        }
        break;
    case CSR_CHANNEL_CN4:
        if (phase_a != 0)
        {
            *phase_a = (uint8_t)GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_6);
        }
        if (phase_b != 0)
        {
            *phase_b = (uint8_t)GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_7);
        }
        break;
    default:
        break;
    }

    tim = csr_encoder_timer(channel);
    if ((tim != 0) && (timer_count != 0))
    {
        *timer_count = (uint16_t)tim->CNT;
    }
}
