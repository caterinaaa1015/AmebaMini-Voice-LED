/* AMB82-MINI foot measurement camera, protocol FOOT10 v1.
 * No neural network: Python performs geometry, assuming a genuine NT$10 coin.
 * 115200 baud, JPEG 1280x720. Disable NN logs; choose the actual camera sensor.
 * CAPTURE -> JPEG packet; ACK,id,checksum -> blue (3s);
 * RESULT,id,1 -> green (5s), only after ACK for the current picture.
 */
#include "VideoStream.h"
extern "C" {
#include "FreeRTOS.h"
#include "task.h"
#include "semphr.h"
}

const int JPEG_CHANNEL = 1;
const uint32_t MAX_JPEG = 524288;
VideoSetting footJpegConfig(1280, 720, 3, VIDEO_JPEG, 1);
SemaphoreHandle_t serialLock, captureSignal;
volatile bool busy = false;
uint32_t nextId = 0, currentId = 0, currentChecksum = 0;
uint32_t receivedId = 0, resultId = 0, sentAt = 0;
uint32_t blueAt = 0, greenAt = 0;
bool awaitingAck = false, blueOn = false, greenOn = false;
char command[64];
size_t used = 0;
bool overflowed = false;

uint32_t checksum(const uint8_t *data, uint32_t length) {
    uint32_t hash = 2166136261u;
    for (uint32_t i = 0; i < length; ++i) hash = (hash ^ data[i]) * 16777619u;
    return hash;
}

bool number(const char *&p, uint32_t &out, char end) {
    if (*p < '0' || *p > '9') return false;
    uint32_t value = 0;
    while (*p >= '0' && *p <= '9') {
        uint32_t digit = *p++ - '0';
        if (value > (UINT32_MAX - digit) / 10) return false;
        value = value * 10 + digit;
    }
    if (*p != end) return false;
    if (end) ++p;
    out = value;
    return true;
}

void status() {
    if (xSemaphoreTake(serialLock, 0) != pdTRUE) return;
    taskENTER_CRITICAL();
    uint32_t tx = currentId, rx = receivedId, result = resultId;
    bool isBusy = busy;
    bool blue = digitalRead(LED_B) == HIGH, green = digitalRead(LED_G) == HIGH;
    taskEXIT_CRITICAL();
    Serial.print("STATUS,SOURCE=AMEBA,MODE=FOOT10,TX="); Serial.print(tx);
    Serial.print(",RX_ID="); Serial.print(rx);
    Serial.print(",RESULT_ID="); Serial.print(result);
    Serial.print(",BLUE="); Serial.print(blue ? "ON" : "OFF");
    Serial.print(",GREEN="); Serial.print(green ? "ON" : "OFF");
    Serial.print(",BUSY="); Serial.println(isBusy ? "ON" : "OFF");
    xSemaphoreGive(serialLock);
}

void error(const char *text) {
    if (xSemaphoreTake(serialLock, 0) != pdTRUE) return;
    Serial.print("ERROR,"); Serial.println(text);
    xSemaphoreGive(serialLock);
}

void captureTask(void *) {
    for (;;) {
        xSemaphoreTake(captureSignal, portMAX_DELAY);
        uint32_t address = 0, length = 0;
        // SDK getImage can block if the camera fails. Host times out and asks for RESET.
        Camera.getImage(JPEG_CHANNEL, &address, &length);
        if (!address || !length || length > MAX_JPEG) {
            taskENTER_CRITICAL(); busy = false; taskEXIT_CRITICAL();
            error("JPEG_SIZE");
            continue;
        }
        const uint8_t *data = (const uint8_t *)address;
        uint32_t hash = checksum(data, length);
        taskENTER_CRITICAL();
        if (++nextId == 0) ++nextId;
        uint32_t id = nextId;
        currentId = id; currentChecksum = hash;
        sentAt = millis(); awaitingAck = true;
        taskEXIT_CRITICAL();
        xSemaphoreTake(serialLock, portMAX_DELAY);
        Serial.print("JPEG,MODE=FOOT10,TX="); Serial.print(id);
        Serial.print(",LENGTH="); Serial.print(length);
        Serial.print(",CHECKSUM="); Serial.println(hash);
        Serial.write(data, length);
        Serial.println(); Serial.flush();
        taskENTER_CRITICAL(); busy = false; taskEXIT_CRITICAL();
        xSemaphoreGive(serialLock);
    }
}

