/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __Y_ENCODER_H
#define __Y_ENCODER_H

/* Includes ------------------------------------------------------------------*/
#include "main.h"

// 不可大于65535 因为F103的定时器是16位的。
#define ENCODER_TIM_PERIOD       (uint16_t)(65535)

void Encoder_Init(void);

int16_t ENCODER_A_GetCounter(void);
int16_t ENCODER_B_GetCounter(void);
int16_t ENCODER_C_GetCounter(void);
int16_t ENCODER_D_GetCounter(void);

#endif

/******************* (C) 版权 2022 XTARK **************************************/
