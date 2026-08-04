"""THE BERTHED PROBE OVER THE RECORDER'S OWN WINDOW, PROVED.

Ticket ``logger-for-bash`` (2026-07-30). ``bin/proofs/test_logger_for_bash.py`` proves the
recorder — that the window is bounded and that the newest records survive the cut. It cannot
prove that 1000 is the RIGHT bound, because that depends on traffic nobody has generated yet.
This proves the instrument that will answer it, and the instrument is where every probe defect
this system has found has actually lived.

WHAT THE FIRST LIVE FIRE FOUND, and it is the same shape twice in one afternoon: a copy of the
evidence counted as more evidence. The survey walked ``~/.cairn/logs`` and reported TWO
namespaces — ``boot`` with 19 runs, and ``boot.pre-decontamination`` with 54, a pre-image
parked beside the record an hour earlier while cleaning a different contamination out of it.
Nothing about a backup distinguishes it from a namespace: it is the same grammar, written by
the same recorder, sitting in the same directory. Fixed by physics rather than by a name to
remember — anything KEPT rather than WRITTEN now lives in a subdirectory, and a subdirectory
is not a file, so it cannot be surveyed at all.

WHAT THIS PROVES:
  - THE INVARIANT: no state where the watch has CLEARED but could never have FIRED —
    specifically, it must not clear on a fresh install where nothing has ever filled and
    therefore nothing can be a peephole. Exhausted, not sampled.
  - FIRE AND CLEAR ARE MUTUALLY EXCLUSIVE, and every clause of each predicate is load-bearing.
  - A NAMESPACE IS IDENTIFIED BY GRAMMAR, NOT BY NAME: the reader counts only files whose
    lines parse as this recorder's records, so a stray text file cannot manufacture a
    one-process peephole finding out of nothing, and a subdirectory is never a namespace.
  - THE WINDOW UNDER TEST IS READ FROM THE ENVIRONMENT, not carried as a stale copy — the
    whole point of the watch is that the number is expected to move.
  - IT IS ARMED IN THE SENSE THE EMISSION GATE MEANS, read through the gate's own instrument.
  - THE DATUM POINTS AT THE TICKET AND DOES NOT COPY IT (Law 6).
  - IT REACHES NOWHERE — no device, no bus, no network.

    python3 bin/proofs/test_retention_window_probe.py     # exit 0 = green
"""

from __future__ import annotations

import ast
import datetime
import importlib.util
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

BERTH = REPO / "bin" / "probes" / "retention_window.py"

_spec = importlib.util.spec_from_file_location("_probe_retention_window", BERTH)
SUT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SUT)

from cairn.base.probe import Probe  # noqa: E402
from cairn.tester.scratch import scratch_dir  # noqa: E402

NOW = datetime.datetime(2026, 7, 30, tzinfo=datetime.timezone.utc)
_failures: list[str] = []


def _at(turned: int, peepholes: int) -> dict:
    """A survey the predicates will read instead of the disk — the dial this proof moves."""
    return {"namespaces": {"window": 1000, "namespaces": [], "turned_over": turned,
                           "peepholes": peepholes}}


def _dir(files: dict[str, str]) -> Path:
    root = scratch_dir("cairn-retention-proof-")
    for name, body in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return root


def _records(pids: list[str], per_pid: int = 1) -> str:
    """Records in the recorder's real grammar, so the reader is proved against the format
    ``bin/logger_for_bash`` writes rather than against a paraphrase of it."""
    out, i = [], 0
    for pid in pids:
        for _ in range(per_pid):
            out.append(f"20260730.120000.{i:06d}.{pid}: a record\n")
            i += 1
    return "".join(out)


# --- the invariant ---------------------------------------------------------------------

