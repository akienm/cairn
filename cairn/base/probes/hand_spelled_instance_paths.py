"""PROBE — is the instance address still spelled by hand, now that one owner exists?

Berth for the WATCHME that ticket ``one-owner-for-the-instance-address`` carries. Berthed
here, beside ``cairn/base``, because that is WHAT IT WATCHES — the resolver whose whole claim
is that nobody re-derives the address any more; the ticket it was compiled from stays in
CairnCommons and this probe deliberately does not follow it there.

THE EFFICACY QUESTION, and why it is this one. The ticket's own WRONG says it plainly: "the
resolver becomes an ELEVENTH place a path is built rather than the only one — the sites keep
their hand-spelled copies and the two shapes drift." A resolver is a CONVENIENCE until
something notices the eleventh spelling. Nothing in the system refuses one: no schema, no
gate, no import rule. So the honest state after this build is a tracked debt with a watch on
it, and this is the watch.

**AN EMPTY SCAN IS A RED, NOT A GREEN.** The count travels with the number of files actually
read. A scan that walked zero files reports zero hand-spellings, which is the vacuous green
this probe's ``enough`` was written against — the same defect as a leak scan that passes
because it searched the wrong tree.

THE FLOOR IS 2, AND THE TICKET SAID 1. Written down here because the discrepancy is the most
useful thing this probe knows on its first pulse. The ticket's falsifier (b), authored at
cast, predicted the scan would return "only the resolver module itself, plus the dispositioned
inference_domain site". Measured at build (2026-08-12), it returns a third:

  - ``cairn/inference_domain/route.py:44`` — DISPOSITIONED, and not a stray. A PROVED ticket
    (``the-inference-proxy-is-a-rules-stack``, closed 2026-08-08) says in its own intention
    "machine facts in ~/.cairn/inference/", four days before the four-rung ruling existed.
    That is a disagreement between two rulings and its resolution is Akien's, not a probe's.
  - ``cairn/build_inspector/inspector.py:216`` — NOT dispositioned, and the finding this
    build surfaced. It was in the cast's census of ten and was dropped from the conversion
    piece at decompose, silently, because a piece's file list is prose and nothing checks it
    against the survey. Two things keep it unconverted rather than one: it addresses a DEVICE
    ACROSS INSTANCES (``devices/chart``, no instance segment), for which none of the three
    rungs this build defines is the right shape; and its import allowlist is ALREADY RED with
    an undecided entry (the live trouble about ``cairn.base.nest``), so admitting a second
    module there would bury one undecided admission under another.

AUTHORITY: none, by construction. This probe deposits and pokes. An eleventh hand-spelled
path is a spec-level fact about whether Akien's reason (II) is holding — "it leaves open the
possibility to expand in the future without rearchitecting that part" — and the back-edge
that re-opens this node is the owner's act at the register (Law 6).
"""

from __future__ import annotations

import re
from pathlib import Path

from cairn.base.probe import Probe, owning_ticket

_CLASS_SPACE = Path(__file__).resolve().parents[2]      # .../cairn/  (the package)

_OWNING_TICKET = "one-owner-for-the-instance-address"

# EXCLUDED, and each for its own reason:
#   address.py — the resolver is the ONE place the address is allowed to be spelled, so
#     counting it would make the floor permanently non-zero for the wrong reason.
#   this file — a probe that must SAY what it looks for spells the pattern in its own prose,
#     and its first live fire proved it: the run reported 3 sites, and the third was line 146
#     of this module, the sentence describing measure (b). That is the sibling probe's lesson
#     arriving in a new costume (``does_optional_mean_never_carried`` counted its own owning
#     ticket and read "the author participates" as evidence that authors participate): a
#     watcher inside its own corpus measures itself. Caught at n=1, by firing it.
_EXCLUDED = ("address.py", Path(__file__).name)

# THE FLOOR, MEASURED AT BUILD rather than predicted: the two sites above. Named, not
# tolerated — a bare number would let a THIRD site appear and the count still read "expected"
# if one of these two were ever converted. The watch is on the NAMES.
_FLOOR_SITES = (
    "cairn/inference_domain/route.py",
    "cairn/build_inspector/inspector.py",
)

