#ifndef APP_MOTOR_H
#define APP_MOTOR_H

#include "main.h"

#define CSR_WHEEL_PI                3.14159265358979f
#define CSR_WHEEL_CONTROL_HZ        50.0f
#define CSR_WHEEL_CONTROL_DT_S      (1.0f / CSR_WHEEL_CONTROL_HZ)
#define CSR_WHEEL_RESOLUTION        1560.0f
#define CSR_WHEEL_DIAMETER_M        0.080f
#define CSR_WHEEL_COUNT_TO_MPS      ((CSR_WHEEL_PI * CSR_WHEEL_DIAMETER_M * CSR_WHEEL_CONTROL_HZ) / CSR_WHEEL_RESOLUTION)

/*
 * App-layer wheel order frozen for OpenRF1:
 *   A = left-front  = M3
 *   B = right-front = M2
 *   C = left-rear   = M4
 *   D = right-rear  = M1
 */

void app_motor_init(void);
void app_motor_run(void);
void motor_speed_set(float A, float B, float C, float D);

#endif
