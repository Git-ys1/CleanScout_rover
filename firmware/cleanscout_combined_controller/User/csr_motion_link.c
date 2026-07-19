#include "main.h"

#define CSR_MOTION_LINE_SIZE             64U
#define CSR_MOTION_RX_RING_SIZE          256U
#define CSR_MOTION_TX_RING_SIZE          1024U

static char g_line[CSR_MOTION_LINE_SIZE];
static uint8_t g_line_length;
static uint8_t g_discard_line;

static volatile uint8_t g_rx_ring[CSR_MOTION_RX_RING_SIZE];
static volatile uint16_t g_rx_head;
static volatile uint16_t g_rx_tail;
static volatile uint8_t g_tx_ring[CSR_MOTION_TX_RING_SIZE];
static volatile uint16_t g_tx_head;
static volatile uint16_t g_tx_tail;

static volatile uint32_t g_rx_overflow_count;
static volatile uint32_t g_tx_overflow_count;
static volatile uint8_t g_rx_overflow_event;
static uint32_t g_bad_frame_count;

static uint16_t csr_ring_next(uint16_t value, uint16_t size)
{
    value++;
    if (value >= size)
    {
        value = 0U;
    }
    return value;
}

static int csr_motion_try_read_byte(uint8_t *value)
{
    uint16_t tail;

    if (g_rx_head == g_rx_tail)
    {
        return 0;
    }
    tail = g_rx_tail;
    *value = g_rx_ring[tail];
    g_rx_tail = csr_ring_next(tail, CSR_MOTION_RX_RING_SIZE);
    return 1;
}

static uint16_t csr_motion_tx_free(void)
{
    uint16_t head;
    uint16_t tail;

    head = g_tx_head;
    tail = g_tx_tail;
    if (head >= tail)
    {
        return (uint16_t)(CSR_MOTION_TX_RING_SIZE - (head - tail) - 1U);
    }
    return (uint16_t)(tail - head - 1U);
}

static int csr_motion_send_text(const char *text)
{
    uint16_t length;
    uint16_t head;
    uint16_t index;

    length = (uint16_t)strlen(text);
    if (length > csr_motion_tx_free())
    {
        g_tx_overflow_count++;
        return 0;
    }

    head = g_tx_head;
    for (index = 0U; index < length; index++)
    {
        g_tx_ring[head] = (uint8_t)text[index];
        head = csr_ring_next(head, CSR_MOTION_TX_RING_SIZE);
    }

    __disable_irq();
    g_tx_head = head;
    USART_ITConfig(USART2, USART_IT_TXE, ENABLE);
    __enable_irq();
    return 1;
}

static void csr_motion_trim(char *line)
{
    size_t length;

    length = strlen(line);
    while (length > 0U)
    {
        if ((line[length - 1U] == '\r') || (line[length - 1U] == '\n') ||
            (line[length - 1U] == ' ') || (line[length - 1U] == '\t'))
        {
            line[length - 1U] = '\0';
            length--;
        }
        else
        {
            break;
        }
    }
}

static int csr_motion_parse_channel(const char *token, csr_channel_t *channel)
{
    long value;
    char *endptr;

    endptr = 0;
    value = strtol(token, &endptr, 10);
    if ((endptr == token) || (*endptr != '\0') || (value < 1L) || (value > 4L))
    {
        return 0;
    }
    *channel = (csr_channel_t)(value - 1L);
    return 1;
}

static int csr_motion_parse_float(const char *token, float *value)
{
    double parsed;
    char *endptr;

    endptr = 0;
    parsed = strtod(token, &endptr);
    if ((endptr == token) || (*endptr != '\0'))
    {
        return 0;
    }
    *value = (float)parsed;
    return 1;
}

static int csr_motion_parse_no_arg(char *token, const char *name, csr_cmd_type_t type, csr_motion_command_t *command)
{
    if (strcmp(token, name) != 0)
    {
        return 0;
    }
    if (strtok(0, ",") != 0)
    {
        csr_motion_link_send_error("arg_count");
        g_bad_frame_count++;
        return -1;
    }
    command->type = type;
    return 1;
}

