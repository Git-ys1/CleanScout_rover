#ifndef _SOFT_I2C_H_
#define _SOFT_I2C_H_
#include <stdio.h>

#include "stm32f10x_conf.h"
#include "stm32f10x.h"


/*******iic IO口映射表*******/
#define SCL_Pin 				GPIO_Pin_1           //IIC时钟引脚
#define SCL_GPIO_Port 			GPIOB
#define SCL_GPIO_CLK 			RCC_APB2Periph_GPIOB 

#define SDA_Pin 				GPIO_Pin_3			//IIC数据引脚
#define SDA_GPIO_Port 			GPIOC
#define SDA_GPIO_CLK 			RCC_APB2Periph_GPIOC 


void soft_i2c_gpio_init(void);//iic引脚初始化配置

// I2C所有操作函数
void i2c_start(void);       //发送I2C开始信号
void i2c_stop(void);        //发送I2C停止信号
uint8_t i2c_wait_ack(void); // I2C等待ACK信号
void i2c_ack(void);         // I2C发送ACK信号
void i2c_nack(void);        // I2C不发送ACK信号

void i2c_write_byte(uint8_t txd);   // I2C发送一个字节
uint8_t i2c_read_byte(uint8_t ack); // I2C读取一个字节

#endif
