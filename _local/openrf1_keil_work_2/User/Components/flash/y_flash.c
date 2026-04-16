/****************************************************************************
 *	@笔者	：	Q
 *	@日期	：	2023年2月9日
 *	@所属	：	杭州友辉科技
 *	@功能	：	存放FLASH相关的函数
 *	@函数列表:
 *	1.	void led_init(void) -- 初始化LED信号灯
 ****************************************************************************/

#include "flash/y_flash.h"

SPI_InitTypeDef SPI_InitStructure;
GPIO_InitTypeDef GPIO_InitStructure;

/* 初始化SPI FLASH的IO口 */
void spi_flash_init(void)
{
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_12;       // SPI CS
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP; // 推挽输出
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOB, &GPIO_InitStructure);
    GPIO_SetBits(GPIOB, GPIO_Pin_12);

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_13 | GPIO_Pin_15;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP; // 复用推挽输出
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_14;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU; // 上拉输入
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    GPIO_SetBits(GPIOB, GPIO_Pin_13 | GPIO_Pin_15);

    RCC_APB1PeriphClockCmd(RCC_APB1Periph_SPI2, ENABLE);

    SPI_InitStructure.SPI_Direction = SPI_Direction_2Lines_FullDuplex;   // 设置SPI单向或者双向的数据模式:SPI设置为双线双向全双工
    SPI_InitStructure.SPI_Mode = SPI_Mode_Master;                        // 设置SPI工作模式:设置为主SPI
    SPI_InitStructure.SPI_DataSize = SPI_DataSize_8b;                    // 设置SPI的数据大小:SPI发送接收8位帧结构
    SPI_InitStructure.SPI_CPOL = SPI_CPOL_High;                          // 选择了串行时钟的稳态:时钟悬空高
    SPI_InitStructure.SPI_CPHA = SPI_CPHA_2Edge;                         // 数据捕获于第二个时钟沿
    SPI_InitStructure.SPI_NSS = SPI_NSS_Soft;                            // NSS信号由硬件（NSS管脚）还是软件（使用SSI位）管理:内部NSS信号有SSI位控制
    SPI_InitStructure.SPI_BaudRatePrescaler = SPI_BaudRatePrescaler_256; // 定义波特率预分频的值:波特率预分频值为256
    SPI_InitStructure.SPI_FirstBit = SPI_FirstBit_MSB;                   // 指定数据传输从MSB位还是LSB位开始:数据传输从MSB位开始
    SPI_InitStructure.SPI_CRCPolynomial = 7;                             // CRC值计算的多项式
    SPI_Init(SPI2, &SPI_InitStructure);                                  // 根据SPI_InitStruct中指定的参数初始化外设SPIx寄存器

    SPI_Cmd(SPI2, ENABLE); // 使能SPI外设

    spi_write_read(0xff);                   // 启动传输
    spi_set_speed(SPI_BaudRatePrescaler_16); // 设置高速
}

/***********************************************
    功能介绍：	SPI 速度设置函数
    函数参数：	SpeedSet:SPI_BaudRatePrescaler_2   2分频   (SPI 36M@sys 72M)
                        SPI_BaudRatePrescaler_8   8分频   (SPI 9M@sys 72M)
                        SPI_BaudRatePrescaler_16  16分频  (SPI 4.5M@sys 72M)
                        SPI_BaudRatePrescaler_256 256分频 (SPI 281.25K@sys 72M)
    返回值：	无
 ***********************************************/
void spi_set_speed(uint16_t SpeedSet)
{
    SPI_InitStructure.SPI_BaudRatePrescaler = SpeedSet;
    SPI_Init(SPI1, &SPI_InitStructure);
    SPI_Cmd(SPI1, ENABLE);
}

/***********************************************
    功能介绍：	SPI读写数据
    函数参数：	TxData 发送的数据
    返回值：	SPDAT 返回字节数据
 ***********************************************/
