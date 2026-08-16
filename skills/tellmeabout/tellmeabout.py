"""tellmeabout.py — Akien's dereference door: the one record a token names, verbatim.

The system hands its one human reader ids and slugs it never taught him to open —
the 2026-08-15 curated review handed him 17 finding ids and itself recorded that
``cairn recordverdict <id>`` alone won't show their bullets (the lived symptom;
ticket tellmeabout). This floor answers the token: it searches the record stores,
and returns exactly one of three shapes —

  found      — the ONE record, in its own words (verbatim from the store, never a
               summary), at its address, with the act it is waiting on
  refused    — the token names more than one record: refuse by LISTING every match
               with its store and address, never guess (one discipline, third
               tenant — recordverdict's multi-match refusal and the orient floor's
               two-rungs refusal are the precedents)
  not_found  — nothing answers: name EVERY store searched, so a store this
               resolver misses is visible, never silent

The stores, and the deterministic match rule per store:

  findings   — the learning_block trace store; a token that is a hex id (or a
               unique prefix of one, >= 4 chars) names a finding
  tickets    — CairnCommons/tickets/<id>.json; token == file stem
  troubles   — CairnCommons/troubles/<slug>.json; token == file stem
  decisions  — CairnCommons/decisions/<date>-<slug>.json; token == stem, or ==
               stem with its date prefix stripped (the way the ids are spoken)
  ideas      — CairnCommons/ideas/<date>-<slug>.json; same date-stripped rule
  charters   — intention+why.json beside code; the congruency lab's filenames
               are the INDEX (source-encoded: cairn-machines-learning_block--…),
               but presentation reads the LIVE charter at its own address, never
               the lab copy (Law 5 — the lab is a derived viewing surface)

READ-ONLY over every store it presents — this module opens files and writes
nothing, anywhere (the ticket's gates; a proof pins it by mtime snapshot).
Deterministic — no LLM anywhere in the floor; presentation is field selection,
never rewording.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from cairn.machines.learning_block import learning_block as lb

REPO = Path(__file__).resolve().parents[2]
COMMONS = REPO.parent / "CairnCommons"
LAB = COMMONS / "intentions-congruency-lab"
CHARTER_SUFFIX = "--intention+why.json"

HEX_ID = re.compile(r"^[0-9a-f]{4,16}$")
DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")
CURSOR = re.compile(r"\[([A-Za-z:()<>_-]+)\]")


def _stores_searched() -> list[str]:
    """Every store this resolver reaches, named with its address — the not-found
    answer carries this whole, so a store the resolver misses is visible."""
    return [
        f"findings — {lb.trace_root()} (learning_block trace store, by hex id or unique prefix)",
        f"tickets — {COMMONS / 'tickets'} (by file stem)",
        f"troubles — {COMMONS / 'troubles'} (by file stem)",
        f"decisions — {COMMONS / 'decisions'} (by stem, date prefix optional)",
        f"ideas — {COMMONS / 'ideas'} (by stem, date prefix optional)",
        f"charters — intention+why.json beside code, indexed by {LAB} (by component name)",
    ]


# ── per-store searches: each returns [{store, name, address, ...}] ───────────

def _find_findings(token: str) -> list[dict]:
    if not HEX_ID.match(token):
        return []
    base = lb.trace_root()
    if not base.is_dir():
        return []
    matches, answered = [], set()
    for path in sorted(base.glob("*.jsonl")):
        for rec in lb.read_trace(path.stem, root=base):
            if rec.get("event") == "verdict":
                data = rec.get("data") or {}
                if data.get("signal") in ("approve", "disprove") and data.get("finding_id"):
                    answered.add(data["finding_id"])
            elif rec.get("event") == "finding" and str(rec.get("id", "")).startswith(token):
                matches.append({"store": "findings", "name": rec.get("id"),
                                "address": str(path), "record": rec})
    for m in matches:
        m["pending"] = m["name"] not in answered
    return matches


def _find_by_stem(token: str, directory: Path, store: str,
                  date_stripped: bool = False) -> list[dict]:
    if not directory.is_dir():
        return []
    matches = []
    for path in sorted(directory.glob("*.json")):
        stem = path.stem
        if stem.startswith("_"):
            continue                       # a store's own charter, not a record in it
        if token == stem or (date_stripped and token == DATE_PREFIX.sub("", stem)):
            matches.append({"store": store, "name": stem, "address": str(path)})
    return matches


def _find_charters(token: str) -> list[dict]:
    """The lab's source-encoded filenames are the index; the LIVE charter is the
    record. A lab entry whose decoded source is not on disk is skipped — it is
    not a component charter this rule can address."""
    if not LAB.is_dir():
        return []
    matches = []
    for path in sorted(LAB.iterdir()):
        if not path.name.endswith(CHARTER_SUFFIX):
            continue
        source_dir = path.name[: -len(CHARTER_SUFFIX)].replace("-", "/")
        component = source_dir.rsplit("/", 1)[-1]
        live = REPO / source_dir / "intention+why.json"
        if component == token and live.is_file():
            matches.append({"store": "charters", "name": f"{source_dir} (component: {component})",
                            "address": str(live)})
    return matches


# ── presentation: own words + address + waiting act, per store ───────────────

def _read_json(address: str):
    with open(address, encoding="utf-8") as fh:
        return json.load(fh)


def _present(m: dict) -> dict:
    store = m["store"]
    if store == "findings":
        rec = m["record"]
        waiting = (
            'Akien\'s verdict — answer with: cairn recordverdict %s <approve|disprove|question> "<your words>"'
            % m["name"] if m["pending"]
            else "nothing — an approve/disprove has answered it (the verdict record lives under CairnCommons/learning/records)")
        return {"found": {"store": store, "id": m["name"], "address": m["address"],
                          "record": rec, "waiting_on": waiting}}
    record = _read_json(m["address"])
    if store == "tickets":
        cursor = CURSOR.search(str(record.get("state", "")))
        waiting = (f"the {cursor.group(1)} crossing — the bracketed summons on its own cursor"
                   if cursor else "no bracketed cursor readable in its state field — read the record")
    elif store == "troubles":
        waiting = ("being cleared through its owner's door — a live trouble stays in the "
                   "session-open inbox until the clearing is measured")
    elif store == "decisions":
        waiting = (f"cairn ruling verify {m['name']} — the per-packet measure of "
                   "conformed/confirmed; a ruling is red until his marker lands")
    elif store == "ideas":
        waiting = (f"nothing it owes — it rests in the queue until someone fires /intent {m['name']} "
                   "(where it is traced, challenged, and possibly killed)")
    else:  # charters
        waiting = ("nothing — a charter changes only when the design shifts; it answers "
                   "to /challenge, deliberately, in hand")
    return {"found": {"store": store, "name": m["name"], "address": m["address"],
                      "record": record, "waiting_on": waiting}}


# ── the one entry point ──────────────────────────────────────────────────────

def resolve(token: str) -> dict:
    """The dereference: exactly one of found / refused / not_found."""
    token = token.strip()
    if not token:
        return {"not_found": token, "stores_searched": _stores_searched(),
                "note": "an empty token names nothing"}
    matches = (
        _find_findings(token)
        + _find_by_stem(token, COMMONS / "tickets", "tickets")
        + _find_by_stem(token, COMMONS / "troubles", "troubles")
        + _find_by_stem(token, COMMONS / "decisions", "decisions", date_stripped=True)
        + _find_by_stem(token, COMMONS / "ideas", "ideas", date_stripped=True)
        + _find_charters(token)
    )
    if not matches:
        return {"not_found": token, "stores_searched": _stores_searched()}
    if len(matches) > 1:
        return {"refused": f"{len(matches)} records answer to {token!r} — refusing to "
                           "guess between them; name one by its fuller token",
                "matches": [{"store": m["store"], "name": m["name"], "address": m["address"]}
                            for m in matches]}
    return _present(matches[0])


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python3 -m skills.tellmeabout.tellmeabout '<id-or-name>'", file=sys.stderr)
        return 2
    got = resolve(argv[0])
    print(json.dumps(got, indent=2, ensure_ascii=False))
    if "found" in got:
        return 0
    return 3 if "refused" in got else 4


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
