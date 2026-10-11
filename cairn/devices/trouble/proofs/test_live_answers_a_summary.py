"""THE LIVE VERB ANSWERS A SUMMARY ROW PER TROUBLE, NEVER THE WHOLE STORE (ticket fa9a2703a9c3).

Measured 2026-10-10: cairn's page asks this lane `live` over the bus on every render, the
reply is a personal message the bus keeps (Law 7), and it carried every live trouble with its
occurrence tail and detail — ~355 KB a reply, ~4,474 of them, ~1.5 GB in the bus. Both bus
callers (cairn's trouble pane, the web server's troubles socket) keep six keys at most.

WHAT THIS PROVES, on a scratch store of 3 live troubles raised 50 times each with a detail:
  (1) _handle_live({}) answers 3 rows, each with exactly the six summary keys and the store's
      own values for them;
  (2) the JSON of that answer is under 4 KB, and 50 more occurrences of each trouble leave its
      size unchanged — the reply grows with the number of troubles, never with their history.

Hollow: _handle_live returning self.live() reds both (extra keys; the detail-laden occurrence
tails put the answer far over 4 KB).

    python3 cairn/devices/trouble/proofs/test_live_answers_a_summary.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

PROVES = {"fa9a2703a9c3": {
    "1": "test_live_answers_one_summary_row_per_trouble",
    "2": "test_the_live_answer_does_not_grow_with_history",
}}

# The ticket's six keys, spelled here rather than imported: the proof states the contract and
# the module's LIVE_SUMMARY_KEYS is what it judges.
SIX = {"id", "standing", "why", "count", "first_seen", "last_seen"}
IDENTS = ("a-proof-trouble-one", "a-proof-trouble-two", "a-proof-trouble-three")
DETAIL = {"payload": "x" * 200, "where": "a scratch store under a proof"}


def _store(tmp: Path, times: int = 50):
    from cairn.devices.trouble.trouble import TroubleDevice  # at call time (hollow-safe)
    dev = TroubleDevice(root=tmp)
    dev.set_diagnostic_receiver(None)  # keep this proof's trail out of the live logs tree
    for ident in IDENTS:
        for i in range(times):
            dev.raise_trouble(ident, why=f"the proof raised {ident}", detail={**DETAIL, "n": i})
    return dev


def test_live_answers_one_summary_row_per_trouble():
    with tempfile.TemporaryDirectory() as d:
        dev = _store(Path(d))
        rows = dev._handle_live({})["troubles"]
        held = {t["id"]: t for t in dev.live()}
        assert len(rows) == 3, len(rows)
        for r in rows:
            assert set(r) == SIX, sorted(r)
            assert all(r[k] == held[r["id"]][k] for k in SIX), r


def test_the_live_answer_does_not_grow_with_history():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        dev = _store(tmp)
        size = len(json.dumps(dev._handle_live({})))
        assert size < 4096, size
        for ident in IDENTS:
            for i in range(50):
                dev.raise_trouble(ident, why=f"the proof raised {ident}",
                                  detail={**DETAIL, "n": 50 + i})
        again = dev._handle_live({})
        # last_seen restamps at the same width; count moves 50 -> 100, which is one digit wider
        # per trouble (first measured run: 648 -> 651). So the answer's SIZE is the invariant
        # once the counts' own digits are taken out — nothing the 50 raises carried rides along.
        widened = sum(len(str(t["count"])) - 2 for t in again["troubles"])
        assert len(json.dumps(again)) - widened == size, (size, len(json.dumps(again)), widened)


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
