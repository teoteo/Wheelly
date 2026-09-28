# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Local server of the editing interface.

It keeps a single model in memory: the changes live as long as the session
lasts and are taken out with the export. No file of the project is written.

The routes (/api/stato, /api/modifica...), the JSON keys and the few messages
it sends are the page's (ui_static/index.html): they stay Italian until the
page moves to English with them.
"""
import difflib, http.server, json, mimetypes, os, socketserver, threading, urllib.parse

import ui_build, ui_model, ui_dimensions, ui_render

SRC     = os.path.dirname(os.path.abspath(__file__))
ROOT    = os.path.dirname(SRC)
STATIC = os.path.join(SRC, "ui_static")


class Session(object):
    """Model, sandbox and last outcome of the checks, under a single lock."""

    def __init__(self):
        self.lock = threading.Lock()
        self.model = ui_model.Model()
        self.sandbox = ui_build.Sandbox()
        self.outcome = self.sandbox.regenerate(ui_model.updated_source(self.model))
        self.reference = {c["nome"]: c["margine"] for c in self.outcome.get("controlli", [])}
        # The CAD files have a sandbox of their own: a long regeneration must
        # not block the preview of the drawings, nor be overwritten by it.
        self.sandbox_cad = ui_build.Sandbox()
        self.job = None
        self.cad_parameters = []

    def start_cad(self):
        """Launches the complete regeneration in a thread, if not already running."""
        if self.job is not None and self.job.state == "in corso":
            return self.job
        with self.lock:
            source = ui_model.updated_source(self.model)
            self.cad_parameters = [q.nome for q in self.model.parameters if q.modificato]
        self.job = ui_build.CadJob()
        threading.Thread(target=self._generate, args=(source, self.job),
                         daemon=True).start()
        return self.job

    def _generate(self, source, job):
        """Generates, and saves into out/ when there is nothing to ask.

        The double step is needed only when the result is debatable: if the
        parameters are those on disk and all the checks pass, the files just
        made are exactly those build.py would produce, and keeping them in a
        temporary folder protects from nothing.
        """
        ui_build.regenerate_cad(self.sandbox_cad, source, job)
        if job.state != "finito" or self.cad_parameters:
            return
        if [c for c in job.checks + job.audit if not c["passa"]]:
            return
        try:
            brought, removed = ui_build.publish(self.sandbox_cad,
                                                os.path.join(ROOT, "out"))
            job.saved = {"file": brought, "rimossi": removed}
        except OSError as exc:
            job.saved = {"errore": str(exc)}

    def cad_state(self):
        if self.job is None:
            return {"stato": "mai", "passi": [], "controlli": [], "audit": [],
                    "falliti": [], "file": [], "durata": 0.0, "errore": None,
                    "parametri": []}
        d = self.job.snapshot()
        d["parametri"] = self.cad_parameters
        return d

    def regenerate(self):
        self.outcome = self.sandbox.regenerate(ui_model.updated_source(self.model))
        return self.outcome

    def state(self):
        p = [q.as_dict() for q in self.model.parameters]
        # the links come from the English label of parameters.py, not from the
        # translated one the page shows: drawings_of matches English words
        for q, par in zip(p, self.model.parameters):
            q["disegni_collegati"] = ui_render.drawings_of(par.disegni)
        return {"sezioni": self.model.sections,
                "parametri": p,
                "esito": self.outcome,
                "riferimento": self.reference,
                "modificati": [q.nome for q in self.model.parameters if q.modificato]}


SESSION = None


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "Wheelly-UI"

    def log_message(self, *a):
        pass                                     # no noise on the terminal

    # -- utilities --------------------------------------------------------
    def _send(self, body, ctype="application/json; charset=utf-8", code=200):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    # -- routes -----------------------------------------------------------
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(route.query)

        if route.path in ("/", "/index.html"):
            return self._static("index.html")
        if route.path.startswith("/static/"):
            return self._static(os.path.basename(route.path))

        if route.path == "/api/testi":
            # the texts of the page, in the language the server runs in
            import texts_editor
            return self._send({k: v for k, v in
                               texts_editor.CATALOGUES[texts_editor.language()].items()
                               if not k.startswith(("plan.", "sec.", "det."))})

        if route.path == "/api/cad":
            return self._send(SESSION.cad_state())

        if route.path == "/api/stato":
            with SESSION.lock:
                return self._send(SESSION.state())

        if route.path == "/api/dove":
            # In which linked drawings the dimension is really found: the page
            # needs it to open the right tab instead of the first of the list.
            name = (q.get("q") or [""])[0]
            with SESSION.lock:
                p = SESSION.model.by_name.get(name)
                if p is None:
                    return self._send({"disegni": []})
                listing = ui_render.drawings_of(p.disegni) + ui_render.ASSEMBLY
                found = []
                for n in listing:
                    path = SESSION.sandbox.dxf(n)
                    if not path:
                        continue
                    r = ui_dimensions.matches(p.valore, ui_dimensions.features(path),
                                              name=p.nome)
                    if r:
                        found.append({"disegno": n, "riscontri": len(r),
                                      "tipo": r[0][0],
                                      "firmato": ui_dimensions.signed(r, p.nome)})
            # First those in which the dimension is recognised, then those in
            # which it is guessed: the page opens the first, and opening a
            # drawing where the value comes back at two hundred points means
            # showing chance.
            found.sort(key=lambda t: (t["firmato"] == 0, t["riscontri"]))
            return self._send({"disegni": found})

        if route.path == "/api/svg":
            name = (q.get("n") or [""])[0]
            if name not in ui_build.DRAWINGS:
                return self._send({"errore": "disegno sconosciuto"}, code=404)
            with SESSION.lock:
                path = SESSION.sandbox.dxf(name)
                if not path:
                    return self._send({"errore": "non generato"}, code=404)
                # `q` is the parameter being edited: if there is one, its
                # dimension is traced on the drawing.
                chosen = (q.get("q") or [""])[0]
                p = SESSION.model.by_name.get(chosen)
                dim = None if p is None else {"nome": p.nome, "valore": p.valore,
                                              "unita": p.unita, "origine": p.origine}
                return self._send(ui_render.to_svg(path, dim),
                                  "image/svg+xml; charset=utf-8")

        if route.path == "/api/export":
            # Not the whole of parameters.py: only what departs from it. The
            # file comes out as parameters_local.py and the base stays intact.
            with SESSION.lock:
                text = ui_model.local_overrides(SESSION.model)
            return self._send(text, "text/plain; charset=utf-8")

        if route.path == "/api/diff":
            with SESSION.lock:
                new = ui_model.local_overrides(SESSION.model)
            old = ""
            if os.path.exists(ui_model.OVERRIDES_FILE):
                old = open(ui_model.OVERRIDES_FILE, encoding="utf-8").read()
            d = difflib.unified_diff(old.splitlines(), new.splitlines(),
                                     "parameters_local.py (sul disco)",
                                     "parameters_local.py (da salvare)",
                                     lineterm="", n=1)
            return self._send("\n".join(d) or "Nessuna modifica.", "text/plain; charset=utf-8")

        return self._send({"errore": "rotta sconosciuta"}, code=404)

    def do_POST(self):
        route = urllib.parse.urlparse(self.path)

        if route.path == "/api/modifica":
            data = self._body()
            with SESSION.lock:
                try:
                    cambiati = SESSION.model.edit(data["nome"], str(data["espressione"]))
                except (ui_model.ExpressionError, KeyError) as exc:
                    return self._send({"ok": False, "errore": str(exc)}, code=200)
                SESSION.regenerate()
                state = SESSION.state()
            # (cambiati - "changed" - is a key of the page's JSON: it stays)
            state.update(ok=True, cambiati=cambiati)
            return self._send(state)

        if route.path == "/api/cad":
            SESSION.start_cad()
            return self._send(SESSION.cad_state())

        if route.path == "/api/pubblica":
            if SESSION.job is None or SESSION.job.state != "finito":
                return self._send({"ok": False, "errore": "nessun CAD da portare in out/"})
            brought, removed = ui_build.publish(SESSION.sandbox_cad,
                                                os.path.join(ROOT, "out"))
            return self._send({"ok": True, "file": brought, "rimossi": removed,
                               "destinazione": os.path.join(ROOT, "out")})

        if route.path == "/api/azzera":
            with SESSION.lock:
                SESSION.model.reset()
                SESSION.regenerate()
                state = SESSION.state()
            state.update(ok=True, cambiati=[])
            return self._send(state)

        return self._send({"errore": "rotta sconosciuta"}, code=404)

    def _static(self, name):
        path = os.path.join(STATIC, name)
        if not os.path.isfile(path):
            return self._send({"errore": "non trovato"}, code=404)
        ctype = mimetypes.guess_type(path)[0] or "text/plain"
        with open(path, "rb") as f:
            self._send(f.read(), ctype + "; charset=utf-8")


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_server(port=8760):
    global SESSION
    SESSION = Session()
    srv = Server(("127.0.0.1", port), Handler)
    return srv, SESSION
