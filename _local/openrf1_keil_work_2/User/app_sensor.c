///*
// * @文件描述:
// * @作者: Q
// * @Date: 2023-02-13 14:01:12
// * @LastEditTime: 2023-03-28 09:32:51
// */
#include "app_sensor.h"

static void AI_xunji_moshi(void);
void AI_ziyou_bizhang(void);
static void AI_xunji_moshi_pro(void);
void AI_gensui_moshi(void);

uint8_t xunji_mode = 0;
uint8_t IR_X3, IR_X2, IR_X4, IR_X1;
int trackState = 0;
int T_cross = 0, flag_F, forbid_F;

/**
 * @函数描述: 传感器相关设备控制初始化
 * @return {*}
 */
void app_sensor_init(void)
{
    TRACK_IR4_Init();
    ultrasonic_sensor_init();
}

/**
 * @函数描述: 循环检测输出传感器引脚的AD值
 * @return {*}
 */
void app_sensor_run(void)
{
    static u8 AI_mode_bak;

    // 有动作执行，直接返回
    if (group_do_ok == 0)
        return;
	
    if (AI_mode == 0)
    {
    }
    else if (AI_mode == 1) /* 调用智能循迹模式函数,可直接在代码14行找到 uint8_t xunji_mode = 1;
                              进行循迹功能切换，等于0时为普通十字路口循迹，等于1时加强了四路循迹，可进行锐角直角循迹，适配本店地图。
                            */
    {
        if (xunji_mode == 0)
            AI_xunji_moshi();
        else
            AI_xunji_moshi_pro();
    }
    else if (AI_mode == 2)
    {
        AI_ziyou_bizhang(); // 自由避障
    }
    else if (AI_mode == 3)
    {
        AI_gensui_moshi(); // 跟随功能
    }
    else if (AI_mode == 10)
    {
        AI_mode = 255;
    }

    if (AI_mode_bak != AI_mode)
    {
        AI_mode_bak = AI_mode;
        group_do_ok = 1;
    }
}

/*************************************************************
函数名称：AI_xunji_moshi()
功能介绍：实现循迹功能
函数参数：无
返回值：  无
*************************************************************/
static void AI_xunji_moshi(void)
{
    uint8_t IR_X3, IR_X2, IR_X4, IR_X1;
    static uint8_t cross_flag = 0, state = 0, cross = 0;

    IR_X3 = TRTACK_IR4_X3_READ();
    IR_X2 = TRTACK_IR4_X2_READ();
    IR_X1 = TRTACK_IR4_X1_READ();
    IR_X4 = TRTACK_IR4_X4_READ();
	//printf("%d  %d  %d  %d \r\n",IR_X1,IR_X2,IR_X3,IR_X4);

    /**********其中三个参数，state包含循迹状态与十字路口的三种状态
     * 0：普通循迹模式
     * 1：第一次遇到十字路口
     * 2：第二次遇到十字路口
     * 3：第三次遇到十字路口
     * cross是state在case 0中遇到十字路口第几次的标志位
     * cross_flag则是十字路口执行完成后的标志位
     **************************************/

	if (cross_flag == 1)
	{
		// 前进
		motor_speed_set(0.2,0.2,0.2,0.2);
		if (IR_X1 == 1 || IR_X4 == 1)
			cross_flag = 0;
	}

	switch (state)
	{
	case 0:
		if (IR_X3 == 0 && IR_X2 == 0 && IR_X1 == 1 && IR_X4 == 1)
		{
			// 前进
			motor_speed_set(0.2,0.2,0.2,0.2);
		}
		else if ((IR_X3 == 0 && IR_X2 == 1) || (IR_X2 == 1 && IR_X4 == 0 && IR_X1 == 1))
		{
			/* 右边出去，左转 */
			motor_speed_set(0,0.2,0,0.2);
		}
		else if ((IR_X3 == 1 && IR_X2 == 0) || (IR_X3 == 1 && IR_X4 == 1 && IR_X1 == 0))
		{
			// 右转
			motor_speed_set(0.2,0,0.2,0);
		}
		else if (IR_X3 == 0 && IR_X2 == 0 && IR_X1 == 0 && IR_X4 == 0 && (cross_flag == 0))
		{

			motor_speed_set(0,0,0,0);
			if (cross == 0)
				state = 1;
			else if (cross == 1)
				state = 2;
			else if (cross == 2)
				state = 3;
		}
		break;
	case 1:
		if (AI_mode == 1)
		{
			// sprintf(cmd_return, "$DGT:%d-%d,%d!", 9, 17, 1); // 打印字符串到数组中
			// parse_cmd(cmd_return);   // 解析动作组
		}
		state = 0;
		cross = 1;
		cross_flag = 1;
		break;
	case 2:
		if (AI_mode == 1)
		{
			// sprintf(cmd_return, "$DGT:%d-%d,%d!", 9, 17, 1); // 打印字符串到数组中
			// parse_cmd(cmd_return);   // 解析动作组
		}
		state = 0;
		cross = 2;
		cross_flag = 1;
		break;
	case 3:
		state = 0;
		cross = 0;
		cross_flag = 0;
		if (AI_mode == 1)
		{
			AI_mode = 255;
		}
		break;
	}
    
}

