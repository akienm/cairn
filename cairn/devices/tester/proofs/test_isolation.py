"""Proof for the tester's owned network — the measured seal (cairn/devices/tester/isolation.py).

The stone's claim: a run the tester supervises can be stripped of its route to a
constrained resource, and the seal is MEASURED from inside, never assumed. Teeth a
hollow build could not pass:

  - THE HOLLOW-SEAL KILLER (deterministic). An isolation that CLAIMS to seal
    (``seals_network = True``) but whose ``wrap`` does not actually remove the route
    must be caught: the measurement returns BREACHED, not SEALED. A sandbox that says
    "sealed" while handing out live sockets is the exact defect the tester exists to
    kill (Law 8). We prove the four seal verdicts by feeding the probe scripted
    outcomes — no network needed, so the tooth bites everywhere.
  - THE LIVE PHYSICS (measured here, honest when it can't be). On a host that can build
    the namespace, ``NetnsIsolation`` really does turn an off-host route into
    "no route" — asserted live. On a host that cannot, the verdict is INDETERMINATE and
    we say so loudly (CP1), rather than fake a pass; only an actual BREACH on a
    seal-capable host reds.
  - NO SCHEMA DRIFT. Folding the seal into a VALIDATION keeps the record at exactly the
    ratified eight fields — the seal rides inside ``method`` + ``evidence``.

Runnable bare:
    python3 cairn/devices/tester/proofs/test_isolation.py     # exit 0 = green
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester import isolation as _iso_mod
from cairn.devices.tester.device import GREEN, VALIDATION_FIELDS, TesterDevice
from cairn.devices.tester.isolation import (
    BREACHED,
    INDETERMINATE,
    OPEN,
    SEALED,
    Isolation,
    NetnsIsolation,
    NoIsolation,
    Seal,
    bwrap_available,
    check_instance_seal,
    get_isolation,
    pristine_snapshot,
    pristine_stats,
    snapshot_instance_space,
)
from cairn.devices.tester.scratch import scratch_dir

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_GREEN_FIXTURE = _FIXTURES / "green_proof.py"


class _Scripted(Isolation):
    """A seal-claiming isolation whose probe outcomes we dictate — lets us prove the
    verdict logic (including the hollow-seal case) without touching the network."""

    name = "scripted"
    seals_network = True

    def __init__(self, control: str, inside: str) -> None:
        self._control = control
        self._inside = inside

    def wrap(self, argv, cwd):
        return ["WRAPPED", *argv]

    def _run_probe(self, argv, cwd):
        # Return the "inside" outcome for a wrapped probe, the baseline otherwise.
        return self._inside if argv and argv[0] == "WRAPPED" else self._control


def test_no_isolation_is_honestly_open():
    iso = NoIsolation()
    assert iso.wrap(["echo", "hi"], ".") == ["echo", "hi"], "no isolation must not alter the argv"
    seal = iso.check_seal(".")
    assert seal.verdict == OPEN
    assert seal.sealed is False
    assert seal.trustworthy is True, "a deliberately-named OPEN is an honest state, not a failure"


def test_the_four_seal_verdicts_are_measured_not_assumed():
    # SEALED: baseline route, none inside → the seal removed it.
    assert _Scripted("ROUTE", "NOROUTE").check_seal(".").verdict == SEALED
    # BREACHED — THE HOLLOW-SEAL KILLER: claims to seal, route still there inside.
    assert _Scripted("ROUTE", "ROUTE").check_seal(".").verdict == BREACHED
    # INDETERMINATE: no baseline route to compare against — CP1, cannot prove anything.
    assert _Scripted("NOROUTE", "NOROUTE").check_seal(".").verdict == INDETERMINATE
    # INDETERMINATE: the inside probe gave an ambiguous answer (timeout/errno) — no guess.
    assert _Scripted("ROUTE", "ERR:110").check_seal(".").verdict == INDETERMINATE


def test_only_sealed_and_open_are_trustworthy():
    assert Seal(SEALED, "").trustworthy is True
    assert Seal(OPEN, "").trustworthy is True
    assert Seal(INDETERMINATE, "").trustworthy is False
    assert Seal(BREACHED, "").trustworthy is False, "a breached seal must never earn trust"


def test_unknown_isolation_is_refused():
    try:
        get_isolation("bogus")
    except ValueError:
        return
    raise AssertionError("get_isolation must refuse an unknown isolation name")


def test_netns_really_seals_on_this_host():
    # Live physics: measured, and honest when the host cannot build the namespace.
    iso = NetnsIsolation()
    ok, why = iso.available()
    if not ok:
        print(f"  INDETERMINATE  netns unavailable here: {why} (CP1 — not faking a pass)")
        return
    seal = iso.check_seal(str(_FIXTURES))
    print(f"  LIVE SEAL  {seal.verdict}: {seal.detail}")
    assert seal.verdict != BREACHED, f"bwrap is present but the seal did not hold: {seal.detail}"
    # SEALED is the expected live result; INDETERMINATE (e.g. this box is offline) is
    # honest, not a failure of the code. Only a BREACH on a seal-capable host is a red.
    assert seal.verdict in (SEALED, INDETERMINATE)


def test_run_proof_records_the_seal_without_schema_drift():
    t = TesterDevice()
    v = t.run_proof(_GREEN_FIXTURE, sink="none", isolation="none")
    assert set(v) == set(VALIDATION_FIELDS), f"seal must ride inside the 8 fields, got {sorted(v)}"
    assert v["evidence"]["seal"]["verdict"] == OPEN
    assert "unsealed" in v["method"]
    assert v["verdict"] == GREEN


def test_run_proof_under_netns_when_available():
    iso = NetnsIsolation()
    ok, _ = iso.available()
    if not ok:
        print("  skipped netns run_proof: namespace unavailable here (honest, not faked)")
        return
    v = TesterDevice().run_proof(_GREEN_FIXTURE, sink="none", isolation="netns")
    assert set(v) == set(VALIDATION_FIELDS)
    seal_verdict = v["evidence"]["seal"]["verdict"]
    print(f"  run_proof netns  proof={v['verdict']}  seal={seal_verdict}")
    assert seal_verdict != BREACHED, "a green proof under a broken seal must not pass silently"
    # The proof itself passes inside the seal (a seal removes the network, not the fixture).
    assert v["verdict"] == GREEN
    if seal_verdict == SEALED:
        assert "seal=sealed" in v["method"]


def test_the_seal_does_not_depend_on_how_the_path_is_spelled():
    # REGRESSION (2026-07-24). The netns seal runs the subject under `bwrap --chdir
    # <proof.parent>`; a RELATIVE parent resolves against the namespace root (/), not the
    # host cwd, so a relative-path call silently broke the chdir — failing the proof (false
    # RED) and downgrading the seal to INDETERMINATE. run_proof now resolve()s the path, so
    # the measured seal must be identical whether the caller spells the path relative or
    # absolute (Law 4: the guarantee is physics, not a "pass an absolute path" convention).
    iso = NetnsIsolation()
    ok, _ = iso.available()
    if not ok:
        print("  skipped path-spelling regression: netns unavailable here (honest, not faked)")
        return
    t = TesterDevice()
    absolute = t.run_proof(_GREEN_FIXTURE, sink="none", isolation="netns")
    rel = os.path.relpath(_GREEN_FIXTURE, os.getcwd())
    assert not os.path.isabs(rel), "the regression needs a genuinely relative spelling"
    relative = t.run_proof(rel, sink="none", isolation="netns")
    print(f"  abs seal={absolute['evidence']['seal']['verdict']}  rel seal={relative['evidence']['seal']['verdict']}")
    assert relative["verdict"] == absolute["verdict"] == GREEN, "a relative path must not fail the proof"
    assert relative["evidence"]["seal"]["verdict"] == absolute["evidence"]["seal"]["verdict"], (
        "the seal verdict must not depend on how the caller spelled the path"
    )
    assert relative["evidence"]["seal"]["verdict"] == SEALED, "on a netns host both spellings must SEAL"


# ── THE COST OF THE SEAL (ticket 1c4ae8f053fe) ───────────────────────────────
#
# MEASURED 2026-09-06 and 2026-09-08: every sealed run copied the live instance root TWICE
# (424M on disk, 4.6s apiece), so ~850M and ~9s per proof before a single tooth ran, and a
# 93-proof re-seal sweep moved ~79G to prove code that had not changed. Three changes, each
# with its own tooth below: the trail tree is not copied (73% of the bytes, and nothing
# reads its contents in a sandbox), the live root is read ONCE per process rather than once
# per proof, and the probe stops needing a whole second copy to write one marker into.
#
# THE FIXTURE ROOT IS THE POINT OF THE FIRST FOUR. They drive `_INSTANCE_ROOT` at a tree
# this proof built, so what is asserted is the RULE (logs empty, everything else carried,
# one read per batch, honest invalidation) rather than a fact about this laptop's ~/.cairn
# on the day it ran. The live root is where the last two teeth belong, because the cost and
# the marker are properties of a real run.


def _fixture_root() -> Path:
    """An instance root that looks like the real one: a fat trail tree, real device state,
    and a venv whose contents must be skipped by PEP 405 rather than by name."""
    root = scratch_dir("cairn-snapshot-cost-proof-") / "cairn"
    (root / "logs" / "bus" / "0").mkdir(parents=True)
    for i in range(40):
        (root / "logs" / "bus" / "0" / f"{i}.jsonl").write_text("x" * 512)
    (root / "devices" / "tester" / "0").mkdir(parents=True)
    (root / "devices" / "tester" / "0" / "state.json").write_text('{"kept": true}')
    (root / "venv").mkdir()
    (root / "venv" / "pyvenv.cfg").write_text("home = /usr/bin\n")
    (root / "venv" / "lib").mkdir()
    (root / "venv" / "lib" / "big.so").write_text("y" * 4096)
    return root


class _FixtureRoot:
    """Point the module's snapshot machinery at a fixture tree, and put it back after."""

    def __init__(self, root: Path) -> None:
        self._root = str(root)

    def __enter__(self) -> str:
        self._saved_root = _iso_mod._INSTANCE_ROOT
        self._saved_pristine = dict(_iso_mod._pristine)
        _iso_mod._INSTANCE_ROOT = self._root
        _iso_mod._pristine.update({"dir": None, "top": None, "builds": 0, "reuses": 0})
        return self._root

    def __exit__(self, *exc) -> None:
        _iso_mod._drop_pristine()
        _iso_mod._INSTANCE_ROOT = self._saved_root
        _iso_mod._pristine.update(self._saved_pristine)


