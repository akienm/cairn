"""THE SLATE DOOR — the most authoritative artifact in the system stops being
unassisted synthesis.

/saveslate is tenant #3 of the ``cairn.skill_block`` seam (ticket
``slate-compiles-from-the-world``, opus-pass rank 5 ruled spec 2026-08-03). The slate
is injected into EVERY future session by the SessionStart hook — authoritative by
construction — so a confident wrong slate compounds forever. This door makes
"compiled from the world" checkable:

- **heads-match**: the packet's ``instruments_read.git_heads`` must equal the LIVE
  repos' HEADs at write time — the coined verifiable-evidence convention (first use):
  a field the door checks against the world, impossible to fill from the transcript
  alone. Stale or missing heads refuse the write, naming live-vs-packet.
- **the reader's closed set**: the slate carries ONLY what ``bin/cmd/slate`` reads
  (at_sea, next_direction, open_threads) plus the store template's envelope — a key
  nothing reads is context paid forever for nothing.
- **the measured ceiling**: the three carried fields' rendered size must be under
  10,000 chars. Measured corpus at install (50 slates): min 2,211 / median 6,880 /
  max 12,878 — the ceiling holds the line below the worst case; the cost is standing,
  paid at every session open.
- **no overwrite**: an id colliding with an existing slate refuses — a slate is a new
  record at a boundary (Law 7).

ONE ACT: a conforming packet berths through the seam AND the slate file is written —
the slates store charter has promised 'the single commons emit chokepoint validates
every record' since v0, with no code behind it; for this write path, this door is
that promise kept. A refused packet writes NOTHING and the refusal is traced (the
``slate-door-refusals`` probe's denominator).

Fire from bash:

    PYTHONPATH=$HOME/dev/src/cairn python3 skills/saveslate/door.py <packet.json>

exit 0 recorded (berth + slate path printed), 2 refused (every lack named, one pass).
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.learning_block.learning_block import (  # noqa: E402
    DoorRefused,
    check_input,
    write_trace,
)
from cairn.skill_block import skill_block as sb    # noqa: E402

_COMMONS = _REPO.parent / "CairnCommons"
_SLATES = _COMMONS / "slates"

# The reader's closed set (bin/cmd/slate CARRIED) + the store template's envelope.
CARRIED = ("at_sea", "next_direction", "open_threads")
ENVELOPE = ("id", "date", "written_at", "session", "author")

# Envelope fields only the DOOR may mint. written_at is the rank key the reader
# trusts (bin/cmd/slate); an author-supplied value could backdate a record of
# truth — the same two-witness argument that killed auto-inherit (cbbadb13530f):
# the stamp must come from the one hand the packet cannot contaminate.
DOOR_MINTED = ("id", "date", "written_at", "author")

# Measured at install over 50 slates: min 2211 / median 6880 / max 12878 chars.
CEILING = 10_000


def live_git_heads(repo: Path | None = None, commons: Path | None = None) -> dict:
    """The two repos' HEADs, read from the world — the same call the skill's
    instrument step runs, so the packet and the judge cannot disagree about what
    'the live head' means (one implementation, two mouths)."""
    heads = {}
    for name, path in (("cairn", repo or _REPO), ("CairnCommons", commons or _COMMONS)):
        try:
            out = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                                 capture_output=True, text=True, timeout=10)
            heads[name] = out.stdout.strip() if out.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            heads[name] = None
    return heads


def judge_packet(payload: dict, *, heads: dict | None = None,
                 slates_dir: Path | str | None = None) -> list[dict]:
    """Every SEMANTIC lack, one pass. Judges only present fields (absence is the
    flat contract's finding)."""
    lacks: list[dict] = []
    slates = Path(slates_dir) if slates_dir is not None else _SLATES

    slate_id = payload.get("slate_id")
    if isinstance(slate_id, str) and slate_id.strip():
        target = slates / f"{slate_id.strip()}.json"
        if target.exists():
            lacks.append({"field": "slate_id",
                          "why": f"a slate already stands at {target} — a slate is a NEW "
                                 "record at a boundary, never an overwrite (Law 7); pick "
                                 "a fresh id"})

    inst = payload.get("instruments_read")
    if inst is not None and not isinstance(inst, dict):
        lacks.append({"field": "instruments_read",
                      "why": "must be an object carrying git_heads (and the other "
                             "instrument outputs) — see the charter's coined convention"})
    elif isinstance(inst, dict) and inst:
        packet_heads = inst.get("git_heads")
        live = heads if heads is not None else live_git_heads()
        if not isinstance(packet_heads, dict) or not packet_heads:
            lacks.append({"field": "instruments_read",
                          "why": "carries no git_heads — the one field the door can check "
                                 "against the WORLD; run the instrument (git rev-parse HEAD "
                                 "in both repos) and put the hashes in the packet"})
        else:
            stale = {k: (packet_heads.get(k), live.get(k))
                     for k in live if packet_heads.get(k) != live.get(k)}
            if stale:
                lacks.append({"field": "instruments_read",
                              "why": "git_heads do not match the live repos — the writer "
                                     "never looked at the world (or it moved since): "
                                     + "; ".join(f"{k}: packet {p!r} vs live {l!r}"
                                                 for k, (p, l) in stale.items())
                                     + ". Re-run the instruments and re-fire."})

    extra = [k for k in payload
             if k not in CARRIED and k not in
             ("slate_id", "instruments_read", "bullets", "exit", "disposition",
              "session")]
    minted = [k for k in extra if k in DOOR_MINTED]
    if minted:
        # NOT "a key nothing reads" — the reader reads these. They are refused
        # because the door mints them at write time (id from slate_id, the rest
        # from the clock and the world); written_at is the rank key, and an
        # author-supplied stamp could backdate the record. Say the true why.
        lacks.append({"field": ", ".join(sorted(minted)),
                      "why": "door-minted envelope fields — the door stamps these at the "
                             "write (id from your slate_id; date/written_at from its own "
                             "clock; author). written_at is the rank key the session-open "
                             "reader trusts, so an author-supplied value could backdate a "
                             "record of truth. Drop them; supply slate_id and let the door "
                             "stamp the rest."})
    extra = [k for k in extra if k not in DOOR_MINTED]
    if extra:
        lacks.append({"field": ", ".join(sorted(extra)),
                      "why": "keys the reader does not read — bin/cmd/slate consumes a "
                             "CLOSED SET (at_sea, next_direction, open_threads) and the "
                             "store charter deliberately ignores any other key; a key "
                             "nothing reads is standing context paid forever for nothing"})

    body = json.dumps({k: payload.get(k) for k in CARRIED})
    if len(body) > CEILING:
        lacks.append({"field": "at_sea/next_direction/open_threads",
                      "why": f"rendered size {len(body)} chars exceeds the ceiling "
                             f"({CEILING}) — the slate is read at EVERY session open, so "
                             "its length is a standing tax (measured corpus: median 6,880, "
                             "max 12,878 — the max is the defect, not the license); cut "
                             "what the next session will not act on"})

    return lacks


def fire(payload: dict, *, now: datetime | None = None, heads: dict | None = None,
         slates_dir: Path | str | None = None, session: str = "",
         skills_root=None, berths=None, trace_root=None) -> dict:
    """Gate the slate — flat AND semantic lacks in ONE refusal — then berth through
    the seam and WRITE the slate in the same act. A refusal writes nothing."""
    contract = sb.load_contract("saveslate", skills_root=skills_root)
    lacks = check_input(contract, payload) + judge_packet(payload, heads=heads,
                                                          slates_dir=slates_dir)
    if lacks:
        write_trace(contract["block"], "send_back", "training",
                    {"lacks": lacks, "judge": "slate-door",
                     "payload_fields": sorted(payload.keys())},
                    now=now, root=trace_root)
        raise DoorRefused(contract["block"], lacks)

    result = sb.fire("saveslate", payload, now=now, skills_root=skills_root,
                     berths=berths, trace_root=trace_root)

    when = now or datetime.now()
    slates = Path(slates_dir) if slates_dir is not None else _SLATES
    record = {
        "id": payload["slate_id"].strip(),
        "date": when.date().isoformat(),
        # The instant of the write, not the day of it. `date` alone cannot rank two
        # slates from the same day, and the reader's filename tiebreak is alphabetical
        # on the TITLE — which on 2026-08-03 named the 15:50 slate current over the
        # 16:41 one and opened the next session a voyage behind. The door already
        # holds this instant; it was being thrown away at day granularity.
        "written_at": when.isoformat(timespec="seconds"),
        "session": session or payload.get("session", ""),
        "author": "CC",
        "at_sea": payload["at_sea"],
        "next_direction": payload["next_direction"],
        "open_threads": payload["open_threads"],
    }
    slate_path = slates / f"{record['id']}.json"
    slate_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    result["slate"] = str(slate_path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    session = ""
    if "--session" in args:
        i = args.index("--session")
        session = args[i + 1] if i + 1 < len(args) else ""
        del args[i:i + 2]
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print("usage: python3 skills/saveslate/door.py [--session <id>] <packet.json>\n"
              "The packet carries /saveslate's input_contract fields — see\n"
              "  python3 -m cairn.skill_block contract saveslate", file=sys.stderr)
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
        result = fire(payload, session=session)
    except OSError as exc:
        print(f"/saveslate: the firing could not be RECORDED — {exc}\n"
              "  no berth and NO SLATE exist for this close; the next session will "
              "open on the previous slate.", file=sys.stderr)
        print(json.dumps({"berth": None, "slate": None, "recorded": False,
                          "reason": str(exc)}, indent=2, sort_keys=True))
        return 0
    except DoorRefused as exc:
        lacks = getattr(exc, "lacks", None) or []
        lines = [f"  - {l['field']}: {l['why']}" for l in lacks] or [f"  - {exc}"]
        print("/saveslate refused — every lack named on this one pass:\n"
              + "\n".join(lines)
              + "\n(the refusal is recorded and NO slate was written; fix the packet "
              "and fire again)", file=sys.stderr)
        return 2
    except sb.SkillBlockRefused as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
