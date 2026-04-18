#ifndef _Y_DELAY_H_
#define _Y_DELAY_H_

#include "main.h"

#define mdelay(x) delay_ms(x)

void delay_ns(u16 t);
void delay_us(u16 t);
void delay_ms(u16 t);
#endif

