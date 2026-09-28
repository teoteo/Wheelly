// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// The real firmware, compiled for the PC.
//
// In here run the Wheel and the Dialog IDENTICAL to the ones that end up on
// the XIAO: the same files, not a copy. Only what is underneath changes - fake
// mechanics instead of AS5600, TMC2208 and pulse generator - and what is on
// top: stdin/stdout or a fake serial port, instead of USB.
//
// What it is for. The firmware can be tested without assembling the wheel, and
// above all the faults that real hardware produces when nobody wants them can
// be produced ON DEMAND: the clutch that slips, the sensor that goes silent
// halfway through a move, the magnet that disappears, the memory that will not
// write. And the tests are the SAME as the Python simulator's: if the firmware
// and the simulator did not behave the same way, one of them would be wrong
// and nobody would notice.
//
// The options are the simulator's, on purpose, so test_simulator.py runs
// against this binary without changing a line.

#include "../wheelly/dialog.h"
#include "../wheelly/wheel.h"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <random>
#include <string>

#include <fcntl.h>
#include <sys/select.h>
#include <sys/time.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <unistd.h>

#if defined(__APPLE__)
#include <util.h>
#else
#include <pty.h>
#endif

using namespace wheelly;

namespace {

struct Options {
    double slip {0.0};
    double slip_deg {2.0};
    double noise_deg {0.03};
    // Degrees per second the wheel moves ON ITS OWN when stopped: the case
    // where holding at rest is really needed. Zero: a wheel that stays put.
    double drift {0.0};
    bool   jammed {false};
    // An asymmetric detent left in place (the reference wheel before
    // the detent was removed for good): moving the way named here climbs
    // the steep flank, the motor stalls and hums and the disc stays put.
    // 0 = none, +1 = stalls going up, -1 = stalls going down.
    int    stall {0};
    // How far the disc really goes from what the firmware's declared ratio
    // promises, as a fraction. A bench disc that went exactly where the
    // estimate said never exercised the aim short and its creep-in: every test arrived at the first leg. -0.10 by
    // default, the side the real wheel is on (its legs moved 0.84-0.92 of
    // the estimate); +0.10 is the other end the firmware must survive.
    double ratio_error {-0.10};
    // Degrees of disc (at the declared ratio) every leg loses before the disc
    // moves: the give of the clutch's TPU tyre, which on the wheel absorbed
    // about 15 microsteps, 0.6 degrees, so that small creep legs did not move
    // the disc at all. It comes back at rest, with the
    // motor released, so every leg pays it again.
    double lost_motion {0.6};
    // A notch of a detent left in place that stalls a slow motor (at 50 full
    // steps/s the reference wheel stalled at some notches, at 100 and up it passed): a
    // leg slower than notch_min_speed that would cross notch_at stops half a
    // degree before it. Negative: no such notch.
    double notch_at {-1.0};
    double notch_min_speed {0.0};
    bool   sensor_silent {false};
    int    sensor_silent_after {-1};
    bool   no_magnet {false};
    // The magnet-detected bit flickering (the magnitude around the
    // AS5600's threshold): in the first 1.5 s of every 4 s it toggles
    // every magnet_flicker ms, then stays solid. 0 = never.
    double magnet_flicker {0.0};
    // The disc's inertia (`settle`): a disc whose motor lets go
    // sooner than coast_ms after its last step - EN high, or the driver's
    // current dropping below the run current - slides on by coast degrees
    // the way the leg went. Held at the run current for coast_ms, the stopped
    // motor has braked it through the tyre, and it stays. 0 = no coasting.
    double coast {0.0};
    double coast_ms {200.0};
    bool   nvs_broken {false};
    // What the NVS holds before the first start, "key=value,key=value"
    // (numbers only): a wheel saved by an older firmware (the
    // rotation trims o1..o12 of protocol 1, folded into the angles once).
    std::string nvs;
    // How many times the wheel starts on the same memory before the dialogue
    // begins: a fold that is not done ONCE shows at the second start.
    int    boots {1};
    unsigned seed {1};
    int    slots {FACTORY_SLOTS};
    double ms_per_deg {8.0};
    bool   pty {false};
    std::string link;
    std::string fw_version {"0.1.0-bench"};
    std::string serial {"51MUL470"};
};

uint32_t now_ms()
{
    struct timeval t;
    gettimeofday(&t, nullptr);
    return (uint32_t)(t.tv_sec * 1000ULL + t.tv_usec / 1000ULL);
}

// ---------------------------------------------------------- fake mechanics

class FakeMechanics : public Mechanics
{
    public:
        explicit FakeMechanics(const Options &o) : m_o(o), m_rng(o.seed), m_born(now_ms()) {}