def test_the_watch_can_never_clear_before_it_could_fire() -> None:
    """THE LOAD-BEARING TOOTH, and the state it guards is the ordinary one: a FRESH INSTALL.
    Nothing has filled, so nothing can be a peephole, so a floorless clear would retire the
    watch on day one having measured nothing. Exhausted over the reachable space
    (``peepholes <= turned_over`` always — only a turned-over namespace can be a peephole)."""
    bad = []
    for turned in range(0, SUT._ENOUGH_TURNED * 4):
        for peepholes in range(0, turned + 1):
            if SUT._enough(_at(turned, peepholes)) and turned < SUT._ENOUGH_TURNED:
                bad.append((turned, peepholes))
    assert not bad, (
        f"the watch clears below the turnover floor at (turned_over, peepholes) = {bad[:6]} — "
        "on a fresh install that is a watch retiring before it could ever fire")


def test_fire_and_clear_are_mutually_exclusive() -> None:
    both = [(t, p) for t in range(0, SUT._ENOUGH_TURNED * 4) for p in range(0, t + 1)
            if SUT._trigger(NOW, _at(t, p)) and SUT._enough(_at(t, p))]
    assert not both, f"fires AND clears on the same survey at {both[:6]}"


def test_every_clause_is_load_bearing() -> None:
    n = SUT._ENOUGH_TURNED
    assert not SUT._trigger(NOW, _at(n - 1, 1)), "fired below the turnover floor"
    assert not SUT._enough(_at(n - 1, 0)), "cleared below the turnover floor"
    assert SUT._trigger(NOW, _at(n, 1)), "did not fire on a real peephole"
    assert SUT._enough(_at(n, 0)), "did not clear once the window survived both profiles"


# --- the reader, against the recorder's real grammar --------------------------------------

def test_a_namespace_is_identified_by_grammar_not_by_name() -> None:
    """A stray text file in the log directory must not read as a namespace with one process —
    the shape that manufactures a peephole finding out of a file the recorder never wrote.
    Measured on this box: a ``preflight.json`` sits in that directory today."""
    root = _dir({"boot": _records(["100", "200"]),
                 "notes.txt": "just some prose\nnobody logged this\n",
                 "boot.lock": "", "preflight.json": '{"a": 1}'})
    s = SUT.survey_the_namespaces(root)
    assert [r["namespace"] for r in s["namespaces"]] == ["boot"], s


def test_a_kept_copy_is_not_a_second_namespace() -> None:
    """THE LIVE-FIRE DEFECT, pinned. A pre-image of the record is byte-identical in grammar to
    the record; only its LOCATION can distinguish it, so the survey is non-recursive and a
    subdirectory can never be surveyed."""
    root = _dir({"boot": _records(["100", "200"]),
                 "archive/boot.pre-decontamination": _records(["300", "400", "500"])})
    s = SUT.survey_the_namespaces(root)
    assert [r["namespace"] for r in s["namespaces"]] == ["boot"], (
        f"a kept copy was counted as evidence: {s}")


def test_a_full_window_holding_one_process_is_a_peephole() -> None:
    """The finding itself: a record that has turned over and can no longer show a previous run
    has stopped being a record and become a peephole onto the present."""
    os.environ["CAIRN_LOGLEN"] = "10"
    try:
        root = _dir({"bash": _records(["100"], per_pid=12),
                     "boot": _records(["200", "300"], per_pid=6)})
        s = SUT.survey_the_namespaces(root)
        rows = {r["namespace"]: r for r in s["namespaces"]}
        assert rows["bash"]["peephole"] is True, rows["bash"]
        assert rows["boot"]["peephole"] is False, rows["boot"]
        assert s["turned_over"] == 2 and s["peepholes"] == 1, s
        assert SUT._trigger(NOW, {"namespaces": s}), "the peephole did not fire the trigger"
    finally:
        del os.environ["CAIRN_LOGLEN"]


def test_a_window_that_has_not_filled_is_not_judged() -> None:
    """An unfilled window says nothing about retention — it has discarded nothing."""
    root = _dir({"bash": _records(["100"], per_pid=3)})
    s = SUT.survey_the_namespaces(root)
    assert s["turned_over"] == 0 and s["peepholes"] == 0, s
    assert not SUT._trigger(NOW, {"namespaces": s}) and not SUT._enough({"namespaces": s})


