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
    pendingTurnResume(false),
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

  if (currentMode != kAutoMode) {
    forceOff();
    return;
  }

  if (state == DISABLED) {
    setOutputEnabled(false);
    setState(COOLDOWN, nowMs);
    return;
  }

  if (state == PAUSED_BY_OBSTACLE) {
    if (pendingTurnResume) {
      pendingTurnResume = false;
      setOutputEnabled(false);
      setState(COOLDOWN, nowMs);
    }
    return;
  }

  if (state == COOLDOWN) {
    if (nowMs - stateStartedAt >= cooldownMs) {
      setOutputEnabled(true);
      setState(RUNNING, nowMs);
    }
    return;
  }

  if (state == RUNNING && nowMs - stateStartedAt >= runMs) {
    setOutputEnabled(false);
    setState(COOLDOWN, nowMs);
  }
}

void CleanScoutFan::pauseByObstacle() {
  if (!initialized || state == DISABLED) {
    return;
  }

  pendingTurnResume = false;
  setOutputEnabled(false);
  setState(PAUSED_BY_OBSTACLE, millis());
}

void CleanScoutFan::notifyTurnCompleted() {
  if (!initialized || state != PAUSED_BY_OBSTACLE) {
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
  setOutputEnabled(false);
  state = DISABLED;
  stateStartedAt = 0;

#if CLEANSCOUT_FAN_DEBUG
  Serial.println(F("fan: forced off"));
#endif
}

bool CleanScoutFan::isRunning() const {
  return state == RUNNING;
}

uint8_t CleanScoutFan::getState() const {
  return static_cast<uint8_t>(state);
}

bool CleanScoutFan::isPausedByObstacle() const {
  return state == PAUSED_BY_OBSTACLE;
}

void CleanScoutFan::setOutputEnabled(bool enabled) {
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
