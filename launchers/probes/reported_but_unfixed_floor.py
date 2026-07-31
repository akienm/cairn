"""PROBE — a floor this seam REPORTED but could not fix: does it actually get fixed?

Berth for the WATCHME that ticket ``superclaude-starts-itself`` carries. Berthed here, in
``launchers/``, because that is WHAT IT WATCHES — ``bootstrap.sh`` and ``superclaude``, three
files away. The ticket it was compiled from lives in the commons and this does not follow it
there (``cairn/base/probe.py``: a probe berths with what it watches).

BERTHING DESTINATION (i), NOT (ii) — a correction to what the ticket first said, kept rather
than quietly swapped. The first draft called this "destination (ii)'s first worked example,
an instance-space probe," reasoning from where the DATA lives: the boot log is in
``~/.cairn/``, never in git. That is the wrong question. The rule sorts on WHAT IS WATCHED,
and what is watched is the launcher's design — the tool, which every install of this repo
gets and every install needs working. So it is (i): checked in, beside the code. Reading
instance-space from a class-space berth is not the exception it looks like; it is exactly the
shape ``probe.py`` describes as ordinary — the predicate CLOSES OVER host-local data, the
data never leaves, only the poke crosses. The tell that (ii) was wrong: an instance-space
berth is an absolute path in a ticket's spec, so the WATCHME gate would red on every other
box that cloned the commons. A rule that places a probe where the gate cannot follow is not
placing it.

THE EFFICACY QUESTION, and why it is this one. The seam's whole intention is Akien's:
"it does what it can, then reports to Claude if there are problems so Claude can get them
fixed — it's part of the tool becoming invisible when you use it." The repair half is proved
(``launchers/proofs/``). The REPORTING half is a bet on a human-and-model loop no proof can
reach: that a finding riding in on ``--append-system-prompt`` gets ACTED ON. Its obvious way
to fail is silent and slow — the same finding rides in launch after launch, is scrolled past
every time, and "the tool is invisible" quietly becomes "the tool is ignored." A report
nobody acts on is worse than no report: it costs tokens every launch and buys a feeling of
coverage. That is the failure this watches for.

THE SHARPER SIGNAL IS ``preflight: bypassed``. A launch that used ``--no-preflight`` means
someone routed AROUND the floor check — the rescue hatch fired in anger. It does not trigger
on its own (one bypass is a legitimate rescue, which is what the hatch is for), so it rides
in the carried datum rather than in the predicate, where the owner can weigh it.

READS A WINDOW, NOT A HISTORY — stated because it bounds every number below. The boot log is
trimmed to ``CAIRN_LOGLEN`` lines (default 1000), so a finding that survived twenty launches
before the window opened is invisible here, and the count under-reports by construction. It
can therefore MISS, never invent: a finding this probe reports as surviving N launches
survived at least N. The window's own adequacy is a DIFFERENT watch, carried by ticket
``logger-for-bash`` and berthed at ``bin/probes/retention_window.py``; if that one fires,
this one's numbers are the first thing it invalidates.

AUTHORITY: none, by construction — it deposits and pokes. Re-opening a node whose intention
did not work is the OWNER's act at the register (Law 6).
"""

from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path

from cairn.base.probe import Probe

# The namespace ``superclaude`` exports for its own launch. Resolved the same way the shell
# side resolves it (``launchers/superclaude``) so the probe and the recorder cannot develop
# two opinions about where the record is.
DEFAULT_BOOT_LOG = Path(os.environ.get("CAIRN_BOOT_LOG")
                        or Path.home() / ".cairn" / "logs" / "boot")

# How many launches a finding must SURVIVE before "reported" counts as "not acted on". Three,
# not two: the second launch is often the same session that was just told, still working. By
# the third, the report has been in front of a session twice and the floor is still down.
_PATIENCE = 3

# How many launches must have REPORTED SOMETHING before either answer is given. Below this the
# loop has not been exercised and any verdict is noise. It is >= _PATIENCE on purpose: a floor
# smaller than the patience would make a state where the watch CLEARS on a corpus that could
# never have fired it — the defect ``does_optional_mean_never_carried`` paid for on 2026-07-30,
# and the reason this file states the relationship instead of picking two numbers by taste.
_FLOOR = 5

_OWNING_TICKET = "superclaude-starts-itself"

_UNFIXED = "report: unfixed — "
_BYPASSED = ("preflight: bypassed", "preflight: skipped by --no-preflight")


