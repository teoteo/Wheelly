#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Draw the driver's INDI panel from the XML it really sends, with real Qt
widgets, in the look of KStars on AstroArch.

WHERE THE PANEL COMES FROM: capture_panel.py, which runs the compiled
driver under indiserver against the simulator and records its XML - so the
tabs, the order, the labels and the permissions are the driver's own, and the
pictures follow the driver when a command is added or removed.

WHAT IT LOOKS LIKE: KStars' INDI control panel (one tab per group; per
property a state light, the label, the elements, and a Set button where the
property can be written) in the theme AstroArch runs - Plasma's Breeze Dark
colour scheme, read from BreezeDark.colors (copied from AstroArch, where KStars
follows the desktop), with Noto Sans. It is a DRAWING of the panel, faithful
in content and layout, not a screenshot of KStars: widths and spacing are
close, not identical to the pixel.

    python draw_panel.py panel_en.xml OUT_DIR [BreezeDark.colors]

Writes one PNG per tab: OUT_DIR/<lang>-<n>-<tab>.png, and one per property:
OUT_DIR/<lang>-<property-name>.png, the portions the guide shows
"""
import configparser
import os
import re
import sys
import xml.etree.ElementTree as ET

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt                                  # noqa: E402
from PySide6.QtGui import QColor, QFont, QPalette, QPainter    # noqa: E402
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,  # noqa: E402
                               QFrame, QGridLayout, QSlider,
                               QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QScrollArea, QTabWidget, QTextEdit, QVBoxLayout,
                               QWidget)

HERE = os.path.dirname(os.path.abspath(__file__))
STATES = {"Idle": "#808080", "Ok": "#27ae60", "Busy": "#f67400", "Alert": "#da4453"}


def read_panel(xml_file):
    """The properties in declaration order, with the values of the last update."""
    # the capture runs in a bench with a home of its own, a temporary folder:
    # in a guide those paths mean nothing, so they are drawn as the home of
    # the user AstroArch runs KStars as - where the files really go. Both
    # prefixes: the bench's home was once "wheelly-prove-", and a panel
    # captured with that name still has it
    text = open(xml_file, encoding="utf-8").read()
    text = re.sub(r"/tmp/wheelly-(?:bench|prove)-[^/<\s]+", "/home/astronaut", text)
    root = ET.fromstring(text)
    prop, order = {}, []
    for e in root:
        m = re.match(r"^(def|set)(Number|Text|Switch|Light|BLOB)Vector$", e.tag)
        if not m:
            continue
        n = e.get("name")
        if m.group(1) == "def" and n not in prop:
            prop[n] = dict(kind=m.group(2), group=e.get("group", ""), label=e.get("label", n),
                           perm=e.get("perm", "ro"), rule=e.get("rule", ""),
                           state=e.get("state", "Idle"), el=[])
            for k in e:
                prop[n]["el"].append(dict(name=k.get("name"), label=k.get("label") or k.get("name"),
                                          value=(k.text or "").strip(), fmt=k.get("format", ""),
                                          min=k.get("min"), max=k.get("max"), step=k.get("step")))
            order.append(n)
        elif n in prop:
            prop[n]["state"] = e.get("state", prop[n]["state"])
            vals = {k.get("name"): (k.text or "").strip() for k in e}
            for el in prop[n]["el"]:
                if el["name"] in vals:
                    el["value"] = vals[el["name"]]
    groups = []
    for n in order:
        if prop[n]["group"] not in groups:
            groups.append(prop[n]["group"])
    return prop, order, groups


def palette(colors_file):
    """A QPalette from a KDE colour scheme file."""
    c = configparser.ConfigParser(interpolation=None, strict=False)
    c.optionxform = str
    c.read(colors_file)

    def col(section, key):
        r, g, b = (int(x) for x in c[section][key].split(",")[:3])
        return QColor(r, g, b)
    p = QPalette()
    for group in (QPalette.Active, QPalette.Inactive):
        p.setColor(group, QPalette.Window, col("Colors:Window", "BackgroundNormal"))
        p.setColor(group, QPalette.WindowText, col("Colors:Window", "ForegroundNormal"))
        p.setColor(group, QPalette.Base, col("Colors:View", "BackgroundNormal"))
        p.setColor(group, QPalette.AlternateBase, col("Colors:View", "BackgroundAlternate"))
        p.setColor(group, QPalette.Text, col("Colors:View", "ForegroundNormal"))
        p.setColor(group, QPalette.Button, col("Colors:Button", "BackgroundNormal"))
        p.setColor(group, QPalette.ButtonText, col("Colors:Button", "ForegroundNormal"))
        p.setColor(group, QPalette.Highlight, col("Colors:Selection", "BackgroundNormal"))
        p.setColor(group, QPalette.HighlightedText, col("Colors:Selection", "ForegroundNormal"))
        p.setColor(group, QPalette.ToolTipBase, col("Colors:Tooltip", "BackgroundNormal"))
        p.setColor(group, QPalette.ToolTipText, col("Colors:Tooltip", "ForegroundNormal"))
        p.setColor(group, QPalette.Light, col("Colors:Button", "BackgroundAlternate"))
        p.setColor(group, QPalette.Mid, col("Colors:Window", "BackgroundAlternate"))
        p.setColor(group, QPalette.Dark, col("Colors:Window", "BackgroundAlternate").darker(140))
        p.setColor(group, QPalette.Link, col("Colors:View", "ForegroundLink"))
    p.setColor(QPalette.Disabled, QPalette.Text, col("Colors:View", "ForegroundInactive"))
    p.setColor(QPalette.Disabled, QPalette.WindowText, col("Colors:Window", "ForegroundInactive"))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, col("Colors:Button", "ForegroundInactive"))
    return p


class Light(QWidget):
    """The round state light KStars draws beside each property."""

    def __init__(self, state):
        super().__init__()
        self.colore = QColor(STATES.get(state, STATES["Idle"]))
        self.setFixedSize(18, 18)

    def paintEvent(self, _):
        q = QPainter(self)
        q.setRenderHint(QPainter.Antialiasing)
        q.setBrush(self.colore)
        q.setPen(self.colore.darker(160))
        q.drawEllipse(2, 2, 14, 14)


def number(v, fmt):
    """An INDI number shown with its printf format, as KStars does (%m sexagesimal aside)."""
    try:
        x = float(v)
    except ValueError:
        return v
    if fmt and "m" not in fmt:
        try:
            return (fmt % x).strip()
        except (TypeError, ValueError):
            pass
    return ("%g" % x)


def has_slider(el):
    """KStars' rule for a writable number: spin box and slider when the range
    is at most 100 steps, a text field otherwise."""
    try:
        lo, hi, st = float(el["min"]), float(el["max"]), float(el["step"])
    except (TypeError, ValueError):
        return False
    return st != 0 and (hi - lo)/st <= 100


def property_row(p):
    """One property: light, label, elements, Set."""
    row = QWidget()
    h = QHBoxLayout(row)
    h.setContentsMargins(0, 2, 0, 2)
    h.addWidget(Light(p["state"]), 0, Qt.AlignTop)
    et = QLabel(p["label"])
    et.setFixedWidth(170)
    et.setWordWrap(True)
    h.addWidget(et, 0, Qt.AlignTop)
    body = QWidget()
    writable = p["perm"] != "ro"
    if p["kind"] == "Switch" and p["rule"] != "AnyOfMany" and len(p["el"]) > 4:
        # KStars: more than four exclusive choices become a drop-down menu
        l = QHBoxLayout(body)
        l.setContentsMargins(0, 0, 0, 0)
        menu = QComboBox()
        for el in p["el"]:
            menu.addItem(el["label"])
            if el["value"] == "On":
                menu.setCurrentIndex(menu.count() - 1)
        menu.setEnabled(writable)
        menu.setMinimumWidth(160)
        l.addWidget(menu)
        l.addStretch(1)
    elif p["kind"] == "Switch":
        l = QHBoxLayout(body)
        l.setContentsMargins(0, 0, 0, 0)
        for el in p["el"]:
            if p["rule"] == "AnyOfMany":
                w = QCheckBox(el["label"])
                w.setChecked(el["value"] == "On")
            else:
                w = QPushButton(el["label"])
                w.setCheckable(True)
                w.setChecked(el["value"] == "On")
            w.setEnabled(writable)
            l.addWidget(w)
        l.addStretch(1)
    elif p["kind"] == "Light":
        l = QHBoxLayout(body)
        l.setContentsMargins(0, 0, 0, 0)
        for el in p["el"]:
            l.addWidget(Light(el["value"]))
            l.addWidget(QLabel(el["label"]))
        l.addStretch(1)
    elif p["kind"] == "BLOB":
        l = QHBoxLayout(body)
        l.setContentsMargins(0, 0, 0, 0)
        for el in p["el"]:
            l.addWidget(QLabel(el["label"]))
            f = QLineEdit("")
            f.setReadOnly(True)
            l.addWidget(f, 1)
    else:
        g = QGridLayout(body)
        g.setContentsMargins(0, 0, 0, 0)
        g.setHorizontalSpacing(6)
        g.setVerticalSpacing(3)
        for i, el in enumerate(p["el"]):
            name_label = QLabel(el["label"])
            name_label.setMinimumWidth(130)
            g.addWidget(name_label, i, 0)
            v = el["value"] if p["kind"] == "Text" else number(el["value"], el["fmt"])
            val = QLineEdit(v)
            val.setReadOnly(True)
            val.setMinimumWidth(140)
            g.addWidget(val, i, 1)
            if writable and has_slider(el):
                # KStars (INDI_E::buildNumber): a writable number whose range
                # is at most 100 steps gets a spin box with arrows and a
                # slider instead of a text field - FILTER_SLOT, 1..5 step 1,
                # is one (the arrows are there in KStars on AstroArch)
                slider_box = QWidget()
                sh = QHBoxLayout(slider_box)
                sh.setContentsMargins(0, 0, 0, 0)
                lo, hi, st = float(el["min"]), float(el["max"]), float(el["step"])
                spin = QDoubleSpinBox()
                dec = 0 if st >= 1 else len(("%g" % st).split(".")[-1])
                spin.setDecimals(dec)
                spin.setRange(lo, hi)
                spin.setSingleStep(st)
                try:
                    spin.setValue(float(el["value"]))
                except ValueError:
                    pass
                spin.setMinimumWidth(70)
                slider = QSlider(Qt.Horizontal)
                slider.setRange(0, int(round((hi - lo)/st)))
                try:
                    slider.setValue(int(round((float(el["value"]) - lo)/st)))
                except ValueError:
                    pass
                sh.addWidget(slider, 1)
                sh.addWidget(spin)
                g.addWidget(slider_box, i, 2)
            elif writable:
                g.addWidget(QLineEdit(""), i, 2)
        g.setColumnStretch(1, 1)
        if writable:
            g.setColumnStretch(2, 1)
    h.addWidget(body, 1)
    button = QPushButton("Set")
    button.setFixedWidth(60)
    button.setVisible(writable and p["kind"] in ("Number", "Text", "BLOB"))
    if button.isVisible() or True:
        # keep the column even where there is no Set, as KStars does
        spacer = QWidget()
        spacer.setFixedWidth(60)
        h.addWidget(button if button.isVisibleTo(row) else spacer, 0, Qt.AlignTop)
    return row


def tab(prop, order, group):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(8, 8, 8, 8)
    v.setSpacing(4)
    first = True
    for n in order:
        if prop[n]["group"] != group:
            continue
        if not first:
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            v.addWidget(line)
        first = False
        v.addWidget(property_row(prop[n]))
    v.addStretch(1)
    return w


def window(prop, order, groups, active):
    """The whole panel window with one group tab selected, device tab on top."""
    f = QWidget()
    f.setWindowTitle("INDI Control Panel")
    v = QVBoxLayout(f)
    devices = QTabWidget()
    inner = QTabWidget()
    for g in groups:
        inner.addTab(tab(prop, order, g), g)
    inner.setCurrentIndex(groups.index(active))
    container = QWidget()
    cv = QVBoxLayout(container)
    cv.setContentsMargins(0, 0, 0, 0)
    cv.addWidget(inner, 1)
    log = QTextEdit()
    log.setReadOnly(True)
    log.setFixedHeight(70)
    cv.addWidget(log)
    devices.addTab(container, "Wheelly")
    v.addWidget(devices)
    return f


def main():
    xml_file, out_dir = sys.argv[1], sys.argv[2]
    # the scheme is NOT kept in the repository (it is KDE's): it is the copy
    # taken from AstroArch into KStars' themes folder on the Mac
    colors = sys.argv[3] if len(sys.argv) > 3 else os.path.expanduser(
        "~/Library/Application Support/kstars/themes/BreezeDark.colors")
    language = re.search(r"panel_(\w+)\.xml$", xml_file).group(1)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setStyle("Fusion")                 # the nearest to Breeze that Qt ships
    app.setPalette(palette(colors))
    app.setFont(QFont("Noto Sans", 10))
    # a switch that is On must read as On: Fusion draws a checked button
    # barely darker, Breeze fills it with the selection colour
    sel = app.palette().color(QPalette.Highlight).name()
    app.setStyleSheet("QPushButton:checked { background: %s; color: white; "
                      "border: 1px solid %s; border-radius: 3px; padding: 3px 8px; }" % (sel, sel))
    prop, order, groups = read_panel(xml_file)
    os.makedirs(out_dir, exist_ok=True)
    for i, g in enumerate(groups, 1):
        f = window(prop, order, groups, g)
        f.resize(900, 100)
        f.adjustSize()
        f.resize(900, max(f.sizeHint().height(), 420))
        png_path = os.path.join(out_dir, "%s-%d-%s.png" % (language, i, re.sub(r"\W+", "-", g).strip("-").lower()))
        f.grab().save(png_path)
        print(png_path)
    # ...and ONE PICTURE PER PROPERTY, the portion of the panel a paragraph of
    # the guide talks about (portions read better than the whole window).
    # The same row the tab draws, alone, on the window's background
    # and as wide as the tab, so the columns fall where they fall in the panel
    for n in order:
        w = QWidget()
        w.setAutoFillBackground(True)
        v = QVBoxLayout(w)
        v.setContentsMargins(10, 8, 10, 8)
        v.addWidget(property_row(prop[n]))
        w.resize(870, 10)
        w.adjustSize()
        w.resize(870, w.sizeHint().height())
        png_path = os.path.join(out_dir, "%s-%s.png" % (language, n.lower().replace("_", "-")))
        w.grab().save(png_path)
    print("%d property pictures in %s" % (len(order), out_dir))


if __name__ == "__main__":
    main()
