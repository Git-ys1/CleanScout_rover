/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __Y_TRACKING_H
#define __Y_TRACKING_H

/* Includes ------------------------------------------------------------------*/
#include "main.h"

/*******传感器IO口映射表*******/
/* 循迹引脚读取，从右数1-》4 */

#define TRTACK_IR4_X1_PIN  GPIO_Pin_4
#define TRTACK_IR4_X1_PORT GPIOC                 /* GPIO端口 */
#define TRTACK_IR4_X1_CLK  RCC_APB2Periph_GPIOC  /* GPIO端口时钟 */

#define TRTACK_IR4_X2_PIN GPIO_Pin_5
#define TRTACK_IR4_X2_PORT GPIOC                /* GPIO端口 */
#define TRTACK_IR4_X2_CLK RCC_APB2Periph_GPIOC  /* GPIO端口时钟 */

#define TRTACK_IR4_X3_PIN GPIO_Pin_0
#define TRTACK_IR4_X3_PORT GPIOB                /* GPIO端口 */
#define TRTACK_IR4_X3_CLK RCC_APB2Periph_GPIOB  /* GPIO端口时钟 */

#define TRTACK_IR4_X4_PIN GPIO_Pin_1
#define TRTACK_IR4_X4_PORT GPIOB                /* GPIO端口 */
#define TRTACK_IR4_X4_CLK RCC_APB2Periph_GPIOB  /* GPIO端口时钟 */

/*******快捷指令表*******/
#define TRTACK_IR4_X1_READ() GPIO_ReadInputDataBit(TRTACK_IR4_X1_PORT,TRTACK_IR4_X1_PIN)
#define TRTACK_IR4_X2_READ() GPIO_ReadInputDataBit(TRTACK_IR4_X2_PORT,TRTACK_IR4_X2_PIN)
#define TRTACK_IR4_X3_READ() GPIO_ReadInputDataBit(TRTACK_IR4_X3_PORT,TRTACK_IR4_X3_PIN)
#define TRTACK_IR4_X4_READ() GPIO_ReadInputDataBit(TRTACK_IR4_X4_PORT,TRTACK_IR4_X4_PIN)

void TRACK_IR4_Init(void);

#endif

/******************* (C) 版权 2022 XTARK **************************************/

