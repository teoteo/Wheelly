// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT
//
// The LED's alarm signals, on the firmware's own code
// with fake time: fast blinking when the wheel did not reach its slot, two
// flashes every 2 s for a drift at rest, three for a lost magnet; one at a
// time, the gravest; none with the LED in "off" mode - which is also how the
// wheel is turned by hand with no current in the motor, and a hand-turned
// wheel drifts by definition.
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
        bool magnet_seen() override { return magnet; }
        uint8_t agc() override { return 128; }
        uint16_t magnitude() override { return magnet ? 800 : 0; }
        void move(long steps) override
        {
            const double degrees = steps / (double)steps_per_degree(FACTORY_DRIVE_RATIO);
            m_from = m_angle; m_to = m_angle + degrees;
            m_start = clock; m_duration = (uint32_t)(std::fabs(degrees) * 20.0);
            m_moving = !jammed;
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
        void led(bool on) override { level = on ? 1.0f : 0.0f; }
        void led_level(float f) override { level = f; }
        uint32_t milliseconds() override { return clock; }

        void push(double degrees) { m_angle = norm(m_angle + degrees); }   // a hand, at rest

        float level {0.0f};
        bool jammed {false};
        bool magnet {true};

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

const float TOP = powf(PULSE_MAX_LIGHT, LED_GAMMA);

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
    // runs for ms and counts how many times the LED went from dark to lit;
    // `always_dark` says whether it stayed at 0 the whole time
    int run(uint32_t ms, bool *always_dark = nullptr)
    {
        int lightings = 0;
        bool on = m.level > 0.0f, dark = true;
        for (uint32_t t = 0; t < ms; t += 5) {
            clock += 5;
            r.step();
            d.step();
            const bool now = m.level > 0.0f;
            if (now) dark = false;
            if (now && !on) lightings++;
            on = now;
        }
        if (always_dark) *always_dark = dark;
        return lightings;
    }
};

}  // namespace

int main()
{
    std::printf("the LED's alarm signals\n");

    // --- the patterns, as a pure function ---------------------------------
    {
        auto count = [](Alarm a, uint32_t duration) {
            int n = 0; bool before = false;
            for (uint32_t ms = 0; ms < duration; ms++) {
                const bool now = alarm_lit(a, ms);
                if (now && !before) n++;
                before = now;
            }
            return n;
        };
        check(count(Alarm::POSITION, 1000) == 4, "position: 4 blinks a second");
        check(count(Alarm::DRIFT, 2000) == 2, "drift: 2 flashes every 2 s");
        check(count(Alarm::MAGNET, 2000) == 3, "magnet: 3 flashes every 2 s");
        check(count(Alarm::NONE, 5000) == 0, "no alarm: never lit");
    }

    // --- the wheel does not get there ---------------------------------------
    {
        Bench b;
        b.m.jammed = true;
        b.send("go 3");
        b.run(60000);
        check(b.d.alarm() == Alarm::POSITION, "a failed move raises the position alarm");
        const int n = b.run(2000);
        check(n >= 7 && n <= 9, "and the LED blinks 4 a second");
        check(b.m.level == 0.0f || std::fabs(b.m.level - TOP) < 1e-6f,
                 "at the top of the pulse, not brighter");
        b.m.jammed = false;
        b.send("go 2");
        check(b.d.alarm() == Alarm::NONE, "sending it again ends the alarm");
        b.run(20000);
        bool dark_all = false;
        b.run(3000, &dark_all);
        check(dark_all, "and once there the LED is dark again (pulse mode, at rest)");
    }

    // --- the wheel is set right by hand after a failure --------
    // The docs promised the fast blinking ends "when the wheel reaches a slot",
    // and the code ended it only on `go` or a new verdict: a wheel turned by
    // hand onto a slot went on blinking.
    {
        Bench b;
        b.m.jammed = true;
        b.send("go 3");               // stuck on slot 1: it failed, and stays there
        b.run(60000);
        b.run(2000);
        check(b.d.alarm() == Alarm::POSITION,
                 "stuck on its old slot, the alarm stays: that slot was not reached");
        b.m.push(144.0);             // by hand, onto slot 3 (5 slots, 72 degrees apart)
        b.run(500);
        check(b.d.alarm() == Alarm::NONE,
                 "turned by hand onto a slot, the fast blinking ends");
    }
    {
        Bench b;
        b.m.jammed = true;
        b.send("go 3");
        b.run(60000);
        b.m.push(30.0);              // by hand, between slots
        b.run(500);
        check(b.d.alarm() == Alarm::POSITION, "between two slots the alarm stays");
        b.m.push(-30.0);             // and back onto its old slot: now it counts
        b.run(500);
        check(b.d.alarm() == Alarm::NONE,
                 "brought back by hand onto a slot it had left, it ends too");
    }

    // --- a drift at rest ----------------------------------------------------
    {
        Bench b;
        b.send("go 2");
        b.run(20000);
        b.m.push(5.0);
        b.run(15000);
        check(b.d.alarm() == Alarm::DRIFT, "a drift at rest raises the drift alarm");
        const int n = b.run(4000);
        check(n == 4, "and the LED flashes twice every 2 s");
        b.send("go 2");
        check(b.d.alarm() == Alarm::NONE, "sending the wheel somewhere ends it");
    }

    // --- the magnet is lost, and comes back ----------------------------------
    {
        Bench b;
        b.run(1000);
        b.m.magnet = false;
        b.run(3000);
        check(b.d.alarm() == Alarm::MAGNET, "a lost magnet raises the magnet alarm");
        const int n = b.run(4000);
        check(n == 6, "and the LED flashes three times every 2 s");
        b.m.push(5.0);               // a drift now must not take its place
        b.run(15000);
        check(b.d.alarm() == Alarm::MAGNET, "a lesser alarm does not replace it");
        // a flickering MD bit (the magnitude around the chip's threshold)
        // keeps the alarm on: seen for a moment is not found again
        for (int i = 0; i < 100; i++) { b.m.magnet = (i % 2) == 0; b.run(20); }
        check(b.d.alarm() == Alarm::MAGNET, "a flickering magnet keeps the alarm on");
        b.m.magnet = true;
        b.run(MAGNET_REARM_MS / 2);
        check(b.d.alarm() == Alarm::MAGNET, "and half a second of magnet is not enough");
        b.run(MAGNET_REARM_MS + MAGNET_CHECK_MS);
        check(b.d.alarm() != Alarm::MAGNET, "the magnet seen again without a break ends it");
    }

    // --- "off" means off: no signal at all ------------------------------------
    {
        Bench b;
        b.send("led off");
        b.m.jammed = true;
        b.send("go 3");
        b.run(60000);
        bool dark_all = false;
        b.run(3000, &dark_all);
        check(dark_all, "LED off: a failed move shows nothing");
        b.m.jammed = false;
        b.send("go 1");
        b.run(20000);
        b.m.push(10.0);              // a hand turning the wheel, no current
        b.run(15000, &dark_all);
        check(dark_all, "LED off: turning the wheel by hand shows nothing");
    }

    std::printf("%s\n", failures ? "FAILED" : "all good");
    return failures ? 1 : 0;
}
