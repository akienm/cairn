"""PROBE — naming the DENIED capability was supposed to stop the list growing. Did it?

Berth for the WATCHME that ticket ``reachability-replaces-the-allowlist`` carries.
Berthed beside ``cairn/machines/build_inspector`` because that is WHAT IT WATCHES: the fire-path
rule declared at ``inspector._FIRE_PATH``, and the closure that rule is shaken over.

THE CLAIM UNDER WATCH, stated as the relation it actually is. Until 2026-08-12 the
verdict path was guarded by an ALLOWLIST — a literal tuple of the modules inspector.py
was permitted to import, living in its own proof. Every legitimate new dependency cost
one human widening with a dated comment (six in six weeks, measured), and on 2026-08-08
one arrived without the widening: ``cairn.tools.base.nest`` entered the fire path in 047d633
and the tooth read as holding while it was red. The replacement names the DENIED
capability instead, so the innocent need no signature. The bet is that this inverts the
maintenance — the closure may grow freely while the denied set sits still.

That is a claim about the FUTURE, which is why it is here and not in the ticket's
acceptance criteria. Every criterion at that voyage's validate berth could pass on the
day it landed with this bet entirely untested.

THE PAIR, and why it is not symmetric:

  - FIRE on the first GAIN. If the denied set has to grow to keep the tooth honest, the
    ticket's own wrong-shape signal has fired and the node is REFUTED, not dinged — one
    occurrence suffices, exactly as the ruled NEVER at inference_domain's probe. A
    SHRINKING set is not the signal: removing a door that no longer exists costs nobody
    a widening, and reading it as a fire would red the rule for being tidied.
  - CLEAR needs a denominator. Zero growth in the denied set proves nothing if the
    closure never moved either — the instrument had no chance to discriminate, and a
    watch that reports that as health is the misaimed census this corpus already met
    once at the librarian. So the clear demands that TEN distinct modules have entered
    the closure since the baseline below: ten widenings the old rule would have charged
    and this one did not.

THE BASELINE IS PROVENANCE, NOT A TUNABLE — the two sets as they stood at this ticket's
PROVED crossing, 2026-08-12, measured by the same walk this probe runs. The carrier is a
relation between two numbers, so both ends have to be written down; a probe that reported
only today's closure would be reporting a number with nothing to be a delta against.

AUTHORITY: none. This probe deposits and pokes. Re-opening the node when its intention
did not work is build_inspector's act at the register (Law 6).
"""

from __future__ import annotations

import json

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "reachability-replaces-the-allowlist"

# Measured at the PROVED crossing, 2026-08-12. A date and a measurement, not a dial.
_CLOSURE_AT_PROVED = (
    "cairn", "cairn.tools.base", "cairn.tools.base.address", "cairn.tools.base.diagnostic",
    "cairn.tools.base.nest", "cairn.devices.codemonkey.machines.orient.orient", "cairn.devices.codemonkey.machines.verdict.verdict", "cairn.tools.charter",
    "cairn.tools.charter.projector", "cairn.tools.import_sieve", "cairn.tools.import_sieve.sieve",
    "cairn.machines.learning_block", "cairn.machines.learning_block.learning_block", "cairn.tools.orient",
    "cairn.tools.orient.orient", "cairn.machines.skill_block", "cairn.machines.skill_block.skill_block",
)
_DENIED_AT_PROVED = (
    "aiohttp", "cairn.tools.tree.tree", "cairn.devices.db_domain", "cairn.devices.inference_domain",
    "cairn.devices.librarian", "ftplib", "http.client", "httpx", "requests", "socket",
    "telnetlib", "urllib.error", "urllib.request",
)

# The clear's denominator floor: below it, an unchanged denied set is silence, not
# evidence. A hand-set constant is a learns-its-gates IOU, named at the owning ticket's
# horizon rather than solved here — the same debt, and the same disclosure, as the
# inference route probe's _ENOUGH.
_ENOUGH = 10


