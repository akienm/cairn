"""threshold_census — which probes say what set the number behind their ``enough``
(ticket 336a781018ba, a-probes-enough-threshold-declares-what-set-it).

THE MEASUREMENT THAT BORE IT. At the cast (2026-09-09) 55 ``_ENOUGH*`` constants stood across
47 probe files, and 34 of those files did not even carry the comment naming the number as a
guess; re-measured 2026-11-12, 69 across 58, with 103 of 105 probe modules carrying an
``enough=``. A number typed into a predicate cannot be asked which ticket or observation set
it, so nothing can ever move it against evidence (I-learns-its-gates). ``Threshold`` in
``cairn.tools.base.probe`` makes the number sayable; this census makes an unsaid one COUNTABLE,
which is the input the confidence engine needs and the number the WATCHME probe holds at 0.

IMPORTLESS, ON PURPOSE. The census reads each probe's SOURCE with ``ast`` and never imports
it: a probe module that imports runs its module body, and a gate that runs what it measures
has stopped measuring (the build_inspector sieve and the WATCHME probe both call this). It
imports nothing from any device (tools/base imports no device, RULE 1).

WHAT COUNTS AS DECLARED. A probe module's ``Probe(`` call carries ``enough=`` (anything but a
literal ``None``) AND ``thresholds=`` as a tuple holding at least one ``Threshold(`` whose
``of`` and ``set_by`` are non-blank string literals. A ``set_by`` that is a variable cannot be
read from source and counts as silent: provenance the gate cannot see is provenance nobody can
audit. A module that does not parse counts as silent and carries its error (Law 7). A guess
that says it is a guess — ``"guess by CC <date>, no ticket, no observation"`` — is declared:
the census counts BLANK provenance, never guessed provenance (the ticket's D3).

TWO BANDS. ``probes/`` is the live band; ``probes_disabled/`` is counted BESIDE it, never
folded in (D8): re-enabling a probe carries its threshold back in with it. ``proofs/`` is
outside the census — a proof's fixture probes are planted to be silent.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

PROBE_FOLDERS = ("probes", "probes_disabled")

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SKIP_PARTS = {"proofs", "__pycache__", "node_modules"}


def _skipped(parts: tuple) -> bool:
    return any(p in _SKIP_PARTS or p.startswith(".") for p in parts)


def probe_files(root: Path) -> list[Path]:
    """Every probe module under ``root``. ``root`` may be a repo (every ``probes/`` and
    ``probes_disabled/`` folder beneath it, outside proofs and dot-dirs) or one probe folder
    itself (its own modules: the sieve's per-component call)."""
    root = Path(root)
    if root.name in PROBE_FOLDERS:
        return sorted(p for p in root.glob("*.py") if p.name != "__init__.py")
    out = []
    for p in root.rglob("*.py"):
        if p.name == "__init__.py" or p.parent.name not in PROBE_FOLDERS:
            continue
        if _skipped(p.relative_to(root).parts[:-1]):
            continue
        out.append(p)
    return sorted(out)


def _call_name(node: ast.AST) -> str:
    f = node.func if isinstance(node, ast.Call) else None
    return getattr(f, "id", None) or getattr(f, "attr", None) or ""


def _literal_str(node) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return ast.unparse(node)
    return None


def _threshold(call: ast.Call) -> dict:
    """One ``Threshold(value, of, set_by)`` read from source: positional or keyword."""
    args = {k.arg: k.value for k in call.keywords if k.arg}
    for name, node in zip(("value", "of", "set_by"), call.args):
        args.setdefault(name, node)
    of, set_by = _literal_str(args.get("of")), _literal_str(args.get("set_by"))
    return {"value": ast.unparse(args["value"]) if "value" in args else None,
            "of": of, "set_by": set_by,
            "declared": bool(of and of.strip() and set_by and set_by.strip())}


def read_probe(path: Path, *, disabled: bool = False) -> dict:
    """One probe module: does its ``enough`` carry a declared threshold?"""
    row = {"path": str(path), "disabled": disabled, "has_enough": False,
           "thresholds": [], "provenance_less": False, "why": "", "error": None}
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError) as e:
        row.update(provenance_less=True, error=f"{type(e).__name__}: {e}",
                   why="the module does not parse, so its threshold cannot be read")
        return row
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and _call_name(n) == "Probe"]
    enough_calls = []
    for c in calls:
        kw = {k.arg: k.value for k in c.keywords if k.arg}
        e = kw.get("enough")
        if e is not None and not (isinstance(e, ast.Constant) and e.value is None):
            enough_calls.append(kw)
    if not enough_calls:
        return row
    row["has_enough"] = True
    silent = []
    for kw in enough_calls:
        th = kw.get("thresholds")
        if th is None:
            silent.append("enough= carries no thresholds=")
            continue
        items = th.elts if isinstance(th, ast.Tuple) else []
        ts = [_threshold(t) for t in items if isinstance(t, ast.Call) and _call_name(t) == "Threshold"]
        row["thresholds"].extend(ts)
        if not any(t["declared"] for t in ts):
            silent.append("thresholds= holds no Threshold with a non-blank of and set_by")
    if silent:
        row.update(provenance_less=True, why="; ".join(silent))
    return row


def census(root: Path | None = None) -> dict:
    """Both bands over ``root`` (default: this repo). Counts the live band in
    total/with_enough/provenance_less and the disabled band beside it (D18)."""
    root = _REPO_ROOT if root is None else Path(root)
    probes = []
    for p in probe_files(root):
        r = read_probe(p, disabled=p.parent.name == "probes_disabled")
        r["path"] = p.relative_to(root).as_posix() if root.name not in PROBE_FOLDERS \
            else f"{root.name}/{p.name}"
        probes.append(r)
    live = [r for r in probes if not r["disabled"]]
    off = [r for r in probes if r["disabled"]]
    return {
        "root": str(root),
        "total": len(live),
        "with_enough": sum(1 for r in live if r["has_enough"]),
        "provenance_less": sum(1 for r in live if r["provenance_less"]),
        "provenance_less_paths": [r["path"] for r in live if r["provenance_less"]],
        "disabled_total": len(off),
        "disabled_provenance_less": sum(1 for r in off if r["provenance_less"]),
        "disabled_provenance_less_paths": [r["path"] for r in off if r["provenance_less"]],
        "probes": probes,
    }


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    c = census(Path(argv[0]) if argv else None)
    print(f"{c['total']} probes, {c['with_enough']} with enough, {c['provenance_less']} "
          f"provenance-less; disabled band: {c['disabled_total']} probes, "
          f"{c['disabled_provenance_less']} provenance-less")
    for p in c["provenance_less_paths"] + c["disabled_provenance_less_paths"]:
        print("  silent:", p)
    return 1 if c["provenance_less"] or c["disabled_provenance_less"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
