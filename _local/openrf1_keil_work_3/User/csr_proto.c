#include "main.h"

#define CSR_PROTO_RX_BUFFER_SIZE 64
#define CSR_PROTO_RX_RING_SIZE 128

static char g_rx_buffer[CSR_PROTO_RX_BUFFER_SIZE];
static uint8_t g_rx_length = 0;
static volatile uint8_t g_rx_ring[CSR_PROTO_RX_RING_SIZE];
static volatile uint16_t g_rx_head = 0;
static volatile uint16_t g_rx_tail = 0;

static int csr_proto_try_read_byte(uint8_t *value)
{
    uint16_t tail;

    if (g_rx_head == g_rx_tail)
    {
        return 0;
    }

    tail = g_rx_tail;
    *value = g_rx_ring[tail];
    tail++;
    if (tail >= CSR_PROTO_RX_RING_SIZE)
    {
        tail = 0;
    }
    g_rx_tail = tail;
    return 1;
}

static void csr_proto_send_text(const char *text)
{
    while (*text != '\0')
    {
        while (USART_GetFlagStatus(USART2, USART_FLAG_TXE) == RESET)
        {
        }
        USART_SendData(USART2, (uint16_t)(uint8_t)(*text));
        text++;
    }
}

static void csr_proto_trim(char *line)
{
    size_t length = strlen(line);
    while (length > 0)
    {
        if ((line[length - 1] == '\r') || (line[length - 1] == '\n') || (line[length - 1] == ' ') || (line[length - 1] == '\t'))
        {
            line[length - 1] = '\0';
            length--;
        }
        else
        {
            break;
        }
    }
}

static int csr_proto_parse_channel(const char *token, csr_channel_t *channel)
{
    long value;
    char *endptr = 0;

    value = strtol(token, &endptr, 10);
    if ((endptr == token) || (*endptr != '\0') || (value < 1) || (value > 4))
    {
        return 0;
    }

    *channel = (csr_channel_t)(value - 1);
    return 1;
}

static int csr_proto_parse_float(const char *token, float *value)
{
    double parsed_value;
    char *endptr = 0;

    parsed_value = strtod(token, &endptr);
    if ((endptr == token) || (*endptr != '\0'))
    {
        return 0;
    }

    *value = (float)parsed_value;
    return 1;
}

static void csr_proto_append_text(char *line, size_t line_size, const char *text)
{
    size_t current_length;
    size_t available_length;

    current_length = strlen(line);
    if (current_length >= (line_size - 1U))
    {
        return;
    }

    available_length = line_size - current_length - 1U;
    strncat(line, text, available_length);
}

static void csr_proto_append_float3(char *line, size_t line_size, float value)
{
    char fragment[24];
    long scaled_value;
    unsigned long abs_scaled;
    unsigned long whole;
    unsigned long fraction;

    if (value >= 0.0f)
    {
        scaled_value = (long)(value * 1000.0f + 0.5f);
    }
    else
    {
        scaled_value = (long)(value * 1000.0f - 0.5f);
    }

    if (scaled_value < 0)
    {
        abs_scaled = (unsigned long)(-scaled_value);
        whole = abs_scaled / 1000UL;
        fraction = abs_scaled % 1000UL;
        sprintf(fragment, "-%lu.%03lu", whole, fraction);
    }
    else
    {
        abs_scaled = (unsigned long)scaled_value;
        whole = abs_scaled / 1000UL;
        fraction = abs_scaled % 1000UL;
        sprintf(fragment, "%lu.%03lu", whole, fraction);
    }

    csr_proto_append_text(line, line_size, fragment);
}

