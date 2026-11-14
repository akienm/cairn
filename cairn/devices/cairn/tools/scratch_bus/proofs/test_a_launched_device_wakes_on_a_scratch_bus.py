"""Proof for ticket 0c2c3f53c2be, clause 5: scratch_bus.launch(device, env) starts a bus
PROCESS under a scratch HOME whose environment carries env, holds device there by name, and
shuts it down at the block's end.

MEASURED 2026-11-13 at origin/main 44e86aa7c: the bus process wakes an addressee by name through
DeviceRoster.shim_for (RemoteBus.hold), but the only fixture bus the cairn device published,
scratch_bus.scratch_bus, ran IN the asking process, so a proof that held a device on it imported
that device's shim. This tooth rides a bus process, so it needs Postgres on 5432; and it reads
the process's environment from /proc, so the Linux sealer's run is the seal (outline 9.4.8.1).

    python3 cairn/devices/cairn/tools/scratch_bus/proofs/test_a_launched_device_wakes_on_a_scratch_bus.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"0c2c3f53c2be": {"5": "test_a_launched_device_is_held_by_a_bus_process_with_its_env"}}

_MARK = "CAIRN_SCRATCH_BUS_LAUNCH_PROOF"


def test_a_launched_device_is_held_by_a_bus_process_with_its_env():
    from cairn.devices.cairn.tools.scratch_bus.scratch_bus import launch
    from cairn.tools.bus_client.remote import exchange
    from cairn.tools.scratch.scratch import account_home
    with launch("codemother", {_MARK: "0c2c"}) as bus:
        home = Path(bus._home)
        st = bus.stats()
        assert st["held"] == ["codemother"], st
        assert int(st["pid"]) != os.getpid(), ("the device was held in the asking process", st)
        live = (account_home() / ".cairn").resolve()
        assert live not in home.resolve().parents, \
            ("the launched bus's home is in the account's own instance-space", home)
        environ = Path(f"/proc/{st['pid']}/environ")
        assert environ.exists(), ("no /proc on this box: the bus process's environment is read "
                                  "by the Linux sealer's run")
        pairs = environ.read_bytes().split(b"\0")
        assert f"{_MARK}=0c2c".encode() in pairs, "the launch env did not reach the bus process"
        assert f"CAIRN_BUS_HOME={home}".encode() in pairs, "the bus does not carry its own address"
    try:
        exchange({"op": "stats"}, home, timeout=5)
    except OSError:
        pass
    else:
        raise AssertionError(f"the launched bus at {home} still answers after its block")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