        float angle() override
        {
            coast_check();
            // Drift is applied HERE and only when stopped: while the wheel
            // moves, the angle comes from the interpolation of the move, and
            // adding drift to it would mean measuring two things at once.
            if (m_o.drift != 0.0 && !m_moving) {
                const uint32_t now = now_ms();
                if (m_last_drift_ms != 0) {
                    const double seconds = (now - m_last_drift_ms) / 1000.0;
                    m_angle = norm(m_angle + m_o.drift * seconds);
                }
                m_last_drift_ms = now;
            }
            return (float)m_angle;
        }

        bool sensor_responds() override
        {
            if (m_o.sensor_silent) return false;
            return !(m_o.sensor_silent_after >= 0 && m_moves >= m_o.sensor_silent_after);
        }

        bool magnet_seen() override
        {
            if (m_o.no_magnet) return false;
            if (m_o.magnet_flicker > 0.0) {
                const uint32_t t = (now_ms() - m_born) % 4000;
                if (t < 1500) return ((uint32_t)(t / m_o.magnet_flicker)) % 2 == 1;
            }
            return true;
        }

        uint8_t agc() override
        {
            // With this magnet at 3.3 V the AGC stays at full scale at any
            // height: the bench finding that made us drop the AGC criterion in
            // favour of the magnitude. Here we lie the same way, otherwise the
            // tests would pass a firmware that trusts it.
            return 128;
        }

        // The weak-field flag goes with the AGC above: at full scale the chip
        // is asking for more field, and says so with ML. The simulator reports
        // ml=1 the same way, and the two halves are compared (the bench once
        // said 0 and the simulator 1, and nothing looked).
        bool field_weak() override { return true; }

        uint16_t magnitude() override
        {
            const double eccentricity = 25.0 * std::sin(m_angle * M_PI / 180.0);
            return (uint16_t)(810.0 + eccentricity);
        }

        void move(long microsteps) override
        {
            // The disc degrees come from the bench's OWN physics, not from
            // wheel.h's STEPS_PER_DEGREE. Dividing by the same
            // constant the firmware multiplies by made any error in it - a
            // missing ratio, a microstep counted twice - invisible here: the
            // fake disc always went exactly where the estimate said. These
            // are the wheel's own numbers: a 200-step motor, the driver at
            // 16 microsteps, a 50 mm clutch on the rim of a 145 mm disc - and
            // then off by --ratio-error, as the real disc is.
            const double motor_turns = microsteps / (200.0 * 16.0);
            const double nominal = motor_turns * 360.0 * (50.0 / 145.0);
            const double through = std::fmax(0.0, std::fabs(nominal) - m_o.lost_motion)
                                   * (1.0 + m_o.ratio_error);
            const double sign = nominal < 0 ? -1.0 : 1.0;
            double reach = through;
            if (m_o.notch_at >= 0.0 && m_speed_now < m_o.notch_min_speed) {
                const double to_notch = norm(sign * (m_o.notch_at - m_angle));
                if (to_notch < reach) reach = std::fmax(0.0, to_notch - 0.5);
            }
            const double degrees = sign * reach;
            m_from = m_angle;
            const bool stalled = (m_o.stall > 0 && nominal > 0) || (m_o.stall < 0 && nominal < 0);
            m_to = stalled ? m_angle : m_angle + degrees + aim_error(degrees);
            m_start = now_ms();
            m_duration = (uint32_t)(std::fabs(degrees) * m_o.ms_per_deg);
            m_moving = true;
            m_moves++;
        }

        void stop() override { m_moving = false; }

        bool is_moving() override
        {
            if (!m_moving) return false;
            const uint32_t elapsed = now_ms() - m_start;
            if (elapsed >= m_duration) {
                m_angle = norm(m_to);
                m_moving = false;
                // the disc has stopped: its inertia is damped only if the
                // motor holds it at the run current for coast_ms from now
                m_stop_ms = now_ms();
                m_coast_sign = m_to < m_from ? -1.0 : 1.0;
                m_coast_pending = m_o.coast > 0.0 && m_to != m_from;
                m_off_at = m_low_at = NEVER;
                note_drive();
                return false;
            }
            const double fraction = m_duration == 0 ? 1.0 : (double)elapsed / m_duration;
            m_angle = norm(m_from + (m_to - m_from) * fraction);
            return true;
        }

