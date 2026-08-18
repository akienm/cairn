"""PROOF — the watch that catches the 29-hour outage recurring is itself wired, not armed.

Ticket the-loop-names-its-own-staleness-instead-of-benching-a-device. ``staleness.py`` has
its own proof; this one judges the PROBE that hangs the predicate on the beat —
``probes/loop_not_stale.py``.

WHY THIS FILE EXISTS AT ALL, AND IT IS THE FINDING THAT BORE IT. The probe shipped with no
proof touching it. It was discovered, loaded, and berthed, the suite read 107/107 green, and
its every-beat path raised ``AttributeError: 'TroubleDevice' object has no attribute 'root'``
the first time anything CALLED it — which happened while measuring its cost for the exit
gate, not while testing it. A watch that cannot run is a watch that is off, and the whole
ticket is about a watch layer being switched off without anyone seeing. So the failure had
the exact shape of the thing being watched for, one level up: armed by hand is not wired,
and the diagnostic is to CALL IT.

WHAT A HOLLOW BUILD PASSES AND THESE TEETH MUST NOT (Law 8):

  * A probe that only ever meets fixtures. Every tooth below that can call the real path
    calls the real path — ``test_the_every_beat_path_actually_runs`` takes no fixture at
    all, and it is the tooth that would have bitten on day one.
  * Counting a CLEARED bench as a bench. The first draft globbed FILENAMES, and a file keeps
    its name after it is cleared, so the cheap half and the expensive half held two
    definitions of "benched" that disagreed exactly when a bench had just been lifted —
    the state right after someone acts on this probe's own advice.
  * Clearing on silence. ``_enough`` must refuse a store that has never recorded the
    condition, because that is indistinguishable from the 29 hours themselves (Law 9), and
    two teeth bite there from both sides.
  * Firing on a device that is genuinely broken. The probe fires on a RELATION, and a
    device that is benched AND really fails to import is a correct bench, not a finding.

    python3 cairn/devices/ground_loop/proofs/test_loop_not_stale.py    # exit 0 = green
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.devices.tester.scratch import scratch_dir  # noqa: E402
from cairn.devices.trouble import trouble as trouble_mod  # noqa: E402
from cairn.devices.ground_loop.loop import SELF_TROUBLE, TROUBLE_PREFIX  # noqa: E402
from cairn.devices.ground_loop.probes import loop_not_stale as P  # noqa: E402

_SERIAL = [0]


class _Store:
    """A real TroubleDevice over a temp root, swapped in where the probe reaches for one.

    The probe constructs ``TroubleDevice()`` bare, on purpose — it reads the world, and a
    probe holding an injected store would be measuring a fixture on the live beat. So the
    swap happens at the module the probe imports FROM, which is the same door the live
    process resolves, and the store is a real one differing only in its root.
    """

    def __init__(self) -> None:
        _SERIAL[0] += 1
        self.root = Path(scratch_dir("loop-not-stale")) / f"troubles-{_SERIAL[0]}"
        self.root.mkdir(parents=True, exist_ok=True)
        self._real = trouble_mod.TroubleDevice
        root = self.root
        trouble_mod.TroubleDevice = lambda *a, **k: self._real(root=root)  # noqa: E731

    def write(self, ident: str, *, standing: str = "OPEN", last_seen: str) -> None:
        (self.root / f"{ident}.json").write_text(json.dumps(
            {"id": ident, "standing": standing, "last_seen": last_seen,
             "why": "fixture", "count": 1}), encoding="utf-8")

    def close(self) -> None:
        trouble_mod.TroubleDevice = self._real


def _survey(*, benched: dict, last_seen=None, started=1_000_000.0) -> dict:
    """A survey shaped exactly as ``survey_the_bench`` returns one, so ``judge`` is fed the
    real contract rather than a convenient subset."""
    return {
        "benched": sorted(benched),
        "verdicts": benched,
        "self_trouble_live": False,
        "condition_last_seen": last_seen,
        "diagnostics": {"process_started": started, "drifted": [], "undecidable": [],
                        "tree_newest_file": None, "tree_newer_than_process": False},
    }


# THE VERDICT CONTRACT CARRIES TWO READINGS, not one, since 2026-08-18: what THIS process
# sees, and what a fresh interpreter sees. The deciding one is the fresh one, because the
# in-process read is taken by the process under suspicion.
_IMPORTS = {"on_disk": True, "imports_cleanly_in_this_process": True,
            "imports_cleanly_fresh": True, "fresh_refusal": None,
            "failures": [], "fresh_failures": []}
_BROKEN = {"on_disk": True, "imports_cleanly_in_this_process": False,
           "imports_cleanly_fresh": False, "fresh_refusal": None,
           "failures": ["ImportError: boom"], "fresh_failures": ["ImportError: boom"]}
# The stale-loop signature: real here, absent on disk.
_STALE = {"on_disk": True, "imports_cleanly_in_this_process": False,
          "imports_cleanly_fresh": True, "fresh_refusal": None,
          "failures": ["ImportError: boom"], "fresh_failures": []}
# The child could not be read at all — never silently clean.
_UNREADABLE = {"on_disk": True, "imports_cleanly_in_this_process": False,
               "imports_cleanly_fresh": False, "fresh_refusal": "exit 1: boom",
               "failures": ["ImportError: boom"], "fresh_failures": None}


# --- the teeth that take no fixture: the probe against the world ------------------------

def test_the_every_beat_path_actually_runs():
    """THE TOOTH THAT WOULD HAVE BITTEN ON DAY ONE. No fixture, no patch, no injected
    store — call the trigger the way the beat calls it and require a verdict. The shipped
    defect was an AttributeError on a name that does not exist, and nothing that stops
    short of calling this line can see it."""
    verdict = P.PROBE.trigger(None, {})
    assert isinstance(verdict, bool), f"the trigger returned {verdict!r}, not a verdict"


def test_the_probe_loads_under_the_loops_own_discovery():
    """Structurally uncallable is a third answer to 'zero callers', and the only way to
    tell it from armed-by-hand is to let the real discovery find and load it."""
    from cairn.devices.ground_loop.discovery import discover
    found = discover(skip=set())
    assert "ground_loop" in found, sorted(found)
    entry = found["ground_loop"]
    assert not entry["failures"], entry["failures"]
    assert [p for p in entry["probes"] if p.to == "harbor_master"], \
        "the loop's own discovery did not load this probe"


def test_a_store_with_no_bench_reads_false():
    """A staleness alarm that is always on is a bench that never lifts — the predicate's
    founding falsification. With NOTHING benched, the probe must be silent.

    THIS TOOTH USED TO ASSERT A SNAPSHOT OF THE PRODUCTION STORE (``trigger(None, {}) is
    False``, no fixture) and it went red on 2026-08-18 for the correct reason: a real bench
    stood, the device imported cleanly, and the probe fired exactly as designed. So the
    check reported the world's state where it meant to report the probe's rule, and the
    louder half is that it had been green only while the store happened to be clean — a
    proof over live data must assert an INVARIANT, never a value. The invariant is: no bench
    tickets, no fire. The world-facing tooth that stays is ``test_the_every_beat_path_
    actually_runs``, which requires a verdict rather than a particular one.
    """
    store = _Store()
    try:
        store.write("some-unrelated-trouble", last_seen="2026-08-13T09:00:00")
        assert P._bench_tickets_exist() is False
        assert P.PROBE.trigger(None, {}) is False
    finally:
        store.close()


# --- the cheap half: benched means LIVE, not merely named -------------------------------

def test_a_live_bench_ticket_is_a_bench():
    store = _Store()
    try:
        store.write(f"{TROUBLE_PREFIX}librarian", last_seen="2026-08-13T09:00:00")
        assert P._bench_tickets_exist() is True
    finally:
        store.close()


def test_a_cleared_bench_ticket_is_not_a_bench():
    """The divergent-definition defect, pinned. The file is still on disk under its bench
    name; only its standing changed. A cheap half that reads names says True here and the
    expensive half says nothing is benched — disagreeing precisely in the state that
    follows someone acting on this probe's advice."""
    store = _Store()
    try:
        store.write(f"{TROUBLE_PREFIX}librarian", standing=trouble_mod.CLEARED,
                    last_seen="2026-08-13T09:00:00")
        assert P._bench_tickets_exist() is False
        assert (store.root / f"{TROUBLE_PREFIX}librarian.json").exists(), \
            "the fixture must leave the file named as a bench, or it proves nothing"
    finally:
        store.close()


