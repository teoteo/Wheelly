// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

#include "dialog.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace wheelly {

namespace {

// Morse: dot 1 unit, dash 3, pause between symbols 1, between letters 3.
const uint32_t MORSE_UNIT_MS = 100;
const char *MORSE_WHEELLY[] = {".--", "....", ".", ".", ".-..", ".-..", "-.--"};
const char  WHEELLY_LETTERS[] = "WHEELLY";

const char *motion_name(Motion m)
{
    switch (m) {
        case Motion::MOVING:   return MOTION_MOVING;
        case Motion::SETTLING: return MOTION_SETTLING;
        case Motion::FAILED: return MOTION_FAILED;
        default:            return MOTION_IDLE;
    }
}

const char *outcome_name(Outcome e)
{
    switch (e) {
        case Outcome::ARRIVED: return EV_ARRIVED;
        case Outcome::WARNING:   return EV_WARNING;
        case Outcome::FAILED:  return EV_FAILED;
        default:              return OUTCOME_NONE;
    }
}

// Why go or jog refused to start. Only for whoever reads the raw serial: the
// driver says it in the user's language from the code.
const char *refusal_text(Error code)
{
    switch (code) {
        case ERR_SENSOR_SILENT: return "AS5600 not responding";
        case ERR_DRIVER_SILENT: return "motor driver not responding - is the 12 V on?";
        default:                return "magnet not detected";
    }
}

const char *name_reason(NameCheck m)
{
    switch (m) {
        case NAME_EMPTY:    return "empty";
        case NAME_TOO_LONG: return "too-long";
        case NAME_BAD_EDGE: return "bad-edge";
        case NAME_BAD_CHAR: return "bad-char";
        case NAME_RESERVED: return "reserved";
        default:            return "duplicate";
    }
}

// Splits the line into words, modifying it in place. Returns how many it
// found. No allocations: we are on a microcontroller.
int split_words(char *line, char *words[], int maximum)
{
    int count = 0;
    char *p = line;
    while (*p != '\0' && count < maximum) {
        while (*p == ' ' || *p == '\t') p++;
        if (*p == '\0') break;
        words[count++] = p;
        while (*p != '\0' && *p != ' ' && *p != '\t') p++;
        if (*p != '\0') *p++ = '\0';
    }
    return count;
}

bool parse_number(const char *text, float &out)
{
    char *end = nullptr;
    const float v = strtof(text, &end);
    if (end == text || *end != '\0') return false;
    if (!isfinite(v)) return false;
    out = v;
    return true;
}

}  // namespace

bool morse_lit(uint32_t units)
{
    // One walk through the letters, consuming the time symbol by symbol and
    // pause by pause, and it STOPS at the first element that contains it.
    //
    // This loop used to be written inline in Dialog, with a break that left
    // only the inner loop: when the time fell in a pause, the outer
    // loop went on to the next letter with the pause not yet consumed, and the
    // first symbol of that letter "contained" it - so every pause lit the LED,
    // and "Blinks Wheelly" from KStars showed a sequence that was not
    // WHEELLY. The table and the total duration were right; only the
    // on/off in between was wrong, and no test looked at it.
    const int letters = (int)(sizeof(MORSE_WHEELLY) / sizeof(MORSE_WHEELLY[0]));
    for (int i = 0; i < letters; i++) {
        const char *code = MORSE_WHEELLY[i];
        for (size_t j = 0; code[j] != '\0'; j++) {
            const uint32_t duration = (code[j] == '-') ? 3 : 1;
            if (units < duration) return true;
            units -= duration;
            const uint32_t pause = (code[j + 1] != '\0') ? 1 : (i < letters - 1 ? 3 : 0);
            if (units < pause) return false;
            units -= pause;
        }
    }
    return false;
}

bool alarm_lit(Alarm which, uint32_t ms)
{
    if (which == Alarm::POSITION)
        return (ms % BLINK_PERIOD_MS) < BLINK_PERIOD_MS / 2;
    if (which == Alarm::DRIFT || which == Alarm::MAGNET) {
        const uint32_t flashes = which == Alarm::DRIFT ? 2 : 3;
        const uint32_t t = ms % FLASH_GROUP_PERIOD_MS;
        for (uint32_t i = 0; i < flashes; i++)
            if (t >= i * FLASH_PITCH_MS && t < i * FLASH_PITCH_MS + FLASH_DURATION_MS) return true;
    }
    return false;
}

float pulse_level(uint32_t ms, float minimum, float maximum)
{
    const float phase = (float)(ms % PULSE_PERIOD_MS) / PULSE_PERIOD_MS;
    const float wave = (sinf(phase * 2.0f * (float)M_PI - (float)M_PI / 2.0f) + 1.0f) / 2.0f;
    const float light = minimum + wave * (maximum - minimum);
    return powf(light, LED_GAMMA);
}

uint32_t morse_duration_ms()
{
    uint32_t units = 0;
    const int letters = (int)(sizeof(MORSE_WHEELLY) / sizeof(MORSE_WHEELLY[0]));
    for (int i = 0; i < letters; i++) {
        const char *code = MORSE_WHEELLY[i];
        const size_t n = strlen(code);
        for (size_t j = 0; j < n; j++) units += (code[j] == '-') ? 3 : 1;
        units += (uint32_t)(n - 1);            // pauses between the symbols
        if (i < letters - 1) units += 3;       // pause between the letters
    }
    return units * MORSE_UNIT_MS;
}

