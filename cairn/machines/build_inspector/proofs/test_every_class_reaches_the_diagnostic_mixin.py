"""Proof of the every_class_reaches_the_diagnostic_mixin sieve (ticket 339a45cee6a1): every class
in cairn/ whose own body defines a function reaches DiagnosticBase through its bases.

Akien, 2026-10-27: "everybody must inherit it. that's why it's a mixin" / "any class with code it
in should be able to run a diagnostic report when we need it." The Probe ROOT is exempt and its
subclasses are judged ("determination isn't made at the rootmost level, but as each subclass
needs"); DiagnosticBase cannot inherit itself; proofs/ measure the system rather than run in it.

Named teeth, one per RED clause of the ticket's falsifier (D6), each building its own fixture tree
that mirrors the repo (<tmp>/cairn/tools/base/diagnostic.py defines DiagnosticBase), so resolution
is tested rather than assumed. The sieve is bound at call time (_Late), so a hollow revert of
inspector.py reads red tooth by tooth rather than dying at import.

    python3 cairn/machines/build_inspector/proofs/test_every_class_reaches_the_diagnostic_mixin.py   # exit 0 = green
"""
import ast
import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402  the fixture door; swept at exit


class _Late:
    """The build's names are resolved AT CALL TIME, never bound at import (see
    test_encapsulation_holds.py: a proof that dies at import prints no teeth, and hollow reads
    UNRAN rather than red)."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._module), name)

_inspector = _Late("cairn.machines.build_inspector.inspector")

# Coverage declaration read by cairn.tools.proof_coverage. The falsifier carries no clause
# markers, so its one clause is "all", held by the tooth that runs every narrow tooth end to end.
PROVES = {
    "339a45cee6a1": {"all": "the_sieve_holds_every_clause_of_the_falsifier"},
}

SIEVE = "every_class_reaches_the_diagnostic_mixin"

PASS = 0
FAIL = 0
_TMP: list[str] = []


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


_CHARTER = json.dumps({"what": "a fixture component", "why": "a fixture component"})

# The floor every fixture stands on: the mixin at its real module address.
_BASE = {
    "cairn/tools/base/intention+why.json": _CHARTER,
    "cairn/tools/base/diagnostic.py":
        "class DiagnosticBase:\n    def emit(self, gate):\n        return gate\n",
}


def _judge(component_dir: str, files: dict[str, str]) -> list[dict]:
    """Write a fixture repo and run the sieve over one of its components."""
    root = Path(str(scratch_dir("diagnostic_mixin_fixture_")))
    _TMP.append(str(root))
    for rel, text in {**_BASE, f"cairn/{component_dir}/intention+why.json": _CHARTER,
                      **files}.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    row = {"dir": component_dir, "component": Path(component_dir).name}
    return _inspector.every_class_reaches_the_diagnostic_mixin(row, root / "cairn" / component_dir)


def _red(found) -> list[tuple]:
    return sorted((f["values"]["cls"], f["values"]["reason"]) for f in found)


def a_class_with_a_def_and_no_bases_is_red():
    found = _judge("tools/t", {"cairn/tools/t/t.py":
                               "class A:\n    def go(self):\n        return 1\n\n\n"
                               "def outer():\n    class Inner:\n        def go(self):\n"
                               "            return 2\n    return Inner\n"})
    assert _red(found) == [("A", "no route"), ("Inner", "no route")], found
    a = next(f for f in found if f["values"]["cls"] == "A")
    assert a["method"] == SIEVE and a["component"] == "t", a
    assert a["values"]["file"] == "cairn/tools/t/t.py" and a["values"]["line"] == 1, a
    assert a["about"].startswith("cairn/tools/t/t.py:1 class A has code"), a["about"]


def a_direct_subclass_of_the_mixin_is_green():
    found = _judge("tools/t", {"cairn/tools/t/t.py":
                               "from cairn.tools.base.diagnostic import DiagnosticBase\n\n\n"
                               "class A(DiagnosticBase):\n    def go(self):\n        return 1\n\n\n"
                               "class B(DiagnosticBase):\n    @property\n    def p(self):\n"
                               "        return 1\n"})
    assert found == [], found


def a_chain_through_another_module_is_green():
    found = _judge("tools/t", {
        "cairn/tools/t/a.py": "from cairn.tools.base.diagnostic import DiagnosticBase as DB\n\n\n"
                              "class A(DB):\n    def go(self):\n        return 1\n",
        "cairn/tools/t/b.py": "from cairn.tools.t.a import A\nimport cairn.tools.t.a as amod\n\n\n"
                              "class B(A):\n    def go(self):\n        return 2\n\n\n"
                              "class C(amod.A):\n    def go(self):\n        return 3\n\n\n"
                              "class D(B):\n    async def go(self):\n        return 4\n",
    })
    assert found == [], found


def a_method_less_class_is_not_judged():
    found = _judge("tools/t", {"cairn/tools/t/t.py":
                               "class Plain:\n    \"\"\"Only a docstring.\"\"\"\n    x = 1\n"
                               "    y: int = 2\n"})
    assert found == [], found


def the_probe_root_is_exempt_and_its_subclasses_are_judged():
    found = _judge("tools/base", {"cairn/tools/base/probe.py":
                                  "class Probe:\n    def carry(self):\n        return 1\n\n\n"
                                  "class P2(Probe):\n    def carry(self):\n        return 2\n\n\n"
                                  "class P3:\n    x = 1\n"})
    # DiagnosticBase itself has a def and is not judged either (D4 member (a)).
    assert _red(found) == [("P2", "no route")], found


def an_unresolvable_base_is_red_with_its_reason():
    found = _judge("tools/t", {"cairn/tools/t/t.py":
                               "from cairn.tools.nowhere import *\n\n\n"
                               "class C(Missing):\n    def go(self):\n        return 1\n"})
    assert _red(found) == [("C", "unresolvable base: Missing")], found


def a_class_under_proofs_is_not_judged():
    found = _judge("tools/t", {"cairn/tools/t/proofs/x.py":
                               "class Fixture:\n    def go(self):\n        return 1\n",
                               "cairn/tools/t/t.py": "X = 1\n"})
    assert found == [], found


def an_outside_base_does_not_reach_but_the_mixin_beside_it_does():
    found = _judge("tools/t", {"cairn/tools/t/t.py":
                               "from abc import ABC\n"
                               "from cairn.tools.base.diagnostic import DiagnosticBase\n\n\n"
                               "class E(Exception):\n    def go(self):\n        return 1\n\n\n"
                               "class G(ABC):\n    def go(self):\n        return 1\n\n\n"
                               "class F(DiagnosticBase, Exception):\n    def go(self):\n"
                               "        return 1\n"})
    assert _red(found) == [("E", "no route"), ("G", "no route")], found


def _census() -> set[tuple[str, int]]:
    """An INDEPENDENT reading of the live tree: a global fixpoint over class NAMES, never over
    imports. A class reaches when any base's last dotted name is a class name that reaches,
    seeded at DiagnosticBase. It shares no code with the sieve, so agreement is evidence."""
    from cairn.tools.base.address import component_of
    classes: dict[str, list] = {}
    for p in sorted((_REPO_ROOT / "cairn").rglob("*.py")):
        rel = p.relative_to(_REPO_ROOT).as_posix()
        if "/proofs/" in rel or "__pycache__" in rel:
            continue
        for n in ast.walk(ast.parse(p.read_text())):
            if isinstance(n, ast.ClassDef):
                code = any(isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)) for b in n.body)
                bases = [ast.unparse(b).split(".")[-1] for b in n.bases]
                classes.setdefault(n.name, []).append((p, rel, n.lineno, bases, code))

    reach = {"DiagnosticBase"}
    grew = True
    while grew:
        grew = False
        for name, defs in classes.items():
            if name not in reach and any(set(b) & reach for _, _, _, b, _ in defs):
                reach.add(name)
                grew = True
    exempt = {("cairn/tools/base/diagnostic.py", "DiagnosticBase"),
              ("cairn/tools/base/probe.py", "Probe")}
    return {(rel, line) for name, defs in classes.items() for p, rel, line, bases, code in defs
            if code and (rel, name) not in exempt and component_of(p) is not None
            and not (set(bases) & reach)}


def the_live_findings_equal_an_independent_census():
    """Clause: live, on cairn/, the findings equal the census set — as an invariant, never a pinned
    count, so it holds at every commit while the sibling tickets drain the list."""
    from cairn.tools.orient.orient import device_census
    rows = device_census(root=_REPO_ROOT / "cairn")["measured"]["components"]
    found = []
    for row in rows:
        found += _inspector.every_class_reaches_the_diagnostic_mixin(
            row, _REPO_ROOT / "cairn" / row["dir"])
    for f in found:
        v = f["values"]
        assert f["about"].startswith(f"{v['file']}:{v['line']} class {v['cls']} "), f
    got = {(f["values"]["file"], f["values"]["line"]) for f in found}
    assert len(got) == len(found), "a class was judged twice (attribution is by deepest owner)"
    want = _census()
    assert got == want, {"sieve_only": sorted(got - want), "census_only": sorted(want - got)}
    print(f"        live: {len(got)} classes with code do not reach DiagnosticBase")


def the_sieve_is_registered():
    assert _inspector.SIEVES.get(SIEVE) is _inspector.every_class_reaches_the_diagnostic_mixin


NARROW = [
    a_class_with_a_def_and_no_bases_is_red,
    a_direct_subclass_of_the_mixin_is_green,
    a_chain_through_another_module_is_green,
    a_method_less_class_is_not_judged,
    the_probe_root_is_exempt_and_its_subclasses_are_judged,
    an_unresolvable_base_is_red_with_its_reason,
    a_class_under_proofs_is_not_judged,
    an_outside_base_does_not_reach_but_the_mixin_beside_it_does,
    the_live_findings_equal_an_independent_census,
    the_sieve_is_registered,
]


def the_sieve_holds_every_clause_of_the_falsifier():
    """The falsifier's one clause ("all"): every narrow tooth, end to end, in one reading."""
    for fn in NARROW:
        fn()


TEETH = NARROW + [the_sieve_holds_every_clause_of_the_falsifier]

if __name__ == "__main__":
    try:
        for fn in TEETH:
            _tooth(fn.__name__, fn)
    finally:
        for d in _TMP:
            shutil.rmtree(d, ignore_errors=True)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
