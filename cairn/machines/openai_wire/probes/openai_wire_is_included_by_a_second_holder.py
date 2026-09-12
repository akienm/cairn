"""PROBE — is openai_wire included by a SECOND holder, or did "anybody can include it" stay
a claim with one taker?

Berth for the WATCHME that ticket ``76639374d9f9`` (openai-wire-is-a-machine-anybody-can-
include) carries. Berthed beside ``cairn/machines/openai_wire`` because that is WHAT IT
WATCHES.

WHAT IT MEASURES. Akien, 2026-09-11: *"if you build it as it's own machine, then anybody
can include it."* The machine was built on that word. The world confirms or kills the word by
one count: how many DISTINCT components in class-space import ``cairn.machines.openai_wire``
from their own code. The count is read off the same import graph the sieve builds
(``import_sieve.import_graph``), so the probe costs one walk and no new instrument.

WHAT COUNTS AS A HOLDER, and it is deliberately narrow:
  - a component is its first two path segments under ``cairn/`` (``devices/<name>`` or
    ``machines/<name>`` or ``tools/<name>``) — a device's nested machine counts for the
    device, because the device is who assembled it;
  - the machine's own tree does not count — a thing including itself proves nothing;
  - proofs/ and probes/ do not count — an instrument that imports what it measures is not a
    holder of it (this very file imports nothing from the machine for that reason).

ENOUGH is TWO. One holder forever is the FINDING, not a pass: the generality was paid for and
never collected, and the honest disposition would have been to build the translation inside
hermes_shim. So the watch does NOT clear on a timer; it clears on the second holder or it
stands as a standing question, and the ticket's own watchme spec says so.

TRIGGER on the first holder — that is the moment the count starts meaning something (zero
holders is a machine nobody has finished wiring, which is cb97524c0e8e's business, not a
finding here). Pokes harbor_master with the roster, the same as its siblings.

AUTHORITY: none. This probe deposits and pokes; deciding that a one-holder machine should be
folded back into its holder is the owner's act (Law 6).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.tools.base.probe import Probe, once, owning_ticket
from cairn.tools.import_sieve import sieve as import_sieve

_OWNING_TICKET = "openai-wire-is-a-machine-anybody-can-include"
_MODULE = "cairn.machines.openai_wire"
_OWN = os.path.join("machines", "openai_wire")
_ENOUGH = 2
_CLASS_ROOT = Path(__file__).resolve().parents[3]   # .../cairn (the package root the graph walks)


def _holder_of(rel_path: str) -> str | None:
    """'devices/x/machines/y/z.py' -> 'devices/x'; 'machines/q/a.py' -> 'machines/q'; None
    for an instrument (proofs/, probes/), a file at the root, or the machine's own tree."""
    parts = rel_path.split(os.sep)
    if len(parts) < 3:
        return None
    if "proofs" in parts or "probes" in parts or "proofs_disabled" in parts:
        return None
    holder = os.sep.join(parts[:2])
    if holder == _OWN:
        return None
    return holder


def judge_graph(graph: dict[str, set[str]]) -> dict:
    """The pure judgement, separable from the walk so the proof can feed it a fixture graph."""
    holders: dict[str, list[str]] = {}
    for path, imported in sorted(graph.items()):
        if not any(m == _MODULE or m.startswith(_MODULE + ".") for m in imported):
            continue
        holder = _holder_of(path)
        if holder is None:
            continue
        holders.setdefault(holder, []).append(path)
    return {"holders": holders, "distinct": len(holders)}


def survey_the_corpus(root: Path | None = None) -> dict:
    """The live read: one import-graph walk over class-space."""
    graph = import_sieve.import_graph(str(root or _CLASS_ROOT))
    if not graph:
        raise import_sieve.HollowScan("the import graph is empty — the walk did not read the tree")
    return judge_graph(graph)


def _corpus(context: dict) -> dict:
    return once(context, "corpus", survey_the_corpus)


def _trigger(now, context: dict) -> bool:
    """TRUE from the first holder on — the count has started to mean something."""
    return _corpus(context)["distinct"] >= 1


def _enough(context: dict) -> bool:
    """CLEARED at TWO distinct holders: Akien's 'anybody can include it' confirmed by the
    world rather than by its author."""
    return _corpus(context)["distinct"] >= _ENOUGH


def _carry(context: dict) -> dict:
    s = _corpus(context)
    return {"finding": (f"{s['distinct']} distinct holder(s) import {_MODULE} — the watch clears "
                        f"at {_ENOUGH}; one holder standing is the generality paid for and not "
                        "yet collected"),
            "holders": s["holders"],
            "distinct": s["distinct"],
            "enough_at": _ENOUGH,
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "clause (e): a real holder serves a real tool-using turn through "
                                 "this machine; the count of holders is what says building it as "
                                 "a machine paid"}


# Same placeholder horizon, same tracked debt, as the probes beside it: the beat rate is not
# yet a real number; 1000 pulses is "clearly a long standing" until it is.
_HORIZON = 1000

PROBE = Probe(
    why="openai_wire was built as its own machine on Akien's word that anybody can then include "
        "it; the world confirms that word by a count of distinct holders, and two is the number "
        "that says the generality paid — one forever is the finding",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "decompose", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey_the_corpus()
    print(json.dumps({"corpus": s,
                      "would_trigger": _trigger(None, {"corpus": s}),
                      "enough": _enough({"corpus": s})}, indent=2, default=str))
