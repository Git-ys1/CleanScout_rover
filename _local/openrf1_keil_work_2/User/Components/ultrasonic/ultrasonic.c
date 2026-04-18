#include "ultrasonic/ultrasonic.h"

/***********************************************
    ultrasonic_gpio_config()
    功能介绍：超声波传感器引脚配置
    函数参数：无
    返回值：	无
 ***********************************************/
static void ultrasonic_gpio_config(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    RCC_APB2PeriphClockCmd(Trig_GPIO_CLK | Echo_GPIO_CLK, ENABLE);

    // 初始化超声波IO口 Trig   Echo 
    GPIO_InitStructure.GPIO_Pin = Trig_Pin;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(Trig_GPIO_Port, &GPIO_InitStructure);

    GPIO_InitStructure.GPIO_Pin = Echo_Pin;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(Echo_GPIO_Port, &GPIO_InitStructure);
}

/**
 * @函数描述: 定时器3初始化,计数1us，用来计算超声波距离
 * @return {*}
 */
static void timer6_init(void)
{
	TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStructure;

	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM6, ENABLE); // 时钟 TIM1 使能

	TIM_TimeBaseInitStructure.TIM_Period = 30000;					/* 设定计数器自动重装值 */
	TIM_TimeBaseInitStructure.TIM_Prescaler = 71;					/* 预分频器 */
	TIM_TimeBaseInitStructure.TIM_ClockDivision = TIM_CKD_DIV1;		/* 设置时钟分割:TDTS = Tck_tim */
	TIM_TimeBaseInitStructure.TIM_CounterMode = TIM_CounterMode_Up; /* TIM向上计数模式 */
	TIM_TimeBaseInit(TIM6, &TIM_TimeBaseInitStructure);
}


/***********************************************
    ultrasonic_sensor_init()
    功能介绍：初始化超声波传感器
    函数参数：无
    返回值：	无
 ***********************************************/
void ultrasonic_sensor_init(void)
{
	ultrasonic_gpio_config();
	timer6_init();
}


/**
 * @函数描述: 获取距离
 * @return {*}返回距离 cm
 * 距离=高电平时间*声速（340M/S） /2
 */
float ultrasonic_distance_read(void)
{
    uint16_t csb_t;
    uint32_t start_time;
    uint32_t timeout = 20; // 设置超时时间为20毫秒

    TRIG_SET(1);
    delay_ms(2);
    TRIG_SET(0);

    TIM_Cmd(TIM6, ENABLE);   // 使能TIMx外设

    // 等待ECHO信号高电平
    start_time = millis();
    while (ECHO_GET() == 0)
    {
        if ((millis() - start_time) > timeout)
        {
            TIM_Cmd(TIM6, DISABLE); // 禁用TIM13外设
            return -1; // 超时返回
        }
    }

    TIM_SetCounter(TIM6, 0); // 清除计数

    start_time = millis();
    while (ECHO_GET())
    {
        if ((millis() - start_time) > timeout)
        {
            TIM_Cmd(TIM6, DISABLE); // 禁用TIM13外设
            return -1; // 超时返回
        }
    }
    
    csb_t = TIM_GetCounter(TIM6);
    TIM_Cmd(TIM6, DISABLE); // 使能TIMx外设
    // 340m/s = 0.017cm/us
    if (csb_t < 25000)
    {
        return (float)csb_t * 0.017;
    }
    return -1;
}



