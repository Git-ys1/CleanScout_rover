#ifndef CSR_WHEEL_ENCODER_H_
#define CSR_WHEEL_ENCODER_H_

#include <Arduino.h>

class WheelEncoder {
  public:
    WheelEncoder();

    void begin(uint8_t index, uint8_t pinA, uint8_t pinB, int8_t directionSign = 1);
    void setDirectionSign(int8_t sign);

    long readTicks() const;
    float sampleTicksPerSecond(unsigned long nowMs);

    static void handlePortBInterrupt();
    static void handlePortCInterrupt();

  private:
    static const uint8_t kWheelCount = 4;

    uint8_t index_;
    uint8_t pinA_;
    uint8_t pinB_;
    uint8_t pcintGroupBit_;
    uint8_t bitMaskA_;
    uint8_t bitMaskB_;
    volatile uint8_t* inputRegA_;
    volatile uint8_t* inputRegB_;
    int8_t directionSign_;
    long lastTicksSnapshot_;
    unsigned long lastSampleMs_;
    bool initialized_;

    static WheelEncoder* instances_[kWheelCount];
    static volatile long encoder_ticks_[kWheelCount];
    static volatile uint8_t encoder_state_[kWheelCount];

    static void serviceGroup(uint8_t pcintGroupBit);
};

#endif