def test_an_unrelated_trouble_is_not_a_bench():
    store = _Store()
    try:
        store.write("some-other-thing-entirely", last_seen="2026-08-13T09:00:00")
        store.write(SELF_TROUBLE, last_seen="2026-08-13T09:00:00")
        assert P._bench_tickets_exist() is False, \
            "the loop naming ITSELF is the correct outcome, not a device on the bench"
    finally:
        store.close()


# --- the judgement: it fires on the RELATION -------------------------------------------

def test_it_fires_on_a_device_benched_while_importing_cleanly():
    """The exact shape of the 29 hours: held out by a live ticket, imports fine right now."""
    j = P.judge(_survey(benched={"librarian": _IMPORTS, "chart": _IMPORTS}))
    assert j["benched_but_importing"] == ["chart", "librarian"], j
    assert P._trigger(None, {"judged": j}) is True


def test_it_stays_silent_on_a_device_that_really_is_broken():
    """A correct bench is not a finding. If this fired here the probe would cry wolf on
    every genuine failure and the layer it protects would be ignored again."""
    j = P.judge(_survey(benched={"librarian": _BROKEN}))
    assert j["benched_but_importing"] == [], j
    assert P._trigger(None, {"judged": j}) is False


def test_one_wrongly_benched_device_among_broken_ones_still_fires():
    """FIRE ON THE FIRST ONE — the failure mode is silent by construction, so a threshold
    of any kind is waiting in the dark."""
    j = P.judge(_survey(benched={"a": _BROKEN, "b": _BROKEN, "c": _IMPORTS}))
    assert j["benched_but_importing"] == ["c"], j
    assert P._trigger(None, {"judged": j}) is True