u8 spi_write_read(u8 TxData)
{
    u8 retry = 0;
    while (SPI_I2S_GetFlagStatus(SPI2, SPI_I2S_FLAG_TXE) == RESET) // 检查指定的SPI标志位设置与否:发送缓存空标志位
    {
        retry++;
        if (retry > 200)
            return 0;
    }
    SPI_I2S_SendData(SPI2, TxData); // 通过外设SPIx发送一个数据
    retry = 0;

    while (SPI_I2S_GetFlagStatus(SPI2, SPI_I2S_FLAG_RXNE) == RESET) // 检查指定的SPI标志位设置与否:接受缓存非空标志位
    {
        retry++;
        if (retry > 200)
            return 0;
    }
    return SPI_I2S_ReceiveData(SPI2); // 返回通过SPIx最近接收的数据
}

/***********************************************
    功能介绍：读取芯片ID
    函数参数：无
    返回值：  0XEF13,表示芯片型号为W25Q80
             0XEF14,表示芯片型号为W25Q16
             0XEF15,表示芯片型号为W25Q32
             0XEF16,表示芯片型号为W25Q64
 ***********************************************/
u16 spi_flash_read_id(void)
{
    u16 Temp = 0;
    SPI_FLASH_CS(0);
    spi_write_read(W25X_ManufactDeviceID); // 发送读取ID命令
    spi_write_read(0x00);
    spi_write_read(0x00);
    spi_write_read(0x00);
    Temp |= spi_write_read(0xFF) << 8;
    Temp |= spi_write_read(0xFF);
    SPI_FLASH_CS(1);
    return Temp;
}

/***********************************************
    功能介绍：	读SPI_FLASH的状态寄存器
    函数参数：	无
    返回值： BIT7  6   5   4   3   2   1   0
            SPR   RV  TB BP2 BP1 BP0 WEL BUSY
            SPR:默认0,状态寄存器保护位,配合WP使用
            TB,BP2,BP1,BP0:FLASH区域写保护设置
            WEL:写使能锁定
            BUSY:忙标记位(1,忙;0,空闲)
            默认:0x00
 ***********************************************/
u8 spi_flash_read_SR(void)
{
    u8 byte = 0;
    SPI_FLASH_CS(0);                    // 使能器件
    spi_write_read(W25X_ReadStatusReg); // 发送读取状态寄存器命令
    byte = spi_write_read(0Xff);        // 读取一个字节
    SPI_FLASH_CS(1);                    // 取消片选
    return byte;
}

/***********************************************
    功能介绍：	写SPI_FLASH的状态寄存器
    函数参数：	写入的SPI_FLASH的状态寄存器值
            BIT	7	6	5	4	3	2	1	0
                SPR	RV	TB	BP2	BP1	BP0	WEL	BUSY
                只有SPR,TB,BP2,BP1,BP0(bit 7,5,4,3,2)可以写
    返回值： 无
 ***********************************************/
void spi_flash_write_SR(u8 byte)
{
    SPI_FLASH_CS(0);                     // 使能器件
    spi_write_read(W25X_WriteStatusReg); // 发送写取状态寄存器命令
    spi_write_read(byte);                // 写入一个字节
    SPI_FLASH_CS(1);                     // 取消片选
}

/***********************************************
    功能介绍：	SPI_FLASH写使能，WEL置位
    函数参数：	无
    返回值：	无
 ***********************************************/
void spi_flash_write_enable(void)
{
    SPI_FLASH_CS(0);                  // 使能器件
    spi_write_read(W25X_WriteEnable); // 发送写使能
    SPI_FLASH_CS(1);                  // 取消片选
}

/***********************************************
    功能介绍：	SPI_FLASH写禁止，将WEL清零
    函数参数：	无
    返回值：	无
 ***********************************************/
void spi_flash_write_disable(void)
{
    SPI_FLASH_CS(0);                   // 使能器件
    spi_write_read(W25X_WriteDisable); // 发送写禁止指令
    SPI_FLASH_CS(1);                   // 取消片选
}

/***********************************************
    功能介绍：	SPI读取1个字节的数据
    函数参数：	ReadAddr       -开始读取的地址(24bit)
    返回值：		无
 ***********************************************/