Dialog::Dialog(Wheel &wheel, Output &output, const char *fw_version,
                 const char *serial)
    : m_wheel(wheel), m_output(output),
      m_fw_version(fw_version), m_serial(serial)
{
}

void Dialog::ok(const char *fields)
{
    if (fields == nullptr || fields[0] == '\0') { m_output.line(PREFIX_OK); return; }
    snprintf(m_output_buf, sizeof(m_output_buf), "%s %s", PREFIX_OK, fields);
    m_output.line(m_output_buf);
}

void Dialog::error(Error code, const char *text, const char *fields)
{
    // Three things on the same line, for three recipients: the code for the
    // machine, which is also the translation key; the named fields as
    // parameters; the English text at the end for whoever watches the raw serial.
    if (fields != nullptr && fields[0] != '\0')
        snprintf(m_output_buf, sizeof(m_output_buf), "%s %d %s %s",
                 PREFIX_ERROR, (int)code, fields, text);
    else
        snprintf(m_output_buf, sizeof(m_output_buf), "%s %d %s",
                 PREFIX_ERROR, (int)code, text);
    m_output.line(m_output_buf);
}

void Dialog::comment(const char *text)
{
    snprintf(m_output_buf, sizeof(m_output_buf), "%c %s", PREFIX_COMMENT, text);
    m_output.line(m_output_buf);
}

void Dialog::receive(char c)
{
    if (c == '\r') return;
    if (c != '\n') {
        if (m_count < sizeof(m_line) - 1) m_line[m_count++] = c;
        else m_too_long = true;
        return;
    }
    m_line[m_count] = '\0';
    const bool was_too_long = m_too_long;
    m_count = 0;
    m_too_long = false;

    if (was_too_long) {
        // Half a line is not executed: we say it is too long. Better a clear
        // error than a command executed halfway.
        error(ERR_BAD_ARGUMENTS, "line too long");
        return;
    }
    execute(m_line);
}

void Dialog::send_status()
{
    Mechanics &m = m_wheel.mechanics();
    const bool sensor_ok = m.sensor_responds();
    snprintf(m_output_buf, sizeof(m_output_buf),
             "%s %s=%d %s=%.2f %s=%.2f %s=%.2f %s=%s %s=%d %s=%d %s=%d %s=%s "
             "%s=%d %s=%d %s=%d %s=%d %s=%d %s=%c",
             PREFIX_OK,
             F_POS, m_wheel.current_slot(),
             F_ANGLE, (double)m_wheel.angle(),
             F_TARGET, (double)m_wheel.target(),
             F_ERR, (double)m_wheel.residual_error(),
             F_MOTION, motion_name(m_wheel.motion()),
             F_RETRIES, m_wheel.retries(),
             F_LEGS, m_wheel.legs(),
             F_BOOSTS, m_wheel.boosts(),
             F_OUTCOME, outcome_name(m_wheel.outcome()),
             F_AGC, sensor_ok ? (int)m.agc() : 0,
             F_MAG, sensor_ok ? (int)m.magnitude() : 0,
             F_MD, (sensor_ok && m.magnet_seen()) ? 1 : 0,
             F_ML, (sensor_ok && m.field_weak()) ? 1 : 0,
             F_MH, (sensor_ok && m.field_strong()) ? 1 : 0,
             // the way the current (or last) leg was sent: with a one-way
             // direction every retry must say the same
             F_DIR, m_wheel.leg_sign() >= 0 ? '+' : '-');
    m_output.line(m_output_buf);
}

void Dialog::send_diag()
{
    // Answers one question only: is it really talking to the hardware? A wire
    // come loose on the motor driver would show up as "the motor does not turn"
    // and would send you looking for the problem in ten wrong places.
    Mechanics &m = m_wheel.mechanics();
    char line[128];

    if (!m.sensor_responds()) {
        comment("AS5600 at 0x36: SILENT");
        comment("check the wiring, and the VDD5V-VDD3V3 jumper on the module");
    } else {
        comment("AS5600 at 0x36: responding");
        snprintf(line, sizeof(line), "STATUS md=%d ml=%d mh=%d  AGC=%d  MAG=%d",
                 m.magnet_seen() ? 1 : 0, m.field_weak() ? 1 : 0,
                 m.field_strong() ? 1 : 0, (int)m.agc(), (int)m.magnitude());
        comment(line);
        // Calibration goes by the magnitude and not by the AGC: with this magnet at
        // 3.3 V the AGC stays at full scale at any height. See hardware.md.
        if (m.magnitude() < 350)
            comment("magnitude below 350: the magnet is too far or off centre");
    }

    // The chip says its own name: the version field of IOIN tells a TMC2208
    // (0x20) from a TMC2209 (0x21), and printing it here is not a nicety. A
    // driver that answers perfectly while the firmware expects the other silicon
    // reads as silence, and is hard to tell from a wiring fault.
    // Through the wheel's check, the one every leg makes: a driver found
    // reset or newly powered is set up again here too, and reported with the
    // `! driver` event - `diag` no longer cures what the moves leave broken.
    if (m_wheel.check_driver() != DriverCheck::SILENT) {
        snprintf(line, sizeof(line), "%s over UART: responding, run %d mA, hold %d mA",
                 m.driver_name(),
                 (int)m_wheel.run_current(), (int)m_wheel.hold_current());
        comment(line);
    } else {
        snprintf(line, sizeof(line),
                 "%s over UART: SILENT - check VM at the driver, then the 1k on the single wire",
                 m.driver_name());
        comment(line);
    }
    // How the LED is driven: a PWM that could not be set up once left it dark
    // while "led on" answered ok
    if (m.led_pwm_bits() > 0)
        snprintf(line, sizeof(line), "LED: PWM, %d bits", m.led_pwm_bits());
    else
        snprintf(line, sizeof(line), "LED: plain on/off, no PWM");
    comment(line);
    ok();
}

