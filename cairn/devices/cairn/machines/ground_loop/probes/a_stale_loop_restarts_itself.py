"""PROBE — does a stale loop EXIT rather than running stale indefinitely?

Berth for the WATCHME that ticket ``a-stale-loop-restarts-itself`` carries.
The mechanism: the runner checks ``device.stale`` after each beat and exits
cleanly (unless COMMAND_DO_NOT_RESTART.flag suppresses), so the launcher
respawns a fresh process. The detection was already proved; this watches
the RESPONSE.

THE SIGNATURE: the self-trouble (ground-loop-is-older-than-the-code-it-judges)
is live AND its count is growing — the loop detected its own staleness and is
still running. After the build ships, this condition should be transient: the
loop detects staleness, exits, the launcher restarts, and the trouble stops
incrementing.

ENOUGH: the self-trouble is not live. A clean restart clears the condition.
"""

from __future__ import annotations

import json

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "a-stale-loop-restarts-itself"
_HORIZON = 1000


def _self_trouble_live() -> dict | None:
    from cairn.devices.cairn.machines.ground_loop.loop import SELF_TROUBLE
    from cairn.devices.trouble.trouble import TroubleDevice
    try:
        for t in TroubleDevice().live():
            if t.get("id") == SELF_TROUBLE:
                return t
    except OSError:
        pass
    return None


def _trigger(now, context: dict) -> bool:
    return _self_trouble_live() is not None


def _enough(context: dict) -> bool:
    return _self_trouble_live() is None


def _carry(context: dict) -> dict:
    t = _self_trouble_live()
    from cairn.devices.cairn.machines.ground_loop import staleness
    diag = staleness.diagnostics(tree=False)
    return {
        "finding": "the ground loop detected its own staleness and is still running — "
                   "the response mechanism (clean exit on stale) should have exited "
                   "this process after the detecting beat",
        "self_trouble_count": t.get("count") if t else 0,
        "self_trouble_last_seen": t.get("last_seen") if t else None,
        "drifted_modules": [f["module"] for f in diag.get("drifted", [])],
        "pid": diag.get("pid"),
        "ticket": owning_ticket(_OWNING_TICKET),
    }


PROBE = Probe(
    why="the staleness trouble has count=207, firing every ~9s — the loop detects "
        "its own age and keeps running stale; this watches the exit mechanism",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "ground_loop", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    t = _self_trouble_live()
    print(json.dumps({
        "live": t is not None,
        "count": t.get("count") if t else 0,
        "would_trigger": _trigger(None, {}),
        "enough": _enough({}),
    }, indent=2, default=str))
