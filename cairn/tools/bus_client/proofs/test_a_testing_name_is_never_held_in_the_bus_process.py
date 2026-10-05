"""Proof for ticket 39dbe8e8316b — the bus client never holds a testing-named device in the
instance's bus process, so a shim a proof stands up on the live bus pulses without wiring and
touches no live device's mail.

Child 2 of 71d1bbfa98b0 (everything born of a test is flagged), split per component under RULE 1
(Akien, 2026-10-01). Test against live, marked as testing (ruled 2026-09-28, extended
2026-10-04). Under the one-bus-process model (48519f4789b1) a shim's first pulse calls
``BaseShim._wire_delivery`` -> ``RemoteBus.wire_delivery(device_id)`` -> ``hold(device_id)`` in
the bus process. MEASURED 2026-10-05 at HEAD 94334efb: a ``testing-…`` shim pulsed on
``bus_client.reach()`` raises LookupError out of its first pulse ("no shim answers to
'testing-probe-…'"), which is why the system_rackmount pilot (20a97889646e) wrapped the live bus
in a ``_TestingBus`` declining ``wire_delivery`` — each proof keeping the mark as policy.

WHERE THE REFUSAL LIVES, MEASURED. A first build put it in ``BaseShim._wire_delivery`` and reddened
cairn/devices/cairn/machines/bus/proofs/test_a_requester_takes_its_reply.py (0/3) and
test_mail_without_a_receiver.py (5/8): a bus process (or a private in-process bus) legitimately
wires ``testing-`` shims it holds itself — delivery happens in the same process. The hazard is
only the crossing: a client asking the LIVE bus process to hold a name that exists only inside a
proof. ``RemoteBus.wire_delivery`` is that crossing, so the refusal is the client's.

This proof measures only cairn/tools/bus_client (RULE 1).

  1. A TESTING SHIM ON THE LIVE BUS IS NEVER HELD THERE. A shim whose device_id is
     ``testing-39dbe8e8316b-<8hex>``, holding cairn.tools.bus_client.bus_client.reach() (with the
     RemoteBus's socket calls written down on the way through), pulses twice without raising,
     and no ``hold`` request naming it reaches the bus process.
  2. IT TOUCHES NO LIVE DEVICE'S MAIL. Every mail call that shim makes on the bus (undelivered,
     read, record_delivery) names its own testing id and nothing else.
  3. THE REFUSAL IS NARROW. ``RemoteBus.wire_delivery`` for an unmarked name still sends exactly
     one ``hold`` request naming it (measured with the socket call recorded and answered locally,
     so no live device is held by the proof).

    python3 cairn/tools/bus_client/proofs/test_a_testing_name_is_never_held_in_the_bus_process.py
"""
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"39dbe8e8316b": {"1": "a_testing_shim_on_the_live_bus_is_never_held_there",
                           "2": "it_touches_no_live_devices_mail",
                           "3": "the_refusal_is_narrow"}}

MARK = "testing-39dbe8e8316b-"
MAIL_OPS = ("undelivered", "read", "record_delivery")
PASS = 0
FAIL = 0
_RUN: dict = {}


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


class _Recording:
    """The bus reach() handed out, with every mail call written down on the way through."""

    def __init__(self, bus, log):
        self._bus, self._log = bus, log

    def __getattr__(self, name):
        target = getattr(self._bus, name)
        if name not in MAIL_OPS:
            return target

        def call(*a, **k):
            self._log.append((name, k.get("to")))
            return target(*a, **k)
        return call


def _pulsed_testing_shim():
    """Stand the testing shim up on the live bus once, pulse it twice, and keep what it did."""
    if _RUN:
        return _RUN
    from cairn.tools.base.shim import BaseShim
    from cairn.tools.bus_client import bus_client
    remote = bus_client.reach()
    socket_calls: list = []
    real_call = remote._call

    def recorded(request, _real=real_call):
        socket_calls.append(dict(request))
        return _real(request)
    remote._call = recorded
    mail: list = []
    device_id = f"{MARK}{uuid.uuid4().hex[:8]}"
    shim = type("_Probe", (BaseShim,), {"device_id": device_id})(_Recording(remote, mail))
    shim.set_diagnostic_receiver(None)     # HOLD: emissions stay in memory, nothing reaches disk
    _RUN.update(device_id=device_id, socket_calls=socket_calls, mail=mail, error=None)
    try:
        shim.on_pulse(datetime.now(timezone.utc))
        shim.on_pulse(datetime.now(timezone.utc))
    except Exception as exc:  # noqa: BLE001 — recorded, and tooth 1 reports it
        _RUN["error"] = f"{type(exc).__name__}: {exc}"
    return _RUN


def a_testing_shim_on_the_live_bus_is_never_held_there():
    run = _pulsed_testing_shim()
    assert run["error"] is None, f"the testing shim's pulse raised: {run['error']}"
    holds = [c for c in run["socket_calls"] if c.get("op") == "hold"
             and run["device_id"] in (c.get("devices") or [])]
    assert not holds, f"the client asked the bus process to hold a testing name: {holds}"


def it_touches_no_live_devices_mail():
    run = _pulsed_testing_shim()
    foreign = [c for c in run["mail"] if c[1] != run["device_id"]]
    assert not foreign, f"the testing shim touched mail not its own: {foreign[:4]}"


def the_refusal_is_narrow():
    from cairn.tools.bus_client.remote import RemoteBus
    sent: list = []
    rb = RemoteBus.__new__(RemoteBus)
    rb._call = lambda request: sent.append(dict(request)) or {}
    rb.wire_delivery("live-shaped-39dbe8e8316b")
    rb.wire_delivery(f"{MARK}declined")
    assert sent == [{"op": "hold", "devices": ["live-shaped-39dbe8e8316b"]}], sent


TEETH = [a_testing_shim_on_the_live_bus_is_never_held_there, it_touches_no_live_devices_mail,
         the_refusal_is_narrow]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
