#ifndef SAFETY_SUPERVISOR_H
#define SAFETY_SUPERVISOR_H

#include <stdint.h>

void safety_supervisor_init(uint32_t now_ms);
void safety_supervisor_tick(uint32_t now_ms);
void safety_supervisor_latch_estop(uint32_t now_ms);
uint8_t safety_supervisor_try_clear_estop(uint32_t now_ms);
uint8_t safety_supervisor_estop_latched(void);

void safety_supervisor_enable_arm_v2(uint32_t now_ms);
void safety_supervisor_note_arm_activity(uint32_t now_ms);
uint8_t safety_supervisor_arm_v2_active(void);

void safety_supervisor_monitor_domains(void);
uint32_t safety_supervisor_risk_event_count(void);
uint32_t safety_supervisor_arm_watchdog_count(void);

#endif
