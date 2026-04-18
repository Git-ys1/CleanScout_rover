#ifndef CSR_SERIAL_PROTOCOL_H_
#define CSR_SERIAL_PROTOCOL_H_

#include <Arduino.h>

enum SerialParseStatus {
  SERIAL_PARSE_OK = 0,
  SERIAL_PARSE_EMPTY,
  SERIAL_PARSE_BAD_PREFIX,
  SERIAL_PARSE_BAD_FIELD_COUNT,
  SERIAL_PARSE_BAD_NUMBER
};

class SerialProtocol {
  public:
    static void sendReady(Stream& serial);
    static void sendAckWheelTargets(Stream& serial);
    static void sendError(Stream& serial, const char* reason);
    static void sendEncoderTelemetry(Stream& serial, const long ticks[4], const float speeds[4]);
    static void sendPidTelemetry(Stream& serial, const float targets[4], const float measured[4], const int16_t outputs[4]);
    static SerialParseStatus parseWheelTargets(const char* line, int16_t targets[4]);
    static const char* statusToReason(SerialParseStatus status);
};

#endif
