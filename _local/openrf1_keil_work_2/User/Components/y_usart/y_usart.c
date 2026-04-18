/****************************************************************************
 *	@笔者	：	Q
 *	@日期	：	2023年2月8日
 *	@所属	：	杭州友辉科技
 *	@功能	：	存放usart串口相关的函数
 *	@函数列表:
 *	1.	void uart1_init(u32 baud) -- 初始化串口1
 *	2.	void uart3_init(u32 baud) -- 初始化串口3
 *	3.	void uart1_send_byte(char dat) -- 串口1发送字节
 *	4.	void uart3_send_byte(char dat) -- 串口3发送字节
 *	5.	void uart1_send_str(char *s) -- 串口1发送字符串
 *	6.	void uart3_send_str(char *s) -- 串口3发送字符串
 ****************************************************************************/

#include "y_usart/y_usart.h"

char uart_receive_buf[UART_BUF_SIZE];
uint16_t uart_get_ok;
char uart_mode;

/* 初始化串口1 */
void uart1_init(uint32_t BaudRate)
{
	USART_InitTypeDef USART_InitStructure;
	GPIO_InitTypeDef GPIO_InitStructure;
	NVIC_InitTypeDef NVIC_InitStructure;

	/* 使能端口时钟 */
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_USART1, ENABLE);

	USART_DeInit(USART1);

	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_9;		/* PA.9 */
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP; /* 复用推挽输出 */
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOA, &GPIO_InitStructure);

	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING; /* 浮空输入 */
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOA, &GPIO_InitStructure);

	USART_InitStructure.USART_BaudRate = BaudRate;									/* 串口波特率 */
	USART_InitStructure.USART_WordLength = USART_WordLength_8b;						/* 字长为8位数据格式 */
	USART_InitStructure.USART_StopBits = USART_StopBits_1;							/* 字长为8位数据格式 */
	USART_InitStructure.USART_Parity = USART_Parity_No;								/* 无奇偶校验位 */
	USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;					/* 收发模式 */
	USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None; /* 无硬件数据流控制 */
	USART_Init(USART1, &USART_InitStructure);

	NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1; /* 抢占优先级 */
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;		  /* 子优先级 */
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;			  /* IRQ通道使能 */
	NVIC_Init(&NVIC_InitStructure);

	USART_ITConfig(USART1, USART_IT_RXNE, ENABLE); /* 开启串口接受中断 */
	USART_ITConfig(USART1, USART_IT_TXE, DISABLE); /* 禁止串口发送中断 */

	USART_Cmd(USART1, ENABLE); /* 使能串口1  */
}

/***********************************************
	函数名称:	uart3_init()
	功能介绍:	初始化串口3
	函数参数:	baud 波特率
	返回值:		无
 ***********************************************/
void uart2_init(u32 baud)
{
	GPIO_InitTypeDef GPIO_InitStructure;
	USART_InitTypeDef USART_InitStructure;
	NVIC_InitTypeDef NVIC_InitStructure;

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2, ENABLE);

	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_2;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOA, &GPIO_InitStructure);

	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_3;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
	GPIO_Init(GPIOA, &GPIO_InitStructure);

	USART_InitStructure.USART_BaudRate = baud;
	USART_InitStructure.USART_WordLength = USART_WordLength_8b;
	USART_InitStructure.USART_StopBits = USART_StopBits_1;
	USART_InitStructure.USART_Parity = USART_Parity_No;
	USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
	USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
	USART_Init(USART2, &USART_InitStructure);

	NVIC_InitStructure.NVIC_IRQChannel = USART2_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_Init(&NVIC_InitStructure);

	USART_ITConfig(USART2, USART_IT_RXNE, ENABLE);
	USART_ITConfig(USART2, USART_IT_TXE, DISABLE); /* 禁止串口发送中断 */

	USART_Cmd(USART2, ENABLE);
}

/***********************************************
	函数名称:	uart3_init()
	功能介绍:	初始化串口3
	函数参数:	baud 波特率
	返回值:		无
 ***********************************************/
