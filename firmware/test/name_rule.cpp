// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT

// Exposes the filter naming rule of wheelly_protocol.h to whoever cannot
// include a C++ header - i.e. the simulator, which is in Python.
//
// Reads one line per name, hex-encoded (so that bytes that would not fit in a
// text line, like 0x0A or 0xFF, get through too), and prints the result of
// check_filter_name(). It serves the cross-check: the rule in Python is a copy,
// and a copy that nobody compares with the original drifts sooner or later.

#include "../wheelly/wheelly_protocol.h"

#include <cstdio>
#include <cstring>
#include <string>
#include <iostream>

int main()
{
    std::string line;
    while (std::getline(std::cin, line)) {
        std::string name;
        bool valid = (line.size() % 2 == 0);
        for (size_t i = 0; valid && i + 1 < line.size(); i += 2) {
            int hi = std::isxdigit((unsigned char)line[i])
                       ? (line[i] <= '9' ? line[i] - '0'
                                         : (line[i] | 32) - 'a' + 10) : -1;
            int lo = std::isxdigit((unsigned char)line[i + 1])
                        ? (line[i + 1] <= '9' ? line[i + 1] - '0'
                                              : (line[i + 1] | 32) - 'a' + 10) : -1;
            if (hi < 0 || lo < 0) { valid = false; break; }
            name.push_back((char)(hi * 16 + lo));
        }
        if (!valid) { std::printf("-1\n"); continue; }
        std::printf("%d\n", (int)wheelly::check_filter_name(name.c_str()));
        std::fflush(stdout);
    }
    return 0;
}