static int csr_motion_parse_line(char *line, csr_motion_command_t *command)
{
    char buffer[CSR_MOTION_LINE_SIZE];
    char *token;
    char *endptr;
    long pwm_value;
    uint8_t index;
    int result;

    memset(command, 0, sizeof(*command));
    csr_motion_trim(line);
    if (line[0] == '\0')
    {
        return 0;
    }

    strncpy(buffer, line, sizeof(buffer) - 1U);
    buffer[sizeof(buffer) - 1U] = '\0';
    token = strtok(buffer, ",");
    if (token == 0)
    {
        csr_motion_link_send_error("bad_prefix");
        g_bad_frame_count++;
        return 0;
    }

    result = csr_motion_parse_no_arg(token, "STOP", CSR_CMD_STOP, command);
    if (result != 0)
    {
        return (result > 0) ? 1 : 0;
    }
    result = csr_motion_parse_no_arg(token, "ESTOP", CSR_CMD_ESTOP, command);
    if (result != 0)
    {
        return (result > 0) ? 1 : 0;
    }
    result = csr_motion_parse_no_arg(token, "CLEAR_ESTOP", CSR_CMD_CLEAR_ESTOP, command);
    if (result != 0)
    {
        return (result > 0) ? 1 : 0;
    }
    result = csr_motion_parse_no_arg(token, "INFO", CSR_CMD_INFO, command);
    if (result != 0)
    {
        return (result > 0) ? 1 : 0;
    }

    if (strcmp(token, "W") == 0)
    {
        for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
        {
            token = strtok(0, ",");
            if ((token == 0) || (csr_motion_parse_float(token, &command->target_vel[index]) == 0))
            {
                csr_motion_link_send_error((token == 0) ? "arg_count" : "parse_float");
                g_bad_frame_count++;
                return 0;
            }
        }
        if (strtok(0, ",") != 0)
        {
            csr_motion_link_send_error("arg_count");
            g_bad_frame_count++;
            return 0;
        }
        command->type = CSR_CMD_W;
        return 1;
    }

    if ((strcmp(token, "E") == 0) || (strcmp(token, "D") == 0))
    {
        csr_cmd_type_t type;

        type = (token[0] == 'E') ? CSR_CMD_E : CSR_CMD_D;
        token = strtok(0, ",");
        if ((token == 0) || (csr_motion_parse_channel(token, &command->channel) == 0))
        {
            csr_motion_link_send_error("bad_channel");
            g_bad_frame_count++;
            return 0;
        }
        if (strtok(0, ",") != 0)
        {
            csr_motion_link_send_error("arg_count");
            g_bad_frame_count++;
            return 0;
        }
        command->type = type;
        return 1;
    }

    if (strcmp(token, "M") == 0)
    {
        token = strtok(0, ",");
        if ((token == 0) || (csr_motion_parse_channel(token, &command->channel) == 0))
        {
            csr_motion_link_send_error("bad_channel");
            g_bad_frame_count++;
            return 0;
        }
        token = strtok(0, ",");
        if (token == 0)
        {
            csr_motion_link_send_error("arg_count");
            g_bad_frame_count++;
            return 0;
        }
        endptr = 0;
        pwm_value = strtol(token, &endptr, 10);
        if ((endptr == token) || (*endptr != '\0'))
        {
            csr_motion_link_send_error("parse_int");
            g_bad_frame_count++;
            return 0;
        }
        if ((pwm_value < -CSR_INPUT_PWM_MAX) || (pwm_value > CSR_INPUT_PWM_MAX))
        {
            csr_motion_link_send_error("range");
            g_bad_frame_count++;
            return 0;
        }
        if (strtok(0, ",") != 0)
        {
            csr_motion_link_send_error("arg_count");
            g_bad_frame_count++;
            return 0;
        }
        command->type = CSR_CMD_M;
        command->pwm = (int16_t)pwm_value;
        return 1;
    }

    csr_motion_link_send_error("bad_prefix");
    g_bad_frame_count++;
    return 0;
}

