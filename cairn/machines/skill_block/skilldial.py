"""SKILLDIAL — the usage roster: how often each skill actually fires, and which cannot say.

Akien, 2026-08-04, ruling /note down to short-term operational notes: *"could wind up
being excised through disuse. which brings up another point, if we're not already, we
have to be measuring each skills usage as we go. not just efficacy, but how many times.
metrics."*

The efficacy half was already built — ``learning_block.dial`` projects firings,
send-backs, findings, approvals and match rate for ONE block, computed on read, storing
nothing. Two things were missing, and this module is only those two:

1. **No roster.** ``dial`` answers about a block you already know to ask about. Nobody
   could see the whole set at once, which is exactly the question the disuse clause
   asks: *which of these is nobody reaching for?*
2. **UNMEASURED read as ZERO.** Six of eleven skills are not seam tenants — no
   contract, no door, no trace — so their usage count is not 0, it is unknowable. A
   surface that prints 0 for them would licence excising a skill nobody had ever wired,
   on evidence that only ever meant "it cannot be counted". Law 7 at a diagnostic
   surface: this prints ``not countable`` and says why, and it will not be talked into
   a number.

NOT A REGISTRY (the manager smell). Nothing is stored, nothing is enrolled, no skill
registers itself. The roster is the ``skills/`` directory listing — the attachment that
already exists — and every number is re-derived from the trace on each read, so it
cannot drift from what it summarizes. Same law as ``dial``'s own.

The disuse clause needs one thing this cannot yet give: a skill that fires rarely and a
skill that has stopped are distinguishable only by WHEN, so ``last_fired`` is carried
here. Whether a gap means dying is a judgement, and it stays Akien's.
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.machines.learning_block.learning_block import dial, read_trace, trace_root
from cairn.machines.skill_block import counters
from cairn.machines.skill_block.skill_block import block_name

_REPO = Path(__file__).resolve().parents[3]
_SKILLS = _REPO / "skills"

# Why a skill cannot be counted, in the store's own words rather than a bare flag: the
# reader of an uncountable row has to know whether to wire it or leave it alone.
NOT_A_TENANT = ("not countable — declares neither an input_contract nor a counted_by, so "
                "it fires no door AND names no other store that would hold its firings. "
                "This is NOT zero uses: it is no measurement. Either wire it to "
                "cairn.machines.skill_block, or declare where its count already lives")
NO_CHARTER = ("not countable — no charter at all, so it is not a component that runs "
              "(CLAUDE.md). Fix the charter before asking about its usage")

# The two ways a skill can be countable. The distinction is load-bearing at the surface:
# a seam tenant yields the full efficacy set (refusals, findings, match rate) because the
# door judges the firing; an elsewhere-counted skill yields firings and a date and NOTHING
# ELSE, because its store records that a thing happened and not how well. Printing 0 in
# those columns would invent a refusal rate for a door that never refuses anything.
VIA_SEAM = "skill-seam"


def skill_names(skills_root: Path | str | None = None) -> list[str]:
    """The roster IS the directory. No enrolment, no manifest, no list to keep in sync."""
    root = Path(skills_root) if skills_root is not None else _SKILLS
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))


def _charter(skill: str, root: Path) -> dict | None:
    charter = root / skill / "intention+why.json"
    if not charter.is_file():
        return None
    try:
        doc = json.loads(charter.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return doc if isinstance(doc, dict) else None


def _last_fired(block: str, traces: Path | None) -> str | None:
    """The newest ``when`` on any record for this block — the field the disuse clause
    needs, because a skill that fires rarely and a skill that has stopped produce the
    same count and differ only in when."""
    whens = [rec.get("when") for rec in read_trace(block, root=traces) if rec.get("when")]
    return max(whens) if whens else None


def roster(*, skills_root: Path | str | None = None,
           traces: Path | str | None = None, **counter_kw) -> list[dict]:
    """One row per skill, every number re-derived on this read. Never writes.

    Three row shapes, and the third is the one this module was wrong about until
    2026-08-04: a skill can be counted somewhere that is not the seam. Five of the six
    rows that read *not countable* were recording their firings all along — in git, in
    chart's own packet berths, in the commons, in the tenant trees. The charter says
    where; this reads it there.
    """
    root = Path(skills_root) if skills_root is not None else _SKILLS
    trace_dir = Path(traces) if traces is not None else trace_root()
    rows: list[dict] = []
    for skill in skill_names(root):
        block = block_name(skill)
        doc = _charter(skill, root)
        row: dict = {"skill": skill, "block": block}

        if doc is None:
            rows.append({**row, "countable": False, "why_not_countable": NO_CHARTER})
            continue

        requires = doc.get("input_contract")
        if isinstance(requires, dict) and requires:
            row.update({"countable": True, "via": VIA_SEAM, "judged": True})
            row.update(dial(block, root=trace_dir))
            row["last_fired"] = _last_fired(block, trace_dir)
            rows.append(row)
            continue

        spec = doc.get("counted_by")
        if not isinstance(spec, dict) or not spec:
            rows.append({**row, "countable": False, "why_not_countable": NOT_A_TENANT})
            continue

        got = counters.count(spec, **counter_kw)
        if "unreadable" in got:
            # A declared store that could not be read is its own third thing: the skill
            # is not unwired, and it is not at zero. Both facts travel.
            rows.append({**row, "countable": False, "declared": spec.get("reader"),
                         "why_not_countable": f"declared {spec.get('reader')!r}, but: "
                                              f"{got['unreadable']}"})
            continue

        row.update({"countable": True, "via": spec.get("reader"), "judged": False,
                    "address": spec.get("address"),
                    "firings": got["firings"], "last_fired": got.get("last_fired"),
                    "detail": got.get("detail"),
                    "what_it_counts": spec.get("what_it_counts")})
        rows.append(row)
    return rows


def render(rows: list[dict]) -> str:
    """A reader-facing surface. It may collapse detail; it may NOT turn an unmeasured
    skill into a measured one, and it may NOT let a firing count pass for a judged one.

    Two dashes with different meanings, and the difference is the whole point. A dash in
    ``fires`` means *nobody can say*. A dash in ``refused``/``findings``/``match`` on a
    counted row means *this store records that it happened, not how it went* — git knows
    a commit exists and nothing about whether it was a good one. Printing 0 there would
    manufacture a perfect refusal record for doors that do not refuse.
    """
    head = (f"{'skill':<12} {'fires':>6} {'refused':>8} {'findings':>9} {'match':>6}  "
            f"{'counted by':<12}  last fired")
    lines = [head, "-" * len(head)]
    seam = elsewhere = uncountable = 0
    for r in rows:
        if not r["countable"]:
            uncountable += 1
            lines.append(f"{r['skill']:<12} {'—':>6} {'—':>8} {'—':>9} {'—':>6}  "
                         f"{'—':<12}  not countable")
            continue
        last = (r.get("last_fired") or "never")[:19]
        if r.get("judged"):
            seam += 1
            rate = r.get("match_rate")
            rate_s = "—" if rate is None else f"{rate:.0%}"
            lines.append(f"{r['skill']:<12} {r['firings']:>6} {r['send_backs']:>8} "
                         f"{r['findings']:>9} {rate_s:>6}  {'the door':<12}  {last}")
        else:
            elsewhere += 1
            lines.append(f"{r['skill']:<12} {r['firings']:>6} {'—':>8} {'—':>9} {'—':>6}  "
                         f"{str(r.get('via') or '?'):<12}  {last}")
    total = sum(r["firings"] for r in rows if r["countable"])
    lines.append("")
    lines.append(f"{seam} judged at a door, {elsewhere} counted elsewhere, "
                 f"{uncountable} not countable — {total} firings visible.")
    lines.append("'not countable' is not zero uses. A dash under refused/findings/match "
                 "means the store records THAT it fired, not how it went.")
    if uncountable:
        for r in rows:
            if not r["countable"]:
                lines.append(f"  {r['skill']}: {r['why_not_countable']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import sys
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("-h", "--help"):
        print("usage: cairn skilldial [--json]\n"
              "Usage metrics per skill, re-derived from the trace on every read.\n"
              "Skills that are not seam tenants print 'not countable', never 0.")
        return 0
    rows = roster()
    print(json.dumps(rows, indent=2, sort_keys=True) if "--json" in args else render(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
