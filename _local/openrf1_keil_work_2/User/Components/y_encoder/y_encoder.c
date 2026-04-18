#include "y_encoder/y_encoder.h"

// 定时器3通道1通道2连接编码器 A
static void Encoder_Init_TIM3(void)
{
	TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;
	TIM_ICInitTypeDef TIM_ICInitStructure;
	GPIO_InitTypeDef GPIO_InitStructure;
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3, ENABLE); //使能定时器4的时钟

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);			  //使能端口时钟
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_7;			  //端口配置
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING; //浮空输入
	GPIO_Init(GPIOA, &GPIO_InitStructure);		  //根据设定参数初始化GPIO

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);			  //使能端口时钟
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6;			  //端口配置
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING; //浮空输入
	GPIO_Init(GPIOA, &GPIO_InitStructure);		  //根据设定参数初始化GPIO

	TIM_TimeBaseStructInit(&TIM_TimeBaseStructure);
	TIM_TimeBaseStructure.TIM_Prescaler = 0x0;					// 预分频器
	TIM_TimeBaseStructure.TIM_Period = ENCODER_TIM_PERIOD;		//设定计数器自动重装值
	TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1;		//选择时钟分频：不分频
	TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up; //TIM向上计数
	TIM_TimeBaseInit(TIM3, &TIM_TimeBaseStructure);
	TIM_EncoderInterfaceConfig(TIM3, TIM_EncoderMode_TI12, TIM_ICPolarity_Rising, TIM_ICPolarity_Rising); //使用编码器模式3
	TIM_ICStructInit(&TIM_ICInitStructure);
	TIM_ICInitStructure.TIM_ICFilter = 10;
	TIM_ICInit(TIM3, &TIM_ICInitStructure);
	TIM_ClearFlag(TIM3, TIM_FLAG_Update);                   //清除TIM的更新标志位
	TIM_ITConfig(TIM3, TIM_IT_Update, ENABLE);
	//Reset counter
	TIM_SetCounter(TIM3, 0);
	TIM_Cmd(TIM3, ENABLE);
}

// TIM4初始化为编码器接口模式, B
static void Encoder_Init_TIM4(void)
{
	TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;
	TIM_ICInitTypeDef TIM_ICInitStructure;
	GPIO_InitTypeDef GPIO_InitStructure;
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM4, ENABLE); //使能定时器4的时钟

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);			  //使能端口时钟
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_7;			  //端口配置
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING; //浮空输入
	GPIO_Init(GPIOB, &GPIO_InitStructure);		  //根据设定参数初始化GPIO

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);			  //使能端口时钟
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6;			  //端口配置
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING; //浮空输入
	GPIO_Init(GPIOB, &GPIO_InitStructure);		  //根据设定参数初始化GPIO

	TIM_TimeBaseStructInit(&TIM_TimeBaseStructure);
	TIM_TimeBaseStructure.TIM_Prescaler = 0x0;					// 预分频器
	TIM_TimeBaseStructure.TIM_Period = ENCODER_TIM_PERIOD;		//设定计数器自动重装值
	TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1;		//选择时钟分频：不分频
	TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up; //TIM向上计数
	TIM_TimeBaseInit(TIM4, &TIM_TimeBaseStructure);
	TIM_EncoderInterfaceConfig(TIM4, TIM_EncoderMode_TI12, TIM_ICPolarity_Rising, TIM_ICPolarity_Rising); //使用编码器模式3
	TIM_ICStructInit(&TIM_ICInitStructure);
	TIM_ICInitStructure.TIM_ICFilter = 10;
	TIM_ICInit(TIM4, &TIM_ICInitStructure);
	TIM_ClearFlag(TIM4, TIM_FLAG_Update);                   //清除TIM的更新标志位
	TIM_ITConfig(TIM4, TIM_IT_Update, ENABLE);
	//Reset counter
	TIM_SetCounter(TIM4, 0);
	TIM_Cmd(TIM4, ENABLE);
}

// 定时器5通道1通道2连接编码器 C
static void Encoder_Init_TIM5(void)
{
	TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;
	TIM_ICInitTypeDef TIM_ICInitStructure;
	GPIO_InitTypeDef GPIO_InitStructure;
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM5, ENABLE); //使能定时器5的时钟

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);			  //使能端口时钟
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0;			  //端口配置
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING; //浮空输入
	GPIO_Init(GPIOA, &GPIO_InitStructure);		  //根据设定参数初始化GPIO

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);			  //使能端口时钟
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_1;			  //端口配置
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING; //浮空输入
	GPIO_Init(GPIOA, &GPIO_InitStructure);		  //根据设定参数初始化GPIO

	TIM_TimeBaseStructInit(&TIM_TimeBaseStructure);
	TIM_TimeBaseStructure.TIM_Prescaler = 0x0;					//预分频器
	TIM_TimeBaseStructure.TIM_Period = ENCODER_TIM_PERIOD;		//设定计数器自动重装值
	TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1;		//选择时钟分频：不分频
	TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up; //TIM向上计数
	TIM_TimeBaseInit(TIM5, &TIM_TimeBaseStructure);

	TIM_EncoderInterfaceConfig(TIM5, TIM_EncoderMode_TI12, TIM_ICPolarity_Rising, TIM_ICPolarity_Rising); //使用编码器模式3

	TIM_ICStructInit(&TIM_ICInitStructure);
	TIM_ICInitStructure.TIM_ICFilter = 10;
	TIM_ICInit(TIM5, &TIM_ICInitStructure);
	TIM_ClearFlag(TIM5, TIM_FLAG_Update);                  //清除TIM的更新标志位
	TIM_ITConfig(TIM5, TIM_IT_Update, ENABLE);
	//Reset counter
	TIM_SetCounter(TIM5, 0);
	TIM_Cmd(TIM5, ENABLE);
}

