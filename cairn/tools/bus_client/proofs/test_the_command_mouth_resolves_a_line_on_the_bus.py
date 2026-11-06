"""Proof for ticket 95c919b5f4aa — bus_client carries a command mouth a shell can call.

`python3 -m cairn.tools.bus_client <device> <words...>` resolves the words on the instance's
one bus process against that device's shim, prints the text to stdout on exit 0 and stderr
otherwise, and exits with the line's code. Akien 2026-11-05 (Q#27, outline 8.4.2): "if there's
a script for it, run it, else get on the bus" — this is the "else". Teeth, one per clause:

  1. a fixture shim answering 'ping' with 'pong' exit 0: the mouth prints 'pong' to stdout and
     exits 0;
  2. a line the fixture refuses with exit 4 prints to stderr and exits 4;
  3. a device name with no shim exits 2 and names the device (and starts no bus);
  4. an unreachable bus exits 1 with the cause on stderr.

The fixture shim is this module's own MouthFixtureShim, addressed as `module:Class` — the form
the bus already holds a shim by (RemoteBus.verbs). Every bus here is a scratch one under a
scratch CAIRN_BUS_HOME and its own unit name; the live bus and store are never touched.

    python3 cairn/tools/bus_client/proofs/test_the_command_mouth_resolves_a_line_on_the_bus.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "95c919b5f4aa": {
        "1": "clause_1_a_line_answered_prints_to_stdout",
        "2": "clause_2_a_refused_line_prints_to_stderr_with_its_code",
        "3": "clause_3_a_device_with_no_shim_is_refused_by_name",
        "4": "clause_4_an_unreachable_bus_exits_1_with_the_cause",
    },
}

FIXTURE_ID = "bus_mouth_fixture_95c9"
FIXTURE = f"cairn.tools.bus_client.proofs.{Path(__file__).stem}:MouthFixtureShim"
UNIT = f"cairn-bus-mouth-proof-{os.getpid()}"
FAILURES: list[str] = []


# --- the fixture shim the scratch bus hosts ------------------------------------------------

def _fixture_classes():
    from cairn.tools.base.device import BaseDevice
    from cairn.tools.base.shim import BaseShim, ONLINE

    class _Dev(BaseDevice):
        def intention(self) -> dict:
            return {"what": "the command mouth proof's fixture (ticket 95c919b5f4aa)"}

        def state(self) -> dict:
            return {}

        def settings(self) -> dict:
            return {}

    class _Shim(BaseShim):
        @property
        def device_id(self) -> str:
            return FIXTURE_ID

        def _start_device(self):
            self._presence = ONLINE
            return _Dev()

        def resolve(self, argv):
            words = list(argv)
            if words == ["ping"]:
                return {"exit": 0, "text": "pong", "data": None}
            if words[:1] == ["refuse"]:
                return {"exit": 4, "text": "refused-by-the-fixture", "data": None}
            return super().resolve(words)

    return _Shim


def __getattr__(name):  # the bus imports MouthFixtureShim by name; built lazily, at its ask
    if name == "MouthFixtureShim":
        return _fixture_classes()
    raise AttributeError(name)


# --- the teeth ------------------------------------------------------------------------------

def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:1200]}", flush=True)
        FAILURES.append(name)


def _env(bus_home: str) -> dict:
    env = dict(os.environ)
    env.update(CAIRN_BUS_HOME=bus_home, CAIRN_BUS_UNIT=UNIT, PYTHONDONTWRITEBYTECODE="1",
               PYTHONPATH=str(REPO) + os.pathsep + env.get("PYTHONPATH", ""))
    return env


def _mouth(bus_home: str, *words: str, timeout: float = 120) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "cairn.tools.bus_client", *words],
                          env=_env(bus_home), cwd=str(REPO), capture_output=True, text=True,
                          timeout=timeout)


def _start(home: Path) -> str:
    r = subprocess.run([sys.executable, "-c",
                        "from cairn.tools.bus_client.remote import ensure_bus\n"
                        "ensure_bus(scratch=True)\nprint('up')\n"],
                       env=_env(str(home)), cwd=str(REPO), capture_output=True, text=True, timeout=120)
    return (r.stdout + r.stderr).strip()


def _teardown(home: Path) -> None:
    subprocess.run([sys.executable, "-c",
                    "from cairn.tools.bus_client.remote import RemoteBus\n"
                    "try:\n    RemoteBus().shutdown()\nexcept Exception:\n    pass\n"],
                   env=_env(str(home)), cwd=str(REPO), capture_output=True, timeout=60)
    subprocess.run(["systemctl", "--user", "stop", f"{UNIT}.service"], capture_output=True)
    subprocess.run(["systemctl", "--user", "reset-failed", f"{UNIT}.service"], capture_output=True)


def clause_1_a_line_answered_prints_to_stdout(home: Path) -> None:
    r = _mouth(str(home), FIXTURE, "ping")
    _check("clause_1_a_line_answered_prints_to_stdout",
           r.returncode == 0 and r.stdout.strip() == "pong" and "pong" not in r.stderr,
           f"rc={r.returncode} stdout={r.stdout[-400:]!r} stderr={r.stderr[-600:]!r}")


def clause_2_a_refused_line_prints_to_stderr_with_its_code(home: Path) -> None:
    r = _mouth(str(home), FIXTURE, "refuse", "this")
    _check("clause_2_a_refused_line_prints_to_stderr_with_its_code",
           r.returncode == 4 and "refused-by-the-fixture" in r.stderr
           and "refused-by-the-fixture" not in r.stdout,
           f"rc={r.returncode} stdout={r.stdout[-400:]!r} stderr={r.stderr[-600:]!r}")


def clause_3_a_device_with_no_shim_is_refused_by_name(empty: Path) -> None:
    name = "no_such_device_95c9"
    r = _mouth(str(empty), name, "list")
    lacks = []
    if r.returncode != 2:
        lacks.append(f"rc={r.returncode}, want 2")
    if name not in r.stderr:
        lacks.append("stderr does not name the device")
    if (empty / "bus.sock").exists():
        lacks.append("a bus was started for a device no shim answers to")
    _check("clause_3_a_device_with_no_shim_is_refused_by_name", not lacks,
           "; ".join(lacks) + f" stdout={r.stdout[-300:]!r} stderr={r.stderr[-500:]!r}")


def clause_4_an_unreachable_bus_exits_1_with_the_cause() -> None:
    # tcpmux's port: a privileged port no bus is ever given. No socket is opened here — the
    # sole-path sieve holds the network doors to remote.py and tls.py (build_inspector).
    far = "127.0.0.1:1"
    r = _mouth(far, FIXTURE, "ping", timeout=180)
    _check("clause_4_an_unreachable_bus_exits_1_with_the_cause",
           r.returncode == 1 and far in r.stderr and not r.stdout.strip()
           and "Traceback" not in r.stderr,
           f"rc={r.returncode} stdout={r.stdout[-300:]!r} stderr={r.stderr[-700:]!r}")


def main() -> int:
    print("95c919b5f4aa — bus_client carries a command mouth a shell can call")
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("95c9-bus-home-")
    empty = scratch_dir("95c9-bus-empty-")
    try:
        up = _start(home)
        if up != "up":
            print(f"  (scratch bus did not start: {up[-500:]})")
        for tooth in (lambda: clause_1_a_line_answered_prints_to_stdout(home),
                      lambda: clause_2_a_refused_line_prints_to_stderr_with_its_code(home),
                      lambda: clause_3_a_device_with_no_shim_is_refused_by_name(empty),
                      clause_4_an_unreachable_bus_exits_1_with_the_cause):
            try:
                tooth()
            except Exception as exc:  # noqa: BLE001 — each tooth reports even when one raises
                _check(getattr(tooth, "__name__", "tooth"), False, f"raised {type(exc).__name__}: {exc}")
    finally:
        _teardown(home)
        shutil.rmtree(home, ignore_errors=True)
        shutil.rmtree(empty, ignore_errors=True)
        shutil.rmtree(Path.home() / ".cairn" / "devices" / FIXTURE_ID, ignore_errors=True)
    print(f"{'GREEN' if not FAILURES else 'RED'}: {len(FAILURES)} failing: {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
