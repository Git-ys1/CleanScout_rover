#include "main.h"

#define ARM_HOST_RX_RING_SIZE            512U
#define ARM_HOST_TX_RING_SIZE            512U

typedef enum
{
    ARM_RX_IDLE = 0,
    ARM_RX_FRAME,
    ARM_RX_DISCARD,
    ARM_RX_BAD_LINE,
    ARM_RX_OVERFLOW_DISCARD
} arm_rx_state_t;

static volatile uint8_t g_rx_ring[ARM_HOST_RX_RING_SIZE];
static volatile uint16_t g_rx_head;
static volatile uint16_t g_rx_tail;
static volatile uint8_t g_tx_ring[ARM_HOST_TX_RING_SIZE];
static volatile uint16_t g_tx_head;
static volatile uint16_t g_tx_tail;

static char g_frame[ARM_PROTOCOL_MAX_FRAME_SIZE];
static uint16_t g_frame_length;
static char g_frame_terminator;
static arm_rx_state_t g_rx_state;
static uint32_t g_last_byte_ms;

static volatile uint32_t g_rx_overflow_count;
static volatile uint32_t g_tx_overflow_count;
static volatile uint8_t g_rx_overflow_event;
static uint32_t g_bad_frame_count;
static volatile uint32_t g_rx_byte_count;
static volatile uint32_t g_tx_byte_count;

static uint16_t arm_ring_next(uint16_t value, uint16_t size)
{
    value++;
    if (value >= size)
    {
        value = 0U;
    }
    return value;
}

static int arm_host_try_read_byte(uint8_t *value)
{
    uint16_t tail;

    if (g_rx_head == g_rx_tail)
    {
        return 0;
    }
    tail = g_rx_tail;
    *value = g_rx_ring[tail];
    g_rx_tail = arm_ring_next(tail, ARM_HOST_RX_RING_SIZE);
    return 1;
}

static uint16_t arm_host_tx_free(void)
{
    uint16_t head;
    uint16_t tail;

    head = g_tx_head;
    tail = g_tx_tail;
    if (head >= tail)
    {
        return (uint16_t)(ARM_HOST_TX_RING_SIZE - (head - tail) - 1U);
    }
    return (uint16_t)(tail - head - 1U);
}

static void arm_host_reset_frame(void)
{
    g_frame_length = 0U;
    g_frame_terminator = '\0';
    g_rx_state = ARM_RX_IDLE;
}

static void arm_host_start_frame(char value, uint32_t now_ms)
{
    g_frame[0] = value;
    g_frame_length = 1U;
    g_last_byte_ms = now_ms;
    g_rx_state = ARM_RX_FRAME;
    g_frame_terminator = (value == '{') ? '}' : '!';
}

void arm_host_link_init(uint32_t baudrate)
{
    GPIO_InitTypeDef gpio_init;
    USART_InitTypeDef usart_init;
    NVIC_InitTypeDef nvic_init;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART3, ENABLE);

    gpio_init.GPIO_Pin = GPIO_Pin_10;
    gpio_init.GPIO_Mode = GPIO_Mode_AF_PP;
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOB, &gpio_init);
    gpio_init.GPIO_Pin = GPIO_Pin_11;
    gpio_init.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(GPIOB, &gpio_init);

    USART_StructInit(&usart_init);
    usart_init.USART_BaudRate = baudrate;
    usart_init.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    USART_Init(USART3, &usart_init);
    USART_ITConfig(USART3, USART_IT_RXNE, ENABLE);
    USART_ITConfig(USART3, USART_IT_TXE, DISABLE);
    USART_Cmd(USART3, ENABLE);

    nvic_init.NVIC_IRQChannel = USART3_IRQn;
    nvic_init.NVIC_IRQChannelPreemptionPriority = 1U;
    nvic_init.NVIC_IRQChannelSubPriority = 0U;
    nvic_init.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&nvic_init);

    g_rx_head = 0U;
    g_rx_tail = 0U;
    g_tx_head = 0U;
    g_tx_tail = 0U;
    g_rx_overflow_count = 0UL;
    g_tx_overflow_count = 0UL;
    g_rx_overflow_event = 0U;
    g_bad_frame_count = 0UL;
    g_rx_byte_count = 0UL;
    g_tx_byte_count = 0UL;
    arm_host_reset_frame();
}

int arm_host_link_send_text(const char *text)
{
    uint16_t length;
    uint16_t index;
    uint16_t head;

    length = (uint16_t)strlen(text);
    if (length > arm_host_tx_free())
    {
        g_tx_overflow_count++;
        return 0;
    }
    head = g_tx_head;
    for (index = 0U; index < length; index++)
    {
        g_tx_ring[head] = (uint8_t)text[index];
        head = arm_ring_next(head, ARM_HOST_TX_RING_SIZE);
    }
    __disable_irq();
    g_tx_head = head;
    USART_ITConfig(USART3, USART_IT_TXE, ENABLE);
    __enable_irq();
    return 1;
}