// TIM2初始化为编码器接口模式， D
static void Encoder_Init_TIM2(void)  
{  
    TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;  
    TIM_ICInitTypeDef TIM_ICInitStructure;  
    GPIO_InitTypeDef GPIO_InitStructure;  
  
    // 使能时钟  
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2, ENABLE);  
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOB | RCC_APB2Periph_AFIO, ENABLE);  
  
    // 重映射TIM2引脚（根据您的硬件参考手册）  
	GPIO_PinRemapConfig(GPIO_FullRemap_TIM2, ENABLE);
  
    // 配置GPIOA的PIN15和GPIOB的PIN3为浮空输入  
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_15;  
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;  
    GPIO_Init(GPIOA, &GPIO_InitStructure);  
  
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_3;  
    GPIO_Init(GPIOB, &GPIO_InitStructure);  
  
    // 初始化TIM2的时间基数结构  
    TIM_TimeBaseStructInit(&TIM_TimeBaseStructure);  
    TIM_TimeBaseStructure.TIM_Prescaler = 0x0; // 预分频器  
    TIM_TimeBaseStructure.TIM_Period = ENCODER_TIM_PERIOD; // 设定计数器自动重装值  
    TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1; // 时钟分频  
    TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up; // 向上计数  
    TIM_TimeBaseInit(TIM2, &TIM_TimeBaseStructure);  
  
    // 配置TIM2为编码器模式  
    TIM_EncoderInterfaceConfig(TIM2, TIM_EncoderMode_TI12, TIM_ICPolarity_Rising, TIM_ICPolarity_Rising);  
  
    // 配置输入捕获参数  
    TIM_ICStructInit(&TIM_ICInitStructure);  
    TIM_ICInitStructure.TIM_ICFilter = 10; // 输入捕获滤波器  
    TIM_ICInit(TIM2, &TIM_ICInitStructure);  
  
    // 清除TIM2的更新中断标志位  
    TIM_ClearITPendingBit(TIM2, TIM_IT_Update);  
    // 使能TIM2的更新中断  
    TIM_ITConfig(TIM2, TIM_IT_Update, ENABLE);  
  
    // 设置TIM2的计数器为0  
    TIM_SetCounter(TIM2, 0); // 或者 TIM2->CNT = 0; 但通常只需要一个  
  
    // 启动TIM2  
    TIM_Cmd(TIM2, ENABLE);  
}






/**
 * @简  述  编码器获取计数器数值
 * @参  数  无
 * @返回值  计数器当前值
 */
int16_t ENCODER_A_GetCounter(void)
{
	int16_t Encoder_TIM = 0;
	Encoder_TIM = (short)TIM3->CNT;
	TIM3->CNT=0;
	return Encoder_TIM;
}

/**
 * @简  述  编码器获取计数器数值
 * @参  数  无
 * @返回值  计数器当前值
 */
int16_t ENCODER_B_GetCounter(void)
{
	int16_t Encoder_TIM = 0;
	Encoder_TIM = (short)TIM4->CNT;
	TIM4->CNT=0;
	return Encoder_TIM;
}

/**
 * @简  述  编码器获取计数器数值
 * @参  数  无
 * @返回值  计数器当前值
 */
int16_t ENCODER_C_GetCounter(void)
{
	int16_t Encoder_TIM = 0;
	Encoder_TIM = (short)TIM5->CNT;
	TIM5->CNT=0;
	return Encoder_TIM;
}

/**
 * @简  述  编码器获取计数器数值
 * @参  数  无
 * @返回值  计数器当前值
 */
int16_t ENCODER_D_GetCounter(void)
{
	int16_t Encoder_TIM = 0;
	Encoder_TIM = (short)TIM2->CNT;
	TIM2->CNT=0;
	return Encoder_TIM;
}

// 初始化编码器GPIO和定时器捕获脉冲
void Encoder_Init(void)
{
	Encoder_Init_TIM2();       //  TIM2 PWMC HAL3
	Encoder_Init_TIM4();       //  TIM4 PWMD HAL4
	Encoder_Init_TIM5();       //  TIM5 PWMA HAL1
	Encoder_Init_TIM3();       //  TIM3 PWMB HAL2
}