def _entries(root) -> set:
    return {str(q.relative_to(root)) for q in Path(root).rglob("*")}


def _drop(*copies) -> None:
    """Sweep the private copies these teeth made by hand. ``run_proof`` sweeps its own in a
    finally; a tooth calling ``snapshot_instance_space`` directly has no such door, and a
    proof that leaks temp directories is the defect ``scratch.py`` was written for."""
    for c in copies:
        shutil.rmtree(Path(c).parent, ignore_errors=True)


def test_the_snapshot_leaves_the_trail_tree_empty_and_present():
    # The trail tree is 73% of what the old snapshot copied and no proof reads its CONTENTS
    # inside a sandbox — but the DIRECTORY has to survive, because check_instance_seal
    # refuses a swap that cannot show every live top-level name. Empty is not the same as
    # gone, and this tooth is the difference.
    with _FixtureRoot(_fixture_root()) as root:
        live_logs = list((Path(root) / "logs").rglob("*"))
        assert len(live_logs) > 40, (
            f"the fixture's trail tree is not fat enough to be worth skipping ({len(live_logs)} "
            f"entries) — this tooth would pass for the wrong reason")
        snap = Path(pristine_snapshot())
        assert (snap / "logs").is_dir(), "the logs DIRECTORY must survive — a missing top-level name turns every later seal INDETERMINATE"
        assert list((snap / "logs").iterdir()) == [], f"the logs tree must arrive empty; got {list((snap / 'logs').iterdir())[:5]}"
        assert (snap / "devices" / "tester" / "0" / "state.json").read_text() == '{"kept": true}', (
            "everything that is NOT the trail tree must still be carried across byte for byte")
        assert (snap / "venv").is_dir() and list((snap / "venv").iterdir()) == [], (
            "a venv is still skipped by pyvenv.cfg and still leaves its mount point")


