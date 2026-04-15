#include "WheelEncoder.h"

#include <avr/interrupt.h>

WheelEncoder* WheelEncoder::instances_[kWheelCount] = {nullptr, nullptr, nullptr, nullptr};
volatile long WheelEncoder::encoder_ticks_[kWheelCount] = {0, 0, 0, 0};
volatile uint8_t WheelEncoder::encoder_state_[kWheelCount] = {0, 0, 0, 0};

WheelEncoder::WheelEncoder()
  : index_(0),
    pinA_(0),
    pinB_(0),
    pcintGroupBit_(0),
    bitMaskA_(0),
    bitMaskB_(0),
    inputRegA_(nullptr),
    inputRegB_(nullptr),
    directionSign_(1),
    lastTicksSnapshot_(0),
    lastSampleMs_(0),
    initialized_(false) {
}

void WheelEncoder::begin(uint8_t index, uint8_t pinA, uint8_t pinB, int8_t directionSign) {
  index_ = index;
  pinA_ = pinA;
  pinB_ = pinB;
  directionSign_ = directionSign >= 0 ? 1 : -1;

  pinMode(pinA_, INPUT_PULLUP);
  pinMode(pinB_, INPUT_PULLUP);

  bitMaskA_ = digitalPinToBitMask(pinA_);
  bitMaskB_ = digitalPinToBitMask(pinB_);
  inputRegA_ = portInputRegister(digitalPinToPort(pinA_));
  inputRegB_ = portInputRegister(digitalPinToPort(pinB_));
  pcintGroupBit_ = digitalPinToPCICRbit(pinA_);

  volatile uint8_t* pcmsk = digitalPinToPCMSK(pinA_);
  *pcmsk |= bit(digitalPinToPCMSKbit(pinA_));
  PCIFR |= bit(pcintGroupBit_);
  PCICR |= bit(pcintGroupBit_);

  encoder_ticks_[index_] = 0;
  encoder_state_[index_] = ((*inputRegA_ & bitMaskA_) != 0) ? 1 : 0;
  lastTicksSnapshot_ = 0;
  lastSampleMs_ = 0;
  instances_[index_] = this;
  initialized_ = true;
}

void WheelEncoder::setDirectionSign(int8_t sign) {
  directionSign_ = sign >= 0 ? 1 : -1;
}

long WheelEncoder::readTicks() const {
  if (!initialized_) {
    return 0;
  }

  noInterrupts();
  long ticks = encoder_ticks_[index_];
  interrupts();
  return ticks;
}

float WheelEncoder::sampleTicksPerSecond(unsigned long nowMs) {
  long ticksNow = readTicks();

  if (lastSampleMs_ == 0) {
    lastSampleMs_ = nowMs;
    lastTicksSnapshot_ = ticksNow;
    return 0.0f;
  }

  unsigned long dtMs = nowMs - lastSampleMs_;
  if (dtMs == 0) {
    return 0.0f;
  }

  long deltaTicks = ticksNow - lastTicksSnapshot_;
  lastTicksSnapshot_ = ticksNow;
  lastSampleMs_ = nowMs;

  return (deltaTicks * 1000.0f) / dtMs;
}

void WheelEncoder::handlePortBInterrupt() {
  serviceGroup(0);
}

void WheelEncoder::handlePortCInterrupt() {
  serviceGroup(1);
}

void WheelEncoder::serviceGroup(uint8_t pcintGroupBit) {
  for (uint8_t i = 0; i < kWheelCount; ++i) {
    WheelEncoder* encoder = instances_[i];
    if (encoder == nullptr || !encoder->initialized_ || encoder->pcintGroupBit_ != pcintGroupBit) {
      continue;
    }

    const bool currentA = ((*encoder->inputRegA_ & encoder->bitMaskA_) != 0);
    const bool previousA = (encoder_state_[i] != 0);

    if (currentA && !previousA) {
      const bool currentB = ((*encoder->inputRegB_ & encoder->bitMaskB_) != 0);
      int8_t delta = (currentA == currentB) ? -1 : 1;
      delta *= encoder->directionSign_;
      encoder_ticks_[i] += delta;
    }

    encoder_state_[i] = currentA ? 1 : 0;
  }
}

ISR(PCINT0_vect) {
  WheelEncoder::handlePortBInterrupt();
}

ISR(PCINT1_vect) {
  WheelEncoder::handlePortCInterrupt();
}
