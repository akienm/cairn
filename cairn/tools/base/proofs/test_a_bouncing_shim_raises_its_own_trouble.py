"""PROOF for ticket eff2fb9810de: a shim that bounces mail raises the trouble at its own address.

Measured 2026-11-10 before the build: ``BaseShim._bounce_to_sender`` posted the bounce with
``body.trouble`` named and raised nothing, so only the SENDER's ``handle_bounce`` ever raised.
Akien's answer (CairnCommons/questions/open-b9037ca75019.json): the component that cannot fill a
request issues the trouble and reports it to the caller; the sender may add to it, "writing is
not safe, but appending is." The sender's raise under the same identity is that addition, and
the trouble lane folds the two on the identity.

  1. mail to an undeclared verb: the receiving shim raises one trouble
     mail-<device>-has-no-verb-<verb>, its detail naming the sender, the verb and the envelope
     id, and the bounce it posts names the same identity;
  2. a handler that raises: the receiving shim raises mail-<device>-verb-<verb>-raised, and the
     handler's own exception still propagates;
  3. no verb, no receive(): the receiving shim raises mail-<device>-has-no-receive;
  4. a raise_trouble that itself raises does not stop or change the bounce, and stderr says so;
  5. answered mail raises nothing, and test_bounce_raises_the_mail_trouble.py passes unchanged.

Diagnostics go to a list receiver; the bus is a spy. Every name is ``testing-eff2-...``.

    python3 cairn/tools/base/proofs/test_a_bouncing_shim_raises_its_own_trouble.py
"""
from __future__ import annotations

import contextlib
import io
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.shim import BaseShim  # noqa: E402

PROVES = {"eff2fb9810de": {
    "1": "the_undeclared_verb_raises_at_the_receiver",
    "2": "the_raising_handler_raises_at_the_receiver",
    "3": "no_receive_raises_at_the_receiver",
    "4": "a_failed_raise_still_bounces",
    "5": "answered_mail_raises_nothing",
}}

PASS = 0
FAIL = 0
_ME = "testing-eff2-me"
_FRIEND = "testing-eff2-friend"
_STANDING = _REPO_ROOT / "cairn/tools/base/proofs/test_bounce_raises_the_mail_trouble.py"


class _Inbox:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def receive_diagnostic(self, record: dict) -> None:
        self.records.append(record)

    def lane(self, gate: str) -> list[dict]:
        return [r for r in self.records if r.get("gate") == gate]


class _SpyBus:
    def __init__(self) -> None:
        self.posted: list[dict] = []

    def post(self, **envelope) -> dict:
        envelope = {"id": f"testing-eff2-post-{len(self.posted)}", **envelope}
        self.posted.append(envelope)
        return envelope

    def undelivered(self, to=None, limit=50) -> list[dict]:
        return []

    def record_delivery(self, envelope_id, *, to, by) -> None:
        pass

    def wire_delivery(self, device_id, deliver) -> None:
        pass

    def read(self, **kw) -> list[dict]:
        return []

    def bounces(self) -> list[dict]:
        return [e for e in self.posted if (e.get("body") or {}).get("is_bounce")]


class _Boom(Exception):
    pass


class _Device:
    def declared_verbs(self):
        return {"ping": lambda envelope: {"pong": True}, "boom": self._boom}

    @staticmethod
    def _boom(envelope):
        raise _Boom("testing-eff2 the handler fell over")


class _Deaf:
    """A device with verbs but no receive()."""

    def declared_verbs(self):
        return {"ping": lambda envelope: {"pong": True}}


class _Shim(BaseShim):
    def __init__(self, bus, device_cls=_Device) -> None:
        self._device_cls = device_cls
        super().__init__(bus=bus)
        self.inbox = _Inbox()
        self.set_diagnostic_receiver(self.inbox)

    @property
    def device_id(self) -> str:
        return _ME

    def _start_device(self):
        return self._device_cls()


def _letter(n: int, verb: str = "") -> dict:
    return {"id": f"testing-eff2-letter-{n}", "sender": _FRIEND, "addressee": _ME,
            "channel": "personal", "verb": verb, "body": {}}


def _raised(shim) -> list[str]:
    return [r["pointer"] for r in shim.inbox.lane("raise_trouble")]


def the_undeclared_verb_raises_at_the_receiver():
    bus = _SpyBus()
    shim = _Shim(bus)
    shim.deliver(_letter(1, verb="no_such_verb"))
    identity = f"mail-{_ME}-has-no-verb-no_such_verb"
    assert _raised(shim) == [identity], _raised(shim)
    detail = shim.inbox.lane("raise_trouble")[0]["values"]["detail"]
    assert detail.get("sender") == _FRIEND and detail.get("original_verb") == "no_such_verb" \
        and detail.get("envelope") == "testing-eff2-letter-1", detail
    assert [b["body"]["trouble"] for b in bus.bounces()] == [identity], bus.bounces()


def the_raising_handler_raises_at_the_receiver():
    bus = _SpyBus()
    shim = _Shim(bus)
    try:
        shim.deliver(_letter(1, verb="boom"))
    except _Boom:
        pass
    else:
        raise AssertionError("the handler's own exception did not propagate")
    identity = f"mail-{_ME}-verb-boom-raised"
    assert _raised(shim) == [identity], _raised(shim)
    assert [b["body"]["trouble"] for b in bus.bounces()] == [identity], bus.bounces()


def no_receive_raises_at_the_receiver():
    bus = _SpyBus()
    shim = _Shim(bus, device_cls=_Deaf)
    shim.deliver(_letter(1))
    identity = f"mail-{_ME}-has-no-receive"
    assert _raised(shim) == [identity], _raised(shim)
    assert [b["body"]["trouble"] for b in bus.bounces()] == [identity], bus.bounces()


def a_failed_raise_still_bounces():
    bus_ok, bus_bad = _SpyBus(), _SpyBus()
    _Shim(bus_ok).deliver(_letter(1, verb="no_such_verb"))
    shim = _Shim(bus_bad)
    calls = []

    def broken(*a, **kw):
        calls.append(a)
        raise RuntimeError("testing-eff2 the trouble lane is down")

    shim.raise_trouble = broken
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        out = shim.deliver(_letter(1, verb="no_such_verb"))
    assert calls, "raise_trouble was never called, so its failure was never exercised"
    assert isinstance(out, dict) and out.get("bounced") is True, out
    strip = lambda es: [{k: v for k, v in e.items() if k != "id"} for e in es]  # noqa: E731
    assert strip(bus_bad.bounces()) == strip(bus_ok.bounces()) and bus_bad.bounces(), (
        bus_bad.bounces(), bus_ok.bounces())
    line = err.getvalue()
    assert f"mail-{_ME}-has-no-verb-no_such_verb" in line and "lane is down" in line, line


def answered_mail_raises_nothing():
    bus = _SpyBus()
    shim = _Shim(bus)
    out = shim.deliver(_letter(1, verb="ping"))
    assert out == {"pong": True}, out
    assert _raised(shim) == [] and bus.bounces() == [], (_raised(shim), bus.bounces())
    r = subprocess.run([sys.executable, str(_STANDING)], cwd=_REPO_ROOT,
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-800:]


TEETH = [the_undeclared_verb_raises_at_the_receiver,
         the_raising_handler_raises_at_the_receiver,
         no_receive_raises_at_the_receiver,
         a_failed_raise_still_bounces,
         answered_mail_raises_nothing]


def _tooth(fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {fn.__name__}")


if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
