#ifndef CLEANSCOUT_FAN_H_
#define CLEANSCOUT_FAN_H_

#include <Arduino.h>

class CleanScoutFan {
  public:
    enum State : uint8_t {
      DISABLED = 0,
      COOLDOWN = 1,
      RUNNING = 2,
      PAUSED_BY_OBSTACLE = 3
    };

    CleanScoutFan(unsigned long cooldownMs, unsigned long runMs);

    void begin(uint8_t pin, bool activeHigh);
    void update(uint8_t currentMode, unsigned long nowMs);

    void pauseByObstacle();
    void notifyTurnCompleted();
    void forceOff();

    bool isRunning() const;
    uint8_t getState() const;
    bool isPausedByObstacle() const;

  private:
    static const uint8_t kAutoMode = 1;

    void setOutputEnabled(bool enabled);
    void setState(State nextState, unsigned long nowMs);

    uint8_t relayPin;
    bool relayActiveHigh;
    bool initialized;
    bool pendingTurnResume;
    State state;
    unsigned long stateStartedAt;
    unsigned long cooldownMs;
    unsigned long runMs;
};

#endif