static void csr_append_text(char *line, size_t line_size, const char *text)
{
    size_t current;

    current = strlen(line);
    if (current < (line_size - 1U))
    {
        strncat(line, text, line_size - current - 1U);
    }
}

static void csr_append_float3(char *line, size_t line_size, float value)
{
    char fragment[24];
    long scaled;
    unsigned long absolute;

    scaled = (value >= 0.0f) ? (long)(value * 1000.0f + 0.5f) : (long)(value * 1000.0f - 0.5f);
    absolute = (scaled < 0L) ? (unsigned long)(-scaled) : (unsigned long)scaled;
    if (scaled < 0L)
    {
        sprintf(fragment, "-%lu.%03lu", absolute / 1000UL, absolute % 1000UL);
    }
    else
    {
        sprintf(fragment, "%lu.%03lu", absolute / 1000UL, absolute % 1000UL);
    }
    csr_append_text(line, line_size, fragment);
}

void csr_motion_link_init(uint32_t baudrate)
{
    GPIO_InitTypeDef gpio_init;
    USART_InitTypeDef usart_init;
    NVIC_InitTypeDef nvic_init;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_AFIO, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2, ENABLE);

    gpio_init.GPIO_Pin = GPIO_Pin_2;
    gpio_init.GPIO_Mode = GPIO_Mode_AF_PP;
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &gpio_init);
    gpio_init.GPIO_Pin = GPIO_Pin_3;
    gpio_init.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(GPIOA, &gpio_init);

    USART_StructInit(&usart_init);
    usart_init.USART_BaudRate = baudrate;
    usart_init.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    USART_Init(USART2, &usart_init);
    USART_ITConfig(USART2, USART_IT_RXNE, ENABLE);
    USART_ITConfig(USART2, USART_IT_TXE, DISABLE);
    USART_Cmd(USART2, ENABLE);

    nvic_init.NVIC_IRQChannel = USART2_IRQn;
    nvic_init.NVIC_IRQChannelPreemptionPriority = 0U;
    nvic_init.NVIC_IRQChannelSubPriority = 0U;
    nvic_init.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&nvic_init);

    g_line_length = 0U;
    g_discard_line = 0U;
    g_rx_head = 0U;
    g_rx_tail = 0U;
    g_tx_head = 0U;
    g_tx_tail = 0U;
    g_rx_overflow_count = 0UL;
    g_tx_overflow_count = 0UL;
    g_rx_overflow_event = 0U;
    g_bad_frame_count = 0UL;
}

int csr_motion_link_poll(csr_motion_command_t *command)
{
    uint8_t value;

    if (g_rx_overflow_event != 0U)
    {
        __disable_irq();
        g_rx_tail = g_rx_head;
        g_rx_overflow_event = 0U;
        __enable_irq();
        g_line_length = 0U;
        g_discard_line = 1U;
        g_bad_frame_count++;
        return 0;
    }

    while (csr_motion_try_read_byte(&value) != 0)
    {
        if (value == '\r')
        {
            continue;
        }
        if (value == '\n')
        {
            if (g_discard_line != 0U)
            {
                g_discard_line = 0U;
                g_line_length = 0U;
                csr_motion_link_send_error("line_too_long");
                continue;
            }
            g_line[g_line_length] = '\0';
            g_line_length = 0U;
            if (csr_motion_parse_line(g_line, command) != 0)
            {
                return 1;
            }
            continue;
        }
        if (g_discard_line != 0U)
        {
            continue;
        }
        if (g_line_length < (CSR_MOTION_LINE_SIZE - 1U))
        {
            g_line[g_line_length++] = (char)value;
        }
        else
        {
            g_discard_line = 1U;
            g_bad_frame_count++;
        }
    }
    return 0;
}

void csr_motion_link_send_ready(void)
{
    csr_motion_send_text("CSR_RF1_READY\r\n");
}

void csr_motion_link_send_ack(const char *name)
{
    char line[40];
    sprintf(line, "ACK:%s\r\n", name);
    csr_motion_send_text(line);
}