def test_a_surviving_trim_mark_counts_as_turnover_on_its_own() -> None:
    """Fullness is the durable half and the mark is the corroborating half: a namespace that
    cut and then shrank below the cap still says so, until the mark itself is trimmed away."""
    root = _dir({"bash": _records(["100"]) +
                 "20260730.120001.000000.100: logtrim: discarded 40 lines, window now starts at X\n"})
    s = SUT.survey_the_namespaces(root)
    row = s["namespaces"][0]
    assert row["trim_marks"] == 1 and row["turned_over"] is True, row


def test_an_absent_log_directory_is_not_a_finding() -> None:
    s = SUT.survey_the_namespaces(scratch_dir("no-such-logdir-") / "cairn-no-such-logdir")
    assert s["namespaces"] == [] and s["turned_over"] == 0 and s["peepholes"] == 0, s


def test_the_window_under_test_is_read_from_the_environment() -> None:
    """A probe carrying its own copy of the number under test would keep answering about a
    window nobody is running — and this number is EXPECTED to move; that is the whole watch."""
    assert SUT._window() == 1000, "the default drifted from the recorder's default"
    os.environ["CAIRN_LOGLEN"] = "37"
    try:
        assert SUT._window() == 37, "the probe ignored a moved window"
    finally:
        del os.environ["CAIRN_LOGLEN"]
    src = BERTH.read_text(encoding="utf-8")
    assert src.count("CAIRN_LOGLEN") >= 1, "the window is not read from the environment at all"


# --- the declaration ---------------------------------------------------------------------

def test_the_probe_is_armed_the_way_the_emission_gate_means_it() -> None:
    from cairn.base import watchme_spec

    ticket_path = watchme_spec._TICKETS / "logger-for-bash.json"
    assert ticket_path.is_file(), f"the owning ticket is not on file at {ticket_path}"
    ticket = json.loads(ticket_path.read_text(encoding="utf-8"))
    assert watchme_spec.watchme_spec_error(ticket) is None, watchme_spec.watchme_spec_error(ticket)
    spec = watchme_spec.spec_for(ticket, "retention-window")
    assert spec is not None, "no spec for the object the workflow string names"
    assert watchme_spec.armed_error(spec) is None, watchme_spec.armed_error(spec)
    assert isinstance(SUT.PROBE, Probe) and SUT.PROBE.carry and SUT.PROBE.enough
    assert (REPO / spec["probe"]).resolve() == BERTH.resolve(), (
        f"the ticket berths the probe at {spec['probe']!r}, this proof is proving {BERTH}")


def test_the_datum_points_at_the_ticket_and_carries_the_rows() -> None:
    """Law 6 — a pointer to the ticket, never a copy. And the per-namespace rows ride along:
    without them the owner would be moving the number off another guess, which is the defect
    the watch exists to retire."""
    os.environ["CAIRN_LOGLEN"] = "10"
    try:
        root = _dir({"bash": _records(["100"], per_pid=12)})
        got = SUT._carry({"namespaces": SUT.survey_the_namespaces(root)})
    finally:
        del os.environ["CAIRN_LOGLEN"]
    assert got["ticket"] == SUT._OWNING_TICKET
    assert got["blind"] == ["bash"], got
    assert got["rows"] and "retained" in got["rows"][0], "the rows do not carry the evidence"
    blob = json.dumps(got)
    for owned in ("intention", "falsifier", "provenance", "children", "stage_needs"):
        assert f'"{owned}"' not in blob, f"the datum copied the ticket's {owned!r} field"


def test_it_reaches_nowhere() -> None:
    tree = ast.parse(BERTH.read_text(encoding="utf-8"))
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            names.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            names.add(n.module.split(".")[0])
    forbidden = {"socket", "http", "urllib", "requests", "psycopg", "psycopg2", "subprocess"}
    assert not (names & forbidden), f"reaches outward: {sorted(names & forbidden)}"


def _main() -> int:
    print(f"proof: the retention-window probe — berth={BERTH.relative_to(REPO)}")
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except AssertionError as exc:
                print(f"  FAIL  {name}: {exc}", file=sys.stderr)
                _failures.append(name)
    if _failures:
        print(f"\n{len(_failures)} FAILED: {', '.join(_failures)}", file=sys.stderr)
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
