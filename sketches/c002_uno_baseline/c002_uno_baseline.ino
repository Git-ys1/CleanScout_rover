#include <Tyler_1.h>

static const unsigned long SERIAL_BAUD = 115200UL;
static const unsigned long COMMAND_TIMEOUT_MS = 400UL;

// 暂不修改 Tyler_1 库，通过占位脚绕开超声/舵机耦合。
// A5 作为超声 trig 占位，D13 同时作为 echo/servo 占位。
Tyler_1 tyler_1(1, 0, 1, 1, 200, A5, 13, 13);

unsigned long lastCommandAtMs = 0;
bool motionCommandActive = false;

bool isSupportedCommand(char command) {
  switch (command) {
    case '1':
    case '2':
    case '3':
    case '4':
    case '5':
    case '6':
    case '7':
    case '8':
    case '9':
      return true;
    default:
      return false;
  }
}

void applyManualCommand(char command) {
  switch (command) {
    case '8':
      tyler_1.forward();
      motionCommandActive = true;
      break;
    case '2':
      tyler_1.backward();
      motionCommandActive = true;
      break;
    case '4':
      tyler_1.turnL();
      motionCommandActive = true;
      break;
    case '6':
      tyler_1.turnR();
      motionCommandActive = true;
      break;
    case '5':
      tyler_1.stop();
      motionCommandActive = false;
      break;
    case '7':
      tyler_1.forwardL();
      motionCommandActive = true;
      break;
    case '9':
      tyler_1.forwardR();
      motionCommandActive = true;
      break;
    case '1':
      tyler_1.backwardR();
      motionCommandActive = true;
      break;
    case '3':
      tyler_1.backwardL();
      motionCommandActive = true;
      break;
  }
}

void pollUsbSerial() {
  while (Serial.available() > 0) {
    char incomingChar = (char)Serial.read();

    if (incomingChar == '\r' || incomingChar == '\n') {
      continue;
    }

    if (!isSupportedCommand(incomingChar)) {
      continue;
    }

    applyManualCommand(incomingChar);
    lastCommandAtMs = millis();
  }
}

void enforceCommandTimeout() {
  if (!motionCommandActive) {
    return;
  }

  if (millis() - lastCommandAtMs > COMMAND_TIMEOUT_MS) {
    tyler_1.stop();
    motionCommandActive = false;
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(100);
  tyler_1.stop();
  lastCommandAtMs = millis();
}

void loop() {
  pollUsbSerial();
  enforceCommandTimeout();
}
