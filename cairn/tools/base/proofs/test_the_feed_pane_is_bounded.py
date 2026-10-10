#!/usr/bin/env python3
"""Proof that the personal feed pane shows a bounded tail of the channel (a43109013780).

Measured 2026-10-10: GET /device/cairn was 1,448,295,623 bytes, nearly all of it the Chat pane,
because ``BaseShim._personal_feed_pane`` projected EVERY message of the device's personal
channel. The pane now carries at most ``FEED_PANE_LIMIT`` turns, the newest, newest last, and
says in one line how many older messages it left out and the command that reads them all.

Teeth, one per falsifier clause (PROVES below), over a fixture shim whose injected bus holds a
channel of 1,000 messages (bodies numbered 0..999 in channel order):
  (1) the pane carries exactly FEED_PANE_LIMIT turns, and they are messages
      1000-FEED_PANE_LIMIT..999 in order — the newest, newest last;
  (2) with 1,000 messages the pane names 800 older messages in its older line; with 5 messages
      there is no older line and all 5 show;
  (3) a turn whose body serializes past FEED_PANE_BODY_BYTES carries {too_large, keys} in its
      place (measured 2026-10-10: after the slice the page was still 131.9 MB, 199 of 200 turns
      being ~355 KB trouble snapshots); a small body passes through unchanged.
Hollow: removing the slice reds tooth 1 (1,000 turns); removing the body bound reds tooth 3.

    bin/cairn test cairn/tools/base/proofs/test_the_feed_pane_is_bounded.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"a43109013780": {
    "1": "test_the_pane_carries_the_newest_limit_turns_newest_last",
    "2": "test_the_pane_names_the_older_messages_only_when_there_are_any",
    "3": "test_an_oversized_body_renders_as_a_stub",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


class _Bus:
    """A bus whose personal channel holds ``n`` messages, bodies numbered in channel order."""

    def __init__(self, n: int, bodies: list | None = None) -> None:
        self.rows = [{"sender": "proof", "date": f"2026-10-10T00:00:{i % 60:02d}",
                      "body": {"n": i}} for i in range(n)]
        if bodies is not None:
            self.rows = [{"sender": "proof", "date": "2026-10-10T00:00:00", "body": b}
                         for b in bodies]

    def read(self, *, to=None, channel=None, reply_to=None):
        assert channel == "personal", channel
        return list(self.rows)


def _pane(n: int, bodies: list | None = None) -> dict:
    # Bound at call time: a reverted subject reds the teeth instead of crashing the reader.
    from cairn.tools.base.device import BaseDevice
    from cairn.tools.base.shim import BaseShim

    class _Shim(BaseShim):
        @property
        def device_id(self) -> str:
            return "spec"

        def device(self):
            return BaseDevice()

    shim = _Shim(bus=_Bus(n, bodies))
    pane = shim._personal_feed_pane()
    assert json.loads(json.dumps(pane)) == pane, "the pane is pure data"
    return pane


def _limit() -> int | None:
    from cairn.tools.base import shim
    return getattr(shim, "FEED_PANE_LIMIT", None)


def test_the_pane_carries_the_newest_limit_turns_newest_last() -> None:
    limit = _limit()
    turns = (_pane(1000).get("data") or {}).get("turns") or []
    got = [t["body"].get("n") for t in turns]
    want = list(range(1000 - limit, 1000)) if isinstance(limit, int) else None
    check("test_the_pane_carries_the_newest_limit_turns_newest_last",
          limit is not None and got == want,
          f"FEED_PANE_LIMIT {limit}; {len(got)} turns, first {got[:1]} last {got[-1:]}")


def test_the_pane_names_the_older_messages_only_when_there_are_any() -> None:
    limit = _limit()
    big = _pane(1000).get("data") or {}
    small = _pane(5).get("data") or {}
    note = str(big.get("older_note", ""))
    want_older = 1000 - limit if isinstance(limit, int) else None
    big_ok = (want_older is not None and big.get("older") == want_older
              and f"{want_older} older messages" in note)
    small_turns = [t["body"].get("n") for t in small.get("turns") or []]
    small_ok = "older" not in small and "older_note" not in small and small_turns == [0, 1, 2, 3, 4]
    check("test_the_pane_names_the_older_messages_only_when_there_are_any", big_ok and small_ok,
          f"1000: older {big.get('older')!r} note {note[:80]!r}; 5: keys {sorted(small)} turns {small_turns}")


def test_an_oversized_body_renders_as_a_stub() -> None:
    from cairn.tools.base import shim
    cap = getattr(shim, "FEED_PANE_BODY_BYTES", None)
    big = {"troubles": "x" * 20000, "count": 3}
    small = {"n": 7, "text": "hello"}
    turns = (_pane(0, [big, small]).get("data") or {}).get("turns") or []
    size = len(json.dumps(big, default=str))
    stub = turns[0]["body"] if turns else None
    ok = (isinstance(cap, int) and cap < size and len(turns) == 2
          and stub == {"too_large": size, "keys": ["count", "troubles"]}
          and turns[0]["sender"] == "proof" and turns[1]["body"] == small)
    check("test_an_oversized_body_renders_as_a_stub", ok,
          f"FEED_PANE_BODY_BYTES {cap}; big body {size} bytes -> {str(stub)[:80]!r}; "
          f"small -> {turns[1]['body'] if len(turns) > 1 else None!r}")


def main() -> int:
    for tooth in (test_the_pane_carries_the_newest_limit_turns_newest_last,
                  test_the_pane_names_the_older_messages_only_when_there_are_any,
                  test_an_oversized_body_renders_as_a_stub):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
