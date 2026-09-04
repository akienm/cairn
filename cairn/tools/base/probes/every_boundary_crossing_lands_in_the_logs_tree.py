"""PROBE — does every boundary crossing land in the logs tree?

Berth for the WATCHME that ticket ``every-boundary-crossing-lands-in-the-logs-tree``
carries. Berthed beside ``cairn/tools/base`` because that is WHAT IT WATCHES: the
emit chokepoint is ``cairn/tools/base/transitions.py``, and every emission should
land a breadcrumb at ``~/.cairn/logs/<device>/<instance>/``.

THE EFFICACY QUESTION: does the floor carry the invariant to devices whose authors
never read this ticket? The proof beside the code settles that the shipped writer
produces one file per emission on the day it ships. Whether a device born AFTER this
ticket logs its crossings without anyone wiring it is the fact the enough clause
watches for.

TWO POPULATIONS COMPARED:

  (a) COMPONENTS THAT EMIT — AST-walked from the source tree, counting
      ``self.emit(...)`` call sites outside proofs (non-recursive per component,
      so a device's count is its own, not a sum of its machines'). This is the same
      predicate the census uses, replicated rather than imported because this probe
      lives at tools/base and the census lives at tools/orient.

  (b) TRAILS ON DISK — devices with at least one ``.json`` file under
      ``~/.cairn/logs/<device>/<instance>/``.

The gap (emitters without trails) is the coverage deficit. A trigger fires when the
gap is non-empty; enough clears when the gap is empty AND coverage has grown past the
baseline that existed when this ticket was cast (2026-08-18: 2 trails against 15
emitters in the recursive count).

FILES ONLY, by construction: both the AST walk (source tree) and the trail walk
(instance-space logs) are filesystem reads — no device, no bus, no network — so
the probe stays cheap enough to sit on a pulse.

AUTHORITY: none. This probe deposits and pokes; closing the gap on a silent emitter
is the owner's act at the floor (Law 6).
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from cairn.tools.base.address import component_dirs, resolve
from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "every-boundary-crossing-lands-in-the-logs-tree"

_TRAILS_AT_CAST = 2


def survey_emitters(*, pkg_root: Path | None = None) -> dict[str, dict]:
    """Walk class-space and count ``self.emit()`` call sites per component.

    Non-recursive per component: a device's count is its OWN ``.py`` files, not
    a sum of its held machines'. Each machine stands on its own count and its own
    trail in the logs tree.

    Returns ``{component_name: {"dir": str, "sites": int}}`` for components with
    at least one site.
    """
    components, _ = component_dirs(pkg_root)
    emitters: dict[str, dict] = {}
    for d in components:
        sites = 0
        for py in sorted(d.glob("*.py")):
            if "proofs" in py.parts or "probes" in py.parts:
                continue
            try:
                tree = ast.parse(py.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "emit"):
                    continue
                val = node.func.value
                if isinstance(val, ast.Name) and val.id == "self":
                    sites += 1
                elif (isinstance(val, ast.Attribute) and val.attr == "debug_sink"
                      and isinstance(val.value, ast.Name) and val.value.id == "self"):
                    sites += 1
        if sites > 0:
            emitters[d.name] = {"dir": str(d), "sites": sites}
    return emitters


def survey_trails(*, roots: dict[str, Path] | None = None) -> dict[str, int]:
    """Walk ``~/.cairn/logs/`` and count ``.json`` trail files per device.

    Returns ``{device_name: file_count}`` for devices with at least one trail.
    """
    logs_root = resolve("instance/logs", roots)
    trails: dict[str, int] = {}
    if not logs_root.exists():
        return trails
    for device_dir in sorted(logs_root.iterdir()):
        if not device_dir.is_dir():
            continue
        count = 0
        for instance_dir in sorted(device_dir.iterdir()):
            if not instance_dir.is_dir():
                continue
            count += len(list(instance_dir.glob("*.json")))
        if count > 0:
            trails[device_dir.name] = count
    return trails


def survey_coverage(*, pkg_root: Path | None = None,
                    roots: dict[str, Path] | None = None) -> dict:
    """Compare components-that-emit against trails-on-disk.

    Returns a dict carrying the two populations, the gap, and corpus-level totals.
    """
    emitters = survey_emitters(pkg_root=pkg_root)
    trails = survey_trails(roots=roots)

    gap = sorted(name for name in emitters if name not in trails)
    covered = sorted(name for name in emitters if name in trails)

    return {
        "emitters": emitters,
        "trails": trails,
        "gap": gap,
        "covered": covered,
        "components_that_emit": len(emitters),
        "trails_on_disk": len(trails),
        "coverage_fraction": (len(covered) / len(emitters)) if emitters else 1.0,
        "hollow": ("the logs root does not exist" if not trails and emitters
                   else None),
    }


def _coverage(context: dict) -> dict:
    return context.get("coverage") or survey_coverage()


def _trigger(now, context: dict) -> bool:
    """TRUE when any component that emits has no trail on disk.

    That is: the gap is non-empty — a component crosses boundaries and nothing
    lands in the logs tree for it. This is the invariant the ticket exists to hold.
    """
    s = _coverage(context)
    if s.get("hollow"):
        return True
    return bool(s["gap"])


def _enough(context: dict) -> bool:
    """CLEARED when the invariant has held across 2+ device births AFTER this ticket.

    The ticket's own ``enough`` names it explicitly: "NOT satisfied by the corpus it
    was written against. Enough when the invariant has held across at least TWO device
    births that came AFTER this ticket landed — a device added later, logging on its
    first run with nobody having wired it." Counted by trails-on-disk exceeding the
    baseline at ticket-cast time (2 trails on 2026-08-18) by at least 2.
    """
    s = _coverage(context)
    if s.get("hollow"):
        return False
    if s["gap"]:
        return False
    return s["trails_on_disk"] >= _TRAILS_AT_CAST + 2


def _carry(context: dict) -> dict:
    s = _coverage(context)
    parts = []
    if s.get("hollow"):
        parts.append(f"the logs tree is HOLLOW — {s['hollow']}")
    if s["gap"]:
        gap_detail = ", ".join(
            f"{name} ({s['emitters'][name]['sites']} emit site(s), "
            f"dir={s['emitters'][name]['dir']})"
            for name in s["gap"])
        parts.append(f"{len(s['gap'])} emitter(s) with no trail on disk: {gap_detail}")

    return {
        "finding": ("; ".join(parts) or
                    "the invariant holds — every emitting component has a trail on disk"),
        "counts": {
            "components_that_emit": s["components_that_emit"],
            "trails_on_disk": s["trails_on_disk"],
            "coverage_fraction": s["coverage_fraction"],
            "gap_count": len(s["gap"]),
        },
        "gap": s["gap"],
        "covered": s["covered"],
        "baseline": {
            "trails_at_cast": _TRAILS_AT_CAST,
            "new_trails_since_cast": s["trails_on_disk"] - _TRAILS_AT_CAST,
        },
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "the ticket's proves_red clause (1): trails-on-disk against "
            "components-that-emit — these are the two counts the carrier requires "
            "as measured values"),
        "suggests": (
            "repair the probe — the logs tree does not exist"
            if s.get("hollow") else
            "read the named emitter(s) in the gap: each is a component whose "
            "self.emit() sites produce transitions that never land a breadcrumb — "
            "the first move is to check whether the component's device class "
            "inherits DiagnosticBase and whether its instance-space logs directory "
            "exists"
            if s["gap"] else
            "the invariant holds — no action needed"
        ),
    }


_HORIZON = 1000

PROBE = Probe(
    why="does every boundary crossing land in the logs tree? — the proof settles "
        "it on the day it ships, and whether the NEXT device carries the invariant "
        "is a fact about the next device, not about the ticket",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    print(json.dumps(_carry({}), indent=2, default=str))
