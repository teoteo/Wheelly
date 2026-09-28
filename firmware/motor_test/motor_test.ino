// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// Wheelly - does the motor turn, and are the phases paired right?
//
//     cd firmware && ./flash.sh motor_test
//
// The real firmware does NOT move without the sensor, and it is right to
// refuse: `go` answers ERR_SENSOR_SILENT, because a wheel that does not know
// where it is has no business turning blind. This bench is for the moment
// before that - the sensor not wired yet, and the question is whether the power
// side works at all.
//
// WHAT ONLY A TURNING MOTOR SHOWS is a pair of phases wired across. The four
// driver outputs are not four wires: they are two PAIRS, A with A and B with B.
// Break a pair on the four-way connector - A+ with B+, A- with B- - and the
// motor does not turn: it buzzes, warms up and stays put, and no register of
// the driver notices, because as far as it can tell two coils are connected.
// Eyes are the only instrument for this one. The right pairs on the
// 14HS10-0404S are BLACK+GREEN and RED+BLUE.
//
// What it does, in order: configures the driver the way the firmware does,
// turns one whole revolution one way, stops, and does it again the other way.
// Half way through each turn it reads DRV_STATUS and says what it found.
//
// BEFORE RUNNING IT:
//   - the motor MUST be connected. Unplugging it with 12 V in kills the driver
//     instantly, so it goes in before the power, not after;
//   - 12 V on, or the chip is off and will not answer;
//   - if the wheel is assembled, IT WILL TURN. Not a token nudge: 200 full
//     steps, one revolution of the motor shaft.

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
static const uint16_t STEPS_PER_TURN = 200;    // the 14HS10 is a 1.8 degree motor
static const uint16_t CURRENT_MA = 150;

// One microstep every 600 us: about 26 rpm, slow enough to hear the motor lose
// steps and to see which way it goes.
static const uint32_t HALF_PERIOD_US = 300;

TMC2208Stepper driver(&Serial1, R_SENSE_OHM);

static void report_state(const char *when)
{
    Serial.print("# DRV_STATUS ");
    Serial.print(when);
    Serial.print(":  CS=");
    Serial.print(driver.cs_actual());
    Serial.print("/31");
    if (driver.ot())   Serial.print("  OVER TEMPERATURE");
    if (driver.otpw()) Serial.print("  temperature pre-warning");
    if (driver.s2ga()) Serial.print("  SHORT TO GROUND on phase A");
    if (driver.s2gb()) Serial.print("  SHORT TO GROUND on phase B");
    if (driver.ola())  Serial.print("  coil A open?");
    if (driver.olb())  Serial.print("  coil B open?");
    if (driver.stst()) Serial.print("  standstill");
    Serial.println();
}

static void turn(bool forward, uint16_t full_steps)
{
    digitalWrite(PIN_DIR, forward ? HIGH : LOW);
    delayMicroseconds(100);          // the driver wants DIR settled before STEP

    const uint32_t total = (uint32_t)full_steps * MICROSTEPS;
    const uint32_t half = total / 2;
    for (uint32_t i = 0; i < total; i++) {
        digitalWrite(PIN_STEP, HIGH);
        delayMicroseconds(3);
        digitalWrite(PIN_STEP, LOW);
        delayMicroseconds(HALF_PERIOD_US);
        // Half way, i.e. while moving: the open-coil flags mean something only
        // while current is actually flowing. At standstill the driver raises
        // them anyway, and they would be a false alarm.
        if (i == half) report_state("while moving");
    }
}

void setup()
{
    Serial.begin(115200);
    const uint32_t end = millis() + 2500;
    while (!Serial && (int32_t)(end - millis()) > 0) { }

    pinMode(PIN_EN, OUTPUT);
    digitalWrite(PIN_EN, HIGH);      // off until it is configured
    pinMode(PIN_STEP, OUTPUT);
    pinMode(PIN_DIR, OUTPUT);
    digitalWrite(PIN_STEP, LOW);

    Serial.println();
    Serial.println("# ====================================================");
    Serial.println("# Wheelly - does the motor turn?");
    Serial.println("# WATCH THE SHAFT. Buzzing but not turning means the two");
    Serial.println("# phases are paired across: black+green and red+blue.");
    Serial.println("# ====================================================");

    Serial1.begin(115200, SERIAL_8N1, PIN_UART_RX, PIN_UART_TX);
    delay(10);
    driver.begin();

    const uint8_t silicon = driver.version();
    Serial.print("# silicon: 0x");
    Serial.print(silicon, HEX);
    Serial.println(silicon == 0x20 ? "  (TMC2208)"
                 : silicon == 0x21 ? "  (TMC2209)" : "  UNKNOWN");
    if (silicon != 0x20 && silicon != 0x21) {
        Serial.println("# the driver does not answer: are the 12 V on?");
        Serial.println("# for the real diagnosis run driver_test: it says where it breaks.");
        return;
    }

    driver.I_scale_analog(false);    // no VREF: the current comes from Rsense
    driver.en_spreadCycle(false);    // StealthChop
    driver.microsteps(MICROSTEPS);
    driver.toff(5);
    driver.rms_current(CURRENT_MA);
    Serial.print("# current asked for: ");
    Serial.print(CURRENT_MA);
    Serial.print(" mA, read back from the driver: ");
    Serial.print(driver.rms_current());
    Serial.println(" mA");

    report_state("before starting");

    digitalWrite(PIN_EN, LOW);       // enabled
    delay(50);

    Serial.println("# one turn forward (200 full steps)...");
    turn(true, STEPS_PER_TURN);
    delay(500);
    report_state("stopped after the turn");

    Serial.println("# ...and one back");
    turn(false, STEPS_PER_TURN);
    delay(500);

    digitalWrite(PIN_EN, HIGH);      // released: at rest the motor runs free
    report_state("released");
    Serial.println("# end. If the shaft made two opposite turns, the power side");
    Serial.println("# and the phase pairing are both good.");
}

void loop()
{
    delay(1000);
}
