"""PROBE — trouble panel surfaces live troubles

WATCHME(trouble-panel-surfaces-live-troubles): watches that the cairn device's
trouble pane declares correctly, its handler returns live troubles, and the
render kind produces the two-sided layout with a red light indicator.

Berths beside the cairn device because the trouble panel IS its pane.
"""
from __future__ import annotations

from cairn.tools.base.probe import Probe


def _trigger(now, context: dict) -> bool:
    result = _check(context)
    return not result["healthy"]


def _check(context: dict) -> dict:
    cached = context.get("trouble_panel_check")
    if cached is not None:
        return cached

    result = {"pane_declared": False, "handler_works": False,
              "render_works": False, "healthy": False}
    try:
        from cairn.devices.cairn.device import CairnDevice
        d = CairnDevice()
        panes = d.declared_panes()
        tp = [p for p in panes if p.get("kind") == "trouble"]
        result["pane_declared"] = bool(tp)
        if not tp:
            context["trouble_panel_check"] = result
            return result

        data = tp[0]["handler"]()
        result["handler_works"] = isinstance(data, list)
        if not result["handler_works"]:
            context["trouble_panel_check"] = result
            return result

        from cairn.devices.web_server.render import render_pane
        sample = data[:3] if data else [{"id": "probe", "standing": "OPEN",
                                          "why": "probe check", "count": 1}]
        html = render_pane({"kind": "trouble", "label": "troubles", "data": sample})
        result["render_works"] = ("trouble-list" in html and "trouble-detail" in html
                                  and "red-light" in html)
        result["healthy"] = (result["pane_declared"] and result["handler_works"]
                             and result["render_works"])
    except Exception as e:
        result["error"] = str(e)

    context["trouble_panel_check"] = result
    return result


def _carry(context: dict) -> dict:
    return _check(context)


def _enough(context: dict) -> bool:
    result = _check(context)
    return result["healthy"]


PROBE = Probe(
    why="the trouble panel is the cairn device's first pane — it surfaces live "
        "troubles from CairnCommons/troubles/ in a two-sided layout with a red "
        "light indicator. This probe watches that the pane declaration, handler, "
        "and render kind all work together correctly.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "triage", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=100,
)
