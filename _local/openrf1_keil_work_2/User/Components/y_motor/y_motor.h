/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __Y_MOTOR_H
#define __Y_MOTOR_H

/* Includes ------------------------------------------------------------------*/
#include "main.h"

// 机器人轮子速度数据结构体
typedef struct
{
	short CNT_RT;
	double RT; // 车轮实时速度，单位m/s
	float TG;  // 车轮目标速度，单位m/s
	short PWM; // 车轮PWM控制速度
} ROBOT_Wheel;

extern ROBOT_Wheel Wheel_A, Wheel_B, Wheel_C, Wheel_D;

void motor_init(void); /* 电机控制引脚配置 */

//电机PID闭环速度控制函数
int16_t SPEED_PidCtlA(float spd_target, float spd_current);   //PID控制函数，电机A
int16_t SPEED_PidCtlB(float spd_target, float spd_current);    //PID控制函数，电机B
int16_t SPEED_PidCtlC(float spd_target, float spd_current);    //PID控制函数，电机C
int16_t SPEED_PidCtlD(float spd_target, float spd_current);    //PID控制函数，电机D

void MOTOR_A_SetSpeed(int16_t speed);   //电机A控制
void MOTOR_B_SetSpeed(int16_t speed);   //电机B控制

void MOTOR_C_SetSpeed(int16_t speed);   //电机C控制
void MOTOR_D_SetSpeed(int16_t speed);   //电机D控制

#endif

/******************* (C) 版权 2022 XTARK **************************************/