        void enable(bool on) override
        {
            coast_check();
            m_enabled = on;
            note_drive();
            coast_check();
        }
        void currents(uint16_t run, uint16_t hold) override
        {
            coast_check();
            m_run = run; m_hold = hold;
            note_drive();
            coast_check();
        }
        void speed(uint32_t steps_per_second, uint32_t) override
        {
            m_speed_now = steps_per_second;
        }
        bool driver_responds() override { return true; }
        void led(bool on) override { m_led = on; }
        uint32_t milliseconds() override { return now_ms(); }

    private:
        // The TMC2208's own drop from the run to the hold current, TPOWERDOWN
        // = 20 (its default, which the firmware leaves) x 2^18 clocks at
        // 12 MHz: 0.44 s after the last step. Modelled because the firmware
        // must not rely on it (Wheel::apply_currents).
        static constexpr uint32_t POWERDOWN_MS = 437;

        // Whether the disc, stopped since m_stop_ms, was let go before its
        // inertia was damped (coast_ms): then it slides on, once. Let go is
        // the earlier of EN going high and the current dropping below the
        // run current - which, with a hold current lower than the run one,
        // the chip does by itself POWERDOWN_MS after the last step, or at
        // once if the hold is lowered later than that.
        void coast_check()
        {
            if (!m_coast_pending || m_moving) return;
            const uint32_t since = now_ms() - m_stop_ms;
            uint32_t let_go = m_off_at;
            if (m_low_at != NEVER) {
                const uint32_t drop = m_low_at > POWERDOWN_MS ? m_low_at : POWERDOWN_MS;
                if (drop < let_go) let_go = drop;
            }
            if (let_go <= since) {
                if ((double)let_go < m_o.coast_ms)
                    m_angle = norm(m_angle + m_coast_sign * m_o.coast);
                m_coast_pending = false;
            } else if ((double)since >= m_o.coast_ms) {
                m_coast_pending = false;         // held long enough: damped
            }
        }
        // what happened to the drive since the stop, in ms after it
        void note_drive()
        {
            if (!m_coast_pending) return;
            const uint32_t since = now_ms() - m_stop_ms;
            if (!m_enabled && m_off_at == NEVER) m_off_at = since;
            if (m_hold < m_run && m_low_at == NEVER) m_low_at = since;
            if (m_hold >= m_run) m_low_at = NEVER;
        }
        static constexpr uint32_t NEVER = 0xFFFFFFFFu;

        double norm(double g) const
        {
            double r = std::fmod(g, 360.0);
            return r < 0 ? r + 360.0 : r;
        }

        // How far the target is missed. The error is proportional to the
        // length of the move, like the real play of a clutch: a one-degree
        // correction cannot slip like a seventy-degree travel. It is also what
        // makes the retries converge by themselves.
        double aim_error(double degrees)
        {
            if (m_o.jammed) return m_o.slip_deg;
            std::normal_distribution<double> noise(0.0, m_o.noise_deg);
            double e = noise(m_rng);
            std::uniform_real_distribution<double> die(0.0, 1.0);
            if (die(m_rng) < m_o.slip) {
                const double share = std::fmin(1.0, std::fabs(degrees) / 72.0);
                const double sign = die(m_rng) < 0.5 ? -1.0 : 1.0;
                e += sign * m_o.slip_deg * share;
            }
            return e;
        }

        const Options &m_o;
        std::mt19937 m_rng;
        double m_angle {0.0};
        double m_from {0.0}, m_to {0.0};
        uint32_t m_start {0}, m_duration {0};
        bool m_moving {false};
        uint32_t m_last_drift_ms {0};
        bool m_enabled {false}, m_led {false};
        uint32_t m_stop_ms {0};
        double m_coast_sign {1.0};
        bool m_coast_pending {false};
        uint32_t m_off_at {0}, m_low_at {0};
        uint16_t m_run {150}, m_hold {0};
        int m_moves {0};
        double m_speed_now {0.0};
        uint32_t m_born;
};

// ------------------------------------------------------------- fake memory

class FakeMemory : public Storage
{
    public:
        explicit FakeMemory(const Options &o) : m_o(o)
        {
            // A wheel with a different number of positions is not a program
            // option: it is a wheel that has that number written in its
            // memory. Here the fake memory is seeded, which is exactly what
            // the firmware would find when switched on in that wheel.
            m_numbers["slots"] = (float)o.slots;
            // the seed, as an older firmware would have left it
            size_t at = 0;
            while (at < o.nvs.size()) {
                size_t end = o.nvs.find(',', at);
                if (end == std::string::npos) end = o.nvs.size();
                const std::string pair = o.nvs.substr(at, end - at);
                const size_t eq = pair.find('=');
                if (eq != std::string::npos)
                    m_numbers[pair.substr(0, eq)] = (float)std::atof(pair.c_str() + eq + 1);
                at = end + 1;
            }
        }

