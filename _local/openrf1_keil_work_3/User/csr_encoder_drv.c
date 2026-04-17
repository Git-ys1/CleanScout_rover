#include "main.h"
#include "stm32f10x_exti.h"

#define CSR_ENCODER_TIM_PERIOD ((uint16_t)65535)

static int32_t g_encoder_total[CSR_CHANNEL_COUNT] = {0};
static int32_t g_encoder_last_delta[CSR_CHANNEL_COUNT] = {0};
static volatile int32_t g_exti_count_a[CSR_CHANNEL_COUNT] = {0};
static volatile int32_t g_exti_count_b[CSR_CHANNEL_COUNT] = {0};
static uint32_t g_afio_mapr_effective = 0;

void csr_encoder_apply_debug_remap(void)
{
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO, ENABLE);

    /*
     * STM32F1 MAPR.SWJ_CFG is unsafe to preserve with read-modify-write:
     * readback can report a different SWJ_CFG than the last value written.
     * Keep an explicit shadow for the bits we own and always rewrite TIM2
     * full remap + "JTAG disabled, SWD enabled" together.
     */
    g_afio_mapr_effective = AFIO->MAPR;
    g_afio_mapr_effective &= ~(AFIO_MAPR_SWJ_CFG | AFIO_MAPR_TIM2_REMAP);
    g_afio_mapr_effective |= AFIO_MAPR_SWJ_CFG_JTAGDISABLE;
    g_afio_mapr_effective |= AFIO_MAPR_TIM2_REMAP_FULLREMAP;
    AFIO->MAPR = g_afio_mapr_effective;
}

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

static uint8_t csr_gpio_pin_cfg(GPIO_TypeDef *gpio, uint8_t pin)
{
    uint32_t reg_value;
    uint8_t shift;

    if (pin < 8U)
    {
        reg_value = gpio->CRL;
        shift = (uint8_t)(pin * 4U);
    }
    else
    {
        reg_value = gpio->CRH;
        shift = (uint8_t)((pin - 8U) * 4U);
    }

    return (uint8_t)((reg_value >> shift) & 0x0FU);
}

static GPIOMode_TypeDef csr_encoder_gpio_mode(csr_encoder_input_mode_t input_mode)
{
    switch (input_mode)
    {
    case CSR_ENCODER_INPUT_IPU:
        return GPIO_Mode_IPU;
    case CSR_ENCODER_INPUT_IPD:
        return GPIO_Mode_IPD;
    case CSR_ENCODER_INPUT_FLOATING:
    default:
        return GPIO_Mode_IN_FLOATING;
    }
}

static uint16_t csr_encoder_tim_mode(csr_encoder_count_mode_t count_mode)
{
    switch (count_mode)
    {
    case CSR_ENCODER_COUNT_TI1:
        return TIM_EncoderMode_TI1;
    case CSR_ENCODER_COUNT_TI2:
        return TIM_EncoderMode_TI2;
    case CSR_ENCODER_COUNT_TI12:
    default:
        return TIM_EncoderMode_TI12;
    }
}

static void csr_encoder_init_common(TIM_TypeDef *tim, csr_encoder_count_mode_t count_mode, uint8_t ic_filter)
{
    TIM_TimeBaseInitTypeDef tim_base_init;
    TIM_ICInitTypeDef tim_ic_init;

    TIM_DeInit(tim);

    TIM_TimeBaseStructInit(&tim_base_init);
    tim_base_init.TIM_Prescaler = 0;
    tim_base_init.TIM_Period = CSR_ENCODER_TIM_PERIOD;
    tim_base_init.TIM_ClockDivision = TIM_CKD_DIV1;
    tim_base_init.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(tim, &tim_base_init);

    TIM_EncoderInterfaceConfig(tim, csr_encoder_tim_mode(count_mode), TIM_ICPolarity_Rising, TIM_ICPolarity_Rising);

    TIM_ICStructInit(&tim_ic_init);
    tim_ic_init.TIM_ICFilter = ic_filter;
    TIM_ICInit(tim, &tim_ic_init);

    TIM_SetCounter(tim, 0);
    TIM_Cmd(tim, ENABLE);
}

static void csr_encoder_init_cn1_with(csr_encoder_input_mode_t input_mode, csr_encoder_count_mode_t count_mode, uint8_t ic_filter)
{
    GPIO_InitTypeDef gpio_init;

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM5, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

    gpio_init.GPIO_Pin = GPIO_Pin_0 | GPIO_Pin_1;
    gpio_init.GPIO_Mode = csr_encoder_gpio_mode(input_mode);
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &gpio_init);

    csr_encoder_init_common(TIM5, count_mode, ic_filter);
}

static void csr_encoder_init_cn1(void)
{
    csr_encoder_init_cn1_with(CSR_ENCODER_INPUT_FLOATING, CSR_ENCODER_COUNT_TI12, CSR_ENCODER_FILTER_CN1);
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

    csr_encoder_init_common(TIM3, CSR_ENCODER_COUNT_TI12, CSR_ENCODER_FILTER_CN2);
}

