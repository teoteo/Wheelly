// SPDX-FileCopyrightText: 2026 Matteo Beretta
// SPDX-License-Identifier: MIT
//
// The two decisions of the sweep viewer (driver/indi-wheelly/doc/
// sweep_viewer.html) about how a magnet sweep is drawn, checked on their own:
//
//   - samples at the same angle - the wheel resting at a slot, every 'status'
//     a sample - are ONE point, not a vertical line of noise;
//   - the vertical window is at least 200 counts: the real wheel's 34-count
//     ripple (390..424) filled the plot and read as a collapse.
//
// They were checked in C++ while the driver drew the plot itself; the
// drawing moved to the viewer, and so did the check. The functions are read
// out of the page, between its two markers, so what is tested is what the
// page runs - not a copy.
//
//     node test_sweep_viewer.mjs
import { readFileSync } from "node:fs";

const page = readFileSync(new URL("../../driver/indi-wheelly/doc/sweep_viewer.html", import.meta.url), "utf8");
const start = page.indexOf("// --- the two decisions");
const end = page.indexOf("// --- end of the two decisions ---");
let failures = 0;
function check(condition, what, detail = "") {
  console.log(`  ${condition ? "ok     " : "FAILED:"} ${what}${condition ? "" : " -> " + detail}`);
  if (!condition) failures++;
}
console.log("\nThe sweep viewer's two decisions\n================================\n");
check(start > 0 && end > start, "the page has the block of the two decisions");
const { mergeSameAngle, verticalWindow } =
  new Function(page.slice(start, end) + "\nreturn { mergeSameAngle, verticalWindow };")();

// the wheel resting at 72 degrees for ten samples, noisy, then moving on
const resting = Array.from({ length: 10 }, (_, i) => [72.0 + (i % 2) * 0.05, 400 + (i % 3) * 6]);
const moving = [[10, 410], [40, 405], [100, 395], [140, 390]];
const merged = mergeSameAngle([...moving, ...resting]);
check(merged.length === moving.length + 1, "ten samples at the same angle are one point",
  `${merged.length} points`);
const at72 = merged.find(p => Math.abs(p[0] - 72) < 0.1);
const mean = resting.reduce((s, p) => s + p[1], 0) / resting.length;
check(at72 && Math.abs(at72[1] - mean) < 1e-9, "at their mean", JSON.stringify(at72));
check(merged.every((p, i) => i === 0 || p[0] > merged[i - 1][0]), "and the points come sorted by angle");
check(mergeSameAngle([[10, 400], [10.3, 410]]).length === 2,
  "samples 0.3 degrees apart stay two points");

// the reference wheel's ripple, 390..424: the window is not stretched to it
const [b, t] = verticalWindow(390, 424);
check(t - b >= 200, "a 34-count ripple gets a window of at least 200 counts", `${b}..${t}`);
check(b <= 390 && t >= 424 && Math.abs((b + t) / 2 - 407) <= 10, "centred on the data", `${b}..${t}`);
// a real drop of hundreds still gets a window that holds it
const [b2, t2] = verticalWindow(150, 800);
check(b2 <= 150 && t2 >= 800 && t2 - b2 < 800, "a real drop of hundreds fills the window, with a small margin",
  `${b2}..${t2}`);
check(verticalWindow(20, 60)[0] >= 0, "never below zero");

console.log(failures ? `\n${failures} FAILED` : "\nall passed");
process.exit(failures ? 1 : 0);