# --- the clear: silence is not evidence -------------------------------------------------

def test_a_store_that_never_saw_the_condition_clears_nothing():
    """Until a restart has been survived there is nothing to have survived. A watch that
    has only ever seen quiet has not been tested (Law 9)."""
    j = P.judge(_survey(benched={}, last_seen=None))
    assert j["condition_ever_recorded"] is False, j
    assert j["survived_a_restart"] is False, j
    assert P._enough({"judged": j}) is False


def test_a_condition_seen_after_this_process_started_clears_nothing():
    """The loop has NOT lived its whole life clean through the event — the condition
    landed inside this process's lifetime, which is the outage in progress."""
    j = P.judge(_survey(benched={}, last_seen="2026-08-13T12:00:00",
                        started=P.judge(_survey(benched={}))["process_started"]))
    later = P.judge(_survey(benched={}, last_seen="2030-01-01T00:00:00", started=1_000_000.0))
    assert later["survived_a_restart"] is False, later
    assert P._enough({"judged": later}) is False


def test_it_clears_only_when_the_condition_predates_this_process():
    """Both halves satisfied, and they share one variable so silence cannot buy either."""
    j = P.judge(_survey(benched={}, last_seen="1970-01-12T13:46:40+00:00",
                        started=2_000_000.0))
    assert j["survived_a_restart"] is True, j
    assert P._enough({"judged": j}) is True


def test_a_wrongly_benched_device_blocks_the_clear_even_after_a_restart():
    """The two halves are AND, not OR — surviving a restart while a device is still
    wrongly benched is the outage continuing, not the outage ending."""
    j = P.judge(_survey(benched={"librarian": _IMPORTS},
                        last_seen="1970-01-12T13:46:40+00:00", started=2_000_000.0))
    assert j["survived_a_restart"] is True, j
    assert P._enough({"judged": j}) is False


def test_an_unparseable_timestamp_does_not_clear():
    """A store it cannot read is not a store that says all-clear."""
    j = P.judge(_survey(benched={}, last_seen="not a timestamp", started=2_000_000.0))
    assert j["survived_a_restart"] is False, j
    assert P._enough({"judged": j}) is False


# --- what the fire hands the recipient --------------------------------------------------