# The same two spellings that produced the cast's census of ten. Its blind spot rides with it
# and is declared rather than fixed: a path built by string concatenation from a variable, or
# by a dynamic join, is invisible to both. A stronger scan is a real improvement and is not
# this ticket's.
_HOME_DOT_CAIRN = re.compile(r"Path\.home\(\)\s*/\s*[\"']\.cairn[\"']")
_EXPANDUSER = re.compile(r"expanduser\(\s*[\"']~/\.cairn")


def survey_class_space() -> dict:
    """Count hand-spelled instance-space paths in class-space source, WITH the number of files
    read. Reads files only — no device, no bus, no network, so the probe stays cheap enough to
    sit on a pulse and needs no clock of its own.

    Proofs are excluded: a proof that asserts the refusal of a bare absolute path has to spell
    one, and counting it would make the corpus permanently dirty by its own teeth.
    """
    sites, scanned = [], 0
    for p in sorted(_CLASS_SPACE.rglob("*.py")):
        if "/proofs/" in str(p) or p.name in _EXCLUDED:
            continue
        try:
            src = p.read_text(encoding="utf-8")
        except OSError:
            continue                     # unreadable is not "clean" — it is also not a site
        scanned += 1
        for pattern in (_HOME_DOT_CAIRN, _EXPANDUSER):
            for m in pattern.finditer(src):
                line = src.count("\n", 0, m.start()) + 1
                rel = str(p.relative_to(_CLASS_SPACE.parent))
                sites.append(f"{rel}:{line}")
    return {"count": len(sites), "sites": sorted(set(sites)), "files_scanned": scanned}


def _trigger(now, context: dict) -> bool:
    """Fires when the count is above the named floor, or when the scan was vacuous.

    THE SECOND HALF IS NOT DECORATION. A scan that read no files reports a count of 0, which
    is indistinguishable from a perfectly clean corpus at exactly the moment the probe has
    stopped working. So an empty scan fires the probe rather than clearing it.
    """
    s = context.get("corpus") or survey_class_space()
    if s["files_scanned"] == 0:
        return True
    return sorted(set(_site_files(s))) != sorted(_FLOOR_SITES)


def _site_files(s: dict) -> list:
    """The file halves of the found sites — the floor is named by FILE, since a line number
    moves whenever anything above it is edited and would make the watch fire on nothing."""
    return [site.rsplit(":", 1)[0] for site in s["sites"]]


def _enough(now, context: dict) -> bool:
    """Never clears on a single quiet pulse, and never clears on a vacuous one.

    The ticket's ``enough`` asks for the count to stand at its floor across THREE consecutive
    pulses that each actually exercised the scan, with the floor accounted for name by name.
    The three-pulse half needs a pulse history this probe cannot see from here — nothing beats
    base's shim on a cadence yet (the wall-clock backing is a filed edge, not built) — so what
    is enforced here is the half that IS measurable: a non-vacuous scan whose sites are
    exactly the named floor. The consecutive-pulse half is a declared debt, not a silent one.
    """
    s = context.get("corpus") or survey_class_space()
    return s["files_scanned"] > 0 and sorted(set(_site_files(s))) == sorted(_FLOOR_SITES)


def _carry(context: dict) -> dict:
    """What rides back: the count, the named sites, and the files scanned — all three, because
    a count without its sites is exactly the claim this ticket exists to stop being made."""
    s = context.get("corpus") or survey_class_space()
    vacuous = s["files_scanned"] == 0
    return {
        "finding": ("the scan read NO FILES — the count is not a measurement"
                    if vacuous else
                    f"{s['count']} hand-spelled instance-space path(s) outside the resolver"),
        "counts": s,
        "floor_expected": list(_FLOOR_SITES),
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "measure (b): a grep for Path.home() with '.cairn' and for "
                             "expanduser('~/.cairn') across non-proof code returns only the "
                             "resolver, plus the dispositioned sites",
        "suggests": ("repair the probe — a vacuous scan cannot report anything" if vacuous
                     else "read the new site: either it is a rung the ladder does not have "
                          "(the build_inspector case — a device across instances), or it is "
                          "a caller that did not adopt the resolver, and those want "
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
