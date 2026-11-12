"""Proof for ticket 1c5e0e7a9d42 — a nested drain hands each envelope over once.

Measured 2026-11-12 03:09:50-51 UTC (bus emissions under ~/.cairn/logs/bus/0): three asks CC
had given up on were delivered to codemother 2, 2 and 3 times in 1.7 s. ``_check_mail`` works
from a snapshot of ``undelivered``. codemother's handler asks inference_domain, and while that
request waits the bus server drains codemother again (``_serve_held``). The inner drain took
the rest of the snapshot, and then the outer loop handed each of those envelopes over a second
time. The first reply to each ask was receipted bus-asker-gave-up; the four after it stood
undelivered as mail-cc-stood-600s.

The world is an in-memory bus (undelivered / record_delivery) and a shim whose device, on its
first envelope, drains its own mailbox from inside the handler — the re-entry the server's
_serve_held makes. No store, no live bus.

One composite tooth answers both clauses (the second clause alone passes without the build; it guards
the fix from over-reaching):

  1. with three envelopes waiting and the first handler draining from inside, each envelope
     reaches the device exactly once and each is receipted once;
  2. mail that arrives after the outer drain returns is still delivered by the next drain,
     so the guard does not outlive its batch.

    python3 cairn/tools/base/proofs/test_a_nested_drain_takes_each_envelope_once.py   # exit 0 = green
"""
from __future__ import annotations

import importlib
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

PROVES = {
    "1c5e0e7a9d42": {"1": "test_a_nested_drain_hands_each_envelope_over_once",
                     "2": "test_a_nested_drain_hands_each_envelope_over_once"},
}


class _Bus:
    """The two calls _check_mail makes, over a list."""

    def __init__(self, ids):
        self.mail = [{"id": i, "sender": "proof", "why": "fixture", "verb": "", "body": {}}
                     for i in ids]
        self.receipts: Counter = Counter()

    def undelivered(self, *, to, limit):
        return [dict(e) for e in self.mail if self.receipts[e["id"]] == 0][:limit]

    def record_delivery(self, eid, *, to, by):
        self.receipts[eid] += 1


class _Device:
    def __init__(self, shim):
        self.shim = shim
        self.got: Counter = Counter()

    def receive(self, envelope):
        self.got[envelope["id"]] += 1
        if envelope["id"] == "env-1":
            # The handler asks; while it waits, the server drains this mailbox again.
            self.shim._check_mail()
        return "handled"


def _shim(bus):
    BaseShim = importlib.import_module("cairn.tools.base.shim").BaseShim

    class _Fixture(BaseShim):
        @property
        def device_id(self):
            return "nested_drain_fixture"

        def probes(self):
            return []

        def _start_device(self):
            return _Device(self)

        def _clear_mail_troubles(self, envelope, taken):
            return None

    shim = _Fixture(bus=bus)
    shim._device = shim._start_device()
    return shim


def test_a_nested_drain_hands_each_envelope_over_once():
    bus = _Bus(["env-1", "env-2", "env-3"])
    shim = _shim(bus)
    shim._check_mail()
    got = shim._device.got
    assert got == Counter({"env-1": 1, "env-2": 1, "env-3": 1}), got
    assert bus.receipts == Counter({"env-1": 1, "env-2": 1, "env-3": 1}), bus.receipts
    # The guard does not outlive its batch: later mail is still delivered.
    bus.mail.append({"id": "env-4", "sender": "proof", "why": "later", "verb": "", "body": {}})
    shim._check_mail()
    assert shim._device.got["env-4"] == 1, shim._device.got
    assert bus.receipts["env-4"] == 1, bus.receipts


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
