#ifndef APP_CHASSIS_H
#define APP_CHASSIS_H

#include "main.h"

typedef struct
{
    float target[4];
    uint32_t last_command_ms;
    uint16_t timeout_ms;
} csr_chassis_state_t;

void app_chassis_init(void);
void app_chassis_set_targets(float a, float b, float c, float d);
void app_chassis_stop(void);
void app_chassis_tick_20ms(void);
const csr_chassis_state_t *app_chassis_get_state(void);

#endif
