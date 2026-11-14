"""Proof for "a bus spawn at the live home from a foreign checkout is refused, and the live home
never follows HOME".

MEASURED 2026-11-14 (akiendell, repro_c.py): with HOME and USERPROFILE set to a fresh folder,
``remote._live_home()`` returned that folder's bus home, so ``ensure_bus`` read home == live,
set scratch False and spawned a detached, NON-scratch bus rooted at a worktree. Two holes:
``_refuse_a_foreign_replace`` (3deafc9e36de) guarded only REPLACING a stale live bus, never
STARTING one when none answers; and ``_live_home``'s Windows branch was ``expanduser('~')``,
which follows HOME.

  1. test_a_foreign_root_at_the_live_home_never_spawns: no bus answers at the live home, the
     caller's class root is not the house root: BusStale names both roots, ``_spawn`` never runs;
  2. test_the_house_root_still_spawns_the_live_bus: the house root's client still starts it;
  3. test_the_windows_live_home_ignores_home_and_userprofile: with ``os.name`` faked to ``nt``,
     ``pwd`` unimportable and HOME/USERPROFILE at a scratch folder, ``_live_home()`` names the
     profile folder the shell reports for FOLDERID_Profile, and a scratch HOME's bus home is not
     the live one.

Host-independent: the wire, ``_spawn``, systemd and the Win32 DLLs are replaced, so nothing
dials, nothing spawns, and clause 3 runs on Linux the way 715d's tooth fakes kernel32. A real
SHGetKnownFolderPath call on Windows is the one thing this proof does not measure.

    bin/cairn test cairn/tools/bus_client/proofs/test_a_foreign_checkout_never_spawns_the_live_bus.py
"""
from __future__ import annotations

import os
import sys
import types
import uuid
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"5a91bdac03b7": {
    "1": "test_a_foreign_root_at_the_live_home_never_spawns",
    "2": "test_the_house_root_still_spawns_the_live_bus",
    "3": "test_the_windows_live_home_ignores_home_and_userprofile",
}}

_FOREIGN_HOUSE = "/nonexistent/testing-fspawn-house-root"
_ENV = "CAIRN_BUS_CLIENT_HOUSE_ROOT"
_PROFILE_ID = "5E6C858F-0E22-4760-9AFE-EA3317B67173"   # FOLDERID_Profile


class _Spawned(Exception):
    """Raised by the stand-in ``_spawn``, so a spawn is recorded and nothing waits on it."""


def _no_bus(monkeypatch, *, house: str):
    """No bus answers anywhere; ``_spawn`` records and stops; systemd is never asked."""
    from cairn.tools.bus_client import remote
    spawns: list[tuple] = []

    def exchange(req, h=None, timeout=None):
        raise ConnectionRefusedError("testing-fspawn: no bus answers")

    def spawn(home, scratch, **k):
        spawns.append((Path(home), scratch))
        raise _Spawned(str(home))

    monkeypatch.setattr(remote, "exchange", exchange)
    monkeypatch.setattr(remote, "_spawn", spawn)
    monkeypatch.setattr(remote, "_beside_the_manager", lambda: True)
    monkeypatch.setenv(_ENV, house)
    return remote, spawns


def test_a_foreign_root_at_the_live_home_never_spawns(monkeypatch):
    remote, spawns = _no_bus(monkeypatch, house=_FOREIGN_HOUSE)
    try:
        remote.ensure_bus(remote._live_home())
    except remote.BusStale as exc:
        said = str(exc)
    except _Spawned:
        raise AssertionError(f"a foreign root spawned the live home's bus: {spawns!r}")
    else:
        raise AssertionError("ensure_bus returned with no bus answering and no refusal")
    assert spawns == [], f"a foreign root reached _spawn: {spawns!r}"
    assert _FOREIGN_HOUSE in said, f"the refusal does not name the house root: {said}"
    assert str(Path(remote._CLASS_ROOT).resolve()) in said, \
        f"the refusal does not name the caller's root: {said}"
    assert "CAIRN_BUS_HOME=" in said, f"the refusal does not say the way out: {said}"


def test_the_house_root_still_spawns_the_live_bus(monkeypatch):
    from cairn.tools.bus_client import remote as r
    remote, spawns = _no_bus(monkeypatch, house=str(Path(r._CLASS_ROOT).resolve()))
    live = remote._live_home()
    try:
        remote.ensure_bus(live)
    except _Spawned:
        pass
    assert spawns == [(live, False)], f"the house root did not start the live bus: {spawns!r}"


def test_the_windows_live_home_ignores_home_and_userprofile(monkeypatch):
    import ctypes
    from cairn.tools.bus_client import remote
    from cairn.tools.scratch.scratch import scratch_dir
    scratch = Path(scratch_dir("testing-fspawn-home-"))
    profile = Path(scratch_dir("testing-fspawn-profile-"))
    asked: list[bytes] = []
    freed: list[object] = []

    def known_folder(guid_ref, flags, token, out_ref):
        asked.append(bytes(guid_ref._obj))
        out_ref._obj.value = str(profile)
        return 0

    dlls = types.SimpleNamespace(
        shell32=types.SimpleNamespace(SHGetKnownFolderPath=known_folder),
        ole32=types.SimpleNamespace(CoTaskMemFree=freed.append))
    fake_os = types.SimpleNamespace(**{k: getattr(os, k) for k in dir(os) if not k.startswith("__")})
    fake_os.name = "nt"
    monkeypatch.setattr(remote, "os", fake_os)
    monkeypatch.setitem(sys.modules, "pwd", None)
    monkeypatch.setattr(remote, "_windll", lambda: dlls)
    monkeypatch.setenv("HOME", str(scratch))
    monkeypatch.setenv("USERPROFILE", str(scratch))
    monkeypatch.delenv("CAIRN_BUS_HOME", raising=False)
    live = remote._live_home()
    want = profile / ".cairn/devices/cairn/machines/bus/0"
    assert live == want, f"the Windows live home followed the environment: {live} (want {want})"
    assert asked == [uuid.UUID(_PROFILE_ID).bytes_le], f"the shell was not asked FOLDERID_Profile: {asked!r}"
    assert len(freed) == 1 and isinstance(freed[0], ctypes.c_wchar_p), \
        f"the shell's string was not freed: {freed!r}"
    scratch_bus = remote.bus_home(scratch / ".cairn/devices/cairn/machines/bus/0")
    assert scratch_bus != live, f"a scratch HOME's bus home reads as the live one: {scratch_bus}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
