"""PROBE — is a 1000-line window big enough to still explain anything?

Berth for the WATCHME that ticket ``logger-for-bash`` carries. Berthed here, in ``bin/``,
beside ``logger_for_bash`` itself — the code it watches (``cairn/tools/base/probe.py``: a probe
berths with what it watches, not with the ticket it was compiled from). Destination (i): the
recorder ships with the repo, so its watcher does too.

THE EFFICACY QUESTION, and why no proof can answer it. ``CAIRN_LOGLEN`` defaults to 1000
because Akien named 1000 ("keep the last n entries. default to 1000") — a reasonable number,
chosen before any traffic existed to size it against, which makes it a hypothesis wearing a
default's clothes (Law 3). Eighteen proofs pin that the window is BOUNDED and that the newest
records are the ones kept. Not one of them can say whether 1000 lines still holds the thing
someone came back for, because that depends entirely on traffic that does not exist yet.

THE FAILURE IS ONE-SIDED, which is what makes this cheap. Too big costs a few kilobytes and
harms nobody. Too small destroys the record's whole reason for existing, and — this is the
part that makes it a watch rather than a check — IT IS ONLY EVER DISCOVERED IN HINDSIGHT, at
the moment someone reaches back for a boot the file no longer holds, which is exactly the
moment they cannot afford to discover it. So the discard has to leave a mark on the way out
or the miss is invisible; ``logtrim`` writes one (``logtrim: discarded N lines, window now
starts at <stamp>``), pinned by ``bin/proofs/test_logger_for_bash.py``.

THE MEASURE: CAN THE WINDOW STILL SHOW TWO RUNS? Sharper than "how many hours does it span",
and it needs no clock. A flight recorder earns its keep by answering "what changed between
then and now" — and a window that has turned over and now holds records from a SINGLE process
cannot answer that at all. It has stopped being a record and become a peephole onto the
present, which is the one thing the process could already see. One record per output line
makes this a live risk rather than a theoretical one: a single ``logrun`` over a chatty
command can fill 1000 lines by itself and take every other process's history with it.

WHY TWO NAMESPACES IS A REAL SAMPLE AND NOT HOME FIELD. ``bash`` (interactive, one record per
output line, bursty) and ``boot`` (a launcher, ~8 records per launch, metronomic) are the two
namespaces this repo ships, and their traffic profiles differ by orders of magnitude — which
is the only axis a retention question actually varies along. n=2 across two profiles is
evidence; n=1 on the author's own namespace is the home-field measurement that killed this
system's first probe (``cairn/tools/base/probes/does_optional_mean_never_carried.py``, 2026-07-30).

READS DIRECTORY LISTINGS AND LINE COUNTS on the local disk — no device, no bus, no network.
AUTHORITY: none. It deposits and pokes; moving the default is the OWNER's act (Law 6).
"""

from __future__ import annotations

import os
from pathlib import Path

from cairn.tools.base.address import resolve
from cairn.tools.base.probe import Probe, owning_ticket

DEFAULT_LOGDIR = Path(os.environ.get("CAIRN_LOGDIR")
                      or resolve("instance/logs"))

# The window the recorder defaults to, resolved the way the recorder resolves it. Read from
# the environment rather than hardcoded: the whole point of the watch is that this number is
# expected to MOVE on evidence, and a probe carrying its own stale copy of the value under
# test would keep answering about a window nobody is running (Law 1 — one place the settled
# number lives, even while it is unsettled).
def _window() -> int:
    raw = os.environ.get("CAIRN_LOGLEN") or os.environ.get("loglen") or "1000"
    return int(raw) if raw.isdigit() and int(raw) > 0 else 1000


# A record that cannot show a PREVIOUS run cannot answer "what changed" — the flight
# recorder's entire job. Two is the floor of usefulness, not a target.
_MIN_RUNS = 2

# How many namespaces must have TURNED OVER before either answer is given. Two: both of the
# namespaces this repo ships, each having actually filled its window. Below that the question
# is unexercised and any verdict is taste. The same floor is on both predicates — see _enough.
_ENOUGH_TURNED = 2

_OWNING_TICKET = owning_ticket("logger-for-bash")


def _pids_and_marks(path: Path) -> tuple[int, int, int] | None:
    """(retained_lines, distinct_pids, trim_marks) for one namespace, or None if the file is
    not a record this recorder wrote.

    IDENTIFIED BY GRAMMAR, NOT BY NAME. The log directory holds other things — this box has a
    ``preflight.json`` in it today — and a probe that counted every file as a namespace would
    report a peephole about a file that is not a log. So a file qualifies only if its lines
    parse as ``<stamp>.<pid>: <msg>``; anything else is not this recorder's and not counted."""
    try:
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    lines = text.splitlines()
    if not lines:
        return None
    pids: set[str] = set()
    marks = parsed = 0
    for line in lines:
        stamp, sep, msg = line.partition(": ")
        if not sep:
            continue
        parts = stamp.split(".")
        if len(parts) != 4 or not all(p.isdigit() for p in parts):
            continue
        parsed += 1
        pids.add(parts[3])
        if msg.startswith("logtrim:"):
            marks += 1
    # A stray text file must not read as a namespace with one pid — the shape that would
    # manufacture a peephole finding out of nothing.
    if parsed * 2 < len(lines):
        return None
    return len(lines), len(pids), marks


