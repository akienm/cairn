"""The tester's operator notices — an unvouched green that completed, told once (b5871526384a).

Akien's answer to open-ed0a56ce6357: when the measurement cannot vouch for a green — a file
whose revert redded no declared tooth — "we let it complete AND notify me", and "if i get
inundated, we'll change it". So the hollow run no longer reds that file; it posts one notice
here (the file plus its diff), and the operator inbox reads them through the tester's
`notices` verb (RULE 1: the inbox asks the verb, never this store).

The tester measured the case, so the tester owns the notices (Law 6): they berth under its own
instance address, one JSON file per notice. A notice's id is a hash of (ticket, file, diff), so
re-sealing the same reading tells the operator once. rate() is the instrument he asked for —
measured from the first notice, from day one (Law 3).

A second kind rides the same store and the same rate (ticket f0aad0cd0f56): a sealed green that
replaced a red measured under other conditions — post_conditions names what changed.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.address import instance_path

HOME: Path | None = None  # a proof points this at a scratch dir


def home() -> Path:
    return HOME or instance_path("tester", 0) / "notices"


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


def _stamp(now: datetime | None) -> str:
    return _now(now).isoformat(timespec="seconds")


def notice_id(ticket: str, file: str, diff: str) -> str:
    return "n-" + hashlib.sha256(f"{ticket}\0{file}\0{diff}".encode()).hexdigest()[:12]


def _write(ticket: str, file: str, line: str, diff: str, now: datetime | None) -> str:
    nid = notice_id(ticket, file, diff)
    path = home() / f"{nid}.json"
    if path.exists():
        return nid
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "id": nid, "ticket": ticket, "file": file, "line": line,
        "diff": diff, "posted_at": _stamp(now), "seen_at": None,
    }, indent=2, ensure_ascii=False) + "\n")
    return nid


def post(ticket: str, file: str, diff: str, *, now: datetime | None = None) -> str:
    return _write(ticket, file,
                  f"{ticket}: {file} reverted and no declared tooth redded — check the diff "
                  f"against the component's intention", diff, now)


def post_conditions(ticket: str, file: str, diff: str, changed: list, *,
                    now: datetime | None = None) -> str:
    return _write(ticket, file,
                  f"{ticket}: {file} sealed green over a red measured under other conditions "
                  f"({', '.join(changed)}) — check that the green answers the component's "
                  f"intention, not the changed measurement", diff, now)


def _all() -> list[dict]:
    if not home().is_dir():
        return []
    return sorted((json.loads(p.read_text()) for p in home().glob("n-*.json")),
                  key=lambda n: n["posted_at"])


def unseen() -> list[dict]:
    return [n for n in _all() if n.get("seen_at") is None]


def seen(nid: str, *, now: datetime | None = None) -> dict | None:
    path = home() / f"{nid}.json"
    if not nid or not path.is_file():
        return None
    rec = json.loads(path.read_text())
    rec["seen_at"] = rec.get("seen_at") or _stamp(now)
    path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
    return rec


def rate(*, now: datetime | None = None) -> dict:
    every = _all()
    if not every:
        return {"total": 0, "first": None, "days": 0, "per_day": 0.0}
    first = every[0]["posted_at"]
    span = (_now(now) - datetime.fromisoformat(first)).total_seconds() / 86400
    days = max(1, math.ceil(span))
    return {"total": len(every), "first": first, "days": days,
            "per_day": round(len(every) / days, 2)}
