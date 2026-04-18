/****************************************************************************
 *	@笔者	：	Q
 *	@日期	：	2023年2月8日
 *	@所属	：	杭州友辉科技
 *	@功能	：	存放舵机相关的函数
 *	@函数列表:
 *	1.	void servo_init(void) -- 舵机gpio初始化
 *	3.	void pwmServo_angle_set(u8 index, int aim, int time) -- 设置舵机控制参数函数
 ****************************************************************************/
#include "y_servo/y_servo.h"

pwmServo_t pwmServo_angle[SERVO_NUM];


/* 舵机gpio初始化 */
static void servo_gpio_init(void)
{
    u8 i;
    GPIO_InitTypeDef GPIO_InitStructure;

    RCC_APB2PeriphClockCmd(SERVO0_GPIO_CLK | SERVO1_GPIO_CLK | SERVO2_GPIO_CLK | SERVO3_GPIO_CLK | SERVO4_GPIO_CLK | SERVO5_GPIO_CLK, ENABLE); /* 使能 舵机 端口时钟 */

    GPIO_InitStructure.GPIO_Pin = SERVO0_PIN;         /* 配置引脚 */
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz; /* IO翻转50MHZ */
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;  /* 推挽输出 */
    GPIO_Init(SERVO0_GPIO_PORT, &GPIO_InitStructure);

    GPIO_InitStructure.GPIO_Pin = SERVO1_PIN;
    GPIO_Init(SERVO1_GPIO_PORT, &GPIO_InitStructure);

    GPIO_InitStructure.GPIO_Pin = SERVO2_PIN;
    GPIO_Init(SERVO2_GPIO_PORT, &GPIO_InitStructure);

    GPIO_InitStructure.GPIO_Pin = SERVO3_PIN;
    GPIO_Init(SERVO3_GPIO_PORT, &GPIO_InitStructure);

    GPIO_InitStructure.GPIO_Pin = SERVO4_PIN;
    GPIO_Init(SERVO4_GPIO_PORT, &GPIO_InitStructure);

    GPIO_InitStructure.GPIO_Pin = SERVO5_PIN;
    GPIO_Init(SERVO5_GPIO_PORT, &GPIO_InitStructure);

    for (i = 0; i < SERVO_NUM; i++)
    {
        pwmServo_angle[i].aim = 1500;
        pwmServo_angle[i].current = 1500;
        pwmServo_angle[i].increment = 0;
        pwmServo_angle[i].time = 5000;
		pwmServo_angle[i].bias=0;
    }
}


/**************************************************************************
函数功能：TIM7初始化，模拟PWM，控制舵机
入口参数：无
返回  值：无
**************************************************************************/
static void TIM7_Init(void)
{
	TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;
	NVIC_InitTypeDef NVIC_InitStructure;
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM7, ENABLE); //使能定时器的时钟
	TIM_TimeBaseStructure.TIM_Prescaler = 71;			 // 预分频器
	TIM_TimeBaseStructure.TIM_Period = 9;				 //设定计数器自动重装值
	TIM_TimeBaseInit(TIM7, &TIM_TimeBaseStructure);
	TIM_ClearFlag(TIM7, TIM_FLAG_Update);               //清除TIM的更新标志位
	TIM_ITConfig(TIM7, TIM_IT_Update, ENABLE);

	//中断优先级NVIC设置
	NVIC_InitStructure.NVIC_IRQChannel = TIM7_IRQn;			  //TIM中断
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1; //先占优先级0级
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;		  //从优先级1级
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;			  //IRQ通道被使能
	NVIC_Init(&NVIC_InitStructure);							  //初始化NVIC寄存器

	TIM_Cmd(TIM7, ENABLE);
}



/* 设置舵机每次增加的偏移量 */
static void servo_increment_offset(uint8_t index)
{
    int aim_temp;

    if (pwmServo_angle[index].increment != 0)
    {
        aim_temp = pwmServo_angle[index].aim+pwmServo_angle[index].bias;
		if (aim_temp > 2490)
			aim_temp=2490;
		else if(aim_temp<500)
			aim_temp=500;
		
        if (abs(aim_temp - pwmServo_angle[index].current) <= fabs(pwmServo_angle[index].increment + pwmServo_angle[index].increment))
        {
            pwmServo_angle[index].current = aim_temp;
            pwmServo_angle[index].increment = 0;
        }
        else
        {
            pwmServo_angle[index].current += pwmServo_angle[index].increment;
        }
    }
}

/***********************************************
    功能介绍：	设置舵机引脚电平
    函数参数1：	index 要设置的舵机引脚索引
    函数参数2：	level 要设置的舵机引脚电平，1为高，0为低
    返回值：无
 ***********************************************/
