#!/bin/sh
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: MIT

# Compile and run the tests on wheelly_protocol.h.
#
# No hardware, no Arduino, no INDI needed: just a compiler.
# Compiled with warnings on and treated as errors, because INDI's CI does the
# same and it is worth finding out here rather than in a pull request.
set -e
cd "$(dirname "$0")"

CXX="${CXX:-c++}"
"$CXX" -std=c++11 -Wall -Wextra -Werror -O1 \
       -o /tmp/wheelly_test_protocol test_protocol.cpp
exec /tmp/wheelly_test_protocol
