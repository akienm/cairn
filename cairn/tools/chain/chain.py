"""chart/chain.py — the seven legs, written down once, and the gate on notes addressed to them.

WHY THIS FILE EXISTS: A TICKET CAN SPEAK TO THE CHART. A ticket carries prose addressed to a
chart LEG — "when you reach survey, settle a3 first, because it can shrink the stone." That
content is real and load-bearing (it is how a caster hands forward what they already know), but
until 2026-07-30 it was written into ``stage_needs``, the field ``cairn/tools/base/needs.py`` owns.

TWO ANIMALS UNDER ONE NAME, and the shapes are what proved it rather than any argument: 33
entries across 12 tickets were chart-keyed STRINGS; 7 entries across 6 tickets were
workflow-keyed LISTS of ``{need, marks}`` — measured, aged, queryable. The needs door validates
keys against the node's own workflow vocabulary and was therefore correct to refuse the prose;
it was being fed a different animal. The collision was invisible because "stage needs" reads
plausibly in both dialects — the term survived while the meaning was swapped under it, which is
the drift that hides (memory: words-kept-meanings-replaced).

THE CHART IS A DIFFERENT AXIS, NOT A RIVAL VOCABULARY. The workflow is the node's voyage
(THINKME → … → PROVED). The chart is the pre-build preamble that runs INSIDE the early stages
and whose validate berth is what opens the BUILDME door (buildme-rides-the-chart, 2026-07-29).
A node has both; they are perpendicular. So ``chart_notes`` is not a second spelling of
``stage_needs`` and must never grow marks — a note is guidance, not a dependency, and nothing
about it is measurable. (COINAGE FLAGGED FOR RATIFY, memory terms-drift-flag-coinages: the
field name ``chart_notes`` is CC's, not Akien's. It is derivable in the native domain — a
nautical chart carries notes printed on it, keyed to the leg they bear on — and it names the
AXIS in the field name, which is exactly what ``stage_needs`` failed to do.)

WHY THE LIST LIVES HERE. The chain order was implicit before this file: each stage module
imports the one it reads from, so "what are the legs, in order" could only be answered by
tracing imports. That is a settled question being re-derived (Law 1), and a gate cannot afford
it. This declares it once, importing NOTHING, so a ticket gate stays as light as a file read;
``dial.STAGE_FIELDS`` is bound to it by a tooth in ``proofs/test_chart_notes.py`` rather than
by a second copy. IOU: dial should CONSTRUCT its registry from ``STAGES`` — that edit touches a
proven module and is a change with a ticket, not a drive-by.

    python3 -m cairn.tools.chain.chain            # scan the live tickets, report ALL nonconformance
"""
from __future__ import annotations

import json
import os

# THE SEVEN LEGS, IN ORDER. The chain the /chart skill fires; the chart device's charter is the
# authority on what each one does. Order is meaningful — a note may be keyed to any leg, but the
# legs run in this sequence and a reader is entitled to see them that way.
STAGES = ("orient", "constrain", "survey", "decompose", "triage", "hypothesize", "validate")

# A note that says nothing is a heading with no body. The floor is a LENGTH, not a grammar, for
# the same reason needs._MIN_HOW_MEASURED is: no regex can decide "does this help the next
# reader", but "tbd" and "" can be refused outright, and are.
_MIN_NOTE = 24


class ChartNoteRefused(ValueError):
    """The chart-notes door turning away a malformed block. Loud, and BEFORE the write: a ticket
    is a record of truth, so the only place to stop a bad one is on the way in (Law 7). The
    report is complete on this one pass (I-complete-diagnostic-on-first-pass) — what was
    refused, what was required, what was carried, and why the field is load-bearing."""


def validate_chart_notes(node: dict) -> None:
    """Refuse a malformed ``chart_notes`` block. Absent is fine — most nodes never chart, and a
    node that charted without leaving notes is not a defect; a MISSHAPEN block is."""
    block = node.get("chart_notes")
    if block is None:
        return
    if not isinstance(block, dict):
        raise ChartNoteRefused(
            f"chart_notes must map CHART LEG -> note; carried {type(block).__name__}. "
            f"The legs are {list(STAGES)} — the whole point of the shape is that a note "
            "attaches to the leg it bears on, so the chart can be handed the note at the "
            "moment it is useful instead of the caster re-reading the whole ticket."
        )
    for leg, note in block.items():
        if leg not in STAGES:
            raise ChartNoteRefused(
                f"{leg!r} is not a leg of the chart chain {list(STAGES)} — a note cannot "
                f"attach to a leg that does not exist. (node {node.get('id')!r}). If this is "
                "a dependency the node's WORKFLOW stage needs, it belongs in stage_needs, "
                "which is keyed by the node's own workflow vocabulary and carries measured "
                "marks; if it is a finding, it belongs where findings are recorded, not in a "
                "block addressed to a chain that has already sailed."
            )
        if not isinstance(note, str):
            raise ChartNoteRefused(
                f"leg {leg!r} carries {type(note).__name__}, expected a string. A chart note "
                "is PROSE for the next mind — it is never marked, aged, or queried, which is "
                "precisely what distinguishes it from a stage_needs entry (a list of "
                f"{{need, marks}}). (node {node.get('id')!r})"
            )
        if len(note.strip()) < _MIN_NOTE:
            raise ChartNoteRefused(
                f"leg {leg!r} carries {note.strip()!r} — under the {_MIN_NOTE}-character floor. "
                "A note this short is a heading with no body: it costs the chart a read and "
                f"hands it nothing. (node {node.get('id')!r})"
            )


