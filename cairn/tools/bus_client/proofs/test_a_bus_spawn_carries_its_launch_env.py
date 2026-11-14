"""Proof for ticket 0c2c3f53c2be, D2's env carry: a bus process started for a launch carries
the launch environment the caller named.

MEASURED 2026-11-13 at origin/main 44e86aa7c: bus_client.remote._spawn started a bus process at
any home but passed it no environment of the caller's — Popen inherited this process's, and
systemd-run handed the unit the MANAGER's environment plus HOME, PATH and CAIRN_TESTER_TEST_ID.
A scratch CodeMother whose roots are named by her environment (inspect_wire.launch) could not
be started that way. No process is spawned here: the spawners are watched, not run.

  1. The Windows and setsid spawns hand Popen the launch environment as ``env``.
  2. The systemd spawn carries every key of the launch environment as a ``--setenv``, HOME
     and PATH from it rather than from this process.
  3. A RemoteBus given ``env`` hands it to the ensure_bus its lazy start calls.

    python3 cairn/tools/bus_client/proofs/test_a_bus_spawn_carries_its_launch_env.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"0c2c3f53c2be": {
    "5b": "test_the_popen_spawns_hand_the_launch_env",
    "5c": "test_the_unit_spawn_sets_every_launch_key",
    "5d": "test_a_remote_bus_hands_its_env_to_the_lazy_start",
}}

_ENV = {"HOME": "/scratch/home", "PATH": "/scratch/bin", "CAIRN_BUS_HOME": "/scratch/home/bus",
        "CAIRN_BUILD_INSPECTOR_CHART_BERTHS": "/scratch/berths"}


class _Popen:
    seen: list = []

    def __init__(self, cmd, **kwargs):
        _Popen.seen.append(kwargs)


def _scratch():
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir("bus-spawn-env-0c2c-")


def test_the_popen_spawns_hand_the_launch_env():
    from cairn.tools.bus_client import remote
    was = remote.subprocess.Popen
    remote.subprocess.Popen = _Popen
    _Popen.seen = []
    try:
        d = _scratch()
        remote._detached(d, True, d / "bus.log", _ENV)
        remote._setsid(d, True, d / "bus.log", "proof", _ENV)
        remote._detached(d, True, d / "bus.log")
    finally:
        remote.subprocess.Popen = was
    assert [k.get("env") for k in _Popen.seen] == [_ENV, _ENV, None], _Popen.seen


def test_the_unit_spawn_sets_every_launch_key():
    from cairn.tools.bus_client import remote

    class _Posix:
        name = "posix"

        def __getattr__(self, k):
            return getattr(os, k)

    argvs = []

    class _Done:
        returncode, stdout, stderr = 0, "", ""

    def _run(argv, **kwargs):
        argvs.append(argv)
        return _Done()

    was_os, was_run = remote.os, remote.subprocess.run
    remote.os, remote.subprocess.run = _Posix(), _run
    try:
        d = _scratch()
        assert remote._spawn(d, True, env=_ENV) == "unit"
    finally:
        remote.os, remote.subprocess.run = was_os, was_run
    argv = argvs[0]
    sets = [a for a in argv[:argv.index("--")] if a.startswith("--setenv=")]
    for k, v in _ENV.items():
        assert f"--setenv={k}={v}" in sets, (k, sets)
    assert len([a for a in sets if a.startswith("--setenv=HOME=")]) == 1, sets


def test_a_remote_bus_hands_its_env_to_the_lazy_start():
    from cairn.tools.bus_client import remote
    calls, started = [], []

    def _exchange(request, home, **kwargs):
        calls.append(request)
        if not started:
            raise FileNotFoundError(home)
        return {"ok": True, "json": {}}

    def _ensure(home, *, scratch=False, env=None):
        started.append(env)
        return {}

    was = remote.exchange, remote.ensure_bus
    remote.exchange, remote.ensure_bus = _exchange, _ensure
    try:
        remote.RemoteBus(_scratch(), scratch=True, env=_ENV).stats()
    finally:
        remote.exchange, remote.ensure_bus = was
    assert started == [_ENV], started


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
