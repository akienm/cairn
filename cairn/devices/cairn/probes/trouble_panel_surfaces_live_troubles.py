"""PROBE — trouble panel surfaces live troubles

WATCHME(trouble-panel-surfaces-live-troubles): watches that the cairn device's trouble
pane declares correctly and that its handler can actually reach the trouble lane and come
back with live troubles.

Berths beside the cairn device because the trouble panel IS its pane.

WHAT THIS PROBE STOPPED WATCHING, AND WHY THAT IS NOT A LOSS (2026-09-07, ticket
9579a6f9cec6 clause (f)). It used to import ``cairn.devices.web_server.render`` and assert
that the rendered HTML carried the two-sided layout and the red light — a cross-device
import from a probe, which is the isolation defect wearing a watch's clothes. The fix is
not to route the render through a verb; it is to notice that RENDERING IS NOT A THING THAT
DRIFTS BETWEEN BEATS. ``render_pane`` is a pure function of its argument: it produces the
same HTML on every pulse until somebody edits it, and an edit is caught by the proofs that
own it (``cairn/devices/cairn/proofs/test_trouble_panel.py``, the render teeth) and by
``component_color``, which reds a component whose source moved off its seal. A probe that
re-asserts a deterministic function once per heartbeat is not measuring, it is reciting —
and it was the only reason this file reached across a device boundary.

WHAT IS LEFT IS WHAT CAN ACTUALLY BREAK WHILE NOBODY IS EDITING: the route. The pane's
handler asks the trouble device for ``live`` over the bus, so between one beat and the
next it can start failing because the lane is down, the verb was renamed, the shim stopped
being discovered, or the reply changed shape. None of that is visible to a proof — every
one of them is a running-system fact — and every one of them ends with the panel dark
while the page still loads. That is the drift this watch exists for.

THE BUS ARRIVES IN THE CONTEXT, never by import: ``CairnShim`` seeds it, because the shim
is the one thing that knows both its device and its bus (the same routing answer
``BaseShim`` has given since 2026-08-04). With no bus in the context the probe is UNHEALTHY
and says so — it does not build one. A probe carries no authority (Law 6), and dialing a
bus of its own would mean firing a ground-loop beat from inside a ground-loop beat.
"""
from __future__ import annotations

from cairn.tools.base.probe import Probe


def _trigger(now, context: dict) -> bool:
    return not _check(context)["healthy"]


def _check(context: dict) -> dict:
    cached = context.get("trouble_panel_check")
    if cached is not None:
        return cached

    result = {"pane_declared": False, "lane_reached": False, "healthy": False,
              "live_count": None}
    try:
        bus = context.get("bus")
        if bus is None:
            raise RuntimeError(
                "no bus in the pulse context — the pane's handler asks the trouble lane "
                "over the bus, so without one this probe cannot tell a healthy panel from "
                "an unreachable lane, and MUST NOT report the healthy one")

        from cairn.devices.cairn.device import CairnDevice
        panes = CairnDevice(bus=bus).declared_panes()
        tp = [p for p in panes if p.get("kind") == "trouble"]
        result["pane_declared"] = bool(tp)
        if not tp:
            context["trouble_panel_check"] = result
            return result

        # THE HANDLER RAISES WHEN THE LANE IS UNREACHABLE, and that is the whole reason this
        # call is the measurement. An empty list here is GOOD NEWS — a healthy system with no
        # standing troubles — so a handler that returned [] on failure would make this probe
        # green at exactly the moment it should be red (Law 7).
        data = tp[0]["handler"]()
        result["lane_reached"] = isinstance(data, list)
        result["live_count"] = len(data) if isinstance(data, list) else None
        result["healthy"] = result["pane_declared"] and result["lane_reached"]
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"

    context["trouble_panel_check"] = result
    return result


def _carry(context: dict) -> dict:
    return _check(context)


def _enough(context: dict) -> bool:
    return _check(context)["healthy"]


PROBE = Probe(
    why="the trouble panel is the cairn device's first pane, and it is the surface a human "
        "meets live troubles on. Its handler asks the trouble device for `live` over the "
        "bus, so it can go dark between beats without a single line of code changing — a "
        "down lane, a renamed verb, an undiscovered shim. This probe watches the route, "
        "which is the half a proof cannot see; the rendering is deterministic and is proved "
        "at cairn/devices/cairn/proofs/test_trouble_panel.py.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "triage", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=100,
)
