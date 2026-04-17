# OpenRF1 控制板开发速查（基于《OpenRF1 控制板开发指导手册》2.2 与电机原理图/网表整理）

> 说明  
> 1. 本文主要为了后续开发查表使用。  
> 2. “2.2 板载资源与接口”中的“说明x”标记在当前 PDF 中未看到完整展开说明，下面先保留原标记。  
> 3. 电机接口部分，**原理图 + 你上传的网表**比总览表更有最终接线价值，因此电机/编码器结论以原理图和网表核对结果为准。

---

## 1. 控制板核心信息

- 主控：STM32F103RCT6
- 板载接口：4 路编码器电机、6 路 PWM 舵机、4 路总线接口、IIC、UART、USB、SWD、PS2、循迹、传感器等
- 电机部分：4 路 AT8236 驱动，每路编码器需要 2 路定时器输入采集

---

## 2.2 板载资源与接口（整理版）

| 编号 | 引脚名称 | 主功能 | 默认复用 | 重定义/重映射 | 备注 |
|---|---|---|---|---|---|
| 1 | VBAT | VBAT | — | — | 说明1 |
| 2 | PC13-TAMPER-RTC | PC13 | TAMPER-RTC | — | 说明3 |
| 3 | PC14-OSC32_IN | PC14 | OSC32_IN | — | 说明3 |
| 4 | PC15-OSC32_OUT | PC15 | OSC32_OUT | — | 说明3 |
| 5 | OSC_IN | OSC_IN | — | CAN_RX | 晶振 |
| 6 | OSC_OUT | OSC_OUT | — | CAN_TX | 晶振 |
| 7 | NRST | NRST | — | — | 复位 |
| 8 | PC0 | PC0 | ADC123_IN10 | — | ADC |
| 9 | PC1 | PC1 | ADC123_IN11 | — | ADC |
| 10 | PC2 | PC2 | ADC123_IN12 | — | ADC |
| 11 | PC3 | PC3 | ADC123_IN13 | — | ADC |
| 12 | VSSA | VSSA | — | — | 模拟地 |
| 13 | VDDA | VDDA | — | — | 模拟电 |
| 14 | PA0-WKUP | PA0 | WKUP / USART2_CTS / ADC123_IN0 / TIM2_CH1_ETR / TIM5_CH1 / TIM8_ETR | — | 说明4/5/6 |
| 15 | PA1 | PA1 | USART2_RTS / ADC123_IN1 / TIM2_CH2 / TIM5_CH2 | — | — |
| 16 | PA2 | PA2 | USART2_TX / ADC123_IN2 / TIM2_CH3 / TIM5_CH3 | — | — |
| 17 | PA3 | PA3 | USART2_RX / ADC123_IN3 / TIM2_CH4 / TIM5_CH4 | — | — |
| 18 | VSS_4 | VSS_4 | — | — | 数字地 |
| 19 | VDD_4 | VDD_4 | — | — | 数字电 |
| 20 | PA4 | PA4 | USART2_CK / ADC12_IN4 / SPI1_NSS / DAC_OUT1 | — | — |
| 21 | PA5 | PA5 | ADC12_IN5 / SPI1_SCK / DAC_OUT2 | — | — |
| 22 | PA6 | PA6 | ADC12_IN6 / TIM3_CH1 / TIM8_BKIN / SPI1_MISO | TIM1_BKIN | — |
| 23 | PA7 | PA7 | ADC12_IN7 / TIM3_CH2 / TIM8_CH1N / SPI1_MOSI | TIM1_CH1N | — |
| 24 | PC4 | PC4 | ADC12_IN14 | — | — |
| 25 | PC5 | PC5 | ADC12_IN15 | — | — |
| 26 | PB0 | PB0 | ADC12_IN8 / TIM3_CH3 / TIM8_CH2N | TIM1_CH2N | — |
| 27 | PB1 | PB1 | ADC12_IN9 / TIM3_CH4 / TIM8_CH3N | TIM1_CH3N | — |
| 28 | PB2 | PB2 | PB2 / BOOT1 | — | — |
| 29 | PB10 | PB10 | USART3_TX / I2C2_SCL | TIM2_CH3 | — |
| 30 | PB11 | PB11 | USART3_RX / I2C2_SDA | TIM2_CH4 | — |
| 31 | VSS_1 | VSS_1 | — | — | 数字地 |
| 32 | VDD_1 | VDD_1 | — | — | 数字电 |
| 33 | PB12 | PB12 | USART3_CK / TIM1_BKIN / SPI2_NSS / I2C2_SMBA / I2S2_WS | — | 说明7 |
| 34 | PB13 | PB13 | USART3_CTS / TIM1_CH1N / SPI2_SCK / I2S2_CK | — | — |
| 35 | PB14 | PB14 | USART3_RTS / TIM1_CH2N / SPI2_MISO | — | — |
| 36 | PB15 | PB15 | TIM1_CH3N / SPI2_MOSI / I2S2_SD | — | — |
| 37 | PC6 | PC6 | I2S2_MCK / TIM8_CH1 / SDIO_D6 | TIM3_CH1 | 说明8 |
| 38 | PC7 | PC7 | I2S3_MCK / TIM8_CH2 / SDIO_D7 | TIM3_CH2 | — |
| 39 | PC8 | PC8 | TIM8_CH3 / SDIO_D0 | TIM3_CH3 | — |
| 40 | PC9 | PC9 | USART1_CK / TIM8_CH4 / SDIO_D1 | TIM3_CH4 | — |
| 41 | PA8 | PA8 | USART1_CK / TIM1_CH1 / MCO | — | — |
| 42 | PA9 | PA9 | USART1_TX / TIM1_CH2 | — | — |
| 43 | PA10 | PA10 | USART1_RX / TIM1_CH3 | — | — |
| 44 | PA11 | PA11 | USART1_CTS / TIM1_CH4 / USBDM / CAN_RX | — | — |
| 45 | PA12 | PA12 | USART1_RTS / TIM1_ETR / USBDP / CAN_TX | — | — |
| 46 | PA13 | PA13 | JTMS / SWDIO | PA13 | 调试 |
| 47 | VSS_2 | VSS_2 | — | — | 数字地 |
| 48 | VDD_2 | VDD_2 | — | — | 数字电 |
| 49 | PA14 | PA14 | JTCK / SWCLK | PA14 | 调试 |
| 50 | PA15 | PA15 | JTDI / SPI3_NSS / I2S3_WS | TIM2_CH1_ETR / SPI1_NSS | — |
| 51 | PC10 | PC10 | UART4_TX / SDIO_D2 | USART3_TX | — |
| 52 | PC11 | PC11 | UART4_RX / SDIO_D3 | USART3_RX | — |
| 53 | PC12 | PC12 | UART5_TX / SDIO_CK | USART3_CK | — |
| 54 | PD2 | PD2 | UART5_RX / TIM3_ETR / SDIO_CMD | PB3 | — |
| 55 | PB3 | PB3 | JTDO / SPI3_SCK / I2S3_CK | TIM2_CH2 / SPI1_SCK / TRACESWO | — |
| 56 | PB4 | PB4 | NJTRST / SPI3_MISO | TIM3_CH1 / SPI1_MISO | — |
| 57 | PB5 | PB5 | SPI3_MOSI / I2C1_SMBA / I2S3_SD | TIM3_CH2 / SPI1_MOSI | — |
| 58 | PB6 | PB6 | TIM4_CH1 / I2C1_SCL | USART1_TX | — |
| 59 | PB7 | PB7 | TIM4_CH2 / I2C1_SDA | USART1_RX | — |
| 60 | BOOT0 | BOOT0 | — | — | 启动配置 |
| 61 | PB8 | PB8 | TIM4_CH3 / SDIO_D4 | I2C1_SCL / CAN_RX | — |
| 62 | PB9 | PB9 | TIM4_CH4 / SDIO_D5 | I2C1_SDA / CAN_TX | — |
| 63 | VSS_3 | VSS_3 | — | — | 数字地 |
| 64 | VDD_3 | VDD_3 | — | — | 数字电 |

