"""Proof for ticket ``f09c594cf6d8`` — the inference domain shows its calls on the command line.

Akien, 2026-10-13: *"cairn inference_domain show/get calls --limit 20 --- show for me
(formatted), get for you (json)"*. Measured the same day: the calls were reachable only as the
bus verb ``calls`` (b905340f8162); declared_views held yield and models, so ``show calls``
answered 'no view'. A view takes arguments since 35b92c5de7ef, so ``calls`` becomes one,
delegating to the verb's own handler, and the verb stays for the librarian.

``domain.read_ticket`` is monkeypatched to record its kwargs and return two rows, so the live
cache is never read. Teeth, one per falsifier clause (PROVES below):
  (1) 'calls' is in InferenceDomainDevice().declared_views();
  (2) _calls_view(limit='2', since='2026-10-01T00:00:00') calls read_ticket with limit=2 and
      that since, and returns {'calls': [...]} that json.dumps accepts;
  (3) _render_view('calls', data) has one line per row carrying its verdict and its created
      second, and ends with '2 calls'.
Hollow: today's device.py reds 1-3.

    bin/cairn test cairn/devices/inference_domain/proofs/test_the_calls_are_a_view.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"f09c594cf6d8": {
    "1": "test_calls_is_a_declared_view",
    "2": "test_the_view_passes_limit_and_since_and_is_json",
    "3": "test_show_prints_one_line_per_call_and_a_count",
}}

SINCE = "2026-10-01T00:00:00"
ROWS = [
    {"id": 2, "created": datetime(2026, 10, 13, 12, 1, 7, 250000, tzinfo=timezone.utc),
     "verdict": "hit", "cost": Decimal("0"),
     "canonical": json.dumps({"kind": "generate", "prompt": "the newer row " + "x" * 120})},
    {"id": 1, "created": datetime(2026, 10, 13, 12, 0, 3, 500000, tzinfo=timezone.utc),
     "verdict": "miss", "cost": Decimal("42"),
     "canonical": json.dumps({"kind": "embed", "prompt": "the older row"})},
]
CALLS: list[dict] = []
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _device():
    """The device with read_ticket recording its kwargs — bound at call time, so a hollow
    device.py reds the tooth rather than the reader."""
    from cairn.devices.inference_domain import domain
    from cairn.devices.inference_domain.device import InferenceDomainDevice

    def fake_read_ticket(**kw):
        CALLS.append(kw)
        return [dict(r) for r in ROWS]

    domain.read_ticket = fake_read_ticket
    return InferenceDomainDevice()


def test_calls_is_a_declared_view() -> None:
    views = _device().declared_views()
    check("test_calls_is_a_declared_view", "calls" in views, f"views {sorted(views)}")


def test_the_view_passes_limit_and_since_and_is_json() -> None:
    CALLS.clear()
    data = _device()._calls_view(limit="2", since=SINCE)
    kw = CALLS[-1] if CALLS else {}
    try:
        json.dumps(data)
        dumps = True
    except TypeError:
        dumps = False
    ok = (kw.get("limit") == 2 and kw.get("since") == SINCE and isinstance(data, dict)
          and isinstance(data.get("calls"), list) and len(data["calls"]) == 2 and dumps)
    check("test_the_view_passes_limit_and_since_and_is_json", ok, f"kwargs {kw}, dumps {dumps}")


def test_show_prints_one_line_per_call_and_a_count() -> None:
    dev = _device()
    data = dev._calls_view(limit="2", since=SINCE)
    text = dev._render_view("calls", data)
    lines = text.rstrip("\n").splitlines()
    ok = (len(lines) == 3
          and "hit" in lines[0] and "2026-10-13" in lines[0] and "12:01:07" in lines[0]
          and "miss" in lines[1] and "12:00:03" in lines[1]
          and lines[-1].strip() == "2 calls")
    check("test_show_prints_one_line_per_call_and_a_count", ok, repr(text[:400]))


def main() -> int:
    for tooth in (test_calls_is_a_declared_view, test_the_view_passes_limit_and_since_and_is_json,
                  test_show_prints_one_line_per_call_and_a_count):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
