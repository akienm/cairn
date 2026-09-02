"""PROBE — does a stale loop EXIT rather than running stale indefinitely?

The mechanism: the runner checks ``device.stale`` after each beat and exits
cleanly (unless COMMAND_DO_NOT_RESTART.flag suppresses), so the launcher
respawns a fresh process.

THE SIGNATURE: the liveness record carries ``stale: true`` in its state AND
the loop is still alive — the loop detected its own staleness and is still
running. After the build ships, this condition should be transient: the loop
detects staleness, exits, the launcher restarts.

ENOUGH: the liveness shows ``stale: false`` or the loop has restarted.
"""

from __future__ import annotations

import json

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "a-stale-loop-restarts-itself"
_HORIZON = 1000


def _liveness_shows_stale() -> bool:
    from cairn.devices.cairn.machines.ground_loop.liveness import read_liveness
    from cairn.tools.base.address import instance_path
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).astimezone()
    home = instance_path("cairn", 0) / "machines" / "ground_loop"
    found = read_liveness(now, home)
    if found["verdict"] != "LIVE":
        return False
    record = found.get("record") or {}
    state = record.get("state") or {}
    return state.get("stale", False) is True


def _trigger(now, context: dict) -> bool:
    return _liveness_shows_stale()


def _enough(context: dict) -> bool:
    return not _liveness_shows_stale()


def _carry(context: dict) -> dict:
    from cairn.devices.cairn.machines.ground_loop import staleness
    diag = staleness.diagnostics(tree=False)
    return {
        "finding": "the ground loop detected its own staleness and is still running — "
                   "the response mechanism (clean exit on stale) should have exited "
                   "this process after the detecting beat",
        "drifted_modules": [f["module"] for f in diag.get("drifted", [])],
        "pid": diag.get("pid"),
        "ticket": owning_ticket(_OWNING_TICKET),
    }


PROBE = Probe(
    why="a stale loop that keeps running holds modules that no longer match their files; "
        "this watches the exit mechanism — the loop should detect staleness and exit",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "ground_loop", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    print(json.dumps({
        "liveness_shows_stale": _liveness_shows_stale(),
        "would_trigger": _trigger(None, {}),
        "enough": _enough({}),
    }, indent=2, default=str))
