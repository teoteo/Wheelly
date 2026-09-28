// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// Wheelly - AS5600 air-gap test
//
// Decides how high the sensor board sits above the magnet. It is not chosen
// on paper: read the AGC, the gain the chip sets to adapt to the field it
// receives, and keep the height that brings it to mid-scale. There the magnet
// can move a little closer or further without the reading getting worse.
//
// At 3.3 V the AGC goes from 0 to 128, so the target is 64. At 5 V it would go
// from 0 to 255 and the target would be 128: power it at 3.3 V, as designed.
// AGC going down = stronger field (magnet closer).
//
// Wiring, ESP32 WROOM-32 (the XIAO works too). The labels are the ones
// silk-screened on the module: six pads in a row on one edge, and three larger
// ones on the opposite edge.
//
//     AS5600 module        ESP32 WROOM-32
//     GND .............    GND
//     5V ..............    3V3          <- it is called 5V, but runs on 3.3
//     SDA .............    GPIO 21
//     SCL .............    GPIO 22      <- silk-screened "SOL", it is SCL
//     DIR .............    GND          <- counting direction
//     PGO .............    NOTHING      <- programming pin: do not touch it
//     PWM (opposite edge)  nothing      <- analogue output, here we read I2C
//
// If the chip does not answer: with a meter, module unpowered, the chip's
// VDD5V and VDD3V3 pins must read as connected, otherwise it will not start at
// 3.3 V. In that case add a jumper - and from then on that module runs at 3.3 V
// only.
//
// Commands on the serial monitor (115200):
//     r   reset the minima and maxima, to start a new turn
//     s   print the summary of the turn
//
// Every line is CSV: it can be pasted into a spreadsheet.

#include <Wire.h>

static const uint8_t PIN_SDA = 21;
static const uint8_t PIN_SCL = 22;

static const uint8_t AS5600 = 0x36;
static const uint8_t REG_STATUS    = 0x0B;   // MD / ML / MH
static const uint8_t REG_RAW_ANGLE = 0x0C;   // 12 bit, MSB first
static const uint8_t REG_AGC       = 0x1A;   // 1 byte
static const uint8_t REG_MAGNITUDE = 0x1B;   // 12 bit

static const uint32_t PERIOD_MS = 50;       // 20 readings per second

// The AGC scale depends on how the chip is powered: 0-128 at 3.3 V, 0-255 at
// 5 V. Start from the designed case and change our mind if a reading above 128
// arrives, which cannot exist at 3.3 V.
static uint16_t scale = 128;

// minima and maxima of the current turn
static uint8_t  agc_min, agc_max;
static uint16_t mag_min, mag_max;
static uint32_t samples;
static uint32_t agc_sum;
static bool     seen_ml, seen_mh, lost_md;

static bool read_reg(uint8_t reg, uint8_t *buf, uint8_t n) {
  Wire.beginTransmission(AS5600);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((int)AS5600, (int)n) != n) return false;
  for (uint8_t i = 0; i < n; i++) buf[i] = Wire.read();
  return true;
}

static bool read8(uint8_t reg, uint8_t *v) { return read_reg(reg, v, 1); }

static bool read12(uint8_t reg, uint16_t *v) {
  uint8_t b[2];
  if (!read_reg(reg, b, 2)) return false;
  *v = (((uint16_t)b[0] << 8) | b[1]) & 0x0FFF;
  return true;
}

static void reset_turn() {
  agc_min = 255; agc_max = 0;
  mag_min = 0xFFFF; mag_max = 0;
  samples = 0; agc_sum = 0;
  seen_ml = seen_mh = lost_md = false;
}

