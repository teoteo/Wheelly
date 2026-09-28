#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: LGPL-2.1-or-later

"""Integration bench for the driver: indiserver + the real driver + the simulator.

No imitation is tested here: the compiled driver runs under indiserver,
attached to the simulator through a fake serial port, and it is spoken to in
the INDI XML protocol - the same one Ekos uses. What is seen here is what Ekos
would see.

    python3 driver_bench.py [path/to/indi_wheelly] [path/to/simulator]

It checks, in order:

  - that the driver presents itself as a filter wheel and connects;
  - which PANEL every property ends up in, which can only be checked by
    looking at the XML: indi_getprop does not show the groups;
  - that the labels are translated, and change when the language changes;
  - that a filter change succeeds and FILTER_SLOT comes back Ok;
  - that an invalid filter name is REFUSED, with an explanation as the newest
    log line, and that an empty name field (a slot without a filter) is not;
  - that a wheel that never arrives puts FILTER_SLOT in Alert, which is what
    stops the capture sequence in Ekos.

The expected texts compared against the driver's messages stay in the
language the driver speaks in that test: many tests run with an Italian LANG
on purpose, to check the Italian catalogue.
"""

import os
import pathlib
import shutil
import tempfile
import re
import signal
import socket
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
DRIVER = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "build" / "indi_wheelly"
SIMULATOR = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else \
    HERE.parent.parent / "firmware" / "simulator" / "wheelly_sim.py"
# On the other end of the cable there can be two things: the Python
# simulator, or the REAL FIRMWARE compiled for the PC. They are interchangeable
# on purpose - they speak the same protocol - and testing the driver against
# both tells whether the two halves of the project really understand each other.
IS_PYTHON = SIMULATOR.suffix == ".py"

# The port and the fake serial belong to THIS run, not to the project. With
# two fixed constants, two runs started by mistake on top of each other fight
# over the same port and the same pty: the result is failures that cannot be
# reproduced, the worst kind of failure, and a defect of the bench that looks
# like one of the driver.
def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


INDI_PORT = _free_port()
# Both paths show in the captured panel (doc/panel_*.xml): doc/draw_panel.py
# masks the bench's home, "/tmp/wheelly-bench-...", so if this prefix changes
# the mask there has to change with it. An older, Italian prefix
# ("wheelly_prova", "wheelly-prove-") is masked too.
SERIAL = f"/tmp/wheelly_link_{os.getpid()}"
DEVICE = "Wheelly"

failed = []
passed = 0


def ok(condition, what, detail=""):
    global passed
    if condition:
        passed += 1
    else:
        failed.append(what)
        print(f"  FAILED: {what}" + (f" -> {detail}" if detail else ""))


# -------------------------------------------------------------- INDI client

class Client:
    """The bare minimum to speak XML with indiserver."""

    def __init__(self, port):
        self.s = socket.create_connection(("127.0.0.1", port), timeout=5)
        self.s.settimeout(0.2)
        # The INDI stream is a sequence of elements without a common root:
        # one is put in front, so that an ordinary XML parser digests it.
        self.parser = ET.XMLPullParser(["end"])
        self.parser.feed(b"<indi>")
        self.props = {}      # name -> {"group":…, "label":…, "state":…, "elements":{}}
        # The order the properties were defined in, as a client lays them out
        # in a tab: a property defined again goes to the END of its group in
        # KStars (the "▶" on the current slot redefines the angles, and they
        # must not end up under the log).
        self.order = []
        self.messages = []
        self.send("<getProperties version='1.7'/>")

    def send(self, text):
        self.s.sendall(text.encode())

    def pump(self, seconds=0.5):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            try:
                data = self.s.recv(65536)
            except socket.timeout:
                continue
            except OSError:
                break
            if not data:
                break
            self.parser.feed(data)
            for _, element in self.parser.read_events():
                self._collect(element)

    def _collect(self, e):
        if e.tag == "message":
            text = e.get("message", "")
            if text:
                self.messages.append(text)
            return
        # delProperty removes the property (or all of them, without a name),
        # as a real client does: without it, a property redefined shorter -
        # the number of positions lowered from the panel - stayed as long as
        # before
        if e.tag == "delProperty":
            if e.get("device") == DEVICE:
                if e.get("name"):
                    self.props.pop(e.get("name"), None)
                    if e.get("name") in self.order:
                        self.order.remove(e.get("name"))
                else:
                    self.props.clear()
                    self.order.clear()
            return
        m = re.match(r"^(def|set)(Number|Text|Switch|Light|BLOB)Vector$", e.tag)
        if not m:
            return
        name = e.get("name")
        if e.get("device") != DEVICE or not name:
            return
        entry = self.props.setdefault(name, {"elements": {}})
        if m.group(1) == "def":
            # a definition is COMPLETE: the elements are those and no others
            entry["elements"] = {}
            if name in self.order:
                self.order.remove(name)
            self.order.append(name)
            entry["group"] = e.get("group", "")
            entry["label"] = e.get("label", "")
            entry["kind"] = m.group(2)
            entry["perm"] = e.get("perm", "")
        entry["state"] = e.get("state", entry.get("state", ""))
        for child in e:
            n = child.get("name")
            if not n:
                continue
            # The attributes of an element - min, max, step, label - arrive
            # only with the DEFINITION of the property; later updates carry
            # the value alone. So what is already known is kept instead of
            # being overwritten with nothing.
            previous = entry["elements"].get(n, {})
            now = dict(previous)
            now["value"] = (child.text or "").strip()
            for key, value in child.attrib.items():
                if key != "name":
                    now[key] = value
            entry["elements"][n] = now
        if e.get("message"):
            self.messages.append(e.get("message"))

    def tab(self, group):
        """The properties of one tab, in the order a client shows them."""
        return [n for n in self.order if self.props.get(n, {}).get("group") == group]

    def state(self, name):
        return self.props.get(name, {}).get("state", "")

    def wait_state(self, name, wanted, seconds=20.0):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.pump(0.2)
            if self.state(name) in wanted:
                return self.state(name)
        return self.state(name)

    def wait_property(self, name, seconds=10.0):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.pump(0.2)
            if name in self.props:
                return True
        return False

    def set_text(self, prop, element, value):
        self.send(f"<newTextVector device='{DEVICE}' name='{prop}'>"
                  f"<oneText name='{element}'>{value}</oneText></newTextVector>")

    def set_number(self, prop, element, value):
        self.send(f"<newNumberVector device='{DEVICE}' name='{prop}'>"
                  f"<oneNumber name='{element}'>{value}</oneNumber></newNumberVector>")

    def set_switch(self, prop, element, others=()):
        # EVERY CONNECT GOES WITH INDI's AUTO SEARCH OFF. A
        # connection that fails on the bench's port - the wrong port, the
        # wrong device, on purpose - makes libindi try the other serial ports
        # it finds, /dev/serial/by-id/*Espressif* included: on a test machine
        # that may be a REAL wheel, in use by Ekos, and opening an ESP32-S3's
        # USB port can toggle DTR/RTS and reset it even if the open is then
        # refused. The bench must never reach a real device, on any machine.
        if prop == "CONNECTION" and element == "CONNECT":
            self.send(f"<newSwitchVector device='{DEVICE}' name='DEVICE_AUTO_SEARCH'>"
                      "<oneSwitch name='INDI_ENABLED'>Off</oneSwitch>"
                      "<oneSwitch name='INDI_DISABLED'>On</oneSwitch></newSwitchVector>")
            self.pump(0.3)
        pieces = "".join(f"<oneSwitch name='{a}'>Off</oneSwitch>" for a in others)
        self.send(f"<newSwitchVector device='{DEVICE}' name='{prop}'>"
                  f"{pieces}<oneSwitch name='{element}'>On</oneSwitch>"
                  f"</newSwitchVector>")

    def close(self):
        try:
            self.s.close()
        except OSError:
            pass


# The calibration angles are ONE PROPERTY PER SLOT, WHEELLY_ANGLE_1 .. _n
# with one element, ANGLE: every row needs a Set of its own, and KStars gives
# one Set per property. Rejected: one vector, WHEELLY_ANGLES, with elements
# ANGLE_1 .. _n.
ROW = re.compile(r"^WHEELLY_ANGLE_(\d+)$")


def angle_rows(c):
    """The rows' names, in slot order."""
    return sorted((n for n in c.props if ROW.match(n)), key=lambda n: int(ROW.match(n).group(1)))


def angle_row(c, slot):
    """(label, value) of a slot's row; the label is the property's."""
    p = c.props["WHEELLY_ANGLE_%d" % slot]
    return p.get("label"), float(p["elements"]["ANGLE"]["value"])


def set_row(c, slot, value):
    """A Set on one row, as KStars sends it: the one element."""
    c.send(f"<newNumberVector device='{DEVICE}' name='WHEELLY_ANGLE_{slot}'>"
           f"<oneNumber name='ANGLE'>{value}</oneNumber></newNumberVector>")


# ------------------------------------------------------------------ the bench