static int csr_proto_parse_line(char *line, csr_proto_command_t *command)
{
    char buffer[CSR_PROTO_RX_BUFFER_SIZE];
    char *token;
    char *endptr = 0;
    long pwm_value;
    uint8_t index;

    memset(command, 0, sizeof(*command));

    csr_proto_trim(line);
    if (line[0] == '\0')
    {
        return 0;
    }

    strncpy(buffer, line, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';

    token = strtok(buffer, ",");
    if (token == 0)
    {
        csr_proto_send_error("bad_prefix");
        return 0;
    }

    if (strcmp(token, "STOP") == 0)
    {
        if (strtok(0, ",") != 0)
        {
            csr_proto_send_error("arg_count");
            return 0;
        }
        command->type = CSR_CMD_STOP;
        command->channel = CSR_CHANNEL_CN1;
        command->pwm = 0;
        return 1;
    }

    if (strcmp(token, "W") == 0)
    {
        for (index = 0; index < CSR_CHANNEL_COUNT; index++)
        {
            token = strtok(0, ",");
            if (token == 0)
            {
                csr_proto_send_error("arg_count");
                return 0;
            }

            if (csr_proto_parse_float(token, &command->target_vel[index]) == 0)
            {
                csr_proto_send_error("parse_float");
                return 0;
            }
        }

        if (strtok(0, ",") != 0)
        {
            csr_proto_send_error("arg_count");
            return 0;
        }

        command->type = CSR_CMD_W;
        command->channel = CSR_CHANNEL_CN1;
        command->pwm = 0;
        return 1;
    }

    if (strcmp(token, "E") == 0)
    {
        token = strtok(0, ",");
        if ((token == 0) || (csr_proto_parse_channel(token, &command->channel) == 0))
        {
            csr_proto_send_error("bad_channel");
            return 0;
        }
        if (strtok(0, ",") != 0)
        {
            csr_proto_send_error("arg_count");
            return 0;
        }
        command->type = CSR_CMD_E;
        command->pwm = 0;
        return 1;
    }

    if (strcmp(token, "R") == 0)
    {
        long reg_target;

        token = strtok(0, ",");
        if (token == 0)
        {
            csr_proto_send_error("bad_channel");
            return 0;
        }

        reg_target = strtol(token, &endptr, 10);
        if ((endptr == token) || (*endptr != '\0') || (reg_target < 0) || (reg_target > CSR_CHANNEL_COUNT))
        {
            csr_proto_send_error("bad_channel");
            return 0;
        }
        if (strtok(0, ",") != 0)
        {
            csr_proto_send_error("arg_count");
            return 0;
        }

        command->type = CSR_CMD_R;
        command->reg_target = (uint8_t)reg_target;
        command->pwm = 0;
        return 1;
    }

    if (strcmp(token, "D") == 0)
    {
        token = strtok(0, ",");
        if ((token == 0) || (csr_proto_parse_channel(token, &command->channel) == 0))
        {
            csr_proto_send_error("bad_channel");
            return 0;
        }
        if (strtok(0, ",") != 0)
        {
            csr_proto_send_error("arg_count");
            return 0;
        }
        command->type = CSR_CMD_D;
        command->pwm = 0;
        return 1;
    }

    if (strcmp(token, "M") == 0)
    {
        token = strtok(0, ",");
        if ((token == 0) || (csr_proto_parse_channel(token, &command->channel) == 0))
        {
            csr_proto_send_error("bad_channel");
            return 0;
        }

        token = strtok(0, ",");
        if (token == 0)
        {
            csr_proto_send_error("arg_count");
            return 0;
        }

        pwm_value = strtol(token, &endptr, 10);
        if ((endptr == token) || (*endptr != '\0'))
        {
            csr_proto_send_error("parse_int");
            return 0;
        }
        if ((pwm_value < -CSR_INPUT_PWM_MAX) || (pwm_value > CSR_INPUT_PWM_MAX))
        {
            csr_proto_send_error("range");
            return 0;
        }
        if (strtok(0, ",") != 0)
        {
            csr_proto_send_error("arg_count");
            return 0;
        }

        command->type = CSR_CMD_M;
        command->pwm = (int16_t)pwm_value;
        return 1;
    }

    csr_proto_send_error("bad_prefix");
    return 0;
}

void csr_proto_init(uint32_t baudrate)
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
    gpio_init.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &gpio_init);

    USART_StructInit(&usart_init);
    usart_init.USART_BaudRate = baudrate;
    usart_init.USART_WordLength = USART_WordLength_8b;
    usart_init.USART_StopBits = USART_StopBits_1;
    usart_init.USART_Parity = USART_Parity_No;
    usart_init.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    usart_init.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    USART_Init(USART2, &usart_init);
    USART_ITConfig(USART2, USART_IT_RXNE, ENABLE);
    USART_Cmd(USART2, ENABLE);

    nvic_init.NVIC_IRQChannel = USART2_IRQn;
    nvic_init.NVIC_IRQChannelPreemptionPriority = 1;
    nvic_init.NVIC_IRQChannelSubPriority = 1;
    nvic_init.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&nvic_init);

    g_rx_length = 0;
    g_rx_head = 0;
    g_rx_tail = 0;
}

