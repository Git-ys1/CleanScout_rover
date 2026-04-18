#include "app_motor.h"

/**
 * @简  述  设置 A B C D轮子的速度，单位m/s
 * @参  数  A B C D轮子的速度
 * @返回值  无
 */
void motor_speed_set(float A,float B,float C,float D)
{
	// 由机器人目标速度计算电机轮子速度（m/s）
	Wheel_A.TG = A;
	Wheel_B.TG = B;
	Wheel_C.TG = C;
	Wheel_D.TG = D;
}


/* 初始化电机相关 */
void app_motor_init(void)
{
    motor_init();
	Encoder_Init();
}

/* 电机运行函数 */
void app_motor_run(void)
{	
	// 通过编码器获取车轮实时转速m/s
	Wheel_A.RT=(float)(ENCODER_A_GetCounter() * MEC_WHEEL_SCALE);
	Wheel_B.RT=(float)(ENCODER_B_GetCounter() * MEC_WHEEL_SCALE);
	Wheel_C.RT=(float)(ENCODER_C_GetCounter() * MEC_WHEEL_SCALE);
	Wheel_D.RT=(float)(ENCODER_D_GetCounter() * MEC_WHEEL_SCALE);

    // 利用PID算法计算电机PWM值
    Wheel_A.PWM = SPEED_PidCtlA(-Wheel_A.TG, Wheel_A.RT); // L1
    Wheel_B.PWM = SPEED_PidCtlB(Wheel_B.TG, Wheel_B.RT); // R1
    Wheel_C.PWM = SPEED_PidCtlC(-Wheel_C.TG, Wheel_C.RT); // L2
    Wheel_D.PWM = SPEED_PidCtlD(Wheel_D.TG, Wheel_D.RT); // R2

    // 设置电机PWM值
    MOTOR_A_SetSpeed(-Wheel_A.PWM);
    MOTOR_B_SetSpeed(-Wheel_B.PWM);
    MOTOR_C_SetSpeed(-Wheel_C.PWM);
    MOTOR_D_SetSpeed(-Wheel_D.PWM);

	//printf("@%f  %f  %d\r\n",Wheel_A.RT,Wheel_A.TG,Wheel_A.PWM);
}