def test_a_batch_reads_the_live_root_once():
    # The falsifier's second clause: "a batch of N proofs copies the instance root once".
    # N here is 4 private copies; the live tree may be walked exactly once for all of them.
    with _FixtureRoot(_fixture_root()):
        copies = [snapshot_instance_space() for _ in range(4)]
        stats = pristine_stats()
        assert stats["builds"] == 1, f"a batch of 4 read the live root {stats['builds']} times, not once"
        assert stats["builds"] + stats["reuses"] == 4, (
            f"every copy must be accounted for as a build or a reuse; 4 copies gave {stats}")
        shapes = [_entries(c) for c in copies]
        assert all(sh == shapes[0] for sh in shapes), "every private copy must carry the same world"
        assert len(shapes[0]) > 3, f"the copies are near-empty ({len(shapes[0])} entries) — a cheap copy of nothing is not the claim"
        _drop(*copies)


def test_a_private_copy_is_private():
    # Copying FROM the pristine instead of from the live tree may not make two proofs share a
    # world. This is the tooth that would catch a hardlink "optimisation" — the obvious next
    # cheap idea, and the one that would silently let proof A see proof B's writes.
    with _FixtureRoot(_fixture_root()):
        a, b = snapshot_instance_space(), snapshot_instance_space()
        pristine = Path(pristine_snapshot())
        (Path(a) / "devices" / "tester" / "0" / "state.json").write_text('{"kept": "MUTATED"}')
        assert (Path(b) / "devices" / "tester" / "0" / "state.json").read_text() == '{"kept": true}', (
            "a write in one proof's world reached another's")
        assert (pristine / "devices" / "tester" / "0" / "state.json").read_text() == '{"kept": true}', (
            "a write in a proof's world reached the pristine every later proof is copied from")
        _drop(a, b)


