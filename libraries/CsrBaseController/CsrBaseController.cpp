#include "CsrBaseController.h"

#include <math.h>
#include <string.h>

namespace {
static const int16_t PWM_DEADBAND = 0;
}

CsrBaseController::CsrBaseController(Tyler_1& drive, Stream& serial)
  : drive_(drive),
    serial_(serial),
    config_(),
    encoders_(),
    controllers_(),
    targetTicksPerSecond_{0.0f, 0.0f, 0.0f, 0.0f},
    measuredTicksPerSecond_{0.0f, 0.0f, 0.0f, 0.0f},
    configLoaded_(false),
    ackPulsePending_(false),
    commandActive_(false),
    lastCommandAtMs_(0),
    lastControlAtMs_(0),
    lineBuffer_(),
    lineLength_(0) {
}

void CsrBaseController::begin(const CsrBaseControllerConfig& config) {
  config_ = config;

  for (uint8_t i = 0; i < kWheelCount; ++i) {
    encoders_[i].begin(i, config_.wheelPins[i].pinA, config_.wheelPins[i].pinB, config_.wheelPins[i].directionSign);
    controllers_[i].begin(
      config_.wheelPi[i].kp,
      config_.wheelPi[i].ki,
      config_.wheelPi[i].integralLimit,
      config_.wheelPi[i].outputLimit,
      config_.controlDtSeconds
    );
    targetTicksPerSecond_[i] = 0.0f;
    measuredTicksPerSecond_[i] = 0.0f;
  }

  drive_.setWheelCommands(0, 0, 0, 0);
  configLoaded_ = true;
  ackPulsePending_ = false;
  commandActive_ = false;
  lastCommandAtMs_ = 0;
  lastControlAtMs_ = millis();
  lineLength_ = 0;
  lineBuffer_[0] = '\0';
}

void CsrBaseController::update(unsigned long nowMs) {
  if (!configLoaded_) {
    return;
  }

  pollSerial(nowMs);

  if ((nowMs - lastControlAtMs_) >= config_.controlPeriodMs) {
    lastControlAtMs_ = nowMs;
    runControlLoop(nowMs);
  }
}

void CsrBaseController::setWheelTargetsTicksPerSecond(float w1, float w2, float w3, float w4) {
  targetTicksPerSecond_[0] = w1;
  targetTicksPerSecond_[1] = w2;
  targetTicksPerSecond_[2] = w3;
  targetTicksPerSecond_[3] = w4;
}

bool CsrBaseController::consumeAckPulse() {
  bool pulse = ackPulsePending_;
  ackPulsePending_ = false;
  return pulse;
}

void CsrBaseController::pollSerial(unsigned long nowMs) {
  while (serial_.available() > 0) {
    char incoming = (char)serial_.read();

    if (incoming == '\r') {
      continue;
    }

    if (incoming == '\n') {
      if (lineLength_ > 0) {
        lineBuffer_[lineLength_] = '\0';
        processLine(nowMs, lineBuffer_);
        lineLength_ = 0;
      }
      continue;
    }

    if (lineLength_ >= (kLineBufferSize - 1)) {
      lineLength_ = 0;
      SerialProtocol::sendError(serial_, "OVERFLOW");
      continue;
    }

    lineBuffer_[lineLength_++] = incoming;
  }
}

void CsrBaseController::processLine(unsigned long nowMs, const char* line) {
  int16_t targets[kWheelCount] = {0, 0, 0, 0};
  SerialParseStatus status = SerialProtocol::parseWheelTargets(line, targets);
  if (status != SERIAL_PARSE_OK) {
    SerialProtocol::sendError(serial_, SerialProtocol::statusToReason(status));
    return;
  }

  setWheelTargetsTicksPerSecond(
    (float)targets[0],
    (float)targets[1],
    (float)targets[2],
    (float)targets[3]
  );

  lastCommandAtMs_ = nowMs;
  commandActive_ = true;
  ackPulsePending_ = true;
  SerialProtocol::sendAckWheelTargets(serial_);
}

void CsrBaseController::runControlLoop(unsigned long nowMs) {
  handleTimeout(nowMs);

  long ticks[kWheelCount] = {0, 0, 0, 0};
  int16_t pwm[kWheelCount] = {0, 0, 0, 0};

  for (uint8_t i = 0; i < kWheelCount; ++i) {
    measuredTicksPerSecond_[i] = encoders_[i].sampleTicksPerSecond(nowMs);
    ticks[i] = encoders_[i].readTicks();

    if (targetTicksPerSecond_[i] == 0.0f) {
      controllers_[i].reset();
      pwm[i] = 0;
      continue;
    }

    float control = controllers_[i].compute(targetTicksPerSecond_[i], measuredTicksPerSecond_[i]);
    pwm[i] = applyDeadbandCompensation((int16_t)lroundf(control));
  }

  drive_.setWheelCommands(pwm[0], pwm[1], pwm[2], pwm[3]);
  SerialProtocol::sendEncoderTelemetry(serial_, ticks, measuredTicksPerSecond_);
}

void CsrBaseController::handleTimeout(unsigned long nowMs) {
  if (!commandActive_) {
    return;
  }

  if ((nowMs - lastCommandAtMs_) <= config_.commandTimeoutMs) {
    return;
  }

  commandActive_ = false;
  zeroTargets();
  resetControllers();
  drive_.setWheelCommands(0, 0, 0, 0);
}

int16_t CsrBaseController::applyDeadbandCompensation(int16_t signedPwm) const {
  if (PWM_DEADBAND <= 0 || signedPwm == 0) {
    return signedPwm;
  }

  if (signedPwm > 0 && signedPwm < PWM_DEADBAND) {
    return PWM_DEADBAND;
  }

  if (signedPwm < 0 && signedPwm > -PWM_DEADBAND) {
    return -PWM_DEADBAND;
  }

  return signedPwm;
}

void CsrBaseController::zeroTargets() {
  for (uint8_t i = 0; i < kWheelCount; ++i) {
    targetTicksPerSecond_[i] = 0.0f;
  }
}

void CsrBaseController::resetControllers() {
  for (uint8_t i = 0; i < kWheelCount; ++i) {
    controllers_[i].reset();
  }
}
