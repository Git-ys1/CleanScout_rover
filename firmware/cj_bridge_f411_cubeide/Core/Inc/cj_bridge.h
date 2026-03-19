#ifndef CJ_BRIDGE_H_
#define CJ_BRIDGE_H_

#include <stdint.h>

#include "cj_bridge_protocol.h"

typedef enum {
  CJ_BRIDGE_IDLE = 0,
  CJ_BRIDGE_WAIT_UNO_STOP_ACK,
  CJ_BRIDGE_WAIT_J_RESULT,
  CJ_BRIDGE_WAIT_UNO_RESUME_ACK,
  CJ_BRIDGE_FAULT
} cj_bridge_state_t;

typedef struct {
  uint32_t (*millis)(void);
  void (*send_uno_line)(const char *line);
  void (*send_j_bytes)(const uint8_t *bytes, uint8_t length);
  void (*log)(const char *message);
} cj_bridge_io_t;

typedef struct {
  cj_bridge_io_t io;
  cj_bridge_state_t state;
  uint32_t state_deadline_ms;
  uint8_t next_seq;
  uint8_t active_color;
  uint8_t last_j_seq;
  uint8_t last_j_type;
} cj_bridge_t;

void cj_bridge_init(cj_bridge_t *bridge, const cj_bridge_io_t *io);
void cj_bridge_tick(cj_bridge_t *bridge);
void cj_bridge_on_uno_line(cj_bridge_t *bridge, const char *line);
void cj_bridge_on_j_frame(cj_bridge_t *bridge, const cj_frame_t *frame);
const char *cj_bridge_state_name(cj_bridge_state_t state);

#endif