---

## 3. 开发最常用功能速查

### 3.1 调试/下载
- SWDIO：PA13
- SWCLK：PA14
- NRST：NRST

### 3.2 板载 LED / 按键 / IIC / 传感器 / 循迹
- LED：PC13（手册 2.3.11）
- 用户按键：PB2（手册 2.3.10）
- 软件 IIC：PB1(SCL)、PC3(SDA)（手册 6.3）
- 传感器接口：PA5_TRIG、PA4_ECHO（手册 2.3.12）
- 4 路循迹：X1=PC4、X2=PC5、X3=PB0、X4=PC14（按新原理图更正；旧 `PB10` 记录判定为错误，不再作为循迹口真值）

### 3.3 编码器/电机相关高频关注引脚
- TIM5：PA0 / PA1
- TIM3：PA6 / PA7（也可映射到 PB4 / PB5 或 PC6 / PC7）
- TIM2：PA15 / PB3（重映射后）
- TIM4：PB6 / PB7
- TIM8 PWM 组：PC6 / PC7 / PC8 / PC9

---

## 4. 四路编码器电机接口最终接线结论（按原理图 + 网表核对）

## 4.1 先说结论：6 线接口定义

每个电机口 CN1~CN4 都是 **6Pin**，从原理图编号 **1 → 6** 排列，功能如下：