static void summary() {
  if (samples == 0) { Serial.println("# no samples"); return; }
  const uint16_t target = (scale + 1) / 2;    // 64 at 3.3 V, 128 at 5 V
  Serial.println("#");
  Serial.printf("# turn over %lu samples\n", (unsigned long)samples);
  if (scale == 255)
    Serial.println("#   ! readings above 128: the module is in 5 V mode, not 3.3."
                   " Scale 0-255 and target 128; the real assembly runs at 3.3 V");
  Serial.printf("#   AGC    min %3u  mean %3lu  max %3u   (target %u, scale 0-%u)\n",
                agc_min, (unsigned long)(agc_sum / samples), agc_max, target, scale);
  Serial.printf("#   AGC swing over the turn: %u\n", (unsigned)(agc_max - agc_min));
  Serial.printf("#   MAGNITUDE  min %u  max %u\n", mag_min, mag_max);
  if (lost_md) Serial.println("#   ! MD dropped: the chip lost the magnet");
  if (seen_ml) Serial.println("#   ! ML: field too weak, move closer (lower foot)");
  if (seen_mh) Serial.println("#   ! MH: field too strong, move away (higher foot)");
  if (!lost_md && !seen_ml && !seen_mh) {
    if (agc_max - agc_min > scale / 6)
      Serial.println("#   AGC wobbles over the turn: magnet off-centre, or not flat");
    else if (agc_min < scale / 4 || agc_max > scale * 3 / 4)
      Serial.println("#   AGC far from mid-scale: try the next foot");
    else
      Serial.println("#   good: AGC in the middle half and steady over the turn");
  }
  Serial.println("#");
}

void setup() {
  Serial.begin(115200);
  delay(300);
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(400000);

  Serial.println();
  Serial.println("# Wheelly - AS5600 air-gap test");
  Wire.beginTransmission(AS5600);
  if (Wire.endTransmission() == 0) {
    Serial.println("# AS5600 found at 0x36");
  } else {
    Serial.println("# ! no answer at 0x36: check 3V3, GND, SDA=21, SCL=22");
    Serial.println("#   and that VDD5V and VDD3V3 are connected on the module");
  }
  reset_turn();
  Serial.println("# commands:  r = reset the turn,  s = summary");
  Serial.println("ms,angle_deg,raw,agc,magnitude,MD,ML,MH");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'r') { reset_turn(); Serial.println("# reset: turn the wheel one full turn"); }
    if (c == 's') summary();
  }

  static uint32_t next_ms = 0;
  if (millis() < next_ms) return;
  next_ms = millis() + PERIOD_MS;

  uint8_t status, agc;
  uint16_t raw, mag;
  static uint32_t silent = 0;        // failed readings in a row
  if (!read8(REG_STATUS, &status) || !read8(REG_AGC, &agc) ||
      !read12(REG_RAW_ANGLE, &raw) || !read12(REG_MAGNITUDE, &mag)) {
    // With no sensor attached it fails twenty times a second: say it once,
    // then every five seconds, otherwise the message buries everything else.
    if (silent == 0 || silent % 100 == 0)
      Serial.println("# ! the AS5600 does not answer: check 3V3, GND, SDA=21, SCL=22,"
                     " and that VDD5V and VDD3V3 are connected on the module");
    silent++;
    return;
  }
  if (silent) { Serial.println("# AS5600 answers"); silent = 0; }
  if (agc > 128) scale = 255;      // at 3.3 V the AGC cannot get there: it is in 5 V mode

  bool md = status & 0x20;   // magnet detected
  bool ml = status & 0x10;   // too weak
  bool mh = status & 0x08;   // too strong

  if (agc < agc_min) agc_min = agc;
  if (agc > agc_max) agc_max = agc;
  if (mag < mag_min) mag_min = mag;
  if (mag > mag_max) mag_max = mag;
  agc_sum += agc;
  samples++;
  if (!md) lost_md = true;
  if (ml)  seen_ml = true;
  if (mh)  seen_mh = true;

  Serial.printf("%lu,%.2f,%u,%u,%u,%d,%d,%d\n",
                (unsigned long)millis(), raw * 360.0 / 4096.0, raw, agc, mag,
                md ? 1 : 0, ml ? 1 : 0, mh ? 1 : 0);
}
