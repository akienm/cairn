"""Proof for ticket da29186ef039 — a clearance that never answered is unanswered, never refused.

Measured 2026-11-18 on ticket 8c5fdb750b75: sail.py printed 'clearance refused ... no reply within
120.0s' and close.sh committed 'PROVED refused at clearance', while the gate was still sweeping;
minutes later it crossed the ticket to PROVED with a clean build gate.

1. a clearance whose bus request raises TimeoutError makes sail.py cross return 3 and say
   'did not answer', and never 'refused';
2. a clearance answering accepted False still makes sail.py cross return 1 and say 'refused' with
   the gate's reason;
3. close.sh names an RC 3 crossing 'clearance unanswered' and exits 3, and its 'PROVED refused'
   commit is reached only on another non-zero RC.

Teeth 1 and 2 run in the scratch world of test_sail_queues_the_ticket_at_codemothers_gates.py
(borrowed by path at call time); tooth 3 reads close.sh's branches.

    python3 cairn/devices/cc/proofs/test_an_unanswered_clearance_is_not_a_refusal.py   # exit 0 = green
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "da29186ef039": {
        "1": "test_a_timed_out_clearance_is_unanswered",
        "2": "test_a_refusing_clearance_is_still_refused",
        "3": "test_close_names_an_unanswered_crossing_unanswered",
    },
}

_HERE = Path(__file__).resolve().parent
_CLOSE = _REPO_ROOT / "cairn" / "devices" / "cc" / "scripts" / "close.sh"


def _harness():
    spec = importlib.util.spec_from_file_location(
        "cc_sail_gates_harness", _HERE / "test_sail_queues_the_ticket_at_codemothers_gates.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _SilentBus:
    """A bus whose every request times out, as Bus.request does when the target never replies."""

    def __init__(self):
        self.requests: list[dict] = []

    def request(self, **kw):
        self.requests.append(kw)
        raise TimeoutError("no reply to envelope fixture… from codemother within 120.0s — "
                           "the target did not reply (CP1: loud, not empty)")

    def post(self, **kw):
        return {"id": "post-1"}


def test_a_timed_out_clearance_is_unanswered():
    h = _harness()
    sail = h._sail()
    with h._world("PROVEME") as w:
        said, out = h._quiet()
        rc = sail.cross(h._TID, participant=sail.Asker(_SilentBus()), tickets_dir=w["store"],
                        out=out, err=out)
        assert rc == 3, f"rc={rc}: {said}"
        assert any("did not answer" in s for s in said), said
        assert not any("refused" in s for s in said), said


def test_a_refusing_clearance_is_still_refused():
    h = _harness()
    sail = h._sail()
    with h._world("PROVEME") as w:
        bus = h._Bus([{"body": {"accepted": False, "reason": "ExitGateRed: no verdict"}}])
        said, out = h._quiet()
        rc = sail.cross(h._TID, participant=sail.Asker(bus), tickets_dir=w["store"],
                        out=out, err=out)
        assert rc == 1, f"rc={rc}: {said}"
        assert any("refused" in s and "ExitGateRed: no verdict" in s for s in said), said


def test_close_names_an_unanswered_crossing_unanswered():
    text = _CLOSE.read_text(encoding="utf-8")
    m = re.search(r'if \[ \$RC -eq 3 \]; then\n(.*?)\nfi', text, re.S)
    assert m, "close.sh has no RC 3 branch"
    branch = m.group(1)
    assert 'commit_all "clearance unanswered"' in branch, branch
    assert "exit 3" in branch, branch
    assert text.index("$RC -eq 3") < text.index('commit_all "PROVED refused at clearance"'), \
        "the RC 3 branch must come before the refused commit"


if __name__ == "__main__":
    failed = 0
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception as exc:  # noqa: BLE001 — every tooth reports, red or raising
                failed += 1
                print(f"FAIL {_name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failed else 0)
