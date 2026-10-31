#!/usr/bin/env python3
"""Proof that the harbor's proven-space rule follows the ticket's kind at BUILDME (ticket 56280fc01410).

Outline 19.14.8 (Akien, 2026-10-31: "for new/changed code tickets the rule is x, for fixit
tickets the rule is y"). Until this build rule 2 of ``clear()`` demanded a sealed-green,
fingerprint-current proof on EVERY crossing, BUILDME included, so a new code-seam's red-first
proof could never be the proof its own BUILDME named (the retreat-and-recross detour, 668c and
e8b5), and a fixit could never name the red it fixes at all.

WHY THE TEETH ARE THESE. The rule is read off the ticket, so it stays deterministic; each tooth
is one clause of 19.14.8.1-3 and a hollow build fails at least one:
  (1) x: a code-seam at BUILDME clears onto an unsealed proof that exists and whose PROVES names
      the ticket;
  (2) x refuses: a missing proof, or one whose PROVES does not name the ticket;
  (3) y: a bug at BUILDME clears onto the proof its ``fixes`` names while that proof's seal is
      really red;
  (4) y refuses (19.14.8.3, a ticket cannot call itself a fixit to get y): a ``fixes`` proof never
      sealed, or sealed green and gone stale, or a red proof the ticket does not name in ``fixes``;
  (5) every crossing other than BUILDME is unchanged: PROVEME onto a not-proven proof is still
      refused for both kinds;
  (6) the gate reads the ticket's kind where it lives: the owner read off a real split ticket
      carries the state file's ``node_class``.

The read of proven-space (``clearance.standing``) and of the owner (``clearance.boat_owner_of``)
are substituted at call time, the established pattern in test_clearance.py, so this measures the
rule and nothing else (RULE 1).

    bin/cairn test cairn/devices/cairn/machines/harbor_master/proofs/test_the_proven_space_rule_follows_the_ticket_kind.py
"""
from __future__ import annotations

import importlib
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

_TID = "56280fc01410"
PROVES = {
    "56280fc01410": {
        "1": "test_a_code_seam_clears_buildme_onto_its_own_red_first_proof",
        "2": "test_a_code_seam_proof_that_does_not_name_the_ticket_is_refused",
        "3": "test_a_fixit_clears_buildme_onto_the_red_it_fixes",
        "4": "test_a_ticket_cannot_call_itself_a_fixit_to_get_y",
        "5": "test_every_other_crossing_still_demands_proven_space",
        "6": "test_the_owner_read_carries_the_state_files_kind",
    },
}

_WF = "code-seam@v2: THINKME -> [TICKETME] -> BUILDME -> PROVEME -> PROVED"
_BUG_WF = "bug@v1: THINKME -> [TICKETME] -> BUILDME -> PROVEME -> PROVED"
_ACTOR = "cc"
_BOAT = "kindrule000a"
_SCRATCH = Path(scratch_dir("proven-space-kind-"))


def _c():
    return importlib.import_module("cairn.devices.cairn.machines.harbor_master.clearance")


def _proof(name: str, proves: dict | None) -> str:
    """A proof file at ``<scratch>/<name>/proofs/test_<name>.py`` declaring ``proves``."""
    d = _SCRATCH / name / "proofs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"test_{name}.py"
    p.write_text((f"PROVES = {proves!r}\n" if proves is not None else "") + "raise SystemExit(1)\n",
                 encoding="utf-8")
    return str(p)


def _read(kind: str) -> dict:
    """One standing() outcome: never sealed, sealed red, sealed green but stale."""
    seal = {"none": None, "red": {"verdict": "red", "date": "2026-10-31"},
            "stale": {"verdict": "green", "date": "2026-10-31"}}[kind]
    return {"proven": False, "seal": seal, "why": f"fixture read: {kind}"}


@contextmanager
def _world(node_class: str, reads: dict, **ticket):
    """Substitute the owner read and the proven-space read; restore both after."""
    c = _c()
    owner = c.BoatOwner(intention="thing/intention+why.json", hands=(_ACTOR,),
                        ticket={"id": _BOAT, "node_class": node_class, **ticket})
    real_owner, real_standing = c.boat_owner_of, c.standing
    c.boat_owner_of = lambda *a, **k: owner
    c.standing = lambda p: reads.get(str(p), _read("none"))
    try:
        yield c
    finally:
        c.boat_owner_of, c.standing = real_owner, real_standing


