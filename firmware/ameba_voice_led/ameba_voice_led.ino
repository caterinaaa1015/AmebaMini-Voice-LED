/*
 * AMB82-MINI (RTL8735BDM) USB Serial LED controller
 *
 * PC -> board: LED,BLUE,ON / LED,BLUE,OFF / LED,GREEN,ON / LED,GREEN,OFF
 *              LED,BLUE,BLINK,3 / LED,GREEN,BLINK,3
 * board -> PC: STATUS,BLUE=ON,GREEN=OFF
 *
 * Board definitions supplied by the Realtek Ameba Arduino core:
 *   LED_B = onboard blue LED (PF9 / Arduino pin 23)
 *   LED_G = onboard green LED (PE6 / Arduino pin 24)
 */

const uint8_t BLUE_LED = LED_B;
const uint8_t GREEN_LED = LED_G;

// If visual testing shows an LED has reversed logic, swap these two values.
const uint8_t LED_ON_LEVEL = HIGH;
const uint8_t LED_OFF_LEVEL = LOW;

bool blueOn = false;
bool greenOn = false;

char commandBuffer[48];
uint8_t commandLength = 0;

void applyLedState() {
  digitalWrite(BLUE_LED, blueOn ? LED_ON_LEVEL : LED_OFF_LEVEL);
  digitalWrite(GREEN_LED, greenOn ? LED_ON_LEVEL : LED_OFF_LEVEL);
}

const char *stateText(bool isOn) {
  return isOn ? "ON" : "OFF";
}

void sendStatus() {
  Serial.print("STATUS,BLUE=");
  Serial.print(stateText(blueOn));
  Serial.print(",GREEN=");
  Serial.println(stateText(greenOn));
}

void blinkThreeTimes(uint8_t ledPin) {
  // The selected LED always ends OFF; the other LED keeps its current state.
  for (uint8_t count = 0; count < 3; count++) {
    digitalWrite(ledPin, LED_ON_LEVEL);
    delay(250);
    digitalWrite(ledPin, LED_OFF_LEVEL);
    delay(250);
  }
}

void handleCommand(const char *command) {
  if (strcmp(command, "LED,BLUE,ON") == 0) {
    blueOn = true;
  } else if (strcmp(command, "LED,BLUE,OFF") == 0) {
    blueOn = false;
  } else if (strcmp(command, "LED,GREEN,ON") == 0) {
    greenOn = true;
  } else if (strcmp(command, "LED,GREEN,OFF") == 0) {
    greenOn = false;
  } else if (strcmp(command, "LED,BLUE,BLINK,3") == 0) {
    blueOn = false;
    blinkThreeTimes(BLUE_LED);
    applyLedState();
    sendStatus();
    return;
  } else if (strcmp(command, "LED,GREEN,BLINK,3") == 0) {
    greenOn = false;
    blinkThreeTimes(GREEN_LED);
    applyLedState();
    sendStatus();
    return;
  } else if (strcmp(command, "STATUS?") == 0) {
    sendStatus();
    return;
  } else {
    Serial.println("ERROR,UNKNOWN_COMMAND");
    return;
  }

  applyLedState();
  sendStatus();
}

void setup() {
  pinMode(BLUE_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  applyLedState();

  Serial.begin(115200);
  delay(300);
  Serial.println("READY,AMB82-MINI");
  sendStatus();
}

void loop() {
  while (Serial.available() > 0) {
    const char received = static_cast<char>(Serial.read());

    if (received == '\r') {
      continue;
    }
    if (received == '\n') {
      commandBuffer[commandLength] = '\0';
      if (commandLength > 0) {
        handleCommand(commandBuffer);
      }
      commandLength = 0;
      continue;
    }

    if (commandLength < sizeof(commandBuffer) - 1) {
      commandBuffer[commandLength++] = received;
    } else {
      commandLength = 0;
      Serial.println("ERROR,COMMAND_TOO_LONG");
    }
  }
}