void Dialog::led_test()
{
    m_led_testing = true;
    m_led_end = m_wheel.mechanics().milliseconds() + morse_duration_ms();
    comment("W .--  H ....  E .  E .  L .-..  L .-..  Y -.--");
    char fields[32];
    snprintf(fields, sizeof(fields), "%s=%.1f", F_DURATION, morse_duration_ms() / 1000.0);
    ok(fields);
}

void Dialog::execute(char *line)
{
    char *words[8];
    const int count = split_words(line, words, 8);
    if (count == 0) return;    // empty line: not a command, no answer

    const char *command = words[0];
    char fields[WHEELLY_LINE_MAX];
    Error code = ERR_NONE;

    // -- identification ---------------------------------------------------
    if (strcmp(command, CMD_VERSION) == 0) {
        snprintf(fields, sizeof(fields), "%s=wheelly %s=%s %s=%d %s=%s %s=%d",
                 F_NAME, F_FW, m_fw_version, F_PROTO, PROTOCOL_VERSION,
                 F_SERIAL, m_serial, F_SLOTS, m_wheel.slots());
        ok(fields);
        return;
    }

    if (strcmp(command, CMD_STATUS) == 0) { send_status(); return; }
    if (strcmp(command, CMD_DIAG) == 0)   { send_diag();  return; }

    // -- movement ------------------------------------------------------------
    if (strcmp(command, CMD_GO) == 0) {
        if (count < 2) { error(ERR_BAD_ARGUMENTS, "go needs a slot"); return; }
        float v;
        if (!parse_number(words[1], v)) { error(ERR_BAD_ARGUMENTS, "slot must be a number"); return; }
        const int n = (int)v;
        if (n < 1 || n > m_wheel.slots()) {
            snprintf(fields, sizeof(fields), "%s=1..%d %s=%s",
                     F_EXPECTED, m_wheel.slots(), F_GOT, words[1]);
            error(ERR_OUT_OF_RANGE, "slot out of range", fields);
            return;
        }
        const float start_angle = m_wheel.angle();
        // read BEFORE go(): once the wheel moves it is between slots (0)
        const int slot_before = m_wheel.current_slot();
        if (!m_wheel.go(n, code)) {
            error(code, refusal_text(code));
            return;
        }
        snprintf(fields, sizeof(fields), "%s=%.2f %s=%.2f %s=%c",
                 F_TARGET, (double)m_wheel.target(), F_FROM, (double)start_angle,
                 // the way the wheel was really sent, which with a one-way
                 // direction is not the shorter one
                 F_DIR, m_wheel.leg_sign() >= 0 ? '+' : '-');
        // a new attempt: the position and drift alarms are over; the magnet
        // one is not (without the magnet go() refuses anyway)
        if (m_alarm == Alarm::POSITION || m_alarm == Alarm::DRIFT) clear_alarm();
        if (slot_before != n && m_wheel.led_mode() == LedMode::PULSE) {
            m_led_pulsing = true;
            m_led_pulse_since = m_wheel.mechanics().milliseconds();
        }
        ok(fields);
        return;
    }

    // jog <degrees>: to the angle read now plus that much
    if (strcmp(command, CMD_JOG) == 0) {
        if (count != 2) { error(ERR_BAD_ARGUMENTS, "jog needs degrees"); return; }
        float v;
        if (!parse_number(words[1], v)) { error(ERR_BAD_ARGUMENTS, "degrees must be a number"); return; }
        const float start_angle = m_wheel.angle();
        if (!m_wheel.jog(v, code)) {
            if (code == ERR_OUT_OF_RANGE) {
                snprintf(fields, sizeof(fields), "%s=-%d..%d %s=%s",
                         F_EXPECTED, JOG_MAX_DEG, JOG_MAX_DEG, F_GOT, words[1]);
                error(code, "jog out of range", fields);
            } else if (code == ERR_NOT_NOW) {
                error(code, "wheel is moving");
            } else {
                error(code, refusal_text(code));
            }
            return;
        }
        snprintf(fields, sizeof(fields), "%s=%.2f %s=%.2f %s=%c",
                 F_TARGET, (double)m_wheel.target(), F_FROM, (double)start_angle,
                 F_DIR, m_wheel.leg_sign() >= 0 ? '+' : '-');
        // a new attempt, as `go`: the position and drift alarms are over.
        // No pulse of the LED: a jog is not a change of filter.
        if (m_alarm == Alarm::POSITION || m_alarm == Alarm::DRIFT) clear_alarm();
        ok(fields);
        return;
    }

    if (strcmp(command, CMD_STOP) == 0) { m_wheel.stop(); ok(); return; }

    // -- calibration ---------------------------------------------------------
    // The lists are built in a loop and not with a fixed five-entry format:
    // the number of slots is a property of the wheel, not of the code.
    if (strcmp(command, CMD_ANGLES) == 0 || strcmp(command, CMD_NAMES) == 0) {
        const char letter = (command[0] == 'a') ? 'a' : 'n';
        size_t written = 0;
        fields[0] = '\0';
        for (int i = 1; i <= m_wheel.slots() && written < sizeof(fields); i++) {
            int printed;
            if (letter == 'n')
                printed = snprintf(fields + written, sizeof(fields) - written, "%s%c%d=%s",
                                  i > 1 ? " " : "", letter, i, m_wheel.name(i));
            else
                printed = snprintf(fields + written, sizeof(fields) - written, "%s%c%d=%.2f",
                                  i > 1 ? " " : "", letter, i,
                                  (double)m_wheel.calibration_angle(i));
            if (printed < 0) break;
            written += (size_t)printed;
        }
        ok(fields);
        return;
    }

    if (strcmp(command, CMD_SLOTS) == 0) {
        if (count > 1) {
            float v;
            if (!parse_number(words[1], v)) { error(ERR_BAD_ARGUMENTS, "slots must be a number"); return; }
            if (!m_wheel.set_slots((int)v, code)) {
                if (code == ERR_NOT_NOW) { error(code, "wheel is moving"); return; }
                snprintf(fields, sizeof(fields), "%s=%d..%d %s=%s",
                         F_EXPECTED, MIN_SLOTS, MAX_SLOTS, F_GOT, words[1]);
                error(code, "slots out of range", fields);
                return;
            }
        }
        snprintf(fields, sizeof(fields), "%s=%d", F_SLOTS, m_wheel.slots());
        ok(fields);
        return;
    }

    // angle <n> <degrees>: the slot's angle, in working memory (it replaced
    // `offset`). It does not move the wheel: see Wheel::set_angle.
    if (strcmp(command, CMD_ANGLE) == 0) {
        if (count != 3) { error(ERR_BAD_ARGUMENTS, "angle needs slot and degrees"); return; }
        float slot, degrees;
        if (!parse_number(words[1], slot) || !parse_number(words[2], degrees)) {
            error(ERR_BAD_ARGUMENTS, "angle takes two numbers");
            return;
        }
        if (!m_wheel.set_angle((int)slot, degrees, code)) {
            if (code == ERR_NOT_NOW) { error(code, "wheel is moving"); return; }
            const bool bad_slot = (int)slot < 1 || (int)slot > m_wheel.slots();
            if (bad_slot)
                snprintf(fields, sizeof(fields), "%s=1..%d %s=%s",
                         F_EXPECTED, m_wheel.slots(), F_GOT, words[1]);
            else
                snprintf(fields, sizeof(fields), "%s=0..%d %s=%s",
                         F_EXPECTED, ANGLE_MAX_DEG, F_GOT, words[2]);
            error(code, bad_slot ? "slot out of range" : "angle out of range", fields);
            return;
        }
        snprintf(fields, sizeof(fields), "a%d=%.2f",
                 (int)slot, (double)m_wheel.calibration_angle((int)slot));
        ok(fields);
        return;
    }

    if (strcmp(command, CMD_NAME) == 0) {
        if (count < 3) { error(ERR_BAD_ARGUMENTS, "name needs slot and text"); return; }
        float slot;
        if (!parse_number(words[1], slot)) { error(ERR_BAD_ARGUMENTS, "slot must be a number"); return; }
        if ((int)slot < 1 || (int)slot > m_wheel.slots()) {
            snprintf(fields, sizeof(fields), "%s=1..%d %s=%s",
                     F_EXPECTED, m_wheel.slots(), F_GOT, words[1]);
            error(ERR_OUT_OF_RANGE, "slot out of range", fields);
            return;
        }
        // A name with spaces arrives split into several words: it is already
        // invalid, and we say so with the right reason instead of gluing it back
        // together and accepting it.
        NameCheck reason = NAME_OK;
        const char *wanted = words[2];
        if (count > 3) reason = NAME_BAD_CHAR;
        if (reason == NAME_OK && m_wheel.set_name((int)slot, wanted, code, reason)) {
            snprintf(fields, sizeof(fields), "n%d=%s", (int)slot, wanted);
            ok(fields);
            return;
        }
        snprintf(fields, sizeof(fields), "%s=%s", F_REASON, name_reason(reason));
        error(ERR_BAD_FILTER_NAME,
               reason == NAME_OK ? "duplicate filter name" : "invalid filter name", fields);
        return;
    }

    if (strcmp(command, CMD_TEACH) == 0) {
        if (count < 2) { error(ERR_BAD_ARGUMENTS, "teach needs a slot"); return; }
        float slot;
        if (!parse_number(words[1], slot)) { error(ERR_BAD_ARGUMENTS, "slot must be a number"); return; }
        if (!m_wheel.reteach((int)slot, code)) {
            if (code == ERR_OUT_OF_RANGE) {
                snprintf(fields, sizeof(fields), "%s=1..%d %s=%s",
                         F_EXPECTED, m_wheel.slots(), F_GOT, words[1]);
                error(code, "slot out of range", fields);
            } else {
                error(code, code == ERR_NOT_NOW ? "wheel is moving"
                                                     : "sensor not usable");
            }
            return;
        }
        snprintf(fields, sizeof(fields), "a%d=%.2f",
                 (int)slot, (double)m_wheel.calibration_angle((int)slot));
        ok(fields);
        return;
    }

    if (strcmp(command, CMD_SAVE) == 0) {
        if (!m_wheel.save(code)) { error(code, "NVS write failed"); return; }
        snprintf(fields, sizeof(fields), "%s=nvs", F_SAVED);
        ok(fields);
        return;
    }

    // -- preferences ---------------------------------------------------------
    if (strcmp(command, CMD_TOLERANCE) == 0) {
        if (count > 1) {
            if (count != 4) { error(ERR_BAD_ARGUMENTS, "tolerance needs good, warn, retries"); return; }
            float good, warn, attempts;
            if (!parse_number(words[1], good) || !parse_number(words[2], warn) ||
                !parse_number(words[3], attempts)) {
                error(ERR_BAD_ARGUMENTS, "tolerance takes three numbers");
                return;
            }
            if (!m_wheel.set_tolerances(good, warn, (int)attempts, code)) {
                // got= too: the driver's message is "expected %1$s, got %2$s",
                // and without it the user read "got .". No spaces
                // in either value, or the field would be cut at the first one.
                snprintf(fields, sizeof(fields), "%s=0<good<=warn<=%d,retries=0..%d %s=%s,%s,%s",
                         F_EXPECTED, TOLERANCE_MAX_DEG, RETRIES_MAX,
                         F_GOT, words[1], words[2], words[3]);
                error(code, "tolerance out of range", fields);
                return;
            }
        }
        snprintf(fields, sizeof(fields), "%s=%.2f %s=%.2f %s=%d",
                 F_GOOD, (double)m_wheel.good_tolerance(),
                 F_WARN, (double)m_wheel.warn_tolerance(),
                 F_RETRIES, m_wheel.max_retries());
        ok(fields);
        return;
    }

    if (strcmp(command, CMD_MOTOR) == 0) {
        // All or nothing: EVERY argument is checked before ANY is applied.
        // When the current was applied first and the speed checked after, "motor 180 350" or "motor 180 99999 1200" answered an error
        // with the current already changed - the driver, told "refused", kept
        // showing the old value while the wheel ran on the new one.
        // motor <mA> <speed> <accel>: speed and acceleration go together, since
        // the driver's panel sets the three at once and half a pair makes no sense.
        float ma = 0, v = 0, a = 0;
        if (count == 3) {
            error(ERR_BAD_ARGUMENTS, "speed needs acceleration too: motor <mA> <speed> <accel>");
            return;
        }
        if (count > 1) {
            if (!parse_number(words[1], ma)) { error(ERR_BAD_ARGUMENTS, "mA must be a number"); return; }
            // same limits as Wheel::set_run_current(), checked here so
            // that nothing is applied when a later argument is refused
            if (!(ma >= 1 && ma <= MOTOR_MA_MAX)) {
                snprintf(fields, sizeof(fields), "%s=1..%u %s=%s", F_EXPECTED, MOTOR_MA_MAX,
                         F_GOT, words[1]);
                error(ERR_OUT_OF_RANGE, "current out of range", fields);
                return;
            }
        }
        if (count > 3) {
            if (!parse_number(words[2], v) || !parse_number(words[3], a)) {
                error(ERR_BAD_ARGUMENTS, "speed and acceleration must be numbers");
                return;
            }
            // same limits as Wheel::set_speed()
            if (!(v >= 1 && v <= MOTOR_SPEED_MAX && a >= 1 && a <= MOTOR_ACCEL_MAX)) {
                snprintf(fields, sizeof(fields), "%s=1..%lu,1..%lu %s=%s,%s", F_EXPECTED,
                         MOTOR_SPEED_MAX, MOTOR_ACCEL_MAX, F_GOT, words[2], words[3]);
                error(ERR_OUT_OF_RANGE, "speed or acceleration out of range", fields);
                return;
            }
        }
        // everything is valid: now apply. The setters check again and cannot
        // refuse what passed above.
        if (count > 1 && !m_wheel.set_run_current((uint16_t)ma, code)) {
            error(code, "current out of range");
            return;
        }
        if (count > 3 && !m_wheel.set_speed((uint32_t)v, (uint32_t)a, code)) {
            error(code, "speed or acceleration out of range");
            return;
        }
        // the move time cap follows the speed, so it travels with it
        snprintf(fields, sizeof(fields), "%s=%d %s=%lu %s=%lu %s=%lu",
                 F_MA, (int)m_wheel.run_current(),
                 F_SPEED, (unsigned long)m_wheel.speed(),
                 F_ACCEL, (unsigned long)m_wheel.acceleration(),
                 F_CEILING, (unsigned long)m_wheel.ceiling_ms());
        ok(fields);
        return;
    }

    if (strcmp(command, CMD_HOLD) == 0) {
        if (count > 1) {
            float ma;
            if (!parse_number(words[1], ma)) { error(ERR_BAD_ARGUMENTS, "mA must be a number"); return; }
            if (ma < 0 || !m_wheel.set_hold_current((uint16_t)ma, code)) {
                snprintf(fields, sizeof(fields), "%s=0..%d %s=%s",
                         F_EXPECTED, (int)m_wheel.run_current(), F_GOT, words[1]);
                error(ERR_OUT_OF_RANGE, "hold current out of range", fields);
                return;
            }
            // Whoever turns it on must know what they are buying: heat next to the
            // cooled sensor, and a chopper singing through the whole exposure.
            if (m_wheel.hold_current() > 0)
                comment("warning: holding current on - heat and chopper noise during exposures");
            snprintf(fields, sizeof(fields), "%s=%d", F_MA, (int)m_wheel.hold_current());
            ok(fields);
            return;
        }
        // The query used to say `detent=yes|no` too: the option is gone (wheelly_protocol.h, NO DETENT OPTION), and a driver that
        // still looks for the field finds it missing, which it already took
        // as "not known".
        snprintf(fields, sizeof(fields), "%s=%d", F_MA, (int)m_wheel.hold_current());
        ok(fields);
        return;
    }

    // -- the settling wait after every leg -----------------------------------
    // settle        -> the wait in ms, and the move time cap it enters
    // settle <ms>   -> sets it, 0..SETTLE_MS_MAX; kept by `save`
    // A command of its own, not a second argument of `hold`: an older driver
    // that sends `hold <mA>` must keep working as it did, and the cap moves
    // with this number, so its reply carries it as `direction`'s does.
    if (strcmp(command, CMD_SETTLE) == 0) {
        if (count > 2) {
            error(ERR_BAD_ARGUMENTS, "settle takes one number: settle <ms>");
            return;
        }
        if (count == 2) {
            float ms;
            if (!parse_number(words[1], ms)) { error(ERR_BAD_ARGUMENTS, "ms must be a number"); return; }
            if (!(ms >= 0.0f && ms <= (float)SETTLE_MS_MAX)
                || !m_wheel.set_settle_ms((uint32_t)lroundf(ms), code)) {
                snprintf(fields, sizeof(fields), "%s=0..%u %s=%s",
                         F_EXPECTED, SETTLE_MS_MAX, F_GOT, words[1]);
                error(ERR_OUT_OF_RANGE, "settle out of range", fields);
                return;
            }
        }
        snprintf(fields, sizeof(fields), "%s=%lu %s=%lu",
                 F_MS, (unsigned long)m_wheel.settle_ms(),
                 F_CEILING, (unsigned long)m_wheel.ceiling_ms());
        ok(fields);
        return;
    }

    // -- the direction: which way the wheel may turn -------------------------
    if (strcmp(command, CMD_DIRECTION) == 0) {
        if (count > 1) {
            Direction d;
            if (!direction_from_name(words[1], d)) {
                snprintf(fields, sizeof(fields), "%s=%s|%s|%s %s=%s", F_EXPECTED,
                         ARG_SHORTEST, ARG_UP, ARG_DOWN, F_GOT, words[1]);
                error(ERR_BAD_ARGUMENTS, "direction must be shortest, up or down", fields);
                return;
            }
            m_wheel.set_direction(d);
        }
        // the cap goes with it: one way, the longest path is nearly two turns
        snprintf(fields, sizeof(fields), "%s=%s %s=%lu", F_DIRECTION,
                 direction_name(m_wheel.direction()),
                 F_CEILING, (unsigned long)m_wheel.ceiling_ms());
        ok(fields);
        return;
    }

    // -- the drive ratio -----------------------------------------------------
    // ratio                  -> the one in use, the base, the factory one...
    // ratio <value>          -> sets the base, and the learning restarts from it
    // ratio learn on|off     -> the learning in use
    if (strcmp(command, CMD_RATIO) == 0) {
        if (count == 3 && strcmp(words[1], ARG_LEARN) == 0) {
            if (strcmp(words[2], ARG_ON) == 0) m_wheel.set_learning(true);
            else if (strcmp(words[2], ARG_OFF) == 0) m_wheel.set_learning(false);
            else {
                snprintf(fields, sizeof(fields), "%s=%s|%s %s=%s", F_EXPECTED,
                         ARG_ON, ARG_OFF, F_GOT, words[2]);
                error(ERR_BAD_ARGUMENTS, "ratio learn takes on or off", fields);
                return;
            }
        } else if (count == 2) {
            float value;
            if (!parse_number(words[1], value)) {
                error(ERR_BAD_ARGUMENTS, "ratio must be a number, or learn on|off");
                return;
            }
            if (!m_wheel.set_ratio(value, code)) {
                if (code == ERR_OUT_OF_RANGE) {
                    snprintf(fields, sizeof(fields), "%s=%.1f..%.1f %s=%s", F_EXPECTED,
                             (double)DRIVE_RATIO_MIN, (double)DRIVE_RATIO_MAX, F_GOT, words[1]);
                    error(code, "ratio out of range", fields);
                } else {
                    error(code, "wheel is moving");
                }
                return;
            }
        } else if (count != 1) {
            error(ERR_BAD_ARGUMENTS, "ratio takes a number, or learn on|off");
            return;
        }
        // the cap goes with it: it is counted at the base ratio
        snprintf(fields, sizeof(fields), "%s=%.4f %s=%.4f %s=%.4f %s=%s %s=%d %s=%lu",
                 F_RATIO, (double)m_wheel.ratio(), F_BASE, (double)m_wheel.base_ratio(),
                 F_FACTORY, (double)FACTORY_DRIVE_RATIO,
                 F_LEARN, m_wheel.learning() ? ARG_ON : ARG_OFF,
                 F_LEARNT, m_wheel.legs_learnt(),
                 F_CEILING, (unsigned long)m_wheel.ceiling_ms());
        ok(fields);
        return;
    }

    if (strcmp(command, CMD_LEGS) == 0) {
        if (count == 2 && strcmp(words[1], ARG_ON) == 0) m_report_legs = true;
        else if (count == 2 && strcmp(words[1], ARG_OFF) == 0) m_report_legs = false;
        else if (count != 1) {
            snprintf(fields, sizeof(fields), "%s=%s|%s %s=%s", F_EXPECTED,
                     ARG_ON, ARG_OFF, F_GOT, words[1]);
            error(ERR_BAD_ARGUMENTS, "legs takes on or off", fields);
            return;
        }
        snprintf(fields, sizeof(fields), "%s=%s", F_REPORT, m_report_legs ? ARG_ON : ARG_OFF);
        ok(fields);
        return;
    }

    // -- the LED -------------------------------------------------------------
    if (strcmp(command, CMD_LED) == 0) {
        if (count == 1) {
            snprintf(fields, sizeof(fields), "%s=%s %s=%s",
                     F_STATE, (m_wheel.led_mode() == LedMode::ON || m_led_testing) ? ARG_ON : ARG_OFF,
                     F_ENABLED, V_YES);
            const size_t n = strlen(fields);
            snprintf(fields + n, sizeof(fields) - n, " %s=%s", F_MODE,
                     m_wheel.led_mode() == LedMode::ON ? ARG_ON
                     : m_wheel.led_mode() == LedMode::PULSE ? ARG_PULSE : ARG_OFF);
            ok(fields);
            return;
        }
        if (strcmp(words[1], ARG_ON) == 0) {
            m_wheel.set_led_mode(LedMode::ON);
            m_led_pulsing = false;
            m_wheel.mechanics().led(true);
            snprintf(fields, sizeof(fields), "%s=%s", F_STATE, ARG_ON);
            ok(fields);
            return;
        }
        if (strcmp(words[1], ARG_OFF) == 0) {
            // off is off: the pulse of a move under way goes out too
            m_wheel.set_led_mode(LedMode::OFF);
            m_led_testing = false;
            m_led_pulsing = false;
            m_wheel.mechanics().led(false);
            snprintf(fields, sizeof(fields), "%s=%s", F_STATE, ARG_OFF);
            ok(fields);
            return;
        }
        if (strcmp(words[1], ARG_PULSE) == 0) {
            m_wheel.set_led_mode(LedMode::PULSE);
            if (!m_led_pulsing && !m_led_testing) m_wheel.mechanics().led(false);
            snprintf(fields, sizeof(fields), "%s=%s %s=%s", F_STATE, ARG_OFF, F_MODE, ARG_PULSE);
            ok(fields);
            return;
        }
        if (strcmp(words[1], ARG_TEST) == 0) { led_test(); return; }
        error(ERR_BAD_ARGUMENTS, "led takes on, pulse, off or test");
        return;
    }

    error(ERR_UNKNOWN_COMMAND, "unknown command");
}

