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
 * C-3.0.6 闭环默认语义：
 * - 原始 M 调试命令已经在 csr_motor_drv.c 内统一为 +pwm 正向
 * - W 闭环层不再二次翻转电机方向
 * - 编码器符号只按串口实测回填：CN2 的 +pwm 计数为负，因此这里反相
 * - CN4 在 C-3.0.6 复测中确认当前表下仍反号，因此保持 +1
 * - CN1/CN3 当前仍无编码器计数，本表不把无反馈问题伪装成符号修正
 */
int8_t g_csr_motor_dir_sign[CSR_CHANNEL_COUNT] = { 1, 1, 1, 1 };
int8_t g_csr_encoder_dir_sign[CSR_CHANNEL_COUNT] = { 1, -1, 1, 1 };

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
