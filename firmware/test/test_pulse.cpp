// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// The LED pulses while the wheel changes slot, and only then.
//
// Two things are checked, on the firmware's own Wheel and Dialog:
//
//   1. the LEVEL, millisecond by millisecond, against the CodePen pen
//      (codepen.io/teo_/pen/WbRRdQX) with the range chosen on the real LED,
//      5..30 %: the formula is written again HERE, and not read from the
//      firmware's constants - a test that used the firmware's numbers would
//      agree with any mistake made in them;
//   2. WHEN it pulses, with a fake mechanics and a fake clock: during a "go" to
//      another slot yes, during a "go" to the slot it is already in no, and
//      after arriving, stopping or failing the LED goes back to off; with
//      "led off" it never pulses, with "led on" it stays steady, and the
//      choice survives "save" and a power cycle.
#include "../wheelly/dialog.h"
#include "../wheelly/wheel.h"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <map>
#include <string>

using namespace wheelly;

namespace {

uint32_t clock = 0;

class FakeMechanics : public Mechanics
{
    public:
        float angle() override { return (float)m_angle; }
        bool sensor_responds() override { return true; }
        bool magnet_seen() override { return true; }
        uint8_t agc() override { return 128; }
        uint16_t magnitude() override { return 800; }
        void move(long steps) override
        {
            // 20 ms a degree, and it lands exactly: the pulse is about when
            // the wheel moves, not about how well it aims
            const double degrees = steps / (double)steps_per_degree(FACTORY_DRIVE_RATIO);
            m_from = m_angle; m_to = m_angle + degrees;
            m_start = clock; m_duration = (uint32_t)(std::fabs(degrees) * 20.0);
            m_moving = !m_jammed;
        }
        void stop() override { m_moving = false; }
        bool is_moving() override
        {
            if (!m_moving) return false;
            if (clock - m_start >= m_duration) { m_angle = norm(m_to); m_moving = false; return false; }
            m_angle = norm(m_from + (m_to - m_from) * (clock - m_start) / (double)m_duration);
            return true;
        }
        void enable(bool) override {}
        void currents(uint16_t, uint16_t) override {}
        void speed(uint32_t, uint32_t) override {}
        bool driver_responds() override { return true; }
        void led(bool on) override { level = on ? 1.0f : 0.0f; pwm = false; }
        void led_level(float f) override { level = f; pwm = true; }
        uint32_t milliseconds() override { return clock; }

        float level {0.0f};
        bool pwm {false};          // the last write was a pulse level, not on/off
        bool m_jammed {false};   // the clutch slips: the wheel never gets there

    private:
        static double norm(double g) { double r = std::fmod(g, 360.0); return r < 0 ? r + 360.0 : r; }
        double m_angle {0.0}, m_from {0.0}, m_to {0.0};
        uint32_t m_start {0}, m_duration {0};
        bool m_moving {false};
};

class FakeStorage : public Storage
{
    public:
        bool load(const char *k, float &v) override
        { auto t = m.find(k); if (t == m.end()) return false; v = t->second; return true; }
        bool load(const char *, const char *&) override { return false; }
        bool store(const char *k, float v) override { m[k] = v; return true; }
        bool store(const char *, const char *) override { return true; }
        bool erase(const char *k) override { m.erase(k); return true; }
        bool commit() override { return true; }
    private:
        std::map<std::string, float> m;
};

class SilentOutput : public Output
{
    public:
        void line(const char *) override {}
};

int failures = 0;

void check(bool condition, const char *what)
{
    std::printf("  %s %s\n", condition ? "ok" : "! ", what);
    if (!condition) failures++;
}

struct Bench {
    FakeMechanics m;
    FakeStorage mem;
    SilentOutput u;
    Wheel r {m, mem};
    Dialog d {r, u, "test", "0"};
    Bench() { r.begin(); }

    void send(const char *line)
    {
        for (const char *p = line; *p; p++) d.receive(*p);
        d.receive('\n');
    }
    // runs the loop for `ms`, and says whether the LED was pulsing - driven
    // with a level strictly between off and full - at any moment of it
    bool run(uint32_t ms, float *minimum = nullptr, float *maximum = nullptr)
    {
        bool pulsed = false;
        float lo = 2.0f, hi = -1.0f;
        for (uint32_t t = 0; t < ms; t += 5) {
            clock += 5;
            r.step();
            d.step();
            if (m.pwm) {
                pulsed = true;
                lo = std::fmin(lo, m.level);
                hi = std::fmax(hi, m.level);
            }
        }
        if (minimum) *minimum = lo;
        if (maximum) *maximum = hi;
        return pulsed;
    }
};

}  // namespace

