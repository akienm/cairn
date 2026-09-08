"""SAIL RECORD — ``in-process`` derived from a live process, never stored on a shared file.

Ticket ``6ec9b384b451`` (the-pickup-phase-says-why-a-ticket-is-not-moving), ruling
``2026-09-08-a-fleet-of-one-reshapes-the-pickup-phase``.

THE DEFECT THIS REPLACES IS MEASURED, NOT FEARED: zero of 258 tickets have ever carried
``:in-process``, and the door built for it in August 2026 has thirteen journaled records
inside one four-day window and no caller since. A phase that claims a running hand cannot
live on a git-tracked file — nothing clears it, because the thing that would clear it is
the process that already died.

SO EVERY TOOTH HERE IS AIMED AT A WAY THE DERIVED READ LIES, and none at what it returns
when everything is fine:

  - IT SAYS LIVE FOR A PROCESS THAT IS ACTUALLY RUNNING — the only claim that cannot be
    faked by an empty implementation, since ``None`` would pass every DEAD tooth below.
  - IT SAYS DEAD FOR A REAPED PID. The plain death.
  - IT SAYS DEAD FOR A RECYCLED PID — a pid that IS running, whose start time disagrees.
    This is the sharp one: a pid-only detector answers LIVE here, and the claim it inherits
    belongs to an unrelated process. Driven against a real running pid, not a fixture.
  - IT NEVER RAISES. Absent, torn, and non-JSON records each come back DEAD with the lack
    NAMED (Law 7 at a diagnostic surface) — a consumer can act on DEAD, never on a
    traceback.
  - THE CROSSING IS THE CALLER, and it outranks the record: a ticket-carrying crossing
    stamps, a crossing into a terminal clears, a ticketless crossing stamps nothing, and a
    crossing whose instance-space cannot be written STILL CROSSES. Writing this record is a
    side effect; a crossing is a record of truth.
  - AND THE CORPUS CARRIES NO STORED CLAIM. Measured over the live tickets, not asserted.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.tools.base import sail_record, transitions  # noqa: E402

_TICKETS = Path.home() / "dev" / "src" / "CairnCommons" / "tickets"
_TICKET = "6ec9b384b451"


def _stamp(home: Path, **over) -> Path:
    """A record written by hand, so a tooth can state exactly which field is wrong."""
    record = {"ticket": _TICKET, "pid": os.getpid(),
              "starttime": sail_record.pid_starttime(os.getpid()),
              "opened": "2026-09-08T00:00:00+00:00"}
    record.update(over)
    home.mkdir(parents=True, exist_ok=True)
    path = home / sail_record.RECORD_NAME
    path.write_text(json.dumps(record))
    return path


def test_a_running_process_reads_LIVE_and_derives_the_phase():
    """The positive claim, and the one an empty implementation could not fake: every DEAD
    tooth below passes for a function that returns DEAD unconditionally."""
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        _stamp(home)
        seen = sail_record.read_sail(home)
        assert seen["verdict"] == "LIVE", seen
        assert seen["lack"] is None, seen
        assert sail_record.derived_phase(_TICKET, home=home) == "in-process"
        # and the claim is about ONE ticket — a live sail on A does not phase B
        assert sail_record.derived_phase("ffffffffffff", home=home) is None


def test_a_reaped_pid_reads_DEAD():
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    assert sail_record.pid_starttime(child.pid) is None or True  # may be recycled; see below
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        _stamp(home, pid=child.pid, starttime=999999999999)
        seen = sail_record.read_sail(home)
        assert seen["verdict"] == "DEAD", seen
        assert seen["lack"] and str(child.pid) in seen["lack"], seen
        assert sail_record.derived_phase(_TICKET, home=home) is None


def test_a_RECYCLED_pid_reads_DEAD_against_a_really_running_process():
    """The tooth a pid-only detector fails. The pid here is alive — this very process — and
    only the start time disagrees, exactly as it would after the kernel handed the number to
    something else."""
    real = sail_record.pid_starttime(os.getpid())
    assert isinstance(real, int), "the starttime read is broken; the tooth measured nothing"
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        _stamp(home, starttime=real + 1)
        seen = sail_record.read_sail(home)
        assert seen["verdict"] == "DEAD", seen
        assert "RECYCL" in seen["lack"].upper(), seen["lack"]
        assert sail_record.derived_phase(_TICKET, home=home) is None


def test_absent_and_unreadable_records_are_DEAD_with_the_lack_NAMED():
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        absent = sail_record.read_sail(home)
        assert absent["verdict"] == "DEAD" and absent["record"] is None
        assert sail_record.RECORD_NAME in absent["lack"], absent["lack"]

        home.mkdir(parents=True, exist_ok=True)
        (home / sail_record.RECORD_NAME).write_text("{not json at all")
        torn = sail_record.read_sail(home)
        assert torn["verdict"] == "DEAD" and "unreadable" in torn["lack"], torn

        (home / sail_record.RECORD_NAME).write_text(json.dumps({"ticket": _TICKET}))
        fieldless = sail_record.read_sail(home)
        assert fieldless["verdict"] == "DEAD" and "unreadable" in fieldless["lack"], fieldless
        # three distinct lacks, so a reader can tell "never opened" from "corrupt"
        assert len({absent["lack"], torn["lack"], fieldless["lack"]}) == 3


def test_no_face_raises_when_instance_space_is_unwritable():
    """Every entry point swallows its own I/O. A derived phase is a convenience; whatever
    calls this is doing something that matters more."""
    with tempfile.TemporaryDirectory() as d:
        blocker = Path(d) / "a-file-where-a-directory-should-be"
        blocker.write_text("")
        home = blocker / "sail"
        assert sail_record.write_sail(_TICKET, home=home, pid=os.getpid()) is None
        assert sail_record.clear_sail(home) is False
        assert sail_record.read_sail(home)["verdict"] == "DEAD"
        assert sail_record.derived_phase(_TICKET, home=home) is None


def test_the_write_is_atomic_and_leaves_no_temp_behind():
    with tempfile.TemporaryDirectory() as d:
        home = Path(d) / "sail"
        path = sail_record.write_sail(_TICKET, home=home, pid=os.getpid())
        assert path and path.exists(), path
        assert sorted(p.name for p in home.iterdir()) == [sail_record.RECORD_NAME], \
            "a temp file survived the write — a reader could pick it up as a second claim"
        assert sail_record.read_sail(home)["verdict"] == "LIVE"
        assert sail_record.clear_sail(home) is True
        assert sail_record.clear_sail(home) is False, "clearing twice must not lie the second time"


def test_the_session_pid_is_read_from_the_environment_not_from_this_process():
    """Measured 2026-09-08: ``emit`` runs in a ``python3 -c`` subprocess that exits within the
    second. Recording ``os.getpid()`` would record a corpse."""
    before = os.environ.get("CLAUDE_PID")
    try:
        os.environ["CLAUDE_PID"] = "4242"
        assert sail_record.session_pid() == 4242
        os.environ["CLAUDE_PID"] = "not-a-number"
        assert sail_record.session_pid() is None, "a junk env var must not crash the stamp"
        del os.environ["CLAUDE_PID"]
        assert sail_record.session_pid() is None
        # and there is NO fallback to this process's own pid — measured by behaviour, not
        # by grepping the source, because the module's docstring says the words too
        with tempfile.TemporaryDirectory() as d:
            assert sail_record.write_sail(_TICKET, home=Path(d)) is None, \
                "the writer stamped a record with no session to name — the pid it used is "
            assert not list(Path(d).iterdir()), "an unnameable sail left a file behind"
    finally:
        if before is None:
            os.environ.pop("CLAUDE_PID", None)
        else:
            os.environ["CLAUDE_PID"] = before


def test_a_ticket_carrying_crossing_stamps_and_a_terminal_clears_it():
    """END TO END THROUGH ``emit``, because the whole design decision was to hang the record
    on the door every voyage already rides rather than on a second discipline nobody calls."""
    before_pid, before_home = os.environ.get("CLAUDE_PID"), sail_record.instance_home
    with tempfile.TemporaryDirectory() as d:
        home = Path(d) / "sail"
        try:
            os.environ["CLAUDE_PID"] = str(os.getpid())
            sail_record.instance_home = lambda instance=0: home

            summons = "code-seam@v2: [THINKME] -> TICKETME -> BUILDME -> PROVEME -> PROVED"
            crossed = transitions.emit(summons, "TICKETME", ticket=_TICKET)
            assert sail_record.read_sail(home)["verdict"] == "LIVE", "the crossing did not stamp"
            assert sail_record.derived_phase(_TICKET, home=home) == "in-process"

            # a crossing into a terminal ends the voyage, and the phase must not survive it
            dropped = transitions.emit(crossed, "DROPPED", ticket=_TICKET)
            assert transitions.is_terminal(transitions.parse_workflow(dropped).here)
            assert sail_record.read_sail(home)["verdict"] == "DEAD", "the terminal left a claim"
        finally:
            sail_record.instance_home = before_home
            if before_pid is None:
                os.environ.pop("CLAUDE_PID", None)
            else:
                os.environ["CLAUDE_PID"] = before_pid


def test_a_ticketless_crossing_stamps_nothing_and_an_unwritable_home_still_crosses():
    before_pid, before_home = os.environ.get("CLAUDE_PID"), sail_record.instance_home
    with tempfile.TemporaryDirectory() as d:
        home = Path(d) / "sail"
        summons = "code-seam@v2: [THINKME] -> TICKETME -> BUILDME -> PROVEME -> PROVED"
        try:
            os.environ["CLAUDE_PID"] = str(os.getpid())
            sail_record.instance_home = lambda instance=0: home
            assert transitions.emit(summons, "TICKETME"), "the ticketless crossing failed"
            assert sail_record.read_sail(home)["verdict"] == "DEAD", \
                "a crossing that names no ticket stamped a claim about one"

            # and now the same crossing with instance-space unreachable
            blocker = Path(d) / "blocked"
            blocker.write_text("")
            sail_record.instance_home = lambda instance=0: blocker / "sail"
            out = transitions.emit(summons, "TICKETME", ticket=_TICKET)
            assert transitions.parse_workflow(out).here == "TICKETME", \
                f"the crossing was lost to a failed side effect: {out}"
        finally:
            sail_record.instance_home = before_home
            if before_pid is None:
                os.environ.pop("CLAUDE_PID", None)
            else:
                os.environ["CLAUDE_PID"] = before_pid


def test_no_ticket_in_the_live_corpus_carries_a_stored_in_process():
    """The claim is about the world, so the world answers it. This is the invariant, not a
    snapshot: the count of tickets may move every day, the count carrying a stored runtime
    claim may never leave zero."""
    stored, seen = [], 0
    for path in sorted(_TICKETS.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            phase = transitions.parse_workflow(doc["workflow_and_state"]).phase
        except Exception:
            continue
        seen += 1
        if phase == "in-process":
            stored.append(path.name)
    # PROSE IS NOT A CLAIM: the first cut of this tooth grepped the raw text and reddened on
    # 54f519a1f728, whose *intention* quotes the string. The measure is the parsed CURSOR.
    assert seen >= 100, f"the corpus walk found only {seen} tickets — a vacuous green"
    assert not stored, f"a runtime claim was committed to a shared file: {stored}"


def test_the_starttime_field_is_pinned_to_WALL_CLOCK_not_merely_self_consistent():
    """THE INDEX IS MEASURED AGAINST THE WORLD, NOT AGAINST ITSELF.

    FOUND BY MUTATION, 2026-09-08, while answering this voyage's chart: the verdict door
    requires a ``discriminating_observation`` per criterion — the observation that shows an
    instrument COULD have failed — so ``_STARTTIME_FIELD`` was deliberately pointed one
    field off and this proof still reported 10/10 green. Every other tooth here WRITES the
    record with ``pid_starttime()`` and READS it back with ``pid_starttime()``, so a wrong
    index round-trips perfectly: the recycled-pid tooth only needs the stored number to
    DIFFER from the live one, which ``+1`` guarantees whatever field is being read.

    That is a coin-toss green — green for a reason that cannot regress — and the fix is to
    pin the field to its SEMANTICS: field 22 of ``/proc/<pid>/stat`` is the process start
    time in clock ticks since boot. So ``btime + ticks/HZ`` must land inside the wall-clock
    window in which we ourselves spawned the child. A wrong index lands nowhere near it.
    """
    hz = os.sysconf("SC_CLK_TCK")
    btime = None
    for ln in open("/proc/stat", encoding="utf-8"):
        if ln.startswith("btime "):
            btime = int(ln.split()[1])
            break
    assert btime, "no btime in /proc/stat — the boot clock this tooth measures against"

    before = time.time()
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    after = time.time()
    try:
        ticks = sail_record.pid_starttime(child.pid)
        assert ticks is not None, "pid_starttime returned None for a live child"
        wall = btime + ticks / hz
        assert before - 2.0 <= wall <= after + 2.0, (
            f"_STARTTIME_FIELD is not pointing at /proc stat field 22: the child was spawned "
            f"in [{before:.1f}, {after:.1f}] but the field reads back as wall-clock {wall:.1f} "
            f"({ticks} ticks at {hz}Hz since boot {btime})")
    finally:
        child.kill()
        child.wait()


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failures = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} green")
    sys.exit(1 if failures else 0)