char spi_flash_read_char(u32 readAddr)
{
    static char tmp;
    SPI_FLASH_CS(0);                        // 使能器件
    spi_write_read(W25X_ReadData);          // 发送读取命令
    spi_write_read((u8)((readAddr) >> 16)); // 发送24bit地址
    spi_write_read((u8)((readAddr) >> 8));
    spi_write_read((u8)(readAddr & 0xFF));
    tmp = spi_write_read(0XFF); // 读数
    SPI_FLASH_CS(1);
    return tmp;
}

/***********************************************
    功能介绍：	在指定地址开始读取指定长度的数据
    函数参数：	pBuffer        -数据存储区
               ReadAddr       -开始读取的地址(24bit)
               NumByteToRead  -要读取的字节数(最大65535)
    返回值：	无
 ***********************************************/
void spi_flash_read(u8 *pBuffer, u32 ReadAddr, u16 NumByteToRead)
{
    u16 i;
    SPI_FLASH_CS(0);                        // 使能器件
    spi_write_read(W25X_ReadData);          // 发送读取命令
    spi_write_read((u8)((ReadAddr) >> 16)); // 发送24bit地址
    spi_write_read((u8)((ReadAddr) >> 8));
    spi_write_read((u8)(ReadAddr & 0xFF));
    for (i = 0; i < NumByteToRead; i++)
    {
        pBuffer[i] = spi_write_read(0XFF); // 循环读数
    }
    SPI_FLASH_CS(1);
}

/***********************************************
    功能介绍：	 SPI写入1个字节的数据
    函数参数：	 tmp        		 -数据
                WriteAddr      -开始写入的地址(24bit)
    返回值：		无
 ***********************************************/
void spi_flash_write_char(char tmp, u32 WriteAddr)
{
    spi_flash_write_enable();
    SPI_FLASH_CS(0);                         // 使能器件
    spi_write_read(W25X_PageProgram);        // 发送写页命令
    spi_write_read((u8)((WriteAddr) >> 16)); // 发送24bit地址
    spi_write_read((u8)((WriteAddr) >> 8));
    spi_write_read((u8)WriteAddr);
    spi_write_read(tmp);   // 写数
    SPI_FLASH_CS(1);       // 取消片选
    spi_flash_wait_busy(); // 等待写入结束
    // uart1_send_str((u8 *)"Byte has been written.\r\n");
}

u8 W25Q_BUF[4096];
void SpiFlashWriteS(u8 *pBuffer, u32 WriteAddr, u16 NumByteToWrite)
{
    u32 secpos;
    u16 secoff;
    u16 secremain;
    u16 i;

    secpos = WriteAddr / 4096; // 扇区地址 0~511 for w25x16
    secoff = WriteAddr % 4096; // 在扇区..内的偏移
    secremain = 4096 - secoff; // 扇区剩余空间大小

    if (NumByteToWrite <= secremain)
        secremain = NumByteToWrite; // 不大于4096个字节
    while (1)
    {
        spi_flash_read(W25Q_BUF, secpos * 4096, 4096); // 读出整个扇区的内容
        for (i = 0; i < secremain; i++)              // 校验数据
        {
            if (W25Q_BUF[secoff + i] != 0XFF)
                break; // 需要擦除
        }
        if (i < secremain) // 需要擦除
        {
            spi_flash_erase_sector(secpos);    // 擦除这个扇区
            for (i = 0; i < secremain; i++) // 复制
            {
                W25Q_BUF[i + secoff] = pBuffer[i];
            }
            spi_flash_write_no_check(W25Q_BUF, secpos * 4096, 4096); // 写入整个扇区
        }
        else
        {
            spi_flash_write_no_check(pBuffer, WriteAddr, secremain); // 写已经擦除了的,直接写入扇区剩余区间.
        }
        if (NumByteToWrite == secremain)
            break; // 写入结束了
        else       // 写入未结束
        {
            secpos++;   // 扇区地址增1
            secoff = 0; // 偏移位置为0

            pBuffer += secremain;        // 指针偏移
            WriteAddr += secremain;      // 写地址偏移
            NumByteToWrite -= secremain; // 字节数递减
            if (NumByteToWrite > 4096)
                secremain = 4096; // 下一个扇区还是写不完
            else
                secremain = NumByteToWrite; // 下一个扇区可以写完了
        }
    }
}

