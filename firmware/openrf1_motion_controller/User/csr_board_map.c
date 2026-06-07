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
 * 这两张表来自 car_move_lihaotian 工程实际参与编译的根目录版本。
 *
 * 原工程同时存在根目录与 User/ 两套 csr_board_map.c/h：Keil 实际编译
 * 根目录 .c，却让 User/main.c 包含 User/ 下的参数头文件。C-3.6.0 将
 * 它们合并为此处唯一真值，避免“改了参数但没编进固件”。
 */
int8_t g_csr_motor_dir_sign[CSR_CHANNEL_COUNT] = {-1, -1, -1, -1};
int8_t g_csr_encoder_dir_sign[CSR_CHANNEL_COUNT] = {1, 1, -1, -1};

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
