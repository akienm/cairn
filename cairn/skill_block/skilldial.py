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

from cairn.learning_block.learning_block import dial, read_trace, trace_root
from cairn.skill_block.skill_block import block_name

_REPO = Path(__file__).resolve().parents[2]
_SKILLS = _REPO / "skills"

# Why a skill cannot be counted, in the store's own words rather than a bare flag: the
# reader of an uncountable row has to know whether to wire it or leave it alone.
NOT_A_TENANT = ("not countable — declares no input_contract, so it fires no door and "
                "leaves no trace. This is NOT zero uses: it is no measurement. Wiring "
                "it to cairn.skill_block is what makes its usage a number")
NO_CHARTER = ("not countable — no charter at all, so it is not a component that runs "
              "(CLAUDE.md). Fix the charter before asking about its usage")


def skill_names(skills_root: Path | str | None = None) -> list[str]:
    """The roster IS the directory. No enrolment, no manifest, no list to keep in sync."""
    root = Path(skills_root) if skills_root is not None else _SKILLS
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))


def _tenancy(skill: str, root: Path) -> tuple[bool, str]:
    charter = root / skill / "intention+why.json"
    if not charter.is_file():
        return False, NO_CHARTER
    try:
        doc = json.loads(charter.read_text())
    except (OSError, json.JSONDecodeError):
        return False, NO_CHARTER
    requires = doc.get("input_contract")
    if not isinstance(requires, dict) or not requires:
        return False, NOT_A_TENANT
    return True, ""


def _last_fired(block: str, traces: Path | None) -> str | None:
    """The newest ``when`` on any record for this block — the field the disuse clause
    needs, because a skill that fires rarely and a skill that has stopped produce the
    same count and differ only in when."""
    whens = [rec.get("when") for rec in read_trace(block, root=traces) if rec.get("when")]
    return max(whens) if whens else None


def roster(*, skills_root: Path | str | None = None,
           traces: Path | str | None = None) -> list[dict]:
    """One row per skill, every number re-derived on this read. Never writes."""
    root = Path(skills_root) if skills_root is not None else _SKILLS
    trace_dir = Path(traces) if traces is not None else trace_root()
    rows: list[dict] = []
    for skill in skill_names(root):
        block = block_name(skill)
        tenant, why_not = _tenancy(skill, root)
        row = {"skill": skill, "block": block, "countable": tenant}
        if not tenant:
            row["why_not_countable"] = why_not
        else:
            row.update(dial(block, root=trace_dir))
            row["last_fired"] = _last_fired(block, trace_dir)
        rows.append(row)
    return rows


def render(rows: list[dict]) -> str:
    """A reader-facing surface. It may collapse detail; it may NOT turn an unmeasured
    skill into a measured one — the uncountable rows print a dash, never a zero."""
    head = f"{'skill':<12} {'fires':>6} {'refused':>8} {'findings':>9} {'match':>6}  last fired"
    lines = [head, "-" * len(head)]
    countable = uncountable = 0
    for r in rows:
        if not r["countable"]:
            uncountable += 1
            lines.append(f"{r['skill']:<12} {'—':>6} {'—':>8} {'—':>9} {'—':>6}  not countable")
            continue
        countable += 1
        rate = r.get("match_rate")
        rate_s = "—" if rate is None else f"{rate:.0%}"
        last = (r.get("last_fired") or "never")[:19]
        lines.append(f"{r['skill']:<12} {r['firings']:>6} {r['send_backs']:>8} "
                     f"{r['findings']:>9} {rate_s:>6}  {last}")
    lines.append("")
    lines.append(f"{countable} skill(s) countable, {uncountable} not — and 'not countable' is "
                 f"not zero uses.")
    if uncountable:
        lines.append("A skill with no door leaves no trace, so disuse and never-wired look "
                     "identical from here.")
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
