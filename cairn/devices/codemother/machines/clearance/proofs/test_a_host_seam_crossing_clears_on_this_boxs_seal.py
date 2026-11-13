#!/usr/bin/env python3
"""Proof for ticket b5d439fd6608: a host-seam crossing clears on this box's verify seal.

Measured 2026-11-13 (the orchestrator, on 496dcbeba174 and b1f182b6b818): a no-target cross of
a host-seam ticket refused "the crossing names no proof at all", because ``gate.declaring()``
finds proofs only by a ``PROVES`` table and a host-seam's proof is its intention's verify,
sealed box-local by the tester (dfe6c1432fc8). The gate now names the ticket's owning
intention, and rule 2b takes that intention's box-local standing as the coverage.

Every tooth stands a SCRATCH world: a commons holding one fixture host-seam intention, the
owner read (``boat_owner_of``) and the crossing world (``_crossing_roots``) substituted, as
test_the_proven_space_rule_follows_the_ticket_kind.py does. The seal is taken by the REAL
``bin/cairn test --host-seam ... --seal`` (the tester's door, RULE 1) and read by the REAL ``standing()``. Clearance
and the gate are bound at call time, never at import.

    bin/cairn test cairn/devices/codemother/machines/clearance/proofs/test_a_host_seam_crossing_clears_on_this_boxs_seal.py
"""
from __future__ import annotations

import contextlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "b5d439fd6608": {
        "1": "test_the_gate_names_a_host_seams_owning_intention",
        "2": "test_a_host_seam_crossing_clears_only_after_this_box_seals",
        "3": "test_a_moved_host_fact_refuses_the_crossing_again",
    },
}

_BOAT = "b5d4f1x70001"   # a scratch ticket id: never a real ticket's
_ACTOR = "cc"
_OWNING = "intentions-not-beside-code/host-testing-b5d439fd6608.json"
_HS_WF = "host-seam@v1: THINKME -> TICKETME -> RESEARCHME -> [POCME] -> PROVEME -> PROVED"
_HS_AT_PROVEME = "host-seam@v1: THINKME -> TICKETME -> RESEARCHME -> POCME -> [PROVEME] -> PROVED"
_CS_WF = "code-seam@v2: THINKME -> [TICKETME] -> BUILDME -> PROVEME -> PROVED"


def _live_commons() -> Path:
    beside = _REPO_ROOT.parent / "CairnCommons"
    return beside if beside.is_dir() else Path.home() / "dev" / "src" / "CairnCommons"


def _world() -> dict:
    """A scratch repo + commons holding one fixture host-seam intention."""
    from cairn.tools.scratch.scratch import scratch_dir
    base = Path(scratch_dir("b5d4-host-seam-crossing-"))
    repo, commons = base / "repo", base / "commons"
    (repo).mkdir()
    (commons / "tickets").mkdir(parents=True)
    seam = commons / _OWNING
    seam.parent.mkdir(parents=True)
    seam.write_text(json.dumps({
        "id": "host-testing-b5d439fd6608", "node_class": "host-seam",
        "intention": "testing-b5d439fd6608 a fixture host-seam",
        "verify": {"command": "true", "green": "testing-b5d439fd6608 exit 0",
                   "horizon": "testing-b5d439fd6608 after an OS upgrade"}}, indent=1),
        encoding="utf-8")
    return {"repo": str(repo), "commons": str(commons), "seam": seam}


class _Ticket:
    def __init__(self, workflow: str):
        self.id, self.workflow, self.fileref = _BOAT, workflow, f"tickets/{_BOAT}.json"

    def doc(self) -> dict:
        return {"id": _BOAT, "owning_intention": _OWNING, "workflow_and_state": self.workflow}


