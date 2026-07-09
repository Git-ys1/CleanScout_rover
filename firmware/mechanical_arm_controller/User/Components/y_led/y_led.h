#ifndef _Y_LED_H_
#define _Y_LED_H_
#include "main.h"

/* 定义led引脚，修改编号就可以修改led引脚 */
#define LED_PIN 		GPIO_Pin_13
#define LED_GPIO_PORT 	GPIOC               /* GPIO端口 */
#define LED_GPIO_CLK 	RCC_APB2Periph_GPIOC /* GPIO端口时钟 */

/* 控制LED的宏 */
#define LED_GET_LEVEL() GPIO_ReadOutputDataBit(LED_GPIO_PORT, LED_PIN)                       // 读取LED信号灯状态
#define LED_ON() 		GPIO_ResetBits(LED_GPIO_PORT, LED_PIN)                                  // LED信号灯点亮
#define LED_OFF() 		GPIO_SetBits(LED_GPIO_PORT, LED_PIN)                                   // LED信号灯熄灭
#define LED_TOGGLE() 	GPIO_WriteBit(LED_GPIO_PORT, LED_PIN, (BitAction)(1 - LED_GET_LEVEL())) // 翻转LED信号灯

/*******LED相关函数声明*******/
void led_init(void); // 初始化LED信号灯
#endif