void csr_motion_link_send_error(const char *reason)
{
    char line[56];
    sprintf(line, "ERR:%s\r\n", reason);
    csr_motion_send_text(line);
}

void csr_motion_link_send_info(void)
{
    csr_motion_send_text("INFO,COMBINED," CSR_COMBINED_FW_VERSION "," CSR_MOTION_PROTOCOL_VERSION "," CSR_ARM_PROTOCOL_VERSION "\r\n");
}

void csr_motion_link_send_enc(csr_channel_t channel, int32_t count, int32_t delta)
{
    char line[96];
    sprintf(line, "ENC,%u,%ld,%ld\r\n", (unsigned int)(channel + 1), (long)count, (long)delta);
    csr_motion_send_text(line);
}

void csr_motion_link_send_dbg(csr_channel_t channel, uint8_t phase_a, uint8_t phase_b, uint16_t timer_count, int32_t count, int32_t delta)
{
    char line[128];
    sprintf(line, "DBG,%u,%u,%u,%u,%ld,%ld\r\n", (unsigned int)(channel + 1),
            (unsigned int)phase_a, (unsigned int)phase_b, (unsigned int)timer_count,
            (long)count, (long)delta);
    csr_motion_send_text(line);
}

void csr_motion_link_send_vel(const float *rt, const float *tg)
{
    char line[192];
    uint8_t index;

    strcpy(line, "VEL");
    for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
    {
        csr_append_text(line, sizeof(line), ",");
        csr_append_float3(line, sizeof(line), rt[index]);
    }
    for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
    {
        csr_append_text(line, sizeof(line), ",");
        csr_append_float3(line, sizeof(line), tg[index]);
    }
    csr_append_text(line, sizeof(line), "\r\n");
    csr_motion_send_text(line);
}

void csr_motion_link_send_pwm(const int16_t *pwm)
{
    char line[96];
    sprintf(line, "PWM,%d,%d,%d,%d\r\n", pwm[0], pwm[1], pwm[2], pwm[3]);
    csr_motion_send_text(line);
}

void csr_motion_link_send_navdbg(const float *cmd, const float *ramp, const float *rt, const int16_t *out)
{
    char line[256];
    char fragment[24];
    uint8_t index;

    strcpy(line, "NAVDBG");
    for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
    {
        csr_append_text(line, sizeof(line), ",");
        csr_append_float3(line, sizeof(line), cmd[index]);
    }
    for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
    {
        csr_append_text(line, sizeof(line), ",");
        csr_append_float3(line, sizeof(line), ramp[index]);
    }
    for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
    {
        csr_append_text(line, sizeof(line), ",");
        csr_append_float3(line, sizeof(line), rt[index]);
    }
    for (index = 0U; index < CSR_CHANNEL_COUNT; index++)
    {
        sprintf(fragment, ",%d", out[index]);
        csr_append_text(line, sizeof(line), fragment);
    }
    csr_append_text(line, sizeof(line), "\r\n");
    csr_motion_send_text(line);
}

uint32_t csr_motion_link_rx_overflow_count(void)
{
    return g_rx_overflow_count;
}

uint32_t csr_motion_link_tx_overflow_count(void)
{
    return g_tx_overflow_count;
}

uint32_t csr_motion_link_bad_frame_count(void)
{
    return g_bad_frame_count;
}

void USART2_IRQHandler(void)
{
    uint16_t next_head;

    if (USART_GetITStatus(USART2, USART_IT_RXNE) != RESET)
    {
        uint8_t value;

        value = (uint8_t)(USART_ReceiveData(USART2) & 0xFFU);
        next_head = csr_ring_next(g_rx_head, CSR_MOTION_RX_RING_SIZE);
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

    if (USART_GetITStatus(USART2, USART_IT_TXE) != RESET)
    {
        if (g_tx_tail != g_tx_head)
        {
            USART_SendData(USART2, g_tx_ring[g_tx_tail]);
            g_tx_tail = csr_ring_next(g_tx_tail, CSR_MOTION_TX_RING_SIZE);
        }
        else
        {
            USART_ITConfig(USART2, USART_IT_TXE, DISABLE);
        }
    }
}