def survey_the_namespaces(logdir: Path | str | None = None) -> dict:
    """Every namespace under the log directory: how full its window is, how many processes it
    can still speak for, and whether it has visibly cut.

    A namespace has TURNED OVER when its window is full — it holds at least ``_window()``
    lines — or when a surviving ``logtrim:`` mark says so outright. Both, because the mark is
    itself a line and gets trimmed away in its turn, so fullness is the durable half and the
    mark is the corroborating half."""
    root = Path(logdir) if logdir is not None else DEFAULT_LOGDIR
    cap = _window()
    rows = []
    try:
        entries = sorted(root.iterdir())
    except OSError:
        entries = []
    # A NAMESPACE IS A FILE DIRECTLY IN THIS DIRECTORY. Non-recursive on purpose, and measured
    # the same day it was written: a decontamination pre-image parked beside the record read
    # as a second namespace with 54 runs of its own, which is a copy of the evidence counted
    # as more evidence. Anything kept rather than written lives in a subdirectory now, and a
    # subdirectory fails `is_file` in _pids_and_marks — physics, not a name to remember.
    for p in entries:
        if p.name.endswith((".lock", ".json")) or ".trim." in p.name:
            continue
        got = _pids_and_marks(p)
        if got is None:
            continue
        retained, pids, marks = got
        turned = retained >= cap or marks > 0
        rows.append({"namespace": p.name, "retained": retained, "runs": pids,
                     "trim_marks": marks, "turned_over": turned,
                     "peephole": turned and pids < _MIN_RUNS})
    return {"window": cap,
            "namespaces": rows,
            "turned_over": sum(1 for r in rows if r["turned_over"]),
            "peepholes": sum(1 for r in rows if r["peephole"])}


def _survey(context: dict) -> dict:
    return context.get("namespaces") or survey_the_namespaces()


def _trigger(now, context: dict) -> bool:
    """TRUE when enough namespaces have turned over to judge AND at least one of them can no
    longer show a previous run. Both clauses bind: firing below the floor pokes about a
    window nobody has filled, and firing on turnover alone would poke about a record that is
    working exactly as designed."""
    s = _survey(context)
    return s["turned_over"] >= _ENOUGH_TURNED and s["peepholes"] > 0


def _enough(context: dict) -> bool:
    """CLEARED once enough namespaces have turned over AND none has become a peephole — 1000
    survived contact with both traffic profiles, the number is no longer a guess, and a
    standing watch on a settled question is the re-derivation Law 1 refuses.

    THE FLOOR IS ON THIS PREDICATE TOO, and it is written out rather than left as
    ``peepholes == 0`` for one reason: without it the watch clears on a fresh install, where
    no namespace has ever filled and therefore none can be a peephole. That is a watch that
    retires before it could ever fire — the defect this system's first probe shipped with and
    paid for on 2026-07-30. The proof beside this file exhausts the space to show it cannot
    happen here. If 1000 later stops holding, that is a NEW watch carried deliberately."""
    s = _survey(context)
    return s["turned_over"] >= _ENOUGH_TURNED and s["peepholes"] == 0


def _carry(context: dict) -> dict:
    """The datum that rides back: which namespaces went blind, at what window, with the
    per-namespace rows so the owner can size the new number instead of guessing again. A
    POINTER to the ticket, never a copy (Law 6)."""
    s = _survey(context)
    blind = [r["namespace"] for r in s["namespaces"] if r["peephole"]]
    return {"finding": "the retention window has turned a record into a peephole",
            "blind": blind,
            "window": s["window"],
            "rows": s["namespaces"],
            "ticket": _OWNING_TICKET,
            "against_falsifier": "1000 lines was a number chosen before there was traffic to "
                                 "size it against, and the miss it causes is only ever "
                                 "discovered by someone who already needed the lost record",
            "suggests": "raise CAIRN_LOGLEN for the named namespaces — the per-namespace rows "
                        "are here so the new number comes off the evidence rather than off "
                        "another guess; a namespace is just an export, so the two can differ"}


# THE HORIZON — the same placeholder for the same reason, pointed at rather than copied: the
# full why, and the tracked debt to re-tune it once the beat is a real number, is written once
# at cairn/tools/base/probes/does_optional_mean_never_carried.py.
_HORIZON = 1000

PROBE = Probe(
    why="is 1000 lines a window that still explains anything — or does a record that has "
        "turned over now speak for a single live process and nothing before it?",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