int main()
{
    // ---- 1. the level, against the pen ----------------------------------
    // Pen: PULSE_DURATION 1700, wave = sin(p*2pi - pi/2), norm = (wave+1)/2.
    // Range: 5..30 %, chosen on the real LED (the pen
    // had 30..100). The factor is perceived brightness; the duty is light,
    // hence ^2.2.
    double worst = 0.0;
    for (uint32_t ms = 0; ms < 3 * 1700; ms += 7) {
        const double phase = (ms % 1700) / 1700.0;
        const double norm = (std::sin(phase * 2 * M_PI - M_PI / 2) + 1) / 2;
        const double expected = std::pow(0.05 + norm * 0.25, 2.2);
        worst = std::fmax(worst, std::fabs(expected - pulse_level(ms)));
    }
    char line[160];
    std::snprintf(line, sizeof(line), "the level follows the pen, 1700 ms, 5..30 %% (worst gap %.6f)", worst);
    check(worst < 1e-5, line);
    check(std::fabs(pulse_level(0) - std::pow(0.05, 2.2)) < 1e-6,
             "it starts from the bottom, not from full");
    check(std::fabs(pulse_level(850) - std::pow(0.30, 2.2)) < 1e-4, "30 % at half period");

    // ---- 2. when it pulses ----------------------------------------------
    {
        Bench b;
        b.send("go 3");
        float lo, hi;
        const bool pulsed = b.run(400, &lo, &hi);
        check(pulsed, "go to another slot: the LED pulses while it moves");
        b.run(8000);
        check(b.r.motion() == Motion::IDLE && b.r.current_slot() == 3, "  (the wheel got to slot 3)");
        check(!b.m.pwm && b.m.level == 0.0f, "arrived: the LED is back off, as the user left it");

        b.send("go 3");
        check(!b.run(3000), "go to the slot it is already in: no pulse (a correction, not a change)");

        b.send("led on");
        b.send("go 1");
        const bool pulsed_on = b.run(8000);
        check(!pulsed_on && !b.m.pwm && b.m.level == 1.0f,
                 "\"led on\": steady on through the change, no pulse");

        b.send("led off");
        b.send("go 4");
        const bool pulsed_off = b.run(8000);
        check(!pulsed_off && b.m.level == 0.0f,
                 "\"led off\": dark through the change - no pulse either");

        b.send("led pulse");
        b.send("go 2");
        check(b.run(400), "\"led pulse\": pulsing again");
        b.run(8000);
    }
    {
        // the choice survives "save" and a power cycle: a new Wheel on the
        // same memory, as the XIAO finds it at the next power-up
        FakeMechanics m;
        FakeStorage mem;
        SilentOutput u;
        {
            Wheel r(m, mem);
            Dialog d(r, u, "test", "0");
            r.begin();
            for (const char *p = "led off\nsave\n"; *p; p++) d.receive(*p);
        }
        Wheel r2(m, mem);
        r2.begin();
        check(r2.led_mode() == LedMode::OFF, "\"led off\" survives save and power-up");
        FakeStorage empty;
        Wheel r3(m, empty);
        r3.begin();
        check(r3.led_mode() == LedMode::PULSE, "a new wheel starts with the pulse on");
    }
    {
        Bench b;
        b.send("go 4");
        b.run(200);
        b.send("stop");
        b.run(50);
        check(!b.m.pwm && b.m.level == 0.0f, "stopped half way: the pulse stops");
    }
    {
        Bench b;
        b.m.m_jammed = true;
        b.send("go 2");
        b.run(60000);
        check(b.r.motion() == Motion::FAILED, "  (the slipping clutch makes the move fail)");
        // a failed move is an ALARM: the breathing stops and
        // the LED blinks fast (test_alarms.cpp), at 0 or at the top - never
        // at a level in between, which would be the pulse going on
        const float top = powf(PULSE_MAX_LIGHT, LED_GAMMA);
        check(b.d.alarm() == Alarm::POSITION
                 && (b.m.level == 0.0f || std::fabs(b.m.level - top) < 1e-6f),
                 "failed: the pulse stops, and the position alarm takes over");
    }
    {
        Bench b;
        b.send("go 5");
        b.run(100);
        b.send("led test");
        b.run(300);
        check(!b.m.pwm, "the Morse test wins over the pulse");
    }
    return failures ? 1 : 0;
}
