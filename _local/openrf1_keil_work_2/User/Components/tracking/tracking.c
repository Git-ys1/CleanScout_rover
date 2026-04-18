#include "tracking/tracking.h"


/**
 * @函数描述:  4路红外循迹初始化引脚，配置为输入
 * @return {*}
 */
void TRACK_IR4_Init(void)
{
	GPIO_InitTypeDef GPIO_InitStructure;

    RCC_APB2PeriphClockCmd(TRTACK_IR4_X1_CLK | TRTACK_IR4_X2_CLK | TRTACK_IR4_X3_CLK | TRTACK_IR4_X4_CLK, ENABLE); /* 使能 舵机 端口时钟 */
	
	GPIO_InitStructure.GPIO_Pin = TRTACK_IR4_X1_PIN;         /* 配置 pin */
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;  	/* 浮空输入 */
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz; 		 /* IO 翻转 50MHz */
    GPIO_Init(TRTACK_IR4_X1_PORT, &GPIO_InitStructure);
	
    GPIO_InitStructure.GPIO_Pin = TRTACK_IR4_X2_PIN;
    GPIO_Init(TRTACK_IR4_X2_PORT, &GPIO_InitStructure);

    GPIO_InitStructure.GPIO_Pin = TRTACK_IR4_X3_PIN;
    GPIO_Init(TRTACK_IR4_X3_PORT, &GPIO_InitStructure);

    GPIO_InitStructure.GPIO_Pin = TRTACK_IR4_X4_PIN;
    GPIO_Init(TRTACK_IR4_X4_PORT, &GPIO_InitStructure);
}


