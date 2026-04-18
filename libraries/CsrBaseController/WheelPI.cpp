#include "WheelPI.h"

WheelPI::WheelPI()
  : kp_(0.0f),
    ki_(0.0f),
    integral_(0.0f),
    integralLimit_(0.0f),
    outputLimit_(255.0f),
    dtSeconds_(0.02f) {
}

void WheelPI::begin(float kp, float ki, float iLimit, float outLimit, float dtSeconds) {
  kp_ = kp;
  ki_ = ki;
  integralLimit_ = abs(iLimit);
  outputLimit_ = abs(outLimit);
  dtSeconds_ = dtSeconds > 0.0f ? dtSeconds : 0.02f;
  reset();
}

void WheelPI::reset() {
  integral_ = 0.0f;
}

float WheelPI::compute(float targetTicksPerSecond, float measuredTicksPerSecond) {
  float error = targetTicksPerSecond - measuredTicksPerSecond;

  integral_ += error * dtSeconds_;
  if (integral_ > integralLimit_) {
    integral_ = integralLimit_;
  } else if (integral_ < -integralLimit_) {
    integral_ = -integralLimit_;
  }

  float output = (kp_ * error) + (ki_ * integral_);
  if (output > outputLimit_) {
    output = outputLimit_;
  } else if (output < -outputLimit_) {
    output = -outputLimit_;
  }

  return output;
}
