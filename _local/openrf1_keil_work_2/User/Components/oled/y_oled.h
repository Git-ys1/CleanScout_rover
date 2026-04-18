/****************************************************************************
 *	@笔者	：	Q
 *	@日期	：	2023年2月10日
 *	@所属	：	杭州松甲科技
 *	@功能	：	存放OLED相关的函数
 ****************************************************************************/

#ifndef _Y_OLED_H_
#define _y_OLED_H_

#include "main.h"

/*******OLED配置命令宏定义*******/
#define OLED_ADDRESS 0x78 // 通过调整0R电阻,屏可以0x78和0x7A两个地址 -- 默认0x78

#define Brightness 0xCF
#define X_WIDTH 128
#define Y_WIDTH 64

/*******OLED相关函数声明*******/
void OLED_Write_Dat(unsigned char I2C_Data);
void OLED_Write_Cmd(unsigned char I2C_Command);
void OLED_ON(void);
void OLED_OFF(void);
void OLED_Set_Pos(unsigned char x, unsigned char y);
void OLED_Fill(unsigned char fill_Data);
void OLED_CLS(void);

void OLED_Init(void);
void OLED_P6x8Str(unsigned char x, unsigned char y, unsigned char ch[]);
void OLED_P8x16Str(unsigned char x, unsigned char y, unsigned char ch[]);
void OLED_P16x16Ch(unsigned char x, unsigned char y, unsigned char N, const unsigned char *fontLibrary);
void OLED_ShowStr(unsigned char x, unsigned char y, unsigned char ch[], unsigned char TextSize);
void OLED_DrawBMP(unsigned char x0, unsigned char y0, unsigned char x1, unsigned char y1, unsigned char BMP[], uint16_t len);
void OLED_TEST(void);
void OLED_ShowColorFont(unsigned char x, unsigned char y, unsigned char N);
#endif
