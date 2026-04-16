#include "app_uart.h"

/**
 * @函数描述: uart串口相关设备控制初始化
 * @return {*}
 */
void app_uart_init(void)
{
	uart1_init(115200); /* 连接总线设备串口 */
	uart2_init(115200); /* 连接总线设备串口 */
	uart3_init(115200); /* 连接总线设备串口 */
    uart5_init(115200); /* 连接总线设备串口 */
}

/**
 * @函数描述: 循环检测串口接收到的指令
 * @return {*}
 */
void app_uart_run(void)
{
    if (uart_get_ok)
    {
        //printf("\r\n  app_uart_run = %s \r\n", uart_receive_buf);
        if (uart_mode == 1)
        {
            // 命令模式
            parse_cmd(uart_receive_buf);
        }
        else if (uart_mode == 2)
        {
            // 单个舵机调试
            parse_action(uart_receive_buf);
        }
        else if (uart_mode == 3)
        {
            // 多路舵机调试
            parse_action(uart_receive_buf);
        }
		else if (uart_mode == 4)
        {
            // 存储模式
            save_action(uart_receive_buf);
        }
		
		uart_get_ok = 0;
		uart_mode = 0;
    }	
}
