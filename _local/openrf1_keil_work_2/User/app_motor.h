/*
 * @文件描述: 
 * @作者: Q
 * @Date: 2023-02-13 16:09:51
 * @LastEditTime: 2023-02-15 15:02:45
 */
#ifndef _APP_MOTOR_H_
#define _APP_MOTOR_H_
#include "main.h"

#define PI					3.14159265358979f

#define PID_RATE 50 // PID频率，(进入PID函数的频率)

// 电机编码器分辨率
#define WHEEL_RESOLUTION 1560.0f // 26极磁编码器分辨率,开关霍尔：13*4*30（减速比）= 1560

// 小车参数
#define MEC_WHEEL_BASE 0.205f													// 轮距，左右轮的距离
#define MEC_ACLE_BASE 0.225f													// 轴距，前后轮的距离
#define MEC_WHEEL_DIAMETER 0.08f												// 轮子直径
#define MEC_WHEEL_SCALE (PI * MEC_WHEEL_DIAMETER * PID_RATE / WHEEL_RESOLUTION) // 轮子速度m/s与编码器转换系数

// 机器人速度限制
#define R_VX_LIMIT 1500 // X轴速度限值 m/s*1000
#define R_VY_LIMIT 1200 // Y轴速度限值 m/s*1000
#define R_VW_LIMIT 6280 // W旋转角速度限值 rad/s*1000

void app_motor_init(void);
void app_motor_run(void);

void motor_speed_set(float A,float B,float C,float D);
#endif
