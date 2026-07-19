#include "main.h"

#define ARM_BUS_RX_RING_SIZE             256U
#define ARM_BUS_TX_RING_SIZE             512U
#define ARM_BUS_RESPONSE_SIZE            64U
#define ARM_BUS_RESPONSE_TIMEOUT_MS      100U
#define ARM_BUS_LAST_RX_SIZE             16U

static volatile uint8_t g_rx_ring[ARM_BUS_RX_RING_SIZE];
static volatile uint16_t g_rx_head;
static volatile uint16_t g_rx_tail;
static volatile uint8_t g_tx_ring[ARM_BUS_TX_RING_SIZE];
static volatile uint16_t g_tx_head;
static volatile uint16_t g_tx_tail;
static volatile uint8_t g_tx_active;

static char g_response[ARM_BUS_RESPONSE_SIZE];
static uint16_t g_response_length;
static uint8_t g_response_active;
static uint8_t g_response_discard;
static uint32_t g_last_response_byte_ms;

static volatile uint32_t g_rx_overflow_count;
static volatile uint32_t g_tx_overflow_count;
static uint32_t g_bad_frame_count;
static volatile uint32_t g_rx_byte_count;
static volatile uint32_t g_tx_byte_count;
static volatile uint8_t g_last_rx[ARM_BUS_LAST_RX_SIZE];
static volatile uint8_t g_last_rx_head;
static volatile uint8_t g_last_rx_count;

static uint16_t arm_bus_ring_next(uint16_t value, uint16_t size)
{
    value++;
    if (value >= size)
    {
        value = 0U;
    }
    return value;
}

static uint16_t arm_bus_tx_free(void)
{
    uint16_t head;
    uint16_t tail;

    head = g_tx_head;
    tail = g_tx_tail;
    if (head >= tail)
    {
        return (uint16_t)(ARM_BUS_TX_RING_SIZE - (head - tail) - 1U);
    }
    return (uint16_t)(tail - head - 1U);
}

static int arm_bus_try_read_byte(uint8_t *value)
{
    uint16_t tail;

    if (g_rx_head == g_rx_tail)
    {
        return 0;
    }
    tail = g_rx_tail;
    *value = g_rx_ring[tail];
    g_rx_tail = arm_bus_ring_next(tail, ARM_BUS_RX_RING_SIZE);
    return 1;
}

static void arm_bus_reset_response(void)
{
    g_response_length = 0U;
    g_response_active = 0U;
    g_response_discard = 0U;
}

void arm_servo_bus_init(uint32_t baudrate)
{
    GPIO_InitTypeDef gpio_init;
    USART_InitTypeDef usart_init;
    NVIC_InitTypeDef nvic_init;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_UART5, ENABLE);

    gpio_init.GPIO_Pin = GPIO_Pin_12;
    gpio_init.GPIO_Mode = GPIO_Mode_AF_OD;
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOC, &gpio_init);

    USART_StructInit(&usart_init);
    usart_init.USART_BaudRate = baudrate;
    usart_init.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    USART_Init(UART5, &usart_init);
    USART_HalfDuplexCmd(UART5, ENABLE);
    USART_ITConfig(UART5, USART_IT_RXNE, ENABLE);
    USART_ITConfig(UART5, USART_IT_TXE, DISABLE);
    USART_ITConfig(UART5, USART_IT_TC, DISABLE);
    USART_Cmd(UART5, ENABLE);

    nvic_init.NVIC_IRQChannel = UART5_IRQn;
    nvic_init.NVIC_IRQChannelPreemptionPriority = 2U;
    nvic_init.NVIC_IRQChannelSubPriority = 0U;
    nvic_init.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&nvic_init);

    g_rx_head = 0U;
    g_rx_tail = 0U;
    g_tx_head = 0U;
    g_tx_tail = 0U;
    g_tx_active = 0U;
    g_rx_overflow_count = 0UL;
    g_tx_overflow_count = 0UL;
    g_bad_frame_count = 0UL;
    g_rx_byte_count = 0UL;
    g_tx_byte_count = 0UL;
    g_last_rx_head = 0U;
    g_last_rx_count = 0U;
    arm_bus_reset_response();
}

int arm_servo_bus_send_frame(const char *frame)
{
    uint16_t length;
    uint16_t index;
    uint16_t head;

    length = (uint16_t)strlen(frame);
    if ((length == 0U) || (length > arm_bus_tx_free()))
    {
        g_tx_overflow_count++;
        return 0;
    }

    head = g_tx_head;
    for (index = 0U; index < length; index++)
    {
        g_tx_ring[head] = (uint8_t)frame[index];
        head = arm_bus_ring_next(head, ARM_BUS_TX_RING_SIZE);
    }

    __disable_irq();
    g_tx_head = head;
    if (g_tx_active == 0U)
    {
        g_tx_active = 1U;
        USART_ITConfig(UART5, USART_IT_RXNE, DISABLE);
        USART_ClearITPendingBit(UART5, USART_IT_TC);
    }
    USART_ITConfig(UART5, USART_IT_TXE, ENABLE);
    __enable_irq();
    return 1;
}

