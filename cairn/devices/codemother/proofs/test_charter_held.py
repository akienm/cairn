"""PROOF — the charter tool's instance is held under codemother (ticket 65b34c57ab71).

The falsifier is numbered (PROVES keys follow the falsifier markers):
(1) a charter tool instance exists under codemother at ``devices/codemother/0/tools/charter``
    in BOTH roots — class-space carries its charter naming ``cairn/tools/charter`` as the
    tool class; instance-space is ensured (the data_recorder backpack's ``inbound/`` folder)
    by ``ensure_charter_instance``, the call ``activate`` and the ``charter`` verb make;
(2) RETIRED by ticket 7778e24dd82e with the bus's held-tool delivery (outline 19.16: only
    devices are on the bus), as 164da559823d D6 retired a clause before it — the tooth that
    asserted a post to ``charter`` lands in the held inbound is deleted, and the held instance
    itself stays;
(3) the data_recorder instance on charter receives a feedback record through codemother's
    ``charter`` verb over the bus and hands it back on read;
(4) the placement leaves charter a TOOL: ``cairn/tools/charter`` carries no shim and no device
    (its 2026-09-02 bus presence, which recorded at charter's OWN instance address, is
    retired), the held instance carries no declaration file and nothing but its backpack, and
    it gates nothing — the holder's shim is the only glue.

THE INSTANCE ROOT IS A SCRATCH DIRECTORY for the whole run: ``address.ROOTS["instance"]`` is
pointed at it before any tooth and restored after, so nothing here touches the live
``~/.cairn`` — the held instance, the backpack and the ground loop's liveness all land in the
fixture world. The bus is in-process (a nonce table, dropped at exit) with codemother
registered and NO device called charter, which is exactly the live roster since the shim
was retired.

A hollow build could not pass: tooth 1 is the ensure itself — reverted, no inbound folder
stands; tooth 3 is the verb — reverted, codemother bounces it.
"""
from __future__ import annotations

import contextlib
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base import address as _address  # noqa: E402

# The subjects are bound at call time, never at import: a hollow reading that takes one away
# must red the teeth by name, not crash the file before the first tooth prints.
scratch_bus = bus_shim = DeviceRoster = _codemother = CodeMotherShim = None


def _bind() -> None:
    global scratch_bus, bus_shim, DeviceRoster, _codemother, CodeMotherShim
    from cairn.devices.cairn.tools.scratch_bus.scratch_bus import scratch_bus, bus_shim
    from cairn.tools.bus_client.roster import DeviceRoster
    from cairn.devices.codemother import shim as _codemother
    from cairn.devices.codemother.shim import CodeMotherShim

PROVES = {"65b34c57ab71": {
    "1": "test_the_instance_exists_under_codemother_in_both_roots",
    "3": "test_the_backpack_receives_and_reads_back_feedback",
    "4": "test_charter_stays_a_tool",
}}

NOW = datetime(2026, 9, 18, 12, 0, 0)
_RUN = uuid.uuid4().hex[:8]     # names this run in message text; never a table name
_SCRATCH = contextlib.ExitStack()   # every bus this run minted rides store.scratch(): dropped at close, swept by pid if not
_LIVE_INSTANCE = _address.ROOTS["instance"]
_CLASS_CHARTER = _REPO_ROOT / "cairn/devices/codemother/0/tools/charter/intention+why.json"


# --- the fixture world ---------------------------------------------------------------------

def _scratch_roots() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    d = scratch_dir("cairn_charter_held_")
    _address.ROOTS["instance"] = d
    return d


def _restore_roots() -> None:
    _address.ROOTS["instance"] = _LIVE_INSTANCE


def _fresh_bus():
    bus = _SCRATCH.enter_context(scratch_bus("charter_held"))
    loop = DeviceRoster(bus)
    loop.hold(bus_shim(bus, loop))
    loop.hold(CodeMotherShim(bus=bus))
    loop.pulse(NOW)
    assert "charter" not in bus.list().get("devices", {}), "a device named charter is on the bus"
    return bus