int arm_host_link_poll(char *frame, uint16_t frame_size, uint16_t *length, uint32_t now_ms)
{
    uint8_t value;

    if (g_rx_overflow_event != 0U)
    {
        __disable_irq();
        g_rx_tail = g_rx_head;
        g_rx_overflow_event = 0U;
        __enable_irq();
        g_frame_length = 0U;
        g_frame_terminator = '\0';
        g_rx_state = ARM_RX_OVERFLOW_DISCARD;
        g_bad_frame_count++;
        return -1;
    }

    if ((g_rx_state == ARM_RX_FRAME) &&
        ((uint32_t)(now_ms - g_last_byte_ms) > CSR_ARM_FRAME_TIMEOUT_MS))
    {
        g_bad_frame_count++;
        arm_host_reset_frame();
        return -1;
    }

    while (arm_host_try_read_byte(&value) != 0)
    {
        if (g_rx_state == ARM_RX_IDLE)
        {
            if ((value == '#') || (value == '{') || (value == '$') || (value == '@'))
            {
                arm_host_start_frame((char)value, now_ms);
            }
            else if ((value != '\r') && (value != '\n') && (value != ' ') && (value != '\t'))
            {
                g_rx_state = ARM_RX_BAD_LINE;
            }
            continue;
        }

        if (g_rx_state == ARM_RX_BAD_LINE)
        {
            if (value == '\n')
            {
                g_bad_frame_count++;
                arm_host_reset_frame();
                return -1;
            }
            continue;
        }

        if (g_rx_state == ARM_RX_OVERFLOW_DISCARD)
        {
            if ((value == '!') || (value == '}') || (value == '\n'))
            {
                arm_host_reset_frame();
            }
            continue;
        }

        if (g_rx_state == ARM_RX_DISCARD)
        {
            if ((value == (uint8_t)g_frame_terminator) || (value == '\n'))
            {
                g_bad_frame_count++;
                arm_host_reset_frame();
                return -1;
            }
            continue;
        }

        g_last_byte_ms = now_ms;
        if ((g_frame[0] == '{') && (value == '{'))
        {
            g_rx_state = ARM_RX_DISCARD;
            continue;
        }
        if (g_frame_length >= (ARM_PROTOCOL_MAX_FRAME_SIZE - 1U))
        {
            g_rx_state = ARM_RX_DISCARD;
            continue;
        }
        g_frame[g_frame_length++] = (char)value;
        if (value == (uint8_t)g_frame_terminator)
        {
            if (g_frame_length >= frame_size)
            {
                g_bad_frame_count++;
                arm_host_reset_frame();
                return -1;
            }
            memcpy(frame, g_frame, g_frame_length);
            frame[g_frame_length] = '\0';
            *length = g_frame_length;
            arm_host_reset_frame();
            return 1;
        }
    }
    return 0;
}

void arm_host_link_send_ready_v2(void)
{
    arm_host_link_send_text("@READY:ARM_V2!");
}

void arm_host_link_send_info_v2(void)
{
    arm_host_link_send_text("@INFO:COMBINED:" CSR_COMBINED_FW_VERSION ":ARM_V2!");
}

void arm_host_link_send_ack(void)
{
    arm_host_link_send_text("@ACK:OK!");
}

void arm_host_link_send_error(const char *reason)
{
    char frame[48];
    sprintf(frame, "@ERR:%s!", reason);
    arm_host_link_send_text(frame);
}

uint32_t arm_host_link_rx_overflow_count(void)
{
    return g_rx_overflow_count;
}

uint32_t arm_host_link_tx_overflow_count(void)
{
    return g_tx_overflow_count;
}

uint32_t arm_host_link_bad_frame_count(void)
{
    return g_bad_frame_count;
}

uint32_t arm_host_link_rx_byte_count(void)
{
    return g_rx_byte_count;
}

uint32_t arm_host_link_tx_byte_count(void)
{
    return g_tx_byte_count;
}

void USART3_IRQHandler(void)
{
    uint16_t next_head;

    if (USART_GetITStatus(USART3, USART_IT_RXNE) != RESET)
    {
        uint8_t value;

        value = (uint8_t)(USART_ReceiveData(USART3) & 0xFFU);
        g_rx_byte_count++;
        next_head = arm_ring_next(g_rx_head, ARM_HOST_RX_RING_SIZE);
        if (next_head != g_rx_tail)
        {
            g_rx_ring[g_rx_head] = value;
            g_rx_head = next_head;
        }
        else
        {
            g_rx_overflow_count++;
            g_rx_overflow_event = 1U;
        }
    }

    if (USART_GetITStatus(USART3, USART_IT_TXE) != RESET)
    {
        if (g_tx_tail != g_tx_head)
        {
            USART_SendData(USART3, g_tx_ring[g_tx_tail]);
            g_tx_byte_count++;
            g_tx_tail = arm_ring_next(g_tx_tail, ARM_HOST_TX_RING_SIZE);
        }
        else
        {
            USART_ITConfig(USART3, USART_IT_TXE, DISABLE);
        }
    }
}