void uart3_init(u32 baud)
{
	GPIO_InitTypeDef GPIO_InitStructure;
	USART_InitTypeDef USART_InitStructure;
	NVIC_InitTypeDef NVIC_InitStructure;

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART3, ENABLE);

	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_OD;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOB, &GPIO_InitStructure);
	
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_11;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
	GPIO_Init(GPIOB, &GPIO_InitStructure);

	USART_InitStructure.USART_BaudRate = baud;
	USART_InitStructure.USART_WordLength = USART_WordLength_8b;
	USART_InitStructure.USART_StopBits = USART_StopBits_1;
	USART_InitStructure.USART_Parity = USART_Parity_No;
	USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
	USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
	USART_Init(USART3, &USART_InitStructure);

	NVIC_InitStructure.NVIC_IRQChannel = USART3_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_Init(&NVIC_InitStructure);

	USART_ITConfig(USART3, USART_IT_RXNE, ENABLE);
	USART_ITConfig(USART3, USART_IT_TXE, DISABLE); /* 禁止串口发送中断 */

	USART_Cmd(USART3, ENABLE);
}

/***********************************************
	函数名称:	uart5_init()
	功能介绍:	初始化串口5
	函数参数:	baud 波特率
	返回值:		无
 ***********************************************/
void uart5_init(u32 baud)
{
	GPIO_InitTypeDef GPIO_InitStructure;
	USART_InitTypeDef USART_InitStructure;
	NVIC_InitTypeDef NVIC_InitStructure;

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_UART5, ENABLE);

	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_12;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_OD;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOC, &GPIO_InitStructure);

	USART_InitStructure.USART_BaudRate = baud;
	USART_InitStructure.USART_WordLength = USART_WordLength_8b;
	USART_InitStructure.USART_StopBits = USART_StopBits_1;
	USART_InitStructure.USART_Parity = USART_Parity_No;
	USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
	USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
	USART_Init(UART5, &USART_InitStructure);
	USART_HalfDuplexCmd(UART5, ENABLE); // 注意这个，启动半双工模式

	NVIC_InitStructure.NVIC_IRQChannel = UART5_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_Init(&NVIC_InitStructure);

	USART_ITConfig(UART5, USART_IT_RXNE, ENABLE);
	USART_ITConfig(UART5, USART_IT_TXE, DISABLE); /* 禁止串口发送中断 */

	USART_Cmd(UART5, ENABLE);
}

/***********************************************
	功能介绍：	串口1发送字节
	函数参数：	dat 发送的字节
	返回值：		无
 ***********************************************/
void uart1_send_byte(char dat)
{
	USART_SendData(USART1, dat);
	while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET)
		;
}

/***********************************************
	功能介绍：	串口1发送字符串
	函数参数：	*s 发送的字符串
	返回值：		无
 ***********************************************/
void uart1_send_str(char *s)
{
	while (*s)
	{
		uart1_send_byte(*s++);
	}
}

/***********************************************
	功能介绍：	串口1发送数字
	函数参数：	tmp 发送的数字
	返回值：		无
 ***********************************************/
void uart1_send_int(int tmp)
{
	static char str[20];
	sprintf((char *)str, "%d", tmp);
	uart1_send_str(str);
}

/* 重定义fputc函数,写这个函数可以使用printf,记得开启Use MicroLIB */
int fputc(int ch, FILE *f)
{
	while ((UART5->SR & 0X40) == 0)
		; // 循环发送,直到发送完毕
	UART5->DR = (u8)ch;
	return ch;
}

/***********************************************
	函数名称:	uart3_send_str()
	功能介绍:	串口3发送字符串
	函数参数:	*s 发送的字符串
	返回值:		无
 ***********************************************/
void uart2_send_str(char *s)
{
	while (*s)
	{
		USART_SendData(USART2, *s++);
		while (USART_GetFlagStatus(USART2, USART_FLAG_TXE) == RESET)
			;
	}
}

/***********************************************
	函数名称:	uart3_send_str()
	功能介绍:	串口3发送字符串
	函数参数:	*s 发送的字符串
	返回值:		无
 ***********************************************/
void uart3_send_str(char *s)
{
	USART_ITConfig(USART3, USART_IT_RXNE, DISABLE);
	while (*s)
	{
		USART_SendData(USART3, *s++);
		while (USART_GetFlagStatus(USART3, USART_FLAG_TXE) == RESET)
			;
	}
	USART_ITConfig(USART3, USART_IT_RXNE, ENABLE);
}

/***********************************************
	函数名称:	uart5_send_str()
	功能介绍:	串口5发送字符串
	函数参数:	*s 发送的字符串
	返回值:		无
 ***********************************************/
void uart5_send_str(char *s)
{
	USART_ITConfig(UART5, USART_IT_RXNE, DISABLE);
	while (*s)
	{
		USART_SendData(UART5, *s++);
		while (USART_GetFlagStatus(UART5, USART_FLAG_TXE) == RESET)
			;
	}
	USART_ITConfig(UART5, USART_IT_RXNE, ENABLE);
}


