#include "main.h"
#include "csr_soft_encoder.h"
#include "stm32f10x_exti.h"

static const int8_t CSR_ENCODER_TABLE[16] = {
    0,  1, -1,  0,
   -1,  0,  0,  1,
    1,  0,  0, -1,
    0, -1,  1,  0
};

static volatile int32_t g_soft_total[CSR_CHANNEL_COUNT] = {0};
static volatile int32_t g_soft_window_delta[CSR_CHANNEL_COUNT] = {0};
static volatile int32_t g_soft_last_delta[CSR_CHANNEL_COUNT] = {0};
static volatile uint8_t g_last_state_cn1 = 0;
static volatile uint8_t g_last_state_cn3 = 0;

static uint8_t csr_soft_encoder_read_cn1_state(void)
{
    uint8_t a = (uint8_t)GPIO_ReadInputDataBit(GPIOC, GPIO_Pin_4);
    uint8_t b = (uint8_t)GPIO_ReadInputDataBit(GPIOC, GPIO_Pin_5);
    return (uint8_t)((a << 1) | b);
}

static uint8_t csr_soft_encoder_read_cn3_state(void)
{
    uint8_t a = (uint8_t)GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_0);
    uint8_t b = (uint8_t)GPIO_ReadInputDataBit(GPIOC, GPIO_Pin_14);
    return (uint8_t)((a << 1) | b);
}

static void csr_soft_encoder_apply_delta(csr_channel_t channel, int8_t delta)
{
    if (delta == 0)
    {
        return;
    }
    g_soft_total[channel] += delta;
    g_soft_window_delta[channel] += delta;
    g_soft_last_delta[channel] = delta;
}

static void csr_soft_encoder_update_cn1(void)
{
    uint8_t current_state = csr_soft_encoder_read_cn1_state();
    uint8_t index = (uint8_t)((g_last_state_cn1 << 2) | current_state);
    csr_soft_encoder_apply_delta(CSR_CHANNEL_CN1, CSR_ENCODER_TABLE[index & 0x0F]);
    g_last_state_cn1 = current_state;
}

static void csr_soft_encoder_update_cn3(void)
{
    uint8_t current_state = csr_soft_encoder_read_cn3_state();
    uint8_t index = (uint8_t)((g_last_state_cn3 << 2) | current_state);
    csr_soft_encoder_apply_delta(CSR_CHANNEL_CN3, CSR_ENCODER_TABLE[index & 0x0F]);
    g_last_state_cn3 = current_state;
}

static void csr_soft_encoder_init_exti_line(uint32_t exti_line)
{
    EXTI_InitTypeDef exti_init;

    EXTI_ClearITPendingBit(exti_line);
    EXTI_StructInit(&exti_init);
    exti_init.EXTI_Line = exti_line;
    exti_init.EXTI_Mode = EXTI_Mode_Interrupt;
    exti_init.EXTI_Trigger = EXTI_Trigger_Rising_Falling;
    exti_init.EXTI_LineCmd = ENABLE;
    EXTI_Init(&exti_init);
}

static void csr_soft_encoder_init_irq(uint8_t irq_channel)
{
    NVIC_InitTypeDef nvic_init;

    nvic_init.NVIC_IRQChannel = irq_channel;
    nvic_init.NVIC_IRQChannelPreemptionPriority = 2;
    nvic_init.NVIC_IRQChannelSubPriority = 0;
    nvic_init.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&nvic_init);
}

void csr_soft_encoder_init(void)
{
    GPIO_InitTypeDef gpio_init;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO | RCC_APB2Periph_GPIOB | RCC_APB2Periph_GPIOC, ENABLE);

    gpio_init.GPIO_Mode = GPIO_Mode_IPU;
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;

    gpio_init.GPIO_Pin = GPIO_Pin_4 | GPIO_Pin_5 | GPIO_Pin_14;
    GPIO_Init(GPIOC, &gpio_init);

    gpio_init.GPIO_Pin = GPIO_Pin_0;
    GPIO_Init(GPIOB, &gpio_init);

    GPIO_EXTILineConfig(GPIO_PortSourceGPIOC, GPIO_PinSource4);
    GPIO_EXTILineConfig(GPIO_PortSourceGPIOC, GPIO_PinSource5);
    GPIO_EXTILineConfig(GPIO_PortSourceGPIOB, GPIO_PinSource0);
    GPIO_EXTILineConfig(GPIO_PortSourceGPIOC, GPIO_PinSource14);

    csr_soft_encoder_init_exti_line(EXTI_Line4);
    csr_soft_encoder_init_exti_line(EXTI_Line5);
    csr_soft_encoder_init_exti_line(EXTI_Line0);
    csr_soft_encoder_init_exti_line(EXTI_Line14);

    csr_soft_encoder_init_irq(EXTI4_IRQn);
    csr_soft_encoder_init_irq(EXTI9_5_IRQn);
    csr_soft_encoder_init_irq(EXTI0_IRQn);
    csr_soft_encoder_init_irq(EXTI15_10_IRQn);

    g_last_state_cn1 = csr_soft_encoder_read_cn1_state();
    g_last_state_cn3 = csr_soft_encoder_read_cn3_state();
    csr_soft_encoder_zero(CSR_CHANNEL_CN1);
    csr_soft_encoder_zero(CSR_CHANNEL_CN3);
}

