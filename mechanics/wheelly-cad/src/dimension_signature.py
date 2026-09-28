# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""The dimension signature: every entity of the drawing says which parameter
it is born from.

The defect it solves is written out in full next to the tracker, in
`parameters.py`: the editor found a dimension in the drawing by looking for a
geometry worth that number, and 234 parameters out of 356 share their value
with another. Choosing the first match and taking it as good means pointing
at the wrong spot without saying so, on a page that is used with the
calipers in hand.

Here is the mechanism, in one place only because the drawings are generated
in THREE different modules - `drawings.py`, `drawing_dimensioned.py`,
`drawings_assembly.py` - and three copies drift apart at the first touch-up.
There are two ways of signing, and the difference is not a detail:

`Msp` serves whoever draws AT ONCE: it reads the tracker just before writing
the entity, so it signs on it the dimensions read since the previous entity
was written.

`MspFixedSignature` serves whoever draws LATER: the assembly views collect
the drawing in closures and write it all at the end, when the reads of the
parameters happened long before. There the signature is captured when the
closure is put aside, and applied when it is written.

In both cases what is recorded is a SUPERSET - some dimension read for
something else ends up in it too - and it must be used to NARROW the
candidates, never to invent them.
"""
import parameters

APPID = "WHEELLY"


def register(doc):
    """Declares the appid in the document: without it, XDATA cannot be written."""
    doc.appids.add(APPID)


def _sign(entity, dims):
    if dims and hasattr(entity, "set_xdata"):
        entity.set_xdata(APPID, [(1000, n) for n in sorted(dims)])
    return entity


class Msp:
    """Modelspace that signs each entity with the dimensions read to build it."""

    def __init__(self, msp, doc):
        object.__setattr__(self, "_msp", msp)
        register(doc)
        parameters.tracker_on()

    def __getattr__(self, name):
        real = getattr(self._msp, name)
        if not name.startswith("add_"):
            return real

        def write(*a, **k):
            # the tracker is read BEFORE calling: the arguments have already
            # been evaluated, so the parameter reads have already happened
            dims = parameters.read_and_reset_tracker()
            return _sign(real(*a, **k), dims)
        return write

    def __iter__(self):
        return iter(self._msp)


class MspFixedSignature:
    """Modelspace that signs with a signature decided from outside, one per
    group.

    Whoever emits sets `.dims` before running the closure that draws, and
    everything that closure writes carries that signature.
    """

    def __init__(self, msp, doc):
        object.__setattr__(self, "_msp", msp)
        object.__setattr__(self, "dims", ())
        register(doc)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)

    def __getattr__(self, name):
        real = getattr(self._msp, name)
        if not name.startswith("add_"):
            return real

        def write(*a, **k):
            return _sign(real(*a, **k), self.dims)
        return write

    def __iter__(self):
        return iter(self._msp)
