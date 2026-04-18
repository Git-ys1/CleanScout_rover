#ifndef CSR_WHEEL_PI_H_
#define CSR_WHEEL_PI_H_

#include <Arduino.h>

class WheelPI {
  public:
    WheelPI();

    void begin(float kp, float ki, float iLimit, float outLimit, float dtSeconds);
    void reset();
    float compute(float targetTicksPerSecond, float measuredTicksPerSecond);

  private:
    float kp_;
    float ki_;
    float integral_;
    float integralLimit_;
    float outputLimit_;
    float dtSeconds_;
};

#endif
