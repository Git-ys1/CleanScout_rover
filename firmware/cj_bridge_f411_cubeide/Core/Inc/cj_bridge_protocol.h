#ifndef CJ_BRIDGE_PROTOCOL_H_
#define CJ_BRIDGE_PROTOCOL_H_

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define CJ_PROTOCOL_SOF0 0x43U
#define CJ_PROTOCOL_SOF1 0x4AU
#define CJ_PROTOCOL_VERSION 0x01U
#define CJ_PROTOCOL_MAX_PAYLOAD 16U
#define CJ_PROTOCOL_MAX_FRAME_SIZE (7U + CJ_PROTOCOL_MAX_PAYLOAD)

typedef enum {
  CJ_MSG_COLOR_FOUND = 0x10,
  CJ_MSG_ARM_BUSY = 0x11,
  CJ_MSG_PICK_DONE = 0x12,
  CJ_MSG_PICK_TIMEOUT = 0x13,
  CJ_MSG_ARM_FAIL = 0x14,
  CJ_MSG_HEARTBEAT = 0x15,
  CJ_MSG_ACK = 0x80,
  CJ_MSG_PICK_WINDOW = 0x81,
  CJ_MSG_ABORT = 0x82,
  CJ_MSG_PING = 0x83
} cj_message_type_t;

typedef struct {
  uint8_t version;
  uint8_t seq;
  uint8_t type;
  uint8_t len;
  uint8_t payload[CJ_PROTOCOL_MAX_PAYLOAD];
} cj_frame_t;

typedef enum {
  CJ_PARSE_WAIT_SOF0 = 0,
  CJ_PARSE_WAIT_SOF1,
  CJ_PARSE_VERSION,
  CJ_PARSE_SEQ,
  CJ_PARSE_TYPE,
  CJ_PARSE_LEN,
  CJ_PARSE_PAYLOAD,
  CJ_PARSE_CRC
} cj_parse_state_t;

typedef struct {
  cj_parse_state_t state;
  cj_frame_t frame;
  uint8_t payload_index;
  uint8_t crc_buffer[4U + CJ_PROTOCOL_MAX_PAYLOAD];
  uint8_t crc_length;
} cj_parser_t;

void cj_protocol_parser_init(cj_parser_t *parser);
bool cj_protocol_parser_push(cj_parser_t *parser, uint8_t byte, cj_frame_t *out_frame);
uint8_t cj_protocol_crc8_atm(const uint8_t *data, size_t length);
uint8_t cj_protocol_build_frame(uint8_t seq, uint8_t type, const uint8_t *payload, uint8_t len, uint8_t *out_buffer, uint8_t out_capacity);

#endif