"""usage — the account's usage, read on an event and kept as one JSON file.

Akien, 2026-11-12: "could be a hook again, writing a json file that you could just look at
any time you wanted to." A Stop hook calls `read_and_write()`; any reader calls `last()`.
The file never passes stale data off as fresh: every answer carries fetched_at and age_s, and
a failed fetch is written as an error beside the last good reading, never in its place.

    python -m cairn.tools.usage            # print the last reading and its age
    python -m cairn.tools.usage --fetch    # fetch now, write, print
    python -m cairn.tools.usage --hook     # Stop-hook entry: fetch, write, exit 0 always

Store: ~/.cairn/devices/cc/0/tools/usage/usage.json (override CAIRN_USAGE_FILE).

The reply shape of the endpoint is a HYPOTHESIS (no network call was measured at build); an
unreadable reply is recorded as a window of None, never invented.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ENDPOINT = "https://api.anthropic.com/api/oauth/usage"
BETA = "oauth-2025-04-20"


def store_path(environ=None) -> Path:
    env = os.environ if environ is None else environ
    # Outline 1.3.1: a tool's data for a holder berths under that holder; the Stop hook is CC's.
    return Path(env.get("CAIRN_USAGE_FILE")
                or Path.home() / ".cairn" / "devices" / "cc" / "0" / "tools" / "usage" / "usage.json")


def creds_path(environ=None) -> Path:
    env = os.environ if environ is None else environ
    return Path(env.get("CAIRN_USAGE_CREDS") or Path.home() / ".claude" / ".credentials.json")


def _token(path: Path) -> str:
    d = json.loads(path.read_text(encoding="utf-8"))
    return (d.get("claudeAiOauth") or {}).get("accessToken") or d.get("accessToken") or ""


def _fetch(token: str, endpoint: str, timeout: float) -> dict:
    req = urllib.request.Request(endpoint, headers={
        "Authorization": f"Bearer {token}", "anthropic-beta": BETA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def _window(raw: dict, key: str) -> dict | None:
    w = raw.get(key) if isinstance(raw, dict) else None
    if not isinstance(w, dict) or w.get("utilization") is None:
        return None
    return {"percent": w["utilization"], "resets_at": w.get("resets_at")}


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def read_and_write(*, environ=None, endpoint: str = ENDPOINT, timeout: float = 10.0,
                   now: float | None = None, fetch=None) -> dict:
    """Fetch once and write the store. Never raises: a failure is recorded, loudly."""
    now = time.time() if now is None else now
    fetch = _fetch if fetch is None else fetch
    path = store_path(environ)
    prior = _load(path)
    record = {"fetched_at": None, "error": None, "seven_day": None, "five_hour": None,
              "last_good": prior.get("last_good") if prior else None}
    token = ""
    try:
        token = _token(creds_path(environ))
        if not token:
            raise RuntimeError("no OAuth access token in the credentials file")
        raw = fetch(token, endpoint, timeout)
        record.update(fetched_at=now, seven_day=_window(raw, "seven_day"),
                      five_hour=_window(raw, "five_hour"))
        record["last_good"] = {k: record[k] for k in ("fetched_at", "seven_day", "five_hour")}
    except Exception as exc:  # noqa: BLE001 — every failure is written, none hidden
        what = f"{type(exc).__name__}: {str(exc)}"
        if token:
            what = what.replace(token, "[token]")
        record["error"] = {"at": now, "what": what[:200]}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(record, indent=1), encoding="utf-8")
    os.replace(tmp, path)
    return record


def last(*, environ=None, now: float | None = None) -> dict:
    """The stored reading with its age. A failed last fetch says so; it never reads as fresh."""
    now = time.time() if now is None else now
    rec = _load(store_path(environ))
    if rec is None:
        return {"state": "absent", "path": str(store_path(environ))}
    good = rec.get("last_good")
    out = {"state": "error" if rec.get("error") else "fresh", "error": rec.get("error"),
           "reading": good, "age_s": round(now - good["fetched_at"]) if good else None}
    if good is None:
        out["state"] = "error-never-read"
    return out


def _line(r: dict) -> str:
    if r["state"] in ("absent", "error-never-read"):
        return f"usage: {r['state'].upper()} {r.get('error') or r.get('path')}"
    g = r["reading"]
    s = g["seven_day"] or {}
    f = g["five_hour"] or {}
    head = "" if r["state"] == "fresh" else f"STALE (last fetch failed: {r['error']['what']}) "
    return (f"usage: {head}7d {s.get('percent')}% resets {s.get('resets_at')} | "
            f"5h {f.get('percent')}% resets {f.get('resets_at')} | read {r['age_s']}s ago")


def main(argv=None, *, environ=None, now: float | None = None, fetch=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--hook" in argv:
        try:
            read_and_write(environ=environ, now=now, fetch=fetch)
        except Exception:  # noqa: BLE001 — a Stop hook never blocks the session
            pass
        return 0
    if "--fetch" in argv:
        read_and_write(environ=environ, now=now, fetch=fetch)
    r = last(environ=environ, now=now)
    print(json.dumps(r, indent=1) if "--json" in argv else _line(r))
    return 0 if r["state"] == "fresh" else 1
