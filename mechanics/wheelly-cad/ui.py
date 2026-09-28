#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""
Wheelly - parameter editing interface
=====================================

Opens the parameter editor in the browser: an expression is changed, the
derived values are recomputed, the drawings are redone and the dimension
chains say at once what is affected.

    python3 ui.py             starts on port 8760
    python3 ui.py --port N    uses another port
    python3 ui.py --no-open   does not open the browser

The Italian flags of before (--porta, --no-apri) still work.

The changes stay in memory: the export gives the parameters_local.py to save
beside src/parameters.py. Nothing is written on its own.
"""
import os, sys, threading, webbrowser

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))


# The flags are English; the older Italian ones stay as
# aliases, because the READMEs, the working notes and the published assembly
# guide (the page on the parameters) quote them.
FLAG_ALIASES = {"--porta": "--port", "--no-apri": "--no-open"}


def main():
    sys.argv[1:] = [FLAG_ALIASES.get(a, a) for a in sys.argv[1:]]
    port = 8760
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])

    try:
        import ezdxf                                    # noqa: F401
    except ImportError:
        sys.exit("ezdxf is missing.  Install it with:  pip install ezdxf")

    import ui_server
    print("\nWheelly - editing interface")
    print("  reading the parameters and generating the starting drawings...", end="", flush=True)
    try:
        srv, session = ui_server.start_server(port)
    except OSError as exc:
        sys.exit("\nCannot open port %d: %s" % (port, exc))

    failed = len(session.outcome.get("falliti", []))
    print("\r  %d parameters, %d drawings, %d checks%s" % (
        len(session.model.parameters),
        len(session.outcome.get("disegni", [])),
        len(session.outcome.get("controlli", [])),
        "" if not failed else "  (%d do not pass)" % failed))

    address = "http://127.0.0.1:%d/" % port
    print("\n  %s\n  Ctrl-C to close.\n" % address)
    if "--no-open" not in sys.argv:
        threading.Timer(0.4, lambda: webbrowser.open(address)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("  closing.\n")
    finally:
        session.sandbox.close()
        session.sandbox_cad.close()
        srv.server_close()


if __name__ == "__main__":
    main()