| 接口脚位 | 功能 | 说明 |
|---|---|---|
| 1 | 电机线 M_A | 接 AT8236 输出端，**不是固定“正极”**，方向由驱动决定 |
| 2 | 编码器电源 +5V | 给霍尔编码器供电 |
| 3 | 编码器 A 相 | 进 MCU 定时器 CH1 |
| 4 | 编码器 B 相 | 进 MCU 定时器 CH2 |
| 5 | 编码器 GND | 编码器地 |
| 6 | 电机线 M_B | 接 AT8236 另一输出端，**不是固定“负极”** |

> 重点：  
> 对这块板来说，电机两根粗线本质上是 **H 桥两端输出**，不是永远固定的“正负极”。  
> **交换 1/6 两根线，或改变 IN1/IN2 控制逻辑，都会改变转向。**

---

## 4.2 四路接口逐路对应关系

### 电机接口 CN1（第1路）
| CN1 脚位 | 板内连接 | 说明 |
|---|---|---|
| CN1.1 | U2 输出端（AT8236 电机端） | 电机线 M_A |
| CN1.2 | VCC_5V | 编码器 +5V |
| CN1.3 | PA0 / TIM5_CH1 | 编码器 A 相输入 |
| CN1.4 | PA1 / TIM5_CH2 | 编码器 B 相输入 |
| CN1.5 | GND | 编码器地 |
| CN1.6 | U2 另一输出端 | 电机线 M_B |

驱动控制：
- U2.IN2 ← PC6 / TIM8_CH1
- U2.IN1 ← PA8（网表名 CH1IO）
- U2.VREF ← +3V3
- U2.VM ← VIN
- U2.GND/EP ← PGND

---

### 电机接口 CN2（第2路）
| CN2 脚位 | 板内连接 | 说明 |
|---|---|---|
| CN2.1 | U3 输出端（AT8236 电机端） | 电机线 M_A |
| CN2.2 | VCC_5V | 编码器 +5V |
| CN2.3 | PA6 / TIM3_CH1 | 编码器 A 相输入 |
| CN2.4 | PA7 / TIM3_CH2 | 编码器 B 相输入 |
| CN2.5 | GND | 编码器地 |
| CN2.6 | U3 另一输出端 | 电机线 M_B |

驱动控制：
- U3.IN2 ← PC7 / TIM8_CH2
- U3.IN1 ← PA11（网表名 CH2IO）
- U3.VREF ← +3V3
- U3.VM ← VIN
- U3.GND/EP ← PGND

---

