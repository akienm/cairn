"""THE BERTHED PROBE OVER THE PREFLIGHT, PROVED — and the contamination its live fire found.

Ticket ``superclaude-starts-itself`` (2026-07-30). Written the way ``cairn/base/proofs/
test_does_optional_probe.py`` had to be written: the Probe PRIMITIVE is proved elsewhere, on
synthetic dials, and every defect this system has found in a probe has been in the INSTANCE.

WHAT THE FIRST LIVE FIRE FOUND, and it was not in the predicates. Fired by hand against the
real boot log the moment the berth existed, the probe reported a finding that had ridden
UNFIXED through twelve separate launches — an unarguable poke to the owner. The finding was
``SYNTHETIC FINDING for the proof``: ``launchers/proofs/test_bootstrap.py``'s own fixture,
written twelve times by twelve runs of the suite, because the harness inherited the
environment and ``bootstrap.sh`` writes to ``${CAIRN_BOOT_LOG:-$HOME/.cairn/logs/boot}``.
The probe was correct, the predicates were correct, and the answer was fabricated — the test
suite had become the evidence. A second pass found six more from the OTHER fixture in the
same file, missed by a first containment check that grepped for one remembered string.

Both are fixed at the source (the harness owns its own namespace; the containment tooth is
structural — every child must go through ``_env()``), and the record was decontaminated with
the removal noted in the record itself. What is proved HERE is the probe's own half.

WHAT THIS PROVES:
  - THE INVARIANT: over the whole corpus space there is NO state where the watch has CLEARED
    but could never have FIRED. Exhausted, not sampled — the defect that killed this system's
    first probe, and the reason ``_FLOOR >= _PATIENCE`` is a relationship and not two numbers.
  - FIRE AND CLEAR ARE MUTUALLY EXCLUSIVE.
  - EVERY CLAUSE OF EACH PREDICATE IS LOAD-BEARING — drop one and the probe is wrong in a
    direction already paid for.
  - THE READER IS A READER: a launch is a pid, a finding is counted once per launch however
    many times that launch repeats it, and a line it cannot parse is skipped rather than
    guessed at (Law 3 — a diagnostic surface reading another one must not invent structure).
  - IT IS ARMED IN THE SENSE THE EMISSION GATE MEANS, read through the gate's own instrument.
  - THE DATUM POINTS AT THE TICKET AND DOES NOT COPY IT (Law 6).
  - IT REACHES NOWHERE — no device, no bus, no network — so it is cheap on a pulse.

    python3 launchers/proofs/test_reported_but_unfixed_probe.py     # exit 0 = green
"""

from __future__ import annotations

import ast
import datetime
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

BERTH = REPO / "launchers" / "probes" / "reported_but_unfixed_floor.py"

_spec = importlib.util.spec_from_file_location("_probe_reported_but_unfixed", BERTH)
SUT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SUT)

from cairn.base.probe import Probe  # noqa: E402

NOW = datetime.datetime(2026, 7, 30, tzinfo=datetime.timezone.utc)
_failures: list[str] = []


def _at(reporting: int, worst: int) -> dict:
    """A survey the predicates will read instead of the disk — the dial this proof moves."""
    return {"boot_log": {"launches": max(reporting, worst), "reporting": reporting,
                         "bypassed": 0, "worst": worst, "worst_finding": "x",
                         "distinct_findings": 1 if worst else 0}}


def _log(records: list[tuple[str, str]]) -> Path:
    """A boot namespace on disk in the recorder's real grammar, so the reader is proved
    against the format ``bin/logger_for_bash`` actually writes, not against a paraphrase."""
    p = Path(tempfile.mkdtemp(prefix="cairn-probe-proof-")) / "boot"
    p.write_text("".join(f"20260730.120000.{i:06d}.{pid}: {msg}\n"
                         for i, (pid, msg) in enumerate(records)), encoding="utf-8")
    return p


