"""Proof: the SEAM between the harbor's lines and the real host device's may-I door.

``test_clearance.py`` proves the fourth refusal against ``_ResourceOwner``, a stand-in built
to catch a gate reaching past a verdict. That fake answers ``ask`` for ANY name — which is
exactly what it must do to test the gate's logic, and exactly why it cannot test the seam.
A harbor holding a line the system device does not serve passes every check in that file.

This stone puts the REAL ``SystemRackmountDevice`` behind ``clear(resources=...)``. Teeth a
hollow build could not pass:

  - THE MENU IS THE CONTRACT: every name in ``HARBOR_LINES`` is a probe the real device
    ADVERTISES, and advertises on the ``ask`` door specifically. The harbor owns its lines and
    the device owns its metrics (Law 6) — and the one thing they must agree on is the name.
    A line the device never heard of raises ``KeyError`` out of a gate whose whole job is to
    answer yes or no, so the seam is checked here rather than discovered at an admission.
  - THE DEVICE'S OWN PREDICATE DRIVES THE REFUSAL: the fourth refusal fires from
    ``_resolve``/``_over``/``_under`` on real host data (a sampler, injected — the physics is
    the device's, only the reading is fixtured), not from a bool a test handed over.
  - BOTH DIRECTIONS: ``cpu_threshold`` crosses going UP, ``memory_floor`` crosses going DOWN.
    A build that ran every line as a threshold clears a box with plenty of CPU and no memory
    left, and dies on the second tooth here.
  - THE VERDICT CARRIES NO READING (Law 6): the refusal names the harbor's own LINE and never
    the device's number. The reading stays home even in the error text — a record of truth
    that leaked it would export the metric's semantics into the harbor forever.
  - NON-VACUITY: a quiet box CLEARS and the crossing is recorded. Without this the three
    refusal teeth above would all pass on a build that refused everything.

WHAT THIS DOES NOT PROVE, and the reason is worth carrying: nothing in the running system
calls ``clear()`` at all. Measured 2026-08-05 — 229 records across 21 component histories,
146 of them emit-shaped, and ZERO carrying ``cleared_by``. So this proves the harbor CAN ask
the real host and be refused by it; it does not prove any crossing is gated. That gap is a
ticket, not a caveat to be read past.

Runs bare (no daemon, no bus, no instance — ``ask`` is a plain method on the device):
    python3 cairn/harbor_master/proofs/test_harbor_asks_the_real_host.py     # exit 0 = green
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.charter import projector
from cairn.harbor_master.clearance import HARBOR_LINES, Unresourced, clear
from cairn.harbor_master.registry import MethodRegistry
from cairn.system_rackmount.rackmount import SystemRackmountDevice

_WF = "code-seam@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED"
_OWNER = "akiendelllinux_cc_0"
_BOAT = "some-code-seam"

_GREEN_FIXTURE = _REPO_ROOT / "cairn" / "tester" / "proofs" / "fixtures" / "green_proof.py"

# Fixtured host readings. The SAMPLER is injected, never the verdict: everything between this
# dict and the gate's yes/no is the device's real code. Distinctive digits so the leak tooth
# below can look for them by sight.
_QUIET = {"cpu": 12.3, "memory_available_mb": 7654.3}
_CPU_PRESSED = {"cpu": 93.7, "memory_available_mb": 7654.3}
_MEMORY_SPENT = {"cpu": 12.3, "memory_available_mb": 511.9}


def _proven_registry():
    reg = MethodRegistry()
    reg.register("build", method=lambda: "built", proof_path=_GREEN_FIXTURE)
    return reg


def _host(reading: dict) -> SystemRackmountDevice:
    """The REAL device, its sampler fixtured. Not a stand-in: `ask`, `_resolve`, `_over` and
    `_under` are all the shipped code."""
    return SystemRackmountDevice(sampler=lambda: dict(reading))


def _paths(tmp: str):
    return str(Path(tmp) / "history.json"), str(Path(tmp) / "state.json")


def test_every_harbor_line_is_a_probe_the_device_advertises_on_the_ask_door():
    # THE SEAM. The harbor holds the lines; the device holds the metrics; the NAME is the only
    # thing they share, and nothing until now checked that they share it. A fake answers any
    # name, so this tooth is invisible to test_clearance.py by construction.
    device = _host(_QUIET)
    menu = {entry["probe"]: entry for entry in device.advertises()}
    for name in HARBOR_LINES:
        assert name in menu, (
            f"the harbor holds a line {name!r} that system_rackmount does not advertise — the "
            f"device offers {sorted(menu)}. At an admission this is a KeyError out of a gate "
            f"whose only job is to answer yes or no"
        )
        assert "ask" in menu[name]["doors"], (
            f"{name!r} is advertised but not on the ASK door ({menu[name]['doors']}) — the "
            f"harbor pulls a verdict, it does not subscribe to a poke"
        )


def test_the_real_device_refuses_a_move_when_cpu_pressure_crosses_the_harbors_line():
    # The fourth refusal, end to end through the shipped predicate: owner acting directly, proven
    # method, legal target — and the host says no.
    reg = _proven_registry()
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_OWNER, boat_id=_BOAT, boat_owner=_OWNER,
                method="build", registry=reg, resources=_host(_CPU_PRESSED),
                history_path=hp, state_path=sp,
            )
        except Unresourced as exc:
            assert not Path(hp).exists(), "a move refused for want of room writes no record"
            assert "cpu_threshold" in str(exc), "the refusal must name the line that was crossed"
            return
        raise AssertionError(
            "93.7% of cores runnable is over the harbor's 75.0 line — the real device must "
            "refuse the move"
        )


def test_the_memory_floor_crosses_the_other_way_and_is_its_own_refusal():
    # DIRECTION. A build that ran every line as "reading >= value" sees 511.9 < 1024.0, calls it
    # uncrossed, and admits a builder onto a box with half a gig left. It passes the tooth above.
    reg = _proven_registry()
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_OWNER, boat_id=_BOAT, boat_owner=_OWNER,
                method="build", registry=reg, resources=_host(_MEMORY_SPENT),
                history_path=hp, state_path=sp,
            )
        except Unresourced as exc:
            assert "memory_floor" in str(exc), (
                f"the crossed line is the memory floor, not the cpu threshold (cpu is quiet at "
                f"{_MEMORY_SPENT['cpu']}%) — the refusal said: {exc}"
            )
            assert not Path(hp).exists(), "a move refused for want of room writes no record"
            return
        raise AssertionError(
            "511.9 MB available is BELOW the harbor's 1024.0 floor — a floor crosses going "
            "down, and the move must be refused"
        )


def test_the_refusal_names_the_line_and_never_the_reading():
    # Law 6 in the error text. The harbor's own line (75.0) is its to publish; the device's
    # reading (93.7) is not, and a refusal that carried it would put the metric's semantics
    # into the harbor's records permanently (Law 7 — records of truth do not get edited).
    reg = _proven_registry()
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_OWNER, boat_id=_BOAT, boat_owner=_OWNER,
                method="build", registry=reg, resources=_host(_CPU_PRESSED),
                history_path=hp, state_path=sp,
            )
        except Unresourced as exc:
            text = str(exc)
            for reading in (_CPU_PRESSED["cpu"], _CPU_PRESSED["memory_available_mb"]):
                assert str(reading) not in text, (
                    f"the refusal leaked the device's reading ({reading}) — the gate receives a "
                    f"VERDICT and never a number, and that has to hold in the message too: {text}"
                )
            assert str(HARBOR_LINES["cpu_threshold"]) in text, (
                "the refusal must carry the harbor's OWN line, so the asker learns what it was "
                "held to without ever learning the host's reading"
            )
            return
        raise AssertionError("expected the pressed box to refuse")


def test_a_quiet_box_clears_the_move_and_the_crossing_is_recorded():
    # NON-VACUITY. Three refusal teeth above all pass on a build that refuses everything; this
    # is the one that says the gate is a gate and not a wall.
    reg = _proven_registry()
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        new = clear(
            _WF, "PROVEME",
            actor=_OWNER, boat_id=_BOAT, boat_owner=_OWNER,
            method="build", registry=reg, resources=_host(_QUIET),
            history_path=hp, state_path=sp,
        )
        assert "[PROVEME]" in new, "12.3% CPU and 7.6 GB free is room — the move must clear"
        history = projector.read_history(hp)
        assert len(history) == 1 and history[0]["to"] == "PROVEME"
        assert history[0]["cleared_by"] == _OWNER, "the record names WHO cleared it (Law 7)"


def _main() -> int:
    checks = [
        test_every_harbor_line_is_a_probe_the_device_advertises_on_the_ask_door,
        test_the_real_device_refuses_a_move_when_cpu_pressure_crosses_the_harbors_line,
        test_the_memory_floor_crosses_the_other_way_and_is_its_own_refusal,
        test_the_refusal_names_the_line_and_never_the_reading,
        test_a_quiet_box_clears_the_move_and_the_crossing_is_recorded,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the harbor's lines are names the real system device serves on its ask door, "
          "and the device's own predicates refuse a move in both directions without ever "
          "handing over a reading. The gate CAN ask the real host; nothing yet makes a crossing "
          "go through it (0 of 229 journaled records carry cleared_by).")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
