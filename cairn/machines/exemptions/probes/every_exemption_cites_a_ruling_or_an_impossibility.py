"""WATCHME probe: the-set-grows-or-it-is-a-museum.

The sieve can only judge what the set declares, and NOTHING DISCOVERS AN
EXEMPTION NOBODY ENTERED. So the failure this probe exists to catch is not a bad
justification — the sieve already reds those — it is the set standing still while
the code keeps growing new places a check declines to run. A set that never grows
reads green forever and means nothing.

The measurement, from the ticket's horizon: site count against pass count, on the
beat. A coarse sweep finds exemption-SHAPED constructs in the corpus; anything it
finds that is neither declared in the set nor acknowledged below is a candidate
nobody has triaged, and the probe fires carrying it.

THE ACKNOWLEDGED LIST IS CHECKED IN ON PURPOSE. The sweep is coarse and will
match things that are not exemptions — measured 2026-09-10, `_EXEMPT_IN = 4` in
the harbor_master clearance probe is a RATIO THRESHOLD, not a site. Dismissing a
candidate therefore costs a commit a reader can see and argue with, rather than a
marker the probe writes to itself in instance-space, which would let the sweep go
quiet by its own hand.

Ticket: 892a0f9cd925-an-exemption-cites-a-ruling-or-an-impossibility.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from cairn.tools.base.probe import Probe

_REPO = Path(__file__).resolve().parents[4]
_SET = _REPO / "cairn" / "machines" / "exemptions" / "exemption_set.json"

# Exemption-shaped constructs. Coarse ON PURPOSE — a pattern narrow enough to
# match only today's eight sites would find nothing new, which is the one thing
# this probe is for.
_SHAPE = re.compile(r"(_EXEMPT|EXEMPT_|SKIP_INSTRUMENT|exemption_of)")

# Swept files under these segments are instruments or the component itself, and
# a hit there is about an exemption rather than being one.
_NOT_A_SITE = ("/proofs/", "/machines/exemptions/")

# Candidates measured 2026-09-10 and judged NOT exemption sites, with the reason.
# A line removed from here re-arms the probe for that path; that is the intent.
_ACKNOWLEDGED = {
    "cairn/devices/cairn/machines/harbor_master/probes/clearance_actually_gates.py":
        "_EXEMPT_IN = 4 is a ratio threshold the probe compares against, not a "
        "place any check declines to run",
}


def _declared() -> tuple[set[str], int]:
    try:
        s = json.loads(_SET.read_text(encoding="utf-8"))
        ex = s.get("exemptions") or []
    except Exception:
        return set(), 0
    return {str(e.get("path", "")) for e in ex if isinstance(e, dict)}, len(ex)


def _swept() -> set[str]:
    found: set[str] = set()
    for p in (_REPO / "cairn").rglob("*.py"):
        rel = p.relative_to(_REPO).as_posix()
        if any(seg in "/" + rel for seg in _NOT_A_SITE):
            continue
        try:
            if _SHAPE.search(p.read_text(encoding="utf-8", errors="replace")):
                found.add(rel)
        except OSError:
            continue
    return found


def _measure(context: dict) -> dict:
    declared, count = _declared()
    swept = _swept()
    untriaged = sorted(swept - declared - set(_ACKNOWLEDGED))
    context.update({
        "declared_sites": count,
        "swept_sites": len(swept),
        "acknowledged_non_sites": len(_ACKNOWLEDGED),
        "untriaged": untriaged,
    })
    return context


def _trigger(now, context: dict) -> bool:
    _measure(context)
    return bool(context["untriaged"])


def _carry(context: dict) -> dict:
    if "untriaged" not in context:
        _measure(context)
    n = len(context["untriaged"])
    return {
        "declared_sites": context["declared_sites"],
        "swept_sites": context["swept_sites"],
        "untriaged": context["untriaged"],
        "finding": (
            "%d exemption-shaped construct(s) in the corpus are neither declared "
            "in exemption_set.json nor acknowledged as non-sites — either the set "
            "has fallen behind the code, or the sweep matched something that is "
            "not an exemption and wants a line in _ACKNOWLEDGED saying why" % n
        ) if n else (
            "every exemption-shaped construct in the corpus is either declared "
            "(%d) or acknowledged as a non-site (%d)"
            % (context["declared_sites"], context["acknowledged_non_sites"])
        ),
    }


def _enough(context: dict) -> bool:
    """Never — and that is the point.

    This watches for a class of thing that keeps being written. There is no
    state in which the corpus has finished growing new exemption sites, so a
    probe that could clear itself here would only be recording that nobody had
    added one lately.
    """
    return False


PROBE = Probe(
    why="the exemption sieve reads only what the set declares, and nothing "
        "discovers a site nobody entered. Left alone the set becomes a museum: "
        "eight entries, all green, while the code grows new places a check "
        "declines to run. This fires when the corpus holds an exemption-shaped "
        "construct that is neither declared nor acknowledged.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)
