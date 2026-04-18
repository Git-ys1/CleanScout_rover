#include "cj_bridge_protocol.h"

#include <string.h>

static void parser_reset(cj_parser_t *parser) {
  parser->state = CJ_PARSE_WAIT_SOF0;
  parser->payload_index = 0;
  parser->crc_length = 0;
  memset(&parser->frame, 0, sizeof(parser->frame));
}

void cj_protocol_parser_init(cj_parser_t *parser) {
  parser_reset(parser);
}

uint8_t cj_protocol_crc8_atm(const uint8_t *data, size_t length) {
  uint8_t crc = 0x00U;
  size_t index = 0;

  while (index < length) {
    crc ^= data[index++];
    for (uint8_t bit = 0; bit < 8U; ++bit) {
      if ((crc & 0x80U) != 0U) {
        crc = (uint8_t)((crc << 1U) ^ 0x07U);
      } else {
        crc <<= 1U;
      }
    }
  }

  return crc;
}

bool cj_protocol_parser_push(cj_parser_t *parser, uint8_t byte, cj_frame_t *out_frame) {
  switch (parser->state) {
    case CJ_PARSE_WAIT_SOF0:
      if (byte == CJ_PROTOCOL_SOF0) {
        parser->state = CJ_PARSE_WAIT_SOF1;
      }
      return false;

    case CJ_PARSE_WAIT_SOF1:
      if (byte == CJ_PROTOCOL_SOF1) {
        parser->state = CJ_PARSE_VERSION;
      } else {
        parser_reset(parser);
      }
      return false;

    case CJ_PARSE_VERSION:
      parser->frame.version = byte;
      parser->crc_buffer[0] = byte;
      parser->crc_length = 1U;
      parser->state = CJ_PARSE_SEQ;
      return false;

    case CJ_PARSE_SEQ:
      parser->frame.seq = byte;
      parser->crc_buffer[parser->crc_length++] = byte;
      parser->state = CJ_PARSE_TYPE;
      return false;

    case CJ_PARSE_TYPE:
      parser->frame.type = byte;
      parser->crc_buffer[parser->crc_length++] = byte;
      parser->state = CJ_PARSE_LEN;
      return false;

    case CJ_PARSE_LEN:
      if (byte > CJ_PROTOCOL_MAX_PAYLOAD) {
        parser_reset(parser);
        return false;
      }

      parser->frame.len = byte;
      parser->crc_buffer[parser->crc_length++] = byte;
      parser->payload_index = 0U;
      parser->state = (byte == 0U) ? CJ_PARSE_CRC : CJ_PARSE_PAYLOAD;
      return false;

    case CJ_PARSE_PAYLOAD:
      parser->frame.payload[parser->payload_index++] = byte;
      parser->crc_buffer[parser->crc_length++] = byte;

      if (parser->payload_index >= parser->frame.len) {
        parser->state = CJ_PARSE_CRC;
      }
      return false;

    case CJ_PARSE_CRC: {
      uint8_t expected_crc = cj_protocol_crc8_atm(parser->crc_buffer, parser->crc_length);
      if (expected_crc == byte && parser->frame.version == CJ_PROTOCOL_VERSION) {
        *out_frame = parser->frame;
        parser_reset(parser);
        return true;
      }

      parser_reset(parser);
      return false;
    }

    default:
      parser_reset(parser);
      return false;
  }
}

uint8_t cj_protocol_build_frame(uint8_t seq, uint8_t type, const uint8_t *payload, uint8_t len, uint8_t *out_buffer, uint8_t out_capacity) {
  uint8_t total_length = (uint8_t)(7U + len);
  uint8_t crc = 0U;

  if (len > CJ_PROTOCOL_MAX_PAYLOAD || out_capacity < total_length) {
    return 0U;
  }

  out_buffer[0] = CJ_PROTOCOL_SOF0;
  out_buffer[1] = CJ_PROTOCOL_SOF1;
  out_buffer[2] = CJ_PROTOCOL_VERSION;
  out_buffer[3] = seq;
  out_buffer[4] = type;
  out_buffer[5] = len;

  if (len > 0U && payload != NULL) {
    memcpy(&out_buffer[6], payload, len);
  }

  crc = cj_protocol_crc8_atm(&out_buffer[2], (size_t)(4U + len));
  out_buffer[6U + len] = crc;
  return total_length;
}