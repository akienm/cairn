"""inspect_wire — the wire shape of codemother's `inspect` verb, published (ticket 266d39d56d06).

Code outside codemother asks build_inspector's judges over the bus (the `inspect` verb, ticket
4c4addb09adb's children). The caller encodes the arguments and decodes the reply; codemother
decodes the arguments and encodes the reply. One module holds both directions so the two sides
cannot disagree, and codemother publishes it, because RULE 1 lets code outside a device reach
into it only through a tool it publishes.

    from cairn.devices.codemother.tools.inspect_wire.inspect_wire import wire_encode, wire_decode
"""
from __future__ import annotations

from pathlib import Path


# THE WIRE SHAPE (ticket 266d39d56d06, D2). The bus carries JSON, and a judge takes Paths,
# Workflows, tickets and frozensets. Each of those crosses in its standing serial form, under
# a {"__wire__": <kind>, "v": ...} tag, and is rebuilt on arrival:
#   - a Path crosses as its string;
#   - a Workflow crosses as its workflow string, parsed with parse_workflow on arrival;
#   - a Ticket crosses as its id, and arrives as the id, which is what every judge reads;
#   - a frozenset or a tuple crosses as a list.
# Both directions live here, so the caller and the answerer cannot disagree. Anything else
# that is not JSON is refused by its type name, never coerced (Law 7).
def wire_encode(value):
    """``value`` in a form the bus can carry; ``wire_decode`` rebuilds it."""
    from cairn.tools.base.workflow_grammar import Workflow
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return {"__wire__": "path", "v": str(value)}
    if isinstance(value, Workflow):
        from cairn.tools.base.transitions import _render_at
        return {"__wire__": "workflow", "v": _render_at(value, value.cursor, value.phase),
                "objects": bool(value.objects)}
    if type(value).__name__ == "Ticket" and type(value).__module__ == "cairn.machines.ticket.ticket":
        return {"__wire__": "ticket", "v": value.id}
    if isinstance(value, (set, frozenset)):
        return {"__wire__": "frozenset", "v": sorted(wire_encode(v) for v in value)}
    if isinstance(value, tuple):
        return {"__wire__": "tuple", "v": [wire_encode(v) for v in value]}
    if isinstance(value, list):
        return [wire_encode(v) for v in value]
    if isinstance(value, dict):
        bad = [k for k in value if not isinstance(k, str)]
        if bad:
            raise TypeError(f"inspect wire: a dict key must be a string, got {bad[0]!r}")
        return {k: wire_encode(v) for k, v in value.items()}
    raise TypeError(f"inspect wire: a {type(value).__module__}.{type(value).__qualname__} "
                    "has no wire form")


def wire_decode(value):
    """The value ``wire_encode`` put on the bus, rebuilt."""
    if isinstance(value, list):
        return [wire_decode(v) for v in value]
    if not isinstance(value, dict):
        return value
    kind = value.get("__wire__")
    if kind is None:
        return {k: wire_decode(v) for k, v in value.items()}
    if kind == "path":
        return Path(value["v"])
    if kind == "workflow":
        import dataclasses
        from cairn.tools.base.workflow_grammar import parse_workflow
        wf = parse_workflow(value["v"])
        return wf if value.get("objects", True) else dataclasses.replace(wf, objects=())
    if kind == "ticket":
        return value["v"]
    if kind == "frozenset":
        return frozenset(wire_decode(v) for v in value["v"])
    if kind == "tuple":
        return tuple(wire_decode(v) for v in value["v"])
    raise ValueError(f"inspect wire: unknown kind {kind!r}")
