"""Proof for ticket ae8d2bfb08e2 — a BaseDevice that declares no reader of its mail keeps none of it.

The ruling (2026-09-30, CairnCommons/intentions-not-beside-code/I-heartbeat-probes-and-bus.md):
"if it's not consumed, it's trash" — and recorded is not consumed. Measured 2026-10-01: 127MB of
inbound mail sat in instance-space with ``last_read`` null on every recorder, because
``BaseDevice.receive`` recorded every envelope whether or not anything would ever read it.

Each tooth hands the fixture device a scratch DataRecorder (``_get_recorder`` honours a preset
``_recorder``), so no tooth touches the live instance root.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.tools.base.device import BaseDevice          # noqa: E402
from cairn.devices.tester.scratch import scratch_dir    # noqa: E402

PROVES = {
    "ae8d2bfb08e2": {
        "1": "test_an_undeclared_device_keeps_no_mail",
        "2": "test_a_declared_device_keeps_exactly_the_mail_it_got",
        "3": "test_both_devices_accept_the_mail",
    },
}

ENVELOPE = {"id": "env-fixture-1", "sender": "proof", "why": "fixture mail", "verb": "", "body": {"k": 1}}


class _Undeclared(BaseDevice):
    device_id = "unread_mail_fixture"

    def intention(self):
        return {"what": "unread mail fixture", "why": "prove undeclared mail is not kept"}

    def state(self):
        return {"resting": "test"}

    def settings(self):
        return {}


class _Declared(_Undeclared):
    RECORDER_ON_READ = "hold"
    RECORDER_READ_FREQUENCY_SECONDS = 60


def _fire(cls):
    DataRecorder = importlib.import_module("cairn.tools.data_recorder.data_recorder").DataRecorder
    dev = cls()
    dev._recorder = DataRecorder(scratch_dir("unread_mail_fixture_") / "inbound",
                                 expected_read_frequency_seconds=cls.RECORDER_READ_FREQUENCY_SECONDS,
                                 on_read=cls.RECORDER_ON_READ)
    reply = dev.receive(dict(ENVELOPE))
    return reply, dev._recorder.read()


def test_an_undeclared_device_keeps_no_mail():
    _reply, records = _fire(_Undeclared)
    assert records == [], records


def test_a_declared_device_keeps_exactly_the_mail_it_got():
    _reply, records = _fire(_Declared)
    assert len(records) == 1, records
    assert records[0]["envelope_id"] == "env-fixture-1", records[0]


def test_both_devices_accept_the_mail():
    for cls in (_Undeclared, _Declared):
        reply, _records = _fire(cls)
        assert reply.get("accepted") is True, (cls.__name__, reply)


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
