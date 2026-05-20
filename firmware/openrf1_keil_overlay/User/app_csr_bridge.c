#include "app_csr_bridge.h"

#include <stdlib.h>
#include <string.h>

#include "app_chassis.h"
#include "csr_uart.h"

typedef enum
{
    CSR_PARSE_OK = 0,
    CSR_PARSE_BAD_PREFIX,
    CSR_PARSE_ARG_COUNT,
    CSR_PARSE_FLOAT
} csr_parse_result_t;

static csr_parse_result_t parse_w_command(const char *line, float *a, float *b, float *c, float *d)
{
    char local[CSR_UART_LINE_BUFFER_SIZE];
    char *token = 0;
    char *end = 0;
    float values[4];
    uint8_t index = 0;

    strncpy(local, line, sizeof(local) - 1);
    local[sizeof(local) - 1] = '\0';

    token = strtok(local, ",");
    if ((token == 0) || (strcmp(token, "W") != 0))
    {
        return CSR_PARSE_BAD_PREFIX;
    }

    for (index = 0; index < 4; index++)
    {
        token = strtok(0, ",");
        if (token == 0)
        {
            return CSR_PARSE_ARG_COUNT;
        }

        values[index] = strtof(token, &end);
        if ((end == token) || (*end != '\0'))
        {
            return CSR_PARSE_FLOAT;
        }
    }

    if (strtok(0, ",") != 0)
    {
        return CSR_PARSE_ARG_COUNT;
    }

    *a = values[0];
    *b = values[1];
    *c = values[2];
    *d = values[3];
    return CSR_PARSE_OK;
}

void app_csr_bridge_init(void)
{
}

void app_csr_bridge_run(void)
{
    char line[CSR_UART_LINE_BUFFER_SIZE];
    float a = 0.0f;
    float b = 0.0f;
    float c = 0.0f;
    float d = 0.0f;
    csr_parse_result_t result;

    if (!csr_uart_read_line(line, sizeof(line)))
    {
        return;
    }

    result = parse_w_command(line, &a, &b, &c, &d);
    if (result == CSR_PARSE_OK)
    {
        app_chassis_set_targets(a, b, c, d);
        printf("ACK:W\r\n");
        return;
    }

    if (result == CSR_PARSE_BAD_PREFIX)
    {
        printf("ERR:bad_prefix\r\n");
    }
    else if (result == CSR_PARSE_ARG_COUNT)
    {
        printf("ERR:arg_count\r\n");
    }
    else
    {
        printf("ERR:parse_float\r\n");
    }
}
