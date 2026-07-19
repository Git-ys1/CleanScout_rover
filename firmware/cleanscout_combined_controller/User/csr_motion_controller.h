#ifndef CSR_MOTION_CONTROLLER_H
#define CSR_MOTION_CONTROLLER_H

#include "csr_motion_link.h"

void csr_motion_controller_init(uint32_t now_ms);
void csr_motion_controller_handle(const csr_motion_command_t *command, uint32_t now_ms);
void csr_motion_controller_tick(void);
void csr_motion_controller_telemetry(void);
void csr_motion_controller_watchdog(uint32_t now_ms);
void csr_motion_controller_stop(void);
uint8_t csr_motion_controller_is_stopped(void);
uint8_t csr_motion_controller_is_moving(void);

#endif
