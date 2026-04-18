#include "CleanScoutFan.h"

#ifndef CLEANSCOUT_FAN_DEBUG
#define CLEANSCOUT_FAN_DEBUG 0
#endif

#if CLEANSCOUT_FAN_DEBUG
namespace {
const __FlashStringHelper* stateLabel(CleanScoutFan::State state) {
  switch (state) {
    case CleanScoutFan::DISABLED:
      return F("DISABLED");
    case CleanScoutFan::COOLDOWN:
      return F("COOLDOWN");
    case CleanScoutFan::RUNNING:
      return F("RUNNING");
    case CleanScoutFan::PAUSED_BY_OBSTACLE:
      return F("PAUSED_BY_OBSTACLE");
    default:
      return F("UNKNOWN");
  }
}
}
#endif

CleanScoutFan::CleanScoutFan(unsigned long cooldownMsValue, unsigned long runMsValue)
  : relayPin(A2),
    relayActiveHigh(true),
    initialized(false),
    outputEnabled(false),
    pendingTurnResume(false),
    manualLatchOn(false),
    controlSource(MANUAL_SOURCE),
    state(DISABLED),
    stateStartedAt(0),
    cooldownMs(cooldownMsValue),
    runMs(runMsValue) {
}

void CleanScoutFan::begin(uint8_t pin, bool activeHigh) {
  relayPin = pin;
  relayActiveHigh = activeHigh;
  initialized = true;

  pinMode(relayPin, OUTPUT);
  forceOff();
}

void CleanScoutFan::update(uint8_t currentMode, unsigned long nowMs) {
  if (!initialized) {
    return;
  }

  if (controlSource == MANUAL_SOURCE) {
    applyCurrentOutput();
    return;
  }

  if (currentMode != kAutoMode) {
    pendingTurnResume = false;
    state = DISABLED;
    stateStartedAt = 0;
    applyCurrentOutput();
    return;
  }

  if (state == DISABLED) {
    setState(COOLDOWN, nowMs);
    applyCurrentOutput();
    return;
  }

  if (state == PAUSED_BY_OBSTACLE) {
    if (pendingTurnResume) {
      pendingTurnResume = false;
      setState(COOLDOWN, nowMs);
      applyCurrentOutput();
    }
    return;
  }

  if (state == COOLDOWN) {
    if (nowMs - stateStartedAt >= cooldownMs) {
      setState(RUNNING, nowMs);
      applyCurrentOutput();
    }
    return;
  }

  if (state == RUNNING && nowMs - stateStartedAt >= runMs) {
    setState(COOLDOWN, nowMs);
    applyCurrentOutput();
  }
}

void CleanScoutFan::setControlSourceAuto(unsigned long nowMs) {
  if (!initialized) {
    return;
  }

  controlSource = AUTO_SOURCE;
  manualLatchOn = false;
  pendingTurnResume = false;
  setState(COOLDOWN, nowMs);
  applyCurrentOutput();
}

void CleanScoutFan::setControlSourceManual(bool preserveManualLatch) {
  if (!initialized) {
    return;
  }

  controlSource = MANUAL_SOURCE;
  pendingTurnResume = false;
  state = DISABLED;
  stateStartedAt = 0;

  if (!preserveManualLatch) {
    manualLatchOn = false;
  }

  applyCurrentOutput();
}

void CleanScoutFan::toggleManualLatch() {
  if (!initialized || controlSource != MANUAL_SOURCE) {
    return;
  }

  manualLatchOn = !manualLatchOn;
  applyCurrentOutput();
}

void CleanScoutFan::applyCurrentOutput() {
  if (!initialized) {
    return;
  }

  bool shouldEnable = false;

  if (controlSource == MANUAL_SOURCE) {
    shouldEnable = manualLatchOn;
  } else if (state == RUNNING) {
    shouldEnable = true;
  }

  setOutputEnabled(shouldEnable);
}

void CleanScoutFan::pauseByObstacle() {
  if (!initialized || controlSource != AUTO_SOURCE || state == DISABLED) {
    return;
  }

  pendingTurnResume = false;
  setState(PAUSED_BY_OBSTACLE, millis());
  applyCurrentOutput();
}

void CleanScoutFan::notifyTurnCompleted() {
  if (!initialized || controlSource != AUTO_SOURCE || state != PAUSED_BY_OBSTACLE) {
    return;
  }

  pendingTurnResume = true;

#if CLEANSCOUT_FAN_DEBUG
  Serial.println(F("fan: turn completed"));
#endif
}

void CleanScoutFan::forceOff() {
  if (!initialized) {
    return;
  }

  pendingTurnResume = false;
  manualLatchOn = false;
  state = DISABLED;
  stateStartedAt = 0;
  applyCurrentOutput();

#if CLEANSCOUT_FAN_DEBUG
  Serial.println(F("fan: forced off"));
#endif
}

bool CleanScoutFan::isRunning() const {
  return outputEnabled;
}

uint8_t CleanScoutFan::getState() const {
  return static_cast<uint8_t>(state);
}

bool CleanScoutFan::isPausedByObstacle() const {
  return state == PAUSED_BY_OBSTACLE;
}

CleanScoutFan::ControlSource CleanScoutFan::getControlSource() const {
  return controlSource;
}

bool CleanScoutFan::isManualLatchOn() const {
  return manualLatchOn;
}

void CleanScoutFan::setOutputEnabled(bool enabled) {
  outputEnabled = enabled;
  digitalWrite(relayPin, enabled == relayActiveHigh ? HIGH : LOW);

#if CLEANSCOUT_FAN_DEBUG
  Serial.print(F("fan output: "));
  Serial.println(enabled ? F("ON") : F("OFF"));
#endif
}

void CleanScoutFan::setState(State nextState, unsigned long nowMs) {
  state = nextState;
  stateStartedAt = nowMs;

#if CLEANSCOUT_FAN_DEBUG
  Serial.print(F("fan state -> "));
  Serial.println(stateLabel(nextState));
#endif
}
