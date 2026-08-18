"""PROBE — is the instance address still spelled by hand, now that one owner exists?

Berth for the WATCHME that ticket ``one-owner-for-the-instance-address`` carries. Berthed
here, beside ``cairn/tools/base``, because that is WHAT IT WATCHES — the resolver whose whole claim
is that nobody re-derives the address any more; the ticket it was compiled from stays in
CairnCommons and this probe deliberately does not follow it there.

THE EFFICACY QUESTION, and why it is this one. The ticket's own WRONG says it plainly: "the
resolver becomes an ELEVENTH place a path is built rather than the only one — the sites keep
their hand-spelled copies and the two shapes drift." A resolver is a CONVENIENCE until
something notices the eleventh spelling.

**THIS PROBE NO LONGER OWNS THE RULE, AND THAT IS THE 2026-08-17 CHANGE.** Until then it
carried its own pair of regexes and its own exclusion list, and ``cairn/tools/base``'s charter
said in as many words that nothing REFUSES a further hand-spelled path. Two spellings of one
rule is precisely the defect this ticket is about, so the probe stopped owning a copy: the rule
lives once, at ``cairn/tools/base/address_rule.py``, as an AST predicate over an EXPRESSION,
and this module COMPOSES it. What was measured when the two were compared is worth keeping —
the text scan found 9 hits over 271 files where the AST rule finds 7 over the same tree, and
the two extra were MENTIONS in prose, one of them a sentence in this very file describing what
it looked for. A watcher inside its own corpus measured itself, and the old fix was to exclude
this file BY NAME. Under the rule that exclusion is not needed and is gone: a mention lives in
an ``ast.Constant``, a spelling is an ``ast.BinOp``, and the rule cannot confuse them.

**THE FLOOR IS EMPTY, AND THAT IS ALSO NEW.** It held two named sites, and both of the reasons
it gave for them have since gone stale — which is exactly the thing this rewrite exists to
record, because nothing announced either one:

  - ``cairn/devices/inference_domain/route.py`` was called a standing disagreement between two
    rulings ("machine facts in ~/.cairn/inference/", from a ticket PROVED four days before the
    four-rung ruling existed). It was converted on 2026-08-17: ``hosts.json`` moved to
    ``devices/inference_domain/0/``, byte-identical, and the prose that followed the address —
    the charter, the README, the rules stack, a proof's comment — moved with it.
  - ``cairn/machines/build_inspector/inspector.py`` was called a rung the ladder does not have
    (a device ACROSS instances) whose import allowlist was already red. It is converted too,
    through ``address.resolve("instance/devices")``, which is the rooted-token face of the same
    table — the ladder did have the rung, one level up from the one that was tried. The line
    number this docstring used to name (``:216``) had ALSO drifted to ``:224`` while nobody
    looked, which is why the floor is named by FILE and why a floor at all is a liability.

So the floor is ``()`` and ``_enough`` clears by measuring a clean world rather than by
matching a list. A named floor cannot tell "still true" from "the reason rotted"; an empty one
has nothing to rot.

**A VACUOUS SCAN IS A RED, AND THE RULE NOW RAISES IT.** The count travels with the number of
files actually read, and ``address_rule.scan`` raises ``HollowScan`` rather than returning a
zero — the vacuity check became physics at the producer instead of a condition every reader had
to remember. This module catches it and turns it into a firing: a probe that raised on a pulse
would take the shim's beat with it, and the honest surface for "the instrument stopped working"
is a loud carry, not a traceback in somebody else's loop.

AUTHORITY: none, by construction. This probe deposits and pokes. An eleventh hand-spelled
path is a spec-level fact about whether Akien's reason (II) is holding — "it leaves open the
possibility to expand in the future without rearchitecting that part" — and the back-edge
that re-opens this node is the owner's act at the register (Law 6).
"""

from __future__ import annotations

from cairn.tools.base import address_rule
from cairn.tools.base.probe import Probe, owning_ticket
from cairn.tools.import_sieve import HollowScan

_OWNING_TICKET = "one-owner-for-the-instance-address"

# THE FLOOR IS EMPTY — see the docstring. Kept as a named constant rather than deleted, because
# a floor is still the right shape for this watch: if Akien ever rules a site legitimate, it is
# named HERE, with its reason, instead of being carved out of the rule the whole corpus reads.
_FLOOR_SITES: tuple[str, ...] = ()


def survey_class_space() -> dict:
    """Shake the one rule over class-space. The rule's own vocabulary, plus ``hollow``.

    COMPOSED, NEVER RE-DERIVED: ``address_rule.scan`` is the single spelling of what counts as
    a hand-spelled address, and this function adds only the two things a PROBE needs that a
    rule should not carry — a non-raising surface for the pulse, and the floor comparison.

    Reads files only — no device, no bus, no network, so the probe stays cheap enough to sit on
    a pulse and needs no clock of its own.
    """
    try:
        found = address_rule.scan()
    except HollowScan as e:
        # The producer's red, carried rather than re-raised. See the docstring: a probe that
        # raises on a pulse breaks the beat of everything else hanging off it.
        return {"count": 0, "sites": [], "files_read": 0, "exempted": [],
                "unreadable": [], "hollow": str(e)}
    found["hollow"] = None
    return found


