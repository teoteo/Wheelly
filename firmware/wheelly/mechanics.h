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
