# ESP32-S3 Pin Assignment — Car Safety Device

## ADC rules on ESP32-S3
- ADC1 → GPIO1–GPIO10   — safe while WiFi is active  ✅
- ADC2 → GPIO11–GPIO20  — blocked by WiFi driver     ❌
- All MQ analog pins must land on ADC1 (GPIO1–GPIO10)

## Strapping / reserved pins — do not use
| GPIO | Reason                        |
|------|-------------------------------|
| 0    | BOOT button                   |
| 3    | JTAG / USB                    |
| 19   | USB D−                        |
| 20   | USB D+                        |
| 45   | VDD_SPI strapping             |
| 46   | ROM log strapping             |

---

## Sensor Pin Table

| Sensor      | Sensor Pin | ESP32-S3 GPIO | Type          | Notes                                      |
|-------------|------------|---------------|---------------|--------------------------------------------|
| MQ2         | AO         | GPIO1         | ADC1_CH0      | Voltage divider required (see below)       |
| MQ2         | DO         | —             | —             | Not used                                   |
| MQ7         | AO         | GPIO2         | ADC1_CH1      | Voltage divider required                   |
| MQ7         | DO         | —             | —             | Not used                                   |
| MQ135       | AO         | GPIO4         | ADC1_CH3      | Voltage divider required                   |
| MQ135       | DO         | —             | —             | Not used                                   |
| KY037       | AO         | GPIO5         | ADC1_CH4      | Sound level — no divider needed (3.3V out) |
| KY037       | DO         | GPIO6         | Digital in    | Sound trigger threshold                    |
| INMP441     | SCK        | GPIO15        | I2S BCLK      |                                            |
| INMP441     | WS         | GPIO16        | I2S LRCLK     |                                            |
| INMP441     | SD         | GPIO17        | I2S Data      |                                            |
| INMP441     | L/R        | GND           | —             | GND = left channel                         |
| DHT11       | DATA       | GPIO7         | Digital 1-wire | 10K pull-up to 3.3V (usually on module)  |
| RF Receiver | DATA       | GPIO8         | Digital in    |                                            |

## SIM808 — Reserved (do NOT solder now, leave pads free)

| SIM808 Pin | ESP32-S3 GPIO | Function         |
|------------|---------------|------------------|
| TXD        | GPIO38        | ESP32 RX (UART1) |
| RXD        | GPIO39        | ESP32 TX (UART1) |
| PWRKEY     | GPIO40        | Power key        |
| RST        | GPIO41        | Reset (optional) |

> SIM808 needs 3.7–4.2V (LiPo cell or dedicated regulator).
> Do NOT power it from ESP32-S3 3.3V or USB 5V directly.

---

## Voltage Divider for MQ Sensors (build 3×)

MQ AO swings 0–5V. ESP32-S3 ADC max is 3.3V.

```
MQ AO ──── 10KΩ ──── ESP32-S3 GPIO (ADC1) ──── 20KΩ ──── GND
```

Output = 5V × 20/(10+20) = **3.33V max** ✓

One divider per MQ sensor between the AO pad and the ADC pin.

---

## GPIO Map (ESP32-S3-DevKitC-1, 44-pin)

```
                        [ USB ]
                 3V3  |       | GND
                 3V3  |       | GPIO43 TX0
                 RST  |       | GPIO44 RX0
   MQ2   ADC1  GPIO1  |       | GPIO1  (same row, left)
   MQ7   ADC1  GPIO2  |       | GPIO2
                GPIO3  |       | GPIO42           ← avoid (strapping)
  MQ135  ADC1  GPIO4  |       | GPIO41  [SIM808 RST  — reserved]
  KY037  AO    GPIO5  |       | GPIO40  [SIM808 PWRKEY — reserved]
  KY037  DO    GPIO6  |       | GPIO39  [SIM808 TXD — reserved]
  DHT11        GPIO7  |       | GPIO38  [SIM808 RXD — reserved]
  RF RX        GPIO8  |       | GPIO37
               GPIO9  |       | GPIO36
               GPIO10 |       | GPIO35
               GPIO11 |       | GPIO21
               GPIO12 |       | GPIO18  (free)
               GPIO13 |       | GPIO17  INMP441 SD
               GPIO14 |       | GPIO16  INMP441 WS
               GPIO15 |       | GPIO15  INMP441 SCK  ← (same pin both sides on some boards)
               GPIO16 |       | GND
               GND    |       | 5V
```

> Exact physical layout varies by board revision.
> Use a multimeter continuity test to confirm GPIO numbers if unsure.