static void csr_encoder_init_cn3_with(csr_encoder_input_mode_t input_mode, csr_encoder_count_mode_t count_mode, uint8_t ic_filter)
{
    GPIO_InitTypeDef gpio_init;

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOB | RCC_APB2Periph_AFIO, ENABLE);

    csr_encoder_apply_debug_remap();

    gpio_init.GPIO_Pin = GPIO_Pin_15;
    gpio_init.GPIO_Mode = csr_encoder_gpio_mode(input_mode);
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &gpio_init);

    gpio_init.GPIO_Pin = GPIO_Pin_3;
    GPIO_Init(GPIOB, &gpio_init);

    csr_encoder_init_common(TIM2, count_mode, ic_filter);
}

static void csr_encoder_init_cn3(void)
{
    csr_encoder_init_cn3_with(CSR_ENCODER_INPUT_FLOATING, CSR_ENCODER_COUNT_TI12, CSR_ENCODER_FILTER_CN3);
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

    csr_encoder_init_common(TIM4, CSR_ENCODER_COUNT_TI12, CSR_ENCODER_FILTER_CN4);
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

int csr_encoder_reconfigure(csr_channel_t channel, csr_encoder_input_mode_t input_mode, csr_encoder_count_mode_t count_mode, uint8_t ic_filter)
{
    if ((input_mode > CSR_ENCODER_INPUT_IPD) || (count_mode > CSR_ENCODER_COUNT_TI2))
    {
        return 0;
    }

    if (channel == CSR_CHANNEL_CN1)
    {
        csr_encoder_init_cn1_with(input_mode, count_mode, ic_filter);
        csr_encoder_zero(channel);
        return 1;
    }

    if (channel == CSR_CHANNEL_CN3)
    {
        csr_encoder_init_cn3_with(input_mode, count_mode, ic_filter);
        csr_encoder_zero(channel);
        return 1;
    }

    return 0;
}

static void csr_encoder_init_exti_line(uint32_t exti_line)
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

static void csr_encoder_init_exti_irq(uint8_t irq_channel)
{
    NVIC_InitTypeDef nvic_init;

    nvic_init.NVIC_IRQChannel = irq_channel;
    nvic_init.NVIC_IRQChannelPreemptionPriority = 2;
    nvic_init.NVIC_IRQChannelSubPriority = 0;
    nvic_init.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&nvic_init);
}

int csr_encoder_exti_probe_start(csr_channel_t channel, csr_encoder_input_mode_t input_mode)
{
    GPIO_InitTypeDef gpio_init;

    if (input_mode > CSR_ENCODER_INPUT_IPD)
    {
        return 0;
    }

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO | RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOB, ENABLE);

    gpio_init.GPIO_Mode = csr_encoder_gpio_mode(input_mode);
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;

    if (channel == CSR_CHANNEL_CN1)
    {
        gpio_init.GPIO_Pin = GPIO_Pin_0 | GPIO_Pin_1;
        GPIO_Init(GPIOA, &gpio_init);

        GPIO_EXTILineConfig(GPIO_PortSourceGPIOA, GPIO_PinSource0);
        GPIO_EXTILineConfig(GPIO_PortSourceGPIOA, GPIO_PinSource1);
        csr_encoder_init_exti_line(EXTI_Line0);
        csr_encoder_init_exti_line(EXTI_Line1);
        csr_encoder_init_exti_irq(EXTI0_IRQn);
        csr_encoder_init_exti_irq(EXTI1_IRQn);
    }
    else if (channel == CSR_CHANNEL_CN3)
    {
        csr_encoder_apply_debug_remap();

        gpio_init.GPIO_Pin = GPIO_Pin_15;
        GPIO_Init(GPIOA, &gpio_init);
        gpio_init.GPIO_Pin = GPIO_Pin_3;
        GPIO_Init(GPIOB, &gpio_init);

        GPIO_EXTILineConfig(GPIO_PortSourceGPIOA, GPIO_PinSource15);
        GPIO_EXTILineConfig(GPIO_PortSourceGPIOB, GPIO_PinSource3);
        csr_encoder_init_exti_line(EXTI_Line15);
        csr_encoder_init_exti_line(EXTI_Line3);
        csr_encoder_init_exti_irq(EXTI15_10_IRQn);
        csr_encoder_init_exti_irq(EXTI3_IRQn);
    }
    else
    {
        return 0;
    }

    g_exti_count_a[channel] = 0;
    g_exti_count_b[channel] = 0;
    return 1;
}