static void AI_xunji_moshi_pro(void)
{
    IR_X3 = TRTACK_IR4_X3_READ();
    IR_X2 = TRTACK_IR4_X2_READ();
    IR_X1 = TRTACK_IR4_X1_READ();
    IR_X4 = TRTACK_IR4_X4_READ();

    //	 printf("%d  %d  %d  %d",IR_X1,IR_X2,IR_X3,IR_X4);
    //	delay_ms(2000);


     /**********其中三个参数，trackState表示直角或锐角转弯时的三种状态
     * 0：普通循迹模式
     * 1：左转情况，当小车遇到角度较小等复杂路况，则一直左转直至电平变为直走电平（1001）时才恢复正常
     * 2：右转情况，当小车遇到角度较小等复杂路况，则一直右转直至电平变为直走电平（1001）时才恢复正常
     * flag_F是为了限制在S弯行进时X4探头频繁切换状态
     * forbid_turn用于适配地图，当遇到第1和第3个T字路口时都不会转弯而是直走
     * 用户在使用过程中，可通过调整IX\IY\IW三个值而达到好的循迹效果
     * 尽量避免使用delay_ms函数，会造成程序异常 
     **************************************/
    switch (trackState)
    {
    case 0:
        if ((IR_X1 == 1 && IR_X2 == 1 && IR_X3 == 1 && IR_X4 == 1 && flag_F != 1))
        {
            motor_speed_set(0.4,0,0.4,0);
        }
        if ((IR_X1 == 1 && IR_X2 == 0 && IR_X3 == 0 && IR_X4 == 1))
        {
            // 四路传感器都检测到黑线，前进
            motor_speed_set(0.2,0.2,0.2,0.2);
            flag_F = 0;
            forbid_F = 0;

            if (forbid_turn == 1 || forbid_turn == 4)
            {
                forbid_turn = 2;
            }
        }
        else if (IR_X1 == 1 && IR_X2 == 0 && IR_X3 == 0 && IR_X4 == 0)
        {
            // 左大弯
            motor_speed_set(0.05,0.4,0.05,0.4);
            trackState = 1;
        }
        else if (IR_X1 == 0 && IR_X2 == 0 && IR_X3 == 0 && IR_X4 == 1)
        {
            if (forbid_turn == 0)
            {
                motor_speed_set(0.2,0.2,0.2,0.2);
                forbid_turn = 1;
            }
            else if (forbid_turn == 3)
            {

                motor_speed_set(0.2,0.2,0.2,0.2);
                forbid_turn = 4;
            }
            else if (forbid_turn != 0 && forbid_turn != 1 && forbid_turn != 4)
            {
                // 右大弯
                motor_speed_set(0.4,0.05,0.4,0.05);
                trackState = 2;
            }
        }
        else if (IR_X4 == 0 && forbid_F != 1)
        {
            // 左最外侧检测
			motor_speed_set(0.1,1,0.1,1);
            flag_F = 1;
        }
        else if (IR_X1 == 0)
        {
            // 右最外侧检测
			motor_speed_set(1,0.1,1,0.1);
        }
        else if (IR_X1 == 1 && IR_X2 == 1 && IR_X3 == 0 && IR_X4 == 1)
        {
            // 中间黑线上的传感器微调车左转
            motor_speed_set(0.2,0.4,0.2,0.4);
        }
        else if (IR_X1 == 1 && IR_X2 == 0 && IR_X3 == 1 && IR_X4 == 1)
        {
            // 中间黑线上的传感器微调车右转
            motor_speed_set(0.4,0.2,0.4,0.2);
        }
        break;
    case 1:
		motor_speed_set(0.08,0.58,0.08,0.58);
        if (IR_X1 == 1 && IR_X2 == 0 && IR_X3 == 0 && IR_X4 == 1)
        {
            trackState = 0;
            forbid_F = 1;
            delay_ms(200);
        }
        break;
    case 2:
		motor_speed_set(0.58,0.08,0.58,0.08);
        if (IR_X1 == 1 && IR_X2 == 0 && IR_X3 == 0 && IR_X4 == 1)
        {
            delay_ms(200);
            trackState = 0;
            forbid_turn = 3;
        }
    }
}

