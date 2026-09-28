// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// Wheelly - does the LED pulse the way its CodePen pen does, on the real LED?
//
//     cd firmware && ./flash.sh led_test
//
// The real firmware pulses the LED only while the wheel goes to another slot,
// and it will not start a move without the sensor and the magnet. WHEN it
// pulses is proven on the PC (test/test_pulse.cpp, fake clock); what
// only the board shows is HOW it looks - the PWM, and the eye correction.
//
// This is not a copy of the firmware: src/wheelly is a link to the firmware's
// own sources, and the level comes from the same pulse_level() and goes
// out through the same MechanicsEsp32::led_level() that the XIAO runs.
//
// Round and round: three pulses as the pen (30..100 %), one second off, three
// pulses at 10..50 %, three at 5..30 % (each followed by one second off),
// then one second steady ON and one OFF.
// The on/off part is not decoration: in the 3.x core a pin attached to LEDC
// ignores digitalWrite, so on/off after a pulse is exactly what used to break.
//
// Nothing moves: the motor is never commanded. 12 V are not needed.

#include "src/wheelly/mechanics_esp32.h"
#include "src/wheelly/dialog.h"

using namespace wheelly;

static Pins pins;
static MechanicsEsp32 mechanics(pins);

void setup()
{
    Serial.begin(115200);
    mechanics.begin();
}

static void three_pulses(float lo, float hi)
{
    Serial.printf("pulse x3, %.0f%% .. %.0f%%\n", lo * 100, hi * 100);
    const uint32_t from = millis();
    while (millis() - from < 3 * PULSE_PERIOD_MS) {
        mechanics.led_level(pulse_level(millis() - from, lo, hi));
        delay(10);
    }
    mechanics.led(false);
    delay(1000);
}

void loop()
{
    // A: the pen (the firmware's defaults); B: 10..50 % and C: 5..30 %, to
    // see the difference on the real LED
    three_pulses(PULSE_MIN_LIGHT, PULSE_MAX_LIGHT);
    three_pulses(0.10f, 0.50f);
    three_pulses(0.05f, 0.30f);
    Serial.println("steady ON");
    mechanics.led(true);
    delay(1000);
    Serial.println("OFF");
    mechanics.led(false);
    delay(1000);
}
