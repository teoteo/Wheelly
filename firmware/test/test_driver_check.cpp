// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// The rule that says whether the motor driver still holds the firmware's
// setup (judge_driver, mechanics.h), one reading at a time.
//
// The bench (test_simulator.py, "the motor's 12 V") shows the rule at work
// against a fake register file, but there a reset trips GSTAT and GCONF
// together, so either witness alone would pass it. Here each one is tried
// alone: a rule that lost one of them would fail a line of this file.

#include "../wheelly/mechanics.h"

#include <cstdio>

using namespace wheelly;

namespace {

int failures = 0;
int checks = 0;

const char *name(DriverState s)
{
    switch (s) {
        case DriverState::READY: return "READY";
        case DriverState::UNSET: return "UNSET";
        default:                 return "SILENT";
    }
}

void expect(const char *what, uint8_t version, uint8_t gstat, uint32_t gconf, DriverState want)
{
    DriverReadback r;
    r.version = version;
    r.gstat = gstat;
    r.gconf = gconf;
    const DriverState got = judge_driver(r);
    checks++;
    if (got != want) {
        failures++;
        std::printf("  FAILED: %s -> %s, expected %s\n", what, name(got), name(want));
    }
}

}  // namespace

int main()
{
    const uint32_t set = tmc::GCONF_CONFIGURED;
    // multistep_filt (bit 8) is 1 after a reset and the setup leaves it:
    // a bit the setup does not write must not decide anything
    const uint32_t filt = 1u << 8;

    expect("a TMC2208 with our setup", tmc::VERSION_2208, 0, set, DriverState::READY);
    expect("a TMC2209 with our setup", tmc::VERSION_2209, 0, set, DriverState::READY);
    expect("a bit the setup leaves alone changes nothing", tmc::VERSION_2208, 0,
           set | filt, DriverState::READY);

    // nobody answering: the library returns 0 on a bad CRC, a floating line
    // may read all ones
    expect("no answer (version 0)", 0x00, 0, set, DriverState::SILENT);
    expect("a line reading all ones", 0xFF, 0xFF, 0xFFFFFFFFu, DriverState::SILENT);
    expect("another chip's version", 0x30, 0, set, DriverState::SILENT);

    // the first witness alone: GSTAT.reset set, GCONF still reading as ours
    expect("GSTAT.reset set, GCONF as written", tmc::VERSION_2208, tmc::GSTAT_RESET, set,
           DriverState::UNSET);
    // the other GSTAT flags are not a reset: drv_err and uv_cp
    expect("GSTAT drv_err alone is not a reset", tmc::VERSION_2208, 1u << 1, set,
           DriverState::READY);
    expect("GSTAT uv_cp alone is not a reset", tmc::VERSION_2208, 1u << 2, set,
           DriverState::READY);

    // the second witness alone, bit by bit: GSTAT clear, one GCONF bit off
    expect("GCONF at its reset values", tmc::VERSION_2208, 0, tmc::GCONF_RESET | filt,
           DriverState::UNSET);
    expect("i_scale_analog back on (VREF sets the current)", tmc::VERSION_2208, 0,
           set | tmc::GCONF_I_SCALE_ANALOG, DriverState::UNSET);
    expect("en_spreadcycle on", tmc::VERSION_2208, 0,
           set | tmc::GCONF_EN_SPREADCYCLE, DriverState::UNSET);
    expect("pdn_disable off (the pin is PDN again)", tmc::VERSION_2208, 0,
           set & ~tmc::GCONF_PDN_DISABLE, DriverState::UNSET);
    expect("mstep_reg_select off (MS1/MS2 set the microsteps)", tmc::VERSION_2208, 0,
           set & ~tmc::GCONF_MSTEP_REG_SELECT, DriverState::UNSET);
    expect("GCONF read as 0 (a read that failed its CRC)", tmc::VERSION_2208, 0, 0,
           DriverState::UNSET);

    std::printf("%d checks, %d failed\n", checks, failures);
    return failures == 0 ? 0 : 1;
}