def _inbound(held: Path) -> list[dict]:
    p = held / "inbound" / "records.jsonl"
    if not p.is_file():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


# --- teeth -----------------------------------------------------------------------------------

def test_the_instance_exists_under_codemother_in_both_roots():
    assert _CLASS_CHARTER.is_file(), f"no class-space charter at {_CLASS_CHARTER}"
    doc = json.loads(_CLASS_CHARTER.read_text(encoding="utf-8"))
    assert doc.get("tool_class") == "cairn/tools/charter", doc.get("tool_class")
    assert doc.get("holder") == "codemother", doc.get("holder")
    held = _codemother.charter_instance()
    assert str(held).startswith(str(_address.ROOTS["instance"])), held
    assert held == _address.ROOTS["instance"] / "devices/codemother/0/tools/charter", held
    assert not (held / "inbound").exists(), "the fixture world already holds it"
    out = _codemother.ensure_charter_instance()
    assert (held / "inbound").is_dir(), out
    assert out["backpack"] == str(held / "inbound"), out
    assert out["address"] == str(held) and out["records"] == 0, out
    # ensured twice is ensured once
    again = _codemother.ensure_charter_instance()
    assert again["backpack"] == out["backpack"], again
    print("ok test_the_instance_exists_under_codemother_in_both_roots")


def test_the_backpack_receives_and_reads_back_feedback():
    held = _codemother.charter_instance()
    bus = _fresh_bus()
    finding = f"charter finding {_RUN}: a class string was improvised"
    reply = bus.request(sender="cc", to="codemother", channel="personal", verb="charter",
                        why="proof: feedback for the held charter instance",
                        body={"record": {"finding": finding}, "read": 1})
    assert reply["sender"] == "codemother" and reply["addressee"] == "cc", reply
    body = reply["body"]
    assert body.get("written"), body
    assert body["address"] == str(held), body
    assert body["read"][-1]["finding"] == finding and body["read"][-1]["id"] == body["written"], body
    assert body["read"][-1]["inspector_target"] == "codemother/0/tools/charter", body["read"][-1]
    assert body["records"] == len(_inbound(held)) >= 1, (body["records"], len(_inbound(held)))
    # the verb is declared beside the others, and reachable cold through the contract
    assert "charter" in CodeMotherShim(bus=bus).declared_contract()["verbs"]
    print("ok test_the_backpack_receives_and_reads_back_feedback")


def test_charter_stays_a_tool():
    tool = _REPO_ROOT / "cairn/tools/charter"
    assert tool.is_dir()
    for gone in ("shim.py", "device.py"):
        assert not (tool / gone).exists(), f"{gone} gives the tool a presence of its own — a machine"
    assert not (_address.ROOTS["instance"] / "devices/charter").exists(), \
        "charter kept state at its own instance address — Law 6's machine test"
    held = _codemother.charter_instance()
    assert sorted(p.name for p in held.iterdir()) == ["inbound"], \
        f"the held instance carries more than its backpack: {sorted(p.name for p in held.iterdir())}"
    # the class-space instance carries a charter and nothing that runs
    inst = _CLASS_CHARTER.parent
    assert sorted(p.name for p in inst.iterdir()) == ["intention+why.json"], sorted(p.name for p in inst.iterdir())
    print("ok test_charter_stays_a_tool")


# --- the run ---------------------------------------------------------------------------------


def _run_all() -> int:
    teeth = [globals()[PROVES["65b34c57ab71"][k]] for k in sorted(PROVES["65b34c57ab71"])]
    _scratch_roots()
    rc = 0
    try:
        for t in teeth:
            try:
                _bind()
                t()
                print(f"  PASS  {t.__name__}")
            except Exception as exc:  # noqa: BLE001
                rc = 1
                print(f"  FAIL  {t.__name__}: {type(exc).__name__}: {exc}")
    finally:
        _restore_roots()
        _SCRATCH.close()
    print("green — the charter tool's instance is held under codemother" if rc == 0 else "RED")
    return rc


if __name__ == "__main__":
    sys.exit(_run_all())