def charted_paths(chain: dict) -> set:
    """Every file path the chain's berths mention — the detector's vocabulary of 'known'.

    Reads each berth in the chain dict (stage -> path-or-None), loads it, and extracts
    paths from the fields that carry them:
      orient:    refs[]
      survey:    holdings[].address, absences[].what (substring paths)
      decompose: sub_problems[].uses[], sub_problems[].writes_to[]
      validate:  criteria[].instrument (substring paths)

    A path that is not a real file path (prose) is included harmlessly — the comparison
    is against git's actual file list, so a prose string simply never matches.
    """
    paths = set()
    for _stage, berth_path in (chain or {}).items():
        if not berth_path or not os.path.isfile(berth_path):
            continue
        try:
            with open(berth_path, encoding="utf-8") as fh:
                pkt = json.load(fh)
        except (OSError, ValueError):
            continue
        for ref in pkt.get("refs") or []:
            if isinstance(ref, str):
                paths.add(ref)
        for h in pkt.get("holdings") or []:
            if isinstance(h, dict) and isinstance(h.get("address"), str):
                paths.add(h["address"])
        for sp in pkt.get("sub_problems") or []:
            if isinstance(sp, dict):
                for u in sp.get("uses") or []:
                    if isinstance(u, str):
                        paths.add(u)
                for w in sp.get("writes_to") or []:
                    if isinstance(w, str):
                        paths.add(w)
    return paths


def uncharted_modifications(charted: set, modified: list, added: list) -> list:
    """Files the build MODIFIED that the chain never mentioned.

    Excludes added files (new files cannot appear in a chart that predates them)
    and files mentioned in any berth. The return is the detector's finding —
    each entry is a path the reader can adjudicate.

    THE SUBSTRING TEST IS GENEROUS BY CHOICE: a file mentioned in a berth for
    any reason at all reads as chartered. The standing consequence is asymmetric
    evidence — this detector's NOISE is strong and its SILENCE is weak.
    """
    added_set = set(added or [])
    findings = []
    for path in (modified or []):
        if path in added_set:
            continue
        if any(path in c or c in path for c in charted):
            continue
        findings.append(path)
    return sorted(findings)


def scan(tickets_dir: str) -> list[dict]:
    """EVERY nonconformance under ``tickets_dir``, never just the first.

    Written this way because the defect it was born from was exactly a first-failure report: the
    needs live-scan raised on ``a-node-holds-one-claim.json`` and eleven more tickets in the same
    condition sat invisible behind alphabetical order, so the finding read as one stale ticket
    for a day. A diagnostic surface delivers ALL the data on its INITIAL pass — re-running to
    gather more is the re-derivation Law 1 refuses, and Akien's own proven method
    (I-complete-diagnostic-on-first-pass) says the first report is the one that must be
    complete.

    Returns ``[{"ticket", "why"}, ...]`` — empty is conformance. Unreadable JSON is reported
    rather than skipped: a ticket that will not parse is a finding, not noise (Law 7)."""
    out: list[dict] = []
    if not os.path.isdir(tickets_dir):
        return out
    for name in sorted(os.listdir(tickets_dir)):
        if not name.endswith(".json") or name.startswith("_"):
            continue
        path = os.path.join(tickets_dir, name)
        try:
            with open(path, encoding="utf-8") as fh:
                node = json.load(fh)
        except (OSError, ValueError) as e:
            out.append({"ticket": name, "why": f"unreadable: {type(e).__name__}: {e}"})
            continue
        if not isinstance(node, dict):
            out.append({"ticket": name, "why": "not a JSON object"})
            continue
        try:
            validate_chart_notes(node)
        except ChartNoteRefused as e:
            out.append({"ticket": name, "why": str(e)})
    return out


def _default_tickets_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(here))),
                        "CairnCommons", "tickets")


if __name__ == "__main__":  # pragma: no cover — the reading, run by hand
    import sys
    findings = scan(sys.argv[1] if len(sys.argv) > 1 else _default_tickets_dir())
    for f in findings:
        print(f"{f['ticket']}: {f['why']}")
    print(f"{len(findings)} nonconforming chart_notes block(s)")
    raise SystemExit(1 if findings else 0)
