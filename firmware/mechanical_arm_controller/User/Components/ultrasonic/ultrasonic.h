/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __Y_ULTRASONIC_H
#define __Y_ULTRASONIC_H

/* Includes ------------------------------------------------------------------*/
#include "main.h"

/*******传感器IO口映射表*******/
#define Trig_Pin 				GPIO_Pin_5//超声波引脚
#define Trig_GPIO_Port 			GPIOA
#define Trig_GPIO_CLK 			RCC_APB2Periph_GPIOA /* GPIO端口时钟 */

#define Echo_Pin 				GPIO_Pin_4
#define Echo_GPIO_Port 			GPIOA
#define Echo_GPIO_CLK 			RCC_APB2Periph_GPIOA /* GPIO端口时钟 */

/*******快捷指令表*******/
#define TRIG_SET(x) GPIO_WriteBit(Trig_GPIO_Port, Trig_Pin, (BitAction)x)
#define ECHO_GET()  GPIO_ReadInputDataBit(Echo_GPIO_Port, Echo_Pin)

void ultrasonic_sensor_init(void);
float ultrasonic_distance_read(void);

#endif

/******************* (C) 版权 2022 XTARK **************************************/

