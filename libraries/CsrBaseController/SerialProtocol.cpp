#include "SerialProtocol.h"

#include <stdlib.h>
#include <string.h>

void SerialProtocol::sendReady(Stream& serial) {
  serial.println(F("CSR_UNO_READY"));
}

void SerialProtocol::sendAckWheelTargets(Stream& serial) {
  serial.println(F("ACK:W"));
}

void SerialProtocol::sendError(Stream& serial, const char* reason) {
  serial.print(F("ERR:"));
  serial.println(reason);
}

void SerialProtocol::sendEncoderTelemetry(Stream& serial, const long ticks[4], const float speeds[4]) {
  serial.print(F("ENC,"));
  serial.print(ticks[0]);
  serial.print(',');
  serial.print(ticks[1]);
  serial.print(',');
  serial.print(ticks[2]);
  serial.print(',');
  serial.print(ticks[3]);
  serial.print(',');
  serial.print(speeds[0], 1);
  serial.print(',');
  serial.print(speeds[1], 1);
  serial.print(',');
  serial.print(speeds[2], 1);
  serial.print(',');
  serial.println(speeds[3], 1);
}

SerialParseStatus SerialProtocol::parseWheelTargets(const char* line, int16_t targets[4]) {
  if (line == nullptr || line[0] == '\0') {
    return SERIAL_PARSE_EMPTY;
  }

  char buffer[64];
  strncpy(buffer, line, sizeof(buffer) - 1);
  buffer[sizeof(buffer) - 1] = '\0';

  char* context = nullptr;
  char* token = strtok_r(buffer, ",", &context);
  if (token == nullptr || strcmp(token, "W") != 0) {
    return SERIAL_PARSE_BAD_PREFIX;
  }

  for (uint8_t i = 0; i < 4; ++i) {
    token = strtok_r(nullptr, ",", &context);
    if (token == nullptr) {
      return SERIAL_PARSE_BAD_FIELD_COUNT;
    }

    char* endPtr = nullptr;
    long parsed = strtol(token, &endPtr, 10);
    if (endPtr == token || *endPtr != '\0' || parsed < -32768L || parsed > 32767L) {
      return SERIAL_PARSE_BAD_NUMBER;
    }
    targets[i] = (int16_t)parsed;
  }

  if (strtok_r(nullptr, ",", &context) != nullptr) {
    return SERIAL_PARSE_BAD_FIELD_COUNT;
  }

  return SERIAL_PARSE_OK;
}

const char* SerialProtocol::statusToReason(SerialParseStatus status) {
  switch (status) {
    case SERIAL_PARSE_EMPTY:
      return "EMPTY";
    case SERIAL_PARSE_BAD_PREFIX:
      return "PREFIX";
    case SERIAL_PARSE_BAD_FIELD_COUNT:
      return "FIELDS";
    case SERIAL_PARSE_BAD_NUMBER:
      return "NUMBER";
    default:
      return "UNKNOWN";
  }
}
