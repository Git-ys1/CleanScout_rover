#ifndef CSR_BASE_CONTROLLER_H_
#define CSR_BASE_CONTROLLER_H_

#include <Arduino.h>

#include <Tyler_1.h>

#include "SerialProtocol.h"
#include "WheelEncoder.h"
#include "WheelPI.h"

struct WheelPinConfig {
  uint8_t pinA;
  uint8_t pinB;
  int8_t directionSign;
};

struct WheelPiConfig {
  float kp;
  float ki;
  float integralLimit;
  float outputLimit;
};

struct CsrBaseControllerConfig {
  WheelPinConfig wheelPins[4];
  WheelPiConfig wheelPi[4];
  uint16_t controlPeriodMs;
  uint16_t commandTimeoutMs;
  bool openLoopDirectDrive;
  float speedFilterAlpha;
  int16_t startupPwm;
  int16_t startupPwmByWheel[4];
  int16_t minDrivePwmByWheel[4];
  float startupMeasuredThreshold;
  float startupMeasuredThresholdByWheel[4];
  int16_t maxPwmStepPerCycle;
  float controlDtSeconds;
  float dMechMm;
  float dEffMm;
  float wbM;
  float twM;
  float kM;
  float cprX1Est;
};

class CsrBaseController {
  public:
    CsrBaseController(Tyler_1& drive, Stream& serial);

    void begin(const CsrBaseControllerConfig& config);
    void update(unsigned long nowMs);

    void setWheelTargetsTicksPerSecond(float w1, float w2, float w3, float w4);
    bool consumeAckPulse();

  private:
    static const uint8_t kWheelCount = 4;
    static const size_t kLineBufferSize = 64;

    Tyler_1& drive_;
    Stream& serial_;
    CsrBaseControllerConfig config_;
    WheelEncoder encoders_[kWheelCount];
    WheelPI controllers_[kWheelCount];
    float targetTicksPerSecond_[kWheelCount];
    float measuredTicksPerSecond_[kWheelCount];
    float filteredTicksPerSecond_[kWheelCount];
    int16_t lastPwmCommand_[kWheelCount];
    bool configLoaded_;
    bool ackPulsePending_;
    bool commandActive_;
    unsigned long lastCommandAtMs_;
    unsigned long lastControlAtMs_;
    char lineBuffer_[kLineBufferSize];
    size_t lineLength_;

    void pollSerial(unsigned long nowMs);
    void processLine(unsigned long nowMs, const char* line);
    void runControlLoop(unsigned long nowMs);
    void handleTimeout(unsigned long nowMs);
    int16_t applyDeadbandCompensation(int16_t signedPwm) const;
    int16_t applyPerWheelMinDrive(uint8_t index, float targetTicksPerSecond, int16_t signedPwm) const;
    int16_t clampOutputDirection(float targetTicksPerSecond, int16_t signedPwm) const;
    int16_t applyStartupCompensation(uint8_t index, float targetTicksPerSecond, float measuredTicksPerSecond, int16_t signedPwm) const;
    int16_t applyOutputSlewLimit(uint8_t index, int16_t signedPwm);
    void zeroTargets();
    void resetControllers();
};

#endif
