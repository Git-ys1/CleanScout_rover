#include "stm32f10x.h"
#include "main.h"

/* SWJ引脚配置 */
void SWJ_gpio_init(void)
{
    /**********************
    1.执行端口重映射时,复用功能时钟得使能:RCC_APB2Periph_AFIO

    2.  &1.GPIO_Remap_SWJ_Disable: !< Full SWJ Disabled (JTAG-DP + SW-DP)
         此时PA13|PA14|PA15|PB3|PB4都可作为普通IO用了
       为了保存某些调试端口,GPIO_Remap_SWJ_Disable也可选择为下面两种模式：

        &2.GPIO_Remap_SWJ_JTAGDisable: !< JTAG-DP Disabled and SW-DP Enabled
        此时PA15|PB3|PB4可作为普通IO用了

        &3.GPIO_Remap_SWJ_NoJTRST: !< Full SWJ Enabled (JTAG-DP + SW-DP) but without JTRST
        此时只有PB4可作为普通IO用了
    **********************/
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOB | RCC_APB2Periph_AFIO, ENABLE); // 使能 PA 端口时钟
    //GPIO_PinRemapConfig(GPIO_Remap_SWJ_Disable, ENABLE);                                               // 使能禁止JTAG和SW-DP
    GPIO_PinRemapConfig(GPIO_Remap_SWJ_JTAGDisable, ENABLE); // 使能禁止JTAG开启SW-DP
}

/**
 * @函数描述: 循环执行工作指示灯任务运行，让LED闪烁 1s跳动一次
 * @return {*}
 */
void app_led_run(void)
{
    static u32 time_count = 0;
    if (millis() - time_count < 1000)
        return;
    time_count = millis();
    LED_TOGGLE();
}

// 初始化配置参数
void parameter_init(void)
{
    uint8_t i = 0;

    delay_ms(10);
    w25x_read((u8 *)(&eeprom_info), W25Q64_INFO_ADDR_SAVE_STR, sizeof(eeprom_info)); // 读取全局变量

    if (eeprom_info.version != VERSION) // 判断版本是否是当前版本
    {
        eeprom_info.version = VERSION; // 复制当前版本
        eeprom_info.dj_record_num = 0; // 学习动作组变量赋值0
    }

    if (eeprom_info.dj_bias_pwm[SERVO_NUM] != FLAG_VERIFY)
    {
        for (i = 0; i < SERVO_NUM; i++)
        {
            eeprom_info.dj_bias_pwm[i] = 0;
        }
        eeprom_info.dj_bias_pwm[SERVO_NUM] = FLAG_VERIFY;
    }

    for (i = 0; i < SERVO_NUM; i++)
    {
		pwmServo_bias_set(i,eeprom_info.dj_bias_pwm[i]);
    }
	
    // 执行预存命令 {G0000#000P1500T1000!#000P1500T1000!}
    if (eeprom_info.pre_cmd[PRE_CMD_SIZE] == FLAG_VERIFY)
    {
        if (eeprom_info.pre_cmd[0] == '$')
        {
            parse_cmd(eeprom_info.pre_cmd);
        }
    }
}




/**
  * @brief  主函数
  * @param  无
  * @retval 无
  */
int main(void)
{
	SysTick_Init();  /* 初始化系统嘀答定时器，1ms定时一次 */
	led_init();
	SWJ_gpio_init();
	app_uart_init();
	app_ps2_init();
	pwmServo_init();
	w25x_init();
	setup_kinematics(100, 105, 88, 155, &kinematics);
	parameter_init();

	
	printf("w25q64 id=%x\n",w25x_readId());
	while(1)
	{
		
    app_ps2_run();
		app_uart_run();
		app_led_run();
		app_action_run();
		
	}
}


