// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT
//
// The sweep plot of the INDI driver (driver/indi-wheelly/plot.cpp), on the
// Mac: plot.cpp needs no INDI, so its two decisions are checked here, next to
// the firmware tests that produce the samples it draws.
//
//   - samples at the same angle - the wheel resting at a slot, every 'status'
//     a sample - are ONE point, not a vertical line of noise;
//   - the vertical window is at least 200 counts: the real wheel's 34-count
//     ripple (390..424) filled the plot and read as a collapse.
//
// If the sweep_png below is written with an argument, the PNG is saved there,
// to be looked at.
#include "../../driver/indi-wheelly/plot.h"

#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

using namespace wheelly;

namespace {
int failures = 0;
void check(bool condition, const char *what)
{
    std::printf("  %s %s\n", condition ? "ok" : "! ", what);
    if (!condition) failures++;
}
}  // namespace

int main(int argc, char **argv)
{
    std::printf("the sweep plot\n");

    // a sweep of the real wheel: moving samples every 3 degrees, and twenty
    // samples resting at each of five slots, with the magnitude's noise
    std::vector<Sample> s;
    const double slots[] = {52.0, 122.9, 197.6, 266.3, 339.8};
    for (double a = 1.5; a < 360; a += 3.0)
        s.push_back({a, 407.0 + 17.0 * std::sin(a * M_PI / 180.0)});
    for (double slot : slots)
        for (int i = 0; i < 20; i++)
            s.push_back({slot, 407.0 + 17.0 * std::sin(slot * M_PI / 180.0) + ((i % 5) - 2) * 3.0});

    const std::vector<Sample> p = plot_points(s);
    int at_slots = 0;
    bool sorted = true;
    for (size_t i = 0; i < p.size(); i++) {
        for (double slot : slots) if (std::fabs(p[i].angle - slot) < 1e-9) at_slots++;
        if (i > 0 && p[i].angle <= p[i - 1].angle) sorted = false;
    }
    check(at_slots == 5, "twenty samples at a resting slot are one point, not a vertical line");
    check(sorted, "and the points are sorted by angle, never two at the same one");
    check(p.size() == 120 + 5, "the moving samples all stay, one point each");
    bool mean_ok = false;
    for (const Sample &x : p)
        if (std::fabs(x.angle - 52.0) < 1e-9)
            mean_ok = std::fabs(x.magnitude - (407.0 + 17.0 * std::sin(52.0 * M_PI / 180.0))) < 1e-6;
    check(mean_ok, "the point is the mean of the samples taken there");

    double low = 0, high = 0;
    plot_window(390, 424, low, high);
    check(high - low >= 200.0 - 1e-9 && low <= 390 && high >= 424,
          "a 34-count ripple gets a window of at least 200 counts, around the data");
    plot_window(0, 20, low, high);
    check(low >= 0.0 && high - low >= 200.0 - 1e-9, "the window never goes below zero");
    plot_window(100, 900, low, high);
    check(low < 100 && high > 900 && high - low < 1000,
          "a real drop of hundreds still fills the plot, with a small margin");

    if (argc > 1) {
        PlotLabels l {"MAGNET SWEEP", "ANGLE (DEG)", "MAGNITUDE", "SAMPLES", "SPAN", "MIN", "MAX"};
        std::vector<double> angles(slots, slots + 5);
        const std::string png = sweep_png(s, angles, l);
        FILE *f = std::fopen(argv[1], "wb");
        if (f) { std::fwrite(png.data(), 1, png.size(), f); std::fclose(f); }
    }

    std::printf(failures ? "%d FAILED\n" : "all passed\n", failures);
    return failures ? 1 : 0;
}
