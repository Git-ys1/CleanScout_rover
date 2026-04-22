#include "csr_board_map.h"

static const char *g_channel_names[CSR_CHANNEL_COUNT] =
{
    "CN1",
    "CN2",
    "CN3",
    "CN4"
};

static const char *g_channel_notes[CSR_CHANNEL_COUNT] =
{
    "左后",
    "左前",
    "右后",
    "右前"
};

/*
 * C-3.3.1A closed-loop channel semantics:
 * - Channel order is CN1/LR, CN2/LF, CN3/RR, CN4/RF.
 * - M,<ch>,<pwm> remains a raw per-channel diagnostic command.
 * - W,a,b,c,d is the chassis-facing command and applies motor_dir_sign.
 * - Current W+ maps all four channels to the same low-level H-bridge phase
 *   (IN1=SET).  csr_motor_drv normalizes compare values so the same signed
 *   PWM magnitude means the same effective duty on every channel.
 * - Encoder signs are defined after the W-layer motor sign correction.
 */
int8_t g_csr_motor_dir_sign[CSR_CHANNEL_COUNT] = { -1, 1, -1, 1 };
int8_t g_csr_encoder_dir_sign[CSR_CHANNEL_COUNT] = { -1, -1, 1, 1 };

const char *csr_channel_name(csr_channel_t channel)
{
    if (channel >= CSR_CHANNEL_COUNT)
    {
        return "CN?";
    }
    return g_channel_names[channel];
}

const char *csr_channel_wheel_note(csr_channel_t channel)
{
    if (channel >= CSR_CHANNEL_COUNT)
    {
        return "未知";
    }
    return g_channel_notes[channel];
}
