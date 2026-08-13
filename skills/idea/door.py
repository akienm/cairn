"""THE IDEA DOOR — capture stops being a sentence in the chat and becomes a record.

/idea is tenant #4 of the ``cairn.machines.skill_block`` seam (after /intent, /sorted and
/saveslate). It is the workflow's FIRST step and the only one whose input comes from
outside the system: nothing upstream can fire it.

WHAT THIS MODULE OWNS that the flat contract cannot: the WRITE TO THE COMMONS. The
skill's markdown could ask its executor to save a file, and that ask would be policy —
the exact shape Law 4 calls a tracked debt. Here the write is physics: one call gates
the capture, traces it, berths it, and lands the record at
``CairnCommons/ideas/<id>.json``, or fails loudly having done neither.

TWO ARTIFACTS, TWO ROOTS, BY LAW. The idea RECORD is knowledge and lives in the commons
(git, shareable, survives the box). The BERTH is instance-space and does not. That is
why /intent's ``from_idea`` cites the record's id and never the berth path.

THE ORDER, AND WHY IT INVERTS THE SORTED CONVENTION. /sorted's door treats an
unwritable recording root as non-fatal — "the recording never wedges the work" — because
there the work was the cast and the berth was only its receipt. Here the record IS the
work. A firing that berths but cannot write the commons record has captured nothing, so
this door says so and exits non-zero, naming the berth that exists without it.

Fire from bash (what the skill actually uses):

    PYTHONPATH=$HOME/dev/src/cairn python3 skills/idea/door.py <packet.json>

exit 0 captured (the record path printed), 2 refused or unwritable.
"""

from __future__ import annotations

import json
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:                       # script-invoked beside the skill
    sys.path.insert(0, str(_REPO))

from cairn.machines.learning_block.learning_block import DoorRefused   # noqa: E402
from cairn.machines.skill_block import skill_block as sb               # noqa: E402

_COMMONS = _REPO.parent / "CairnCommons"
_SLUG_WORDS = 7
_SLUG_MAX = 48


def ideas_dir(commons: Path | str | None = None) -> Path:
    return (Path(commons) if commons is not None else _COMMONS) / "ideas"


def slug_of(prose: str) -> str:
    """A readable, deterministic handle for the record — first few words, kebabbed.

    Deterministic on purpose: the id is what /intent's ``from_idea`` cites, and an id
    a human cannot guess from the prose is an id a human will get wrong.
    """
    words = re.findall(r"[a-z0-9]+", str(prose).lower())[:_SLUG_WORDS]
    return ("-".join(words) or "idea")[:_SLUG_MAX].strip("-")


def _record_path(base: Path, when: datetime, prose: str) -> tuple[Path, str]:
    """Date-prefixed so the store reads chronologically; suffixed only on collision, so
    two ideas captured the same day with the same opening words stay distinguishable
    without every id carrying noise."""
    stem = f"{when.strftime('%Y-%m-%d')}-{slug_of(prose)}"
    path = base / f"{stem}.json"
    if path.exists():
        stem = f"{stem}-{uuid.uuid4().hex[:4]}"
        path = base / f"{stem}.json"
    return path, stem


def fire(payload: dict, *, now: datetime | None = None, skills_root=None, berths=None,
         trace_root=None, commons: Path | str | None = None) -> dict:
    """Gate the capture, ride the seam, then land the record. Returns both addresses.

    No semantic judges. The flat contract IS the whole gate — prose, author, bullets —
    because the step's gate is "captured text that can be interpreted later" and every
    additional question is friction on the one step that cannot afford any. What this
    adds to ``sb.fire`` is the commons write, and only that.
    """
    when = now or datetime.now()
    result = sb.fire("idea", payload, now=when, skills_root=skills_root,
                     berths=berths, trace_root=trace_root)

    base = ideas_dir(commons)
    base.mkdir(parents=True, exist_ok=True)
    path, stem = _record_path(base, when, payload["prose"])
    path.write_text(json.dumps({
        "id": stem,
        "date": when.isoformat(),
        "author": payload["author"],
        "prose": payload["prose"],
        "interpretation": "deferred",
        "trace_id": result["trace_id"],
        "finding_id": result["finding_id"],
        "berth": result["berth"],
    }, indent=2, sort_keys=True) + "\n")

    return {**result, "idea": str(path), "id": stem}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print("usage: python3 skills/idea/door.py <packet.json>\n"
              "The packet carries /idea's input_contract fields — see\n"
              "  python3 -m cairn.machines.skill_block contract idea", file=sys.stderr)
        return 2
    try:
        payload = json.loads(Path(args[0]).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"packet {args[0]!r} unreadable — {exc}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print(f"packet {args[0]!r} must be a JSON object", file=sys.stderr)
        return 2
    try:
        result = fire(payload)
    except DoorRefused as exc:
        lacks = getattr(exc, "lacks", None) or []
        lines = [f"  - {l['field']}: {l['why']}" for l in lacks] or [f"  - {exc}"]
        print("/idea capture refused — every lack named on this one pass:\n"
              + "\n".join(lines)
              + "\n(the refusal is recorded; fix the packet and fire again)",
              file=sys.stderr)
        return 2
    except sb.SkillBlockRefused as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except OSError as exc:
        # Inverting the sorted convention deliberately: here the RECORD is the work.
        print(f"/idea: the idea could not be WRITTEN — {exc}\n"
              "  the firing may have berthed, but nothing was captured: there is no\n"
              "  record in CairnCommons/ideas/ for /intent to reach for. Say the idea\n"
              "  again once the commons is writable — this is a loss, not a hiccup.",
              file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
