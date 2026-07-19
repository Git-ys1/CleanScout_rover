#ifndef BOARD_RESOURCE_MAP_H
#define BOARD_RESOURCE_MAP_H

#include "stm32f10x.h"
#include <stdint.h>

#define CSR_COMBINED_FW_VERSION          "1.0.0"
#define CSR_MOTION_PROTOCOL_VERSION      "MOTION_V1"
#define CSR_ARM_PROTOCOL_VERSION         "ARM_V2"

#define CSR_MOTION_BAUDRATE              115200UL
#define CSR_ARM_HOST_BAUDRATE            115200UL
#define CSR_ARM_BUS_BAUDRATE             115200UL

#define CSR_ARM_SESSION_TIMEOUT_MS       400UL
#define CSR_ARM_FRAME_TIMEOUT_MS         100UL
#define CSR_ARM_SERVO_MIN_PWM            500U
#define CSR_ARM_SERVO_MAX_PWM            2490U
#define CSR_ARM_SERVO_COUNT              6U

/*
 * 合并固件资源真值：
 * USART2 PA2/PA3 只服务树莓派底盘协议；
 * USART3 PB10/PB11 只服务香橙派机械臂协议；
 * UART5 PC12 使用芯片半双工模式，只连接总线舵机。
 *
 * 机械臂旧工程的 TIM7 本地 PWM 不进入本工程。其 PA8、PA9、PB11
 * 分别与底盘方向、USART1、USART3 冲突，且双后端镜像会重复执行动作。
 */
void board_resource_map_init(void);

#endif
