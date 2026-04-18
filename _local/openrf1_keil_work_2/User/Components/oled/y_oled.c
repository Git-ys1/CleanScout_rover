/****************************************************************************
 *	@笔者	：	Q
 *	@日期	：	2023年2月10日
 *	@功能	：	存放OLED相关的函数
 *****************************************************************************/

#include "y_oled.h"
#include "soft_i2c/y_soft_i2c.h"
#include "resource/resource.h"

/***********************************************
    函数名称：i2c_write_byte(I2C_Byte)
    功能介绍：I2C写一个字节
    函数参数：I2C_Byte 写入的字节
    返回值：	无
 ***********************************************/
void I2C_WriteByte(uint8_t addr, uint8_t data)
{
    i2c_start();
    i2c_write_byte(OLED_ADDRESS); // 发送器件地址+写命令
    if (i2c_wait_ack())          // 等待应答
    {
        i2c_stop();
        return;
    }
    i2c_write_byte(addr); // 写寄存器地址
    i2c_wait_ack();      // 等待应答
    i2c_write_byte(data); // 发送数据
    if (i2c_wait_ack())  // 等待ACK
    {
        i2c_stop();
        return;
    }
    i2c_stop();
    return;
}

/***********************************************
    函数名称：OLED_Write_Dat(I2C_Data)
    功能介绍：OLED写一个数据字节
    函数参数：I2C_Data 写入的数据字节
    返回值：	无
 ***********************************************/
void OLED_Write_Dat(unsigned char I2C_Data)
{
    I2C_WriteByte(0x40, I2C_Data);
}

/***********************************************
    函数名称：OLED_Write_Cmd(I2C_Command)
    功能介绍：OLED写一个命令字节
    函数参数：I2C_Command 写入的命令字节
    返回值：	无
 ***********************************************/
void OLED_Write_Cmd(unsigned char I2C_Command)
{
    I2C_WriteByte(0x00, I2C_Command);
}

/***********************************************
    函数名称：OLED_ON()
    功能介绍：OLED开启
    函数参数：无
    返回值：	无
 ***********************************************/
void OLED_ON(void)
{
    OLED_Write_Cmd(0X8D);
    OLED_Write_Cmd(0X14);
    OLED_Write_Cmd(0XAF);
}

/***********************************************
    函数名称：OLED_OFF()
    功能介绍：OLED关闭
    函数参数：无
    返回值：	无
 ***********************************************/
void OLED_OFF(void)
{
    OLED_Write_Cmd(0X8D);
    OLED_Write_Cmd(0X10);
    OLED_Write_Cmd(0XAE);
}

/***********************************************
    函数名称：OLED_Set_Pos(x,y)
    功能介绍：设置OLED写入坐标
    函数参数：x 横坐标 y 纵坐标
    返回值：	无
 ***********************************************/
void OLED_Set_Pos(unsigned char x, unsigned char y)
{
    OLED_Write_Cmd(0xb0 + y);
    OLED_Write_Cmd(((x & 0xf0) >> 4) | 0x10);
    OLED_Write_Cmd((x & 0x0f) | 0x01);
}

/***********************************************
    函数名称：OLED_Fill(fill_Data)
    功能介绍：OLED全屏显示
    函数参数：fill_Data 全屏指令
    返回值：	无
 ***********************************************/
void OLED_Fill(unsigned char fill_Data)
{
    unsigned char y, x;
    for (y = 0; y < 8; y++)
    {
        OLED_Write_Cmd(0xb0 + y);
        OLED_Write_Cmd(0x01);
        OLED_Write_Cmd(0x10);
        for (x = 0; x < X_WIDTH; x++)
            OLED_Write_Dat(fill_Data);
    }
}

/***********************************************
    函数名称：OLED_CLS()
    功能介绍：OLED复位 全屏清除
    函数参数：无
    返回值：	无
 ***********************************************/
void OLED_CLS(void)
{
    OLED_Fill(0x00);
}

/***********************************************
    函数名称：OLED_Init()
    功能介绍：OLED初始化
    函数参数：无
    返回值：	无
 ***********************************************/
void OLED_Init(void)
{
    OLED_Write_Cmd(0xae);       // 关闭oled面板
    OLED_Write_Cmd(0x00);       // 设置低列地址
    OLED_Write_Cmd(0x10);       // 设置高列地址
    OLED_Write_Cmd(0x40);       // 设置起始行地址  设置映射RAM显示起始行(0x00~0x3F)
    OLED_Write_Cmd(0x81);       // 设置对比度控制寄存器
    OLED_Write_Cmd(Brightness); // 设置SEG输出电流亮度
    OLED_Write_Cmd(0xa1);       // 设置SEG/列映射     0xa0左右反置 0xa1正常
    OLED_Write_Cmd(0xc8);       // 设置COM/行扫描方向   0xc0上下反置 0xc8正常
    OLED_Write_Cmd(0xa6);       // 设置正常显示
    OLED_Write_Cmd(0xa8);       // 设置多路复用比(1~64)
    OLED_Write_Cmd(0x3f);       // 1/64 duty
    OLED_Write_Cmd(0xd3);       // 设置显示偏移位移映射RAM计数器(0x00~0x3F)
    OLED_Write_Cmd(0x00);       // 不偏移
    OLED_Write_Cmd(0xd5);       // 设置显示时钟分频比/振荡频率
    OLED_Write_Cmd(0x80);       // 设置分频比，设置时钟为100帧/秒
    OLED_Write_Cmd(0xd9);       // 设置预充电周期
    OLED_Write_Cmd(0xf1);       // 设定预充电为15个时钟，放电为1个时钟
    OLED_Write_Cmd(0xda);       // 设置com引脚硬件配置
    OLED_Write_Cmd(0x12);
    OLED_Write_Cmd(0xdb); // 设置VCOM高
    OLED_Write_Cmd(0x40); // 设置VCOM取消选择电平
    OLED_Write_Cmd(0x20); // 设置页面寻址模式(0x00/0x01/0x02)
    OLED_Write_Cmd(0x02);
    OLED_Write_Cmd(0x8d); // 设置充电泵启用/禁用
    OLED_Write_Cmd(0x14); // 设置(0x10)禁用
    OLED_Write_Cmd(0xa4); // 禁用整个显示(0xa4/0xa5)
    OLED_Write_Cmd(0xa6); // 禁用反向显示(0xa6/0xa7)
    OLED_Write_Cmd(0xaf); // 打开oled面板
    OLED_Fill(0x00);      // 初始清屏
    OLED_Set_Pos(0, 0);

    OLED_CLS();
}