void handle(const char *text) {
    if (strcmp(text, "STATUS?") == 0) { status(); return; }
    if (strcmp(text, "CAPTURE") == 0) {
        taskENTER_CRITICAL();
        bool occupied = busy;
        if (!occupied) {
            busy = true; awaitingAck = false; blueOn = greenOn = false;
            receivedId = resultId = 0;
            digitalWrite(LED_B, LOW); digitalWrite(LED_G, LOW);
        }
        taskEXIT_CRITICAL();
        if (occupied) error("BUSY");
        else xSemaphoreGive(captureSignal);
        return;
    }
    bool isAck = strncmp(text, "ACK,", 4) == 0;
    bool isResult = strncmp(text, "RESULT,", 7) == 0;
    if (isAck || isResult) {
        const char *p = text + (isAck ? 4 : 7);
        uint32_t id = 0, value = 0;
        if (!number(p, id, ',') || !number(p, value, '\0')) { error("BAD_COMMAND"); return; }
        taskENTER_CRITICAL();
        bool accepted = false;
        if (isAck && awaitingAck && id == currentId && value == currentChecksum &&
            millis() - sentAt <= 90000) {
            receivedId = id; awaitingAck = false;
            blueOn = true; blueAt = millis(); digitalWrite(LED_B, HIGH);
            accepted = true;
        } else if (isResult && !busy && id != 0 && id == currentId && id == receivedId && value <= 1) {
            resultId = value ? id : 0;
            greenOn = value == 1; greenAt = millis();
            digitalWrite(LED_G, greenOn ? HIGH : LOW);
            accepted = true;
        }
        taskEXIT_CRITICAL();
        if (accepted) status(); else error("ID_OR_CHECKSUM_MISMATCH");
        return;
    }
    error("UNKNOWN_COMMAND");
}

void setup() {
    pinMode(LED_G, OUTPUT); pinMode(LED_B, OUTPUT);
    digitalWrite(LED_G, LOW); digitalWrite(LED_B, LOW);
    Serial.begin(115200);
    serialLock = xSemaphoreCreateMutex(); captureSignal = xSemaphoreCreateBinary();
    if (!serialLock || !captureSignal) {
        Serial.println("ERROR,MEMORY"); while (true) delay(1000);
    }
    footJpegConfig.setJpegQuality(2);
    Camera.configVideoChannel(JPEG_CHANNEL, footJpegConfig);
    Camera.videoInit(); Camera.channelBegin(JPEG_CHANNEL);
    if (xTaskCreate(captureTask, "foot_jpeg", 4096, NULL, tskIDLE_PRIORITY + 1, NULL) != pdPASS) {
        Serial.println("ERROR,CAPTURE_TASK"); while (true) delay(1000);
    }
    Serial.println("READY,AMEBA_FOOT10");
}

void loop() {
    taskENTER_CRITICAL();
    uint32_t now = millis();
    if (blueOn && now - blueAt >= 3000) { blueOn = false; digitalWrite(LED_B, LOW); }
    if (greenOn && now - greenAt >= 5000) { greenOn = false; digitalWrite(LED_G, LOW); }
    if (awaitingAck && now - sentAt > 90000) awaitingAck = false;
    taskEXIT_CRITICAL();
    while (Serial.available()) {
        char ch = Serial.read();
        if (ch == '\r') continue;
        if (ch == '\n') {
            command[used] = 0;
            if (overflowed) error("COMMAND_TOO_LONG"); else if (used) handle(command);
            used = 0; overflowed = false;
        } else if (!overflowed && used < sizeof(command) - 1) command[used++] = ch;
        else overflowed = true;
    }
    static uint32_t lastStatus = 0;
    if (millis() - lastStatus >= 1000) { status(); lastStatus = millis(); }
    delay(5);
}