static void servo_pin_set(u8 index, BitAction level)
{
    switch (index)
    {
    case 0:
        SERVO0_PIN_SET(level);
        break;
    case 1:
        SERVO1_PIN_SET(level);
        break;
    case 2:
        SERVO2_PIN_SET(level);
        break;
    case 3:
        SERVO3_PIN_SET(level);
        break;
    case 4:
        SERVO4_PIN_SET(level);
        break;
    case 5:
        SERVO5_PIN_SET(level);
        break;
    default:
        break;
    }
}

// TIM7中断
void TIM7_IRQHandler(void)
{
	static u8 flag = 0;
	static u8 duoji_index1 = 0;
	int temp;
	
	if (TIM_GetITStatus(TIM7, TIM_IT_Update) != RESET) //检查TIM更新中断发生与否
	{
		/* 通过改变重装载值和舵机下标索引，每个舵机定时2500（2.5ms），执行8个舵机后完成一个周期20000（20ms） */
		if (duoji_index1 == 8)
		{
			duoji_index1 = 0;
		}

		if (flag == 0)
		{
			TIM7->ARR = ((unsigned int)(pwmServo_angle[duoji_index1].current));
			servo_pin_set(duoji_index1, Bit_SET);
			servo_increment_offset(duoji_index1);
		}
		else
		{
			temp = 2500 - (unsigned int)(pwmServo_angle[duoji_index1].current);
			TIM7->ARR = temp;
			servo_pin_set(duoji_index1, Bit_RESET);
			duoji_index1++;
		}
		flag = !flag;
		
		TIM_ClearITPendingBit(TIM7, TIM_IT_Update);    //清除TIMx更新中断标志
	}
}

/***********************************************
    功能介绍：	PWM舵机初始化配置函数
    函数参数：	无
    返回值：	无
 ***********************************************/
void pwmServo_init(void)
{
	servo_gpio_init();
	TIM7_Init();
}

/***********************************************
    功能介绍：	设置舵机控制参数函数
    函数参数：	index 舵机编号 aim 执行目标 time 执行时间(如果aim 执行目标==0，视为舵机停止)
    返回值：		无
 ***********************************************/
void pwmServo_angle_set(uint8_t index, int aim, int time)
{
	uint8_t i;
	
	//角度数据超出范围，退出
	if ((aim > 2500) || (aim < 500))
        return;
	
	if(index==255)
	{
		for (i = 0; i < SERVO_NUM; i++)
		{
			pwmServo_angle[i].aim = aim;
			pwmServo_angle[i].increment = (float)((pwmServo_angle[i].aim - pwmServo_angle[i].current) / (pwmServo_angle[i].time / 20.000));
			pwmServo_angle[i].time = time;
		}
		return;
	}
	
    /* 限制输入值大小 */
    if (index >= SERVO_NUM)
        return;

    if (time > 10000)
        time = 10000;

    if (time < 20) /* 执行时间太短，舵机直接以最快速度运动 */
    {
        pwmServo_angle[index].aim = aim;
        pwmServo_angle[index].current = aim;
        pwmServo_angle[index].increment = 0;
    }
    else
    {
        pwmServo_angle[index].aim = aim;
        pwmServo_angle[index].time = time;
        pwmServo_angle[index].increment = (float)((pwmServo_angle[index].aim - pwmServo_angle[index].current) / (pwmServo_angle[index].time / 20.000));
    }
}

/***********************************************
    功能介绍：	设置舵机运动停止函数
    函数参数：	index 舵机编号
    返回值：		无
 ***********************************************/
void pwmServo_stop_motion(uint8_t index)
{
	uint8_t i;
	
	if(index==255)
	{
		for (i = 0; i < SERVO_NUM; i++)
		{
			pwmServo_angle[i].aim = pwmServo_angle[index].current;
			pwmServo_angle[i].increment = 0.001;
		}
		return;
	}
	
	/* 限制输入值大小 */
    if (index >= SERVO_NUM)
        return;
	
	pwmServo_angle[index].aim = pwmServo_angle[index].current;
	pwmServo_angle[index].increment = 0.001;
}

/***********************************************
    功能介绍：	设置舵机偏差参数函数
    函数参数：	index 舵机编号 aim 执行目标 time 执行时间(如果aim 执行目标==0，视为舵机停止)
    返回值：		无
 ***********************************************/
void pwmServo_bias_set(uint8_t index, int bias)
{
	/* 限制输入值大小 */
    if (index >= SERVO_NUM)
        return;
	
	pwmServo_angle[index].bias=bias;
	pwmServo_angle[index].increment = 0.001;
}
