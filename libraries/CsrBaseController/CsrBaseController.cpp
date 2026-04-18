#include "CsrBaseController.h"

#include <math.h>
#include <string.h>

namespace {
static const int16_t PWM_DEADBAND = 0;

template <typename T>
static T clampValue(T value, T minValue, T maxValue) {
  if (value < minValue) {
    return minValue;
  }
  if (value > maxValue) {
    return maxValue;
  }
  return value;
}
}

CsrBaseController::CsrBaseController(Tyler_1& drive, Stream& serial)
  : drive_(drive),
    serial_(serial),
    config_(),
    encoders_(),
    controllers_(),
    targetTicksPerSecond_{0.0f, 0.0f, 0.0f, 0.0f},
    measuredTicksPerSecond_{0.0f, 0.0f, 0.0f, 0.0f},
    filteredTicksPerSecond_{0.0f, 0.0f, 0.0f, 0.0f},
    lastPwmCommand_{0, 0, 0, 0},
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
    filteredTicksPerSecond_[i] = 0.0f;
    lastPwmCommand_[i] = 0;
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
    float rawTicksPerSecond = encoders_[i].sampleTicksPerSecond(nowMs);
    float alpha = clampValue(config_.speedFilterAlpha, 0.0f, 1.0f);
    filteredTicksPerSecond_[i] += alpha * (rawTicksPerSecond - filteredTicksPerSecond_[i]);
    measuredTicksPerSecond_[i] = filteredTicksPerSecond_[i];
    ticks[i] = encoders_[i].readTicks();

    if (config_.openLoopDirectDrive) {
      controllers_[i].reset();
      pwm[i] = applyDeadbandCompensation((int16_t)constrain(lroundf(targetTicksPerSecond_[i]), -255, 255));
      pwm[i] = applyOutputSlewLimit(i, pwm[i]);
      continue;
    }

    if (targetTicksPerSecond_[i] == 0.0f) {
      controllers_[i].reset();
      pwm[i] = 0;
      pwm[i] = applyOutputSlewLimit(i, pwm[i]);
      continue;
    }

    float control = controllers_[i].compute(targetTicksPerSecond_[i], measuredTicksPerSecond_[i]);
    pwm[i] = applyDeadbandCompensation((int16_t)lroundf(control));
    pwm[i] = clampOutputDirection(targetTicksPerSecond_[i], pwm[i]);
    pwm[i] = applyStartupCompensation(i, targetTicksPerSecond_[i], measuredTicksPerSecond_[i], pwm[i]);
    pwm[i] = applyPerWheelMinDrive(i, targetTicksPerSecond_[i], pwm[i]);
    pwm[i] = applyOutputSlewLimit(i, pwm[i]);
  }

  drive_.setWheelCommands(pwm[0], pwm[1], pwm[2], pwm[3]);
  SerialProtocol::sendEncoderTelemetry(serial_, ticks, measuredTicksPerSecond_);
  SerialProtocol::sendPidTelemetry(serial_, targetTicksPerSecond_, measuredTicksPerSecond_, pwm);
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

int16_t CsrBaseController::clampOutputDirection(float targetTicksPerSecond, int16_t signedPwm) const {
  if (targetTicksPerSecond > 0.0f && signedPwm < 0) {
    return 0;
  }

  if (targetTicksPerSecond < 0.0f && signedPwm > 0) {
    return 0;
  }

  return signedPwm;
}

int16_t CsrBaseController::applyPerWheelMinDrive(uint8_t index, float targetTicksPerSecond, int16_t signedPwm) const {
  if (signedPwm == 0 || targetTicksPerSecond == 0.0f) {
    return signedPwm;
  }

  int16_t minDrivePwm = 0;
  if (index < kWheelCount) {
    minDrivePwm = config_.minDrivePwmByWheel[index];
  }

  if (minDrivePwm <= 0) {
    return signedPwm;
  }

  if (fabsf(targetTicksPerSecond) < config_.startupMeasuredThreshold) {
    return signedPwm;
  }

  int16_t absPwm = abs(signedPwm);
  if (absPwm >= minDrivePwm) {
    return signedPwm;
  }

  return signedPwm > 0 ? minDrivePwm : -minDrivePwm;
}

int16_t CsrBaseController::applyStartupCompensation(uint8_t index, float targetTicksPerSecond, float measuredTicksPerSecond, int16_t signedPwm) const {
  int16_t startupPwm = config_.startupPwm;
  if (index < kWheelCount && config_.startupPwmByWheel[index] > 0) {
    startupPwm = config_.startupPwmByWheel[index];
  }
  float startupMeasuredThreshold = config_.startupMeasuredThreshold;
  if (index < kWheelCount && config_.startupMeasuredThresholdByWheel[index] > 0.0f) {
    startupMeasuredThreshold = config_.startupMeasuredThresholdByWheel[index];
  }

  if (signedPwm == 0 || startupPwm <= 0) {
    return signedPwm;
  }

  if (fabsf(targetTicksPerSecond) <= 0.0f) {
    return signedPwm;
  }

  if (fabsf(measuredTicksPerSecond) > startupMeasuredThreshold) {
    return signedPwm;
  }

  int16_t absPwm = abs(signedPwm);
  if (absPwm >= startupPwm) {
    return signedPwm;
  }

  return signedPwm > 0 ? startupPwm : -startupPwm;
}

int16_t CsrBaseController::applyOutputSlewLimit(uint8_t index, int16_t signedPwm) {
  if (config_.maxPwmStepPerCycle <= 0) {
    lastPwmCommand_[index] = signedPwm;
    return signedPwm;
  }

  int16_t previous = lastPwmCommand_[index];
  int16_t minValue = previous - config_.maxPwmStepPerCycle;
  int16_t maxValue = previous + config_.maxPwmStepPerCycle;
  int16_t limited = clampValue<int16_t>(signedPwm, minValue, maxValue);
  lastPwmCommand_[index] = limited;
  return limited;
}

void CsrBaseController::zeroTargets() {
  for (uint8_t i = 0; i < kWheelCount; ++i) {
    targetTicksPerSecond_[i] = 0.0f;
  }
}

void CsrBaseController::resetControllers() {
  for (uint8_t i = 0; i < kWheelCount; ++i) {
    controllers_[i].reset();
    filteredTicksPerSecond_[i] = 0.0f;
    lastPwmCommand_[i] = 0;
  }
}
