#include <Arduino.h>
#include <DHT.h>
#include <RCSwitch.h>

// ── Sensor pins (ESP32-S3) — see PINOUT.md ────────────────────────────────
#define PIN_MQ2     1
#define PIN_MQ7     2
#define PIN_MQ135   4
#define PIN_KY037   5
#define PIN_DHT11   7
#define PIN_RF_RX   8

// ── SIM808 pins ───────────────────────────────────────────────────────────
#define SIM_TX      38   // ESP32 TX → SIM808 RXD
#define SIM_RX      39   // ESP32 RX → SIM808 TXD
#define SIM_PWRKEY  40

// ── Config ────────────────────────────────────────────────────────────────
#define DEVICE_ID   "esp32-car-001"
#define APN         "internet.mic1.com.lb"
#define APN_USER    "mic1"
#define APN_PASS    "mic1"
#define SERVER_URL  "https://apothecial-emmalynn-preluxuriously.ngrok-free.dev/debug/ingest"
#define PHONE_NUMBER "+961XXXXXXXX"   // ← your phone number in international format

DHT dht(PIN_DHT11, DHT11);
RCSwitch rf;
HardwareSerial sim808(1);   // UART1

// ─────────────────────────────────────────────────────────────────────────
// ADC helper — averages N samples with a settling gap between channel reads
// ─────────────────────────────────────────────────────────────────────────
int adcRead(int pin, int samples = 16) {
  long sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(5);
  }
  return sum / samples;
}

// ─────────────────────────────────────────────────────────────────────────
// Threshold functions — TODO: re-calibrate after gas exposure tests
// ─────────────────────────────────────────────────────────────────────────
const char* smokeLevel(int raw) {
  if (raw < 800)  return "LOW";
  if (raw < 2000) return "MEDIUM";
  return "HIGH";
}

const char* coLevel(int raw) {
  if (raw < 1500) return "LOW";
  if (raw < 2500) return "MEDIUM";
  return "HIGH";
}

const char* airQuality(int raw) {
  if (raw < 1000) return "GOOD";
  if (raw < 2000) return "MODERATE";
  if (raw < 3000) return "POOR";
  return "HAZARDOUS";
}

// ─────────────────────────────────────────────────────────────────────────
// SIM808 helpers
// ─────────────────────────────────────────────────────────────────────────

String simCmd(const char* cmd, int timeout = 2000) {
  while (sim808.available()) sim808.read();  // flush
  sim808.println(cmd);
  long start = millis();
  String resp = "";
  while (millis() - start < timeout) {
    while (sim808.available()) resp += (char)sim808.read();
    if (resp.indexOf("OK") != -1 || resp.indexOf("ERROR") != -1) break;
  }
  Serial.printf("[SIM808] >> %s\n[SIM808] << %s\n", cmd, resp.c_str());
  return resp;
}

bool simWaitFor(const char* target, int timeout = 5000) {
  long start = millis();
  String buf = "";
  while (millis() - start < timeout) {
    while (sim808.available()) buf += (char)sim808.read();
    if (buf.indexOf(target) != -1) return true;
  }
  return false;
}

void sim808PowerOn() {
  sim808.println("AT");
  if (simWaitFor("OK", 1000)) {
    Serial.println("[SIM808] Already on.");
    return;
  }
  Serial.println("[SIM808] Powering on...");
  digitalWrite(SIM_PWRKEY, LOW);
  delay(1200);
  digitalWrite(SIM_PWRKEY, HIGH);
  simWaitFor("Call Ready", 10000);
  Serial.println("[SIM808] Ready.");
}