void Dialog::raise_alarm(Alarm which)
{
    if (which <= m_alarm) return;           // a graver one is already showing
    m_alarm = which;
    m_alarm_since = m_wheel.mechanics().milliseconds();
    m_last_magnet_check = m_alarm_since;
}

void Dialog::clear_alarm()
{
    if (m_alarm == Alarm::NONE) return;
    m_alarm = Alarm::NONE;
    // back to what the mode says, as after the Morse test
    if (!m_led_testing) m_wheel.mechanics().led(m_wheel.led_mode() == LedMode::ON);
}

void Dialog::step()
{
    // Events are a luxury, not the truth: everything they say can be found
    // again in 'status'. They serve to make the driver react quickly.
    Outcome which;
    int slot, attempts;
    float deviation;
    // The leg's report goes BEFORE the verdict it may have led to, so a host
    // reading up to the verdict has every leg of the positioning.
    Wheel::LegReport leg;
    if (m_wheel.leg_to_report(leg) && m_report_legs) {
        snprintf(m_output_buf, sizeof(m_output_buf),
                 "%c %s %s=%d %s=%s %s=%s %s=%ld %s=%.3f %s=%.4f %s=%.3f %s=%.3f %s=%.3f %s=%.3f %s=%s %s=%s",
                 PREFIX_EVENT, EV_LEG, F_N, leg.n, F_KIND, leg_kind_name(leg.kind),
                 F_JOG, leg.jog ? V_YES : V_NO, F_STEPS, leg.steps,
                 F_MOTOR, (double)(leg.steps * 360.0 / (200.0 * MICROSTEPS)),
                 F_RATIO, (double)leg.ratio, F_AIM, (double)leg.aim,
                 F_FROM, (double)leg.from, F_TO, (double)leg.to, F_MOVED, (double)leg.moved,
                 F_LONG, leg.long_leg ? V_YES : V_NO, F_LEARN, leg.learnt ? V_YES : V_NO);
        m_output.line(m_output_buf);
    }
    if (m_wheel.event_to_send(which, slot, deviation, attempts)) {
        snprintf(m_output_buf, sizeof(m_output_buf), "%c %s %s=%d %s=%.2f %s=%d",
                 PREFIX_EVENT, outcome_name(which), F_POS, slot,
                 F_ERR, (double)deviation, F_RETRIES, attempts);
        m_output.line(m_output_buf);
        if (which == Outcome::FAILED) {
            raise_alarm(Alarm::POSITION);
            m_slot_at_failure = m_wheel.current_slot();
        }
        else if (m_alarm == Alarm::POSITION || m_alarm == Alarm::DRIFT) clear_alarm();
    }
    float drift;
    if (m_wheel.drift_to_report(drift)) {
        snprintf(m_output_buf, sizeof(m_output_buf), "%c %s %s=%d %s=%.2f",
                 PREFIX_EVENT, EV_DRIFT, F_POS, m_wheel.current_slot(),
                 F_ERR, (double)drift);
        m_output.line(m_output_buf);
        raise_alarm(Alarm::DRIFT);
    }
    DriverCheck setup;
    if (m_wheel.driver_to_report(setup)) {
        snprintf(m_output_buf, sizeof(m_output_buf), "%c %s %s=%s",
                 PREFIX_EVENT, EV_DRIVER, F_REASON,
                 setup == DriverCheck::POWERED ? V_POWER : V_RESET);
        m_output.line(m_output_buf);
    }
    if (m_wheel.sensor_to_report()) {
        snprintf(m_output_buf, sizeof(m_output_buf), "%c %s %s=0",
                 PREFIX_EVENT, EV_SENSOR, F_MD);
        m_output.line(m_output_buf);
        raise_alarm(Alarm::MAGNET);
    }
    // A wheel turned by hand onto a slot after a failed move: the fast blinking
    // ends, as firmware.md and the panel guide promise ("when the wheel reaches
    // a slot or is sent again"). When only `go` or a new verdict ended it, a
    // wheel set right by hand went on blinking all night.
    // current_slot() is 0 while moving and outside the warn tolerance,
    // so this is "at rest, on a slot, within tolerance".
    if (m_alarm == Alarm::POSITION) {
        const int slot_now = m_wheel.current_slot();
        if (slot_now != m_slot_at_failure) {
            if (slot_now != 0) clear_alarm();
            else m_slot_at_failure = 0;     // it left its slot: any one now counts
        }
    }
    if (m_alarm == Alarm::MAGNET) {
        const uint32_t now = m_wheel.mechanics().milliseconds();
        if ((uint32_t)(now - m_last_magnet_check) >= MAGNET_CHECK_MS) {
            m_last_magnet_check = now;
            // the wheel's hysteresis, not one reading: a flickering MD bit
            // would end the alarm and the event would not raise it again
            if (m_wheel.mechanics().sensor_responds() && !m_wheel.magnet_lost()) clear_alarm();
        }
    }

    if (m_led_testing) {
        // The Morse is generated here instead of with waits, because blocking
        // the loop for seven seconds would mean not answering commands - and
        // 'status' must always be able to answer, even during the test.
        const uint32_t now = m_wheel.mechanics().milliseconds();
        if ((int32_t)(now - m_led_end) >= 0) {
            m_led_testing = false;
            m_wheel.mechanics().led(m_wheel.led_mode() == LedMode::ON);
            return;
        }
        const uint32_t elapsed = now - (m_led_end - morse_duration_ms());
        m_wheel.mechanics().led(morse_lit(elapsed / MORSE_UNIT_MS));
    } else if (m_alarm != Alarm::NONE && m_wheel.led_mode() != LedMode::OFF) {
        const uint32_t ms = m_wheel.mechanics().milliseconds() - m_alarm_since;
        m_wheel.mechanics().led_level(
            alarm_lit(m_alarm, ms) ? powf(PULSE_MAX_LIGHT, LED_GAMMA) : 0.0f);
    } else if (m_led_pulsing) {
        // The Morse test wins over the pulse: it is asked for on purpose, and
        // a pulse under it would garble the letters. When the test ends the
        // pulse picks up again at the next pass, if the wheel is still moving.
        const Motion mo = m_wheel.motion();
        if (mo != Motion::MOVING && mo != Motion::SETTLING) {
            m_led_pulsing = false;
            m_wheel.mechanics().led(m_wheel.led_mode() == LedMode::ON);
            return;
        }
        m_wheel.mechanics().led_level(
            pulse_level(m_wheel.mechanics().milliseconds() - m_led_pulse_since));
    }
    (void)WHEELLY_LETTERS;
}

}  // namespace wheelly
