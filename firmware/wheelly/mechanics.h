// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// Wheelly - the boundary between what decides and what touches the wires.
//
// Above this line is the logic: tolerances, retries, verdict, the dialogue
// with the driver. Below it are the AS5600, the TMC2208, the pulse generator
// and the XIAO's memory.
//
// The boundary exists for a practical reason: **the logic is tested on the Mac**.
// The same Wheel and the same Dialog that end up on the microcontroller are
// also compiled for the PC with fake mechanics underneath, and pass the same
// tests as the simulator. Without this cut, the only way to test the firmware
// would be to assemble the wheel, and the ugly cases - the clutch that slips
// three times, the sensor that goes silent halfway through a move - cannot be
// produced on demand.
//
// No Arduino in here: only C++11.

#ifndef WHEELLY_MECHANICS_H
#define WHEELLY_MECHANICS_H

#include <stdint.h>
#include <stddef.h>

namespace wheelly {

// The microstepping the TMC driver is set to. Here, at the boundary, because
// it fixes the UNITS of the interface below: move() counts MICROsteps, speed()
// takes FULL steps per second. When move() was documented as whole steps
// and the XIAO multiplied by 16, while wheel.h's STEPS_PER_DEGREE already
// counted microsteps: every move on the real wheel was sixteen times its
// estimate, and the Mac bench could not see it (its fake mechanics divided by
// the same constant). See test_units.py.
const uint16_t MICROSTEPS = 16;

// ---------------------------------------------------- is the driver still ours
//
// THE MOTOR DRIVER FORGETS ITS CONFIGURATION WHEN ITS MOTOR SUPPLY GOES. The
// TMC2208's registers live on VM, the 12 V, not on the XIAO's 3.3 V: with VM
// off the chip does not answer on the UART at all, and when VM comes back it
// starts from its reset values - current from the VREF trimmer
// (i_scale_analog = 1), microsteps from the MS1/MS2 pins, the power-down pin
// as PDN and not as UART. The assembly guide itself says USB first and 12 V
// second, so at every normal power-up the configuration the firmware writes at
// boot goes nowhere; and a 12 V plug that drops and comes back wipes it again
// with the XIAO still running. On the reference wheel a jog of +10 degrees
// moved +2.28 with the driver at its reset values, and +9.76 and +9.84 after
// `diag` - which fixed it only because it happened to redo the setup of a
// driver it had seen silent at boot. A driver reset while it was ALREADY
// configured would not have been fixed even by `diag`.
//
// So before every leg of motor, and in `diag`, the driver is ASKED whether it
// is still the one that was configured, and set up again if not. What is
// asked is three registers that can be read back (TMC2208 datasheet, register
// map; the same addresses on a TMC2209):
//   - IOIN (0x06, R): its version field says a TMC2208 or TMC2209 answered
//     with a good CRC - nothing else counts as an answer;
//   - GSTAT (0x01, R+WC): bit 0, `reset`, is set by the chip after every
//     reset and stays set until written back to 1; the setup clears it, so
//     finding it set again means a reset since;
//   - GCONF (0x00, RW): the bits the setup writes read back as written.
//     A second witness, in case GSTAT was cleared by someone else, and the
//     one that sees a setup that never took.
// Not IFCNT (0x02), the counter of good writes: it would say a reset only by
// comparison with a count kept here, it wraps at 256, and every write the
// library makes moves it. Not IHOLD_IRUN or TPWMTHRS: they are write-only.
//
// The verdict is a pure function of what was read, here and not in
// mechanics_esp32.cpp, so that the Mac bench runs the very same rule against
// a fake register file (test/firmware_bench.cpp, test/test_driver_check.cpp).
namespace tmc {
const uint8_t REG_GCONF = 0x00;
const uint8_t REG_GSTAT = 0x01;
const uint8_t REG_IOIN = 0x06;
const uint8_t GSTAT_RESET = 1u << 0;
// GCONF bits written by the setup (datasheet, GCONF): i_scale_analog (0)
// off, en_spreadcycle (2) off, pdn_disable (6) and mstep_reg_select (7) on.
const uint32_t GCONF_I_SCALE_ANALOG = 1u << 0;
const uint32_t GCONF_EN_SPREADCYCLE = 1u << 2;
const uint32_t GCONF_PDN_DISABLE = 1u << 6;
const uint32_t GCONF_MSTEP_REG_SELECT = 1u << 7;
const uint32_t GCONF_WATCHED = GCONF_I_SCALE_ANALOG | GCONF_EN_SPREADCYCLE
                               | GCONF_PDN_DISABLE | GCONF_MSTEP_REG_SELECT;
const uint32_t GCONF_CONFIGURED = GCONF_PDN_DISABLE | GCONF_MSTEP_REG_SELECT;
// After a reset: i_scale_analog = 1, pdn_disable = 0, mstep_reg_select = 0.
const uint32_t GCONF_RESET = GCONF_I_SCALE_ANALOG;
// IOIN's version field (bits 31..24): who answered.
const uint8_t VERSION_2208 = 0x20;
const uint8_t VERSION_2209 = 0x21;
}  // namespace tmc

// What was read back from the driver.
struct DriverReadback {
    uint8_t version;    // IOIN's version field; 0 when nothing came back
    uint8_t gstat;
    uint32_t gconf;
};

enum class DriverState {
    READY,      // answers, and still holds our setup
    UNSET,      // answers, but was reset (or never set up): set it up
    SILENT      // does not answer: no VM, or the single wire is broken
};

inline DriverState judge_driver(const DriverReadback &r)
{
    if (r.version != tmc::VERSION_2208 && r.version != tmc::VERSION_2209)
        return DriverState::SILENT;
    if (r.gstat & tmc::GSTAT_RESET) return DriverState::UNSET;
    if ((r.gconf & tmc::GCONF_WATCHED) != tmc::GCONF_CONFIGURED) return DriverState::UNSET;
    return DriverState::READY;
}

// What driver_check() found, and did: the wheel reports the two middle cases
// with the `! driver` event (wheelly_protocol.h, EV_DRIVER).
enum class DriverCheck {
    READY,
    POWERED,    // it was silent and now answers: the 12 V arrived; set up
    RESET,      // it answered with its setup gone: set up again
    SILENT
};

// Everything the wheel can do at the level of the iron.
class Mechanics
{
    public:
        virtual ~Mechanics() {}

