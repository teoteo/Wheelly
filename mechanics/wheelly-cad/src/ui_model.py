# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Model of the parameters for the editing interface.

Reads src/parameters.py, interprets the expressions in Fusion's syntax and
recomputes the derived values. It never writes to the source: the export
produces a text that the user saves when they want.

Some names stay Italian on purpose: the seven fields of a parameter (nome,
unita, espressione, valore, disegni, origine, descrizione - name, unit,
expression, value, drawings, origin, description) and the keys of
Parameter.as_dict() are the JSON the page's script (ui_static/index.html)
reads, and the attributes are read through those same strings.
"""
import ast, math, os, re

SRC = os.path.dirname(os.path.abspath(__file__))
PARAMETERS_FILE = os.path.join(SRC, "parameters.py")
OVERRIDES_FILE = os.path.join(SRC, "parameters_local.py")

FIELDS = ("nome", "unita", "espressione", "valore", "disegni", "origine", "descrizione")

# The only functions allowed: those that really appear in the expressions.
# In Fusion the angular arguments and results are in degrees.
FUNCTIONS = {
    "sqrt": math.sqrt,
    "atan": lambda x: math.degrees(math.atan(x)),
    # Like atan, it returns degrees: it serves the law of cosines, which is the
    # way to get an angle from the three sides of a triangle - for example the
    # half width of the clutch window from the clearance it must leave.
    "acos": lambda x: math.degrees(math.acos(x)),
    "sin":  lambda x: math.sin(math.radians(x)),
    "cos":  lambda x: math.cos(math.radians(x)),
    "tan":  lambda x: math.tan(math.radians(x)),
}

LITERAL = re.compile(r"^-?\d+(?:\.\d+)?(?:\s+(?:mm|deg))?$")
UNITS     = re.compile(r"\b(mm|deg)\b")
IDENT     = re.compile(r"[A-Za-z_]\w*")


class ExpressionError(Exception):
    pass


# The messages of ExpressionError are shown by the page as they are: they are
# still Italian, like the rest of what the page shows outside the catalogues
# (texts_editor), and move to the catalogues together with it.

def _in_python(expression):
    """Translates a Fusion expression into equivalent Python source."""
    e = UNITS.sub("", expression)      # the units are decorative: 50 mm -> 50
    e = e.replace("^", "**")
    return e.strip()


def dependencies(expression, known_names):
    """Parameter names cited by the expression, in order of appearance."""
    seen = []
    for t in IDENT.findall(UNITS.sub("", expression)):
        if t in known_names and t not in seen:
            seen.append(t)
    return seen


def evaluate(expression, values):
    """Numeric value of the expression, given the values of the other parameters."""
    source = _in_python(expression)
    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError as exc:
        raise ExpressionError("sintassi non valida: %s" % exc.msg)
    _check_tree(tree)
    env = dict(FUNCTIONS)
    env.update(values)
    try:
        result = eval(compile(tree, "<espressione>", "eval"),
                      {"__builtins__": {}}, env)
    except NameError as exc:
        raise ExpressionError(str(exc).replace("name", "nome").replace("is not defined", "non esiste"))
    except ZeroDivisionError:
        raise ExpressionError("divisione per zero")
    except ValueError as exc:
        raise ExpressionError("dominio non valido: %s" % exc)
    if not isinstance(result, (int, float)) or isinstance(result, bool):
        raise ExpressionError("il risultato non e' un numero")
    if result != result or result in (float("inf"), float("-inf")):
        raise ExpressionError("il risultato non e' finito")
    return float(result)


_ALLOWED_NODES = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name,
                  ast.Load, ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div,
                  ast.Pow, ast.USub, ast.UAdd)


def _check_tree(tree):
    """Allows only arithmetic and calls to the known functions: nothing else."""
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ExpressionError("costrutto non ammesso: %s" % type(node).__name__)
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
                raise ExpressionError("funzione non ammessa")
            if node.keywords or len(node.args) != 1:
                raise ExpressionError("le funzioni ammesse prendono un solo argomento")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise ExpressionError("costante non numerica")


# --------------------------------------------------------------------------
# Reading the source
# --------------------------------------------------------------------------

def _source_rows():
    """The list P of parameters.py, read as data (not executed)."""
    with open(PARAMETERS_FILE, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=PARAMETERS_FILE)
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "P"):
            return [ast.literal_eval(t) for t in node.value.elts]
    raise RuntimeError("in %s non trovo la lista P" % PARAMETERS_FILE)


def overrides_on_disk():
    """The local overrides already saved, read as data (not executed).

    Read as a syntax tree, so the comments do not matter: a file written by
    an older editor, with the Italian header and "# derivato: cambia solo il
    valore" beside the rows, reads exactly like one written by this one. The
    dictionary is taken under either of its two names - OVERRIDES, or the
    older SCOSTAMENTI - as parameters.py does.
    """
    if not os.path.exists(OVERRIDES_FILE):
        return {}
    with open(OVERRIDES_FILE, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=OVERRIDES_FILE)
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in ("OVERRIDES", "SCOSTAMENTI")):
            return ast.literal_eval(node.value)
    return {}


class Parameter(object):
    def __init__(self, row, sezione, index, base=None):
        self.nome, self.unita, self.espressione, self.valore = row[0], row[1], row[2], float(row[3])
        self.disegni, self.origine, self.descrizione = row[4], row[5], row[6]
        self.section = sezione
        self.index = index                      # original position, for the export
        # Two bases, and both are needed. `base` is what is written in
        # parameters.py; `_base` is the starting point of the session, that is
        # the base with the overrides already saved on top. Against the second
        # one says what has changed now, against the first what goes into the
        # overrides file - otherwise re-exporting would lose yesterday's.
        self.base_expression = row[2]
        self.base_value = float(row[3])
        self.file_expression, self.file_value = base or (row[2], float(row[3]))
        self.deps = []
        self.computed = None                     # value of the expression, if computable
        self.error = None

    @property
    def letterale(self):
        """Whether the expression is a plain number (a literal)."""
        return bool(LITERAL.match(self.espressione.strip()))

    @property
    def modificato(self):
        """Whether it has been modified in this session."""
        return (self.espressione != self.base_expression
                or abs(self.valore - self.base_value) > 1e-9)

    @property
    def overridden(self):
        """Whether it departs from parameters.py: it is what goes into the overrides."""
        return (self.espressione != self.file_expression
                or abs(self.valore - self.file_value) > 1e-9)

    def as_dict(self):
        d = {c: getattr(self, c) for c in FIELDS}
        # What the page shows goes in the editor's language; the English of
        # parameters.py stays on the object, because the links to the drawings
        # (ui_render.drawings_of) are read from it.
        import texts_editor
        d["descrizione"] = texts_editor.parameter_text(self.texts_key, "description",
                                                        self.descrizione)
        d["disegni"] = texts_editor.parameter_text(self.texts_key, "group",
                                                    self.disegni)
        # the keys are the page's (JSON): they stay as they are
        d.update(sezione=self.section, letterale=self.letterale,
                 modificato=self.modificato, deps=self.deps,
                 errore=self.error, calcolato=self.computed,
                 espressione_base=self.base_expression, valore_base=self.base_value,
                 usato_da=getattr(self, "usato_da", []),
                 disallineato=getattr(self, "disallineato", False))
        return d


class Model(object):
    """All the parameters, with the dependency graph and the recomputation."""

    TOLERANCE = 0.005        # the values in the file are rounded to 2 decimals

    def __init__(self):
        self.parameters = []
        self.sections = []
        sezione = ""
        overrides = overrides_on_disk()
        occurrences = {}
        for i, row in enumerate(_source_rows()):
            if len(row) == 1:
                sezione = row[0].strip("- ").strip()
                self.sections.append(sezione)
                continue
            base = (row[2], float(row[3]))
            if row[0] in overrides:
                expression, value = overrides[row[0]]
                row = (row[0], row[1], expression, float(value)) + tuple(row[4:])
            self.parameters.append(Parameter(row, sezione, i, base))
            # the key of its texts in the translation catalogue: the name, or
            # name#2 for the second row with the same name (texts_editor)
            occurrences[row[0]] = occurrences.get(row[0], 0) + 1
            self.parameters[-1].texts_key = (row[0] if occurrences[row[0]] == 1
                                             else "%s#%d" % (row[0], occurrences[row[0]]))
        self.by_name = {p.nome: p for p in self.parameters}
        self._graph()
        self.recompute()

    # -- graph ------------------------------------------------------------
    def _graph(self):
        names = set(self.by_name)
        for p in self.parameters:
            p.deps = dependencies(p.espressione, names)
        for p in self.parameters:
            p.usato_da = [q.nome for q in self.parameters if p.nome in q.deps]
        self.order = self._topological_order()

    def _topological_order(self):
        state, order = {}, []

        def visit(name, chain):
            if state.get(name) == "done":
                return
            if state.get(name) == "visiting":
                raise RuntimeError("dipendenza circolare: %s" % " -> ".join(chain + [name]))
            state[name] = "visiting"
            for d in self.by_name[name].deps:
                visit(d, chain + [name])
            state[name] = "done"
            order.append(name)

        for p in self.parameters:
            visit(p.nome, [])
        return order

    # -- recomputation ----------------------------------------------------
    def recompute(self):
        """Re-evaluates every expression in dependency order.

        A parameter with a formula expression takes the computed value: it is
        the definition of derived. One with a literal expression keeps the
        written value, and if the two diverge we flag it instead of
        overwriting it.
        """
        values = {}
        for name in self.order:
            p = self.by_name[name]
            p.error = None
            p.computed = None
            p.disallineato = False
            try:
                p.computed = evaluate(p.espressione, values)
            except ExpressionError as exc:
                p.error = str(exc)
            if p.error is None:
                if p.letterale:
                    p.disallineato = abs(p.computed - p.valore) > self.TOLERANCE
                else:
                    p.valore = round(p.computed, 2)
            values[name] = p.valore
        self.values_by_name = values
        return values

    # -- editing ----------------------------------------------------------
    def edit(self, name, expression):
        """Changes the expression of a parameter and recomputes everything.

        If the expression is not valid the change is undone, so the model
        never stays in a state it cannot evaluate.
        """
        p = self.by_name[name]
        previous = p.espressione
        p.espressione = expression.strip()
        try:
            p.deps = dependencies(p.espressione, set(self.by_name))
            self.order = self._topological_order()
        except RuntimeError as exc:
            p.espressione = previous
            p.deps = dependencies(previous, set(self.by_name))
            self.order = self._topological_order()
            raise ExpressionError(str(exc))
        values_before = dict(self.values_by_name)
        self.recompute()
        if p.error:
            errore = p.error
            p.espressione = previous
            self._graph()
            self.recompute()
            raise ExpressionError(errore)
        if p.letterale:
            p.valore = p.computed
            self.recompute()
        for q in self.parameters:
            q.usato_da = [r.nome for r in self.parameters if q.nome in r.deps]
        return [n for n, v in self.values_by_name.items()
                if abs(v - values_before.get(n, v)) > 1e-9 or n not in values_before]

    def reset(self):
        for p in self.parameters:
            p.espressione, p.valore = p.base_expression, p.base_value
        self._graph()
        self.recompute()


# --------------------------------------------------------------------------
# Export: parameters.py updated
# --------------------------------------------------------------------------

def _format_value(v):
    v = round(v, 2)
    return "%.1f" % v if abs(v - round(v)) < 1e-9 else ("%.2f" % v).rstrip("0")


def _tuple_positions():
    """For every parameter, the stretches of text holding expression and value.

    Uses the exact positions the AST knows, instead of looking for the text
    with regular expressions: so there is no way of hitting the wrong line.
    """
    with open(PARAMETERS_FILE, encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines(keepends=True)
    start = [0]
    for r in lines[:-1]:
        start.append(start[-1] + len(r))

    def span(node):
        return (start[node.lineno - 1] + node.col_offset,
                start[node.end_lineno - 1] + node.end_col_offset)

    positions = {}
    tree = ast.parse(text, filename=PARAMETERS_FILE)
    for node in tree.body:
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "P"):
            for t in node.value.elts:
                if len(t.elts) > 1:
                    positions[ast.literal_eval(t.elts[0])] = (span(t.elts[2]), span(t.elts[3]))
    return text, positions


def updated_source(model):
    """The text of parameters.py with everything that comes out of it inside, and nothing else.

    It touches only expression and value of the parameters that depart from
    the file: the rest stays identical byte for byte. It serves the sandbox,
    which needs a complete parameters.py to run - and it must contain the
    overrides already saved too, not only the changes of this session,
    otherwise the preview would regenerate with the base values.
    """
    text, positions = _tuple_positions()
    changes = []
    for p in model.parameters:
        if not p.overridden:
            continue
        (e0, e1), (v0, v1) = positions[p.nome]
        changes.append((e0, e1, _repr_string(p.espressione)))
        changes.append((v0, v1, _format_value(p.valore)))
    for a, b, new in sorted(changes, reverse=True):
        text = text[:a] + new + text[b:]
    return text


def _repr_string(s):
    return '"%s"' % s if '"' not in s else "'%s'" % s


# The header of parameters_local.py, in English, and the same words as the
# file kept in the repository, so that saving from the
# editor does not rewrite the header for nothing. A file written with the old
# Italian header is still read (overrides_on_disk() reads the dictionary, not
# the comments).
OVERRIDES_HEADER = '''# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: CERN-OHL-P-2.0

"""Local overrides of the base parameters.

Generated by the editor. It is saved next to parameters.py, which loads it on
its own: what is written here wins over the base. To go back to the starting
design it is enough to delete this file.

Each entry is name: (expression, value). There are also the derived
parameters that changed value without changing expression, because
parameters.py holds the values already computed and cannot redo the sums on
its own.
"""
'''


def local_overrides(model):
    """The text of parameters_local.py: only what departs from the base.

    Not only the changes of this session: everything that differs from
    parameters.py, overrides already saved included. Otherwise re-exporting
    would erase the earlier work.
    """
    out = sorted((p for p in model.parameters if p.overridden),
                 key=lambda p: p.index)
    lines = [OVERRIDES_HEADER, "OVERRIDES = {"]
    if not out:
        lines.append("    # no overrides: the design is the base one")
    sezione = None
    for p in out:
        if p.section != sezione:
            sezione = p.section
            lines.append("    # --- %s ---" % sezione)
        lines.append('    "%s": (%s, %s),%s'
                     % (p.nome, _repr_string(p.espressione),
                        _format_value(p.valore),
                        "" if p.espressione != p.file_expression
                        else "   # derived: only the value changes"))
    lines.append("}")
    return "\n".join(lines) + "\n"
