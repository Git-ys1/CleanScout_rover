#ifndef __STM32F10X_CONF_H
#define __STM32F10X_CONF_H

/*
 * C-3.6.0 只启用当前底盘固件真正使用的标准外设库模块。
 * 避免模板工程把 ADC/CAN/I2C/SDIO 等无关驱动全部编入工程。
 */
#include "stm32f10x_gpio.h"
#include "stm32f10x_rcc.h"
#include "stm32f10x_tim.h"
#include "stm32f10x_usart.h"
#include "misc.h"

/* 默认关闭参数断言，减少正式固件体积。需要底层调试时可临时打开。 */
/* #define USE_FULL_ASSERT 1 */

#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line);
#define assert_param(expr) ((expr) ? (void)0 : assert_failed((uint8_t *)__FILE__, __LINE__))
#else
#define assert_param(expr) ((void)0)
#endif

#endif