int arm_servo_bus_poll_response(char *frame, uint16_t frame_size, uint16_t *length, uint32_t now_ms)
{
    uint8_t value;

    if ((g_response_active != 0U) &&
        ((uint32_t)(now_ms - g_last_response_byte_ms) > ARM_BUS_RESPONSE_TIMEOUT_MS))
    {
        g_bad_frame_count++;
        arm_bus_reset_response();
        return -1;
    }

    while (arm_bus_try_read_byte(&value) != 0)
    {
        if (g_response_active == 0U)
        {
            if (value == '#')
            {
                g_response[0] = '#';
                g_response_length = 1U;
                g_response_active = 1U;
                g_last_response_byte_ms = now_ms;
            }
            continue;
        }

        g_last_response_byte_ms = now_ms;
        /*
         * 当前 PC12 半双工链路实测会在舵机正式回包前出现一个额外 '#'
         * （原始字节为 "##000P1500!"）。第二个 '#' 是明确的新帧头，
         * 从这里重新同步，后续内容仍按严格的 #...! 边界处理。
         */
        if (value == '#')
        {
            g_response[0] = '#';
            g_response_length = 1U;
            g_response_discard = 0U;
            continue;
        }
        if (g_response_discard != 0U)
        {
            if (value == '!')
            {
                g_bad_frame_count++;
                arm_bus_reset_response();
                return -1;
            }
            continue;
        }
        if (g_response_length >= (ARM_BUS_RESPONSE_SIZE - 1U))
        {
            g_response_discard = 1U;
            continue;
        }
        g_response[g_response_length++] = (char)value;
        if (value == '!')
        {
            if (g_response_length >= frame_size)
            {
                g_bad_frame_count++;
                arm_bus_reset_response();
                return -1;
            }
            memcpy(frame, g_response, g_response_length);
            frame[g_response_length] = '\0';
            *length = g_response_length;
            arm_bus_reset_response();
            return 1;
        }
    }
    return 0;
}

uint8_t arm_servo_bus_is_tx_idle(void)
{
    return (g_tx_active == 0U) ? 1U : 0U;
}

uint32_t arm_servo_bus_rx_overflow_count(void)
{
    return g_rx_overflow_count;
}

uint32_t arm_servo_bus_tx_overflow_count(void)
{
    return g_tx_overflow_count;
}

uint32_t arm_servo_bus_bad_frame_count(void)
{
    return g_bad_frame_count;
}

uint32_t arm_servo_bus_rx_byte_count(void)
{
    return g_rx_byte_count;
}

uint32_t arm_servo_bus_tx_byte_count(void)
{
    return g_tx_byte_count;
}

uint8_t arm_servo_bus_copy_last_rx(uint8_t *output, uint8_t output_size)
{
    uint8_t count;
    uint8_t start;
    uint8_t index;

    __disable_irq();
    count = g_last_rx_count;
    if (count > output_size)
    {
        count = output_size;
    }
    start = (uint8_t)((g_last_rx_head + ARM_BUS_LAST_RX_SIZE - count) % ARM_BUS_LAST_RX_SIZE);
    for (index = 0U; index < count; index++)
    {
        output[index] = g_last_rx[(uint8_t)((start + index) % ARM_BUS_LAST_RX_SIZE)];
    }
    __enable_irq();
    return count;
}

void UART5_IRQHandler(void)
{
    uint16_t next_head;

    if (USART_GetITStatus(UART5, USART_IT_RXNE) != RESET)
    {
        uint8_t value;

        value = (uint8_t)(USART_ReceiveData(UART5) & 0xFFU);
        g_rx_byte_count++;
        g_last_rx[g_last_rx_head] = value;
        g_last_rx_head = (uint8_t)((g_last_rx_head + 1U) % ARM_BUS_LAST_RX_SIZE);
        if (g_last_rx_count < ARM_BUS_LAST_RX_SIZE)
        {
            g_last_rx_count++;
        }
        next_head = arm_bus_ring_next(g_rx_head, ARM_BUS_RX_RING_SIZE);
        if (next_head != g_rx_tail)
        {
            g_rx_ring[g_rx_head] = value;
            g_rx_head = next_head;
        }
        else
        {
            g_rx_overflow_count++;
        }
    }

    if (USART_GetITStatus(UART5, USART_IT_TXE) != RESET)
    {
        if (g_tx_tail != g_tx_head)
        {
            USART_SendData(UART5, g_tx_ring[g_tx_tail]);
            g_tx_byte_count++;
            g_tx_tail = arm_bus_ring_next(g_tx_tail, ARM_BUS_TX_RING_SIZE);
        }
        else
        {
            USART_ITConfig(UART5, USART_IT_TXE, DISABLE);
            USART_ITConfig(UART5, USART_IT_TC, ENABLE);
        }
    }

    if (USART_GetITStatus(UART5, USART_IT_TC) != RESET)
    {
        USART_ClearITPendingBit(UART5, USART_IT_TC);
        USART_ITConfig(UART5, USART_IT_TC, DISABLE);
        USART_ITConfig(UART5, USART_IT_RXNE, ENABLE);
        g_tx_active = 0U;
    }
}
