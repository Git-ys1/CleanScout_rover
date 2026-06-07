#ifndef _MAIN_H_
#define _MAIN_H_

/* C 标准库：协议解析、字符串拼装和固定宽度整数。 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/* STM32F103RCT6 CMSIS 与精简 SPL 配置。 */
#include "stm32f10x.h"
#include "stm32f10x_conf.h"

/* OpenRF1 自写底盘模块。 */
#include "csr_board_map.h"
#include "csr_motor_drv.h"
#include "csr_encoder_drv.h"
#include "csr_proto.h"

#endif
