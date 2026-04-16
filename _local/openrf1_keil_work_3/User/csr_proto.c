#include "main.h"

#define CSR_PROTO_RX_BUFFER_SIZE 64

static char g_rx_buffer[CSR_PROTO_RX_BUFFER_SIZE];
static uint8_t g_rx_length = 0;

static int csr_proto_try_read_byte(uint8_t *value)
{
    if (USART_GetFlagStatus(USART2, USART_FLAG_RXNE) == RESET)
    {
        return 0;
    }

    *value = (uint8_t)(USART_ReceiveData(USART2) & 0xFF);
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

static int csr_proto_parse_line(char *line, csr_proto_command_t *command)
{
    char buffer[CSR_PROTO_RX_BUFFER_SIZE];
    char *token;
    char *endptr = 0;
    long pwm_value;

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
    USART_Cmd(USART2, ENABLE);

    g_rx_length = 0;
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
