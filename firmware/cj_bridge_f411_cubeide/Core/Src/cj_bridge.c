#include "cj_bridge.h"

#include <stdbool.h>
#include <string.h>

#define CJ_UNO_ACK_TIMEOUT_MS 1000UL
#define CJ_J_LOCAL_TIMEOUT_MS 10000UL
#define CJ_J_WATCHDOG_TIMEOUT_MS 12000UL

static void log_line(cj_bridge_t *bridge, const char *line) {
  if (bridge->io.log != 0) {
    bridge->io.log(line);
  }
}

static void set_state(cj_bridge_t *bridge, cj_bridge_state_t state, uint32_t timeout_ms) {
  bridge->state = state;
  if (timeout_ms > 0UL) {
    bridge->state_deadline_ms = bridge->io.millis() + timeout_ms;
  } else {
    bridge->state_deadline_ms = 0UL;
  }
}

static void send_j_message(cj_bridge_t *bridge, uint8_t type, const uint8_t *payload, uint8_t len) {
  uint8_t buffer[CJ_PROTOCOL_MAX_FRAME_SIZE] = {0};
  uint8_t frame_len = cj_protocol_build_frame(bridge->next_seq++, type, payload, len, buffer, sizeof(buffer));
  if (frame_len > 0U && bridge->io.send_j_bytes != 0) {
    bridge->io.send_j_bytes(buffer, frame_len);
  }
}

static void send_j_ack(cj_bridge_t *bridge, uint8_t acked_seq, uint8_t acked_type) {
  uint8_t payload[2] = {acked_seq, acked_type};
  send_j_message(bridge, CJ_MSG_ACK, payload, sizeof(payload));
}

static void enter_fault(cj_bridge_t *bridge, const char *reason) {
  set_state(bridge, CJ_BRIDGE_FAULT, 0UL);
  log_line(bridge, reason);
}

void cj_bridge_init(cj_bridge_t *bridge, const cj_bridge_io_t *io) {
  memset(bridge, 0, sizeof(*bridge));
  bridge->io = *io;
  bridge->state = CJ_BRIDGE_IDLE;
  bridge->next_seq = 1U;
}

void cj_bridge_tick(cj_bridge_t *bridge) {
  uint32_t now = bridge->io.millis();

  if (bridge->state == CJ_BRIDGE_WAIT_UNO_STOP_ACK && bridge->state_deadline_ms > 0UL && now > bridge->state_deadline_ms) {
    enter_fault(bridge, "FAULT: UNO stop ack timeout");
    return;
  }

  if (bridge->state == CJ_BRIDGE_WAIT_J_RESULT && bridge->state_deadline_ms > 0UL && now > bridge->state_deadline_ms) {
    uint8_t reason = 0x01U;
    send_j_message(bridge, CJ_MSG_ABORT, &reason, 1U);
    if (bridge->io.send_uno_line != 0) {
      bridge->io.send_uno_line("RESUME_REQ");
    }
    set_state(bridge, CJ_BRIDGE_WAIT_UNO_RESUME_ACK, CJ_UNO_ACK_TIMEOUT_MS);
    log_line(bridge, "watchdog: J result timeout, forcing resume");
    return;
  }

  if (bridge->state == CJ_BRIDGE_WAIT_UNO_RESUME_ACK && bridge->state_deadline_ms > 0UL && now > bridge->state_deadline_ms) {
    enter_fault(bridge, "FAULT: UNO resume ack timeout");
  }
}

void cj_bridge_on_uno_line(cj_bridge_t *bridge, const char *line) {
  if (strcmp(line, "PING") == 0) {
    if (bridge->io.send_uno_line != 0) {
      bridge->io.send_uno_line("PONG");
    }
    return;
  }

  if (strcmp(line, "STOP_ACK") == 0 && bridge->state == CJ_BRIDGE_WAIT_UNO_STOP_ACK) {
    uint8_t timeout_payload[2] = {
      (uint8_t)(CJ_J_LOCAL_TIMEOUT_MS & 0xFFU),
      (uint8_t)((CJ_J_LOCAL_TIMEOUT_MS >> 8U) & 0xFFU)
    };
    send_j_message(bridge, CJ_MSG_PICK_WINDOW, timeout_payload, sizeof(timeout_payload));
    bridge->diag_pick_window_sent_count++;
    set_state(bridge, CJ_BRIDGE_WAIT_J_RESULT, CJ_J_WATCHDOG_TIMEOUT_MS);
    return;
  }

  if (strcmp(line, "RESUME_ACK") == 0 && bridge->state == CJ_BRIDGE_WAIT_UNO_RESUME_ACK) {
    set_state(bridge, CJ_BRIDGE_IDLE, 0UL);
    bridge->active_color = 0U;
    return;
  }
}

void cj_bridge_on_j_frame(cj_bridge_t *bridge, const cj_frame_t *frame) {
  bridge->last_j_seq = frame->seq;
  bridge->last_j_type = frame->type;
  send_j_ack(bridge, frame->seq, frame->type);

  switch (frame->type) {
    case CJ_MSG_COLOR_FOUND:
      bridge->diag_color_found_count++;
      if (bridge->state != CJ_BRIDGE_IDLE) {
        return;
      }
      bridge->active_color = frame->len > 0U ? frame->payload[0] : 0U;
      if (bridge->io.send_uno_line != 0) {
        bridge->io.send_uno_line("STOP_REQ");
      }
      set_state(bridge, CJ_BRIDGE_WAIT_UNO_STOP_ACK, CJ_UNO_ACK_TIMEOUT_MS);
      return;

    case CJ_MSG_PICK_DONE:
      bridge->diag_pick_done_count++;
      break;
    case CJ_MSG_PICK_TIMEOUT:
      bridge->diag_pick_timeout_count++;
      break;
    case CJ_MSG_ARM_FAIL:
      bridge->diag_arm_fail_count++;
      break;
    default:
      break;
  }

  switch (frame->type) {
    case CJ_MSG_PICK_DONE:
    case CJ_MSG_PICK_TIMEOUT:
    case CJ_MSG_ARM_FAIL:
      if (bridge->state != CJ_BRIDGE_WAIT_J_RESULT &&
          bridge->state != CJ_BRIDGE_WAIT_UNO_STOP_ACK) {
        return;
      }
      if (bridge->state == CJ_BRIDGE_WAIT_UNO_STOP_ACK) {
        bridge->diag_early_j_result_count++;
        log_line(bridge, "bridge: early J result, forcing resume");
      }
      if (bridge->io.send_uno_line != 0) {
        bridge->io.send_uno_line("RESUME_REQ");
      }
      set_state(bridge, CJ_BRIDGE_WAIT_UNO_RESUME_ACK, CJ_UNO_ACK_TIMEOUT_MS);
      return;

    case CJ_MSG_HEARTBEAT:
    case CJ_MSG_ARM_BUSY:
    case CJ_MSG_ACK:
    case CJ_MSG_PING:
    default:
      return;
  }
}

const char *cj_bridge_state_name(cj_bridge_state_t state) {
  switch (state) {
    case CJ_BRIDGE_IDLE:
      return "IDLE";
    case CJ_BRIDGE_WAIT_UNO_STOP_ACK:
      return "WAIT_UNO_STOP_ACK";
    case CJ_BRIDGE_WAIT_J_RESULT:
      return "WAIT_J_RESULT";
    case CJ_BRIDGE_WAIT_UNO_RESUME_ACK:
      return "WAIT_UNO_RESUME_ACK";
    case CJ_BRIDGE_FAULT:
      return "FAULT";
    default:
      return "UNKNOWN";
  }
}