def _seal(seam: Path) -> None:
    """Seal through the tester's door, ``bin/cairn test`` — never its module (RULE 1)."""
    from cairn.tools.base.script_argv import bash_script_argv
    argv = bash_script_argv(_REPO_ROOT / "bin" / "cairn") + ["test", "--host-seam", str(seam), "--seal"]
    r = subprocess.run(argv, cwd=str(_REPO_ROOT), stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, f"fixture: the host-seam seal ran {r.returncode}:\n{r.stdout}{r.stderr}"


@contextlib.contextmanager
def _clearance(w: dict):
    """Substitute the owner read, the crossing world and the class table; restore all three."""
    c = importlib.import_module("cairn.devices.codemother.machines.clearance.clearance")
    t = importlib.import_module("cairn.tools.base.transitions")
    owner = c.BoatOwner(intention=_OWNING, hands=(_ACTOR,),
                        ticket={"id": _BOAT, "node_class": "host-seam",
                                "owning_intention": _OWNING,
                                "falsifier": {"clauses": [{"n": 1, "claim": "the verify is green"}]}})
    roots = {"repo": w["repo"], "commons": w["commons"]}
    was = c.boat_owner_of, c._crossing_roots, t.load_class_def
    real_load = t.load_class_def
    c.boat_owner_of = lambda *a, **k: owner
    c._crossing_roots = lambda: roots
    t.load_class_def = lambda name, *, root=None: real_load(
        name, root=root if root is not None and Path(root).is_dir() else _live_commons() / "node_classes")
    try:
        yield c
    finally:
        c.boat_owner_of, c._crossing_roots, t.load_class_def = was


def _cross(c, proven_by) -> Exception | None:
    """Ask the gate to PROVED; the refusal, or None. Unjournaled: no history_path."""
    try:
        c.clear(_HS_AT_PROVEME, "PROVED", actor=_ACTOR, boat_id=_BOAT, proven_by=proven_by)
    except Exception as exc:  # noqa: BLE001 — the refusal IS the measurement
        print(f"       refused: {type(exc).__name__}: {str(exc)[:240]}")
        return exc
    print("       cleared")
    return None


def test_the_gate_names_a_host_seams_owning_intention():
    from cairn.devices.codemother.machines.clearance.gate import ClearanceGate
    w = _world()
    gate = ClearanceGate(roots={"repo": w["repo"], "commons": w["commons"]})
    hs = gate.crossing_of(_Ticket(_HS_WF))
    print(f"       host-seam proven_by: {hs['proven_by']}")
    assert hs["proven_by"] == [str(w["seam"])], (
        f"the host-seam crossing does not name its owning intention: {hs['proven_by']}")
    cs = gate.crossing_of(_Ticket(_CS_WF))
    assert cs["proven_by"] == gate.proven_by(_BOAT, cs["target"]), (
        f"a code-seam crossing's proven_by moved: {cs['proven_by']}")


def test_a_host_seam_crossing_clears_only_after_this_box_seals():
    w = _world()
    seam = str(w["seam"])
    with _clearance(w) as c:
        before = _cross(c, [seam])
        assert isinstance(before, c.Unproven), f"an unsealed host-seam was not refused: {before!r}"
        _seal(w["seam"])
        after = _cross(c, [seam])
    assert after is None, f"a host-seam sealed green on this box was refused: {after!r}"


def test_a_moved_host_fact_refuses_the_crossing_again():
    from cairn.tools.validation_store import validation_store as vs
    w = _world()
    _seal(w["seam"])
    real = vs.host_facts
    moved = {**real(), "kernel": "testing-b5d439fd6608-kernel"}
    vs.host_facts = lambda: moved
    try:
        with _clearance(w) as c:
            got = _cross(c, [str(w["seam"])])
    finally:
        vs.host_facts = real
    assert got is not None, "a host whose kernel moved still cleared"
    assert "kernel" in str(got), f"the refusal does not name the fact that moved: {got}"


if __name__ == "__main__":
    reds = 0
    for name, fn in [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]:
        try:
            fn()
            print(f"  ok   {name}")
        except BaseException as exc:  # noqa: BLE001 — each tooth's failure is said, verbatim
            reds += 1
            print(f"  RED  {name}: {type(exc).__name__}: {exc}")
    print("\nGREEN" if not reds else f"\nRED ({reds})")
    sys.exit(1 if reds else 0)
