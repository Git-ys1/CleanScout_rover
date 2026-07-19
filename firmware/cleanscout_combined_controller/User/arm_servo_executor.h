#ifndef ARM_SERVO_EXECUTOR_H
#define ARM_SERVO_EXECUTOR_H

#include "arm_protocol.h"

typedef enum
{
    ARM_EXEC_OK = 0,
    ARM_EXEC_BUSY,
    ARM_EXEC_LINK_FULL
} arm_exec_result_t;

void arm_servo_executor_init(void);
arm_exec_result_t arm_servo_executor_submit(const arm_protocol_command_t *command, uint8_t enhanced_mode, uint32_t now_ms);
void arm_servo_executor_tick(uint32_t now_ms);
void arm_servo_executor_stop_all(uint32_t now_ms);
uint8_t arm_servo_executor_is_idle(uint32_t now_ms);
uint8_t arm_servo_executor_is_expanded(void);

#endif
