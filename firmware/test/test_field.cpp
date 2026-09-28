// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT
//
// The AS5600's field flags ML and MH reach "status" and "diag" as the chip
// says them. They were sent as constants, ml=1 mh=0 - the usual reading with
// this magnet at 3.3 V - but ML also lights when the module's VDD5V-VDD3V3
// bridge breaks (hardware.md): a constant hid a diagnosis.
#include "../wheelly/dialog.h"
#include "../wheelly/wheel.h"

#include <cstdio>
#include <cstring>
#include <map>
#include <string>
#include <vector>

using namespace wheelly;

namespace {

class FakeMechanics : public Mechanics
{
    public:
        float angle() override { return 0.0f; }
        bool sensor_responds() override { return true; }
        bool magnet_seen() override { return true; }
        bool field_weak() override { return weak; }
        bool field_strong() override { return strong; }
        uint8_t agc() override { return 128; }
        uint16_t magnitude() override { return 800; }
        void move(long) override {}
        void stop() override {}
        bool is_moving() override { return false; }
        void enable(bool) override {}
        void currents(uint16_t, uint16_t) override {}
        void speed(uint32_t, uint32_t) override {}
        bool driver_responds() override { return true; }
        void led(bool) override {}
        void led_level(float) override {}
        uint32_t milliseconds() override { return 0; }
        bool weak {false}, strong {false};
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

class RecordingOutput : public Output
{
    public:
        void line(const char *r) override { lines.push_back(r); }
        std::vector<std::string> lines;
};

int failures = 0;

void check(bool condition, const char *what, const std::string &seen)
{
    std::printf("  %s %s%s%s\n", condition ? "ok" : "! ", what,
                condition ? "" : " -> ", condition ? "" : seen.c_str());
    if (!condition) failures++;
}

std::string ask(Dialog &d, RecordingOutput &u, const char *command)
{
    u.lines.clear();
    for (const char *p = command; *p; p++) d.receive(*p);
    d.receive('\n');
    std::string all;
    for (auto &r : u.lines) all += r + "\n";
    return all;
}

}  // namespace

int main()
{
    std::printf("the AS5600 field flags, as the chip reports them\n");
    FakeMechanics m;
    FakeStorage mem;
    RecordingOutput u;
    Wheel r {m, mem};
    Dialog d {r, u, "test", "0"};
    r.begin();

    const struct { bool weak, strong; const char *status, *diag; } cases[] = {
        {false, false, "ml=0 mh=0", "ml=0 mh=0"},
        {true,  false, "ml=1 mh=0", "ml=1 mh=0"},
        {false, true,  "ml=0 mh=1", "ml=0 mh=1"},
    };
    for (auto &c : cases) {
        m.weak = c.weak;
        m.strong = c.strong;
        std::string s = ask(d, u, "status");
        check(s.find(c.status) != std::string::npos, "status reports the field", s);
        s = ask(d, u, "diag");
        check(s.find(c.diag) != std::string::npos, "and so does diag", s);
    }
    std::printf("%s\n", failures ? "FAILED" : "all good");
    return failures ? 1 : 0;
}