def survey_the_corpus() -> dict:
    """The live read: today's closure and today's declared denied set.

    Reads the rule from its ONE declaration (``inspector._FIRE_PATH``) rather than
    restating it — a probe carrying its own copy of the set it watches would go green
    against itself while the real set drifted. A walk that comes back empty RAISES
    through import_sieve rather than reporting a clean zero: a 0-file closure reads as
    both 'nothing new entered' and 'nothing was measured', which is the quiet this watch
    exists to end.
    """
    from cairn.machines.build_inspector.inspector import _FIRE_PATH, _REPO_ROOT
    from cairn.tools.import_sieve import sieve

    graph = sieve.import_graph(str(_REPO_ROOT))
    closure = sorted(sieve.module_name(p) for p in sieve.reaches(graph, _FIRE_PATH["start"]))
    return {"closure": closure,
            "denied": sorted(_FIRE_PATH["modules"]),
            "graph_files": len(graph)}


def judge(survey: dict) -> dict:
    """The pure judgement, separable from the read so the proof can feed it fixtures."""
    gained = sorted(set(survey["denied"]) - set(_DENIED_AT_PROVED))
    dropped = sorted(set(_DENIED_AT_PROVED) - set(survey["denied"]))
    entered = sorted(set(survey["closure"]) - set(_CLOSURE_AT_PROVED))
    return {"denied_gained": gained,
            "denied_dropped": dropped,
            "closure_entered": entered,
            "closure_now": len(survey["closure"]),
            "closure_at_proved": len(_CLOSURE_AT_PROVED),
            "denied_now": len(survey["denied"]),
            "denied_at_proved": len(_DENIED_AT_PROVED)}


def _seen(context: dict) -> dict:
    return context.get("judged") or judge(context.get("survey") or survey_the_corpus())


def _trigger(now, context: dict) -> bool:
    """TRUE on the first GAIN — the wrong-shape signal, which refutes rather than dings."""
    return bool(_seen(context)["denied_gained"])


def _enough(context: dict) -> bool:
    """CLEARED when the denied set has not gained AND at least _ENOUGH distinct modules
    have entered the closure since the baseline. The pair shares one variable (the set
    gained or it did not) plus a denominator floor that makes the zero mean something —
    mutually exclusive by construction."""
    s = _seen(context)
    return not s["denied_gained"] and len(s["closure_entered"]) >= _ENOUGH


def _carry(context: dict) -> dict:
    s = _seen(context)
    return {"finding": "the denied set GREW — a capability had to be added to keep the "
                       "fire-path rule honest, which is the wrong-shape signal this "
                       "ticket named: naming the capability was not more general than "
                       "naming the innocent, and the node's claim is refuted",
            "denied_gained": s["denied_gained"],
            "counts": {"denied_at_proved": s["denied_at_proved"],
                       "denied_now": s["denied_now"],
                       "closure_at_proved": s["closure_at_proved"],
                       "closure_now": s["closure_now"],
                       "closure_entered_since": len(s["closure_entered"])},
            "closure_entered": s["closure_entered"],
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the ticket's WRONG-SHAPE SIGNAL, verbatim: 'if the "
                                 "denied set has to GROW to keep the tooth honest, then "
                                 "naming the capability was not more general than naming "
                                 "the innocent and this node's whole claim is refuted' — "
                                 "the gain above is that observation",
            "suggests": "read WHY the entry was added before treating it as a defect. A "
                        "genuinely NEW capability (a second inference transport, a new "
                        "store) is the set growing with the world and is the honest case "
                        "the claim always allowed; an entry added because a module "
                        "slipped into the closure and the rule missed it is the claim "
                        "failing, and the two are told apart by the commit that added it"}


# Same placeholder horizon, same tracked debt, as the probes at cairn/tools/base and
# cairn/devices/inference_domain: the beat rate is not yet a real number.
_HORIZON = 1000

PROBE = Probe(
    why="the allowlist had to be widened by hand for every legitimate dependency and one "
        "arrived without the widening; this rule names the denied capability instead, so "
        "the closure may grow freely while the set sits still — the watch is whether the "
        "set actually sits still, and how much closure growth it sat through",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    # The smoke-fire surface: the live sets and what the pair would do with them now.
    s = survey_the_corpus()
    j = judge(s)
    print(json.dumps({"graph_files": s["graph_files"], "judged": j,
                      "would_trigger": _trigger(None, {"judged": j}),
                      "enough": _enough({"judged": j})}, indent=2))
