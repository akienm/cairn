"""PROBE — does the device column vary with the world?

Berth for the WATCHME that ticket
``probescan-resolves-the-real-shim-not-a-discovered-one`` carries.
Berthed here, beside ``bin/cmd/probescan``, because that is WHAT IT
WATCHES — the device column probescan reports, which is the rung each
device reaches when the postman's own path is walked.

THE QUESTION: does the device column actually VARY across runs, or has
the shim resolution become a static answer?  The ticket's build taught
probescan to resolve REGISTERED shims (from ``shim.py`` on disk) rather
than only discovering them.  That fix is structural and passes a proof
— but a structural fix that produces the same column every time it runs
is the stuck needle back, measured at a different altitude.  Variance is
the live measure: if the column never changes, the resolution has stopped
tracking the world it reports on.

DOES NOT RUN PROBESCAN ITSELF.  Probescan is an instrument run by a hand;
a probe that runs the instrument it watches is the manager smell probescan's
docstring already refuses.  This probe composes the SAME underlying
resolution function (``can_receive``) that probescan composes — the pattern
probescan's own docstring endorses ("if a standing watch is later wanted,
it composes ``scan()`` rather than re-deriving it").  It reads the world
independently on each beat and records what it sees.

CROSS-RUN ACCUMULATION.  Most probes read the world once and answer.  This
one needs a HISTORY of readings, because the question is about variance
ACROSS readings, not about a single snapshot.  The history is a JSONL file
in instance-space, one row per sample.  The file is the probe's only
persistent artifact, and it is the ground_loop's to own (Law 6) — the
device column is a fact about the ground_loop's roster.

AUTHORITY: none. It deposits and pokes; the back-edge that re-opens a node
is the OWNER's act (Law 6).

Ticket: probescan-resolves-the-real-shim-not-a-discovered-one (2026-08-14).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket
from cairn.tools.base.address import instance_path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_OWNING_TICKET = "probescan-resolves-the-real-shim-not-a-discovered-one"
_HORIZON = 1000
_STUCK_NEEDLE = 20
_MIN_SAMPLES_FOR_ENOUGH = 3

_HISTORY = instance_path("cairn") / "machines" / "ground_loop" / "probes" / "device_column_history.jsonl"


def _load_probescan():
    """Import ``bin/cmd/probescan`` — extensionless, so standard import won't find it."""
    import importlib.machinery, importlib.util
    path = str(_REPO_ROOT / "bin" / "cmd" / "probescan")
    loader = importlib.machinery.SourceFileLoader("probescan", path)
    spec = importlib.util.spec_from_loader("probescan", loader, origin=path)
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = path
    spec.loader.exec_module(mod)
    return mod


def _sample_column() -> dict:
    """Build the device column by composing can_receive for each discovered device.

    Returns ``{device_id: rung_string}`` — the same data probescan's receive
    column carries, built from the same function.
    """
    probescan = _load_probescan()
    from cairn.devices.cairn.machines.ground_loop.discovery import device_folders

    devices = sorted({d for d, _ in device_folders(_REPO_ROOT)})
    return {d: probescan.can_receive(d, _REPO_ROOT)["rung"] for d in devices}


def _read_history() -> list[dict]:
    """All stored samples, oldest first."""
    if not _HISTORY.is_file():
        return []
    rows = []
    for line in _HISTORY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _append_sample(column: dict) -> None:
    """Append one sample to the history file."""
    _HISTORY.parent.mkdir(parents=True, exist_ok=True)
    row = {"at": datetime.now(timezone.utc).isoformat(), "column": column}
    with open(_HISTORY, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def _column_key(column: dict) -> str:
    """A hashable string for a column dict, for comparing across runs."""
    return json.dumps(column, sort_keys=True)


def survey() -> dict:
    """The whole measurement: sample the column, store it, and analyse history."""
    column = _sample_column()
    _append_sample(column)

    history = _read_history()
    columns_seen = {_column_key(row["column"]) for row in history}

    changed_devices = set()
    if len(history) >= 2:
        for i in range(1, len(history)):
            prev = history[i - 1]["column"]
            curr = history[i]["column"]
            for dev in set(prev) | set(curr):
                if prev.get(dev) != curr.get(dev):
                    changed_devices.add(dev)

    resolved_then_changed = set()
    for dev in changed_devices:
        for row in history:
            if row["column"].get(dev) == "4-resolved-not-delivered":
                if any(later["column"].get(dev) != "4-resolved-not-delivered"
                       for later in history[history.index(row) + 1:]):
                    resolved_then_changed.add(dev)
                break

    consecutive_identical = 0
    if len(history) >= 2:
        last_key = _column_key(history[-1]["column"])
        for row in reversed(history[:-1]):
            if _column_key(row["column"]) == last_key:
                consecutive_identical += 1
            else:
                break

    return {
        "samples": len(history),
        "distinct_columns": len(columns_seen),
        "changed_devices": sorted(changed_devices),
        "resolved_then_changed": sorted(resolved_then_changed),
        "consecutive_identical": consecutive_identical,
        "current_column": column,
        "stuck_needle": consecutive_identical >= _STUCK_NEEDLE,
    }


def _trigger(now, context: dict) -> bool:
    s = context.get("survey") or survey()
    context["survey"] = s
    if s["stuck_needle"]:
        return True
    if s["distinct_columns"] >= 2 and s["resolved_then_changed"]:
        return True
    return False


def _enough(context: dict) -> bool:
    s = context.get("survey") or survey()
    if s["samples"] < _MIN_SAMPLES_FOR_ENOUGH:
        return False
    if s["stuck_needle"]:
        return False
    if s["distinct_columns"] < 2:
        return False
    if not s["resolved_then_changed"]:
        return False
    return True


def _carry(context: dict) -> dict:
    s = context.get("survey") or survey()
    if s["stuck_needle"]:
        finding = (
            f"STUCK NEEDLE — {s['consecutive_identical']} consecutive identical "
            f"columns across {s['samples']} samples; the resolution has stopped "
            f"tracking the world"
        )
    elif s["distinct_columns"] >= 2 and s["resolved_then_changed"]:
        finding = (
            f"VARIANCE CONFIRMED — {s['distinct_columns']} distinct columns "
            f"across {s['samples']} samples; devices that resolved then changed: "
            f"{', '.join(s['resolved_then_changed'])}"
        )
    elif s["distinct_columns"] >= 2:
        finding = (
            f"VARIANCE WITHOUT RESOLUTION CHANGE — {s['distinct_columns']} "
            f"distinct columns but no device that was at 4-resolved then changed; "
            f"changed devices: {', '.join(s['changed_devices'])}"
        )
    else:
        finding = (
            f"HOLDING — {s['samples']} sample(s), {s['distinct_columns']} "
            f"distinct column(s), waiting for the world to vary"
        )
    return {
        "finding": finding,
        "survey": s,
        "ticket": owning_ticket(_OWNING_TICKET),
    }


PROBE = Probe(
    why="the shim resolution is structural (a proof pins it) but a structural "
        "fix that produces the same column every time it runs is the stuck "
        "needle back — variance across runs is the live measure that the "
        "resolution is tracking the world, not reciting a static answer",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "ground_loop", "kind": "efficacy",
          "ticket": owning_ticket(_OWNING_TICKET),
          "object": "probescans_device_column_varies_with_the_world"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey()
    print(json.dumps({
        "survey": s,
        "would_trigger": _trigger(None, {"survey": s}),
        "enough": _enough({"survey": s}),
        "carry": _carry({"survey": s}),
    }, indent=2, default=str))
