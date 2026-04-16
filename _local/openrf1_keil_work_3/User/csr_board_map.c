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
 * 初始方向按当前已知实测预填：CN1/CN3 需要翻转，CN2/CN4 保持。
 * 这只是 bringup 起点，最终以 C-3.0.5 真值表回填为准。
 */
int8_t g_csr_motor_dir_sign[CSR_CHANNEL_COUNT] = { -1, 1, -1, 1 };
int8_t g_csr_encoder_dir_sign[CSR_CHANNEL_COUNT] = { 1, 1, 1, 1 };

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
