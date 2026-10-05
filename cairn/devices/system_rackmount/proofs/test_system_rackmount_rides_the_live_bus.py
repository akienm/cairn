"""Proof for ticket 20a97889646e — system_rackmount's proof rides the live bus, marked as testing.

RULE 1 (Akien, 2026-10-01): a device's public interface is the bus, and nothing outside a
device reaches into its code. On 2026-10-05 encapsulation_breaches measured exactly one row
from system_rackmount: test_system_rackmount.py:54 imported BusDevice from the cairn device to
stand up a private scratch bus. Test against live, marked as testing (ruled 2026-09-28,
extended 2026-10-04): the live system is the test surface, and every test output carries a
mark so it can be thrown away.

This proof measures only system_rackmount (RULE 1: a ticket's proofs measure its own component).

  1. SYSTEM_RACKMOUNT REACHES INTO NO DEVICE. No encapsulation_breaches row has a file under
     cairn/devices/system_rackmount/.
  2. ITS BUS TRAFFIC IS LIVE AND MARKED. With cairn.tools.bus_client.bus_client.reach wrapped to
     record every call on the bus it hands out, the end-to-end tooth of test_system_rackmount.py
     posts at least one envelope through it (the live bus, not a private one); every envelope
     posted names a sender AND an addressee starting "testing-20a97889646e-", and every read
     names such an addressee — so none of it touches a live device's mail or identity.

    python3 cairn/devices/system_rackmount/proofs/test_system_rackmount_rides_the_live_bus.py
"""
import importlib
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 900  # the sieve walks the whole import graph to find the component's edges

PROVES = {"20a97889646e": {"1": "system_rackmount_reaches_into_no_device",
                           "2": "its_bus_traffic_is_live_and_marked"}}

MARK = "testing-20a97889646e-"
PASS = 0
FAIL = 0


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


def system_rackmount_reaches_into_no_device():
    breaches = importlib.import_module("cairn.machines.build_inspector.inspector").encapsulation_breaches
    rows = [b for b in breaches(str(_REPO_ROOT))
            if str(b["file"]).startswith("cairn/devices/system_rackmount/")]
    assert not rows, f"{len(rows)} reach(es) from system_rackmount: " + \
        "; ".join(f"{b['file']}:{b['line']} -> {b['module']}" for b in rows[:8])


class _Recording:
    """The bus reach() handed out, with every post and read written down on the way through."""

    def __init__(self, bus, log):
        self._bus, self._log = bus, log

    def post(self, **kw):
        self._log.append(("post", kw.get("to"), kw.get("sender")))
        return self._bus.post(**kw)

    def read(self, **kw):
        self._log.append(("read", kw.get("to"), None))
        return self._bus.read(**kw)

    def __getattr__(self, name):
        return getattr(self._bus, name)


def its_bus_traffic_is_live_and_marked():
    bc = importlib.import_module("cairn.tools.bus_client.bus_client")
    log: list = []
    real = bc.reach
    bc.reach = lambda *devices: _Recording(real(*devices), log)
    try:
        mod = importlib.import_module("cairn.devices.system_rackmount.proofs.test_system_rackmount")
        try:
            mod.test_alert_me_at_80_cpu_end_to_end_through_the_heartbeat()
        finally:
            mod._SCRATCH.close()
    finally:
        bc.reach = real
    posts = [e for e in log if e[0] == "post"]
    assert posts, ("the end-to-end tooth posted nothing through bus_client.reach() — it is not "
                   "riding the live bus")
    unmarked = [e for e in log if not str(e[1] or "").startswith(MARK)
                or (e[0] == "post" and not str(e[2] or "").startswith(MARK))]
    assert not unmarked, f"{len(unmarked)} unmarked bus call(s): {unmarked[:4]}"


TEETH = [system_rackmount_reaches_into_no_device, its_bus_traffic_is_live_and_marked]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
