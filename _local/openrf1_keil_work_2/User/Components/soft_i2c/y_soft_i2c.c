#include "soft_i2c/y_soft_i2c.h"
#include "y_delay/y_delay.h"

#define I2C_TIMEOUT_TIMES 100 // 超时倍数

void soft_i2c_gpio_init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    RCC_APB2PeriphClockCmd(SCL_GPIO_CLK | SDA_GPIO_CLK, ENABLE); /* 使能端口时钟 */

    GPIO_InitStructure.GPIO_Pin = SCL_Pin;			// 外接I2C
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_OD;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;	// 速度
    GPIO_Init(SCL_GPIO_Port, &GPIO_InitStructure);	// 对选中管脚初始化
	
	GPIO_InitStructure.GPIO_Pin = SDA_Pin;			// 外接I2C
    GPIO_Init(SDA_GPIO_Port, &GPIO_InitStructure);	// 对选中管脚初始化
	
}

// 延时 用于等待应答时的超时判断 移植时需修改
void i2c_delay() // 每步的间隔 用于等待电平稳定和控制通讯速率
{
    unsigned char i;
    i = 1;
    while (--i)
    {

    }
}

// SCL拉高 移植时需修改
void I2C_SCL_H(void)
{
    GPIO_SetBits(SCL_GPIO_Port, SCL_Pin);
}

// SCL拉低 移植时需修改
void I2C_SCL_L(void)
{
    GPIO_ResetBits(SCL_GPIO_Port, SCL_Pin);
}

// SDA拉高 移植时需修改
void I2C_SDA_H(void)
{
    GPIO_SetBits(SDA_GPIO_Port, SDA_Pin);
}

// SDA拉低 移植时需修改
void I2C_SDA_L(void)
{
    GPIO_ResetBits(SDA_GPIO_Port, SDA_Pin);
}

// 读取SDA 移植时需修改
uint8_t I2C_SDA_Read(void)
{
    return GPIO_ReadInputDataBit(SDA_GPIO_Port, SDA_Pin);
}

/*******************************************************************************
 * 函 数 名       : i2c_start
 * 函数功能		 : 产生I2C起始信号
 * 输    入       : 无
 * 输    出    	 : 无
 *******************************************************************************/
void i2c_start(void)
{
    I2C_SDA_H();
    I2C_SCL_H();
    i2c_delay();

    I2C_SDA_L(); // 当SCL为高电平时，SDA由高变为低
    i2c_delay();
    I2C_SCL_L(); // 钳住I2C总线，准备发送或接收数据
}

/*******************************************************************************
 * 函 数 名         : i2c_stop
 * 函数功能		   : 产生I2C停止信号
 * 输    入         : 无
 * 输    出         : 无
 *******************************************************************************/
void i2c_stop(void)
{
    I2C_SDA_L();
    I2C_SCL_H();
    i2c_delay();

    I2C_SDA_H(); // 当SCL为高电平时，SDA由低变为高
    i2c_delay();
}

/*******************************************************************************
 * 函 数 名         : i2c_ack
 * 函数功能		   : 产生ACK应答
 * 输    入         : 无
 * 输    出         : 无
 *******************************************************************************/
void i2c_ack(void)
{
    I2C_SCL_L();
    I2C_SDA_L(); // SDA为低电平
    i2c_delay();

    I2C_SCL_H();
    i2c_delay();
    I2C_SCL_L();
    I2C_SDA_H();
}

/*******************************************************************************
 * 函 数 名         : i2c_nack
 * 函数功能		   : 产生NACK非应答
 * 输    入         : 无
 * 输    出         : 无
 *******************************************************************************/
void i2c_nack(void)
{
    I2C_SCL_L();
    I2C_SDA_H(); // SDA为高电平
    i2c_delay();

    I2C_SCL_H();
    i2c_delay();
    I2C_SCL_L();
}

/*******************************************************************************
* 函 数 名         : i2c_wait_ack
* 函数功能		   : 等待应答信号到来
* 输    入         : 无
* 输    出         : 1，接收应答失败
                     0，接收应答成功
*******************************************************************************/
uint8_t i2c_wait_ack(void)
{
    uint16_t time_temp = 0;

    I2C_SCL_H();
    I2C_SDA_H();
    i2c_delay();
    while (I2C_SDA_Read()) // 等待SDA为低电平
    {
        time_temp++;
        i2c_delay();
        if (time_temp > I2C_TIMEOUT_TIMES) // 超时则强制结束I2C通信
        {
            i2c_stop();
            return 1;
        }
    }
    I2C_SCL_L();
    return 0;
}

/*******************************************************************************
 * 函 数 名         : i2c_write_byte
 * 函数功能		   : I2C发送一个字节
 * 输    入         : dat：发送一个字节
 * 输    出         : 无
 *******************************************************************************/
void i2c_write_byte(uint8_t dat)
{
    uint8_t i = 0;

    I2C_SCL_L();
    for (i = 0; i < 8; i++) // 循环8次将一个字节传出，先传高再传低位
    {
        if ((dat & 0x80) > 0)
            I2C_SDA_H();
        else
            I2C_SDA_L();
        dat <<= 1;
        i2c_delay();
        I2C_SCL_H();
        i2c_delay();
        I2C_SCL_L();
        i2c_delay();
    }
}

/*******************************************************************************
 * 函 数 名         : i2c_read_byte
 * 函数功能		   : I2C读一个字节
 * 输    入         : ack = 1时，发送ACK，ack = 0，发送nACK
 * 输    出         : 应答或非应答
 *******************************************************************************/
uint8_t i2c_read_byte(uint8_t ack)
{
    uint8_t i = 0, receive = 0;

    for (i = 0; i < 8; i++) // 循环8次将一个字节读出，先读高再传低位
    {
        I2C_SCL_L();
        i2c_delay();
        I2C_SCL_H();
        receive <<= 1;
        if (I2C_SDA_Read())
            receive++;
        i2c_delay();
    }
    if (!ack)
        i2c_nack();
    else
        i2c_ack();

    return receive;
}
