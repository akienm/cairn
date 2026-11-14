"""Proof for ticket b38af5fd1852 (ground_loop only) — a second ground loop exits quietly; --force replaces it.

Akien 2026-11-13, Q#93 (outline 5.3.5.2.1-2): "spinning up a second ground loop should see the first ... and
exit quietly. if we're starting a new one on purpose ... we'll add --force, which means kill the old one."
Every tooth runs against an injected scratch home; nothing touches ~/.cairn.

    python <this file>
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.devices.cairn.machines.ground_loop import guard, heartbeat  # noqa: E402
from cairn.tools.base.address import instance_path  # noqa: E402

PROVES = {
    "b38af5fd1852": {
        "1": "a_second_loop_exits_zero_silently_and_force_kills_the_old_one",
        "2": "the_ground_loop_lock_path_carries_the_cairn_instance",
    },
}

_HOLDER = ("import sys, time\n"
           "from pathlib import Path\n"
           "from cairn.devices.cairn.machines.ground_loop.guard import claim_singleton\n"
           "c = claim_singleton(Path(sys.argv[1]))\n"
           "print('WON', flush=True)\n"
           "time.sleep(60)\n")
_DOOR = ("import sys\n"
         "from pathlib import Path\n"
         "from cairn.devices.cairn.machines.ground_loop.__main__ import main\n"
         "sys.exit(main(Path(sys.argv[1]), class_root=Path(sys.argv[2]), watch=Path(sys.argv[2]), "
         "force='--force' in sys.argv[3:], cadence=0.05))\n")


def _env():
    return dict(os.environ, PYTHONPATH=str(REPO))


def _holder(home: Path) -> subprocess.Popen:
    p = subprocess.Popen([sys.executable, "-c", _HOLDER, str(home)], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, env=_env())
    assert p.stdout.readline().strip() == "WON", "the scratch holder never took its claim"
    heartbeat.write_record(datetime.now(timezone.utc).astimezone(), {"beats": 1}, p.pid, home)
    return p


def a_second_loop_exits_zero_silently_and_force_kills_the_old_one() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        home = Path(td) / "0"
        empty = Path(td) / "empty_class_root"
        empty.mkdir()
        holder = _holder(home)
        try:
            quiet = subprocess.run([sys.executable, "-c", _DOOR, str(home), str(empty)], capture_output=True, text=True,
                                   timeout=20, env=_env())
            assert quiet.returncode == 0, f"a second loop exits 0, got {quiet.returncode}: {quiet.stderr[-300:]!r}"
            assert quiet.stderr.strip() == "" and quiet.stdout.strip() == "", \
                f"a second loop is silent: {quiet.stderr!r} {quiet.stdout!r}"
            time.sleep(0.3)
            assert holder.poll() is None, "the quiet second loop signalled the first"
            # --force: kill the old one and take the claim. The new loop must run (not exit), so stop it ourselves.
            forced = subprocess.Popen([sys.executable, "-c", _DOOR, str(home), str(empty), "--force"], stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True, env=_env())
            try:
                holder.wait(timeout=15)
                assert holder.poll() is not None, "--force did not kill the old loop"
                time.sleep(0.5)
                assert forced.poll() is None, f"the forced loop is not running: rc={forced.returncode}"
                assert guard.held(home), "the forced loop does not hold the claim"
            finally:
                forced.kill()
                forced.wait(timeout=5)
        finally:
            holder.kill()
            holder.wait(timeout=5)


def the_ground_loop_lock_path_carries_the_cairn_instance() -> None:
    home = instance_path("cairn", 0) / "machines" / "ground_loop"
    lock = home / guard.LOCK_NAME
    parts = lock.parts
    assert "devices" in parts and "cairn" in parts[parts.index("devices") + 1:] , f"no device segment in {lock}"
    i = parts.index("devices")
    assert parts[i + 1] == "cairn" and parts[i + 2] == "0", f"the lock path lacks devices/cairn/0: {lock}"


TEETH = [a_second_loop_exits_zero_silently_and_force_kills_the_old_one,
         the_ground_loop_lock_path_carries_the_cairn_instance]


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
