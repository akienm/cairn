"""PROOF — a message sent to CC is ledgered when it lands and when a CC session reads it
(ticket 078476729bca).

The probe the_shim_delivers_mail used to trigger on ``context['diagnostics_received']``, a
key nothing sets, so it could never fire or conclude. The build gives it a real source: the
shim appends a 'delivered' line to ``mail_ledger.jsonl`` when deliver() persists an envelope,
and a 'consumed' line naming the CC session when consume_mail() removes one. The probe counts
that ledger.

What a hollow build cannot pass (Law 8):
  - No ledger: deliver() and consume_mail() write nothing, so a_delivery_is_ledgered and
    a_consumption_names_its_session read zero lines.
  - The old probe: its trigger reads a context key, so an empty context never fires and the
    enough/holds teeth find no ledger to read.

Every tooth runs over a temporary directory: shim._MAIL_DIR, shim._LEDGER and the probe's
LEDGER point inside it and are restored after. The shim and the probe are imported inside the
teeth, never at module level — this build adds what they bind.

    python3 cairn/devices/cc/proofs/test_the_shim_delivers_mail.py   # exit 0 = green
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "078476729bca": {
        "1": "test_the_device_is_whole",
        "2": "test_the_probes_load_with_zero_failures",
        "3": "test_a_consumption_names_its_session",
    },
}

_DEVICE = _REPO_ROOT / "cairn" / "devices" / "cc"


@contextmanager
def _sandbox():
    """Point the shim and the probe at a temporary mail dir and ledger; restore after."""
    from cairn.devices.cc import shim
    from cairn.devices.cc.probes import the_shim_delivers_mail as probe
    saved = (shim._MAIL_DIR, shim._LEDGER, probe.LEDGER, os.environ.get("CLAUDE_CODE_SESSION_ID"))
    with tempfile.TemporaryDirectory(prefix="cc-mail-ledger-proof-") as tmp:
        root = Path(tmp)
        shim._MAIL_DIR = root / "mail"
        shim._LEDGER = probe.LEDGER = root / "mail_ledger.jsonl"
        try:
            yield shim, probe, root
        finally:
            shim._MAIL_DIR, shim._LEDGER, probe.LEDGER = saved[:3]
            if saved[3] is None:
                os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
            else:
                os.environ["CLAUDE_CODE_SESSION_ID"] = saved[3]


def _consume_as(shim, session: str) -> list[dict]:
    os.environ["CLAUDE_CODE_SESSION_ID"] = session
    return shim.CCShim.consume_mail()


def _lines(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


# --- teeth ------------------------------------------------------------------

def test_the_device_is_whole():
    """Clause (1): the device has its charter, a shim inheriting BaseShim, and a probe."""
    from cairn.devices.cc.shim import CCShim
    from cairn.tools.base.shim import BaseShim
    assert (_DEVICE / "intention+why.json").is_file(), "no charter beside the cc device"
    assert issubclass(CCShim, BaseShim), "CCShim does not inherit BaseShim"
    assert (_DEVICE / "probes" / "the_shim_delivers_mail.py").is_file(), "the mail probe is gone"


def test_the_probes_load_with_zero_failures():
    """Clause (2): the ground loop's probe cache loads the cc probe folder with no failures."""
    from cairn.devices.cairn.machines.ground_loop.discovery import ProbeCache
    probes, failures = ProbeCache().probes_for(_DEVICE / "probes")
    assert not failures, f"probe loading failures: {failures}"
    assert any("bus messages" in p.why for p in probes), \
        f"the mail probe did not load: {[p.why[:40] for p in probes]}"


def test_a_delivery_is_ledgered():
    with _sandbox() as (shim, probe, root):
        out = shim.CCShim().deliver({"from": "proof", "body": "hello"})
        lines = _lines(shim._LEDGER)
        assert [x["event"] for x in lines] == ["delivered"], lines
        assert lines[0]["id"] == Path(out["path"]).stem, (lines[0], out)
        assert lines[0]["from"] == "proof", lines[0]
        assert probe._trigger(None, {}) is True, "a ledgered delivery did not trigger the probe"


def test_a_consumption_names_its_session():
    """Clause (3): a message sent through the shim's channel reaches a CC session, and the
    ledger names which one read it."""
    with _sandbox() as (shim, probe, root):
        out = shim.CCShim().deliver({"from": "proof", "body": "hello"})
        got = _consume_as(shim, "s1")
        assert [m["id"] for m in got] == [Path(out["path"]).stem], got
        consumed = [x for x in _lines(shim._LEDGER) if x["event"] == "consumed"]
        assert len(consumed) == 1, consumed
        assert consumed[0]["id"] == Path(out["path"]).stem and consumed[0]["session"] == "s1", consumed


def test_enough_needs_two_sessions():
    with _sandbox() as (shim, probe, root):
        for _ in range(3):
            shim.CCShim().deliver({"from": "proof"})
            _consume_as(shim, "s1")
        assert probe._enough({}) is False, "three reads in ONE session concluded the watch"
        shim.CCShim().deliver({"from": "proof"})
        _consume_as(shim, "s2")
        assert probe._enough({}) is True, "four reads across two sessions did not conclude"
        carry = probe._carry({})
        assert carry["delivered"] == 4 and carry["consumed"] == 4, carry
        assert carry["sessions"] == ["s1", "s2"], carry
        assert len(carry["delivery_times"]) == 3, carry


def test_an_empty_ledger_never_fires():
    with _sandbox() as (shim, probe, root):
        assert not shim._LEDGER.exists()
        assert probe._trigger(None, {}) is False, "an empty ledger triggered"
        assert probe._enough({}) is False, "an empty ledger concluded"
        assert probe.PROBE.payload({})["holds"] is True, "an empty ledger read as failing"


def test_undelivered_mail_fails_after_a_day():
    with _sandbox() as (shim, probe, root):
        old = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        shim._ledger({"event": "delivered", "id": "msg-old", "at": old, "from": "proof"})
        payload = probe.PROBE.payload({})
        assert payload["holds"] is False, payload
        assert payload["finding"].strip(), payload
        shim._ledger({"event": "consumed", "id": "msg-old",
                      "at": datetime.now(timezone.utc).isoformat(), "session": "s1"})
        assert probe.PROBE.payload({})["holds"] is True, "read mail still reads as failing"


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