/***********************************************
    函数名称：OLED_P6x8Str(x,y,ch[])
    功能介绍：显示6*8一组标准ASCII字符串
    函数参数：x 起始点横坐标(0~127) y 起始点纵坐标(0~7) ch[] 要显示的字符串
    返回值：	无
 ***********************************************/
void OLED_P6x8Str(unsigned char x, unsigned char y, unsigned char ch[])
{
    unsigned char c = 0, i = 0, j = 0;
    while (ch[j] != '\0')
    {
        c = ch[j] - 32;
        if (x > 126)
        {
            x = 0;
            y++;
        }
        OLED_Set_Pos(x, y);
        for (i = 0; i < 6; i++)
            OLED_Write_Dat(F6x8[c][i]);
        x += 6;
        j++;
    }
}

/***********************************************
    函数名称：OLED_P8x16Str(x,y,ch[])
    功能介绍：显示8*16一组标准ASCII字符串
    函数参数：x 起始点横坐标(0~127) y 起始点纵坐标(0~7) ch[] 要显示的字符串
    返回值：	无
 ***********************************************/
void OLED_P8x16Str(unsigned char x, unsigned char y, unsigned char ch[])
{
    unsigned char c = 0, i = 0, j = 0;
	y=y*2;
    while (ch[j] != '\0')
    {
        c = ch[j] - 32;
        if (x > 120)
        {
            x = 0;
            y++;
        }
        OLED_Set_Pos(x, y);
        for (i = 0; i < 8; i++)
            OLED_Write_Dat(F8X16[c * 16 + i]);
        OLED_Set_Pos(x, y + 1);
        for (i = 0; i < 8; i++)
            OLED_Write_Dat(F8X16[c * 16 + i + 8]);
        x += 8;
        j++;
    }
}

/***********************************************
    函数名称：OLED_ShowStr(x,y,ch[],TextSize)
    功能介绍：显示codetab.h中的ASCII字符
    函数参数：x 起始点横坐标(0~127) y 起始点纵坐标(0~7) ch[] 要显示的字符串 TextSize 字符大小(1:6*8 ; 2:8*16)
    返回值：	无
 ***********************************************/
void OLED_ShowStr(unsigned char x, unsigned char y, unsigned char ch[], unsigned char TextSize)
{
    unsigned char c = 0, i = 0, j = 0;
    switch (TextSize)
    {
    case 1:
    {
        while (ch[j] != '\0')
        {
            c = ch[j] - 32;
            if (x > 126)
            {
                x = 0;
                y++;
            }
            OLED_Set_Pos(x, y);
            for (i = 0; i < 6; i++)
                OLED_Write_Dat(F6x8[c][i]);
            x += 6;
            j++;
        }
    }
    break;
    case 2:
    {
        while (ch[j] != '\0')
        {
            c = ch[j] - 32;
            if (x > 120)
            {
                x = 0;
                y++;
            }
            OLED_Set_Pos(x, y);
            for (i = 0; i < 8; i++)
                OLED_Write_Dat(F8X16[c * 16 + i]);
            OLED_Set_Pos(x, y + 1);
            for (i = 0; i < 8; i++)
                OLED_Write_Dat(F8X16[c * 16 + i + 8]);
            x += 8;
            j++;
        }
    }
    break;
    }
}


/***********************************************
    函数名称：OLED_DrawBMP(x0,y0,x1,y1,BMP[])
    功能介绍：显示显示BMP图片128×64
    函数参数：x 起始点横坐标(0~127) y 起始点纵坐标(0~7) BMP[] 要显示的图片， len 图片的大小
    返回值：	无
 ***********************************************/
void OLED_DrawBMP(unsigned char x0, unsigned char y0, unsigned char x1, unsigned char y1, unsigned char BMP[], uint16_t len)
{
    unsigned int j = 0;
    unsigned char x, y;

    for (y = y0; y <= y1; y++)
    {

        OLED_Set_Pos(x0, y);
        for (x = x0; x < x1; x++)
        {
            if (len < j)
                return;
            OLED_Write_Dat(BMP[j++]);
        }
    }
}

/***********************************************
    函数名称：OLED_TEST()
    功能介绍：OLED测试程序
    函数参数：无
    返回值：	无
 ***********************************************/
void OLED_TEST(void)
{
	OLED_CLS();
	OLED_P8x16Str(0,0,"hello");
}


void OLED_P16x16Ch(unsigned char x, unsigned char y, unsigned char N, const unsigned char *fontLibrary)
{
    unsigned char wm = 0;
    unsigned int adder = 32 * N;
    OLED_Set_Pos(x, y);
    for (wm = 0; wm < 16; wm++)
    {
        OLED_Write_Dat(fontLibrary[adder]);
        adder += 1;
    }
    OLED_Set_Pos(x, y + 1);
    for (wm = 0; wm < 16; wm++)
    {
        OLED_Write_Dat(fontLibrary[adder]);
        adder += 1;
    }
}
