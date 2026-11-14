"""inspect_wire — the wire shape of codemother's `inspect` verb, and the client that asks it
(tickets 266d39d56d06, 7ea59855b1f4; a plain tool since 0c2c3f53c2be).

Code outside codemother asks build_inspector's judges over the bus (the `inspect` verb, ticket
4c4addb09adb's children). The caller encodes the arguments and decodes the reply; codemother
decodes the arguments and encodes the reply. One module holds both directions so the two sides
cannot disagree. It is a tool with users (Law 6), not a device's: it imports nothing of
codemother's, and the CodeMother that answers is a separate process launched by name.

    from cairn.tools.inspect_wire.inspect_wire import wire_encode, wire_decode, ask, launch
"""
from __future__ import annotations

from pathlib import Path


# THE WIRE SHAPE (ticket 266d39d56d06, D2). The bus carries JSON, and a judge takes Paths,
# Workflows, tickets and frozensets. Each of those crosses in its standing serial form, under
# a {"__wire__": <kind>, "v": ...} tag, and is rebuilt on arrival:
#   - a Path crosses as {"__wire__": "path", "root": "cairn"|"CairnCommons", "rel": <posix>} (ticket e215f7524659):
#     the ROOT it sits under and where under it, never the asking box's absolute spelling, which names a disk the
#     answerer may not share. A path under neither root, or one carrying '..', is refused at encode; an unknown
#     root is refused at decode; the rel is split on both / and \\ so a Windows caller's spelling decodes on Linux;
#   - a Workflow crosses as its workflow string, parsed with parse_workflow on arrival;
#   - a Ticket crosses as its id, and arrives as the id, which is what every judge reads;
#   - a frozenset or a tuple crosses as a list.
# Both directions live here, so the caller and the answerer cannot disagree. Anything else
# that is not JSON is refused by its type name, never coerced (Law 7).
def _roots() -> dict:
    """The two roots a path may cross under, as THIS process names them (ticket e215f7524659)."""
    from cairn.tools.edges.edges import commons_root
    return {"cairn": Path(__file__).resolve().parents[3], "CairnCommons": Path(commons_root())}


def _path_to_wire(value: Path) -> dict:
    for name, root in _roots().items():
        try:
            rel = Path(value).resolve().relative_to(Path(root).resolve())
        except ValueError:
            continue
        if ".." in rel.parts:
            break
        return {"__wire__": "path", "root": name, "rel": rel.as_posix()}
    raise ValueError(f"inspect wire: path {str(value)!r} is under neither root ({', '.join(_roots())}); "
                     "a path crosses by its root, so a scratch or foreign path has no wire form")


def _path_from_wire(value: dict) -> Path:
    import re
    roots = _roots()
    root = value.get("root")
    if root not in roots:
        raise ValueError(f"inspect wire: path root {root!r} is not one of {sorted(roots)}")
    parts = [p for p in re.split(r"[\\/]", str(value.get("rel", ""))) if p not in ("", ".")]
    if ".." in parts:
        raise ValueError(f"inspect wire: path rel {value.get('rel')!r} escapes its root")
    return Path(roots[root]).joinpath(*parts)


def wire_encode(value):
    """``value`` in a form the bus can carry; ``wire_decode`` rebuilds it."""
    from cairn.tools.base.workflow_grammar import Workflow
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return _path_to_wire(value)
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
        return _path_from_wire(value)
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


# THE CLIENT (tickets 7ea59855b1f4, 0c2c3f53c2be). Code outside codemother asks a judge through
# ``ask`` rather than importing the inspector (RULE 1; outline 9.4.3.3.4, Q#88: over the bus).
# The CodeMother that answers is a real process: a bus process under a scratch HOME, started by
# the cairn device's published scratch_bus.launch, which holds her by name the way the rack
# does, so the asking process never imports her shim. Her world is named by her environment at
# launch (``launch``), never by a write into her module, and her inspector honours it only
# under a scratch HOME (ticket d2ecdb867bc9). Outside any launch block the first ask in a
# process launches one plain world and every later ask rides it, so a proof module pays for one
# bus process, not one per tooth; it is shut down at exit.
#
# THE ANSWER'S CONTRACT (D7): the bus is JSON, so what ask returns equals the direct call's
# JSON-normal form, json.loads(json.dumps(direct, default=str)). The codec is not taught to
# rebuild a judge's returned tuple; compare in that form.
_HELD: dict = {}      # "bus": the world asks ride now; "default", "stack", "minted": the default
_WORLDS: list = []    # open launch worlds, innermost last


