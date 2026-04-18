/****************************************************************************
 *	@笔者	：	Q
 *	@日期	：	2023年2月8日
 *	@所属	：	杭州友辉科技
 *	@功能	：	存放usart串口相关的函数
 ****************************************************************************/

#ifndef _Y_USART_H_
#define _Y_USART_H_
#include "main.h"

#define UART_BUF_SIZE 1024 // 定义最大接收字节数 128

extern char uart_receive_buf[UART_BUF_SIZE]; // 接收缓冲,最大UART_BUF_SIZE个字节.末字节为换行符
extern uint16_t uart_get_ok;              // 接收完成标记
extern char uart_mode;                      /* 指令的模式 */

#define interrupt_open() {__enable_irq();}

#define uart1_open() 	{USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);}
#define uart1_close() 	{USART_ITConfig(USART1, USART_IT_RXNE, DISABLE);}

#define uart2_open() 	{USART_ITConfig(USART2, USART_IT_RXNE, ENABLE);}		
#define uart2_close() 	{USART_ITConfig(USART2, USART_IT_RXNE, DISABLE);}		

#define uart3_open() 	{USART_ITConfig(USART3, USART_IT_RXNE, ENABLE);}		
#define uart3_close() 	{USART_ITConfig(USART3, USART_IT_RXNE, DISABLE);}

#define readOnly(x) x->CR1 |= 4; x->CR1 &= 0xFFFFFFF7;    //串口x配置为只读，CR1->RE=1, CR1->TE=0
#define sendOnly(x) x->CR1 |= 8; x->CR1 &= 0xFFFFFFFB;    //串口x配置为只写，CR1->RE=0, CR1->TE=1

/*******串口相关函数声明*******/
void uart1_init(uint32_t BaudRate); /* 初始化串口1 */
void uart1_send_str(char *s);         /* Usart1发送字符串 */
void uart1_send_int(int tmp);       /*	串口1发送数字 */

void uart3_init(u32 baud);
void uart3_send_str(char *s);

void uart2_init(u32 baud);
void uart2_send_str(char *s);

void uart5_init(u32 baud);
void uart5_send_str(char *s);

#endif