void csr_encoder_exti_snapshot(csr_channel_t channel, int32_t *count_a, int32_t *count_b, uint8_t *phase_a, uint8_t *phase_b, uint32_t *pending)
{
    uint32_t pending_value = EXTI->PR;

    if (count_a != 0)
    {
        *count_a = 0;
    }
    if (count_b != 0)
    {
        *count_b = 0;
    }
    if (pending != 0)
    {
        *pending = pending_value;
    }

    if (channel >= CSR_CHANNEL_COUNT)
    {
        return;
    }

    if (count_a != 0)
    {
        *count_a = g_exti_count_a[channel];
    }
    if (count_b != 0)
    {
        *count_b = g_exti_count_b[channel];
    }

    csr_encoder_debug_snapshot(channel, phase_a, phase_b, 0);
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

void csr_encoder_reg_snapshot(uint8_t target, csr_encoder_reg_snapshot_t *snapshot)
{
    TIM_TypeDef *tim = 0;

    if (snapshot == 0)
    {
        return;
    }

    snapshot->mapr_raw = AFIO->MAPR;
    snapshot->mapr_effective = g_afio_mapr_effective;
    snapshot->smcr = 0;
    snapshot->ccmr1 = 0;
    snapshot->ccer = 0;
    snapshot->cnt = 0;
    snapshot->pin_a_cfg = 0;
    snapshot->pin_b_cfg = 0;
    snapshot->pin_a_level = 0;
    snapshot->pin_b_level = 0;
    snapshot->gpioa_crl = GPIOA->CRL;
    snapshot->gpioa_crh = GPIOA->CRH;
    snapshot->gpioa_idr = GPIOA->IDR;
    snapshot->gpiob_crl = GPIOB->CRL;
    snapshot->gpiob_crh = GPIOB->CRH;
    snapshot->gpiob_idr = GPIOB->IDR;

    if ((target >= 1U) && (target <= CSR_CHANNEL_COUNT))
    {
        csr_channel_t channel = (csr_channel_t)(target - 1U);
        tim = csr_encoder_timer(channel);

        switch (channel)
        {
        case CSR_CHANNEL_CN1:
            snapshot->pin_a_cfg = csr_gpio_pin_cfg(GPIOA, 0U);
            snapshot->pin_b_cfg = csr_gpio_pin_cfg(GPIOA, 1U);
            snapshot->pin_a_level = (uint8_t)GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_0);
            snapshot->pin_b_level = (uint8_t)GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_1);
            break;
        case CSR_CHANNEL_CN2:
            snapshot->pin_a_cfg = csr_gpio_pin_cfg(GPIOA, 6U);
            snapshot->pin_b_cfg = csr_gpio_pin_cfg(GPIOA, 7U);
            snapshot->pin_a_level = (uint8_t)GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_6);
            snapshot->pin_b_level = (uint8_t)GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_7);
            break;
        case CSR_CHANNEL_CN3:
            snapshot->pin_a_cfg = csr_gpio_pin_cfg(GPIOA, 15U);
            snapshot->pin_b_cfg = csr_gpio_pin_cfg(GPIOB, 3U);
            snapshot->pin_a_level = (uint8_t)GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_15);
            snapshot->pin_b_level = (uint8_t)GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_3);
            break;
        case CSR_CHANNEL_CN4:
            snapshot->pin_a_cfg = csr_gpio_pin_cfg(GPIOB, 6U);
            snapshot->pin_b_cfg = csr_gpio_pin_cfg(GPIOB, 7U);
            snapshot->pin_a_level = (uint8_t)GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_6);
            snapshot->pin_b_level = (uint8_t)GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_7);
            break;
        default:
            break;
        }
    }

    if (tim != 0)
    {
        snapshot->smcr = (uint16_t)tim->SMCR;
        snapshot->ccmr1 = (uint16_t)tim->CCMR1;
        snapshot->ccer = (uint16_t)tim->CCER;
        snapshot->cnt = (uint16_t)tim->CNT;
    }
}

void EXTI0_IRQHandler(void)
{
    if (EXTI_GetITStatus(EXTI_Line0) != RESET)
    {
        g_exti_count_a[CSR_CHANNEL_CN1]++;
        EXTI_ClearITPendingBit(EXTI_Line0);
    }
}

void EXTI1_IRQHandler(void)
{
    if (EXTI_GetITStatus(EXTI_Line1) != RESET)
    {
        g_exti_count_b[CSR_CHANNEL_CN1]++;
        EXTI_ClearITPendingBit(EXTI_Line1);
    }
}

void EXTI3_IRQHandler(void)
{
    if (EXTI_GetITStatus(EXTI_Line3) != RESET)
    {
        g_exti_count_b[CSR_CHANNEL_CN3]++;
        EXTI_ClearITPendingBit(EXTI_Line3);
    }
}

void EXTI15_10_IRQHandler(void)
{
    if (EXTI_GetITStatus(EXTI_Line15) != RESET)
    {
        g_exti_count_a[CSR_CHANNEL_CN3]++;
        EXTI_ClearITPendingBit(EXTI_Line15);
    }
}