def _cross(c, wf: str, target: str, proven_by):
    """Ask the gate; return the refusal, or None when it cleared."""
    with tempfile.TemporaryDirectory() as tmp:
        try:
            c.clear(wf, target, actor=_ACTOR, boat_id=_BOAT, proven_by=proven_by,
                    history_path=str(Path(tmp) / "history.json"),
                    state_path=str(Path(tmp) / "state.json"))
        except Exception as exc:  # noqa: BLE001 — the refusal IS the measurement here
            return exc
    return None


def test_a_code_seam_clears_buildme_onto_its_own_red_first_proof():
    p = _proof("xnamed", {_TID: {"all": "t"}, _BOAT: {"all": "t"}})
    with _world("code-seam", {p: _read("none")}) as c:
        got = _cross(c, _WF, "BUILDME", p)
    assert got is None, f"x: an unsealed proof naming the ticket must clear BUILDME, got {got!r}"
    with _world("code-seam", {p: _read("red")}) as c:
        got = _cross(c, _WF, "BUILDME", p)
    assert got is None, f"x: a red proof naming the ticket must clear BUILDME, got {got!r}"


def test_a_code_seam_proof_that_does_not_name_the_ticket_is_refused():
    other = _proof("xother", {"someoneelse0": {"all": "t"}})
    bare = _proof("xbare", None)
    missing = str(_SCRATCH / "xmissing" / "proofs" / "test_xmissing.py")
    for label, p in (("names another ticket", other), ("declares nothing", bare),
                     ("does not exist", missing)):
        with _world("code-seam", {p: _read("none")}) as c:
            got = _cross(c, _WF, "BUILDME", p)
        assert isinstance(got, c.Unproven), f"x must refuse a proof that {label}, got {got!r}"


def test_a_fixit_clears_buildme_onto_the_red_it_fixes():
    p = _proof("yfixes", {"sometheroth0": {"all": "t"}})
    with _world("bug", {p: _read("red")}, fixes=[p]) as c:
        got = _cross(c, _BUG_WF, "BUILDME", p)
    assert got is None, f"y: the red a fixit names in fixes must clear BUILDME, got {got!r}"


def test_a_ticket_cannot_call_itself_a_fixit_to_get_y():
    p = _proof("yliar", {"sometheroth0": {"all": "t"}})
    cases = (("its fixes proof was never sealed", {p: _read("none")}, [p]),
             ("its fixes proof is green gone stale, not red", {p: _read("stale")}, [p]),
             ("the red proof is not in its fixes", {p: _read("red")}, []))
    for label, reads, fixes in cases:
        with _world("bug", reads, fixes=fixes) as c:
            got = _cross(c, _BUG_WF, "BUILDME", p)
        assert isinstance(got, c.Unproven), f"y must refuse when {label}, got {got!r}"


def test_every_other_crossing_still_demands_proven_space():
    p = _proof("other", {_BOAT: {"all": "t"}})
    at_build = "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED"
    bug_at_build = "bug@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED"
    with _world("code-seam", {p: _read("red")}) as c:
        got = _cross(c, at_build, "PROVEME", p)
    assert isinstance(got, c.Unproven), f"x must not reach past BUILDME, got {got!r}"
    with _world("bug", {p: _read("red")}, fixes=[p]) as c:
        got = _cross(c, bug_at_build, "PROVEME", p)
    assert isinstance(got, c.Unproven), f"y must not reach past BUILDME, got {got!r}"


def test_the_owner_read_carries_the_state_files_kind():
    from cairn.tools.base import ticket_file
    tickets = _REPO_ROOT.parent / "CairnCommons" / "tickets"
    plan = next(p for p in sorted(tickets.glob(f"{_TID}-*.json"))
                if not p.name.endswith(".state.json"))
    want = ticket_file.read_ticket(plan).get("node_class")
    got = (_c().boat_owner_of(_TID).ticket or {}).get("node_class")
    assert want and got == want, f"the owner read carries node_class {got!r}; the ticket says {want!r}"


def main() -> int:
    failed = 0
    for name in PROVES[_TID].values():
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            failed += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print("GREEN" if not failed else f"RED ({failed} failed)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
