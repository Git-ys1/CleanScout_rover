#ifndef _Y_GLOBAL_H_
#define _Y_GLOBAL_H_

#include "main.h"
#include "app_motor.h"
/*
	宏定义数据
*/
#define VERSION 20230629  // 版本定义
#define ACTION_USE_ROM 0  // 1:动作组使用内部数组动作组	0:动作组使用上位机下载动作组
#define CYCLE 1000		  // PWM模块周期
#define PS2_LED_RED 0x73  // PS2手柄红灯模式
#define PS2_LED_GRN 0x41  // PS2手柄绿灯模式
#define PSX_BUTTON_NUM 16 // 手柄按键数目
#define PS2_MAX_LEN 32	  // 手柄命令最大字节数
#define FLAG_VERIFY 0x25  // 校验标志
#define ACTION_SIZE 256	  // 一个动作的存储大小

#define SERVO_NUM 8 /* 舵机数量 */

#define MODULE "YH-KSTM32"

#define W25Q64_INFO_ADDR_SAVE_STR (((8 << 10) - 4) << 10) //(8*1024-4)*1024		//eeprom_info结构体存储的位置

extern u8 AI_mode;
extern u8 forbid_turn;//循迹模式适配地图
extern u8 group_do_ok;

extern uint8_t uart_receive_num;
extern int oled_mode;

#define CMD_RETURN_SIZE 1024

#define PRE_CMD_SIZE 128

typedef struct
{
	u32 version;
	u32 dj_record_num;
	char pre_cmd[PRE_CMD_SIZE + 1];
	int dj_bias_pwm[SERVO_NUM + 1];
	uint8_t color_base_flag;
	int color_red_base;
	int color_grn_base;
	int color_blu_base;

	uint16_t ps2_cmd_size; /* ps2指令数据大小 */
} eeprom_info_t;

extern eeprom_info_t eeprom_info;
extern char cmd_return[CMD_RETURN_SIZE];

uint16_t str_contain_str(char *str, char *str2);
int abs_int(int int1);
void selection_sort(int *a, int len);
void replace_char(char *str, char ch1, char ch2);
void int_exchange(int *int1, int *int2);
float abs_float(float value);

void parse_action(char *uart_receive_buf);
void parse_cmd(char *cmd);

int kinematics_move(float x, float y, float z, int time);
void set_servo(int index, int pwm, int time);
void zx_uart_send_str(char *str);

void soft_reset(void);
void parse_string(char *str);
void rewrite_eeprom(void);
void save_action(char *str);
void app_action_run(void);
void do_group_once(int group_num);
#endif
