#ifndef _MAIN_H_
#define _MAIN_H_
#include <stdio.h>  //标准库文件
#include <string.h> //标准库文件
#include <math.h>   //标准库文件
#include <stdlib.h>

#include "stm32f10x_conf.h"
#include "stm32f10x.h"

/* 驱动 */
#include "./y_delay/y_delay.h" /* 包含延时函数 */
#include "./y_timer/y_timer.h" /* 包含定时相关函数 */
#include "./y_led/y_led.h"     /* 包含led相关函数 */
#include "./y_usart/y_usart.h" /* 串口相关函数 */
#include "./y_servo/y_servo.h" /* 舵机相关函数 */
#include "y_motor/y_motor.h"
#include "y_encoder/y_encoder.h"
#include "ps2/y_ps2.h"
#include "ultrasonic/ultrasonic.h"
#include "tracking/tracking.h"
#include "flash/y_flash.h"
#include "oled/y_oled.h"
#include "soft_i2c/y_soft_i2c.h"

#include "./y_kinematics/y_kinematics.h" /* 逆运动学算法 */
#include "./y_global/y_global.h"

/* 应用 */
#include "app_ps2.h"
#include "app_motor.h"
#include "app_uart.h"
#include "app_sensor.h"
#include "resource/resource.h"
typedef u8 bool;

#endif
