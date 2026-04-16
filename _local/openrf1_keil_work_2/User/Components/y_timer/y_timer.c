/****************************************************************************
 *	@笔者	：	Q
 *	@日期	：	2023年2月8日
 *	@所属	：	杭州友辉科技
 *	@功能	：	存放定时器相关的函数
 *	@函数列表:
 *	1.	void systick_init(void) -- 初始化systick
 *	2.	void SysTick_Handler(void) interrupt 19 -- systick中断函数
 *	3.	u32 millis(void) -- 滴答时钟查询
 ****************************************************************************/
#include "./y_timer/y_timer.h"

static u32 systick_ms = 0; /* 记录时间 */

/* 初始化systick */
void SysTick_Init(void) // 1毫秒@72MHz
{
	SysTick_Config(SystemCoreClock / 1000);
}

/* SysTick中断 */
void SysTick_Handler(void)
{
	systick_ms++;
}

/* 获取滴答时钟数值 */
u32 millis(void)
{
	return systick_ms;
}



