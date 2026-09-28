// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// Wheelly - the text dialog: from lines to commands, and back.
//
// It knows neither Arduino nor the serial port: it receives bytes and returns
// lines. The transport is supplied by whoever uses it - USB CDC on the XIAO,
// stdin/stdout on the test bench. It is the same cut the simulator has, and it
// serves the same purpose: running this very same code on the PC, under the tests.
//
// No dynamic allocation: fixed buffers, because this ends up on a
// microcontroller, and a heap fragmented after weeks of uptime is the kind of
// fault that shows up on the one good night.

#ifndef WHEELLY_DIALOG_H
#define WHEELLY_DIALOG_H

#include "wheel.h"
#include "wheelly_protocol.h"

namespace wheelly {

// Whoever receives the lines to send. On the XIAO it writes to USB, on the bench to stdout.
class Output
{
    public:
        virtual ~Output() {}
        virtual void line(const char *text) = 0;
};

// The alarms the LED can show; described with their timing further down.
enum class Alarm { NONE, DRIFT, POSITION, MAGNET };   // in order of gravity

class Dialog
{
    public:
        Dialog(Wheel &wheel, Output &output, const char *fw_version,
                const char *serial);

        // A byte arrived from the channel. On a complete line it executes and answers.
        void receive(char c);
        // To be called continuously: it sends the events the wheel has produced.
        void step();

    private:
        void execute(char *line);
        void ok(const char *fields = nullptr);
        void error(Error code, const char *text, const char *fields = nullptr);
        void comment(const char *text);
        void send_status();
        void send_diag();
        void led_test();

        Wheel &m_wheel;
        Output &m_output;
        const char *m_fw_version;
        const char *m_serial;

        char m_line[WHEELLY_LINE_MAX + 1];
        size_t m_count {0};
        bool m_too_long {false};

        char m_output_buf[WHEELLY_LINE_MAX + 1];

        // `legs on|off`: the `! leg` event after every leg.
        // Off at every start and never saved: it is for a measuring tool.
        bool m_report_legs {false};

        // state of the LED test under way
        bool m_led_testing {false};
        uint32_t m_led_end {0};

        // the pulse while the wheel changes slot
        bool m_led_pulsing {false};
        uint32_t m_led_pulse_since {0};

        // the alarm the LED is showing, if any (see Alarm)
        void raise_alarm(Alarm which);
        void clear_alarm();
        Alarm m_alarm {Alarm::NONE};
        uint32_t m_alarm_since {0};
        uint32_t m_last_magnet_check {0};
        // The slot the wheel stood on when a move failed (0 = between slots).
        // The fast blinking ends when the wheel is found at rest on a slot, by
        // hand too - but a wheel that never left its old slot (a slipping
        // clutch) has not "reached" anything, so that slot counts only after
        // the wheel has been seen off it.
        int m_slot_at_failure {0};

    public:
        Alarm alarm() const { return m_alarm; }
};

// THE LED SAYS WHAT WENT WRONG (hardware.md: off while
// the wheel works, lit only to signal an anomaly, and it can be switched off
// altogether - with the LED in "off" mode none of these shows: it is also the
// mode to turn the wheel by hand with no current in the motor, and a wheel
// turned by hand drifts by definition). One alarm at
// a time, the gravest; the Morse test wins over all of them.
//   POSITION   the wheel did not reach the slot after every retry: fast
//              blinking, 4 a second, until it reaches one or is sent again;
//   DRIFT      the wheel moved on its own at rest beyond the threshold: two
//              short flashes every 2 s, until it is sent somewhere;
//   MAGNET     the sensor no longer sees the magnet: three short flashes
//              every 2 s, until it sees it again.
// The brightness is the top of the pulse (5..30 %, chosen on the real LED).
const uint32_t BLINK_PERIOD_MS = 250;      // POSITION: 4 a second
const uint32_t FLASH_GROUP_PERIOD_MS = 2000;         // DRIFT, MAGNET: a group every 2 s
const uint32_t FLASH_DURATION_MS = 120;
const uint32_t FLASH_PITCH_MS = 300;            // from the start of a flash to the next
const uint32_t MAGNET_CHECK_MS = 500;      // how often a lost magnet is looked for

// Whether the LED is lit, that many ms into an alarm. A pure function, outside
// the class, so the patterns can be checked on the PC.
bool alarm_lit(Alarm which, uint32_t ms);

// How long "WHEELLY" lasts in Morse, in milliseconds. Outside the class because
// the tests need it too, and they check it is the documented number.
uint32_t morse_duration_ms();

// Whether the LED is lit at that many Morse units from the start of "WHEELLY".
// A pure function, outside the class, so the sequence can be checked on the
// PC unit by unit - which the protocol tests could not do (see dialog.cpp).
bool morse_lit(uint32_t units);

// The LED pulses while the wheel goes to ANOTHER slot: it starts when the command arrives and stops when the wheel is
// there, or has failed, or is stopped. Not on a "go" to the slot it is already
// in - that is a small correction, not a change of filter, and a light that
// breathed at every correction would stop meaning anything.
//
// The timing comes from a pen on CodePen (codepen.io/teo_/pen/WbRRdQX): a sine
// with a 1700 ms period that starts from the bottom. The brightness is NOT
// the pen's 0.3..1.0: on the real LED 30..100, 10..50 and 5..30 were
// compared side by side (firmware/led_test) and 5..30 was chosen - at full
// brightness the LED is a lamp in a dark observatory.
const uint32_t PULSE_PERIOD_MS = 1700;
const float PULSE_MIN_LIGHT = 0.05f;
const float PULSE_MAX_LIGHT = 0.30f;
// The pen changes a COLOUR, and a colour on a screen is already coded for the
// eye (sRGB, gamma about 2.2); a PWM duty is light, linear. Driving the LED
// with 0.3 as duty would give a pulse that sits bright and dips briefly -
// not the pen. So the level is raised to the gamma here: 5 % of brightness is
// 0.14 % of duty.
const float LED_GAMMA = 2.2f;

// The duty cycle of the LED, 0..1, that many milliseconds after the start of
// the pulse. A pure function, outside the class, so it can be checked on the
// PC against the pen's formula. The bottom and the top are arguments so that
// the bench on the board (led_test) can show other ranges side by side with
// the same code; the firmware uses the defaults.
float pulse_level(uint32_t ms, float minimum = PULSE_MIN_LIGHT,
                         float maximum = PULSE_MAX_LIGHT);

}  // namespace wheelly

#endif  // WHEELLY_DIALOG_H
