#include "main.h"

static volatile uint32_t g_csr_ms = 0;
static int16_t g_target_pwm[CSR_CHANNEL_COUNT] = {0};
static uint32_t g_last_command_ms = 0;

static uint32_t csr_millis(void)
{
    return g_csr_ms;
}

void SysTick_Handler(void)
{
    g_csr_ms++;
}

static void csr_systick_init(void)
{
    SysTick_Config(SystemCoreClock / 1000U);
}

static void csr_apply_targets(void)
{
    uint8_t i;
    for (i = 0; i < CSR_CHANNEL_COUNT; i++)
    {
        csr_motor_set((csr_channel_t)i, g_target_pwm[i]);
    }
}

static void csr_stop_all(void)
{
    uint8_t i;
    for (i = 0; i < CSR_CHANNEL_COUNT; i++)
    {
        g_target_pwm[i] = 0;
    }
    csr_motor_stop_all();
}

int main(void)
{
    csr_proto_command_t command;
    int32_t delta;
    int32_t count;
    uint32_t now_ms;

    csr_systick_init();
    csr_motor_init();
    csr_encoder_init();
    csr_proto_init(CSR_PROTO_BAUDRATE);
    csr_stop_all();
    g_last_command_ms = csr_millis();

    csr_proto_send_ready();

    while (1)
    {
        if (csr_proto_poll(&command) != 0)
        {
            g_last_command_ms = csr_millis();

            switch (command.type)
            {
            case CSR_CMD_M:
                g_target_pwm[command.channel] = command.pwm;
                csr_apply_targets();
                csr_proto_send_ack("M");
                break;
            case CSR_CMD_E:
                delta = csr_encoder_read_and_reset(command.channel);
                count = csr_encoder_peek(command.channel);
                csr_proto_send_ack("E");
                csr_proto_send_enc(command.channel, count, delta);
                break;
            case CSR_CMD_STOP:
                csr_stop_all();
                csr_proto_send_ack("STOP");
                break;
            default:
                break;
            }
        }

        now_ms = csr_millis();
        if ((now_ms - g_last_command_ms) > CSR_COMMAND_TIMEOUT_MS)
        {
            csr_stop_all();
            g_last_command_ms = now_ms;
        }
    }
}
