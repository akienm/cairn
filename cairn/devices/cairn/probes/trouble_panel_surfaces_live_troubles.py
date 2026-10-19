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

WHAT IS LEFT IS WHAT CAN ACTUALLY BREAK WHILE NOBODY IS EDITING: the read. The pane's
handler reads trouble's store as files through the tool trouble publishes (ticket
ee04bb869795 — it asked verb ``live`` over the bus until 2026-10-18, and every reply stood as
a bus row), so between one beat and the next it can start failing because the store moved,
a file in it went bad, or the tool's rows changed shape. None of that is visible to a proof —
every one of them is a running-system fact — and every one of them ends with the panel dark
while the page still loads. That is the drift this watch exists for.

THE ROOTS ARRIVE IN THE CONTEXT when a caller has them (``context["roots"]``); absent, the
tool reads the real instance root. A probe carries no authority (Law 6): it reads, and an
absent store is UNHEALTHY and says so, never zero troubles.
"""
from __future__ import annotations

from cairn.tools.base.probe import Probe, watch_carry

_TICKET_ID = "7a1265439f54"


def _trigger(now, context: dict) -> bool:
    return not _check(context)["healthy"]


def _check(context: dict) -> dict:
    cached = context.get("trouble_panel_check")
    if cached is not None:
        return cached

    result = {"pane_declared": False, "lane_reached": False, "healthy": False,
              "live_count": None}
    try:
        from cairn.devices.cairn.device import CairnDevice
        panes = CairnDevice(roots=context.get("roots")).declared_panes()
        tp = [p for p in panes if p.get("kind") == "trouble"]
        result["pane_declared"] = bool(tp)
        if not tp:
            context["trouble_panel_check"] = result
            return result

        # THE HANDLER RAISES WHEN THE STORE IS ABSENT, and that is the whole reason this
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
    """The measurement, plus — when it is unhealthy — WHY, as the finding. ``watch_carry``
    reads ``finding`` and nothing else; a reason left under ``error`` reaches the ticket as
    the generic no-finding, which is how 7a1265439f54 landed at FIXME on 2026-10-05 saying
    only that its probe had nothing to say (Law 7)."""
    out = dict(_check(context))
    if not out["healthy"]:
        if out.get("error"):
            out["finding"] = f"the trouble panel's read failed: {out['error']}"
        elif not out["pane_declared"]:
            out["finding"] = "the cairn device declares no trouble pane"
        else:
            out["finding"] = "the trouble pane's handler did not come back with a list"
    return out


def _enough(context: dict) -> bool:
    return _check(context)["healthy"]


PROBE = Probe(
    why="the trouble panel is the cairn device's first pane, and it is the surface a human "
        "meets live troubles on. Its handler reads trouble's store as files through the "
        "tool trouble publishes, so it can go dark between beats without a single line of "
        "code changing — a moved store, a bad file, a changed row. This probe watches the read, "
        "which is the half a proof cannot see; the rendering is deterministic and is proved "
        "at cairn/devices/cairn/proofs/test_trouble_panel.py.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "triage", "kind": "efficacy"},
    verb="watch",
    carry=watch_carry(_TICKET_ID, _carry, fails=_trigger),
    enough=_enough,
    horizon=100,
)