/***********************************************
	函数名称:	uart_data_parse()
	功能介绍:	解析串口接收的数据
	函数参数:	uart_data 串口接收的数据
				uart_num 串口号
	返回值:		无
 ***********************************************/
void uart_data_parse(char rx_data,uint8_t uart_num)
{
	static u16 buf_index = 0;
	
	if (uart_get_ok)
		return;
		
	if (uart_mode == 0)
	{
		if (rx_data == '$')
		{
			// 命令模式 $XXX!
			uart_mode = 1;
		}
		else if (rx_data == '#')
		{
			// 单舵机模式	#000P1500T1000! 类似这种命令
			uart_mode = 2;
		}
		else if (rx_data == '{')
		{
			// 多舵机模式	{#000P1500T1000!#001P1500T1000!} 多个单舵机命令用大括号括起来
			uart_mode = 3;
		}
		else if (rx_data == '<')
		{
			// 保存动作组模式	<G0000#000P1500T1000!#001P1500T1000!B000!> 用尖括号括起来 带有组序号
			uart_mode = 4;
		}
		buf_index = 0;
	}

	uart_receive_buf[buf_index++] = rx_data;

	if ((uart_mode == 1) && (rx_data == '!'))
	{
		uart_receive_buf[buf_index] = '\0';
		uart_get_ok = 1;
	}
	else if ((uart_mode == 2) && (rx_data == '!'))
	{
		uart_receive_buf[buf_index] = '\0';
		uart_get_ok = 1;
	}
	else if ((uart_mode == 3) && (rx_data == '}'))
	{
		uart_receive_buf[buf_index] = '\0';
		uart_get_ok = 1;
	}
	else if ((uart_mode == 4) && (rx_data == '>'))
	{
		uart_receive_buf[buf_index] = '\0';
		uart_get_ok = 1;
	}
	
	if(uart_get_ok==1)
	{
		uart_receive_num = uart_num;
	}

	if (buf_index >= UART_BUF_SIZE)
		buf_index = 0;
}

/* 串口1中断服务程序 */
void USART1_IRQHandler(void)
{
	//先判断标志位
	if (USART_GetITStatus(USART1, USART_IT_RXNE) == SET)
	{
		//接收数据
		uint8_t sbuf_bak = USART_ReceiveData(USART1);
		
		uart_data_parse(sbuf_bak,1);//数据解析
		//手动清除标志位
		USART_ClearITPendingBit(USART1, USART_IT_RXNE);  
	}
}

/***********************************************
	函数名称:	void USART2_IRQHandler(void)
	功能介绍:	串口3中断函数
	函数参数:	无
	返回值:		无
 ***********************************************/
void USART2_IRQHandler(void)
{
	//先判断标志位
	if (USART_GetITStatus(USART2, USART_IT_RXNE) == SET)
	{
		//接收数据
		uint8_t sbuf_bak = USART_ReceiveData(USART2);
		
		uart_data_parse(sbuf_bak,2);//数据解析
		//手动清除标志位
		USART_ClearITPendingBit(USART2, USART_IT_RXNE);  
	}
}

/***********************************************
	函数名称:	void USART3_IRQHandler(void)
	功能介绍:	串口3中断函数
	函数参数:	无
	返回值:		无
 ***********************************************/
void USART3_IRQHandler(void)
{
	//先判断标志位
	if (USART_GetITStatus(USART3, USART_IT_RXNE) == SET)
	{
		//接收数据
		uint8_t sbuf_bak = USART_ReceiveData(USART3);
		
		uart_data_parse(sbuf_bak,3);//数据解析
		//手动清除标志位
		USART_ClearITPendingBit(USART3, USART_IT_RXNE);  
	}

}

/***********************************************
	函数名称:	void USART3_IRQHandler(void)
	功能介绍:	串口5中断函数
	函数参数:	无
	返回值:		无
 ***********************************************/
void UART5_IRQHandler(void)
{
	//先判断标志位
	if (USART_GetITStatus(UART5, USART_IT_RXNE) == SET)
	{
		//接收数据
		uint8_t sbuf_bak = USART_ReceiveData(UART5);
		
		uart_data_parse(sbuf_bak,5);//数据解析
		//手动清除标志位
		USART_ClearITPendingBit(UART5, USART_IT_RXNE);  
	}
}