def test_the_pristine_is_rebuilt_when_the_top_level_moves():
    # The cache's honesty clause. A batch runs while daemons write, and a NEW TOP-LEVEL entry
    # is the one movement a stale pristine cannot survive: check_instance_seal refuses a swap
    # that cannot show every live top-level name, so the whole rest of the batch would read
    # INDETERMINATE. It must fail toward a fresh copy, never toward a wrong one.
    with _FixtureRoot(_fixture_root()) as root:
        pristine_snapshot()
        assert pristine_stats()["builds"] == 1
        pristine_snapshot()
        assert pristine_stats()["builds"] == 1, "an unchanged root must not be re-read"
        (Path(root) / "a_new_device_appeared").mkdir()
        snap = Path(pristine_snapshot())
        assert pristine_stats()["builds"] == 2, "a new top-level entry must rebuild the pristine"
        assert (snap / "a_new_device_appeared").is_dir(), "and the rebuild must actually carry it"


def test_the_seal_evidence_carries_what_it_cost():
    # The falsifier's first clause, read off the record rather than off a docstring — and
    # bounded on BOTH sides, because "under 150MB" is also true of a swap that copied
    # nothing, which would be a hollow green wearing the number we wanted.
    rec = TesterDevice().run_proof(_GREEN_FIXTURE, sink="none")
    cost = rec["evidence"]["instance_seal"]["scratch"]
    assert cost["measured"] is True, f"a sealed run must report what its sandbox cost: {cost}"
    print(f"  scratch: {cost['disk_bytes'] / 1e6:.1f}MB disk, {cost['entries']} entries, "
          f"live root read {cost['builds']}x this process")
    assert cost["disk_bytes"] < 150_000_000, (
        f"the per-proof sandbox is {cost['disk_bytes'] / 1e6:.0f}MB — ticket 1c4ae8f053fe's "
        f"falsifier is under 150MB (it was ~850MB across two copies before 2026-09-08)")
    assert cost["entries"] > 500 and cost["disk_bytes"] > 1_000_000, (
        f"the sandbox is nearly empty ({cost['entries']} entries, {cost['disk_bytes']} bytes) — "
        f"reads are not the defect this seal is for, and a cheap copy of nothing is not the win")
    assert cost["builds"] >= 1, "the cost record must carry the batch's own read count"


def test_the_probe_removes_its_own_exhaust():
    # THE WHOLE REASON THE SECOND FULL COPY CAN GO. The old shape took a second 424M snapshot
    # purely so the seal's probe had somewhere disposable to write its marker — an instrument
    # must not contaminate its own reading. One copy now, and the guarantee is bought instead
    # by the probe unlinking what it wrote. That unlink is load-bearing and invisible, so it
    # is asserted DIRECTLY at check_instance_seal rather than through run_proof: run_proof
    # takes its before-manifest AFTER the probe, which makes a leaked marker unreportable
    # there — i.e. a tooth aimed through run_proof would pass whether or not the unlink ran,
    # and pass FOR THE WRONG REASON. Here the swap root itself is the witness.
    ok, why = bwrap_available()
    if not ok:
        print(f"  INDETERMINATE  cannot build an instance seal on this host: {why}")
        return
    swap = snapshot_instance_space()
    try:
        seal = check_instance_seal(get_isolation("none"), swap, str(Path(__file__).parent))
        assert seal.verdict == SEALED, (
            f"this tooth reads a CONFIRMED seal; got {seal.verdict}: {seal.detail}")
        left = [q.name for q in Path(swap).iterdir() if q.name.startswith("instance-seal-probe-")]
        assert not left, (
            f"the probe's exhaust is still sitting in the world the proof will run in: {left} — "
            f"with one copy per proof there is no second snapshot absorbing it")
    finally:
        _drop(swap)


def _main() -> int:
    checks = [
        test_no_isolation_is_honestly_open,
        test_the_four_seal_verdicts_are_measured_not_assumed,
        test_only_sealed_and_open_are_trustworthy,
        test_unknown_isolation_is_refused,
        test_netns_really_seals_on_this_host,
        test_run_proof_records_the_seal_without_schema_drift,
        test_run_proof_under_netns_when_available,
        test_the_seal_does_not_depend_on_how_the_path_is_spelled,
        test_the_snapshot_leaves_the_trail_tree_empty_and_present,
        test_a_batch_reads_the_live_root_once,
        test_a_private_copy_is_private,
        test_the_pristine_is_rebuilt_when_the_top_level_moves,
        test_the_seal_evidence_carries_what_it_cost,
        test_the_probe_removes_its_own_exhaust,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the tester owns a MEASURED network seal; the hollow-seal case is caught")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