int csr_proto_poll(csr_proto_command_t *command)
{
    uint8_t value;

    while (csr_proto_try_read_byte(&value) != 0)
    {
        if (value == '\r')
        {
            continue;
        }

        if (value == '\n')
        {
            g_rx_buffer[g_rx_length] = '\0';
            g_rx_length = 0;
            if (csr_proto_parse_line(g_rx_buffer, command) != 0)
            {
                return 1;
            }
            continue;
        }

        if (g_rx_length < (CSR_PROTO_RX_BUFFER_SIZE - 1))
        {
            g_rx_buffer[g_rx_length++] = (char)value;
        }
        else
        {
            g_rx_length = 0;
            csr_proto_send_error("line_too_long");
        }
    }

    return 0;
}

void csr_proto_send_ready(void)
{
    csr_proto_send_text("CSR_RF1_READY\r\n");
}

void csr_proto_send_ack(const char *name)
{
    char line[32];
    sprintf(line, "ACK:%s\r\n", name);
    csr_proto_send_text(line);
}

void csr_proto_send_error(const char *reason)
{
    char line[48];
    sprintf(line, "ERR:%s\r\n", reason);
    csr_proto_send_text(line);
}

void csr_proto_send_enc(csr_channel_t channel, int32_t count, int32_t delta)
{
    char line[96];
    sprintf(line, "ENC,%u,%ld,%ld\r\n", (unsigned int)(channel + 1), (long)count, (long)delta);
    csr_proto_send_text(line);
}

void csr_proto_send_dbg(csr_channel_t channel, uint8_t phase_a, uint8_t phase_b, uint16_t timer_count, int32_t count, int32_t delta)
{
    char line[128];
    sprintf(
        line,
        "DBG,%u,%u,%u,%u,%ld,%ld\r\n",
        (unsigned int)(channel + 1),
        (unsigned int)phase_a,
        (unsigned int)phase_b,
        (unsigned int)timer_count,
        (long)count,
        (long)delta
    );
    csr_proto_send_text(line);
}

void csr_proto_send_reg(uint8_t target, const csr_encoder_reg_snapshot_t *snapshot)
{
    char line[160];

    if (snapshot == 0)
    {
        csr_proto_send_error("reg_snapshot");
        return;
    }

    sprintf(
        line,
        "REG,%u,%08lX,%04X,%04X,%04X,%04X\r\n",
        (unsigned int)target,
        (unsigned long)snapshot->mapr,
        (unsigned int)snapshot->smcr,
        (unsigned int)snapshot->ccmr1,
        (unsigned int)snapshot->ccer,
        (unsigned int)snapshot->cnt
    );
    csr_proto_send_text(line);
}

void csr_proto_send_vel(const float *rt, const float *tg)
{
    char line[192];
    uint8_t index;

    strcpy(line, "VEL");
    for (index = 0; index < CSR_CHANNEL_COUNT; index++)
    {
        csr_proto_append_text(line, sizeof(line), ",");
        csr_proto_append_float3(line, sizeof(line), rt[index]);
    }
    for (index = 0; index < CSR_CHANNEL_COUNT; index++)
    {
        csr_proto_append_text(line, sizeof(line), ",");
        csr_proto_append_float3(line, sizeof(line), tg[index]);
    }
    csr_proto_append_text(line, sizeof(line), "\r\n");
    csr_proto_send_text(line);
}

void csr_proto_send_pwm(const int16_t *pwm)
{
    char line[96];

    sprintf(
        line,
        "PWM,%d,%d,%d,%d\r\n",
        pwm[0],
        pwm[1],
        pwm[2],
        pwm[3]
    );
    csr_proto_send_text(line);
}

void USART2_IRQHandler(void)
{
    uint16_t next_head;
    uint8_t value;

    if (USART_GetITStatus(USART2, USART_IT_RXNE) != RESET)
    {
        value = (uint8_t)(USART_ReceiveData(USART2) & 0xFF);
        next_head = g_rx_head + 1U;
        if (next_head >= CSR_PROTO_RX_RING_SIZE)
        {
            next_head = 0U;
        }

        if (next_head != g_rx_tail)
        {
            g_rx_ring[g_rx_head] = value;
            g_rx_head = next_head;
        }
    }
}