def test_the_carry_names_the_diagnosis_order_and_its_own_ticket():
    """Getting the order backwards is how this went unread for 29 hours, so the carry
    states it; and the probe has no authority to re-open anything (Law 6), so it must
    point at the owning ticket rather than act."""
    j = P.judge(_survey(benched={"librarian": _IMPORTS}))
    carry = P._carry({"judged": j})
    assert carry["benched_but_importing"] == ["librarian"], carry
    assert "process start" in carry["read_this_first"], carry["read_this_first"]
    assert carry["read_this_first"].index("restart") < \
        carry["read_this_first"].index("clear"), "the fix order must survive in the carry"
    assert P._OWNING_TICKET in json.dumps(carry["ticket"]), carry["ticket"]
    assert "ERROR STRING" in carry["against_falsifier"], \
        "the hollow pass this build refuses must travel with the finding"


def test_the_reading_that_decides_is_taken_where_this_process_is_not():
    """THE TOOTH FOR THE SECOND TICKET'S OWN DISEASE, found by aiming the finished probe at
    the world. The first build took the second reading with ``discover()`` IN THIS PROCESS —
    and this process is the ground loop, the thing suspected of being stale. A stale process
    re-execs the probe file fine and then binds its ``from cairn... import`` through the
    boot-time ``sys.modules``, so it REPRODUCES the failure and reads the misattributed bench
    as a real defect. The probe could only ever fire when run from somewhere other than the
    loop it watches.

    Measured here rather than argued: one throwaway tree, one module held pre-edit by this
    interpreter, one probe importing the symbol the edit added. The two readings must
    DISAGREE — that disagreement is the whole instrument."""
    import subprocess, sys, textwrap
    from cairn.devices.ground_loop.discovery import discover

    root = Path(scratch_dir("loop-not-stale")) / f"fresh-{_SERIAL[0]}-{id(object())}"
    pkg, dev = root / "wtree", root / "devices" / "widget" / "probes"
    pkg.mkdir(parents=True); dev.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "gear.py").write_text("OLD = 1\n")
    (dev / "p.py").write_text(textwrap.dedent("""
        from wtree.gear import NEWSYM
        from cairn.tools.base.probe import Probe
        PROBE = Probe(why="fixture", trigger=lambda now, ctx: False, to="harbor_master",
                      body={}, carry=lambda ctx: {}, enough=lambda ctx: True)
    """))
    sys.path.insert(0, str(root))
    try:
        import wtree.gear  # noqa: F401  — HELD by this process, pre-edit
        (pkg / "gear.py").write_text("OLD = 1\nNEWSYM = 2\n")

        here = discover(root / "devices")["widget"]
        assert here["failures"], "this process was supposed to hold the pre-edit module"

        fresh = P.fresh_import_reading(here["folder"])
        assert fresh["refusal"] is None, fresh["refusal"]
        assert fresh["failures"] == [], fresh["failures"]
        assert fresh["probes"] == 1, fresh
    finally:
        sys.path.remove(str(root))
        sys.modules.pop("wtree.gear", None)
        sys.modules.pop("wtree", None)


def test_a_device_that_fails_here_and_imports_fresh_is_the_loops_fault():
    """The judgement over that pair. Before the fix this fixture read as a REAL defect —
    silent — which is exactly backwards."""
    seen = P.judge(_survey(benched={"widget": _STALE}, last_seen="2000-01-01T00:00:00+00:00"))
    assert seen["benched_but_importing"] == ["widget"], seen
    assert seen["reproduces_here_but_not_fresh"] == ["widget"], seen
    assert P.PROBE.trigger(None, {"judged": seen}) is True


def test_a_fresh_reading_that_refused_never_lifts_a_bench():
    """A crashed subprocess is not a clean import. Reading a refusal as 'imports cleanly'
    would lift a real bench on the strength of a dead child process."""
    seen = P.judge(_survey(benched={"widget": _UNREADABLE},
                           last_seen="2000-01-01T00:00:00+00:00"))
    assert seen["benched_but_importing"] == [], seen
    assert seen["fresh_reading_refused"] == ["widget"], seen


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — the proof reports, it does not raise
            failures += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — the watch is wired, fires on the relation, and does not clear on silence")
