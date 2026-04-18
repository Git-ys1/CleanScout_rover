#ifndef _APP_PS2_H_
#define _APP_PS2_H_
#include "main.h"

//保存ps2指令
typedef struct
{
	/******************** 按下指令 *******************/
    /* 左边4个按键 */
    char pressed_left_up[32];
    char pressed_left_right[32];
    char pressed_left_down[32];
    char pressed_left_left[32];

    /* 右边4个按键  */
    char pressed_right_up[32];
    char pressed_right_right[32];
    char pressed_right_down[32];
    char pressed_right_left[32];

    /* 中间两个按键  */
    char pressed_select[32];
    char pressed_start[32];

    /* 前面左右各两个按键  */
    char pressed_left_1[32];
    char pressed_left_2[32];
    char pressed_right_1[32];
    char pressed_right_2[32];
	
	char pressed_key_rocker_left[32];//摇杆按键
	char pressed_key_rocker_right[32];
	
	/******************** 释放指令 *******************/
    /* 左边4个按键 */
    char release_left_up[32];
    char release_left_right[32];
    char release_left_down[32];
    char release_left_left[32];

    /* 右边4个按键  */
    char release_right_up[32];
    char release_right_right[32];
    char release_right_down[32];
    char release_right_left[32];

    /* 中间两个按键  */
    char release_select[32];
    char release_start[32];

    /* 前面左右各两个按键  */
    char release_left_1[32];
    char release_left_2[32];
    char release_right_1[32];
    char release_right_2[32];
	
	char release_key_rocker_left[32];//摇杆按键
	char release_key_rocker_right[32];
} ps2_cmd_t;

void app_ps2_init(void);
void app_ps2_run(void);
#endif
