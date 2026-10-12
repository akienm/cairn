#!/usr/bin/env python3
"""Proof that every channel pane on a device page reads only what it shows (86423bb5f054).

Measured 2026-10-10 (trouble chat-pane-is-unbounded): GET /device/cairn took ~25 s, because
``_personal_feed_pane`` sliced after an unbounded ``bus.read`` and ``_info_pane`` and
``_debug_pane`` rendered every message on their channels with no bound at all. Each pane now
asks the bus for the newest ``FEED_PANE_LIMIT`` (f8a97b570073's ``read(limit=)``), takes the
total from ``bus.count``, and names the rest in one older line.

Teeth, one per falsifier clause (PROVES below), over a fixture shim whose injected bus holds
1,000 messages on each of personal, info and debug and records every read's kwargs:
  (1) each of the three panes calls read with limit=FEED_PANE_LIMIT and renders exactly that
      many entries, the newest, plus an older line naming 800;
  (2) no pane calls read without a limit.
Hollow: removing limit from ``_info_pane`` reds tooth 2.

    bin/cairn test cairn/tools/base/proofs/test_every_pane_reads_only_what_it_shows.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"86423bb5f054": {
    "1": "test_each_pane_renders_the_newest_limit_and_names_the_older",
    "2": "test_no_pane_reads_without_a_limit",
}}

TOTAL = 1000
PANES = (("_personal_feed_pane", "personal", "turns"),
         ("_info_pane", "info", "entries"),
         ("_debug_pane", "debug", "entries"))
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


class _Bus:
    """1,000 messages per channel, bodies numbered in channel order; every read is recorded."""

    def __init__(self) -> None:
        self.reads: list[dict] = []
        self.rows = {ch: [{"sender": "proof", "date": "2026-10-12T00:00:00", "body": {"n": i}}
                          for i in range(TOTAL)] for _p, ch, _k in PANES}

    def read(self, *, to=None, channel=None, reply_to=None, limit=None):
        self.reads.append({"to": to, "channel": channel, "limit": limit})
        rows = list(self.rows[channel])
        return rows if limit is None else rows[-limit:]

    def count(self, *, to=None, channel=None, reply_to=None):
        return len(self.rows[channel])


def _panes() -> tuple[dict, _Bus]:
    # Bound at call time: a reverted subject reds the teeth instead of crashing the reader.
    from cairn.tools.base.device import BaseDevice
    from cairn.tools.base.shim import BaseShim

    class _Shim(BaseShim):
        @property
        def device_id(self) -> str:
            return "spec"

        def device(self):
            return BaseDevice()

    bus = _Bus()
    shim = _Shim(bus=bus)
    out = {}
    for method, _ch, _key in PANES:
        pane = getattr(shim, method)()
        assert json.loads(json.dumps(pane)) == pane, "the pane is pure data"
        out[method] = pane
    return out, bus


def _limit() -> int | None:
    from cairn.tools.base import shim
    return getattr(shim, "FEED_PANE_LIMIT", None)


def test_each_pane_renders_the_newest_limit_and_names_the_older() -> None:
    limit = _limit()
    panes, bus = _panes()
    want = list(range(TOTAL - limit, TOTAL)) if isinstance(limit, int) else None
    older = TOTAL - limit if isinstance(limit, int) else None
    detail, ok = [], isinstance(limit, int)
    for method, ch, key in PANES:
        data = panes[method].get("data") or {}
        got = [e["body"].get("n") for e in data.get(key) or []]
        asked = [r["limit"] for r in bus.reads if r["channel"] == ch]
        note = str(data.get("older_note", ""))
        good = (asked == [limit] and got == want and data.get("older") == older
                and f"{older} older messages" in note)
        ok = ok and good
        detail.append(f"{method}: asked {asked}, {len(got)} shown, older {data.get('older')!r}")
    check("test_each_pane_renders_the_newest_limit_and_names_the_older", ok, "; ".join(detail))


def test_no_pane_reads_without_a_limit() -> None:
    _panes_, bus = _panes()
    unlimited = [r for r in bus.reads if r["limit"] is None]
    channels = sorted({r["channel"] for r in bus.reads})
    check("test_no_pane_reads_without_a_limit",
          not unlimited and channels == sorted(ch for _m, ch, _k in PANES),
          f"{len(bus.reads)} read(s) over {channels}; unlimited: {unlimited}")


def main() -> int:
    for tooth in (test_each_pane_renders_the_newest_limit_and_names_the_older,
                  test_no_pane_reads_without_a_limit):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
