#ifndef _Y_SERVO_H_
#define _Y_SERVO_H_
#include "main.h"


#define SERVO0_PIN 				GPIO_Pin_9
#define SERVO0_GPIO_PORT 		GPIOB               /* GPIO端口 */
#define SERVO0_GPIO_CLK 		RCC_APB2Periph_GPIOB /* GPIO端口时钟 */

#define SERVO1_PIN 				GPIO_Pin_8
#define SERVO1_GPIO_PORT 		GPIOB               /* GPIO端口 */
#define SERVO1_GPIO_CLK 		RCC_APB2Periph_GPIOB /* GPIO端口时钟 */

#define SERVO2_PIN 				GPIO_Pin_5
#define SERVO2_GPIO_PORT 		GPIOB               /* GPIO端口 */
#define SERVO2_GPIO_CLK 		RCC_APB2Periph_GPIOB /* GPIO端口时钟 */

#define SERVO3_PIN 				GPIO_Pin_4
#define SERVO3_GPIO_PORT 		GPIOB               /* GPIO端口 */
#define SERVO3_GPIO_CLK 		RCC_APB2Periph_GPIOB /* GPIO端口时钟 */

#define SERVO4_PIN 				GPIO_Pin_2
#define SERVO4_GPIO_PORT 		GPIOD               /* GPIO端口 */
#define SERVO4_GPIO_CLK			RCC_APB2Periph_GPIOD /* GPIO端口时钟 */

#define SERVO5_PIN 				GPIO_Pin_11
#define SERVO5_GPIO_PORT 		GPIOC               /* GPIO端口 */
#define SERVO5_GPIO_CLK 		RCC_APB2Periph_GPIOC /* GPIO端口时钟 */

/* 控制舵机引脚输出的宏 */
#define SERVO0_PIN_SET(level) GPIO_WriteBit(SERVO0_GPIO_PORT, SERVO0_PIN, (BitAction)level)
#define SERVO1_PIN_SET(level) GPIO_WriteBit(SERVO1_GPIO_PORT, SERVO1_PIN, (BitAction)level)
#define SERVO2_PIN_SET(level) GPIO_WriteBit(SERVO2_GPIO_PORT, SERVO2_PIN, (BitAction)level)
#define SERVO3_PIN_SET(level) GPIO_WriteBit(SERVO3_GPIO_PORT, SERVO3_PIN, (BitAction)level)
#define SERVO4_PIN_SET(level) GPIO_WriteBit(SERVO4_GPIO_PORT, SERVO4_PIN, (BitAction)level)
#define SERVO5_PIN_SET(level) GPIO_WriteBit(SERVO5_GPIO_PORT, SERVO5_PIN, (BitAction)level)




typedef struct
{
    uint16_t aim;      // 执行目标
    uint16_t time;     // 执行时间
    uint16_t current;  // 当前值
    float increment;     // 增量
	int bias;			//偏差
} pwmServo_t;

/*******相关函数声明*******/
void pwmServo_init(void);                            /* 舵机初始化 */
void pwmServo_angle_set(uint8_t index, int aim, int time); /* 设置舵机参数 */
void pwmServo_stop_motion(uint8_t index);//舵机运动停止函数
void pwmServo_bias_set(uint8_t index, int bias);//设置舵机偏差参数
#endif
