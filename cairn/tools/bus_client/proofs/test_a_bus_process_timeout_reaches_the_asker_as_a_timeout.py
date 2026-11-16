"""Proof for ticket 11d79defab3b: a bus-process timeout reaches the asker as a TimeoutError.

Measured 2026-11-16 on akiendelllinux. 149b9a1ab9c4's walk (q79) asked codemother's verdict gate
over the bus at 02:38:08 MST. Codemother took envelope 09d15224 and queued it on her verdict
worker (thread codemother-verdict-gate, tid 3020324, started 02:38:08 and still running at
03:05). The worker re-runs 149b's 74 instruments one after another. At 890 s the asker died with
    RuntimeError: bus process: TimeoutError: no reply to envelope 09d15224… from codemother
    within 890.0s — the target did not reply
Ticket.queueme waits on the ticket's own berth after a reply times out (ticket 0bcb816d6e9c,
STAGE_BUDGET_S 3600 s), but it catches TimeoutError. RemoteBus._call re-raised the bus process's
"TimeoutError: …" as RuntimeError, so the wait never ran, and the walk refused PROVED while the
verdict was still running. The client already maps a remote "LookupError: …" back to LookupError.

  1. a call the bus process answers with "TimeoutError: <words>" raises TimeoutError, and its
     message keeps the words;
  2. any other refusal still raises RuntimeError("bus process: …"), and a LookupError is still a
     LookupError;
  3. the same holds through reach(): a request from a far client, and from a local one, raises
     TimeoutError when the bus process timed out.

The wire is replaced: remote.exchange answers from a script, so nothing dials.

    bin/cairn test cairn/tools/bus_client/proofs/test_a_bus_process_timeout_reaches_the_asker_as_a_timeout.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"11d79defab3b": {
    "1": "test_a_remote_timeout_raises_timeout_error",
    "2": "test_other_refusals_keep_their_kinds",
    "3": "test_a_request_through_reach_raises_timeout_error",
}}

_WORDS = ("no reply to envelope testing-11d7 from codemother within 890.0s — "
          "the target did not reply (CP1: loud, not empty)")
_FAR = "far-box.invalid:7419"


def _scratch_home() -> str:
    from cairn.tools.scratch.scratch import scratch_dir
    return str(scratch_dir("testing-11d7-home-"))


def _wired(error: str, home: str, act):
    """Run ``act()`` with CAIRN_BUS_HOME=home and every call answered with ``error``;
    returns the exception act raised (or None)."""
    from cairn.tools.bus_client import remote

    def exchange(req, h=None, timeout=None):
        if req.get("op") == "stats":
            return {"ok": True, "json": {"pid": 1}}
        if req.get("op") == "hold":
            return {"ok": True, "held": list(req.get("devices") or [])}
        return {"ok": False, "error": error}

    saved_env, saved = os.environ.get("CAIRN_BUS_HOME"), remote.exchange
    os.environ["CAIRN_BUS_HOME"] = home
    remote.exchange = exchange
    try:
        act()
    except Exception as exc:  # the kind is what is measured
        return exc
    finally:
        remote.exchange = saved
        if saved_env is None:
            os.environ.pop("CAIRN_BUS_HOME", None)
        else:
            os.environ["CAIRN_BUS_HOME"] = saved_env
    return None


def _post_from(home: str):
    from cairn.tools.bus_client.remote import RemoteBus
    return lambda: RemoteBus(home).post(sender="testing-11d7", to="codemother", verb="x", body={})


def test_a_remote_timeout_raises_timeout_error():
    home = _scratch_home()
    got = _wired(f"TimeoutError: {_WORDS}", home, _post_from(home))
    assert isinstance(got, TimeoutError), f"a bus-process timeout arrived as {type(got).__name__}: {got!r}"
    assert str(got) == _WORDS, f"the timeout's words changed: {str(got)!r}"


def test_other_refusals_keep_their_kinds():
    home = _scratch_home()
    other = _wired("ValueError: a bad body", home, _post_from(home))
    assert type(other) is RuntimeError and str(other) == "bus process: ValueError: a bad body", repr(other)
    looked = _wired("LookupError: no device 'x'", home, _post_from(home))
    assert isinstance(looked, LookupError) and looked.args == ("no device 'x'",), repr(looked)


def test_a_request_through_reach_raises_timeout_error():
    from cairn.tools import bus_client
    for home in (_FAR, _scratch_home()):
        got = _wired(f"TimeoutError: {_WORDS}", home, lambda: bus_client.reach("codemother").request(
            sender="testing-11d7", to="codemother", verb="machines/verdict/queueme",
            body={"fileref": "testing-11d7"}, timeout=890.0))
        assert isinstance(got, TimeoutError), (
            f"a request through reach() at {home} arrived as {type(got).__name__}: {got!r}")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
