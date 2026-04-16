#include "y_motor/y_motor.h"

// 电机PID控制参数
int16_t motor_kp = 800;
int16_t motor_kd = 400;

// 机器人轮子数据
ROBOT_Wheel Wheel_A, Wheel_B, Wheel_C, Wheel_D;

/**
 * @简  述  电机引脚配置函数
 */
void motor_init(void)
{
	GPIO_InitTypeDef GPIO_InitStructure;
	TIM_TimeBaseInitTypeDef TIM_Initstructure; // 定义TIM结构体
	TIM_OCInitTypeDef TIM_OCInitStructure;		   // 定义输出比较结构体
	
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_TIM8, ENABLE); // 打开定时器的时钟
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO, ENABLE);
	
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);
	

	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7 | GPIO_Pin_8 | GPIO_Pin_9; /* 配置 pin */
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;									 /* 复用输出 */
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;								 /* IO 翻转 50MHz */
	GPIO_Init(GPIOC, &GPIO_InitStructure);

	GPIO_InitStructure.GPIO_Pin =GPIO_Pin_8 | GPIO_Pin_11 | GPIO_Pin_12;		  /* 配置 pin */
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;  /* 推挽输出 */
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz; /* IO 翻转 50MHz */
	GPIO_Init(GPIOA, &GPIO_InitStructure);

	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;		  /* 配置 pin */
	GPIO_Init(GPIOC, &GPIO_InitStructure);


	//设置缺省值
    TIM_OCStructInit(&TIM_OCInitStructure);

	TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_PWM1;			   // 采用PWM1模式
	TIM_OCInitStructure.TIM_OutputState = TIM_OutputState_Enable; // 配置输出使能OR使能
	TIM_OCInitStructure.TIM_OCPolarity = TIM_OCPolarity_High;	   // 比较输出极性
	TIM_OCInitStructure.TIM_Pulse = 0;
	
	TIM_OC1Init(TIM8, &TIM_OCInitStructure);					   // 输出比较初始化
	TIM_OC2Init(TIM8, &TIM_OCInitStructure);					   // 输出比较初始化
	TIM_OC3Init(TIM8, &TIM_OCInitStructure);					   // 输出比较初始化
	TIM_OC4Init(TIM8, &TIM_OCInitStructure);					   // 输出比较初始化
	
	TIM_Initstructure.TIM_ClockDivision = TIM_CKD_DIV1;		// 不分频
	TIM_Initstructure.TIM_CounterMode = TIM_CounterMode_Up; // 向上计数
	TIM_Initstructure.TIM_Period = 2000;
	TIM_Initstructure.TIM_Prescaler = 1;
	TIM_TimeBaseInit(TIM8, &TIM_Initstructure);
	TIM_Cmd(TIM8, ENABLE); // 使能时钟
	
	//设置PWM输出为使能
    TIM_CtrlPWMOutputs(TIM8, ENABLE);
}

/**
 * @简  述  电机PID控制函数
 * @参  数  spd_target:编码器速度目标值 ,范围（±250）
 *          spd_current: 编码器速度当前值
 * @返回值  电机PWM速度
 */
int16_t SPEED_PidCtlA(float spd_target, float spd_current)
{
	static int16_t motor_pwm_out;
	static float bias, bias_last;

	// 获得偏差值
	bias = spd_target - spd_current;

	// PID计算电机输出PWM值
	motor_pwm_out += motor_kp * bias + motor_kd * (bias - bias_last);

	// 记录上次偏差
	bias_last = bias;

	// 限制最大输出
	if (motor_pwm_out > 2000)
		motor_pwm_out = 2000;
	if (motor_pwm_out < -2000)
		motor_pwm_out = -2000;

	// 返回PWM控制值
	return motor_pwm_out;
}

/**
 * @简  述  电机PID控制函数
 * @参  数  spd_target:编码器速度目标值
 *          spd_target: 编码器速度当前值
 * @返回值  电机PWM速度
 */
int16_t SPEED_PidCtlB(float spd_target, float spd_current)
{
	static int16_t motor_pwm_out;
	static float bias, bias_last;

	// 获得偏差值
	bias = spd_target - spd_current;

	// PID计算电机输出PWM值
	motor_pwm_out += motor_kp * bias + motor_kd * (bias - bias_last);

	// 记录上次偏差
	bias_last = bias;

	// 限制最大输出
	if (motor_pwm_out > 2000)
		motor_pwm_out = 2000;
	if (motor_pwm_out < -2000)
		motor_pwm_out = -2000;

	// printf("@%d  ",motor_pwm_out);

	// 返回PWM控制值
	return motor_pwm_out;
}