def _records(path: Path) -> list[tuple[str, str]]:
    """(pid, message) for every parseable record in the retained window.

    A LAUNCH IS A PID. ``superclaude`` is one process per launch and every record it writes
    carries that pid, so the pid is the launch identity — no launch counter to keep in sync,
    and records interleaved from a concurrent shell separate themselves. A line that does not
    parse is skipped rather than guessed at: this is a diagnostic surface reading another
    diagnostic surface, and inventing structure is how a probe reports confidently about
    something it did not measure (Law 3)."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []                      # no record is not a finding — the seam may never have run
    out = []
    for line in text.splitlines():
        stamp, sep, msg = line.partition(": ")
        if not sep:
            continue
        parts = stamp.split(".")
        if len(parts) != 4 or not all(p.isdigit() for p in parts):
            continue
        out.append((parts[3], msg))
    return out


def survey_the_boot_log(path: Path | str | None = None) -> dict:
    """What the retained window says about the report-and-fix loop.

    Reads ONE FILE on the local disk — no device, no bus, no network — so it stays cheap
    enough to sit on a pulse (the shrinking-footprint discipline)."""
    recs = _records(Path(path) if path is not None else DEFAULT_BOOT_LOG)

    launches: set[str] = set()
    reporting: set[str] = set()
    bypassed: set[str] = set()
    by_finding: dict[str, set[str]] = defaultdict(set)

    for pid, msg in recs:
        launches.add(pid)
        if msg.startswith(_UNFIXED):
            finding = msg[len(_UNFIXED):].strip()
            reporting.add(pid)
            by_finding[finding].add(pid)
        elif msg in _BYPASSED or msg.startswith("preflight: skipped by"):
            bypassed.add(pid)

    worst, worst_finding = 0, None
    for finding, pids in by_finding.items():
        if len(pids) > worst:
            worst, worst_finding = len(pids), finding

    return {"launches": len(launches),
            "reporting": len(reporting),
            "bypassed": len(bypassed),
            "worst": worst,
            "worst_finding": worst_finding,
            "distinct_findings": len(by_finding)}


def _survey(context: dict) -> dict:
    return context.get("boot_log") or survey_the_boot_log()


def _trigger(now, context: dict) -> bool:
    """TRUE when the loop has been exercised enough to judge AND some finding has ridden in
    on ``_PATIENCE`` separate launches without being fixed. Both clauses bind: firing below
    the floor pokes the owner about noise, and firing on any repeat at all would poke about a
    session that simply has not gotten to it yet."""
    s = _survey(context)
    return s["reporting"] >= _FLOOR and s["worst"] >= _PATIENCE


def _enough(context: dict) -> bool:
    """CLEARED once the loop has been exercised enough AND nothing survived to the patience
    line — the reported-to-Claude path demonstrably closes, and a standing watch on a settled
    question is the re-derivation Law 1 refuses.

    THE FLOOR IS ON THIS PREDICATE TOO, and that is the whole reason it is spelled out rather
    than left as ``worst < _PATIENCE``. Without it the watch clears on an empty log — zero
    reports, zero survivors, question never asked — which is a watch that retires before it
    can fire. That exact asymmetry killed this system's first probe on its first pulse
    (``cairn/base/probes/does_optional_mean_never_carried.py``, 2026-07-30); it is a known
    shape now, and the proof beside this file exhausts the space to show it cannot recur here.

    If the answer later goes bad, that is a NEW watch a node carries deliberately — not this
    one silently resuming."""
    s = _survey(context)
    return s["reporting"] >= _FLOOR and s["worst"] < _PATIENCE


def _carry(context: dict) -> dict:
    """The datum that rides back: the finding that would not die, how many launches it rode,
    and the bypass count beside it. A POINTER to the ticket, never a copy (Law 6 — the ticket
    belongs to the commons)."""
    s = _survey(context)
    return {"finding": "a reported floor is riding in unfixed, launch after launch",
            "unfixed": s["worst_finding"],
            "survived_launches": s["worst"],
            "counts": s,
            "also": ("%d launch(es) in the window used --no-preflight — the rescue hatch "
                     "firing in anger is the sharper signal, and it is here rather than in "
                     "the trigger because one bypass is a legitimate rescue" % s["bypassed"]),
            "ticket": _OWNING_TICKET,
            "against_falsifier": "the seam reports what it cannot fix, and the report is "
                                 "scrolled past — invisible became ignored",
            "window_caveat": "the boot log is trimmed to CAIRN_LOGLEN lines, so these counts "
                             "are a floor, never a ceiling",
            "suggests": "back-edge superclaude-starts-itself and re-open the reporting half: "
                        "either the report is not reaching a session that can act, or the "
                        "finding is one this seam should be repairing rather than reporting"}


# THE HORIZON — same placeholder, same debt, and deliberately not re-derived. The unit is
# PULSES because the shim counts pulses and a clock is bounded out; nothing pulses cairn/base's
# shim today, so 1000 is honest as "clearly a long standing" and dishonest as a measurement.
# The full why, and the tracked debt to re-tune it once the beat is a real number, is written
# once at cairn/base/probes/does_optional_mean_never_carried.py — pointed at rather than
# copied, because two copies of a placeholder is two things to forget to re-tune (Law 1).
_HORIZON = 1000

PROBE = Probe(
    why="does a floor this seam REPORTED but could not fix actually get fixed — or does the "
        "same finding ride in on --append-system-prompt launch after launch until 'the tool "
        "is invisible' has quietly become 'the tool is ignored'?",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
