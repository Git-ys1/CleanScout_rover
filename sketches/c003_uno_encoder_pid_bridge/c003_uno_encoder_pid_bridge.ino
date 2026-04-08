#include <Tyler_1.h>
#include <CsrBaseController.h>
#include <WheelEncoder.h>

#ifndef CSR_WHEEL4_RAW_PROBE
#define CSR_WHEEL4_RAW_PROBE 0
#endif

static const unsigned long SERIAL_BAUD = 115200UL;
static const unsigned long LED_PULSE_MS = 60UL;
static const unsigned long RAW4_REPORT_MS = 100UL;

static const float D_MECH_MM = 80.0f;
static const float D_EFF_MM = 78.0f;
static const float WB_M = 0.16535f;
static const float TW_M = 0.17850f;
static const float K_M = 0.171925f;
static const float CPR_X1_EST = 260.0f;

static const uint16_t CONTROL_PERIOD_MS = 20U;
static const uint16_t COMMAND_TIMEOUT_MS = 400U;
static const uint16_t COMMAND_TIMEOUT_DEBUG_MS = 2000U;
static const bool USE_DEBUG_TIMEOUT = true;
static const float CONTROL_DT_SECONDS = 0.02f;

static const float WHEEL_KP = 2.0f;
static const float WHEEL_KI = 0.5f;
static const float WHEEL_I_LIMIT = 150.0f;
static const float WHEEL_OUTPUT_LIMIT = 255.0f;

static const int8_t ENC_SIGN_W1 = 1;
static const int8_t ENC_SIGN_W2 = 1;
static const int8_t ENC_SIGN_W3 = -1;
static const int8_t ENC_SIGN_W4 = 1;

Tyler_1 tyler_1(1, 0, 1, 1, 200, 255, 255, 255);
CsrBaseController controller(tyler_1, Serial);
WheelEncoder wheel4Probe;

unsigned long ledOffAtMs = 0;
unsigned long raw4LastReportAtMs = 0;

static CsrBaseControllerConfig makeControllerConfig() {
  CsrBaseControllerConfig config = {};

  config.wheelPins[0].pinA = A0;
  config.wheelPins[0].pinB = A1;
  config.wheelPins[0].directionSign = ENC_SIGN_W1;

  config.wheelPins[1].pinA = A2;
  config.wheelPins[1].pinB = A3;
  config.wheelPins[1].directionSign = ENC_SIGN_W2;

  config.wheelPins[2].pinA = A4;
  config.wheelPins[2].pinB = A5;
  config.wheelPins[2].directionSign = ENC_SIGN_W3;

  config.wheelPins[3].pinA = 9;
  config.wheelPins[3].pinB = 10;
  config.wheelPins[3].directionSign = ENC_SIGN_W4;

  for (uint8_t i = 0; i < 4; ++i) {
    config.wheelPi[i].kp = WHEEL_KP;
    config.wheelPi[i].ki = WHEEL_KI;
    config.wheelPi[i].integralLimit = WHEEL_I_LIMIT;
    config.wheelPi[i].outputLimit = WHEEL_OUTPUT_LIMIT;
  }

  config.controlPeriodMs = CONTROL_PERIOD_MS;
  config.commandTimeoutMs = USE_DEBUG_TIMEOUT ? COMMAND_TIMEOUT_DEBUG_MS : COMMAND_TIMEOUT_MS;
  config.controlDtSeconds = CONTROL_DT_SECONDS;
  config.dMechMm = D_MECH_MM;
  config.dEffMm = D_EFF_MM;
  config.wbM = WB_M;
  config.twM = TW_M;
  config.kM = K_M;
  config.cprX1Est = CPR_X1_EST;

  return config;
}

static CsrBaseControllerConfig controllerConfig = makeControllerConfig();

void pulseStatusLed() {
  digitalWrite(LED_BUILTIN, HIGH);
  ledOffAtMs = millis() + LED_PULSE_MS;
}

void updateStatusLed() {
  if (ledOffAtMs != 0 && (long)(millis() - ledOffAtMs) >= 0) {
    digitalWrite(LED_BUILTIN, LOW);
    ledOffAtMs = 0;
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  Serial.begin(SERIAL_BAUD);
  delay(100);

#if CSR_WHEEL4_RAW_PROBE
  wheel4Probe.begin(3, 9, 10, ENC_SIGN_W4);
#else
  controller.begin(controllerConfig);
#endif
  SerialProtocol::sendReady(Serial);
}

void loop() {
  unsigned long nowMs = millis();

#if CSR_WHEEL4_RAW_PROBE
  if ((nowMs - raw4LastReportAtMs) >= RAW4_REPORT_MS) {
    raw4LastReportAtMs = nowMs;
    Serial.print(F("RAW4,"));
    Serial.print(wheel4Probe.readTicks());
    Serial.print(',');
    Serial.print(digitalRead(9));
    Serial.print(',');
    Serial.println(digitalRead(10));
  }
#else
  controller.update(nowMs);

  if (controller.consumeAckPulse()) {
    pulseStatusLed();
  }
#endif

  updateStatusLed();
}
