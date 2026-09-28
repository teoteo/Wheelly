// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// Wheelly - how much current the clutch wants, asked of the clutch.
//
//     cd firmware && ./flash.sh torque_test
//
// How much torque it takes is not something the arithmetic knows: the disc
// knows. This bench climbs in steps from today's current to the motor's rating,
// and holds the motor turning long enough at each step for a hand to resist the
// clutch and feel when it stops slipping.
//
// THE MOTOR SAYS WHICH STEP IT IS ON. Whoever runs this is at the wheel, not at
// the terminal, so before each step the motor makes as many NUDGES as the step
// number: one nudge on the first current, two on the second, and so on. They
// can be counted by ear, or with a hand on the disc, without looking at
// anything.
//
//     1 nudge  -> 150 mA  (as it is today)      4 nudges -> 300 mA
//     2 nudges -> 200 mA                        5 nudges -> 350 mA
//     3 nudges -> 250 mA
//
// Then, at each step: four seconds one way and four the other, so the disc ends
// up roughly where it started and the hand gets to try both directions.
//
// IT STOPS AT 350 mA, a notch below the 400 the 14HS10-0404S is rated for.
// The margin costs nothing: if the clutch still slips
// at 350 the answer is not the last fifty milliampere, it is the spring
// preload, because the slipping threshold is set by the preload and not by the
// motor.
//
// Heat is not a problem HERE but it has to be known: at 350 mA the motor burns
// 2 x 0.35^2 x 30 = 7.4 W, against 1.35 today. In service that lasts the two
// seconds of a move, because the hold current is zero and the motor is let go.
// Here it lasts eight seconds per step, which the motor absorbs without warming
// up. It would be a different matter with a hold current on.

#include <TMCStepper.h>

// The pins, from the board as it is wired: same source as the real firmware,
// mechanics/wheelly-cad/src/wiring.py.
static const int PIN_STEP = 1;      // D0
static const int PIN_DIR = 2;       // D1
static const int PIN_EN = 4;        // D3, active low
static const int PIN_UART_TX = 7;   // D8, behind R2
static const int PIN_UART_RX = 8;   // D9, straight

static const float R_SENSE_OHM = 0.110f;   // marked R110 on the module
static const uint16_t MICROSTEPS = 16;

// The steps. The first one is today's current, because a test that does not
// start from where you are cannot tell you whether anything got better.
static const uint16_t CURRENT_STEPS[] = {150, 200, 250, 300, 350};
static const int CURRENT_STEP_COUNT = sizeof(CURRENT_STEPS) / sizeof(CURRENT_STEPS[0]);

static const uint32_t HALF_PERIOD_US = 300;   // ~26 rpm at the shaft
static const uint32_t DURATION_PER_DIR_MS = 4000;

TMC2208Stepper driver(&Serial1, R_SENSE_OHM);

static void step_pulse()
{
    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(3);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(HALF_PERIOD_US);
}

// Turns for a given time, and half way through reads the driver.
static void turn(bool forward, uint32_t duration_ms, bool report)
{
    digitalWrite(PIN_DIR, forward ? HIGH : LOW);
    delayMicroseconds(100);
    const uint32_t end = millis() + duration_ms;
    const uint32_t half = millis() + duration_ms / 2;
    bool said = false;
    while ((int32_t)(end - millis()) > 0) {
        step_pulse();
        if (report && !said && (int32_t)(half - millis()) <= 0) {
            said = true;
            Serial.print("#   moving: CS=");
            Serial.print(driver.cs_actual());
            Serial.print("/31");
            if (driver.ot())   Serial.print("  OVER TEMPERATURE");
            if (driver.otpw()) Serial.print("  temperature pre-warning");
            Serial.println();
        }
    }
}

// The nudges that say which step we are on. An eighth of a turn each, with a
// clean pause between: countable with a hand on the disc.
static void skips(int count)
{
    for (int s = 0; s < count; s++) {
        digitalWrite(PIN_DIR, HIGH);
        delayMicroseconds(100);
        for (int i = 0; i < 25 * (int)MICROSTEPS; i++) step_pulse();
        delay(350);
    }
    delay(1200);   // long pause: the nudges end here and the pull begins
}

void setup()
{
    Serial.begin(115200);
    const uint32_t end = millis() + 2500;
    while (!Serial && (int32_t)(end - millis()) > 0) { }

    pinMode(PIN_EN, OUTPUT);
    digitalWrite(PIN_EN, HIGH);
    pinMode(PIN_STEP, OUTPUT);
    pinMode(PIN_DIR, OUTPUT);
    digitalWrite(PIN_STEP, LOW);

    Serial.println();
    Serial.println("# ====================================================");
    Serial.println("# Wheelly - how much current the clutch wants");
    Serial.println("# Count the NUDGES: as many as the step number.");
    Serial.println("# 1=150  2=200  3=250  4=300  5=350 mA");
    Serial.println("# ====================================================");

    Serial1.begin(115200, SERIAL_8N1, PIN_UART_RX, PIN_UART_TX);
    delay(10);
    driver.begin();

    const uint8_t silicon = driver.version();
    if (silicon != 0x20 && silicon != 0x21) {
        Serial.println("# the driver does not answer: 12 V on? see driver_test.");
        return;
    }

    driver.I_scale_analog(false);
    driver.en_spreadCycle(false);
    driver.microsteps(MICROSTEPS);
    driver.toff(5);

    digitalWrite(PIN_EN, LOW);
    delay(50);

    for (int g = 0; g < CURRENT_STEP_COUNT; g++) {
        driver.rms_current(CURRENT_STEPS[g]);
        delay(20);
        Serial.print("# step ");
        Serial.print(g + 1);
        Serial.print(": asked for ");
        Serial.print(CURRENT_STEPS[g]);
        Serial.print(" mA, the driver makes ");
        Serial.print(driver.rms_current());
        Serial.println(" mA");

        skips(g + 1);
        turn(true, DURATION_PER_DIR_MS, true);
        delay(500);
        turn(false, DURATION_PER_DIR_MS, false);
        delay(1500);
    }

    driver.rms_current(CURRENT_STEPS[0]);     // left as it was
    digitalWrite(PIN_EN, HIGH);
    Serial.println("# end: motor released, current back to 150 mA.");
    Serial.println("# At which step did the clutch stop slipping?");
}

void loop()
{
    delay(1000);
}
