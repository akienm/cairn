"""Proof for ticket 6b0dfaa14efd — the usage tool reads once, writes one file, keeps failures beside the last good.

Red first: written before cairn/tools/usage/usage.py exists. Every tooth injects the fetch and
patches urllib's urlopen to raise, so no network is touched. Teeth bind the tool at call time,
never at import.

    python <this file>
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "6b0dfaa14efd": {
        "1": "a_good_fetch_is_written_and_read_fresh",
        "2": "a_failed_fetch_sits_beside_the_last_good_reading",
        "3": "the_token_never_appears",
        "4": "a_missing_credential_is_recorded_and_the_hook_exits_zero",
        "5": "no_network_is_touched",
    },
}

TOKEN = "sk-ant-oat01-PROOF-TOKEN-0123456789"
RAW = {"seven_day": {"utilization": 46.0, "resets_at": "2026-11-14T08:00:00Z"},
       "five_hour": {"utilization": 12.5, "resets_at": "2026-11-12T22:00:00Z"}}


def _usage():
    from cairn.tools.usage import usage
    return usage


@contextlib.contextmanager
def _world(token: str | None = TOKEN):
    """A scratch store and credentials file, urlopen patched to raise."""
    real = urllib.request.urlopen

    def _no_network(*a, **k):
        raise AssertionError("the proof reached the network")

    urllib.request.urlopen = _no_network
    try:
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            creds = d / "creds.json"
            if token is not None:
                creds.write_text(json.dumps({"claudeAiOauth": {"accessToken": token}}), encoding="utf-8")
            env = {"CAIRN_USAGE_FILE": str(d / "usage" / "usage.json"), "CAIRN_USAGE_CREDS": str(creds)}
            yield env, d / "usage" / "usage.json"
    finally:
        urllib.request.urlopen = real


def _good(token, endpoint, timeout):
    return RAW


def _boom(token, endpoint, timeout):
    raise RuntimeError(f"HTTP 401 for Bearer {token}")


def a_good_fetch_is_written_and_read_fresh():
    u = _usage()
    with _world() as (env, path):
        rec = u.read_and_write(environ=env, now=1000.0, fetch=_good)
        assert path.is_file(), "no store file written"
        assert rec["error"] is None and rec["fetched_at"] == 1000.0, rec
        for key, pct in (("seven_day", 46.0), ("five_hour", 12.5)):
            w = rec[key]
            assert w and w["percent"] == pct and w["resets_at"], f"{key} not carried: {w}"
        got = u.last(environ=env, now=1030.0)
        assert got["state"] == "fresh" and got["age_s"] == 30, got
        assert got["reading"]["seven_day"]["percent"] == 46.0, got


def a_failed_fetch_sits_beside_the_last_good_reading():
    u = _usage()
    with _world() as (env, path):
        u.read_and_write(environ=env, now=1000.0, fetch=_good)
        before = json.loads(path.read_text(encoding="utf-8"))["last_good"]
        rec = u.read_and_write(environ=env, now=2000.0, fetch=_boom)
        assert rec["error"] and rec["error"]["at"] == 2000.0, rec
        assert rec["last_good"] == before, f"the last good reading was replaced: {rec['last_good']} vs {before}"
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        assert on_disk["error"] and on_disk["last_good"] == before, on_disk
        got = u.last(environ=env, now=2060.0)
        assert got["state"] == "error", f"a failed last fetch read as {got['state']}"
        assert got["reading"] == before and got["age_s"] == 1060, got


def the_token_never_appears():
    u = _usage()
    with _world() as (env, path):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            u.read_and_write(environ=env, now=1000.0, fetch=_boom)
            u.main(["--json"], environ=env, now=1000.0)
            u.main(["--fetch"], environ=env, fetch=_boom)
            u.main(["--hook"], environ=env, fetch=_boom)
        assert TOKEN not in out.getvalue(), "the token was printed"
        assert TOKEN not in path.read_text(encoding="utf-8"), "the token was written to the store"
        assert path.is_file(), "nothing was written to check"


def a_missing_credential_is_recorded_and_the_hook_exits_zero():
    u = _usage()
    for token in (None, ""):
        with _world(token) as (env, path):
            rc = u.main(["--hook"], environ=env, fetch=_good)
            assert rc == 0, f"--hook returned {rc} for token={token!r}"
            rec = json.loads(path.read_text(encoding="utf-8"))
            assert rec["error"] and rec["fetched_at"] is None, rec
    with _world() as (env, path):
        assert u.main(["--hook"], environ=env, fetch=_boom) == 0, "--hook returned non-zero on a failed fetch"


def no_network_is_touched():
    u = _usage()
    with _world() as (env, _path):
        with contextlib.redirect_stdout(io.StringIO()):
            u.read_and_write(environ=env, now=1.0, fetch=_good)
            u.main(["--hook"], environ=env, fetch=_good)
        # the default fetch is the only door to the network; with urlopen patched it must be loud, not silent
        rec = u.read_and_write(environ=env, now=2.0)
        assert rec["error"] and "reached the network" in rec["error"]["what"], (
            f"the default fetch did not go through urllib.request.urlopen: {rec['error']}")


TEETH = [a_good_fetch_is_written_and_read_fresh, a_failed_fetch_sits_beside_the_last_good_reading,
         the_token_never_appears, a_missing_credential_is_recorded_and_the_hook_exits_zero,
         no_network_is_touched]


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
