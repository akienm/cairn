#!/usr/bin/env python3
"""Proof that sail's chart call waits as long as a gate's answer can take (ticket 8b171277190c).

WHAT IT PROVES: cairn/devices/cc/scripts/sail.py chart() handed Ticket.chart a 120 s timeout
(GATE_TIMEOUT_S). Codemother's constrain gate runs every proof of the component as instruments;
for the tester that took many minutes, so sail gave up while codemother kept going. The chart
now waits CHART_TIMEOUT_S (890 s, below the bus socket's 900 s, the way the verdict does);
clearance keeps its 120 s.

Both teeth load sail by path at call time and patch its ``_ticket`` to a stub that records the
timeout it is handed. No bus, no ticket store.

Teeth, one per falsifier clause (PROVES below):
  (1) chart() hands Ticket.chart a timeout equal to sail.CHART_TIMEOUT_S and at least 890 s;
  (2) cross() hands clearance's queueme sail.GATE_TIMEOUT_S, still 120 s.

    python3 cairn/devices/cc/proofs/test_a_chart_waits_as_long_as_a_gate_can_take.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"8b171277190c": {
    "1": "test_chart_hands_the_ticket_the_long_timeout",
    "2": "test_clearance_keeps_the_short_timeout",
}}

_SAIL = _REPO_ROOT / "cairn" / "devices" / "cc" / "scripts" / "sail.py"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _sail():
    spec = importlib.util.spec_from_file_location("cc_sail_chart_timeout_proof", _SAIL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Stub:
    """Stands in for the Ticket: records the timeout each call is handed."""

    def __init__(self):
        self.chart_timeout = None
        self.queueme_timeout = None

    def chart(self, *, participant, timeout, stages):
        self.chart_timeout = timeout
        return {"charted": True, "stages": [], "stopped_at": None}

    def queueme(self, gate, *, participant, timeout):
        self.queueme_timeout = timeout
        return {"accepted": True}


def test_chart_hands_the_ticket_the_long_timeout() -> None:
    name = PROVES["8b171277190c"]["1"]
    try:
        sail = _sail()
        stub = _Stub()
        sail._ticket = lambda tid, tickets_dir=None: stub
        sail.chart("fixture8b17a", participant=object(), out=lambda s: None, err=lambda s: None)
        want = getattr(sail, "CHART_TIMEOUT_S", None)
        got = stub.chart_timeout
        ok = want is not None and got == want and got >= 890.0
        check(name, ok, f"chart handed timeout={got}, CHART_TIMEOUT_S={want}")
    except Exception as exc:  # noqa: BLE001 — the unbuilt subject reds the tooth, never crashes the reader
        check(name, False, f"{type(exc).__name__}: {exc}")


def test_clearance_keeps_the_short_timeout() -> None:
    name = PROVES["8b171277190c"]["2"]
    try:
        sail = _sail()
        stub = _Stub()
        sail._ticket = lambda tid, tickets_dir=None: stub
        try:
            sail.cross("fixture8b17a", participant=object(), out=lambda s: None)
        except Exception:  # noqa: BLE001 — only the timeout the call reached the stub with matters
            pass
        got = stub.queueme_timeout
        check(name, got == sail.GATE_TIMEOUT_S == 120.0, f"clearance handed timeout={got}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    test_chart_hands_the_ticket_the_long_timeout()
    test_clearance_keeps_the_short_timeout()
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
