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

# The window rule: a first guess, adjusted against real need, not a settled law.
DEFAULT_WINDOW = {"kind": "count", "n": 5}


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
    record.setdefault("at", datetime.now().isoformat(timespec="seconds"))
    history = append(read_history(history_path), record)
    _atomic_write(history_path, history)
    state = project(history, window=window)
    _atomic_write(state_path, state)
    return state
