// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// Wheelly - the real mechanics: AS5600, TMC2208/2209, step pulses.
//
// It is the only file of the firmware that touches the wires, and also the only
// one that CANNOT be tested without the wheel assembled. That is why it is kept
// thin: nothing is decided here: an angle is read, steps are sent, a LED is lit.
// Tolerances, retries and verdict live in wheel.cpp, which also runs on the PC
// under the tests.
//
// The libraries are the ones chosen in the survey of firmware.md, section 9, and
// the three known traps are noted where they apply.

#ifndef WHEELLY_MECHANICS_ESP32_H
#define WHEELLY_MECHANICS_ESP32_H

#ifdef ARDUINO

#include "mechanics.h"
#include "wheelly_protocol.h"   // FACTORY_RUN_MA

#include <AS5600.h>
#include <FastAccelStepper.h>
#include <TMCStepper.h>

namespace wheelly {

// The XIAO ESP32-S3 pin labels, the way they are printed on the board, and the
// GPIO behind each one. Pins are written with the label and never with the bare
// number, because the label is the only thing the wiring drawing and the person
// holding the soldering iron both use: nobody can compare "43" with a drawing
// that says D6. firmware/test/test_pins.py holds a second copy of this table
// and compares the two.
namespace xiao {
enum : uint8_t {
    D0 = 1, D1 = 2, D2 = 3, D3 = 4, D4 = 5, D5 = 6,
    D6 = 43, D7 = 44, D8 = 7, D9 = 8, D10 = 9,
};
}  // namespace xiao

// The pins, taken from the board as it is actually wired. The single source is
// mechanics/wheelly-cad/src/wiring.py, which also draws
// pcb/en_board-layout.svg and pcb/schemi/: the drawing the board is
// soldered from. test_pins.py fails if this table and that drawing drift apart.
//
// THIS TABLE WAS ONCE A PROPOSAL, and it was wrong on six signals out of
// eight - written before the layout was verified on the board, and never
// compared with it. It showed as
// two symptoms that looked unrelated: `diag` answered "TMC2209 over UART:
// SILENT", because the firmware was talking on D6/D7 while the single wire is
// on D8/D9; and EN measured 0 V with the driver enabled, because `begin()`
// drives the LED low on what it thought was D3 - and D3 is where EN is. The
// hunt went to MS1/MS2 and to R2, which were never the problem. Only I2C
// matched, and only because D4/D5 happened to agree.
struct Pins {
    uint8_t sda   = xiao::D4;
    uint8_t scl   = xiao::D5;
    uint8_t step  = xiao::D0;
    uint8_t dir   = xiao::D1;
    // EN: no boot-strapping constraint on GPIO4, which is what hardware.md asks
    // for. It also carries the 10 k pull-up to VIO, so the driver stays off
    // while the XIAO's pins are still high impedance.
    uint8_t en    = xiao::D3;
    // The single-wire UART of the driver: TX goes through R2 (1 k), RX comes
    // straight off the same hole. Datasheet page 20, pcb/README.md.
    uint8_t uart_rx = xiao::D9;
    uint8_t uart_tx = xiao::D8;
    uint8_t led   = xiao::D10;   // external, so it can be shielded from the optics
};

class MechanicsEsp32 : public Mechanics
{
    public:
        explicit MechanicsEsp32(const Pins &pins = Pins());

        // Switches everything on. Returns false if the sensor cannot be found:
        // that is no reason not to start - the driver must be able to connect
        // and say what is wrong - but it has to be known.
        bool begin();

        float angle() override;
        bool sensor_responds() override;
        bool magnet_seen() override;
        bool field_weak() override;
        bool field_strong() override;
        uint8_t agc() override;
        uint16_t magnitude() override;

        void move(long steps) override;
        void stop() override;
        bool is_moving() override;
        void enable(bool on) override;
        void currents(uint16_t run_ma, uint16_t hold_ma) override;
        void speed(uint32_t steps_per_second, uint32_t acceleration) override;
        bool driver_responds() override;
        DriverCheck driver_check() override;

        const char *driver_name() override;

        void led(bool on) override;
        void led_level(float fraction) override;
        int led_pwm_bits() override { return m_led_bits; }
        uint32_t milliseconds() override;

    private:
        // Sets the driver up from scratch and reads back which silicon it is.
        // Called by begin() and again by driver_check() whenever the driver
        // answers without our setup: pcb/README.md prescribes USB first and
        // 12 V second, so at boot the driver is normally unpowered, and a 12 V
        // that drops and comes back resets it (mechanics.h).
        bool configure_driver();
        DriverReadback read_driver();
        void apply_currents();

        Pins m_p;
        AS5600 m_sensor;
        // One class for both chips: TMC2208Stepper speaks the subset a TMC2208
        // and a TMC2209 have in common, which is all Wheelly uses.
        TMC2208Stepper m_driver;
        FastAccelStepperEngine m_engine;
        FastAccelStepper *m_stepper {nullptr};

        bool m_sensor_alive {false};
        bool m_driver_alive {false};
        uint8_t m_silicon {0};          // IOIN's version field, 0 if silent
        uint8_t m_led_bits {0};         // the LED's PWM bits, 0 = plain on/off
        uint32_t m_led_max {0};
        uint16_t m_run_ma {(uint16_t)FACTORY_RUN_MA};
        uint16_t m_hold_ma {0};
        uint32_t m_last_check {0};
};

}  // namespace wheelly

#endif  // ARDUINO
#endif  // WHEELLY_MECHANICS_ESP32_H
