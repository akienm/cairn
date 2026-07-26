"""charter/projector.py — a charter's ``state`` window is COMPILED from its
``history``, never authored by hand.

A charter factors into two files: a bounded ``state`` (a cursor + a WINDOW of recent
history) and an append-only ``history`` (the full voyage log). This module is the
projector — the small tool that regenerates the window from history on every append.

Why it matters (the whole point of the split):
  - state is a PURE FUNCTION of history. It cannot DRIFT from the log because it is
    derived from it — the window is not a second copy anyone maintains. That is what
    makes the split honest (Law 1: the answered question "what is the recent state"
    becomes structure; re-deriving it by reading the whole journal is the defect this
    removes — the same move as inference_domain's compile-once, one scale in).
  - history is APPEND-ONLY (Law 7: a record of truth is never mutated, only appended —
    the shape of db_domain's INSERT-only store). The one write-door is ``append``.
  - the bound is STRUCTURAL, not a discipline: a count window is hard-capped by the
    projector, so the file every mind reads first cannot bloat (Law 4).

Placement is a FILED OPEN EDGE (tickets/charter-state-history-split.json, child b):
the projector does not know or care WHERE history lives — a JSON file today, a
db_domain store later — it operates on the record sequence. Its core is deliberately
storage-agnostic; the thin file layer below is only the today-shape.

The window rule is a GUESS to be adjusted against real need (Law 3 + grow-against-need,
Akien 2026-07-21): count-of-N is the default; since-the-last-gate self-sizes to the
current stretch of work. Neither is settled — ``DEFAULT_WINDOW`` is one turn of a cheap knob.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime

from cairn.base.diagnostic import DiagnosticBase

# The window rule: a first guess, adjusted against real need, not a settled law.
DEFAULT_WINDOW = {"kind": "count", "n": 5}


# ── the shape gate: what a record of truth must carry ────────────────────────
#
# ONE FIELD, AND THE NUMBER IS MEASURED (Law 3, ratified by Akien 2026-07-25). Across all 14
# component histories, 66 records, every author and date:
#
#     at, seq     100%   the door writes these ITSELF — not a schema question
#     standing     98%   65/66; the single record missing it IS the defect this gate closes
#     gate         80%   13 legitimate records lack it — requiring it would invalidate them
#     proof        56%   situational
#     validation   32%   situational
#
# So the universal floor is exactly ``standing`` — the field harbor_master's register actually
# reads, carried by every component since the beginning, and the one whose silent absence let a
# malformed record become permanent (CairnCommons/troubles/append-door-has-no-schema-gate.json).
# Nothing else clears the bar, so nothing else is here.
#
# PER-COMPONENT DECLARED SHAPE IS FILED, NOT BUILT: no component today needs a field beyond the
# floor, so the declaring surface would have zero consumers. It opens when one does, and the
# charter is where it would be declared.
#
# The refusal happens BEFORE any write — a record of truth is permanent, so the only place a bad
# one can be stopped is on the way in (Law 4: the single door is the single door precisely so a
# rule can be enforced in one place; Law 7: the costly direction is accepting it quietly).
UNIVERSAL_REQUIRED = ("standing",)


class RecordRefused(ValueError):
    """The append door turning away a record that no reader could read. Loud, and BEFORE the
    write — the whole point, since history is append-only and cannot be edited afterwards."""


# ── the diagnostic surface at the append door ────────────────────────────────
#
# The append door is THE gate: every component's voyage advances through this one call, so
# instrumenting here instruments every gate progression in Cairn at once — no per-device
# wiring, no scan, no daemon. The progression IS the event (Law 3: the emission is the
# measurement; the shrinking-footprint discipline: event, never poll).
#
# The projector is a module, not a device, so it carries the mechanism every device
# inherits rather than a second one of its own (Law 1 — one emitter, one shape). Import
# stays stdlib-deep: ``DiagnosticBase`` is datetime-only, so the boot-order law holds.
#
# Unwired by default. With no receiver the records HOLD on the surface (never dropped,
# Law 7) — so the instrument is inert until someone attaches, which is the targeted-and-
# temporary discipline the diagnostic charter asks for.
class _AppendDoor(DiagnosticBase):
    @property
    def diagnostic_source(self) -> str:
        return "charter.projector.append_entry"


_door = _AppendDoor()


def set_diagnostic_receiver(receiver) -> None:
    """Attach (or, with ``None``, tear down) the instrument on the append door."""
    _door.set_diagnostic_receiver(receiver)


def held_diagnostics() -> list[dict]:
    """Records emitted while nothing was attached — held, not lost."""
    return _door.held_diagnostics()


# ── the pure core: state is a function of history ────────────────────────────


def next_seq(history: list[dict]) -> int:
    """The next monotonic sequence number — one past the last, 0 for an empty log."""
    return (history[-1]["seq"] + 1) if history else 0


def append(history: list[dict], record: dict) -> list[dict]:
    """Return history with ``record`` appended — the ONLY mutation history admits (Law 7).

    Pure: returns a new list, stamps a monotonic ``seq``, and touches no prior record.
    An in-place edit or a delete is not offered here because a record of truth has neither.
    """
    return [*history, {**record, "seq": next_seq(history)}]


def _window(history: list[dict], rule: dict) -> list[dict]:
    kind = rule.get("kind")
    if kind == "count":
        n = rule["n"]
        return history[-n:] if n > 0 else []
    if kind == "since_gate":
        # From the last gate-marked record (inclusive) to the head; the whole log if the
        # voyage has not hit a gate yet (legitimately short, early on).
        for i in range(len(history) - 1, -1, -1):
            if history[i].get("gate"):
                return history[i:]
        return list(history)
    raise ValueError(f"unknown window rule: {rule!r}")


def project(history: list[dict], *, window: dict = DEFAULT_WINDOW) -> dict:
    """Compile ``state`` from ``history``: the current cursor + a bounded window.

    cursor = the head of the voyage (the last record), or None for an empty log.
    window = the tail per the rule. count = the full length, so the window's
    boundedness stays visible. Deterministic: same history in, same state out — which
    is exactly why the persisted ``state`` can never diverge from the truth.
    """
    return {
        "cursor": history[-1] if history else None,
        "window": _window(history, window),
        "count": len(history),
    }


# ── the today-shape: a thin append-only file + its projected sidecar ─────────


def read_history(path: str) -> list[dict]:
    """Load the append-only history, or an empty log if it does not exist yet."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _atomic_write(path: str, data) -> None:
    """Write JSON via a temp file + rename, so a reader never sees a half-written log."""
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def append_entry(
    history_path: str, state_path: str, record: dict, *, window: dict = DEFAULT_WINDOW
) -> dict:
    """The single write-door: append one record, and the tool regenerates the state.

    "You just append; the tool cleans up" — the caller hands one record; the projector
    grows the append-only history and rewrites the bounded ``state`` sidecar from it. The
    only mutation to history is this append (Law 7); ``state`` is always a fresh projection,
    never hand-edited (any prior ``state`` on disk is overwritten by the truth).
    """
    record = dict(record)
    # THE GATE, before anything is touched. The report is complete on this one pass
    # (I-complete-diagnostic-on-first-pass): what was refused, where it was going, what was
    # required, what was actually present, and why the field matters — so the caller fixes it
    # without a second run.
    missing = [k for k in UNIVERSAL_REQUIRED if not record.get(k)]
    if missing:
        raise RecordRefused(
            f"append refused: record for {history_path!r} is missing {missing} — "
            f"required {list(UNIVERSAL_REQUIRED)}, carried {sorted(record)}. "
            "'standing' is what a component's readers (harbor_master's register) read to "
            "derive where a boat stands; a record without it enters the history unreadable "
            "and CANNOT be edited out afterwards (Law 7 — append-only). "
            "Measured floor: 65/66 records across all 14 histories carry it; the one that "
            "did not is the trouble this gate closes "
            "(CairnCommons/troubles/append-door-has-no-schema-gate.json)."
        )
    record.setdefault("at", datetime.now().isoformat(timespec="seconds"))
    prior = read_history(history_path)
    history = append(prior, record)
    _atomic_write(history_path, history)
    state = project(history, window=window)
    _atomic_write(state_path, state)
    # The gate contact — emitted AFTER the write lands, so the record describes a transition
    # that actually happened. Carries only what this door truthfully knows; whatever the seed
    # asks for and this cannot supply shows up MISSING in the findings, which is the honest
    # signal (a datum invented to make a report look complete is the hollow build, Law 8).
    _door.emit(
        "append_entry",
        pointer=record.get("id") or record.get("ticket") or history_path,
        values={
            "identity": record.get("id") or record.get("ticket"),
            "location": history_path,
            "code": "cairn/charter/projector.py::append_entry",
            # A TRUE expected-vs-actual for this door: the caller asked to stand at a gate;
            # the projection is what the compiled state actually came to rest on. A divergence
            # here means the window rule or the append dropped the caller's move on the floor.
            "expected": record.get("gate"),
            "actual": (state.get("cursor") or {}).get("gate"),
            "fatality": "non-fatal",             # the write landed; a raise never reaches here
            "seq": history[-1].get("seq"),       # assigned by append(), not by the caller
            "entries": len(history),
            "from": (project(prior, window=window).get("cursor") or {}).get("gate") if prior else None,
        },
    )
    return state