/***********************************************
    功能介绍:   在指定地址开始写入指定长度的数据
    函数参数:	pBuffer        -数据存储区
               WriteAddr      -开始写入的地址(24bit)
               NumByteToWrite -要写入的字节数(最大65535)
    返回值：    无
 ***********************************************/
void spi_flash_write(u8 *pBuffer, u32 WriteAddr, u16 NumByteToWrite)
{
    u8 SpiFlash_BUF[4096];
    u32 sector = 0;
    u16 sectorremain;
    u16 i;

    sectorremain = 4096 - WriteAddr % 4096; // 单扇区剩余的字节数
    if (NumByteToWrite <= sectorremain)
        sectorremain = NumByteToWrite;
    while (1)
    {
        sector = WriteAddr >> 12; // 扇区地址
        spi_flash_read(SpiFlash_BUF, sector * 4096, 4096);
        for (i = 0; i < sectorremain; i++)
        {                                                   // 校验数据
            if (SpiFlash_BUF[WriteAddr % 4096 + i] != 0XFF) // 需要擦除
                break;
        }
        if (i < sectorremain)
        {                                   // 需要擦除
            spi_flash_erase_sector(sector); // 擦除这个扇区
            for (i = 0; i < sectorremain; i++)
            { // 复制
                SpiFlash_BUF[WriteAddr % 4096 + i] = pBuffer[i];
            }
            spi_flash_write_sector(SpiFlash_BUF, sector * 4096, 4096); // 写入整个扇区
        }
        else
            spi_flash_write_sector(pBuffer, WriteAddr, sectorremain);
        if (NumByteToWrite == sectorremain)
            break; // 写入结束了
        else
        {
            pBuffer += sectorremain;
            WriteAddr += sectorremain;
            NumByteToWrite -= sectorremain; // 减去已经写入了的字节数
            if (NumByteToWrite > 4096)
                sectorremain = 4096; // 一次可以写入4096个字节
            else
                sectorremain = NumByteToWrite; // 不够4096个字节了
        }
    }
}

/***********************************************
    功能介绍：SPI在一页内写入少于256个字节的数据
    函数参数：pBuffer        -数据存储区
             WriteAddr      -开始写入的地址(24bit)
             NumByteToWrite -要写入的字节数(最大256),该数不应该超过该页的剩余字节数
    返回值：		无
 ***********************************************/
void spi_flash_write_page(u8 *pBuffer, u32 WriteAddr, u16 NumByteToWrite)
{
    u16 i, pageremain;
    pageremain = 256 - WriteAddr % 256; // 单页剩余的字节数
    if (NumByteToWrite > pageremain)
    {
        NumByteToWrite = pageremain;
        // uart1_send_str((u8 *)"There are not enough writable bytes left in this page!\r\n");
    }
    spi_flash_write_enable();                // 写使能
    SPI_FLASH_CS(0);                         // 使能器件
    spi_write_read(W25X_PageProgram);        // 发送写页命令
    spi_write_read((u8)((WriteAddr) >> 16)); // 发送24bit地址
    spi_write_read((u8)((WriteAddr) >> 8));
    spi_write_read((u8)WriteAddr);
    for (i = 0; i < NumByteToWrite; i++)
    {
        spi_write_read(pBuffer[i]); // 循环写数
    }
    SPI_FLASH_CS(1);       // 取消片选
    spi_flash_wait_busy(); // 等待写入结束
    // uart1_send_int(NumByteToWrite);
    // uart1_send_str((u8 *)" bytes have been written.\r\n");
}

/***********************************************
    功能介绍:   SPI在一扇区内写入少于4096个字节的数据
    函数参数:   pBuffer        -数据存储区
                WriteAddr      -开始写入的地址(24bit)
                NumByteToWrite -要写入的字节数(最大4096),该数不应该超过该扇区的剩余字节数
    返回值:	无
 ***********************************************/