class Bench:
    """Starts the simulator and indiserver, and stops them leaving nothing behind."""

    def __init__(self, *simulator_knobs, language=None, config=None):
        # The tests must NOT write into the driver's real configuration.
        # INDI saves in $HOME/.indi/, and the driver also puts the serial port
        # in there: the tests use a pty that no longer exists on the next run,
        # and whoever connected after them found the driver pointed at a dead
        # port, with an error that explained nothing. It really happened. So
        # the tests get a home of their own, thrown away at the end.
        self.home = tempfile.mkdtemp(prefix="wheelly-bench-")
        # an ALREADY WRITTEN configuration, as the driver finds it on its second
        # start: defects on the second use are invisible to tests from scratch
        if config:
            os.makedirs(os.path.join(self.home, ".indi"))
            with open(os.path.join(self.home, ".indi", "%s_config.xml" % DEVICE), "w") as f:
                f.write(config)
        launch = [sys.executable, str(SIMULATOR)] if IS_PYTHON else [str(SIMULATOR)]
        self.sim = subprocess.Popen(
            [*launch, "--pty", "--link", SERIAL, *simulator_knobs],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            if os.path.exists(SERIAL):
                break
            time.sleep(0.05)

        env = dict(os.environ)
        env["HOME"] = self.home
        # The folder the driver reads the /dev/serial/by-id/ links from, to
        # find a wheel that comes back under another ttyACMn: the bench's own,
        # so that no test ever looks at the machine's real devices.
        self.by_id = os.path.join(self.home, "by-id")
        os.makedirs(self.by_id)
        env["WHEELLY_SERIAL_BY_ID"] = self.by_id
        if language:
            env["LANG"] = language
            env["LC_ALL"] = language
        # The local socket with "-u", and it is not a detail: indiserver ALWAYS
        # opens one, and the default path is hard-wired (/tmp/indiserver).
        # Ekos in Local mode starts its own indiserver, which takes that
        # socket: without "-u" the tests do not start while KStars has a
        # session open, recognisable by the error
        # "Local server: bind: Address already in use". With one of their own,
        # the tests run even while the panel is being looked at.
        self.server = subprocess.Popen(
            ["indiserver", "-p", str(INDI_PORT),
             "-u", os.path.join(self.home, "socket"), "-r", "0", str(DRIVER)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
        time.sleep(1.2)

    def connect(self, client):
        client.pump(1.0)
        client.set_text("DEVICE_PORT", "PORT", SERIAL)
        client.pump(0.4)
        client.set_switch("CONNECTION", "CONNECT", ["DISCONNECT"])
        return client.wait_state("CONNECTION", ("Ok", "Alert"), 15)

    def close(self):
        for p in (self.server, self.sim):
            try:
                p.send_signal(signal.SIGINT)
                p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        if os.path.exists(SERIAL):
            try:
                os.unlink(SERIAL)
            except OSError:
                pass
        shutil.rmtree(self.home, ignore_errors=True)


# ---------------------------------------------------------------------- tests

# Where everything must end up. It is the explicit request: filter names and
# operation in the main panel, calibration and adjustments in a dedicated one.
EXPECTED_PANELS = {
    "FILTER_SLOT":        "Main Control",
    "FILTER_NAME":        "Main Control",
    "WHEELLY_POSITION":   "Main Control",
    "WHEELLY_SENSOR":     "Main Control",
    "WHEELLY_ANGLE_1":    "Calibration and Diagnostics",
    "WHEELLY_ANGLE_5":    "Calibration and Diagnostics",
    "WHEELLY_SAVE":       "Calibration and Diagnostics",
    "WHEELLY_JOG_DOWN":   "Calibration and Diagnostics",
    "WHEELLY_JOG_UP":     "Calibration and Diagnostics",
    "WHEELLY_TOLERANCE":  "Calibration and Diagnostics",
    "WHEELLY_SLOTS":      "Calibration and Diagnostics",
    "WHEELLY_MOTOR":      "Options",
    "WHEELLY_HOLD":       "Options",
    "WHEELLY_DIRECTION":  "Options",
    "WHEELLY_LED":        "Options",
    "WHEELLY_LOG":        "Calibration and Diagnostics",
    "WHEELLY_FILES":      "Calibration and Diagnostics",
    "WHEELLY_SWEEP_DIR":  "Calibration and Diagnostics",
    "WHEELLY_FIRMWARE":   "Options",
    "WHEELLY_CONFIG":     "Options",
    "WHEELLY_LANGUAGE":   "Options",
}


def test_panels_and_language():
    print("panels, labels and language")
    bench = Bench(language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    try:
        result = bench.connect(c)
        ok(result == "Ok", "the driver connects to the simulator", result)
        c.pump(2.0)

        missing = [n for n in EXPECTED_PANELS if n not in c.props]
        ok(not missing, "every expected property has been defined",
           str(missing))

        wrong = {n: c.props[n].get("group")
                 for n, expected in EXPECTED_PANELS.items()
                 if n in c.props and c.props[n].get("group") != expected}
        ok(not wrong, "every property is in the right panel", str(wrong))

        # The labels are translated: with an Italian LANG, Italian must show.
        label = c.props.get("WHEELLY_ANGLE_1", {}).get("elements", {}).get("ANGLE", {}).get("label", "")
        ok(label == "Angolo di taratura (°)", "the labels are in Italian", label)
        # one row per slot, and no single vector nor "Save position"
        ok(angle_rows(c) == ["WHEELLY_ANGLE_%d" % i for i in range(1, 6)]
           and "WHEELLY_ANGLES" not in c.props and "WHEELLY_TEACH" not in c.props,
           "the angles: one row per slot, no single vector, no 'Save position'",
           f"{angle_rows(c)} {sorted(n for n in c.props if 'ANGLE' in n or 'TEACH' in n)}")
        # no rotation trim, and no "clear" button for it
        ok("WHEELLY_OFFSET" not in c.props
           and list(c.props.get("WHEELLY_SAVE", {}).get("elements", {})) == ["SAVE"],
           "no rotation trim and no 'clear the trims' any more",
           str(list(c.props.get("WHEELLY_SAVE", {}).get("elements", {}))))
        # "Save to the wheel" in Options too, RIGHT UNDER INDI's
        # "Configuration", which is left as INDI made it
        options = c.tab("Options")
        at = options.index("CONFIG_PROCESS") if "CONFIG_PROCESS" in options else -9
        config = c.props.get("WHEELLY_CONFIG", {})
        ok(options[at + 1:at + 2] == ["WHEELLY_CONFIG"]
           and config.get("label") == "Configurazione della ruota"
           and {k: v.get("label") for k, v in config.get("elements", {}).items()}
               == {"SAVE": "Salva nella ruota"},
           "Options: 'Configurazione della ruota' right under INDI's Configuration",
           f"{options} {config.get('label')} {config.get('elements')}")
        ok(len(c.props.get("CONFIG_PROCESS", {}).get("elements", {})) == 4,
           "and INDI's own Configuration keeps its four buttons",
           str(list(c.props.get("CONFIG_PROCESS", {}).get("elements", {}))))
        ok(c.props.get("FILTER_SLOT", {}).get("label", "") == "Posizione",
           "the base class properties' labels as well",
           c.props.get("FILTER_SLOT", {}).get("label", ""))

        # The NAMES, on the other hand, are not: they are identifiers and
        # stay English for ever.
        ok(all(n.isupper() or "_" in n for n in EXPECTED_PANELS),
           "the property names stay English identifiers")

        # the filter names come from the wheel, not from a fallback list
        names = c.props.get("FILTER_NAME", {}).get("elements", {})
        values = [v["value"] for v in names.values()]
        ok("Lum" in values and "Ha" in values,
           "the filter names come from the wheel", str(values))
    finally:
        c.close()
        bench.close()

    # and in English
    bench = Bench(language="en_US.UTF-8")
    c = Client(INDI_PORT)
    try:
        bench.connect(c)
        c.pump(2.0)
        label = c.props.get("WHEELLY_ANGLE_1", {}).get("elements", {}).get("ANGLE", {}).get("label", "")
        ok(label == "Calibration angle (°)", "with an English LANG the labels are English",
           label)
        ok(c.props.get("WHEELLY_CONFIG", {}).get("label") == "Wheel configuration",
           "and the Options row is 'Wheel configuration'",
           str(c.props.get("WHEELLY_CONFIG", {}).get("label")))
    finally:
        c.close()
        bench.close()


def test_filter_change():
    print("filter change")
    bench = Bench()
    c = Client(INDI_PORT)
    try:
        bench.connect(c)
        c.pump(1.5)

        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", 4)
        # While moving, FILTER_SLOT must stay Busy: it is what keeps Ekos
        # from shooting.
        seen_busy = False
        end = time.monotonic() + 3
        while time.monotonic() < end:
            c.pump(0.1)
            if c.state("FILTER_SLOT") == "Busy":
                seen_busy = True
                break
        ok(seen_busy, "FILTER_SLOT is Busy during the move",
           c.state("FILTER_SLOT"))

        result = c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 20)
        ok(result == "Ok", "the filter change succeeds", result)
        value = c.props["FILTER_SLOT"]["elements"]["FILTER_SLOT_VALUE"]["value"]
        ok(value.startswith("4"), "and the reported position is the fourth", value)

        # the main panel shows where the wheel is
        pos = c.props.get("WHEELLY_POSITION", {}).get("elements", {})
        ok(abs(float(pos["ANGLE"]["value"]) - 216.0) < 1.0,
           "the angle shown is the fourth position's",
           str(pos.get("ANGLE")))
        # Against the Good tolerance the panel shows, i.e. what the wheel
        # reported at connection: a literal here would break at every change
        # of the factory value.
        good = c.props.get("WHEELLY_TOLERANCE", {}).get("elements", {}).get("GOOD", {})
        ok(abs(float(pos["ERROR"]["value"])) <= float(good.get("value", "nan")),
           "and the residual error is within the good tolerance",
           f"{pos.get('ERROR')} good={good.get('value')}")

        # the sensor is instrumentation visible while the wheel works
        sens = c.props.get("WHEELLY_SENSOR", {}).get("elements", {})
        ok(float(sens["MAGNITUDE"]["value"]) > 100,
           "the sensor magnitude reaches Ekos", str(sens.get("MAGNITUDE")))
    finally:
        c.close()
        bench.close()


def test_name_refused():
    print("invalid filter name: red light on the names, and the reason in the log")
    bench = Bench(language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    try:
        bench.connect(c)
        c.pump(1.5)
        before = dict(c.props["FILTER_NAME"]["elements"])

        # The label states the field's name and nothing else. The rule had
        # ended up in it for a while - in KStars the label is also the tooltip -
        # and the price was seeing it truncated with an ellipsis in the column,
        # because the label is also visible text. See firmware.md, section 5.1.
        label = c.props["FILTER_NAME"]["label"]
        ok(label == "Nomi dei filtri",
           "the names' label states the field's name and nothing else", label)
        ok("WHEELLY_NAME_RULE" not in c.props,
           "and there is no extra property stating the rule")

        # A space in the middle: the real mistake, the one made first.
        c.set_text("FILTER_NAME", "FILTER_SLOT_NAME_1", "Lum 31mm")
        c.wait_state("FILTER_NAME", ("Alert",), 5)
        ok(c.state("FILTER_NAME") == "Alert",
           "the names field goes to alarm", c.state("FILTER_NAME"))

        # FILTER_SLOT, on the other hand, must NOT turn red, and it matters: in
        # Ekos FILTER_SLOT in Alert means "filter change failed", and it stops
        # the capture sequence. A misspelt name is the writer's mistake, not
        # the wheel's: it must not throw a night away.
        ok(c.state("FILTER_SLOT") != "Alert",
           "but FILTER_SLOT does not: in Alert it would stop the capture in Ekos",
           c.state("FILTER_SLOT"))

        after = c.props["FILTER_NAME"]["elements"]
        ok(after["FILTER_SLOT_NAME_1"]["value"] == before["FILTER_SLOT_NAME_1"]["value"],
           "the text goes back to the good one: it is VISIBLE that it was not accepted",
           after["FILTER_SLOT_NAME_1"]["value"])

        # The reason is in the message, the only place left: so it must be
        # enough on its own - which position, which name, what is wrong, and
        # what to write instead.
        log = " ".join(c.messages[-4:])
        ok("Posizione 1" in log, "the message says which position",
           log[-250:])
        ok('"Lum 31mm"' in log, "and repeats the refused name", log[-250:])
        ok("spazio" in log,
           "and NAMES the offending character, instead of listing the allowed ones",
           log[-250:])
        ok('"Lum_31mm"' in log,
           "and proposes a good name derived from the one written", log[-250:])
        ok("Ammessi" in log and "cifre" in log and "32" in log,
           "and ALWAYS lists the characters that can be used", log[-250:])
        # The refusal must be the NEWEST line: KStars' log puts the newest on
        # top and its status bar shows only that one. With the rule sent after
        # the refusal, the line in sight was the generic rule, and which slot
        # and why stayed hidden under it.
        ok("Posizione 1" in c.messages[-1] and "spazio" in c.messages[-1],
           "the refusal itself is the newest line, the one in sight",
           c.messages[-1])

        # the worst case for length: a long name, a long reason, and an equally
        # long proposed name
        long_name = "-" + "Lum_stretto_31mm_Baader_CMOS" + "-"
        c.set_text("FILTER_NAME", "FILTER_SLOT_NAME_1", "Lum_ok")
        c.wait_state("FILTER_NAME", ("Ok",), 5)
        c.set_text("FILTER_NAME", "FILTER_SLOT_NAME_1", long_name)
        c.wait_state("FILTER_NAME", ("Alert",), 5)
        # too long for one line: the rule and the refusal go on two, and the
        # refusal is still the newest
        ok("Posizione 1" in c.messages[-1] and "Ammessi" in c.messages[-2],
           "on two lines the rule comes first and the refusal last",
           str(c.messages[-2:]))

        # an accented letter cannot even be printed: in UTF-8 it is two bytes,
        # and sending back only one is not valid XML - the client would die on
        # the whole stream, not on that message
        c.set_text("FILTER_NAME", "FILTER_SLOT_NAME_1", "Halfa")
        c.wait_state("FILTER_NAME", ("Ok",), 5)
        before_accent = len(c.messages)
        c.set_text("FILTER_NAME", "FILTER_SLOT_NAME_1", "H-alfà")
        c.wait_state("FILTER_NAME", ("Alert",), 5)
        log = " ".join(c.messages[before_accent:])
        ok("accentata" in log,
           "an accented letter is described as such, not printed by halves",
           log[-250:])

        # a valid name puts everything back in order
        c.set_text("FILTER_NAME", "FILTER_SLOT_NAME_1", "Lum_31mm")
        result = c.wait_state("FILTER_NAME", ("Ok",), 5)
        ok(result == "Ok", "the corrected name is accepted", result)

        # a duplicate: "Ha" is already the fifth position's name
        before_dup = len(c.messages)
        c.set_text("FILTER_NAME", "FILTER_SLOT_NAME_2", "ha")
        c.wait_state("FILTER_NAME", ("Alert",), 5)
        log = " ".join(c.messages[before_dup:])
        ok("maiuscole" in log,
           "a duplicate is explained as such", log[-250:])
        ok("sarebbe accettato" not in log,
           "and nothing is proposed there: cleaning it up would leave it the same",
           log[-250:])
        ok("Ammessi" in log,
           "but the allowed characters are there all the same, as in every refusal",
           log[-250:])

        # No message may be TRUNCATED, and it is checked at the end, when they
        # have all gone by: an INDI message is a char[MAXINDIMESSAGE] with
        # MAXINDIMESSAGE = 255, and what does not fit vanishes silently. It
        # happened: with the rule appended to the refusal, "-Lum-" arrived
        # truncated to "...una cif". The limit lets 254 bytes through, so
        # measuring is not enough: a whole sentence ends with a full stop.
        ours = [m for m in c.messages if "rifiutato" in m or "Ammessi" in m]
        # four refusals, each with its rule - on one line or on two
        ok(sum("rifiutato" in m for m in ours) >= 4
           and sum("Ammessi" in m for m in ours) >= 4,
           "and all the refusal messages have arrived", str(len(ours)))
        truncated = [m for m in ours
                     if len(m.encode("utf-8")) > 254 or not m.endswith(".")]
        ok(not truncated, "and none arrives truncated by the INDI limit",
           str(truncated)[-300:])
    finally:
        c.close()
        bench.close()


def set_names(c, values):
    """All the names in one go, as Ekos and KStars' panel send them."""
    pieces = "".join(f"<oneText name='FILTER_SLOT_NAME_{i + 1}'>{v}</oneText>"
                     for i, v in enumerate(values))
    c.send(f"<newTextVector device='{DEVICE}' name='FILTER_NAME'>{pieces}"
           "</newTextVector>")
    c.pump(1.5)


def field_names(c):
    names = c.props["FILTER_NAME"]["elements"]
    return [names[f"FILTER_SLOT_NAME_{i + 1}"]["value"] for i in range(len(names))]


def test_empty_slots():
    """A slot without a filter is normal: its field is left empty. That
    refused the whole set, with a red light and, in sight, only the generic
    rule. An empty field now becomes "Empty_<slot>": unique by the slot number,
    valid for the firmware, the same in every language."""
    print("empty name fields: a slot without a filter")
    bench = Bench(language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    try:
        bench.connect(c)
        c.pump(1.5)

        # the case seen in Ekos: four filters, the fifth slot left empty
        before = len(c.messages)
        set_names(c, ["Lum", "Red", "Green", "Blue", ""])
        ok(c.state("FILTER_NAME") == "Ok",
           "a set with an empty slot is accepted - the wheel took it too",
           c.state("FILTER_NAME"))
        ok(field_names(c) == ["Lum", "Red", "Green", "Blue", "Empty_5"],
           "and the empty slot shows its name, Empty_5, as Ekos will list it",
           str(field_names(c)))
        log = " ".join(c.messages[before:])
        ok("Posizione 5" in log and '"Empty_5"' in log,
           "the log says which slot was named and how", log[-250:])
        ok("rifiutato" not in log and "Ammessi" not in log,
           "and nothing is refused", log[-250:])

        # several empty slots, one of them only blanks: the slot number keeps
        # them apart, so the duplicate rule is not tripped
        set_names(c, ["Lum", "Red", "", "  ", ""])
        ok(c.state("FILTER_NAME") == "Ok",
           "several empty slots are accepted together", c.state("FILTER_NAME"))
        ok(field_names(c) == ["Lum", "Red", "Empty_3", "Empty_4", "Empty_5"],
           "each with its own name", str(field_names(c)))

        # the second use: the set sent again as the panel now shows it
        set_names(c, field_names(c))
        ok(c.state("FILTER_NAME") == "Ok",
           "sending the set again as shown is accepted", c.state("FILTER_NAME"))

        # a filter put back into an empty slot takes its place
        set_names(c, ["Lum", "Red", "Green", "Empty_4", "Empty_5"])
        ok(field_names(c)[2] == "Green" and c.state("FILTER_NAME") == "Ok",
           "a slot that was empty takes a filter name again", str(field_names(c)))

        # an empty slot together with a really bad name: the set is refused,
        # the empty slot is NOT announced as named, and the refusal of the
        # bad one is the line in sight
        shown = field_names(c)
        before = len(c.messages)
        set_names(c, ["Lum", "Red 2", "Green", "", "Empty_5"])
        ok(c.state("FILTER_NAME") == "Alert",
           "a bad name next to an empty slot is still refused",
           c.state("FILTER_NAME"))
        ok(field_names(c) == shown,
           "and the fields go back as they were", str(field_names(c)))
        ok("Posizione 2" in c.messages[-1] and "spazio" in c.messages[-1],
           "the specific reason is the newest line", c.messages[-1])
        ok(not any("lasciata vuota" in m for m in c.messages[before:]),
           "and no slot is announced as named by a set that was refused",
           str(c.messages[before:]))
    finally:
        c.close()
        bench.close()


def test_sweep():
    print("the magnet sweep, and the PNG it produces")
    import base64
    import struct
    import zlib

    bench = Bench(language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    try:
        bench.connect(c)
        c.pump(1.5)
        start = int(float(
            c.props["FILTER_SLOT"]["elements"]["FILTER_SLOT_VALUE"]["value"]))

        # BLOBs do not arrive until they are asked for: it is the CLIENT that
        # must enable them. In KStars the checkbox next to the property does
        # it, and it is on by default; here it is said by hand, because
        # without it the plot would not leave the server and the test would
        # test nothing.
        c.send(f"<enableBLOB device='{DEVICE}'>Also</enableBLOB>")
        c.pump(0.3)

        c.set_switch("WHEELLY_SWEEP", "RUN")
        # During the turn the wheel really moves: FILTER_SLOT must say so,
        # otherwise the panel shows a still wheel while it is turning.
        seen_busy = False
        end = time.monotonic() + 6
        while time.monotonic() < end:
            c.pump(0.1)
            if c.state("FILTER_SLOT") == "Busy":
                seen_busy = True
                break
        ok(seen_busy, "during the sweep the wheel shows as moving",
           c.state("FILTER_SLOT"))

        result = c.wait_state("WHEELLY_SWEEP", ("Ok", "Alert"), 120)
        ok(result == "Ok", "the full turn ends well", result)
        c.pump(1.0)

        arrival = int(float(
            c.props["FILTER_SLOT"]["elements"]["FILTER_SLOT_VALUE"]["value"]))
        ok(arrival == start,
           "and the wheel returns where it was: whoever was capturing finds their filter",
           f"started from {start}, ended on {arrival}")

        text = " ".join(c.messages[-4:])
        ok("Spazzolata finita" in text and "escursione" in text,
           "the message says how it went", text[-250:])

        # the plot
        ok("WHEELLY_SWEEP_PLOT" in c.props, "the plot arrives as a BLOB")
        element = c.props["WHEELLY_SWEEP_PLOT"]["elements"]["PLOT"]
        # The format must NOT be ".png". KStars, when the extension is an
        # image format Qt can read, opens a window to show it - and that
        # window is a child of the main one like the INDI panel, so closing
        # it takes the panel along. The name still ends in .png, so that any
        # viewer opens it.
        ok(element.get("format") == ".wheelly.png",
           "the format is not an image for Qt: KStars opens no window",
           str(element.get("format")))

        png = base64.b64decode(element["value"])
        ok(png[:8] == b"\x89PNG\r\n\x1a\n", "and it really is a PNG",
           str(png[:8]))
        # If the plot has not arrived, the tests that follow have nothing to
        # look at: they stop here instead of blowing up inside zlib, so the
        # fault reads as a defect and not as a bench accident.
        if png[:8] != b"\x89PNG\r\n\x1a\n":
            return
        ok(int(element.get("size", 0)) == len(png),
           "and the declared size is the real one",
           f"declared {element.get('size')}, arrived {len(png)}")

        # We write the PNG by hand, byte by byte, with no library: so it is
        # not enough that it starts well. It is read back chunk by chunk
        # checking every CRC, and the zlib stream is decompressed: if the
        # writer got a sum wrong, it shows here.
        i, idat, header = 8, b"", None
        broken = []
        while i < len(png):
            length = struct.unpack(">I", png[i:i + 4])[0]
            kind = png[i + 4:i + 8]
            body = png[i + 8:i + 8 + length]
            crc = struct.unpack(">I", png[i + 8 + length:i + 12 + length])[0]
            if crc != zlib.crc32(kind + body) & 0xFFFFFFFF:
                broken.append(kind.decode())
            if kind == b"IHDR":
                header = struct.unpack(">IIBBBBB", body)
            if kind == b"IDAT":
                idat += body
            i += 12 + length
        ok(not broken, "every PNG chunk has the right CRC", str(broken))
        ok(header is not None and header[0] == 640 and header[1] == 420,
           "the header states the right size", str(header))
        ok(header is not None and header[2] == 8 and header[3] == 3,
           "eight-bit palette, as declared", str(header))
        pixels = zlib.decompress(idat)
        ok(len(pixels) == 420 * (640 + 1),
           "and there are as many pixels as needed, row filter included",
           f"{len(pixels)} instead of {420 * 641}")

        # There must be enough samples to draw a curve. At the normal polling
        # rate a turn gave twenty, and twenty points over three hundred and
        # sixty degrees are a constellation, not a measurement: hence the
        # denser polling during the sweep.
        said = [m for m in c.messages if "Spazzolata finita" in m]
        count = int(re.search(r"(\d+) campioni", said[-1]).group(1)) if said else 0
        ok(count >= 30, "and there are enough samples to draw a curve",
           f"{count} samples")

        # And the plot must contain DATA, not just the frame: without a trace -
        # samples never collected, a wrong scale - the drawing would still be
        # a valid PNG and all the tests above would pass just the same.
        #
        # The threshold is loose on purpose. Against the simulator the trace
        # covers about 1200 pixels, against the real firmware 680: the fake
        # sensor of the C++ bench models the same eccentricity but WITHOUT
        # noise, so the curve is thinner. A tight threshold would have said
        # "defect" where there was only a difference between the two fakes.
        trace = sum(1 for b in pixels if b == 4)
        ok(trace > 300, "and the sample trace is there, it is not a blank sheet",
           f"{trace} trace pixels")

        # The file's path must be STATED, and written in the panel: where the
        # client saves it is the client's choice, and the driver does not know.
        path = c.props["WHEELLY_FILES"]["elements"]["SWEEP"]["value"]
        ok(path.endswith(".png") and bench.home in path,
           "the panel says where the plot is on disk", path)
        # Name with date and time, and in Documents: a plot is something to
        # look at, and goes where things are looked at.
        ok(re.fullmatch(r".*/Documents/\d{4}-\d\d-\d\d_\d\d-\d\d-\d\d_wheelly_sweep\.png",
                        path) is not None,
           "with the right name and in the right folder", path)
        ok(os.path.exists(path), "and it really is there", path)
        # If the file is not there, the comparison has nothing to compare: it
        # is skipped, so the fault reads as a defect and not as a bench
        # accident. The same rule as the missing PNG.
        if os.path.exists(path):
            with open(path, "rb") as f:
                on_disk = f.read()
            ok(on_disk == png,
               "and it is the very same plot that arrived as a BLOB",
               f"{len(on_disk)} bytes on disk, {len(png)} arrived")
        ok(path in " ".join(c.messages[-4:]),
           "and the path is in the log too", " ".join(c.messages[-4:])[-200:])

        # The folder can be changed: "~/Documents" is a sensible default, not
        # a truth that holds for every machine.
        folder = c.props["WHEELLY_SWEEP_DIR"]["elements"]["DIR"]["value"]
        ok(folder.endswith("/Documents"),
           "out of the box the sweeps go to Documents", folder)
        elsewhere = os.path.join(bench.home, "elsewhere")
        c.set_text("WHEELLY_SWEEP_DIR", "DIR", elsewhere)
        ok(c.wait_state("WHEELLY_SWEEP_DIR", ("Ok", "Alert"), 5) == "Ok",
           "and changing it is accepted", c.state("WHEELLY_SWEEP_DIR"))
        ok(os.path.isdir(elsewhere),
           "and the folder is created at once, not at the first lost sweep",
           elsewhere)

        # A second sweep must NOT delete the first: the point of measuring the
        # magnet is comparing a before and an after, and a fixed name that
        # gets overwritten throws away exactly the term of comparison.
        c.set_switch("WHEELLY_SWEEP", "RUN")
        ok(c.wait_state("WHEELLY_SWEEP", ("Ok", "Alert"), 120) == "Ok",
           "a second sweep can be run")
        c.pump(1.0)
        second = c.props["WHEELLY_FILES"]["elements"]["SWEEP"]["value"]
        ok(second != path, "and it writes a new file, not the same one",
           f"{path} -> {second}")
        ok(os.path.exists(path) and os.path.exists(second),
           "and the first is still there: sweeps do not overwrite each other",
           f"first={os.path.exists(path)}, second={os.path.exists(second)}")
        ok(second.startswith(elsewhere),
           "and the second goes into the new folder", second)

        # a folder that cannot be written must be SAID at once
        before_folder = len(c.messages)
        c.set_text("WHEELLY_SWEEP_DIR", "DIR", "/proc/sweeps")
        c.wait_state("WHEELLY_SWEEP_DIR", ("Alert",), 5)
        ok(c.state("WHEELLY_SWEEP_DIR") == "Alert",
           "a folder that cannot be written goes to alarm",
           c.state("WHEELLY_SWEEP_DIR"))
        ok("non si può usare" in " ".join(c.messages[before_folder:]),
           "saying so at once, instead of letting the first sweep find out",
           " ".join(c.messages[before_folder:])[-200:])
        c.set_text("WHEELLY_SWEEP_DIR", "DIR", elsewhere)
        c.pump(0.5)

        # a sweep while the wheel is moving cannot be run
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE",
                     (start % 5) + 1)
        c.pump(0.3)
        before = len(c.messages)
        c.set_switch("WHEELLY_SWEEP", "RUN")
        c.wait_state("WHEELLY_SWEEP", ("Alert",), 5)
        ok(c.state("WHEELLY_SWEEP") == "Alert",
           "and while the wheel is moving the sweep is refused",
           c.state("WHEELLY_SWEEP"))
        ok("aspetta che si fermi" in " ".join(c.messages[before:]),
           "saying why", " ".join(c.messages[before:])[-200:])
    finally:
        c.close()
        bench.close()


def test_names_from_the_wheel_on_second_start():
    """THE FILTER NAMES ARE THE WHEEL'S, even when the PC has some saved.
    libindi loads FILTER_NAME from the configuration at start-up
    and asks the driver for the names only if it has none: left to itself,
    from the second start the panel showed the PC's names - stale, if the wheel had been
    renamed elsewhere or reflashed - and the driver, which had not asked for
    them, rewrote them all at the first Set. The test starts from a
    configuration with names different from the wheel's."""
    print("the names on the second start")
    stale = "".join("<oneText name='FILTER_SLOT_NAME_%d'>Stale%d</oneText>" % (i, i)
                    for i in range(1, 6))
    bench = Bench(config="<INDIDriver><newTextVector device='%s' name='FILTER_NAME'>"
                         "%s</newTextVector></INDIDriver>" % (DEVICE, stale))
    c = Client(INDI_PORT)
    try:
        ok(bench.connect(c) == "Ok", "the driver connects")
        c.wait_property("FILTER_NAME", 10)
        c.pump(1.0)
        names = [c.props["FILTER_NAME"]["elements"]["FILTER_SLOT_NAME_%d" % i]["value"]
                 for i in range(1, 6)]
        ok(names == ["Lum", "Red", "Green", "Blue", "Ha"],
           "the panel shows the WHEEL's names, not those saved on the PC", str(names))
    finally:
        c.close()
        bench.close()


def test_slot_count_from_the_panel():
    """THE NUMBER OF POSITIONS IS CHANGED FROM THE PANEL (simpler than a
    serial monitor). From five to seven and back: every time
    FILTER_SLOT, the names, the angles and the trims follow, with elements
    that have their own names - lengthening them with resize() gave elements
    without a name."""
    print("the number of positions from the panel")
    bench = Bench()
    c = Client(INDI_PORT)
    try:
        ok(bench.connect(c) == "Ok", "the driver connects")
        c.wait_property("WHEELLY_SLOTS", 10)
        c.pump(1.0)
        ok(abs(float(c.props["WHEELLY_SLOTS"]["elements"]["COUNT"]["value"]) - 5) < 0.5,
           "the panel says five positions, the wheel's",
           c.props["WHEELLY_SLOTS"]["elements"]["COUNT"]["value"])
        for count in (7, 5):
            before = len(c.messages)
            c.set_number("WHEELLY_SLOTS", "COUNT", count)
            result = c.wait_state("WHEELLY_SLOTS", ("Ok", "Alert"), 8)
            c.pump(1.5)
            slot = c.props["FILTER_SLOT"]["elements"]["FILTER_SLOT_VALUE"]
            angles = angle_rows(c)
            ok(result == "Ok" and float(slot.get("max", 0)) == count,
               "%d positions: FILTER_SLOT goes up to %d" % (count, count),
               "%s max=%s" % (result, slot.get("max")))
            ok(len(c.props["FILTER_NAME"]["elements"]) == count,
               "%d positions: the names are %d" % (count, count),
               "%d names" % len(c.props["FILTER_NAME"]["elements"]))
            # the pitch buttons follow: 360/7 = 51.43, 360/5 = 72
            pitch = "51.43" if count == 7 else "72"
            down = c.props["WHEELLY_JOG_DOWN"]["elements"].get("JOG_M_PITCH", {})
            up = c.props["WHEELLY_JOG_UP"]["elements"].get("JOG_P_PITCH", {})
            ok(down.get("label") == "-%s°" % pitch and up.get("label") == "+%s°" % pitch,
               "%d positions: the pitch jogs say %s°" % (count, pitch),
               "%s %s" % (down.get("label"), up.get("label")))
            tab = c.tab("Calibration and Diagnostics")
            rows = ["WHEELLY_ANGLE_%d" % i for i in range(1, count + 1)]
            ok(tab[:count + 2] == ["WHEELLY_SLOTS"] + rows + ["WHEELLY_JOG_DOWN"],
               "%d positions: the rows are redefined in order, without moving down the tab" % count,
               str(tab))
            ok(angles == rows,
               "%d positions: exactly %d rows, WHEELLY_ANGLE_1..%d" % (count, count, count),
               str(angles))
            text = " ".join(c.messages[before:])
            ok("Save" in text or "Salva" in text,
               "%d positions: the log says that keeping them needs a save" % count,
               text[-200:])
    finally:
        c.close()
        bench.close()


def test_angle_set():
    """THE CALIBRATION ANGLES ARE EDITABLE, ONE ROW PER SLOT, each with its
    Set. A Set on a row with a
    new angle sends 'angle n' for that slot and moves the wheel there at once,
    as the position control does; a Set on an unchanged row sends no angle and
    only takes the wheel to its slot. Every change is said in the log,
    "Posizione 3: 144.00° → 145.50°", and written in the movement register. A
    value the wheel refuses leaves the old one, in Alert, with the wheel's
    reason. The exchange is watched with Driver Debug on."""
    print("the calibration angles: Set on a row, the move, the log")
    bench = Bench("--ms-per-degree", "2", language="it_IT.UTF-8")
    c = Client(INDI_PORT)

    def set_one(slot, value):
        before = len(c.messages)
        set_row(c, slot, value)
        c.pump(0.4)
        result = c.wait_state("WHEELLY_ANGLE_%d" % slot, ("Ok", "Alert"), 8)
        c.pump(0.8)
        return result, " ".join(c.messages[before:])

    def arrive():
        result = c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 15)
        c.pump(0.6)
        return result, float(c.props["WHEELLY_POSITION"]["elements"]["ANGLE"]["value"])

    try:
        ok(bench.connect(c) == "Ok", "the driver connects")
        c.wait_property("WHEELLY_ANGLE_1", 10)
        c.set_switch("WHEELLY_LOG", "LOG_ON", ["LOG_OFF"])
        c.set_switch("DEBUG", "ENABLE", ["DISABLE"])
        c.wait_property("DEBUG_LEVEL", 5)
        # "Debug" alone is not enough: the driver's lines are LOGF_DEBUG, and
        # they show only with the "Driver Debug" level on
        c.send(f"<newSwitchVector device='{DEVICE}' name='DEBUG_LEVEL'>"
               "<oneSwitch name='DBG_DEBUG'>On</oneSwitch></newSwitchVector>")
        c.pump(1.0)
        ok(all(c.props[r].get("perm") == "rw" for r in angle_rows(c)),
           "every row is read-write: KStars shows a Set on each",
           str([c.props[r].get("perm") for r in angle_rows(c)]))
        result, text = set_one(3, "145.50")
        sent = [m for m in text.split("-> ")[1:] if m.startswith("angle ")]
        ok(result == "Ok" and len(sent) == 1 and sent[0].startswith("angle 3 145.50"),
           "Set on row 3: only 'angle 3' reaches the wheel", f"{result} {sent}")
        ok("Posizione 3: 144.00° → 145.50°" in text,
           "and the log says the change, old → new", text[-300:])
        ok("-> go 3" in text,
           "Set on row 3: the wheel goes to that slot at once", text[-300:])
        result, where = arrive()
        ok(result == "Ok" and abs(where - 145.5) <= 0.8 and angle_row(c, 3)[1] == 145.5,
           "and arrives there, through FILTER_SLOT like a change of filter",
           f"{result} {where} {angle_row(c, 3)}")
        # a row not changed: no angle, only the move to its slot
        result, text = set_one(1, "0")
        ok(result == "Ok" and "-> angle" not in text and "-> go 1" in text,
           "Set on an unchanged row: no angle sent, the wheel goes to that slot",
           text[-300:])
        arrive()
        # a value the wheel refuses: Alert, the old value, the wheel's reason
        result, text = set_one(2, "400")
        why = [m for m in text.split("  ") if "Posizione 2" in m]
        ok(result == "Alert" and angle_row(c, 2)[1] == 72.0
           and "Posizione 2: l'angolo non è stato cambiato" in text and "-> go" not in text,
           "an angle out of range: Alert, the old value stays, the log says why, no move",
           f"{result} {angle_row(c, 2)} {text[-300:]}")
        # the movement register: a row per change, with its own outcome
        register = os.path.join(bench.home, ".indi", "wheelly_movements.csv")
        rows = open(register).read().splitlines() if os.path.exists(register) else []
        changes = [r for r in rows if ",angle-set," in r]
        ok(len(changes) == 1 and changes[0].split(",")[1:5] == ["3", "145.50", "144.00", "1.50"],
           "every change is a row of the movement register: slot, new, old, change",
           str(changes))
    finally:
        c.close()
        bench.close()


def test_current_slot_marker():
    """THE CURRENT SLOT IS MARKED: INDI cannot colour an
    element, so the label of the slot the wheel stands on reads "▶ 2". A
    label travels only with a definition, so the driver redefines the angles
    - and everything after them in the tab, or KStars would move them to
    the bottom - when the slot changes, and only then."""
    print("the current slot marked in the calibration angles")
    bench = Bench("--ms-per-degree", "2", language="it_IT.UTF-8")
    c = Client(INDI_PORT)

    def labels():
        return {"ANGLE_%s" % ROW.match(r).group(1): c.props[r].get("label") for r in angle_rows(c)}

    try:
        ok(bench.connect(c) == "Ok", "the driver connects")
        c.wait_property("WHEELLY_ANGLE_1", 10)
        c.pump(1.5)
        tab = c.tab("Calibration and Diagnostics")
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", 4)
        c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 15)
        c.pump(1.0)
        got = labels()
        ok(got.get("ANGLE_4") == "▶ 4" and [v for v in got.values() if "▶" in v] == ["▶ 4"],
           "on slot 4, its angle reads '▶ 4' and no other is marked", str(got))
        ok(c.tab("Calibration and Diagnostics") == tab,
           "the calibration tab keeps its order after the redefinition",
           f"{tab} -> {c.tab('Calibration and Diagnostics')}")
        # not at every poll: two seconds at rest, no definition of the angles
        c.s.settimeout(0.2)
        defined = []
        end = time.monotonic() + 2.0
        while time.monotonic() < end:
            try:
                data = c.s.recv(65536)
            except socket.timeout:
                continue
            defined.append(data.count(b"defNumberVector"))
            c.parser.feed(data)
            for _, element in c.parser.read_events():
                c._collect(element)
        ok(sum(defined) == 0, "at rest the angles are not defined again at every poll",
           f"{sum(defined)} definitions in 2 s")
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", 1)
        c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 15)
        c.pump(1.0)
        got = labels()
        ok(got.get("ANGLE_1") == "▶ 1" and got.get("ANGLE_4") == "4",
           "on slot 1 the mark moves with it", str(got))
    finally:
        c.close()
        bench.close()


def test_live_row():
    """THE CURRENT ROW FOLLOWS THE JOGS. After a jog the current slot's row shows
    the angle read now, labelled "▶ 2 *", not taught yet; its Set with the
    value unchanged teaches it WITHOUT moving - what a "Save position"
    button would do; edited, it is an ordinary change and the wheel goes; a
    move that is not a jog, a Set on another row included, gives the row its
    taught angle back. One definition per event, none at a poll. Driver Debug
    on, to see what reaches the wheel."""
    print("the current row follows the jogs, and the '*' until confirmed")
    bench = Bench("--ms-per-degree", "2", language="it_IT.UTF-8")
    c = Client(INDI_PORT)

    def marked():
        return [c.props[r].get("label") for r in angle_rows(c) if "▶" in (c.props[r].get("label") or "")]

    def jog(element, row_name="WHEELLY_JOG_UP"):
        c.set_switch(row_name, element)
        c.pump(0.3)
        c.wait_state(row_name, ("Ok", "Alert"), 15)
        c.pump(0.8)

    def set_one(slot, value):
        before = len(c.messages)
        set_row(c, slot, value)
        c.pump(0.4)
        c.wait_state("WHEELLY_ANGLE_%d" % slot, ("Ok", "Alert"), 8)
        c.pump(0.8)
        return " ".join(c.messages[before:])

    def angle():
        return float(c.props["WHEELLY_POSITION"]["elements"]["ANGLE"]["value"])

    def go(slot):
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", slot)
        c.pump(0.3)
        settle()

    def settle():
        c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 20)
        c.pump(1.0)

    try:
        ok(bench.connect(c) == "Ok", "the driver connects")
        c.wait_property("WHEELLY_ANGLE_1", 10)
        c.set_switch("WHEELLY_LOG", "LOG_ON", ["LOG_OFF"])
        c.set_switch("DEBUG", "ENABLE", ["DISABLE"])
        c.wait_property("DEBUG_LEVEL", 5)
        c.send(f"<newSwitchVector device='{DEVICE}' name='DEBUG_LEVEL'>"
               "<oneSwitch name='DBG_DEBUG'>On</oneSwitch></newSwitchVector>")
        c.pump(1.0)
        go(2)
        tab = c.tab("Calibration and Diagnostics")
        ok(angle_row(c, 2)[0] == "▶ 2", "live row: on slot 2, '▶ 2'", str(angle_row(c, 2)))

        # a jog: the row shows the angle read now, with the "*"
        jog("JOG_P1")
        label, value = angle_row(c, 2)
        ok(label == "▶ 2 *" and abs(value - angle()) < 0.01 and abs(value - 73.0) <= 0.5,
           "live row: after a jog +1, '▶ 2 *' and the angle read now",
           f"{label} {value} {angle()}")
        ok(marked() == ["▶ 2 *"], "live row: and no other row marked", str(marked()))
        ok(c.tab("Calibration and Diagnostics") == tab,
           "live row: the tab keeps its order after the redefinition",
           f"{tab} -> {c.tab('Calibration and Diagnostics')}")
        live = value

        # its Set, as shown: slot 2 taught there, and nothing moves
        text = set_one(2, c.props["WHEELLY_ANGLE_2"]["elements"]["ANGLE"]["value"])
        ok("-> angle 2 %.2f" % live in text and "-> go" not in text,
           "live row: Set as shown teaches slot 2 at the live angle, and nothing moves",
           text[-400:])
        ok("Posizione 2: 72.00° → %.2f°" % live in text,
           "live row: and the log says old → new", text[-300:])
        label, value = angle_row(c, 2)
        ok(label == "▶ 2" and abs(value - live) < 0.01,
           "live row: confirmed, back to '▶ 2' with the new angle", f"{label} {value}")

        # a jog, then a filter change without confirming: the row goes back
        jog("JOG_P1")
        ok(angle_row(c, 2)[0] == "▶ 2 *", "live row: a second jog, the '*' again",
           str(angle_row(c, 2)))
        go(4)
        label, value = angle_row(c, 2)
        ok(label == "2" and abs(value - live) < 0.01 and angle_row(c, 4)[0] == "▶ 4",
           "live row: left without confirming, slot 2 shows its taught angle again",
           f"{label} {value} {angle_row(c, 4)}")

        # a jog, then the SAME slot chosen again: the wheel goes back to the
        # taught angle, and so does the row - the slot does not change, so
        # only the move itself can say it
        jog("JOG_P1")
        ok(angle_row(c, 4)[0] == "▶ 4 *", "live row: jog on slot 4, '▶ 4 *'", str(angle_row(c, 4)))
        go(4)
        ok(angle_row(c, 4) == ("▶ 4", 216.0) and abs(angle() - 216.0) <= 0.8,
           "live row: slot 4 chosen again, the row back to its taught angle, no '*'",
           f"{angle_row(c, 4)} {angle()}")

        # a jog on slot 4, then a Set on ANOTHER row: the wheel goes there,
        # and slot 4, not confirmed, keeps its taught angle
        jog("JOG_P0_1")
        ok(angle_row(c, 4)[0] == "▶ 4 *", "live row: jog on slot 4, '▶ 4 *'", str(angle_row(c, 4)))
        text = set_one(1, "0")
        ok("-> angle" not in text and "-> go 1" in text,
           "live row: a Set on another row takes the wheel there, teaching nothing",
           text[-300:])
        settle()
        ok(angle_row(c, 1)[0] == "▶ 1" and angle_row(c, 4) == ("4", 216.0),
           "live row: slot 4 back to its taught angle, the marker on slot 1",
           f"{angle_row(c, 1)} {angle_row(c, 4)}")

        # a jog, then the live row edited: an ordinary change, the wheel goes
        jog("JOG_M1", "WHEELLY_JOG_DOWN")
        ok(angle_row(c, 1)[0] == "▶ 1 *", "live row: jog on slot 1, '▶ 1 *'", str(angle_row(c, 1)))
        text = set_one(1, "5.00")
        ok("-> angle 1 5.00" in text and "-> go 1" in text,
           "live row: the live row edited is a change of that angle, and the wheel goes",
           text[-300:])
        settle()
        ok(angle_row(c, 1) == ("▶ 1", 5.0) and abs(angle() - 5.0) <= 0.8,
           "live row: and arrives, '▶ 1' at 5.00", f"{angle_row(c, 1)} {angle()}")

        # at rest, no definition at a poll
        c.s.settimeout(0.2)
        defined = 0
        end = time.monotonic() + 2.0
        while time.monotonic() < end:
            try:
                data = c.s.recv(65536)
            except socket.timeout:
                continue
            defined += data.count(b"defNumberVector")
            c.parser.feed(data)
            for _, element in c.parser.read_events():
                c._collect(element)
        ok(defined == 0, "live row: at rest no definition at every poll", f"{defined} in 2 s")

        # a jog, then the sweep: the row goes back BEFORE the turn - a
        # definition during or after it wipes the plot - and the plot arrives
        jog("JOG_P1")
        ok(angle_row(c, 1)[0] == "▶ 1 *", "live row: jog before the sweep, '▶ 1 *'",
           str(angle_row(c, 1)))
        c.send(f"<enableBLOB device='{DEVICE}'>Also</enableBLOB>")
        c.set_switch("WHEELLY_SWEEP", "RUN")
        c.pump(0.3)
        result = c.wait_state("WHEELLY_SWEEP", ("Ok", "Alert"), 60)
        c.pump(1.0)
        plot = c.props.get("WHEELLY_SWEEP_PLOT", {}).get("elements", {}).get("PLOT", {}).get("value", "")
        ok(result == "Ok" and angle_row(c, 1) == ("▶ 1", 5.0) and len(plot) > 1000,
           "live row: the sweep gives the row back its taught angle, and the plot arrives",
           f"{result} {angle_row(c, 1)} {len(plot)}")

        # the register: the confirmation is a teach, the edit a set
        register = os.path.join(bench.home, ".indi", "wheelly_movements.csv")
        rows = open(register).read().splitlines() if os.path.exists(register) else []
        kinds = [(r.split(",")[1], r.split(",")[6]) for r in rows if ",angle-" in r]
        ok(kinds == [("2", "angle-taught"), ("1", "angle-set")],
           "live row: the confirmation is an angle-taught row, the edit an angle-set",
           str(kinds))
    finally:
        c.close()
        bench.close()


def test_failure_stops_the_capture():
    print("the wheel that never arrives")
    # a fast fake motor: the test is about the verdict, not about the time a
    # slow move takes (every leg lands 6 degrees past where it was sent, the
    # shortest way - the default - backs up and overshoots
    # again, until the retries are used up)
    bench = Bench("--stuck", "--slip-degrees", "6", "--ms-per-degree", "2",
                  language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    try:
        bench.connect(c)
        c.pump(1.5)
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", 2)
        result = c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 30)
        ok(result == "Alert",
           "FILTER_SLOT goes to Alert: that is what stops the sequence in Ekos", result)
        text = " ".join(c.messages[-5:])
        ok("NON raggiunta" in text or "ritentativ" in text,
           "and the message explains what happened", text[-250:])
        # the hint on slip or stall: a detent left in place is
        # the first suspect, and the log says where the guide removes it
        text = " ".join(c.messages[-6:])
        # "Il corpo della ruota." is the END of the line: an INDI message is
        # cut silently at 255 characters, and a cut hint would lose it
        ok("fermo della ruota" in text and "capitolo 10, Il corpo della ruota." in text,
           "and suggests checking that the detent was removed (guide, chapter 10)",
           text[-300:])
    finally:
        c.close()
        bench.close()


def test_faulty_sensor():
    print("the wheel that moves by itself, and the advice that comes of it")
    # A wheel that drifts at rest. The firmware notices and
    # says so; the driver must turn it into ADVICE, because the user does not
    # know that a holding current exists nor what value to start from. It is
    # the reason the event exists: without the advice it would be just
    # another alarm.
    bench = Bench("--drift", "0.4", language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    try:
        bench.connect(c)
        c.pump(1.5)
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", 2)
        c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 10)
        before = len(c.messages)
        c.pump(6.0)
        text = " ".join(c.messages[before:])
        ok("spostata" in text or "sola" in text,
           "the driver says it moved by itself", text[-260:])
        ok("tenuta" in text.lower(), "and suggests the holding current", text[-260:])
        ok("150" in text, "also saying what value to start from", text[-260:])
        # and it does not ask "if yours has none": the detent
        # is always removed, the holding current is the single advice
        ok("tacca" not in text, "and asks nothing about a detent", text[-260:])
    finally:
        c.close()
        bench.close()

    print("the sensor that does not answer")
    bench = Bench("--sensor-silent", language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    try:
        bench.connect(c)
        c.pump(1.5)
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", 3)
        result = c.wait_state("FILTER_SLOT", ("Alert",), 10)
        ok(result == "Alert", "with a silent sensor the filter change fails", result)
        text = " ".join(c.messages[-6:])
        ok("ponticello" in text or "sensore" in text.lower(),
           "and the message sends you to look in the right place", text[-250:])
    finally:
        c.close()
        bench.close()


def test_flickering_magnet():
    """A FLICKERING MAGNET (seen on the reference wheel: magnitude 314,
    around the AS5600's threshold): without hysteresis the firmware sends
    '! sensor md=0' tens of times a second. With it the Ekos log says the
    magnet is lost once per episode: the fakes flicker for 1.5 s of every 4,
    so in 5.5 s two messages, not seventy."""
    print("a flickering magnet: said once per episode")
    bench = Bench("--magnet-flicker", "20", language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    try:
        before = len(c.messages)
        bench.connect(c)
        c.pump(5.5)
        lost = [m for m in c.messages[before:] if "non rileva più il magnete" in m]
        ok(1 <= len(lost) <= 2, "the lost magnet is in the log once per episode",
           f"{len(lost)} messages")
    finally:
        c.close()
        bench.close()


def test_calibration():
    print("calibration actions and holding current")
    bench = Bench(language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    try:
        bench.connect(c)
        c.pump(1.5)

        ok(abs(angle_row(c, 3)[1] - 144.0) < 0.01,
           "the calibration angles come from the wheel", str(angle_row(c, 3)))

        before = len(c.messages)
        c.set_switch("WHEELLY_SAVE", "SAVE")
        result = c.wait_state("WHEELLY_SAVE", ("Ok", "Alert"), 8)
        ok(result == "Ok" and "Taratura salvata nella ruota" in " ".join(c.messages[before:]),
           "saving into the wheel succeeds", result)
        # the same, from Options
        before = len(c.messages)
        c.set_switch("WHEELLY_CONFIG", "SAVE")
        result = c.wait_state("WHEELLY_CONFIG", ("Ok", "Alert"), 8)
        c.pump(0.3)
        ok(result == "Ok" and "Taratura salvata nella ruota" in " ".join(c.messages[before:]),
           "and from Options, 'Configurazione della ruota'", result)

        # The holding current is off by default: the light is grey AND THE
        # FIELD SAYS 0, the wheel's real value. Rejected: keeping the
        # recommended 150 there as a proposal and leaving the "off" to the
        # light - a user who saved 0, reconnected and saw 150 would believe
        # the wheel had gone back to 150. The recommendation is in the drift
        # message (test_faulty_sensor checks the "150" there).
        hold = c.props["WHEELLY_HOLD"]
        ok(hold["state"] == "Idle", "the holding current starts OFF (grey light)",
           hold["state"])
        ok(abs(float(hold["elements"]["HOLD_MA"]["value"])) < 0.001,
           "and the field shows the wheel's real 0, not a proposal",
           hold["elements"]["HOLD_MA"]["value"])
        before = len(c.messages)
        c.set_number("WHEELLY_HOLD", "HOLD_MA", 50)
        c.wait_state("WHEELLY_HOLD", ("Ok", "Alert"), 8)
        c.pump(0.6)
        text = " ".join(c.messages[before:])
        ok("scalda" in text.lower() and "tenuta" in text.lower(),
           "and switching it on says what it costs", text[-250:])
        # and switched off again from the panel it turns GREY, as on
        # connection: green would make the same state read two ways
        c.set_number("WHEELLY_HOLD", "HOLD_MA", 0)
        c.wait_state("WHEELLY_HOLD", ("Ok", "Idle", "Alert"), 8)
        c.pump(0.4)
        ok(c.props["WHEELLY_HOLD"]["state"] == "Idle",
           "switched off from the panel, the light turns grey again",
           c.props["WHEELLY_HOLD"]["state"])
        # The SECOND connection: the field must show what
        # the WHEEL has, read at connection, not what the panel had. So the
        # panel is left at 50 and the wheel set to 0 behind the driver's
        # back, then the other way round: a field that is not rewritten from
        # the wheel shows the stale number, whichever it is
        c.set_number("WHEELLY_HOLD", "HOLD_MA", 50)
        c.wait_state("WHEELLY_HOLD", ("Ok", "Alert"), 8)
        for wanted in (0, 40):
            c.set_switch("CONNECTION", "DISCONNECT", ["CONNECT"])
            c.wait_state("CONNECTION", ("Idle",), 10)
            c.pump(0.5)
            reply = talk_to_the_wheel("hold %d" % wanted)
            c.set_switch("CONNECTION", "CONNECT", ["DISCONNECT"])
            c.wait_state("CONNECTION", ("Ok", "Alert"), 15)
            c.wait_property("WHEELLY_HOLD", 10)
            c.pump(1.0)
            got = c.props.get("WHEELLY_HOLD", {}).get("elements", {}).get("HOLD_MA", {}).get("value")
            ok(got is not None and abs(float(got) - wanted) < 0.001,
               f"reconnected with {wanted} mA in the wheel, the field shows {wanted}",
               f"{got} {reply[-1:]}")
        c.set_number("WHEELLY_HOLD", "HOLD_MA", 0)
        c.wait_state("WHEELLY_HOLD", ("Idle", "Alert"), 8)

        # speed and acceleration REACH THE WHEEL: a "Set" that sent only the
        # current would leave the two fields showing what had been written
        # until the next connection re-read the wheel's values. The
        # number the wheel sends back is checked, not the one the panel
        # already had: values different from the starting ones are set and
        # the motor state is asked for again
        c.send(f"<newNumberVector device='{DEVICE}' name='WHEELLY_MOTOR'>"
               "<oneNumber name='RUN_MA'>340</oneNumber>"
               "<oneNumber name='SPEED'>260</oneNumber>"
               "<oneNumber name='ACCEL'>1500</oneNumber></newNumberVector>")
        result = c.wait_state("WHEELLY_MOTOR", ("Ok", "Alert"), 8)
        # ...and the WHEEL is checked, not the panel: the panel showed what had
        # been written even when nothing was sent. Disconnected and
        # reconnected, the driver re-reads speed and acceleration from the wheel
        c.set_switch("CONNECTION", "DISCONNECT", ["CONNECT"])
        c.wait_state("CONNECTION", ("Idle", "Ok", "Alert"), 8)
        c.pump(0.5)
        c.set_switch("CONNECTION", "CONNECT", ["DISCONNECT"])
        c.wait_state("CONNECTION", ("Ok", "Alert"), 15)
        c.wait_property("WHEELLY_MOTOR", 10)
        c.pump(0.8)
        mot = c.props["WHEELLY_MOTOR"]["elements"]
        ok(result == "Ok" and abs(float(mot["SPEED"]["value"]) - 260) < 0.5
           and abs(float(mot["ACCEL"]["value"]) - 1500) < 0.5,
           "the panel's speed and acceleration reach the wheel",
           "%s %s" % (result, {k: v["value"] for k, v in mot.items()}))

        # the LED mode: "pulse" by default, read from the wheel
        led = c.props["WHEELLY_LED"]["elements"]
        ok(led["LED_PULSE"]["value"] == "On",
           "the LED starts in 'pulse while moving'",
           str({k: v["value"] for k, v in led.items()}))
        for choice in ("LED_OFF", "LED_ON", "LED_PULSE"):
            others = [x for x in ("LED_ON", "LED_PULSE", "LED_OFF", "LED_TEST") if x != choice]
            c.set_switch("WHEELLY_LED", choice, others)
            result = c.wait_state("WHEELLY_LED", ("Ok", "Alert"), 8)
            c.pump(0.3)
            led = c.props["WHEELLY_LED"]["elements"]
            ok(result == "Ok" and led[choice]["value"] == "On",
               f"{choice}: the wheel accepts it and the panel reads it back", result)

        # the LED test
        c.set_switch("WHEELLY_LED", "LED_TEST", ["LED_ON", "LED_PULSE", "LED_OFF"])
        result = c.wait_state("WHEELLY_LED", ("Ok", "Alert"), 8)
        ok(result == "Ok", "the LED test starts", result)
        text = " ".join(c.messages[-3:])
        ok("Morse" in text, "and says it is blinking in Morse", text[-200:])

        # the movement log is off by default
        reg = c.props["WHEELLY_LOG"]["elements"]
        ok(reg["LOG_OFF"]["value"] == "On",
           "the movement log starts off",
           str({k: v["value"] for k, v in reg.items()}))

        # the log with the old Italian name is not left
        # behind: with the log switched on, the history continues in the file
        # with the new name - the second-use defect of whoever already had a log
        indi = os.path.join(bench.home, ".indi")
        os.makedirs(indi, exist_ok=True)
        with open(os.path.join(indi, "wheelly_movimenti.csv"), "w") as f:
            f.write("timestamp,slot\nearlier-row,1\n")
        c.set_switch("WHEELLY_LOG", "LOG_ON", ["LOG_OFF"])
        c.wait_state("WHEELLY_LOG", ("Ok", "Alert"), 5)
        new = os.path.join(indi, "wheelly_movements.csv")
        inside = open(new).read() if os.path.exists(new) else ""
        ok("earlier-row" in inside and not os.path.exists(os.path.join(indi, "wheelly_movimenti.csv")),
           "the log with the old name continues in wheelly_movements.csv", inside[:80])
        c.set_switch("WHEELLY_LOG", "LOG_OFF", ["LOG_ON"])
    finally:
        c.close()
        bench.close()


def test_settle_hold():
    """The hold after arrival: the second element of the holding
    property, read back from the wheel at connection, sent to it when changed,
    and the move time cap following it."""
    print("the hold after arrival, in the holding property")
    WARNING = "più dei 30 s dopo i quali Ekos rinuncia"
    bench = Bench(language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    try:
        bench.connect(c)
        c.pump(1.5)
        hold = c.props["WHEELLY_HOLD"]["elements"]
        ok("SETTLE_MS" in hold and abs(float(hold["SETTLE_MS"]["value"]) - 300) < 0.001,
           "the holding property has the hold after arrival, 300 ms from the wheel",
           str(hold.get("SETTLE_MS")))
        ok(hold.get("SETTLE_MS", {}).get("label") == "Tenuta dopo l'arrivo (ms)",
           "labelled in the panel's language", str(hold.get("SETTLE_MS")))
        ok(len(hold) == 2, "and no new property: the same one, two fields", str(list(hold)))

        # set from the panel: it reaches the wheel, and the cap follows it -
        # 2 s after each of the 14 legs puts the worst case past Ekos's 30 s
        before = len(c.messages)
        c.set_number("WHEELLY_HOLD", "SETTLE_MS", 2000)
        state = c.wait_state("WHEELLY_HOLD", ("Ok", "Idle", "Alert"), 8)
        c.pump(0.6)
        text = " ".join(c.messages[before:])
        ok(state in ("Ok", "Idle"), "setting it is accepted", state)
        ok(abs(float(c.props["WHEELLY_HOLD"]["elements"]["SETTLE_MS"]["value"]) - 2000) < 0.001,
           "the field shows the wheel's reply", "")
        ok(WARNING in text, "and the log warns that the cap passes Ekos's 30 s", text[-300:])
        # a move still ends Ok: the driver's own cap is the wheel's, grown
        c.set_number("WHEELLY_HOLD", "SETTLE_MS", 1000)
        c.wait_state("WHEELLY_HOLD", ("Ok", "Idle", "Alert"), 8)
        t0 = time.monotonic()
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", 3)
        c.pump(0.5)
        result = c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 40)
        took = time.monotonic() - t0
        ok(result == "Ok" and took >= 1.0,
           "a move with a 1 s hold ends Ok, after the hold", f"{result} {took:.1f} s")
        # the current alone does not touch the hold (an older firmware,
        # without `settle`, must not go to Alert when only the current is set)
        c.set_number("WHEELLY_HOLD", "HOLD_MA", 40)
        c.wait_state("WHEELLY_HOLD", ("Ok", "Alert"), 8)
        c.set_number("WHEELLY_HOLD", "HOLD_MA", 0)
        c.wait_state("WHEELLY_HOLD", ("Idle", "Alert"), 8)
        ok(abs(float(c.props["WHEELLY_HOLD"]["elements"]["SETTLE_MS"]["value"]) - 1000) < 0.001,
           "setting the current leaves the hold as it was", "")

        # behind the driver's back: the field shows what the WHEEL has
        c.set_switch("CONNECTION", "DISCONNECT", ["CONNECT"])
        c.wait_state("CONNECTION", ("Idle",), 10)
        c.pump(0.5)
        heard = talk_to_the_wheel("settle")
        ok(any("ms=1000" in r for r in heard), "the panel's value is in the wheel", str(heard))
        talk_to_the_wheel("settle 650")
        c.set_switch("CONNECTION", "CONNECT", ["DISCONNECT"])
        c.wait_state("CONNECTION", ("Ok", "Alert"), 15)
        c.wait_property("WHEELLY_HOLD", 10)
        c.pump(1.0)
        got = c.props["WHEELLY_HOLD"]["elements"]["SETTLE_MS"]["value"]
        ok(abs(float(got) - 650) < 0.001, "reconnected, the field shows the wheel's 650", got)
    finally:
        c.close()
        bench.close()


def talk_to_the_wheel(text, seconds=3.0):
    """A command sent to the wheel DIRECTLY, with the driver disconnected: to
    look at the wheel and not at the panel, and to change something behind
    the driver's back. Returns the lines received up to the result included."""
    import termios
    import tty
    fd = os.open(SERIAL, os.O_RDWR | os.O_NOCTTY)
    try:
        tty.setraw(fd)
        termios.tcflush(fd, termios.TCIOFLUSH)
        os.write(fd, (text + "\n").encode())
        data = b""
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if not select_ready(fd, 0.2):
                continue
            data += os.read(fd, 4096)
            lines = data.decode(errors="replace").replace("\r", "").split("\n")
            if any(r.startswith(("ok", "err")) for r in lines):
                return [r for r in lines if r]
        return [r for r in data.decode(errors="replace").splitlines() if r]
    finally:
        os.close(fd)


def test_jog():
    """THE JOG ROWS: pitch, 10, 1, 0.1 degrees each way
    in the calibration tab. A jog is a move TO the angle read plus the step,
    done by the firmware's closed loop and followed here: Busy while it
    moves, Ok and the angle in the log when done, FILTER_SLOT untouched. The
    Set on the current slot's row teaches the angle reached (no "Save
    position" button: test_live_row has the details)."""
    print("the jog rows, and the Set that teaches")
    bench = Bench(language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    # two rows of at most four buttons: KStars turns five or more into a
    # drop-down menu, and a single row of eight would be one
    ROWS = {"WHEELLY_JOG_DOWN": ["JOG_M_PITCH", "JOG_M10", "JOG_M1", "JOG_M0_1"],
            "WHEELLY_JOG_UP": ["JOG_P0_1", "JOG_P1", "JOG_P10", "JOG_P_PITCH"]}

    def press(element):
        row = next(r for r, e in ROWS.items() if element in e)
        before = len(c.messages)
        c.set_switch(row, element, [x for x in ROWS[row] if x != element])
        c.pump(0.3)
        result = c.wait_state(row, ("Ok", "Alert"), 15)
        c.pump(0.5)
        return result, " ".join(c.messages[before:])

    def angle():
        return float(c.props["WHEELLY_POSITION"]["elements"]["ANGLE"]["value"])

    try:
        ok(bench.connect(c) == "Ok", "the driver connects")
        c.wait_property("WHEELLY_JOG_UP", 10)
        labels = {}
        for row, elements in ROWS.items():
            got = c.props.get(row, {}).get("elements", {})
            ok(list(got) == elements and len(got) <= 4,
               f"jog: {row} has its buttons, at most four", str(list(got)))
            labels.update({k: v.get("label") for k, v in got.items()})
        ok(labels.get("JOG_M_PITCH") == "-72°" and labels.get("JOG_M0_1") == "-0,1°"
           and labels.get("JOG_P10") == "+10°" and labels.get("JOG_P_PITCH") == "+72°",
           "jog: 360/5, 10, 1, 0.1 each way, translated", str(labels))
        ok("TEACH" not in c.props.get("WHEELLY_SAVE", {}).get("elements", {})
           and "WHEELLY_TEACH" not in c.props,
           "jog: no teach action nor 'Save position': the Set on the row teaches",
           str(list(c.props.get("WHEELLY_SAVE", {}).get("elements", {}))))
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", 2)
        c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 20)
        c.pump(0.5)
        start = angle()
        result, text = press("JOG_P1")
        ok(result == "Ok" and "da dove chiedeva il passo" in text,
           "jog +1: Ok, and the log says where the wheel is, in Italian", f"{result} {text[-200:]}")
        ok(abs(angle() - start - 1.0) <= 0.5,
           "jog +1: the wheel really moved one degree", f"{start} -> {angle()}")
        ok(c.state("FILTER_SLOT") == "Ok", "jog: FILTER_SLOT is not a filter change",
           c.state("FILTER_SLOT"))
        start = angle()
        result, text = press("JOG_M0_1")
        ok(result == "Ok" and -0.25 <= angle() - start <= -0.02,
           "jog -0.1: a small step back, really taken", f"{result} {start} -> {angle()}")
        # the Set on row 2, as shown: slot 2 takes the angle reached
        now = angle()
        before = len(c.messages)
        set_row(c, 2, c.props["WHEELLY_ANGLE_2"]["elements"]["ANGLE"]["value"])
        c.pump(0.3)
        result = c.wait_state("WHEELLY_ANGLE_2", ("Ok", "Alert"), 8)
        c.pump(0.8)
        text = " ".join(c.messages[before:])
        taught = angle_row(c, 2)[1]
        ok(result == "Ok" and abs(taught - now) < 0.1 and "Salva nella ruota" in text,
           "Set on row 2: slot 2 takes the angle the jogs reached, and says how to keep it",
           f"{result} {taught} vs {now} {text[-200:]}")
        # one pitch: from slot 2 to slot 3, the jog's own verdict
        result, text = press("JOG_P_PITCH")
        c.pump(0.6)
        ok(result == "Ok" and abs(angle() - 144.0) <= 0.8
           and c.props["FILTER_SLOT"]["elements"]["FILTER_SLOT_VALUE"]["value"] in ("3", "3.0"),
           "jog +72: one slot pitch, onto slot 3", f"{result} {angle()} {text[-150:]}")
        # refused while the wheel moves: a filter change, then a jog at once
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", 4)
        c.pump(0.1)
        result, text = press("JOG_P10")
        ok(result == "Alert" and "mentre si muove" in text,
           "jog: refused while the wheel moves, and says why", f"{result} {text[-200:]}")
        c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 20)
    finally:
        c.close()
        bench.close()


def test_no_detent():
    """NO DETENT OPTION. The wheel's detent is always
    removed - the motor cannot climb out of its notches - so the panel has no
    detent switch and the log never warns about one, not at connection nor
    when the holding current goes back to 0 (it would have sounded on every
    wheel). What it does instead: when the motor stalls, the log suggests
    checking that the detent was really removed. The stall here is the
    simulator's asymmetric detent left in place, and the jog +10 goes up the
    steep flank, so the jog fails; in English, the other catalog."""
    print("no detent option, and the hint on a stall")
    bench = Bench("--stall", "up", "--ms-per-degree", "2")
    c = Client(INDI_PORT)
    HINT = "check first that the wheel's detent"
    try:
        ok(bench.connect(c) == "Ok", "the driver connects")
        c.wait_property("WHEELLY_JOG_UP", 10)
        c.pump(1.0)
        ok("WHEELLY_DETENT" not in c.props,
           "no detent: the panel has no detent switch", str(sorted(c.props)))
        text = " ".join(c.messages)
        ok("detent" not in text.lower(),
           "no detent: nothing about a detent at connection", text[-250:])
        c.set_number("WHEELLY_HOLD", "HOLD_MA", 150)
        c.wait_state("WHEELLY_HOLD", ("Ok", "Alert"), 8)
        before = len(c.messages)
        c.set_number("WHEELLY_HOLD", "HOLD_MA", 0)
        c.wait_state("WHEELLY_HOLD", ("Idle", "Alert"), 8)
        c.pump(0.5)
        text = " ".join(c.messages[before:])
        ok("detent" not in text.lower(),
           "no detent: holding back to 0 says nothing about a detent", text[-250:])

        before = len(c.messages)
        # +10 and not +1: a stalled +1 ends 1 degree off, which an Alert
        # tolerance above 1 (an older factory value was 1.5)
        # calls a "warning", and the jog Ok
        c.set_switch("WHEELLY_JOG_UP", "JOG_P10", ["JOG_P0_1", "JOG_P1", "JOG_P_PITCH"])
        c.pump(0.3)
        result = c.wait_state("WHEELLY_JOG_UP", ("Ok", "Alert"), 30)
        c.pump(0.5)
        text = " ".join(c.messages[before:])
        ok(result == "Alert" and "did not get where the step asked" in text,
           "stall: the jog up the stalling flank fails", f"{result} {text[-250:]}")
        ok(HINT in text and "chapter 10, The wheel body." in text,
           "stall: and the log suggests checking that the detent was removed",
           text[-300:])
    finally:
        c.close()
        bench.close()


def test_direction():
    """ONE WAY ROUND (the motor hums and stalls against the steep flank of an
    asymmetric detent, so such a wheel should turn one way only). The panel shows the wheel's direction, sets it, reminds to
    save; the move time cap follows speed and direction, and past Ekos's 30 s
    the log warns - when it is set and at connection. And end to end: on a
    wheel that stalls going up (the reference wheel's detent, before it was
    removed; kept here for a mechanism stiffer one way),
    the shortest way - the factory default - fails and one
    way down arrives."""
    print("the direction of travel")
    bench = Bench("--stall", "up", language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    WARNING = "più dei 30 s dopo i quali Ekos rinuncia"

    def elements():
        e = c.props.get("WHEELLY_DIRECTION", {}).get("elements", {})
        return {k: v["value"] for k, v in e.items()}

    def choose(element):
        others = [x for x in ("DIR_SHORTEST", "DIR_UP", "DIR_DOWN") if x != element]
        before = len(c.messages)
        c.set_switch("WHEELLY_DIRECTION", element, others)
        result = c.wait_state("WHEELLY_DIRECTION", ("Ok", "Alert"), 8)
        c.pump(0.4)
        return result, " ".join(c.messages[before:])

    def motor(speed, accel):
        before = len(c.messages)
        c.send(f"<newNumberVector device='{DEVICE}' name='WHEELLY_MOTOR'>"
               "<oneNumber name='RUN_MA'>350</oneNumber>"
               f"<oneNumber name='SPEED'>{speed}</oneNumber>"
               f"<oneNumber name='ACCEL'>{accel}</oneNumber></newNumberVector>")
        c.wait_state("WHEELLY_MOTOR", ("Ok", "Alert"), 8)
        c.pump(0.4)
        return " ".join(c.messages[before:])

    def go(slot):
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", slot)
        c.pump(0.3)
        return c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 30)

    try:
        ok(bench.connect(c) == "Ok", "the driver connects")
        c.wait_property("WHEELLY_DIRECTION", 10)
        c.pump(1.0)
        labels = {k: v.get("label") for k, v in
                  c.props.get("WHEELLY_DIRECTION", {}).get("elements", {}).items()}
        # the shortest way (the assembly guide removes the detent): the
        # factory value, from the header
        ok(elements() == {"DIR_SHORTEST": "On", "DIR_UP": "Off", "DIR_DOWN": "Off"}
           and c.state("WHEELLY_DIRECTION") == "Ok",
           "direction: on connection the shortest way, the factory default, read from the wheel",
           "%s %s" % (elements(), c.state("WHEELLY_DIRECTION")))
        ok(labels.get("DIR_SHORTEST") == "La via più corta"
           and labels.get("DIR_UP") == "Solo angoli crescenti",
           "direction: the labels are translated", str(labels))

        # end to end, on the wheel that stalls going up: the shortest way from
        # slot 1 to slot 2 (0 -> 72 degrees) is up, into the steep flank
        ok(go(1) == "Ok", "direction: to slot 1 first")
        ok(go(2) == "Alert", "direction: the shortest way into the stall: FILTER_SLOT Alert")
        # one way down, the option kept for such a wheel, goes the long way
        result, text = choose("DIR_DOWN")
        ok(result == "Ok" and elements()["DIR_DOWN"] == "On",
           "direction: 'decreasing angles only' from the panel, accepted and read back",
           "%s %s" % (result, elements()))
        ok("Salva nella ruota" in text, "direction: and the log reminds to save", text[-200:])
        ok(go(2) == "Ok", "direction: one way down, 1 -> 2 arrives despite the stall going up")
        ok(go(1) == "Ok", "direction: and back to 1, still down")
        result, text = choose("DIR_SHORTEST")
        ok(result == "Ok" and elements()["DIR_SHORTEST"] == "On",
           "direction: back to the shortest way from the panel", "%s %s" % (result, elements()))

        # the cap: a slow 50/300 is fine the shortest way...
        text = motor(50, 300)
        ok(WARNING not in text, "direction: slow, the shortest way stays under Ekos's 30 s",
           text[-250:])
        # ...and one way it is not: said when the direction is chosen
        result, text = choose("DIR_DOWN")
        ok(WARNING in text, "direction: slow and one way, the log warns about Ekos's 30 s",
           text[-300:])
        # and when the speed is chosen
        motor(300, 1200)
        text = motor(50, 300)
        ok(WARNING in text, "direction: and when a slow speed is set", text[-300:])
        # and at connection
        c.set_switch("CONNECTION", "DISCONNECT", ["CONNECT"])
        c.wait_state("CONNECTION", ("Idle", "Alert"), 8)
        c.pump(0.5)
        reply = talk_to_the_wheel("direction")
        ok(any("direction=down" in r for r in reply) and
           any(re.search(r"ceiling=(\d+)", r) and int(re.search(r"ceiling=(\d+)", r).group(1)) > 30000
               for r in reply),
           "direction: the panel really set the wheel, and its cap is past 30 s", str(reply))
        before = len(c.messages)
        c.set_switch("CONNECTION", "CONNECT", ["DISCONNECT"])
        c.wait_state("CONNECTION", ("Ok", "Alert"), 15)
        c.wait_property("WHEELLY_DIRECTION", 10)
        c.pump(1.0)
        text = " ".join(c.messages[before:])
        ok(WARNING in text, "direction: found slow and one way, the log says so on connection",
           text[-300:])
        # the factory speed (300/1200): no warning
        text = motor(300, 1200)
        ok(WARNING not in text, "direction: at the default speed one way fits in 30 s", text[-250:])
    finally:
        c.close()
        bench.close()


def test_wrong_port():
    print("the wrong port must not pass for a good one")
    # A fake serial port that answers nothing is opened. Frankenwheely lied
    # about this: its Handshake returned true in any case, and pointed at the
    # wrong port the driver happily declared itself connected.
    import tty
    master, slave = os.openpty()
    tty.setraw(master)
    tty.setraw(slave)
    silent = f"/tmp/wheelly_silent_{os.getpid()}"
    if os.path.islink(silent) or os.path.exists(silent):
        os.unlink(silent)
    os.symlink(os.ttyname(slave), silent)

    bench = Bench()
    c = Client(INDI_PORT)
    try:
        c.pump(1.0)
        c.set_text("DEVICE_PORT", "PORT", silent)
        c.pump(0.4)
        c.set_switch("CONNECTION", "CONNECT", ["DISCONNECT"])
        result = c.wait_state("CONNECTION", ("Ok", "Alert"), 20)
        ok(result == "Alert",
           "on a port that does not answer the connection FAILS", result)
        auto = c.props.get("DEVICE_AUTO_SEARCH", {}).get("elements", {})
        ok(auto.get("INDI_DISABLED", {}).get("value") == "On",
           "and Auto Search was off: no other serial port was tried",
           str({k: v.get("value") for k, v in auto.items()}))
        text = " ".join(c.messages[-4:])
        ok("Wheelly" in text or "ruota" in text.lower() or "porta" in text.lower(),
           "and says so, instead of behaving strangely", text[-200:])
    finally:
        c.close()
        bench.close()
        os.close(slave)
        os.close(master)
        if os.path.islink(silent):
            os.unlink(silent)


def test_motor_supply():
    print("the motor's 12 V after the USB: refused, then set up and said")
    # The assembly guide's order, USB first: the wheel talks, the motor
    # driver does not until the 12 V arrive. A filter change then is refused
    # with a sentence that names the 12 V, and the first one after the 12 V
    # moves, with one line saying the driver was set up (EV_DRIVER).
    start = time.monotonic()
    bench = Bench("--vm-off-for", "6000")
    c = Client(INDI_PORT)
    try:
        bench.connect(c)
        c.pump(1.0)
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", 3)
        ok(c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 10) == "Alert",
           "no 12 V: the filter change is refused", c.state("FILTER_SLOT"))
        ok(any("12 V supply connected" in m for m in c.messages),
           "and the log names the 12 V", str(c.messages[-3:]))
        c.pump(max(0.0, 7.0 - (time.monotonic() - start)))     # the 12 V arrive
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", 3)
        ok(c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 30) == "Ok",
           "12 V on: the filter change arrives", c.state("FILTER_SLOT"))
        c.pump(1.0)
        said = [m for m in c.messages if "got its 12 V after the wheel had started" in m]
        ok(len(said) == 1, "and the log says once that the driver was set up", str(said))
    finally:
        c.close()
        bench.close()


def start_simulator(link, *knobs):
    """Another simulator - another wheel on the cable, the same serial number."""
    launch = [sys.executable, str(SIMULATOR)] if IS_PYTHON else [str(SIMULATOR)]
    sim = subprocess.Popen([*launch, "--pty", "--link", link, *knobs],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        if os.path.exists(link):
            break
        time.sleep(0.05)
    return sim


def stop(process):
    try:
        process.send_signal(signal.SIGINT)
        process.wait(timeout=3)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


def replace_link(path, target):
    if os.path.islink(path) or os.path.exists(path):
        os.unlink(path)
    os.symlink(target, path)


def test_usb_unplugged():
    print("the wheel's USB unplugged and plugged back: the driver finds it again")
    # SEEN ON THE REFERENCE WHEEL: unplugged and plugged back, the wheel came
    # back as another ttyACMn while the driver stayed "Connected" on the dead
    # descriptor - "Write Error: Input/output error" 25 times in a few
    # seconds, the angle frozen, commands lost - until Disconnect/Connect by
    # hand. Here the port the user chose is a name that VANISHES with the
    # wheel (like /dev/ttyACM1), and the wheel comes back on a new pty, found
    # through its by-id link (the bench's own folder, see Bench).
    lost_text = ("USB link to the wheel was lost", "collegamento USB con la ruota")
    back_text = ("is back on", "è tornata su")
    down_text = ("not reachable right now", "non è raggiungibile")

    def count(texts):
        return sum(1 for m in c.messages if any(t in m for t in texts))

    def wait_message(texts, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            c.pump(0.2)
            if count(texts):
                return True
        return False

    acm = f"/tmp/wheelly_acm_{os.getpid()}"
    second = f"/tmp/wheelly_link2_{os.getpid()}"
    third = f"/tmp/wheelly_link3_{os.getpid()}"
    bench = Bench()
    by_id = os.path.join(bench.by_id, "usb-Espressif_Wheelly_bench-if00")
    replace_link(acm, os.path.realpath(SERIAL))
    replace_link(by_id, os.path.realpath(SERIAL))
    c = Client(INDI_PORT)
    sims = []
    try:
        c.pump(1.0)
        c.set_text("DEVICE_PORT", "PORT", acm)
        c.pump(0.4)
        c.set_switch("CONNECTION", "CONNECT", ["DISCONNECT"])
        ok(c.wait_state("CONNECTION", ("Ok", "Alert"), 15) == "Ok",
           "connected on the port that will vanish", c.state("CONNECTION"))
        c.pump(1.5)

        # UNPLUGGED: the wheel comes back on another pty, the old name goes
        sims.append(start_simulator(second))
        stop(bench.sim)
        os.unlink(acm)
        replace_link(by_id, os.path.realpath(second))
        ok(wait_message(lost_text, 8.0), "the loss is noticed and said",
           str(c.messages[-3:]))
        c.pump(0.5)
        lost_state = c.state("CONNECTION")
        connect_on = c.props.get("CONNECTION", {}).get("elements", {}) \
                      .get("CONNECT", {}).get("value")
        position_lost = c.state("WHEELLY_POSITION")
        ok(wait_message(back_text, 20.0), "and the wheel is found again, by its by-id link",
           str(c.messages[-3:]))
        ok(lost_state == "Ok" and connect_on == "On",
           "while it was away: still connected for Ekos, CONNECTION On and Ok",
           f"{lost_state} {connect_on}")
        ok(position_lost == "Alert", "but the frozen position shown in Alert", position_lost)
        ok(c.wait_state("WHEELLY_POSITION", ("Ok",), 5) == "Ok",
           "and live again once it is back", c.state("WHEELLY_POSITION"))
        back = [m for m in c.messages if any(t in m for t in back_text)]
        ok(back and by_id in back[-1], "on the link that follows the USB serial", str(back))
        c.pump(2.0)
        ok(count(lost_text) == 1 and count(back_text) == 1,
           "ONE line for the loss and ONE for the return, not one per poll",
           f"lost {count(lost_text)}, back {count(back_text)}")
        ok(not any("Write Error" in m or "not answering" in m or "non risponde" in m
                   for m in c.messages),
           "and no write errors in the log", str([m for m in c.messages if "rror" in m]))

        # it works: a filter change on the wheel found again
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", 3)
        ok(c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 30) == "Ok",
           "a filter change after the reconnection arrives", c.state("FILTER_SLOT"))

        # THE SECOND TIME (a defect of the second use hides from a test that
        # unplugs once): now the name the user chose comes back, and the by-id
        # link is gone - the configured port is tried first.
        sims.append(start_simulator(third))
        stop(sims[0])
        os.unlink(by_id)
        replace_link(acm, os.path.realpath(third))
        ok(_wait_count(c, back_text, 2, 25.0),
           "unplugged a second time: found again on the port the user chose",
           str(c.messages[-3:]))
        ok(count(lost_text) == 2, "with one more line for the loss", str(count(lost_text)))
        ok(count(down_text) == 0, "and no complaints while nobody asked anything",
           str(count(down_text)))

        # Disconnect and Connect by hand still work after a reconnection:
        # the descriptor the driver opened itself is released
        c.set_switch("CONNECTION", "DISCONNECT", ["CONNECT"])
        c.wait_state("CONNECTION", ("Idle",), 10)
        c.pump(0.5)
        held = driver_descriptors_on(bench, os.path.realpath(third))
        ok(held == 0, "after Disconnect the driver holds no descriptor on the wheel's port",
           f"{held} still open")
        c.set_switch("CONNECTION", "CONNECT", ["DISCONNECT"])
        ok(c.wait_state("CONNECTION", ("Ok", "Alert"), 15) == "Ok",
           "Disconnect and Connect by hand after a reconnection: connected",
           c.state("CONNECTION"))
    finally:
        c.close()
        for sim in sims:
            stop(sim)
        bench.close()
        for path in (acm, second, third):
            if os.path.islink(path):
                os.unlink(path)


def driver_descriptors_on(bench, device):
    """How many descriptors the driver process has open on `device`
    (Linux, /proc): a descriptor the reconnection opened and Disconnect
    forgot would keep the port - a real one, busy for the next program."""
    found = 0
    children = subprocess.run(["pgrep", "-P", str(bench.server.pid)],
                              capture_output=True, text=True).stdout.split()
    for pid in children:
        folder = f"/proc/{pid}/fd"
        for fd in os.listdir(folder) if os.path.isdir(folder) else []:
            try:
                if os.readlink(os.path.join(folder, fd)) == device:
                    found += 1
            except OSError:
                pass
    return found


def _wait_count(c, texts, wanted, seconds):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        c.pump(0.2)
        if sum(1 for m in c.messages if any(t in m for t in texts)) >= wanted:
            return True
    return False


def test_middle_band():
    print("the middle band: warn but carry on")
    # It is the most wanted behaviour and the easiest to get wrong: outside
    # the good tolerance but inside the alarm one the capture MUST go on. If
    # Alert were set here, a recoverable warning would stop the night.
    #
    # It is reached deterministically, not by hoping for noise: every move
    # lands exactly 0.3 degrees beyond where it was sent, the good tolerance
    # stays 0.1 and the alarm one widens to 5, so the error falls in between
    # and there are no retries to reshuffle the cards. The shortest way and
    # an exact drive: one way the wheel aims short and
    # creeps in with approach legs, and where it stops depends on how many;
    # the shortest way from slot 1 to 3 is one leg up, 0.3 past the target.
    bench = Bench("--stuck", "--slip-degrees", "0.3", "--ratio-error", "0",
                  "--lost-motion", "0", language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    try:
        bench.connect(c)
        c.pump(1.5)
        c.set_switch("WHEELLY_DIRECTION", "DIR_SHORTEST", ["DIR_UP", "DIR_DOWN"])
        ok(c.wait_state("WHEELLY_DIRECTION", ("Ok", "Alert"), 8) == "Ok",
           "the shortest way, from the panel")
        c.send(f"<newNumberVector device='{DEVICE}' name='WHEELLY_TOLERANCE'>"
               "<oneNumber name='GOOD'>0.10</oneNumber>"
               "<oneNumber name='WARN'>5.0</oneNumber>"
               "<oneNumber name='RETRIES'>3</oneNumber></newNumberVector>")
        result = c.wait_state("WHEELLY_TOLERANCE", ("Ok", "Alert"), 8)
        ok(result == "Ok", "the tolerances are set from Ekos", result)

        before = len(c.messages)
        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", 3)
        result = c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 25)
        ok(result == "Ok",
           "in the middle band FILTER_SLOT comes back Ok: the capture goes on",
           result)
        text = " ".join(c.messages[before:])
        ok("prosegue" in text or "tolleranza" in text,
           "but the warning is there and says so", text[-250:])
        ok("NON raggiunta" not in text,
           "and it is not mistaken for a failure", text[-250:])
    finally:
        c.close()
        bench.close()


def test_wrong_device():
    print("a device that answers, but is not a Wheelly")
    # Different from the silent port: here someone answers. Frankenwheely lied
    # about this - its handshake returned true regardless - and connecting to
    # the focuser by mistake the driver declared itself connected to the wheel.
    import threading
    import tty
    master, slave = os.openpty()
    tty.setraw(master)
    tty.setraw(slave)
    fake = f"/tmp/wheelly_impostor_{os.getpid()}"
    if os.path.islink(fake) or os.path.exists(fake):
        os.unlink(fake)
    os.symlink(os.ttyname(slave), fake)

    stop = threading.Event()

    def impostor():
        rest = b""
        while not stop.is_set():
            try:
                if not select_ready(master, 0.1):
                    continue
                data = os.read(master, 4096)
            except OSError:
                return
            if not data:
                return
            rest += data
            while b"\n" in rest:
                _, rest = rest.split(b"\n", 1)
                # it answers as a different device, but it answers
                os.write(master, b"ok name=focheggiatore fw=2.0 proto=1\n")

    threading.Thread(target=impostor, daemon=True).start()

    bench = Bench(language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    try:
        c.pump(1.0)
        c.set_text("DEVICE_PORT", "PORT", fake)
        c.pump(0.4)
        c.set_switch("CONNECTION", "CONNECT", ["DISCONNECT"])
        result = c.wait_state("CONNECTION", ("Ok", "Alert"), 20)
        ok(result == "Alert",
           "a device that answers but is not a Wheelly is REFUSED",
           result)
        text = " ".join(c.messages[-4:])
        ok("Wheelly" in text or "porta" in text.lower(),
           "and the message sends you to check the port", text[-200:])
    finally:
        stop.set()
        c.close()
        bench.close()
        os.close(slave)
        os.close(master)
        if os.path.islink(fake):
            os.unlink(fake)


def test_unknown_protocol():
    print("a firmware speaking another version of the protocol")
    # Only against the simulator: the switch that makes a wheel declare another
    # version is its own.
    # A wheel with a protocol the driver does not know must be REFUSED, with the
    # message that names both versions - not half-driven.
    if not IS_PYTHON:
        print("  (simulator only: the real firmware has no such switch)")
        return
    sys.path.insert(0, str(SIMULATOR.parent))
    # the simulator's protocol module (protocollo.py until the English rename)
    import protocol
    # the next one, and the previous one: protocol 1 had the rotation trim,
    # and its target meant angle + trim
    for other in (protocol.PROTOCOL_VERSION + 1, protocol.PROTOCOL_VERSION - 1):
        bench = Bench("--protocol-version", str(other), language="en_US.UTF-8")
        c = Client(INDI_PORT)
        try:
            result = bench.connect(c)
            ok(result == "Alert", f"protocol {other} is refused", str(result))
            text = " ".join(c.messages[-6:])
            # the English text of msg.wrong.protocol, with both numbers in it
            ok(f"speaks protocol {other}" in text
               and f"this driver speaks {protocol.PROTOCOL_VERSION}" in text,
               "and the message states both versions", text[-250:])
        finally:
            c.close()
            bench.close()


def test_too_many_positions():
    print("a wheel with more positions than the driver handles")
    # The warning goes through the catalogue and states the whole range
    # (not English written in the code, and not only the maximum).
    if not IS_PYTHON:
        print("  (simulator only: the real firmware already refuses the number)")
        return
    sys.path.insert(0, str(SIMULATOR.parent))
    import protocol
    too_many = protocol.MAX_SLOTS + 1
    bench = Bench("--slots", str(too_many), language="it_IT.UTF-8")
    c = Client(INDI_PORT)
    try:
        bench.connect(c)
        c.pump(1.0)
        text = " ".join(c.messages)
        ok(f"dichiara {too_many} posizioni" in text
           and f"da {protocol.MIN_SLOTS} a {protocol.MAX_SLOTS}" in text,
           "the warning is translated and states the whole range", text[-300:])
    finally:
        c.close()
        bench.close()


def select_ready(fd, seconds):
    import select as _s
    return bool(_s.select([fd], [], [], seconds)[0])


def test_seven_position_wheel():
    print("a seven-position wheel")
    # It is the answer to the question "are a Wheelly5 and a Wheelly7 driver
    # needed?": no, because the wheel says how many positions it has and the
    # driver adapts. Separate drivers would force whoever installs to know it
    # in order to pick the right entry, and whoever gets it wrong ends up
    # with seven boxes on a five-position wheel.
    bench = Bench("--slots", "7")
    c = Client(INDI_PORT)
    try:
        result = bench.connect(c)
        ok(result == "Ok", "the driver connects to a different wheel", result)
        c.pump(2.0)

        slot = c.props["FILTER_SLOT"]["elements"]["FILTER_SLOT_VALUE"]
        ok(float(slot.get("max", 0)) == 7,
           "FILTER_SLOT goes up to seven, not to twelve nor to five",
           str(slot.get("max")))
        ok(float(slot.get("min", 0)) == 1, "and starts from one", str(slot.get("min")))

        ok(len(c.props["FILTER_NAME"]["elements"]) == 7,
           "there are seven filter names",
           str(len(c.props["FILTER_NAME"]["elements"])))
        ok(len(angle_rows(c)) == 7,
           "and seven calibration angles",
           str(angle_rows(c)))

        c.set_number("FILTER_SLOT", "FILTER_SLOT_VALUE", 7)
        result = c.wait_state("FILTER_SLOT", ("Ok", "Alert"), 25)
        ok(result == "Ok", "and the seventh position is reached", result)
    finally:
        c.close()
        bench.close()


def test_consistent_positions():
    print("the positions are the same in every panel")
    bench = Bench()
    c = Client(INDI_PORT)
    try:
        bench.connect(c)
        c.pump(2.0)
        # The inconsistency this test was born from: FILTER_SLOT went up to
        # twelve - the base class default, which had never been changed -
        # while the calibration panel showed five.
        expected = len(angle_rows(c))
        slot = c.props["FILTER_SLOT"]["elements"]["FILTER_SLOT_VALUE"]
        ok(float(slot.get("max", 0)) == expected,
           "the FILTER_SLOT maximum is the number of calibration angles",
           f"slot max={slot.get('max')}, angles={expected}")
        ok(len(c.props["FILTER_NAME"]["elements"]) == expected,
           "and there are as many filter names",
           str(len(c.props["FILTER_NAME"]["elements"])))
    finally:
        c.close()
        bench.close()


def main():
    if not DRIVER.exists():
        print(f"driver missing: {DRIVER}")
        return 2
    if not SIMULATOR.exists():
        print(f"simulator missing: {SIMULATOR}")
        return 2

    who = "the real firmware" if not IS_PYTHON else "the simulator"
    title = f"INDI driver integration bench, against {who}"
    print(f"\n{title}")
    print("=" * len(title) + "\n")

    # A test that blows up is still a failed test, and must not drag along
    # all those that came after it. It really happens: a driver sending a
    # byte that is not valid UTF-8 breaks the client's XML parser, which is
    # exactly what would happen to KStars.
    for test in (test_panels_and_language,
                 test_consistent_positions,
                 test_seven_position_wheel,
                 test_filter_change,
                 test_name_refused,
                 test_empty_slots,
                 test_sweep,
                 test_names_from_the_wheel_on_second_start,
                 test_slot_count_from_the_panel,
                 test_angle_set,
                 test_current_slot_marker,
                 test_live_row,
                 test_failure_stops_the_capture,
                 test_faulty_sensor,
                 test_flickering_magnet,
                 test_calibration,
                 test_settle_hold,
                 test_jog,
                 test_no_detent,
                 test_direction,
                 test_middle_band,
                 test_usb_unplugged,
                 test_motor_supply,
                 test_wrong_port,
                 test_wrong_device,
                 test_unknown_protocol,
                 test_too_many_positions):
        try:
            test()
        except Exception as trouble:
            failed.append(test.__name__)
            print(f"  CRASHED: {test.__name__} -> {trouble!r}")

    print("\n-------------------------------")
    print(f"{passed} passed, {len(failed)} failed\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
