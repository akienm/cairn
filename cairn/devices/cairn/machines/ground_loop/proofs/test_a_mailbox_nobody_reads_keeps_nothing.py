"""Proof for ticket 0bcd51173524 — a discovered device's mailbox keeps no mail it has no reader for.

Sibling of ae8d2bfb08e2 (BaseDevice). ``_FeedbackDevice`` is the mailbox every discovered
device's shim holds; it recorded every envelope whether or not anything would ever read it. The
ruling (2026-09-30, CairnCommons/intentions-not-beside-code/I-heartbeat-probes-and-bus.md): "if
it's not consumed, it's trash".

Each tooth hands the mailbox a scratch DataRecorder (``_get_recorder`` honours a preset
``_recorder``), so no tooth touches the live instance root. The module under proof is resolved
inside each tooth, so a reverted build reds teeth instead of killing the import.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

from cairn.tools.scratch.scratch import scratch_dir    # noqa: E402

PROVES = {
    "0bcd51173524": {
        "1": "test_an_undeclared_mailbox_keeps_no_mail",
        "2": "test_a_declared_mailbox_keeps_exactly_the_mail_it_got",
        "3": "test_both_mailboxes_accept_the_mail",
    },
}

ENVELOPE = {"id": "env-fixture-1", "sender": "proof", "why": "fixture mail", "verb": "", "body": {"k": 1}}


def _fire(declared: bool):
    D = importlib.import_module("cairn.devices.cairn.machines.ground_loop.discovered")
    DataRecorder = importlib.import_module("cairn.tools.data_recorder.data_recorder").DataRecorder
    cls = D._FeedbackDevice
    if declared:
        cls = type("_Declared", (D._FeedbackDevice,),
                   {"RECORDER_ON_READ": "hold", "RECORDER_READ_FREQUENCY_SECONDS": 60})
    dev = cls("mailbox_fixture")
    dev._recorder = DataRecorder(scratch_dir("mailbox_fixture_") / "inbound",
                                 expected_read_frequency_seconds=cls.RECORDER_READ_FREQUENCY_SECONDS,
                                 on_read=cls.RECORDER_ON_READ)
    reply = dev.receive(dict(ENVELOPE))
    return reply, dev._recorder.read()


def test_an_undeclared_mailbox_keeps_no_mail():
    _reply, records = _fire(False)
    assert records == [], records


def test_a_declared_mailbox_keeps_exactly_the_mail_it_got():
    _reply, records = _fire(True)
    assert len(records) == 1, records
    assert records[0]["envelope_id"] == "env-fixture-1", records[0]


def test_both_mailboxes_accept_the_mail():
    for declared in (False, True):
        reply, _records = _fire(declared)
        assert reply == {"accepted": True, "device": "mailbox_fixture"}, (declared, reply)


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