# --- the invariant ---------------------------------------------------------------------

def test_the_watch_can_never_clear_before_it_could_fire() -> None:
    """THE LOAD-BEARING TOOTH. If the watch has CLEARED, the corpus was always big enough that
    it COULD have fired. Exhaustive over the reachable space (``worst <= reporting`` always —
    a finding cannot be reported by more launches than reported anything), so no state the
    code happens to sit in today can hide a hole."""
    bad = []
    for reporting in range(0, SUT._FLOOR * 3):
        for worst in range(0, reporting + 1):
            ctx = _at(reporting, worst)
            if SUT._enough(ctx) and reporting < SUT._PATIENCE:
                bad.append((reporting, worst))
    assert not bad, (
        f"the watch clears on a corpus too small to have ever fired it, at "
        f"(reporting, worst) = {bad[:6]} — a watch that retires before it can bite is the "
        "v1 LEARNME failure wearing a probe's clothes")


def test_the_floor_is_at_least_the_patience() -> None:
    """The relationship, asserted directly. The two numbers are not independent taste: a floor
    below the patience leaves a reachable corpus where the watch clears but no finding could
    ever have survived long enough to fire it."""
    assert SUT._FLOOR >= SUT._PATIENCE, (
        f"_FLOOR={SUT._FLOOR} is below _PATIENCE={SUT._PATIENCE} — the watch can clear on a "
        "corpus where firing was arithmetically impossible")


def test_fire_and_clear_are_mutually_exclusive() -> None:
    """No corpus may both poke the owner and retire the watch — that would report a finding
    and simultaneously refuse to be asked again."""
    both = [(r, w) for r in range(0, SUT._FLOOR * 3) for w in range(0, r + 1)
            if SUT._trigger(NOW, _at(r, w)) and SUT._enough(_at(r, w))]
    assert not both, f"fires AND clears on the same corpus at {both[:6]}"


def test_every_clause_is_load_bearing() -> None:
    f, p = SUT._FLOOR, SUT._PATIENCE
    assert not SUT._trigger(NOW, _at(f - 1, p)), "fired below the floor — pokes about noise"
    assert not SUT._enough(_at(0, 0)), (
        "cleared on an empty record — zero reports, zero survivors, question never asked")
    assert SUT._trigger(NOW, _at(f, p)), "did not fire on a finding that survived the patience"
    assert not SUT._trigger(NOW, _at(f, p - 1)), (
        "poked about a finding still inside the patience window — the session was told and "
        "may still be working on it")
    assert SUT._enough(_at(f, p - 1)), "did not clear once an exercised loop kept closing"


# --- the reader, against the recorder's real grammar --------------------------------------

def test_a_launch_is_a_pid_and_a_finding_counts_once_per_launch() -> None:
    """A launch that reports the same finding twice must count once — else a chatty launch
    manufactures survival on its own, which is the single-sample failure in a new dress."""
    p = _log([("100", "launch: argv=[]"),
              ("100", "report: unfixed — the floor"),
              ("100", "report: unfixed — the floor"),
              ("200", "launch: argv=[]"),
              ("200", "report: unfixed — the floor")])
    s = SUT.survey_the_boot_log(p)
    assert s["launches"] == 2, s
    assert s["reporting"] == 2, s
    assert s["worst"] == 2, f"one launch repeating itself was counted as survival: {s}"
    assert s["worst_finding"] == "the floor", s


def test_an_unparseable_line_is_skipped_not_guessed_at() -> None:
    """This is a diagnostic surface reading another one. Inventing structure for a line it
    cannot parse is how a probe reports confidently about something it did not measure."""
    p = _log([("100", "launch: x"), ("100", "report: unfixed — real")])
    p.write_text(p.read_text(encoding="utf-8") + "not a record at all\nalso: not one\n",
                 encoding="utf-8")
    s = SUT.survey_the_boot_log(p)
    assert s["launches"] == 1 and s["worst"] == 1, s