bool initGPRS() {
  simCmd("ATE0");          // disable echo — required for clean response parsing
  simCmd("AT");
  simCmd("AT+CFUN=1");

  // Wait for network registration — can take 30-60 s on first power-on
  Serial.println("[SIM808] Waiting for network...");
  bool registered = false;
  for (int i = 0; i < 30; i++) {
    String r = simCmd("AT+CREG?", 3000);
    // +CREG: 0,1 = home  |  +CREG: 0,5 = roaming
    if (r.indexOf("+CREG: 0,1") != -1 || r.indexOf("+CREG: 0,5") != -1) {
      Serial.println("[SIM808] Network registered.");
      registered = true;
      break;
    }
    Serial.printf("[SIM808] Not registered yet (%d/30)...\n", i + 1);
    delay(3000);
  }
  if (!registered) {
    Serial.println("[SIM808] Network registration failed.");
    return false;
  }

  simCmd("AT+SAPBR=0,1", 5000);   // close any stale bearer first
  delay(1000);
  simCmd("AT+SAPBR=3,1,\"Contype\",\"GPRS\"");
  simCmd("AT+SAPBR=3,1,\"APN\",\"" APN "\"");
  simCmd("AT+SAPBR=3,1,\"USER\",\"" APN_USER "\"");
  simCmd("AT+SAPBR=3,1,\"PWD\",\"" APN_PASS "\"");
  simCmd("AT+SAPBR=1,1", 15000);   // open bearer — give it more time

  String status = simCmd("AT+SAPBR=2,1");
  bool ok = status.indexOf("1,1") != -1;
  Serial.println(ok ? "[SIM808] GPRS up." : "[SIM808] GPRS failed.");
  return ok;
}

bool httpPost(const char* url, const String& json) {
  // Re-open bearer if it dropped since startup
  String bearerStatus = simCmd("AT+SAPBR=2,1");
  if (bearerStatus.indexOf("1,1") == -1) {
    Serial.println("[SIM808] Bearer down — reconnecting...");
    if (!initGPRS()) return false;
  }

  simCmd("AT+HTTPSSL=1");   // enable SSL for https://
  simCmd("AT+HTTPTERM");
  delay(300);

  if (simCmd("AT+HTTPINIT").indexOf("OK") == -1) return false;
  simCmd("AT+HTTPPARA=\"CID\",1");

  String urlCmd = "AT+HTTPPARA=\"URL\",\"";
  urlCmd += url;
  urlCmd += "\"";
  simCmd(urlCmd.c_str());

  simCmd("AT+HTTPPARA=\"CONTENT\",\"application/json\"");
  simCmd("AT+HTTPPARA=\"USERDATA\",\"ngrok-skip-browser-warning: true\\r\\n\"");

  String dataCmd = "AT+HTTPDATA=" + String(json.length()) + ",10000";
  sim808.println(dataCmd);
  if (!simWaitFor("DOWNLOAD", 3000)) {
    simCmd("AT+HTTPTERM");
    return false;
  }
  sim808.print(json);
  delay(500 + json.length() / 20);

  // Capture the full +HTTPACTION response so we can read the status code
  while (sim808.available()) sim808.read();   // flush
  sim808.println("AT+HTTPACTION=1");
  long actionStart = millis();
  String actionResp = "";
  while (millis() - actionStart < 20000) {
    while (sim808.available()) actionResp += (char)sim808.read();
    if (actionResp.indexOf("+HTTPACTION") != -1 &&
        actionResp.indexOf("\n") != -1) break;
  }
  Serial.println("[SIM808] HTTPACTION: " + actionResp);

  // 200 OK or 201 Created = success
  bool ok = actionResp.indexOf("+HTTPACTION: 1,200") != -1 ||
            actionResp.indexOf("+HTTPACTION: 1,201") != -1;

  delay(500);
  simCmd("AT+HTTPREAD");
  simCmd("AT+HTTPTERM");
  return ok;
}

// ─────────────────────────────────────────────────────────────────────────
// Build JSON payload
// ─────────────────────────────────────────────────────────────────────────
String buildJson(float temp, float hum, int mq2, int mq7, int mq135) {
  char buf[300];
  snprintf(buf, sizeof(buf),
    "{\"device_id\":\"%s\","
    "\"temperature\":%.1f,"
    "\"humidity\":%.1f,"
    "\"smokeLevel\":\"%s\","
    "\"airQuality\":\"%s\","
    "\"coLevel\":\"%s\","
    "\"latitude\":0.0,"
    "\"longitude\":0.0}",
    DEVICE_ID, temp, hum,
    smokeLevel(mq2),
    airQuality(mq135),
    coLevel(mq7)
  );
  return String(buf);
}