def _site_files(s: dict) -> list:
    """The file halves of the found sites — the floor is named by FILE, since a line number
    moves whenever anything above it is edited and would make the watch fire on nothing.

    The site strings are the rule's (``{"site": "<path>:<line>", "shape": ...}``); reading the
    key rather than assuming a bare string is the same lesson the offload probe learned the
    expensive way — a reader that agrees with itself instead of with the writer proves nothing.
    """
    return [entry["site"].rsplit(":", 1)[0] for entry in s["sites"]]


def _trigger(now, context: dict) -> bool:
    """Fires when the found sites are not exactly the named floor, or when the scan was vacuous.

    THE SECOND HALF IS NOT DECORATION. A scan that read no files reports a count of 0, which
    is indistinguishable from a perfectly clean corpus at exactly the moment the probe has
    stopped working. So an empty scan fires the probe rather than clearing it.
    """
    s = context.get("corpus") or survey_class_space()
    if s["hollow"]:
        return True
    return sorted(set(_site_files(s))) != sorted(_FLOOR_SITES)


def _enough(context: dict) -> bool:
    """Never clears on a single quiet pulse, and never clears on a vacuous one.

    THE SIGNATURE IS A FIX, AND IT IS THE 2026-08-17 FINDING WORTH KEEPING. This read
    ``_enough(now, context)`` from the day it was written, and ``Probe.gathered_enough``
    calls ``self.enough(context)`` with ONE argument — so the first time a shim asked this
    watch whether it had gathered enough, it would have raised TypeError instead of
    answering. It never raised, because nothing beats base's shim on a cadence yet: a probe
    that is armed and structurally unaskable reads exactly like a probe that is armed and
    quiet. Censused across the corpus the same hour: 30 probes carry an ``enough``, and this
    was the only one with the wrong arity — n=1, in the file this ticket owns. The
    corpus-wide physics (probescan already walks every probe and exercises the send and
    receive ends; asking whether the shim can ASK the probe is the third end) is outside
    this ticket's bounds and is a ticket, not a quiet widening.

    The ticket's ``enough`` asks for the count to stand at its floor across THREE consecutive
    pulses that each actually exercised the scan, with the floor accounted for name by name.
    The three-pulse half needs a pulse history this probe cannot see from here — nothing beats
    base's shim on a cadence yet (the wall-clock backing is a filed edge, not built) — so what
    is enforced here is the half that IS measurable: a non-vacuous scan whose sites are
    exactly the named floor. The consecutive-pulse half is a declared debt, not a silent one.
    """
    s = context.get("corpus") or survey_class_space()
    return not s["hollow"] and sorted(set(_site_files(s))) == sorted(_FLOOR_SITES)


def _carry(context: dict) -> dict:
    """What rides back: the count, the named sites, and the files read — all three, because
    a count without its sites is exactly the claim this ticket exists to stop being made.

    ``exemptions_bearing_weight`` rides too, and it is the half a count cannot say: the rule's
    exemption set is CLOSED AT TWO (the module that owns the address, and any file under a
    ``proofs/`` directory), and ``scan`` records a member only when it actually caught
    something. A member that stopped appearing is one the rule no longer needs, and this is
    where a reader would see that.
    """
    s = context.get("corpus") or survey_class_space()
    return {
        "finding": (f"the scan is HOLLOW — {s['hollow']}" if s["hollow"] else
                    f"{s['count']} hand-spelled instance-space path(s) outside the resolver, "
                    f"over {s['files_read']} files"),
        "counts": s,
        "floor_expected": list(_FLOOR_SITES),
        "exemptions_bearing_weight": s["exempted"],
        "unreadable": s["unreadable"],
        "rule": "cairn/tools/base/address_rule.py — the one spelling; this probe composes it",
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "measure (b): the address rule shaken across non-proof code "
                             "returns only the resolver, plus any site Akien has named",
        "suggests": ("repair the probe — a vacuous scan cannot report anything" if s["hollow"]
                     else "read the new site: either it is a rung the ladder does not have, or "
                          "it is a caller that did not adopt the resolver, and those want "
                          "different answers"),
    }


# THE HORIZON. Same unit and same honesty as the sibling probes in this folder: PULSES,
# because the shim counts pulses and a clock is bounded out — and nothing beats base's shim on
# a cadence today, so the loudness rides the read-side door (``BaseShim.overdue()``) alone.
# 1000 is "clearly a long standing" against any beat rate we would plausibly pick; it is
# honest as a placeholder and dishonest as a measurement, and it must be re-tuned when the
# beat becomes a real number.
_HORIZON = 1000

PROBE = Probe(
    why="is the instance address still spelled by hand? — a resolver nothing enforces is a "
        "convenience, and the way this design fails is that the sites keep their copies and "
        "the two shapes drift",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    import json
    print(json.dumps(_carry({}), indent=2, default=str))
