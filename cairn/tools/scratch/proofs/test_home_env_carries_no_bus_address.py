"""Proof for ticket 3301915df481, clause 1: scratch.home_env hands a scratch-HOME subprocess no
bus address from its caller.

Measured 2026-11-12 on akienasus: a session whose env carried CAIRN_BUS_HOME=akiendelllinux.local:7419
ran test_root_verb_vocabulary.py, whose _run built dict(os.environ, HOME=scratch). The scratch-HOME
child dialled the Dell's live bus, and a tooth red over the Dell's status while the Dell's own seal
read it green. A scratch HOME is not isolation while the bus address rides an env var.

The tooth sets every CAIRN_BUS_* variable the corpus names, plus an ordinary one, and asks home_env
for a scratch HOME: every bus key is gone, the ordinary key and HOME are right, and an extra the
caller passes (an explicit CAIRN_BUS_HOME included) is applied last.

    python3 cairn/tools/scratch/proofs/test_home_env_carries_no_bus_address.py   # exit 0 = green
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"3301915df481": {"1": "test_home_env_drops_every_bus_variable_and_keeps_the_rest"}}

# The bus-location surface, as grep finds it over cairn/ and bin/ on 2026-11-12.
_BUS_VARS = ("CAIRN_BUS_HOME", "CAIRN_BUS_UNIT", "CAIRN_BUS_TLS_DIR", "CAIRN_BUS_MOUTH",
             "CAIRN_BUS_TCP_PORT", "CAIRN_BUS_DRAIN_S")


def test_home_env_drops_every_bus_variable_and_keeps_the_rest():
    from cairn.tools.scratch import scratch  # bound at call time: home_env is what the build adds

    saved = {k: os.environ.get(k) for k in (*_BUS_VARS, "CAIRN_FIXTURE_3301915DF481")}
    try:
        for k in _BUS_VARS:
            os.environ[k] = "akiendelllinux.local:7419" if k == "CAIRN_BUS_HOME" else "fixture"
        os.environ["CAIRN_FIXTURE_3301915DF481"] = "kept"
        home = Path("/nonexistent/scratch-home-3301915df481")

        env = scratch.home_env(home, PYTHONPATH="p")
        leaked = sorted(k for k in env if k.startswith("CAIRN_BUS_"))
        assert leaked == [], f"bus variables leaked into a scratch-HOME env: {leaked}"
        assert env["HOME"] == str(home), env.get("HOME")
        assert env["CAIRN_FIXTURE_3301915DF481"] == "kept"
        assert env["PYTHONPATH"] == "p"
        assert env.get("PATH") == os.environ.get("PATH")

        named = scratch.home_env(home, CAIRN_BUS_HOME="/scratch/bus")
        assert named["CAIRN_BUS_HOME"] == "/scratch/bus", "an explicit bus extra must survive"
        assert all(isinstance(v, str) for v in named.values())
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _main() -> int:
    try:
        test_home_env_drops_every_bus_variable_and_keeps_the_rest()
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        print(f"  FAIL  test_home_env_drops_every_bus_variable_and_keeps_the_rest: "
              f"{type(exc).__name__}: {exc}")
        return 1
    print("  PASS  test_home_env_drops_every_bus_variable_and_keeps_the_rest")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