class InspectRefused(RuntimeError):
    """codemother answered ``accepted: False``. ``raised`` names the type a judge raised, or is
    None when the ask itself was refused (off the allow-list, arguments that do not rebuild)."""

    def __init__(self, judge: str, reason: str, raised: str | None = None):
        super().__init__(f"inspect {judge!r} refused: {reason}")
        self.judge, self.reason, self.raised = judge, reason, raised


ROOT_ENV = {"berths": "CAIRN_BUILD_INSPECTOR_CHART_BERTHS",
            "tickets_root": "CAIRN_BUILD_INSPECTOR_TICKETS_ROOT",
            "crossing_roots": "CAIRN_BUILD_INSPECTOR_CROSSING_ROOTS"}


def _launch_env(berths, tickets_root, crossing_roots) -> dict:
    import json
    env = {}
    if berths is not None:
        env[ROOT_ENV["berths"]] = str(Path(berths))
    if tickets_root is not None:
        env[ROOT_ENV["tickets_root"]] = str(Path(tickets_root))
    if crossing_roots is not None:
        roots = crossing_roots() if callable(crossing_roots) else crossing_roots
        env[ROOT_ENV["crossing_roots"]] = json.dumps({k: str(v) for k, v in roots.items()})
    return env


def _settle() -> None:
    """Point ``_HELD["bus"]`` at the world an ask rides now."""
    bus = _WORLDS[-1] if _WORLDS else _HELD.get("default")
    if bus is None:
        _HELD.pop("bus", None)
    else:
        _HELD["bus"] = bus


def launch(*, berths=None, tickets_root=None, crossing_roots=None):
    """A context: a scratch CodeMother whose inspector reads ``berths`` as its chart berths,
    ``tickets_root`` as its tickets root and ``crossing_roots`` (a dict of root name to path,
    or a callable answering one, read once at launch) as the world a crossing is derived from.
    Unnamed roots are her scratch HOME's own. Every ask inside the block rides her; her bus is
    shut down at the block's end. Yields the bus."""
    import contextlib
    from cairn.devices.cairn.tools.scratch_bus.scratch_bus import launch as launch_device

    @contextlib.contextmanager
    def _world():
        with launch_device("codemother", _launch_env(berths, tickets_root, crossing_roots),
                           prefix="inspect-wire") as bus:
            _WORLDS.append(bus)
            _settle()
            try:
                yield bus
            finally:
                _WORLDS.remove(bus)
                _settle()

    return _world()


def _bus():
    if _WORLDS:
        return _WORLDS[-1]
    if "default" not in _HELD:
        import atexit
        import contextlib
        from cairn.devices.cairn.tools.scratch_bus.scratch_bus import launch as launch_device
        stack = contextlib.ExitStack()
        bus = stack.enter_context(launch_device("codemother", prefix="inspect-wire"))
        atexit.register(stack.close)
        _HELD.update(default=bus, stack=stack, minted=_HELD.get("minted", 0) + 1)
    _settle()
    return _HELD["default"]


def ask(judge: str, *args, **kwargs):
    """``judge(*args, **kwargs)`` as codemother's ``inspect`` verb answers it, rebuilt.
    A refusal raises InspectRefused naming the judge and the reason (Law 7: a gate that cannot
    answer never reads green)."""
    try:
        reply = _bus().request(
            sender="cc", to="codemother", channel="personal", verb="inspect",
            why=f"inspect_wire.ask: {judge}",
            body={"judge": judge, "args": wire_encode(list(args)), "kwargs": wire_encode(kwargs)},
            timeout=300)
    except (OSError, RuntimeError, LookupError) as exc:
        raise InspectRefused(judge, f"no answer from codemother over the bus: "
                                    f"{type(exc).__name__}: {exc}") from exc
    body = (reply or {}).get("body") or {}
    if (reply or {}).get("sender") != "codemother" or not body.get("accepted"):
        raise InspectRefused(judge, body.get("reason") or f"no answer from codemother: {reply}",
                             body.get("raised"))
    return wire_decode(body["data"])