        bool load(const char *key, float &value) override
        {
            const auto t = m_numbers.find(key);
            if (t == m_numbers.end()) return false;
            value = t->second;
            return true;
        }
        bool load(const char *key, const char *&value) override
        {
            const auto t = m_texts.find(key);
            if (t == m_texts.end()) return false;
            value = t->second.c_str();
            return true;
        }
        bool store(const char *key, float value) override
        {
            if (m_o.nvs_broken) return false;
            m_numbers[key] = value;
            return true;
        }
        bool store(const char *key, const char *value) override
        {
            if (m_o.nvs_broken) return false;
            m_texts[key] = value;
            return true;
        }
        bool erase(const char *key) override
        {
            if (m_o.nvs_broken) return false;
            m_numbers.erase(key);
            m_texts.erase(key);
            return true;
        }
        bool commit() override { return !m_o.nvs_broken; }

    private:
        const Options &m_o;
        std::map<std::string, float> m_numbers;
        std::map<std::string, std::string> m_texts;
};

// --------------------------------------------------------------- transport

class FdOutput : public Output
{
    public:
        explicit FdOutput(int fd) : m_fd(fd) {}
        void line(const char *text) override
        {
            const std::string r = std::string(text) + "\n";
            ssize_t written = 0;
            const char *p = r.c_str();
            size_t left = r.size();
            while (left > 0 && (written = write(m_fd, p, left)) > 0) {
                p += written;
                left -= (size_t)written;
            }
        }
    private:
        int m_fd;
};

bool option_arg(int argc, char **argv, int &i, const char *name, std::string &out)
{
    if (std::strcmp(argv[i], name) != 0) return false;
    if (i + 1 >= argc) { std::fprintf(stderr, "missing value for %s\n", name); std::exit(2); }
    out = argv[++i];
    return true;
}

}  // namespace