// ─────────────────────────────────────────────────────────────────────────
// SMS sender
// ─────────────────────────────────────────────────────────────────────────
String buildSMS(float temp, float hum, int mq2, int mq7, int mq135) {
  char buf[160];
  snprintf(buf, sizeof(buf),
    "[Car Safety]\nT:%.1fC H:%.0f%%\nSmoke:%s\nCO:%s\nAir:%s",
    temp, hum,
    smokeLevel(mq2),
    coLevel(mq7),
    airQuality(mq135)
  );
  return String(buf);
}

bool sendSMS(const char* number, const String& msg) {
  simCmd("AT+CMGF=1");
  delay(500);

  String cmd = "AT+CMGS=\"";
  cmd += number;
  cmd += "\"";

  while (sim808.available()) sim808.read();   // flush
  Serial.printf("[SIM808] >> %s\n", cmd.c_str());
  sim808.println(cmd);

  // Capture whatever the SIM808 sends back (should contain '>')
  long start = millis();
  String buf = "";
  while (millis() - start < 8000) {
    while (sim808.available()) buf += (char)sim808.read();
    if (buf.indexOf(">") != -1) break;
  }
  Serial.printf("[SIM808] << %s\n", buf.c_str());

  if (buf.indexOf(">") == -1) {
    Serial.println("[SIM808] No prompt — check number format or SIM credit");
    return false;
  }

  sim808.print(msg);
  delay(200);
  sim808.write(26);   // Ctrl+Z sends the message

  bool ok = simWaitFor("+CMGS:", 20000);
  Serial.println(ok ? "[SIM808] SMS sent." : "[SIM808] SMS failed.");
  return ok;
}

// ─────────────────────────────────────────────────────────────────────────
// Setup
// ─────────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(1000);

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  dht.begin();
  rf.enableReceive(PIN_RF_RX);

  // SIM808 — TX/RX swapped from original; revert if no response in passthrough
  pinMode(SIM_PWRKEY, OUTPUT);
  digitalWrite(SIM_PWRKEY, HIGH);
  sim808.begin(9600, SERIAL_8N1, SIM_TX, SIM_RX);
  delay(1000);

  sim808PowerOn();
  initGPRS();

  Serial.println("\nMQ sensors need ~30 s warm-up — waiting...");
  for (int i = 30; i > 0; i--) {
    Serial.printf("  %d s\r", i);
    delay(1000);
  }
  Serial.println("\nReady.\n");
}

// ─────────────────────────────────────────────────────────────────────────
// Loop
// ─────────────────────────────────────────────────────────────────────────
void loop() {
  const float toVolt = 3.3f / 4095.0f;

  int mq2Raw   = adcRead(PIN_MQ2);
  int mq7Raw   = adcRead(PIN_MQ7);
  int mq135Raw = adcRead(PIN_MQ135);
  int ky037Raw = adcRead(PIN_KY037);

  float temp = dht.readTemperature();
  float hum  = dht.readHumidity();

  Serial.println("──────────────────────────────────────────");
  Serial.printf("MQ2    (smoke)   : %4d / 4095  (%.2f V)\n", mq2Raw,   mq2Raw   * toVolt);
  Serial.printf("MQ7    (CO)      : %4d / 4095  (%.2f V)\n", mq7Raw,   mq7Raw   * toVolt);
  Serial.printf("MQ135  (air)     : %4d / 4095  (%.2f V)\n", mq135Raw, mq135Raw * toVolt);
  Serial.printf("KY037  (sound)   : %4d / 4095  (%.2f V)\n", ky037Raw, ky037Raw * toVolt);

  if (isnan(temp) || isnan(hum)) {
    Serial.println("DHT11            : read error — check wiring");
  } else {
    Serial.printf("DHT11  temp      : %.1f C\n", temp);
    Serial.printf("DHT11  humidity  : %.1f %%\n", hum);
  }

  if (rf.available()) {
    Serial.printf("RF received      : value=%-10lu  bits=%d  protocol=%d\n",
                  rf.getReceivedValue(),
                  rf.getReceivedBitlength(),
                  rf.getReceivedProtocol());
    rf.resetAvailable();
  } else {
    Serial.println("RF               : no signal");
  }

  if (!isnan(temp) && !isnan(hum)) {
    String msg = buildSMS(temp, hum, mq2Raw, mq7Raw, mq135Raw);
    Serial.println("\nSending SMS:\n" + msg);
    sendSMS(PHONE_NUMBER, msg);
  }

  delay(10000);
}
