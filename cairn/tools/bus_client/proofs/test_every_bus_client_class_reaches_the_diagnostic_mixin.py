#!/usr/bin/env python3
"""Proof that every class with code in bus_client reaches DiagnosticBase, and loses nothing by it.

Measured 2026-11-06: 95c919b5f4aa's PROVED crossing was refused by build_inspector's
every_class_reaches_the_diagnostic_mixin; run directly over cairn/tools/bus_client the sieve
names exactly two classes, remote.RemoteBus and roster.DeviceRoster ('no route'). Ticket
819cbe3a9927 makes DiagnosticBase their base, as b13c53dd679c did for aider_shim.

Teeth, each importing the code under test at call time:
  (1) the sieve returns no findings for cairn/tools/bus_client;
  (2) behaviour unchanged: both are DiagnosticBase subclasses; RemoteBus keeps _home/_far,
      verbs() keys 'shim' for module:Class and 'device' otherwise, a RemoteBus at a far home
      nothing answers raises without starting anything; DeviceRoster.hold stays idempotent by
      device_id and held keeps the order held; remote.py's top-level imports are stdlib plus
      cairn.tools.base.diagnostic only;
  (3) every other bus_client proof, run as its own process, still exits 0 (where no
      CairnCommons sits beside the repo — hollow's worktree — a sibling that fails is named,
      not judged).

    PYTHONPATH=. python3 cairn/tools/bus_client/proofs/test_every_bus_client_class_reaches_the_diagnostic_mixin.py
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"819cbe3a9927": {
    "1": "test_no_bare_class_in_bus_client",
    "2": "test_behaviour_unchanged",
    "3": "test_behaviour_unchanged",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail[:1500]}" if detail else ""), flush=True)
    if not ok:
        FAILURES.append(name)


def test_no_bare_class_in_bus_client() -> None:
    from cairn.machines.build_inspector import inspector
    found = inspector.every_class_reaches_the_diagnostic_mixin(
        {"component": "cairn/tools/bus_client", "dir": "cairn/tools/bus_client"},
        _REPO / "cairn" / "tools" / "bus_client")
    check("test_no_bare_class_in_bus_client", found == [],
          f"{len(found)} finding(s): " + "; ".join(str(f.get("about")) for f in found))


_FAR_DRIVE = r"""
import json, os, sys
os.environ.pop("CAIRN_BUS_HOME", None)
from cairn.tools.bus_client.remote import RemoteBus
rb = RemoteBus("127.0.0.1:1")
out = {"home": rb._home, "far": list(rb._far) if rb._far else None}
sent = []
rb._call = lambda req: sent.append(req) or {"exit": 0}
rb.verbs("pkg.mod:Cls", ["list"]); rb.verbs("codemother", ["list"])
out["keys"] = [sorted(k for k in r if k not in ("op", "verbs")) for r in sent]
del rb._call
try:
    rb.stats()
    out["far_call"] = "answered"
except Exception as exc:
    out["far_call"] = type(exc).__name__
print(json.dumps(out))
"""


def _top_imports(path: Path) -> list[str]:
    mods = []
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Import):
            mods += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.append(node.module)
    return mods


def test_behaviour_unchanged() -> None:
    import json
    from cairn.tools.base.diagnostic import DiagnosticBase
    from cairn.tools.bus_client.remote import RemoteBus
    from cairn.tools.bus_client.roster import DeviceRoster

    lacks: list[str] = []
    for cls in (RemoteBus, DeviceRoster):
        if not issubclass(cls, DiagnosticBase):
            lacks.append(f"{cls.__name__} is not a DiagnosticBase")

    env = {**os.environ, "PYTHONPATH": str(_REPO)}
    r = subprocess.run([sys.executable, "-c", _FAR_DRIVE], cwd=str(_REPO), env=env,
                       capture_output=True, text=True, timeout=120)
    try:
        far = json.loads(r.stdout.strip().splitlines()[-1])
        if far["home"] != "127.0.0.1:1" or far["far"] != ["127.0.0.1", 1]:
            lacks.append(f"RemoteBus at a far home holds home={far['home']!r} far={far['far']!r}")
        if far["keys"] != [["shim"], ["device"]]:
            lacks.append(f"verbs() keys changed: {far['keys']}")
        if far["far_call"] in ("answered",):
            lacks.append("a far home nothing answers answered")
    except (ValueError, IndexError, KeyError) as exc:
        lacks.append(f"far-home drive failed ({exc}): rc={r.returncode} {r.stderr[-600:]}")

    class _S:
        def __init__(self, d):
            self.device_id = d

    roster = DeviceRoster(bus=None, root=_REPO / "cairn")
    a1, b, a2 = _S("alpha"), _S("beta"), _S("alpha")
    for s in (a1, b, a2):
        roster.hold(s)
    if roster.held != ["alpha", "beta"] or roster.shim_for("alpha") is not a1:
        lacks.append(f"DeviceRoster.hold is no longer idempotent in order: held={roster.held}")

    allowed = set(sys.stdlib_module_names) | {"__future__", "cairn.tools.base.diagnostic"}
    extra = [m for m in _top_imports(_REPO / "cairn" / "tools" / "bus_client" / "remote.py")
             if m.split(".")[0] not in allowed and m not in allowed]
    if extra:
        lacks.append(f"remote.py's top-level imports grew beyond stdlib + diagnostic: {extra}")

    unrun: list[str] = []
    if not lacks:
        commons_beside = (_REPO.parent / "CairnCommons").is_dir()
        here = Path(__file__).resolve()
        for proof in sorted(here.parent.glob("test_*.py")):
            if proof == here:
                continue
            run = subprocess.run([sys.executable, str(proof)], cwd=str(_REPO), env=env,
                                 capture_output=True, text=True, timeout=900)
            if run.returncode == 0:
                continue
            if not commons_beside:
                unrun.append(proof.name)
                continue
            tail = (run.stdout + run.stderr).strip().splitlines()[-4:]
            lacks.append(f"{proof.name} exited {run.returncode}: {' | '.join(tail)}")

    check("test_behaviour_unchanged", not lacks, "; ".join(lacks) or (
        f"not measured here, no CairnCommons beside {_REPO} (hollow's worktree): {unrun}" if unrun else ""))


def main() -> int:
    os.chdir(_REPO)
    print("819cbe3a9927 — every class with code in bus_client reaches the diagnostic mixin")
    for tooth in (test_no_bare_class_in_bus_client, test_behaviour_unchanged):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