void spi_flash_write_sector(u8 *pBuffer, u32 WriteAddr, u16 NumByteToWrite)
{
    u16 sectorremain;
    sectorremain = 4096 - WriteAddr % 4096; // 单扇区剩余的字节数
    if (NumByteToWrite > sectorremain)
    {
        NumByteToWrite = sectorremain;
        // uart1_send_str((u8 *)"There are not enough writable bytes left in this sector!\r\n");
    }
    spi_flash_write_no_check(pBuffer, WriteAddr, NumByteToWrite);
}

/***********************************************
    功能介绍：	无检验写SPI_FLASH
    函数参数：	pBuffer        -数据存储区
                WriteAddr      -开始写入的地址(24bit)
                NumByteToWrite -要写入的字节数(最大65535 1块 16扇区 256页)
    返回值：		无
 ***********************************************/
void spi_flash_write_no_check(u8 *pBuffer, u32 WriteAddr, u16 NumByteToWrite)
{
    u16 pageremain;
    pageremain = 256 - WriteAddr % 256; // 单页剩余的字节数
    if (NumByteToWrite <= pageremain)
        pageremain = NumByteToWrite;
    while (1)
    {
        spi_flash_write_page(pBuffer, WriteAddr, pageremain);
        if (NumByteToWrite == pageremain)
            break; // 写入结束了
        else
        {
            pBuffer += pageremain;
            WriteAddr += pageremain;
            NumByteToWrite -= pageremain; // 减去已经写入了的字节数
            if (NumByteToWrite > 256)
                pageremain = 256; // 一次可以写入256个字节
            else
                pageremain = NumByteToWrite; // 不够256个字节了
        }
    }
}

/***********************************************
    功能介绍：	擦除一个扇区 最少150毫秒
    函数参数：	Dst_Addr  -扇区地址 (最大2047)
    返回值：	无
 ***********************************************/
void spi_flash_erase_sector(u32 Dst_Addr)
{
    Dst_Addr <<= 12;
    spi_flash_write_enable(); // SET WEL
    spi_flash_wait_busy();
    SPI_FLASH_CS(0);                        // 使能器件
    spi_write_read(W25X_SectorErase);       // 发送扇区擦除指令
    spi_write_read((u8)((Dst_Addr) >> 16)); // 发送24bit地址
    spi_write_read((u8)((Dst_Addr) >> 8));
    spi_write_read((u8)Dst_Addr);
    SPI_FLASH_CS(1);       // 取消片选
    spi_flash_wait_busy(); // 等待擦除完成
    // uart1_send_str((u8 *)"Sector has been erased.\r\n");
}

/***********************************************
    功能介绍：	擦除整个芯片
    函数参数：	无
    返回值：	无
 ***********************************************/
void spi_flash_erase_chip(void)
{
    spi_flash_write_enable(); // SET WEL
    spi_flash_wait_busy();
    SPI_FLASH_CS(0);                // 使能器件
    spi_write_read(W25X_ChipErase); // 发送芯片擦除命令
    SPI_FLASH_CS(1);                // 取消片选
    spi_flash_wait_busy();          // 等待芯片擦除结束
    // uart1_send_str((u8 *)"Chip has been erased.\r\n");
}

/***********************************************
    功能介绍：	等待空闲
    函数参数：	无
    返回值：	无
 ***********************************************/
void spi_flash_wait_busy(void)
{
    /* 等待BUSY位清空 */
    while ((spi_flash_read_SR() & 0x01) == 0x01)
        ;
}

/***********************************************
    功能介绍：	进入掉电模式
    函数参数：	无
    返回值：	无
 ***********************************************/
void spi_flash_power_down(void)
{
    SPI_FLASH_CS(0);                // 使能器件
    spi_write_read(W25X_PowerDown); // 发送掉电命令
    SPI_FLASH_CS(1);                // 取消片选
    delay_us(3);                    // 等待TPD
}

/***********************************************
    功能介绍：	唤醒
    函数参数：	无
    返回值：	无
 ***********************************************/
void spi_flash_wake_up(void)
{
    SPI_FLASH_CS(0);                       // 使能器件
    spi_write_read(W25X_ReleasePowerDown); // 发送唤醒指令
    SPI_FLASH_CS(1);                       // 取消片选
    delay_us(3);                           // 等待TRES1
}
