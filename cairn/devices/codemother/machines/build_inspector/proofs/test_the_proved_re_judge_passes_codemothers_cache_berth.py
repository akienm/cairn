"""The PROVED re-judge passes codemother's cache berth to proof_coverage.lacks (ticket b64847df255d).

Clause (1) of b64847df255d says an inspect's proof_covers_the_ticket answers an unchanged ticket
warm. Its proof_coverage proof measures the cache inside lacks(); nothing there can see whether
the inspector ever hands it one. Measured 2026-11-23 at PROVEME: the hollow reverted inspector.py
and no tooth went red, so the wiring half of the build stood unproven. This tooth is that half,
and it lives here because the call site is codemother's code (RULE 1): proof_coverage's proofs
measure proof_coverage only.

The tooth stubs proof_coverage.load_tickets with one ticket at PROVEME and proof_coverage.lacks
with a recorder, runs the sieve, and reads the keyword the inspector passed. No house ticket is
judged and nothing is written. The berth expected is the holder's tool-instance address (Law 6):
``address.instance_path("codemother", 0) / "tools" / "proof_coverage" / "0"``.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(_REPO))

from cairn.devices.codemother.machines.build_inspector import inspector  # noqa: E402
from cairn.tools import proof_coverage  # noqa: E402
from cairn.tools.base import address  # noqa: E402

PROVES = {"b64847df255d": {
    "1": "test_the_re_judge_passes_codemothers_cache_berth",
}}

FAILURES: list[str] = []
_TICKET = {"id": "cachewire0001", "title": "a fixture ticket at PROVEME",
           "workflow_and_state": "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME:waiting] -> PROVED"}


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}  — {detail}")
    if not ok:
        FAILURES.append(name)


def test_the_re_judge_passes_codemothers_cache_berth() -> None:
    calls: list[dict] = []

    def _recorder(ticket, **kw):
        calls.append({"ticket": ticket.get("id"), **kw})
        return []

    saved = (proof_coverage.load_tickets, proof_coverage.lacks)
    proof_coverage.load_tickets = lambda commons: [dict(_TICKET)]
    proof_coverage.lacks = _recorder
    try:
        inspector.proof_covers_the_ticket(_REPO / "cairn")
    finally:
        proof_coverage.load_tickets, proof_coverage.lacks = saved
    want = address.instance_path("codemother", 0) / "tools" / "proof_coverage" / "0"
    got = calls[0].get("cache") if calls else None
    check("test_the_re_judge_passes_codemothers_cache_berth",
          len(calls) == 1 and got is not None and Path(got) == want,
          f"{len(calls)} lacks call(s); cache={got!r}, want {str(want)!r}")


if __name__ == "__main__":
    test_the_re_judge_passes_codemothers_cache_berth()
    print(f"{len(FAILURES)} failed" if FAILURES else "all teeth green")
    raise SystemExit(1 if FAILURES else 0)