### 电机接口 CN3（第3路）
| CN3 脚位 | 板内连接 | 说明 |
|---|---|---|
| CN3.1 | U4 输出端（AT8236 电机端） | 电机线 M_A |
| CN3.2 | VCC_5V | 编码器 +5V |
| CN3.3 | PA15 / TIM2_CH1 | 编码器 A 相输入 |
| CN3.4 | PB3 / TIM2_CH2 | 编码器 B 相输入 |
| CN3.5 | GND | 编码器地 |
| CN3.6 | U4 另一输出端 | 电机线 M_B |

驱动控制：
- U4.IN2 ← PC8 / TIM8_CH3
- U4.IN1 ← PA12（网表名 CH3IO）
- U4.VREF ← +3V3
- U4.VM ← VIN
- U4.GND/EP ← PGND

> 注意：  
> 这一组编码器口用的是 **TIM2 重映射后的 PA15/PB3** 组合，不是 TIM2 默认的 PA0/PA1。

---

### 电机接口 CN4（第4路）
| CN4 脚位 | 板内连接 | 说明 |
|---|---|---|
| CN4.1 | U5 输出端（AT8236 电机端） | 电机线 M_A |
| CN4.2 | VCC_5V | 编码器 +5V |
| CN4.3 | PB6 / TIM4_CH1 | 编码器 A 相输入 |
| CN4.4 | PB7 / TIM4_CH2 | 编码器 B 相输入 |
| CN4.5 | GND | 编码器地 |
| CN4.6 | U5 另一输出端 | 电机线 M_B |

驱动控制：
- U5.IN2 ← PC9 / TIM8_CH4
- U5.IN1 ← PC10（网表名 CH4IO）
- U5.VREF ← +3V3
- U5.VM ← VIN
- U5.GND/EP ← PGND

---

## 4.3 四路编码器资源分配总表

| 电机口 | 编码器 A | 编码器 B | 采用定时器 | 驱动 PWM/控制线1 | 驱动控制线2 |
|---|---|---|---|---|---|
| CN1 | PA0 / TIM5_CH1 | PA1 / TIM5_CH2 | TIM5 | PC6 / TIM8_CH1 | PA8 |
| CN2 | PA6 / TIM3_CH1 | PA7 / TIM3_CH2 | TIM3 | PC7 / TIM8_CH2 | PA11 |
| CN3 | PA15 / TIM2_CH1 | PB3 / TIM2_CH2 | TIM2（重映射） | PC8 / TIM8_CH3 | PA12 |
| CN4 | PB6 / TIM4_CH1 | PB7 / TIM4_CH2 | TIM4 | PC9 / TIM8_CH4 | PC10 |

---

## 5. 这套“编码器电机”到底是怎么实现编码的？

## 5.1 硬件层流程

1. **电机本体 6 线引出**
   - 2 根接直流电机
   - 2 根给霍尔编码器供电（+5V/GND）
   - 2 根输出编码器 A/B 正交脉冲

2. **电机两根动力线进入 AT8236**
   - 板上每路用 1 颗 AT8236 做驱动
   - AT8236 的 VM 接 VIN，说明电机供电直接来自板子的电机电源母线
   - IN1 / IN2 由 MCU 控制，用于正反转 / 调速

3. **A/B 两相信号直接进 STM32 定时器输入通道**
   - 第1路进 TIM5_CH1/CH2
   - 第2路进 TIM3_CH1/CH2
   - 第3路进 TIM2_CH1/CH2（重映射）
   - 第4路进 TIM4_CH1/CH2

4. **定时器工作在 Encoder Interface Mode**
   - STM32 硬件定时器直接对 A/B 正交脉冲计数
   - 硬件自动判断方向，计数器可加可减
   - 计数值可表示位置，周期采样后可算速度

---

## 5.2 STM32 里“编码器模式”本质

STM32F103 的通用定时器 TIM2/TIM3/TIM4/TIM5 都支持 **增量式编码器接口模式**。  
在这种模式下：

- TI1、TI2 两路输入分别接编码器 A/B
- 定时器根据 A/B 相位关系自动判断转向
- 计数器在 0~ARR 之间增减计数
- 软件只需要读 CNT，就能得到位置变化
- 周期性读 CNT 差值，就能得到速度

