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
 * C-3.1.4C closed-loop vehicle-forward semantics:
 * - M,<ch>,<pwm> remains a raw per-channel diagnostic command.
 * - W,a,b,c,d is the chassis-facing command and applies motor_dir_sign.
 * - CN1/CN3 are mounted opposite to CN2/CN4 in the current chassis, so W+
 *   must drive them with raw negative PWM.
 * - Encoder signs are defined after the W-layer motor sign correction.
 *
 * 2026-04-19 raw sign retest:
 * - CN1 raw -500 -> ENC delta negative, so semantic W+ needs encoder -1.
 * - CN3 raw -500 -> ENC delta positive, so semantic W+ keeps encoder +1.
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