int main(int argc, char **argv)
{
    Options o;
    std::string v;
    for (int i = 1; i < argc; i++) {
        if (option_arg(argc, argv, i, "--slip", v))            o.slip = std::atof(v.c_str());
        else if (option_arg(argc, argv, i, "--slip-degrees", v)) o.slip_deg = std::atof(v.c_str());
        else if (option_arg(argc, argv, i, "--noise-degrees", v))      o.noise_deg = std::atof(v.c_str());
        else if (option_arg(argc, argv, i, "--drift", v))            o.drift = std::atof(v.c_str());
        else if (option_arg(argc, argv, i, "--magnet-flicker", v))   o.magnet_flicker = std::atof(v.c_str());
        else if (option_arg(argc, argv, i, "--sensor-silent-after", v)) o.sensor_silent_after = std::atoi(v.c_str());
        else if (option_arg(argc, argv, i, "--seed", v))              o.seed = (unsigned)std::atoi(v.c_str());
        else if (option_arg(argc, argv, i, "--slots", v))             o.slots = std::atoi(v.c_str());
        else if (option_arg(argc, argv, i, "--ms-per-degree", v))      o.ms_per_deg = std::atof(v.c_str());
        else if (option_arg(argc, argv, i, "--link", v))      o.link = v;
        else if (option_arg(argc, argv, i, "--fw-version", v))       o.fw_version = v;
        else if (option_arg(argc, argv, i, "--serial", v))           o.serial = v;
        else if (option_arg(argc, argv, i, "--ratio-error", v)) o.ratio_error = std::atof(v.c_str());
        else if (option_arg(argc, argv, i, "--lost-motion", v)) o.lost_motion = std::atof(v.c_str());
        else if (option_arg(argc, argv, i, "--notch-at", v)) o.notch_at = std::atof(v.c_str());
        else if (option_arg(argc, argv, i, "--notch-min-speed", v)) o.notch_min_speed = std::atof(v.c_str());
        else if (option_arg(argc, argv, i, "--nvs", v))       o.nvs = v;
        else if (option_arg(argc, argv, i, "--coast", v))     o.coast = std::atof(v.c_str());
        else if (option_arg(argc, argv, i, "--coast-ms", v))  o.coast_ms = std::atof(v.c_str());
        else if (option_arg(argc, argv, i, "--boots", v))     o.boots = std::atoi(v.c_str());
        else if (option_arg(argc, argv, i, "--stall", v))     o.stall = v == "up" ? 1 : v == "down" ? -1 : 0;
        else if (std::strcmp(argv[i], "--stuck") == 0)      o.jammed = true;
        else if (std::strcmp(argv[i], "--sensor-silent") == 0)  o.sensor_silent = true;
        else if (std::strcmp(argv[i], "--no-magnet") == 0) o.no_magnet = true;
        else if (std::strcmp(argv[i], "--nvs-broken") == 0)     o.nvs_broken = true;
        else if (std::strcmp(argv[i], "--pty") == 0)           o.pty = true;
        // options the simulator has and that are not needed here are ignored
        // silently, so the same tests run against both
        else if (std::strncmp(argv[i], "--", 2) == 0 && i + 1 < argc &&
                 std::strncmp(argv[i + 1], "--", 2) != 0) i++;
    }

    int rd = STDIN_FILENO, wr = STDOUT_FILENO;
    int slave = -1;
    if (o.pty) {
        int master = -1;
        if (openpty(&master, &slave, nullptr, nullptr, nullptr) != 0) {
            std::perror("openpty");
            return 2;
        }
        // The pty must be put in RAW mode on both ends. Without it, the line
        // discipline echoes back what the driver writes and translates line
        // endings: the driver ends up reading its own commands as if they were
        // replies, never finds a result, and times out with nothing looking
        // broken. An hour lost for two lines.
        for (int fd : {master, slave}) {
            struct termios mode;
            if (tcgetattr(fd, &mode) == 0) {
                cfmakeraw(&mode);
                tcsetattr(fd, TCSANOW, &mode);
            }
        }
        const char *name = ttyname(slave);
        if (!o.link.empty()) {
            unlink(o.link.c_str());
            if (symlink(name, o.link.c_str()) != 0) std::perror("symlink");
        }
        std::printf("fake serial port ready: %s\n", name);
        if (!o.link.empty())
            std::printf("stable link: %s\n", o.link.c_str());
        std::printf("point the INDI driver here. Ctrl-C to close.\n");
        std::fflush(stdout);
        rd = wr = master;
    }

    FakeMechanics mechanics(o);
    FakeMemory memory(o);
    // the earlier starts on the same memory, each a whole Wheel as at a
    // power-up; the last one is the wheel the dialogue talks to
    for (int b = 1; b < o.boots; b++) {
        Wheel earlier(mechanics, memory);
        earlier.begin();
    }
    Wheel wheel(mechanics, memory);
    FdOutput output(wr);
    Dialog dialog(wheel, output, o.fw_version.c_str(), o.serial.c_str());

    wheel.begin();

    for (;;) {
        // The main loop is the same the XIAO will have: advance the wheel's
        // time, send the events, and digest the bytes that arrived. It never
        // blocks on a read, because 'status' must be able to answer while the
        // wheel is moving.
        wheel.step();
        dialog.step();

        // Give up the fake serial port's exclusivity, continuously. When INDI
        // opens a port it marks it exclusive with TIOCEXCL; on disconnect it
        // closes its descriptor, but we keep ours open - otherwise the pty
        // would vanish - and the port keeps the mark. From then on nobody can
        // open it: it connects the first time and never again.
        if (slave >= 0) ioctl(slave, TIOCNXCL);

        fd_set fds;
        FD_ZERO(&fds);
        FD_SET(rd, &fds);
        struct timeval timeout {0, 2000};
        if (select(rd + 1, &fds, nullptr, nullptr, &timeout) > 0) {
            char chunk[256];
            const ssize_t got = read(rd, chunk, sizeof(chunk));
            if (got <= 0) {
                if (got == 0 && !o.pty) break;   // stdin closed: stop
                if (got < 0 && errno != EINTR && errno != EAGAIN) break;
            }
            for (ssize_t i = 0; i < got; i++) dialog.receive(chunk[i]);
        }
    }

    if (!o.link.empty()) unlink(o.link.c_str());
    if (slave >= 0) close(slave);
    return 0;
}
