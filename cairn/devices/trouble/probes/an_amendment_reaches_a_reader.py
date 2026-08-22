"""PROBE — does an amendment on a trouble record reach a reader?

Berth for the WATCHME that ticket ``a-false-statement-in-a-trouble-record-can-be-corrected-in-place``
carries. Berthed beside ``cairn/devices/trouble`` because that is WHAT IT WATCHES: amendments appended
to the cleared_by list are the feature the ticket built, and the one way this design fails silently is
an amendment landing in a record nobody reads — the reach question the ticket carries knowingly.

THE REACH QUESTION. A cleared trouble leaves live() and stops appearing at session open. An amendment
on a cleared record stays invisible to every standing surface unless someone greps. This probe measures
exactly that: per amended record, which surfaces would put it in front of a reader? The count of
unreachable amendments is the evidence for whether a reach ticket is owed.

TWO INVARIANTS:

  (a) THE AMENDMENT IS INTACT: cleared_by carries entries with ``amendment: true``, ``by``, ``at``,
      and ``correction`` — all four fields present and non-empty. A truncated amendment is a record
      that says it was corrected and cannot say how.

  (b) THE REACH IS MEASURED: for each amended record, whether live() would surface it (only if
      standing != CLEARED), whether the session banner would render it (same gate), and whether a
      grep of the commons would find it (always yes, since the file is in git). The probe does not
      REQUIRE reach — it MEASURES it, so the consumer (Akien) has the evidence for whether a reach
      ticket is owed.

FILES AND ONE STORE READ. Walks the trouble store through its own door. A store this probe cannot
reach raises rather than reporting a clean zero.

AUTHORITY: none. This probe deposits and pokes; deciding whether the reach justifies a new ticket is
Akien's act (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "a-false-statement-in-a-trouble-record-can-be-corrected-in-place"

_AMENDMENT_FIELDS = {"amendment", "by", "at", "correction"}


def judge(records: list[dict]) -> dict:
    """The pure judgement: amendment integrity and reach, separated from the read."""
    amended_records = []
    total_amendments = 0
    truncated = []
    reach_report = []

    for t in records:
        tid = t.get("id", "<unknown>")
        amendments = [e for e in t.get("cleared_by", []) if e.get("amendment")]
        if not amendments:
            continue

        amended_records.append(tid)
        total_amendments += len(amendments)

        for i, a in enumerate(amendments):
            missing = _AMENDMENT_FIELDS - set(a.keys())
            empty = {k for k in _AMENDMENT_FIELDS if k in a and not a[k]}
            if missing or empty:
                truncated.append({
                    "record": tid, "index": i,
                    "missing_fields": sorted(missing),
                    "empty_fields": sorted(empty),
                })

        is_live = t.get("standing") != "CLEARED"
        reach_report.append({
            "record": tid,
            "amendment_count": len(amendments),
            "standing": t.get("standing"),
            "reaches_live": is_live,
            "reaches_session_banner": is_live,
            "reaches_grep": True,
        })

    reachable_via_live = sum(1 for r in reach_report if r["reaches_live"])
    unreachable_except_grep = sum(
        1 for r in reach_report
        if not r["reaches_live"] and not r["reaches_session_banner"]
    )

    return {
        "amended_records": amended_records,
        "total_amendments": total_amendments,
        "truncated_amendments": truncated,
        "reach": reach_report,
        "reachable_via_live": reachable_via_live,
        "unreachable_except_grep": unreachable_except_grep,
        "all_intact": len(truncated) == 0,
    }


def survey_the_corpus() -> dict:
    """The live read — the trouble store through its own door."""
    from cairn.devices.trouble.trouble import TroubleDevice
    d = TroubleDevice()
    return judge(d.all())


def _corpus(context: dict) -> dict:
    return context.get("corpus") or survey_the_corpus()


def _trigger(now, context: dict) -> bool:
    """TRUE when any amendment is truncated (integrity break).

    The REACH question is not a trigger — unreachable amendments are the design's known
    limit, measured and carried. A truncated amendment is the build failing.
    """
    s = _corpus(context)
    return bool(s["truncated_amendments"])


def _enough(context: dict) -> bool:
    """CLEARED when five or more amendments have been recorded, all intact, and the reach
    question has a consistent answer across them.

    The five-amendment floor is the ticket's own ``enough`` clause. A consistent answer
    means every amended record got the same reach result — all reachable or all unreachable
    — so the consumer knows the pattern, not just a sample.
    """
    s = _corpus(context)
    if s["total_amendments"] < 5:
        return False
    if s["truncated_amendments"]:
        return False
    if not s["reach"]:
        return False
    reach_values = {r["reaches_live"] for r in s["reach"]}
    return len(reach_values) == 1


def _carry(context: dict) -> dict:
    s = _corpus(context)
    parts = []
    if s["truncated_amendments"]:
        parts.append(f"{len(s['truncated_amendments'])} amendment(s) are truncated — "
                     f"missing or empty fields")
    if s["unreachable_except_grep"] and s["amended_records"]:
        parts.append(f"{s['unreachable_except_grep']}/{len(s['amended_records'])} "
                     f"amended record(s) are unreachable except by grep — "
                     f"cleared records leave live() and the session banner")

    return {
        "finding": "; ".join(parts) or (
            "all amendments are intact"
            + (f"; {s['unreachable_except_grep']}/{len(s['amended_records'])} "
               f"unreachable except by grep"
               if s["unreachable_except_grep"] else
               "; all amended records are reachable via live()")
        ),
        "amended_records": s["amended_records"],
        "total_amendments": s["total_amendments"],
        "all_intact": s["all_intact"],
        "reach": s["reach"],
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "the ticket's falsifier reds on (1) an amendment that "
                             "erased rather than appended — this probe catches the "
                             "truncated case; (2) a correction without a join key — "
                             "the cleared_by list position IS the join; and the reach "
                             "question: amendments on cleared records that no surface "
                             "renders are the design's known limit, and the count is "
                             "the evidence for whether a reach ticket is owed",
        "suggests": ("fix the truncated amendments — the writer dropped a field"
                     if s["truncated_amendments"] else
                     "the reach evidence accumulates here; Akien decides whether "
                     "the unreachable count justifies a surface change"),
    }


_HORIZON = 1000

PROBE = Probe(
    why="does an amendment on a trouble record reach a reader? — the reach question "
        "the ticket carries knowingly, measured here so Akien has the evidence for "
        "whether a reach ticket is owed",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey_the_corpus()
    print(json.dumps({"corpus": s,
                      "would_trigger": _trigger(None, {"corpus": s}),
                      "enough": _enough({"corpus": s})}, indent=2, default=str))
