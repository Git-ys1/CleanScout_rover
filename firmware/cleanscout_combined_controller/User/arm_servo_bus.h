#ifndef ARM_SERVO_BUS_H
#define ARM_SERVO_BUS_H

#include <stdint.h>

void arm_servo_bus_init(uint32_t baudrate);
int arm_servo_bus_send_frame(const char *frame);
int arm_servo_bus_poll_response(char *frame, uint16_t frame_size, uint16_t *length, uint32_t now_ms);
uint8_t arm_servo_bus_is_tx_idle(void);
uint32_t arm_servo_bus_rx_overflow_count(void);
uint32_t arm_servo_bus_tx_overflow_count(void);
uint32_t arm_servo_bus_bad_frame_count(void);
uint32_t arm_servo_bus_rx_byte_count(void);
uint32_t arm_servo_bus_tx_byte_count(void);
uint8_t arm_servo_bus_copy_last_rx(uint8_t *output, uint8_t output_size);

#endif