def test_an_absent_record_is_not_a_finding() -> None:
    """A box where the seam has never run must be silent, not accusatory."""
    s = SUT.survey_the_boot_log(Path(tempfile.gettempdir()) / "cairn-no-such-boot-log")
    assert s == {"launches": 0, "reporting": 0, "bypassed": 0, "worst": 0,
                 "worst_finding": None, "distinct_findings": 0}, s
    assert not SUT._trigger(NOW, {"boot_log": s}) and not SUT._enough({"boot_log": s})


def test_the_bypass_is_counted_but_does_not_fire() -> None:
    """``--no-preflight`` is the sharper signal and rides in the datum, not the predicate:
    one bypass is a legitimate rescue, which is exactly what the hatch is for."""
    p = _log([("100", "launch: x"), ("100", "preflight: bypassed"),
              ("200", "launch: x"), ("200", "preflight: skipped by --no-preflight")])
    s = SUT.survey_the_boot_log(p)
    assert s["bypassed"] == 2, s
    assert not SUT._trigger(NOW, {"boot_log": s}), "a bypass fired the trigger on its own"


# --- the declaration ---------------------------------------------------------------------

def test_the_probe_is_armed_the_way_the_emission_gate_means_it() -> None:
    """Read ARMED through the gate's own instrument, never a parallel notion of it — else this
    proof could pass a probe the door refuses."""
    from cairn.base import watchme_spec

    ticket_path = watchme_spec._TICKETS / "superclaude-starts-itself.json"
    assert ticket_path.is_file(), f"the owning ticket is not on file at {ticket_path}"
    ticket = json.loads(ticket_path.read_text(encoding="utf-8"))
    assert watchme_spec.watchme_spec_error(ticket) is None, watchme_spec.watchme_spec_error(ticket)
    spec = watchme_spec.spec_for(ticket, "reported-but-unfixed-floor")
    assert spec is not None, "no spec for the object the workflow string names"
    assert watchme_spec.armed_error(spec) is None, watchme_spec.armed_error(spec)
    assert isinstance(SUT.PROBE, Probe) and SUT.PROBE.carry and SUT.PROBE.enough


def test_the_berth_is_where_the_ticket_says_it_is() -> None:
    """Done is verified in the world, never in the record: the ticket's spec must name THIS
    file, resolved from the repo root the gate resolves from."""
    from cairn.base import watchme_spec

    ticket = json.loads((watchme_spec._TICKETS / "superclaude-starts-itself.json")
                        .read_text(encoding="utf-8"))
    spec = watchme_spec.spec_for(ticket, "reported-but-unfixed-floor")
    assert (REPO / spec["probe"]).resolve() == BERTH.resolve(), (
        f"the ticket berths the probe at {spec['probe']!r}, this proof is proving {BERTH}")


def test_the_datum_points_at_the_ticket_and_does_not_copy_it() -> None:
    """Law 6 — the ticket belongs to the commons; a probe carries a pointer to it."""
    got = SUT._carry(_at(SUT._FLOOR, SUT._PATIENCE))
    assert got["ticket"] == SUT._OWNING_TICKET
    blob = json.dumps(got)
    for owned in ("intention", "falsifier", "provenance", "children", "stage_needs"):
        assert f'"{owned}"' not in blob, f"the datum copied the ticket's {owned!r} field"
    assert "window_caveat" in got, (
        "the datum does not carry the caveat that its counts are a floor — the boot log is "
        "trimmed, so a finding older than the window is invisible and the count under-reports")


def test_it_reaches_nowhere() -> None:
    """No device, no bus, no network — the cost that lets it sit on every pulse. Over the AST,
    so a prose mention in a docstring cannot red it and a real import cannot hide in one."""
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
    print(f"proof: the reported-but-unfixed-floor probe — berth={BERTH.relative_to(REPO)}")
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