/**
 * @简  述  电机PID控制函数
 * @参  数  spd_target:编码器速度目标值
 *          spd_target: 编码器速度当前值
 * @返回值  电机PWM速度
 */
int16_t SPEED_PidCtlC(float spd_target, float spd_current)
{
	static int16_t motor_pwm_out;
	static float bias, bias_last;

	// 获得偏差值
	bias = spd_target - spd_current;

	// PID计算电机输出PWM值
	motor_pwm_out += motor_kp * bias + motor_kd * (bias - bias_last);

	// 记录上次偏差
	bias_last = bias;

	// 限制最大输出
	if (motor_pwm_out > 2000)
		motor_pwm_out = 2000;
	if (motor_pwm_out < -2000)
		motor_pwm_out = -2000;

	// 返回PWM控制值
	return motor_pwm_out;
}

/**
 * @简  述  电机PID控制函数
 * @参  数  spd_target:编码器速度目标值
 *          spd_target: 编码器速度当前值
 * @返回值  电机PWM速度
 */
int16_t SPEED_PidCtlD(float spd_target, float spd_current)
{
	static int16_t motor_pwm_out;
	static float bias, bias_last;

	// 获得偏差值
	bias = spd_target - spd_current;

	// PID计算电机输出PWM值
	motor_pwm_out += motor_kp * bias + motor_kd * (bias - bias_last);

	// 记录上次偏差
	bias_last = bias;

	// 限制最大输出
	if (motor_pwm_out > 2000)
		motor_pwm_out = 2000;
	if (motor_pwm_out < -2000)
		motor_pwm_out = -2000;

	// 返回PWM控制值
	return motor_pwm_out;
}

/**
 * @简  述 电机PWM速度控制
 * @参  数 speed 电机转速数值，范围-2000~2000
 * @返回值 无
 */
void MOTOR_A_SetSpeed(int16_t speed)
{
	int16_t temp;

	temp = speed;

	if (temp > 2000)
		temp = 2000;
	if (temp < -2000)
		temp = -2000;

	if (temp > 0)
	{
		TIM_SetCompare2(TIM8, temp);
		GPIO_WriteBit(GPIOA, GPIO_Pin_11, Bit_RESET);
	}
	else
	{
		TIM_SetCompare2(TIM8, 2000 + temp);
		GPIO_WriteBit(GPIOA, GPIO_Pin_11, Bit_SET);
	}
}

/**
 * @简  述 电机PWM速度控制
 * @参  数 speed 电机转速数值，范围-2000~2000
 * @返回值 无
 */
void MOTOR_B_SetSpeed(int16_t speed)
{
	int16_t temp;

	temp = speed;

	if (temp > 2000)
		temp = 2000;
	if (temp < -2000)
		temp = -2000;

	if (temp > 0)
	{
		TIM_SetCompare4(TIM8, temp);
		GPIO_WriteBit(GPIOC, GPIO_Pin_10, Bit_RESET);
	}
	else
	{
		TIM_SetCompare4(TIM8, 2000 + temp);
		GPIO_WriteBit(GPIOC, GPIO_Pin_10, Bit_SET);
	}
}

/**
 * @简  述 电机PWM速度控制
 * @参  数 speed 电机转速数值，范围-2000~2000
 * @返回值 无
 */
void MOTOR_C_SetSpeed(int16_t speed)
{
	int16_t temp;

	temp = speed;

	if (temp > 2000)
		temp = 2000;
	if (temp < -2000)
		temp = -2000;

	if (temp > 0)
	{
		TIM_SetCompare1(TIM8, temp);
		GPIO_WriteBit(GPIOA, GPIO_Pin_8, Bit_RESET);
	}
	else
	{
		TIM_SetCompare1(TIM8, 2000 + temp);
		GPIO_WriteBit(GPIOA, GPIO_Pin_8, Bit_SET);
	}
}

/**
 * @简  述 电机PWM速度控制
 * @参  数 speed 电机转速数值，范围-2000~2000
 * @返回值 无
 */
void MOTOR_D_SetSpeed(int16_t speed)
{
	int16_t temp;

	temp = speed;

	if (temp > 2000)
		temp = 2000;
	if (temp < -2000)
		temp = -2000;

	if (temp > 0)
	{
		TIM_SetCompare3(TIM8, temp);
		GPIO_WriteBit(GPIOA, GPIO_Pin_12, Bit_RESET);
	}
	else
	{
		TIM_SetCompare3(TIM8, 2000 + temp);
		GPIO_WriteBit(GPIOA, GPIO_Pin_12, Bit_SET);
	}
}