也就是说，这块板 **不是用外部中断手搓计数**，而是直接吃 STM32 的定时器编码器硬件功能。

---

## 5.3 板上控制链路

完整控制链路可以写成：

**目标速度**  
→ PID 计算  
→ 生成驱动输出（PWM / 方向）  
→ AT8236 驱动电机  
→ 电机转动  
→ 霍尔编码器输出 A/B 脉冲  
→ TIM2/TIM3/TIM4/TIM5 编码器模式计数  
→ 软件读取计数/速度  
→ 回到 PID 闭环修正

这也和手册第 6.10 节描述一致：  
先初始化 `Encoder_Init_TIM2/3/4/5`，把定时器配置成编码器接口模式，再进行速度检测与 PID 闭环。

---

## 5.4 一个容易混淆的点

### 为什么 2.2 表里 PC6~PC9 看起来也和 TIM3/TIM8 有关，但真正编码器口却不是全都接在 PC6~PC9 上？

因为：

- **2.2 表**列的是 **MCU 管脚自身具备哪些复用能力**
- **实际电机接口接线**要看 **板级原理图和网表**
- 在这块板上：
  - **PC6~PC9 实际被拿去做 4 路电机驱动输入的一组高速控制线**
  - **编码器 A/B 则分别走 TIM5 / TIM3 / TIM2(重映射) / TIM4 这四组通道**

所以，开发时一定要区分：

- **“芯片能干什么”**（2.2 资源表）
- **“板子实际上把它接到了哪里”**（原理图/网表）

---

## 6. 电机驱动实现方式：我能确定到什么程度？

### 我可以确定的部分
- 每路电机都由 1 颗 AT8236 驱动
- 每路编码器 A/B 都接到 1 个定时器的 CH1/CH2
- `PC6/7/8/9` 这一组明显是 4 路驱动中的高频控制线，分别对应 `TIM8_CH1~CH4`
- 手册明确说 `IN1`、`IN2` 可用于控制速度/方向，编码器用于 PID 闭环

### 我不能百分之百替你瞎说的部分
仅凭当前手册+原理图+网表，还**不能 100% 断言官方例程一定是“双 PWM 驱动”还是“PWM + GPIO 方向控制”**。  
因为网表只说明：
- 一路输入接到了 TIM8_CHx
- 另一路输入接到了普通 MCU 引脚（也可能被软件配置为普通 GPIO 输出）

所以更稳妥的工程判断是：

- **IN2 这一组大概率承担 PWM 调速主输出**
- **IN1 这一组大概率承担方向/使能，或参与刹车控制**
- 真正的软件策略，最好再去看官方源码里 `motor.c / encoder.c / pwm.c` 之类文件确认

---

## 7. 给你后续写代码时的直接建议

### 7.1 编码器初始化建议
- Motor1 → TIM5 编码器模式
- Motor2 → TIM3 编码器模式
- Motor3 → TIM2 编码器模式（记得开重映射）
- Motor4 → TIM4 编码器模式

### 7.2 驱动输出建议
- PWM 输出优先看 TIM8_CH1~CH4：PC6、PC7、PC8、PC9
- 方向/使能控制看：PA8、PA11、PA12、PC10

### 7.3 若你要自己重写底层
最小可行分层建议：

- `bsp_motor_hw.c`：AT8236 驱动输出
- `bsp_encoder.c`：TIM2/3/4/5 编码器接口
- `motor_ctrl.c`：速度闭环/PID
- `robot_chassis.c`：四轮解算

---

## 8. 最终一句话版结论

这块 OpenRF1 的 4 路编码电机方案，本质上是：

- **AT8236 负责出力驱动**
- **TIM8_CH1~4 这组线负责 4 路驱动 PWM**
- **TIM5 / TIM3 / TIM2(重映射) / TIM4 分别负责 4 路编码器 A/B 计数**
- **编码器不是外部中断软计数，而是 STM32 定时器编码器模式硬件计数**
