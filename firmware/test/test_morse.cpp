// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// The LED test blinks "WHEELLY" in Morse: is the sequence the right one, unit
// by unit?
//
// Why it exists. "Blinks Wheelly" from KStars, with the LED wired up, once
// showed a sequence that was not WHEELLY. The letter table
// and the total duration were right - and those were the only two things the
// tests looked at. The on/off in between was wrong: every pause lit the LED.
//
// The expected sequence is built HERE, from the international Morse table
// written in this file, not from the firmware's own table: a test that read
// the firmware's table would agree with any mistake made in it.
#include "../wheelly/dialog.h"

#include <cstdio>
#include <cstring>
#include <string>

using namespace wheelly;

static const char *code(char letter)
{
    switch (letter) {
        case 'W': return ".--";
        case 'H': return "....";
        case 'E': return ".";
        case 'L': return ".-..";
        case 'Y': return "-.--";
    }
    return "";
}

int main()
{
    // dot 1 unit on, dash 3 on, 1 off between symbols, 3 off between letters
    std::string expected;
    const char *word = "WHEELLY";
    for (size_t i = 0; word[i]; i++) {
        const char *c = code(word[i]);
        for (size_t j = 0; c[j]; j++) {
            expected += (c[j] == '-') ? "111" : "1";
            if (c[j + 1]) expected += "0";
        }
        if (word[i + 1]) expected += "000";
    }

    int failures = 0;
    std::string seen;
    for (uint32_t u = 0; u < expected.size() + 5; u++) seen += morse_lit(u) ? '1' : '0';
    const std::string expected_with_tail = expected + "00000";
    if (seen != expected_with_tail) {
        std::printf("  !  the LED sequence is not WHEELLY\n     expected %s\n     seen     %s\n",
                    expected_with_tail.c_str(), seen.c_str());
        failures++;
    } else {
        std::printf("  ok the LED sequence is WHEELLY, %zu units\n", expected.size());
    }
    if (morse_duration_ms() != expected.size() * 100u) {
        std::printf("  !  duration %u ms, %zu needed\n", (unsigned)morse_duration_ms(), expected.size() * 100);
        failures++;
    } else {
        std::printf("  ok duration %u ms\n", (unsigned)morse_duration_ms());
    }
    return failures ? 1 : 0;
}