int32_t csr_soft_encoder_read_and_reset(csr_channel_t channel)
{
    int32_t delta;

    if ((channel != CSR_CHANNEL_CN1) && (channel != CSR_CHANNEL_CN3))
    {
        return 0;
    }

    __disable_irq();
    delta = g_soft_window_delta[channel];
    g_soft_window_delta[channel] = 0;
    __enable_irq();

    return delta;
}

int32_t csr_soft_encoder_peek(csr_channel_t channel)
{
    if ((channel != CSR_CHANNEL_CN1) && (channel != CSR_CHANNEL_CN3))
    {
        return 0;
    }
    return g_soft_total[channel];
}

int32_t csr_soft_encoder_last_delta(csr_channel_t channel)
{
    if ((channel != CSR_CHANNEL_CN1) && (channel != CSR_CHANNEL_CN3))
    {
        return 0;
    }
    return g_soft_last_delta[channel];
}

void csr_soft_encoder_zero(csr_channel_t channel)
{
    if ((channel != CSR_CHANNEL_CN1) && (channel != CSR_CHANNEL_CN3))
    {
        return;
    }

    __disable_irq();
    g_soft_total[channel] = 0;
    g_soft_window_delta[channel] = 0;
    g_soft_last_delta[channel] = 0;
    if (channel == CSR_CHANNEL_CN1)
    {
        g_last_state_cn1 = csr_soft_encoder_read_cn1_state();
    }
    else
    {
        g_last_state_cn3 = csr_soft_encoder_read_cn3_state();
    }
    __enable_irq();
}

void csr_soft_encoder_debug_phase(csr_channel_t channel, uint8_t *phase_a, uint8_t *phase_b)
{
    if (phase_a != 0)
    {
        *phase_a = 0;
    }
    if (phase_b != 0)
    {
        *phase_b = 0;
    }

    if (channel == CSR_CHANNEL_CN1)
    {
        if (phase_a != 0)
        {
            *phase_a = (uint8_t)GPIO_ReadInputDataBit(GPIOC, GPIO_Pin_4);
        }
        if (phase_b != 0)
        {
            *phase_b = (uint8_t)GPIO_ReadInputDataBit(GPIOC, GPIO_Pin_5);
        }
    }
    else if (channel == CSR_CHANNEL_CN3)
    {
        if (phase_a != 0)
        {
            *phase_a = (uint8_t)GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_0);
        }
        if (phase_b != 0)
        {
            *phase_b = (uint8_t)GPIO_ReadInputDataBit(GPIOC, GPIO_Pin_14);
        }
    }
}

void EXTI0_IRQHandler(void)
{
    if (EXTI_GetITStatus(EXTI_Line0) != RESET)
    {
        csr_soft_encoder_update_cn3();
        EXTI_ClearITPendingBit(EXTI_Line0);
    }
}

void EXTI4_IRQHandler(void)
{
    if (EXTI_GetITStatus(EXTI_Line4) != RESET)
    {
        csr_soft_encoder_update_cn1();
        EXTI_ClearITPendingBit(EXTI_Line4);
    }
}

void EXTI9_5_IRQHandler(void)
{
    if (EXTI_GetITStatus(EXTI_Line5) != RESET)
    {
        csr_soft_encoder_update_cn1();
        EXTI_ClearITPendingBit(EXTI_Line5);
    }
}

void EXTI15_10_IRQHandler(void)
{
    if (EXTI_GetITStatus(EXTI_Line14) != RESET)
    {
        csr_soft_encoder_update_cn3();
        EXTI_ClearITPendingBit(EXTI_Line14);
    }
}
