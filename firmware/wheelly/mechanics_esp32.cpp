// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

#ifdef ARDUINO

#include "mechanics_esp32.h"
#include "wheelly_protocol.h"   // FACTORY_SPEED, FACTORY_ACCEL

#include <Wire.h>

namespace wheelly {

namespace {

// The UART to the driver. The datasheet describes the single wire with a 1 k
// resistor between TX and RX, so everything sent comes straight back: the
// library has to skip its own echo before reading the reply, and TMCStepper
// does - it hunts for the sync byte instead of counting bytes.
//
// The library is TMCStepper and no longer janelia's TMC2209, and the reason is
// written here because the symptom looks like a wiring fault:
// janelia's compares the IOIN version field with 0x21 and declares anything
// else mute. The module in the box is a TMC2208, which answers 0x20 - alive,
// well wired, and reported as silent.
const long BAUD_DRIVER = 115200;

// How often to re-check that the sensor still answers: not at every reading,
// it is asked at every pass of the loop. The motor driver is not on this
// clock: it is asked before every leg (driver_check()), never during one,
// where a round of UART would steal time from the pulses.
const uint32_t CHECK_PERIOD_MS = 1000;

// The sense resistors of the module, READ ON THE PART: both are marked R110,
// i.e. 0,110 ohm. TMCStepper turns milliampere into IRUN from this number, so
// it is the one quote that must never be guessed. Changing driver module means
// re-reading it off the resistors.
const float R_SENSE_OHM = 0.110f;

// The `version` field of IOIN, which is how the chip says what it is. Both are
// accepted: Wheelly uses only what the two have in common - StealthChop,
// microstepping and current over UART - and nothing that is 2209-only.
// StallGuard is not among them and is not missed: the clutch is meant to slip,
// and the reference comes from the AS5600.
const uint8_t SILICON_2208 = 0x20;
const uint8_t SILICON_2209 = 0x21;

// The microstepping (MICROSTEPS, sixteen) lives in mechanics.h, because it fixes the units of the interface: it configures the
// driver here and converts the FULL steps/s of speed() into pulses.

// PWM of the LED. A few kHz is far above any flicker the eye or a camera would
// see. 13 bits keep the bottom of the pulse (dialog.h) - 5 % of brightness,
// 0.14 % of duty after the eye correction - at 11 steps, where 10 bits gave one
// or two and the fade stairs visibly out of the dark.
//
// WHY A TABLE OF TRIES: a LED can stay dark with nobody able to tell. 5 kHz
// at 13 bits "can not be achieved" on the XIAO ESP32-S3 with core 3.3.11 (the LEDC
// clock there is not the 80 MHz this comment used to assume), ledcAttach()
// failed, its result was not looked at, and every "led on" answered ok with
// the pin never attached - 0.03 V measured on a bare XIAO while plain
// digitalWrite on the same pin gave 3.2 V. So the settings are tried in order
// and the first the chip accepts is kept: 13 bits at 4 kHz first (it fits a
// 40 MHz clock), then fewer bits; if none works the LED falls back to plain
// on/off, and `diag` says which.
// TPWMTHRS: StealthChop below about 12 full steps/s, SpreadCycle above (see
// configure_driver). 12 MHz / (12 full steps * 16 microsteps).
const uint32_t STEALTH_BELOW_TSTEP = 12000000UL / (12UL * MICROSTEPS);

struct LedPwm { uint32_t hz; uint8_t bits; };
const LedPwm LED_PWM_TRIES[] = {{5000, 13}, {4000, 13}, {5000, 12}, {5000, 11}, {5000, 10}};

}  // namespace

MechanicsEsp32::MechanicsEsp32(const Pins &pins)
    : m_p(pins), m_driver(&Serial1, R_SENSE_OHM) {}

bool MechanicsEsp32::begin()
{
    // The LED is on LEDC from the start, and on/off goes through LEDC too.
    // It cannot be half and half: in the 3.x core a pin attached to LEDC is
    // no longer a GPIO for the peripheral manager, and a digitalWrite on it
    // does nothing (it only logs an error) - so after the first pulse "led on"
    // and "led off" would have stopped working without a word. Found writing
    // the pulse, before it happened.
    m_led_bits = 0;
    for (const LedPwm &t : LED_PWM_TRIES) {
        if (ledcAttach(m_p.led, t.hz, t.bits)) { m_led_bits = t.bits; break; }
    }
    if (m_led_bits > 0) {
        m_led_max = (1u << m_led_bits) - 1;
        ledcWrite(m_p.led, 0);
    } else {
        pinMode(m_p.led, OUTPUT);       // no PWM at all: on and off still work
        digitalWrite(m_p.led, LOW);
    }

    // --- sensor ----------------------------------------------------------
    Wire.begin(m_p.sda, m_p.scl);
    Wire.setClock(400000);
    m_sensor.begin();
    m_sensor_alive = m_sensor.isConnected();

    // --- motor driver -----------------------------------------------------
    m_driver_alive = configure_driver();

    // --- pulse generator ---------------------------------------------------
    m_engine.init();
    m_stepper = m_engine.stepperConnectToPin(m_p.step);
    if (m_stepper != nullptr) {
        // The DIR pin is inverted (found at the first moves of the assembled
        // wheel): with J1 wired as in the guide (black A+, green A-, red B+,
        // blue B-) and the sensor looking down on the magnet, positive steps
        // turned the disc towards DECREASING angle - every leg moved the
        // wheel away from its target, about 0.92 of the length asked, and
        // looked like a stall. A fact of the design, not of one wheel: whoever
        // wires J1 the other way round must flip it here.
        m_stepper->setDirectionPin(m_p.dir, false);
        m_stepper->setEnablePin(m_p.en, true);   // active low, like the driver
        m_stepper->setAutoEnable(false);         // we decide the enabling ourselves
        // the factory values until Wheel::begin() applies the saved ones
        m_stepper->setSpeedInHz(FACTORY_SPEED * MICROSTEPS);
        m_stepper->setAcceleration(FACTORY_ACCEL * MICROSTEPS);
    }

    enable(false);
    return m_sensor_alive;
}

bool MechanicsEsp32::configure_driver()
{
    // Always the explicit-pins variant: the UART defaults changed with
    // Arduino-ESP32 3.x and leaning on them fails silently.
    Serial1.begin(BAUD_DRIVER, SERIAL_8N1, m_p.uart_rx, m_p.uart_tx);
    delay(10);

    // begin() sets pdn_disable and mstep_reg_select: from here on the UART
    // commands the chip, and MS1/MS2 no longer choose the microstepping. On a
    // TMC2208 that is the only way to reach it - those two pins are not an
    // address, as they are on a 2209.
    m_driver.begin();

    m_silicon = m_driver.version();
    if (m_silicon != SILICON_2208 && m_silicon != SILICON_2209) {
        // Zero, 0xFF and anything else all mean the same thing: nobody is
        // answering on the single wire, or answering something we cannot vouch
        // for. Better mute than configured by guesswork.
        m_silicon = 0;
        return false;
    }

    // VREF OUT OF THE DESIGN. With i_scale_analog on - which is the reset
    // default - the trimmer scales the full-scale current, and the whole chain
    // hangs off a quarter of a volt read with a probe. Turning it off makes the
    // current come from Rsense and IRUN alone: repeatable, readable back, and
    // the same on a board built by somebody else. It is the reason the 174 mA
    // constant this file used to carry is gone.
    m_driver.I_scale_analog(false);
    // StealthChop AT REST, SpreadCycle WHEN MOVING.
    // StealthChop alone was chosen for silence in an observatory, but at the
    // low speed the wheel needs (50 full steps/s) it gives less torque, and
    // the motor hummed against the steep flank of the detent in both
    // directions, while from halfway between two notches it moved. StealthChop
    // can be kept for holding only: the chip switches by itself on TPWMTHRS: StealthChop while TSTEP (the time between two
    // microsteps, in 12 MHz clocks) is at least TPWMTHRS, SpreadCycle when it
    // is shorter. At rest TSTEP is at its maximum, so holding stays silent;
    // at 12 full steps/s = 192 microsteps/s TSTEP is 12e6/192 = 62500, so
    // any real move (50 full steps/s gives 15000) runs in SpreadCycle.
    // TRIAL: to become a setting with its default once proven on the wheel.
    m_driver.en_spreadCycle(false);
    m_driver.TPWMTHRS(STEALTH_BELOW_TSTEP);
    m_driver.microsteps(MICROSTEPS);
    m_driver.toff(5);                   // chopper off-time: without it the motor is silent
    apply_currents();
    // GSTAT.reset is set by every reset of the chip and stays set until it
    // is written back: cleared HERE, at the end of the setup, so that finding
    // it set again before a leg means a reset since (driver_check()). Without
    // this the first check after a power-up with the 12 V already on would
    // report a reset that the setup had already mended.
    m_driver.GSTAT(tmc::GSTAT_RESET);
    return true;
}

DriverReadback MechanicsEsp32::read_driver()
{
    // Three rounds of UART, before a leg and never during one. A read that
    // fails its CRC comes back 0 from the library: version 0 is silence, and
    // a GCONF of 0 is a setup gone - both the safe side.
    DriverReadback r;
    r.version = m_driver.version();
    r.gstat = m_driver.GSTAT();
    r.gconf = m_driver.GCONF();
    return r;
}

DriverCheck MechanicsEsp32::driver_check()
{
    const DriverState state = judge_driver(read_driver());
    if (state == DriverState::READY) { m_driver_alive = true; return DriverCheck::READY; }
    if (state == DriverState::SILENT) {
        m_driver_alive = false;
        m_silicon = 0;
        return DriverCheck::SILENT;
    }
    // It answers without our setup: powered since it was last seen silent,
    // or reset under our feet. The same routine as at boot.
    const bool was_alive = m_driver_alive;
    m_driver_alive = configure_driver();
    if (!m_driver_alive) return DriverCheck::SILENT;
    return was_alive ? DriverCheck::RESET : DriverCheck::POWERED;
}

void MechanicsEsp32::apply_currents()
{
    // rms_current(mA, mult) puts IRUN from the milliampere and IHOLD at mult
    // times that. The ratio is computed instead of written, so asking for a
    // hold current the run current cannot support is impossible by
    // construction.
    const float ratio = m_run_ma > 0
                         ? (float)m_hold_ma / (float)m_run_ma : 0.0f;
    m_driver.rms_current(m_run_ma, ratio);
    // At zero hold the coils are let go instead of braking: nothing warms up
    // next to the sensor, and a wheel that drifts at rest is told to turn the
    // hold on by the drift watch.
    m_driver.freewheel(m_hold_ma > 0 ? 0 : 1);
}

const char *MechanicsEsp32::driver_name()
{
    switch (m_silicon) {
        case SILICON_2208: return "TMC2208";
        case SILICON_2209: return "TMC2209";
        // silent: which one it is cannot be known, so both are named. Saying
        // only "TMC2209" reported a silent 2208 - the chip Wheelly has - as a
        // silent 2209
        default:           return "TMC2208/2209";
    }
}

float MechanicsEsp32::angle()
{
    // rawAngle() gives 0..4095 over a turn: 0.088 degrees per count.
    return m_sensor.rawAngle() * (360.0f / 4096.0f);
}

bool MechanicsEsp32::sensor_responds()
{
    const uint32_t now = millis();
    if ((uint32_t)(now - m_last_check) > CHECK_PERIOD_MS) {
        m_last_check = now;
        m_sensor_alive = m_sensor.isConnected();
    }
    return m_sensor_alive;
}

bool MechanicsEsp32::magnet_seen()
{
    return m_sensor.magnetDetected();
}

bool MechanicsEsp32::field_weak()
{
    return m_sensor.magnetTooWeak();
}

bool MechanicsEsp32::field_strong()
{
    return m_sensor.magnetTooStrong();
}

uint8_t MechanicsEsp32::agc()
{
    // With this magnet at 3.3 V the AGC stays at full scale at any height:
    // it is read for diagnostics, but the calibration criterion is the magnitude.
    // See hardware.md, the section on how the air gap was chosen.
    return m_sensor.readAGC();
}

uint16_t MechanicsEsp32::magnitude()
{
    return m_sensor.readMagnitude();
}

void MechanicsEsp32::move(long microsteps)
{
    if (m_stepper == nullptr) return;
    // Already microsteps - one pulse each - and NOT multiplied again: when
    // this line did "* MICROSTEPS" while wheel.cpp's estimate
    // (STEPS_PER_DEGREE) already counted microsteps, so every move was sixteen
    // times its estimate. test_units.py reads this function to keep it so.
    m_stepper->move(microsteps);
}

void MechanicsEsp32::stop()
{
    if (m_stepper != nullptr) m_stepper->forceStop();
}

bool MechanicsEsp32::is_moving()
{
    return m_stepper != nullptr && m_stepper->isRunning();
}

void MechanicsEsp32::enable(bool on)
{
    // The driver's EN is active low, and at rest it must be left HIGH: the 10 k
    // pull-up to VIO keeps the driver off at every moment the XIAO is not
    // driving that pin - reset, boot, pins at high impedance.
    if (m_stepper != nullptr) {
        if (on) m_stepper->enableOutputs();
        else m_stepper->disableOutputs();
    } else {
        pinMode(m_p.en, OUTPUT);
        digitalWrite(m_p.en, on ? LOW : HIGH);
    }
}

void MechanicsEsp32::currents(uint16_t run_ma, uint16_t hold_ma)
{
    m_run_ma = run_ma;
    m_hold_ma = hold_ma;
    if (m_driver_alive) apply_currents();
}

void MechanicsEsp32::speed(uint32_t steps_per_second, uint32_t acceleration)
{
    if (m_stepper == nullptr) return;
    m_stepper->setSpeedInHz(steps_per_second * MICROSTEPS);
    m_stepper->setAcceleration(acceleration * MICROSTEPS);
}

bool MechanicsEsp32::driver_responds()
{
    // Only whether the chip answers: setting it up again is driver_check()'s
    // job, which the wheel calls before every leg and in `diag`. This
    // function used to redo the setup while the driver was dead, rate
    // limited, and only `diag` called it: the moves never did.
    return judge_driver(read_driver()) != DriverState::SILENT;
}

void MechanicsEsp32::led(bool on)
{
    if (m_led_bits == 0) { digitalWrite(m_p.led, on ? HIGH : LOW); return; }
    ledcWrite(m_p.led, on ? m_led_max : 0);
}

void MechanicsEsp32::led_level(float fraction)
{
    if (fraction < 0.0f) fraction = 0.0f;
    if (fraction > 1.0f) fraction = 1.0f;
    // without PWM the pulse becomes on/off at half level: better than dark
    if (m_led_bits == 0) { digitalWrite(m_p.led, fraction >= 0.5f ? HIGH : LOW); return; }
    ledcWrite(m_p.led, (uint32_t)lroundf(fraction * m_led_max));
}

uint32_t MechanicsEsp32::milliseconds()
{
    return millis();
}

}  // namespace wheelly

#endif  // ARDUINO
