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


# THE CLIENT (ticket 7ea59855b1f4). A proof outside codemother asks a judge through ``ask``
# rather than importing the inspector (RULE 1; outline 9.4.3.3.4, Q#88: over the bus). The
# first ask in a process enters a scratch bus (the cairn device's published scratch_bus) and
# holds CodeMother's shim on it; every later ask in that process rides the same bus, so a proof
# module pays for one scratch bus, not one per tooth. The bus drops when the process exits.
# The shim import stays inside codemother, which is what lets this module be the door.
_HELD: dict = {}


class InspectRefused(RuntimeError):
    """codemother answered ``accepted: False``. ``raised`` names the type a judge raised, or is
    None when the ask itself was refused (off the allow-list, arguments that do not rebuild)."""

    def __init__(self, judge: str, reason: str, raised: str | None = None):
        super().__init__(f"inspect {judge!r} refused: {reason}")
        self.judge, self.reason, self.raised = judge, reason, raised


def _scratch_bus():
    if "bus" not in _HELD:
        import atexit
        import contextlib
        from datetime import datetime
        from cairn.devices.cairn.tools.scratch_bus.scratch_bus import bus_shim, scratch_bus
        from cairn.devices.codemother.shim import CodeMotherShim
        from cairn.tools.bus_client.roster import DeviceRoster
        stack = contextlib.ExitStack()
        bus = stack.enter_context(scratch_bus("inspect_ask"))
        roster = DeviceRoster(bus)
        roster.hold(bus_shim(bus, roster))
        roster.hold(CodeMotherShim(bus=bus))
        roster.pulse(datetime.now())
        atexit.register(stack.close)
        _HELD.update(bus=bus, stack=stack, minted=_HELD.get("minted", 0) + 1)
    return _HELD["bus"]


def ask(judge: str, *args, **kwargs):
    """``judge(*args, **kwargs)`` as codemother's ``inspect`` verb answers it, rebuilt.
    A refusal raises InspectRefused naming the judge and the reason (Law 7: a gate that cannot
    answer never reads green)."""
    reply = _scratch_bus().request(
        sender="cc", to="codemother", channel="personal", verb="inspect",
        why=f"inspect_wire.ask: {judge}",
        body={"judge": judge, "args": wire_encode(list(args)), "kwargs": wire_encode(kwargs)},
        timeout=300)
    body = reply.get("body") or {}
    if reply.get("sender") != "codemother" or not body.get("accepted"):
        raise InspectRefused(judge, body.get("reason") or f"no answer from codemother: {reply}",
                             body.get("raised"))
    return wire_decode(body["data"])


# THE FIXTURE WORLD (ticket 7ea59855b1f4, D4). Seven outside proofs stood a fixture world
# behind the inspector by writing its globals: _CHART_BERTHS, _TICKETS_ROOT and _crossing_roots.
# A write cannot cross a bus, and a judge keyword would let any caller choose the evidence a
# gate reads, which _crossing_roots exists to forbid (ticket d2ecdb867bc9). So the world is
# stood behind CodeMother's in-process inspector by her own published tool, for the length of
# the block, and put back after. It reaches only the inspector in this process: the scratch
# CodeMother that ``ask`` holds, never a live one.
_FIXTURE_GLOBALS = {"berths": "_CHART_BERTHS", "tickets_root": "_TICKETS_ROOT"}


def fixture(*, berths=None, tickets_root=None, crossing_roots=None):
    """A context: the inspector reads ``berths`` as its chart berths, ``tickets_root`` as its
    tickets root, and ``crossing_roots`` (a dict, or a callable answering one) as the world a
    crossing is derived from. Unnamed ones stay as they are."""
    import contextlib
    import importlib

    @contextlib.contextmanager
    def _world():
        insp = importlib.import_module("cairn.machines.build_inspector.inspector")
        named = {"berths": berths, "tickets_root": tickets_root}
        saved = {g: getattr(insp, g) for g in _FIXTURE_GLOBALS.values()}
        saved_roots = insp._crossing_roots
        try:
            for key, glob in _FIXTURE_GLOBALS.items():
                if named[key] is not None:
                    setattr(insp, glob, Path(named[key]))
            if crossing_roots is not None:
                insp._crossing_roots = (crossing_roots if callable(crossing_roots)
                                        else (lambda: crossing_roots))
            yield
        finally:
            for glob, value in saved.items():
                setattr(insp, glob, value)
            insp._crossing_roots = saved_roots

    return _world()
