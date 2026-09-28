<!-- SPDX-FileCopyrightText: 2026 Matteo Beretta -->
<!-- SPDX-License-Identifier: LGPL-2.1-or-later -->

# The panel pictures

Tools for the INDI panel guide (docs/driver), run by the mechanical build.

1. `capture_panel.py OUT_DIR [indi_wheelly] [simulator]` - runs **on
   AstroArch** (the driver builds there, not on the Mac): the compiled driver
   under indiserver against the simulator, the same bench as
   `driver_bench.py`; records the XML it sends, in English and in Italian.
2. `draw_panel.py panel_en.xml OUT_DIR [scheme.colors]` - runs on the
   Mac: draws each tab with real Qt widgets (PySide6, in `doc/.venv`, not
   tracked) in the theme KStars has on AstroArch - Plasma **Breeze Dark**,
   Noto Sans. The colour scheme is KDE's and is not kept here: it is read from
   `~/Library/Application Support/kstars/themes/BreezeDark.colors`, copied
   from AstroArch's `/usr/share/color-schemes/BreezeDark.colors`.

It is a drawing of the panel, faithful in content and layout, not a KStars
screenshot.

To give KStars on the Mac the same theme, for comparing the drawing with the
real panel: that scheme file in its themes folder, and `currentTheme=Breeze Dark`
in the `[General]` group of `~/Library/Preferences/kstarsrc` (keep a copy of the
previous file).
