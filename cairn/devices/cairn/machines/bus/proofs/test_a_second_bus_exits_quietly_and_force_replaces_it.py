"""Proof for ticket ac71d984ebda — a second bus exits quietly; --force replaces it.

Akien 2026-11-13, Q#93 (outline 5.3.5.2.1-2): "spinning up a second ground loop should see the first, and that
it's fine, and exit quietly ... we'll add --force, which means kill the old one." The bus is CC's read of that
answer (the outline says so), not yet his word. Every tooth runs against a SCRATCH home directory: no bus is
started, the live bus is never reached, and nothing touches ~/.cairn.

    python <this file>
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "ac71d984ebda": {
        "1": "a_second_bus_exits_zero_silently_and_force_takes_the_claim_from_the_first",
        "2": "the_bus_lock_path_carries_the_cairn_instance",
    },
}

_HOLDER = ("import sys, time\n"
           "from pathlib import Path\n"
           "from cairn.devices.cairn.machines.bus.server import claim\n"
           "h = claim(Path(sys.argv[1]))\n"
           "print('WON' if h else 'LOST', flush=True)\n"
           "time.sleep(60)\n")
_SECOND = ("import sys\n"
           "from pathlib import Path\n"
           "from cairn.devices.cairn.machines.bus.server import serve\n"
           "sys.exit(serve(Path(sys.argv[1]), None))\n")


def _env() -> dict:
    return dict(os.environ, PYTHONPATH=str(REPO))


def a_second_bus_exits_zero_silently_and_force_takes_the_claim_from_the_first() -> None:
    from cairn.devices.cairn.machines.bus import server
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        home = Path(td) / "0"
        held = server.claim(home)
        assert held is not None, "the scratch claim was not taken"
        try:
            second = subprocess.run([sys.executable, "-c", _SECOND, str(home)], capture_output=True, text=True,
                                    timeout=60, env=_env())
            assert second.returncode == 0, f"a second bus exits 0, got {second.returncode}: {second.stderr[-300:]!r}"
            assert second.stdout.strip() == "" and second.stderr.strip() == "", \
                f"a second bus is silent: stdout={second.stdout!r} stderr={second.stderr!r}"
        finally:
            held.close()
    # --force: kill the holder named in bus.pid and take the claim
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        home = Path(td) / "0"
        holder = subprocess.Popen([sys.executable, "-c", _HOLDER, str(home)], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, env=_env())
        try:
            assert holder.stdout.readline().strip() == "WON", "the scratch holder never took its claim"
            forced = server.force_claim(home, wait_s=15)
            assert forced is not None, "--force did not take the claim"
            try:
                holder.wait(timeout=15)
                assert holder.poll() is not None, "--force did not kill the old bus"
                assert server.claim(home) is None, "the forcing process does not hold the claim"
            finally:
                forced.close()
        finally:
            holder.kill()
            holder.wait(timeout=5)


def the_bus_lock_path_carries_the_cairn_instance() -> None:
    from unittest import mock
    from cairn.devices.cairn.machines.bus import server
    with mock.patch.dict(os.environ):
        os.environ.pop("CAIRN_BUS_HOME", None)
        home = server.bus_home(None)
    parts = (home / "bus.lock").parts
    assert parts[-6:-1] == ("devices", "cairn", "machines", "bus", "0"), \
        f"the bus.lock path lacks devices/cairn/machines/bus/<instance>: {home / 'bus.lock'}"


TEETH = [a_second_bus_exits_zero_silently_and_force_takes_the_claim_from_the_first,
         the_bus_lock_path_carries_the_cairn_instance]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