        // --- position sensor ----------------------------------------------
        // The angle of the disc in degrees, 0..360. Call it only if
        // sensor_responds(): when the sensor is silent the value is meaningless.
        virtual float angle() = 0;
        virtual bool sensor_responds() = 0;
        virtual bool magnet_seen() = 0;
        // The AS5600's own verdict on the field (STATUS bits ML and MH). A
        // fake mechanics reports a good field; the real one reads the chip.
        // They were sent as fixed ml=1 mh=0 - the usual reading with this
        // magnet at 3.3 V, but ML also lights when the module's VDD5V-VDD3V3
        // bridge breaks (hardware.md), and a constant hid it.
        virtual bool field_weak() { return false; }
        virtual bool field_strong() { return false; }
        virtual uint8_t agc() = 0;
        virtual uint16_t magnitude() = 0;

        // --- motor ---------------------------------------------------------
        // Starts a move of a given number of MICROSTEPS (see MICROSTEPS above),
        // the sign giving the direction. It does not block: ask is_moving()
        // afterwards whether it has finished.
        virtual void move(long microsteps) = 0;
        virtual void stop() = 0;
        virtual bool is_moving() = 0;
        // Enabled means current in the coils. At rest it is released, unless
        // the user has asked for a holding current.
        virtual void enable(bool on) = 0;
        virtual void currents(uint16_t run_ma, uint16_t hold_ma) = 0;
        // In FULL motor steps per second (and per second squared): 200 is one
        // motor turn per second. The implementation multiplies by MICROSTEPS.
        virtual void speed(uint32_t steps_per_second, uint32_t acceleration) = 0;
        virtual bool driver_responds() = 0;
        // Before a leg of motor, and in `diag`: reads the driver back
        // (judge_driver above), sets it up again if it was reset or has just
        // been powered, and says which. The body is for fakes with no chip
        // behind them; the XIAO and the Mac bench override it.
        virtual DriverCheck driver_check()
        {
            return driver_responds() ? DriverCheck::READY : DriverCheck::SILENT;
        }
        // Which silicon answered on the UART. It has a body and is not pure on
        // purpose: the fake mechanics of the bench and the simulator have no
        // chip to ask, and making them answer a question they cannot answer
        // would be a lie that the two-halves comparison would then enshrine.
        // The real one overrides it with what it read from IOIN.
        virtual const char *driver_name() { return "TMC2208"; }   // the chip Wheelly has

        // --- diagnostic LED -------------------------------------------------
        virtual void led(bool on) = 0;
        // The LED at a fraction of full brightness, 0..1, already corrected for
        // the eye: it is the duty cycle, not the perceived level. It has a body
        // so that a mechanics without PWM still shows SOMETHING - lit while the
        // level is above zero - instead of refusing to compile; the XIAO
        // overrides it with the real PWM. Used by the pulse during a change of
        // slot (see pulse_level in dialog.h).
        virtual void led_level(float fraction) { led(fraction > 0.0f); }
        // How the LED is driven, for `diag`: the PWM's bits, 0 for plain on/off.
        // A PWM that could not be set up used to fail without a word.
        virtual int led_pwm_bits() { return 0; }

        // --- time -----------------------------------------------------------
        virtual uint32_t milliseconds() = 0;
};

// The calibration, i.e. what has to survive a power-off.
class Storage
{
    public:
        virtual ~Storage() {}
        virtual bool load(const char *key, float &value) = 0;
        virtual bool load(const char *key, const char *&value) = 0;
        virtual bool store(const char *key, float value) = 0;
        virtual bool store(const char *key, const char *value) = 0;
        // Removes a key; true also when it was not there. Born with the end
        // of the rotation trim: the old trims are folded into
        // the angles once and their keys erased, so no later start folds
        // them again (Wheel::load_or_default).
        virtual bool erase(const char *key) = 0;
        virtual bool commit() = 0;   // makes what was written final
};

}  // namespace wheelly

#endif  // WHEELLY_MECHANICS_H
