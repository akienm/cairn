"""Proof for ticket 3deafc9e36de "a client from another checkout refuses a stale live bus instead
of shutting it down".

MEASURED 2026-11-12 (memory: another root evicts the host bus): a run from an old sha or a git
worktree, on the live HOME, found the house bus answering ``stale`` (it serves the house root, not
the caller's), and ``_replace`` shut it down and started one from the worktree. Every other client
on the box was then served by a throwaway checkout's code. The fix: at the live home, a client
whose class root is not the house's own refuses, LOUDLY (Law 7), naming both roots and the way
out (``CAIRN_BUS_HOME=<scratch home>``), and sends no shutdown.

  1. test_a_foreign_root_at_the_live_home_sends_no_shutdown: through RemoteBus._call, a stale
     live bus meets a foreign root: BusStale names both roots and CAIRN_BUS_HOME, no shutdown;
  2. test_the_house_root_still_replaces_the_live_bus: the house root's client still shuts it down;
  3. test_a_foreign_root_at_a_scratch_home_still_replaces: a scratch home is the caller's own;
  4. test_no_resolvable_house_root_replaces_as_today: no env, no editable install: as before.

The wire is replaced for the call (remote.exchange records and answers, so nothing dials),
``subprocess.run`` is replaced so no systemctl runs, and ``_spawn`` raises, so a build that
still replaced could never start a bus at the live home. The subject is bound inside each tooth.

    bin/cairn test cairn/tools/bus_client/proofs/test_a_foreign_root_refuses_a_stale_live_bus.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"7579b542b4d4": {"3": "test_a_foreign_root_at_the_live_home_sends_no_shutdown"},
          "3deafc9e36de": {
    "1": "test_a_foreign_root_at_the_live_home_sends_no_shutdown",
    "2": "test_the_house_root_still_replaces_the_live_bus",
    "3": "test_a_foreign_root_at_a_scratch_home_still_replaces",
    "4": "test_no_resolvable_house_root_replaces_as_today",
}}

_FOREIGN_HOUSE = "/nonexistent/testing-3deaf-house-root"
_LIVE_BUS_ROOT = "/nonexistent/testing-3deaf-live-bus-root"
_ENV = "CAIRN_BUS_CLIENT_HOUSE_ROOT"


def _wired(monkeypatch, *, house: str | None):
    """Replace the wire and systemctl; set (or clear) the house root. Returns (remote, sent)."""
    from cairn.tools.bus_client import remote
    sent: list[dict] = []
    state = {"down": False}

    def exchange(req, h=None, timeout=None):
        sent.append(dict(req))
        op = req.get("op")
        if op == "shutdown":
            state["down"] = True
            return {"ok": True, "json": {"stopping": True}}
        if state["down"]:
            raise ConnectionRefusedError("testing-3deaf: the replaced bus is gone")
        return {"ok": False, "stale": True, "root": _LIVE_BUS_ROOT}

    def no_spawn(*a, **k):
        raise RuntimeError("testing-3deaf: this proof never spawns a bus")

    monkeypatch.setattr(remote, "exchange", exchange)
    monkeypatch.setattr(remote, "_spawn", no_spawn)
    monkeypatch.setattr(remote.subprocess, "run",
                        lambda args, *a, **k: remote.subprocess.CompletedProcess(args, 1, "", ""))
    if house is None:
        monkeypatch.delenv(_ENV, raising=False)
    else:
        monkeypatch.setenv(_ENV, house)
    return remote, sent


def _shutdowns(sent) -> int:
    return sum(1 for r in sent if r.get("op") == "shutdown")


def _scratch_home() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return Path(scratch_dir("testing-3deaf-home-"))


def test_a_foreign_root_at_the_live_home_sends_no_shutdown(monkeypatch):
    remote, sent = _wired(monkeypatch, house=_FOREIGN_HOUSE)
    live = remote._live_home()
    bus = remote.RemoteBus(live)
    try:
        bus.stats()
    except remote.BusStale as exc:
        said = str(exc)
    else:
        raise AssertionError(f"a foreign root at the live home did not refuse: {sent!r}")
    assert _shutdowns(sent) == 0, f"a foreign root sent shutdown to the live bus: {sent!r}"
    # the refusal names the house root as resolved: on Windows "/nonexistent/..." is
    # "C:\nonexistent\..." (ticket 7579b542b4d4)
    assert str(Path(_FOREIGN_HOUSE).resolve()) in said, f"the refusal does not name the house root: {said}"
    assert str(remote._CLASS_ROOT) in said, f"the refusal does not name the caller's root: {said}"
    assert _LIVE_BUS_ROOT in said, f"the refusal does not name the live bus's root: {said}"
    assert "CAIRN_BUS_HOME=" in said, f"the refusal does not say the way out: {said}"


def test_the_house_root_still_replaces_the_live_bus(monkeypatch):
    from cairn.tools.bus_client import remote as r
    remote, sent = _wired(monkeypatch, house=str(r._CLASS_ROOT))
    remote._replace(remote._live_home())
    assert _shutdowns(sent) == 1, f"the house root's client did not replace the stale bus: {sent!r}"


def test_a_foreign_root_at_a_scratch_home_still_replaces(monkeypatch):
    remote, sent = _wired(monkeypatch, house=_FOREIGN_HOUSE)
    remote._replace(_scratch_home())
    assert _shutdowns(sent) == 1, f"a scratch home's stale bus was not replaced: {sent!r}"


def test_no_resolvable_house_root_replaces_as_today(monkeypatch):
    remote, sent = _wired(monkeypatch, house=None)

    def no_distribution(name):
        raise remote.importlib.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(remote.importlib.metadata, "distribution", no_distribution)
    remote._replace(remote._live_home())
    assert _shutdowns(sent) == 1, f"with no house root the stale bus was not replaced: {sent!r}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