/*************************************************************
函数名称：AI_ziyou_bizhang()
功能介绍：识别物体距离从而避开物体前进
函数参数：无
返回值：  无
*************************************************************/
void AI_ziyou_bizhang(void)
{
    static u32 systick_ms_bak = 0;
    static int bz_num = 0, bz_num_bak = 0;
    int adc_csb;
    if (millis() - systick_ms_bak > 50)
    {
        systick_ms_bak = millis();

        adc_csb = (int)ultrasonic_distance_read(); // 获取a0的ad值，计算出距离
        //printf("adc_csb=%d\r\n", adc_csb);
        if ((adc_csb < 35) && (adc_csb > 15))
        {
            
            bz_num = 2;
      
        }
        else if (adc_csb < 15)
        {
					
            bz_num = 1;
					
        }else  {
					
				    bz_num = 3;
				}
				
        if (bz_num != bz_num_bak)
        {
            switch (bz_num)
            {
            case 1:
                motor_speed_set(-0.3,-0.3,-0.3,-0.3);
                break;
            case 2:
                motor_speed_set(0,1,0,1);
                break;
            case 3:
                motor_speed_set(0.3,0.3,0.3,0.3);

                break;
            default:
                zx_uart_send_str("error\n");
                break;
            }
            bz_num_bak = bz_num;
        }
    }
}

/*************************************************************
函数名称：AI_gensui_moshi()
功能介绍：检测物体距离，在一定距离内实现跟随功能
函数参数：无
返回值：  无
*************************************************************/
void AI_gensui_moshi(void)
{
    static u32 systick_ms_bak = 0;
    int adc_csb;
    if (millis() - systick_ms_bak > 100)
    {
        systick_ms_bak = millis();
        adc_csb = ultrasonic_distance_read(); // 获取a0的ad值，计算出距离

        if ((adc_csb > 40))
        {
            // 距离30~50cm前进
            motor_speed_set(0.6,0.6,0.6,0.6);
        }
        else if ((adc_csb < 20) && (adc_csb > 0))
        {
            // 距离低于20cm就后退
            motor_speed_set(-0.6,-0.6,-0.6,-0.6);
        }
        else
        {
            // 其他情况停止
            motor_speed_set(0,0,0,0);
        }
    }
}
