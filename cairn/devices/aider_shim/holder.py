"""hold() — put Cairn's surfaces at their import names, THEN let aider be imported.

ORDER IS THE WHOLE MECHANISM, and it is the one thing here that can be got wrong silently.
Every surface must be at ``sys.modules[name]`` before any aider module executes, because
the first ``import litellm`` or ``from posthog import Posthog`` that runs against an empty
slot loads the real package, and once loaded it stays loaded — nothing later can take it
back. So ``hold()`` refuses to run after aider is already imported rather than doing half
a job: a device that quietly held two of three surfaces would look exactly like one that
held all three, right up until the call that dialed out.

WHY STUBS RATHER THAN CONFIGURATION. aider has an analytics opt-out. Using it would mean
the disposition lives in the foreign program's code, is re-decided by every upgrade of it,
and is invisible to us when it changes. Akien ruled the other way on 2026-08-16 — *"Stub
them at sys.modules like litellm"* — and the packages are not installed either, so the
stub is not the only thing between a telemetry client and the network. It is the second
lock on a door that also has no key cut for it.

THE STUBS ARE NOT INERT-BY-SILENCE. Each records what was asked of it. An analytics client
that is never called and one that is called constantly are the same shape at rest, and the
difference matters: if aider is trying to send events, this device should be able to say
so rather than merely not send them.
"""

from __future__ import annotations

import sys
import types

from cairn.devices.aider_shim import interceptor

#: Marks a module as one of ours, so a check can tell our surface from the real package.
#: ``interceptor._Surface`` carries it too — identity, not a name match.
SURFACE_FLAG = "_cairn_surface"


class _Recorder:
    """A no-op that remembers being used. Every stub attribute resolves to one of these."""

    def __init__(self, module: str, path: str, calls: list):
        self._module, self._path, self._calls = module, path, calls

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return _Recorder(self._module, f"{self._path}.{name}", self._calls)

    def __call__(self, *a, **kw):
        self._calls.append({"module": self._module, "called": self._path,
                            "args": len(a), "kwargs": sorted(kw)})
        return self

    def __repr__(self):
        return f"<cairn stub {self._module}.{self._path}>"

    # aider constructs Posthog(...) and catches MixpanelException; both must behave.
    def __bool__(self):
        return False


class _Stub(types.ModuleType):
    """A module that answers any attribute with a recorder, and records what was asked."""

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        calls = self.__dict__.setdefault("_cairn_calls", [])
        self.__dict__.setdefault("_cairn_asked", []).append(name)
        return _Recorder(self.__name__, name, calls)


def _stub(name: str, exceptions=()) -> types.ModuleType:
    """Build a stub for ``name``. Exception names must be REAL classes, not recorders.

    aider writes ``except MixpanelException:`` — a recorder there raises TypeError inside
    an except clause, which is a crash wearing an unrelated traceback. Anything the foreign
    program uses in a `raise` or `except` position has to be an actual exception class.
    """
    mod = _Stub(name)
    setattr(mod, SURFACE_FLAG, True)
    mod.__dict__["_cairn_calls"] = []
    mod.__dict__["_cairn_asked"] = []
    for ex in exceptions:
        mod.__dict__[ex] = type(ex, (Exception,), {"__module__": name})
    return mod


#: Measured off aider/analytics.py at HEAD 5dc9490bb: `from mixpanel import
#: MixpanelException` and `from posthog import Posthog`. The exception name is listed
#: because aider uses it in an `except` clause; Posthog is a constructor and a recorder
#: handles it.
STUBS = {
    "mixpanel": ("MixpanelException",),
    "posthog": (),
}


class HeldTooLate(RuntimeError):
    """aider was imported before the surfaces were installed. Loud, per Law 7."""


def held() -> dict:
    """What is standing at each name right now — ours, or something else."""
    out = {"litellm": interceptor.installed()}
    for name in STUBS:
        mod = sys.modules.get(name)
        out[name] = bool(mod is not None and getattr(mod, SURFACE_FLAG, False))
    return out


def hold(**interceptor_kwargs) -> dict:
    """Install every surface. MUST be called before aider is imported.

    Returns the standing state, which a caller may assert on. Raises :class:`HeldTooLate`
    if aider is already in ``sys.modules`` — refusing is the honest move, because by then
    the real packages may already be loaded and there is no way to unload them.
    """
    already = sorted(m for m in sys.modules if m == "aider" or m.startswith("aider."))
    if already:
        raise HeldTooLate(
            f"aider is already imported ({len(already)} modules, e.g. {already[:3]}) — the "
            "surfaces must be installed BEFORE any aider module executes, and a real "
            "package loaded on the way in cannot be unloaded afterwards."
        )
    for name, exceptions in STUBS.items():
        existing = sys.modules.get(name)
        if existing is not None and not getattr(existing, SURFACE_FLAG, False):
            raise HeldTooLate(
                f"the real {name!r} is already loaded in this process — it cannot be "
                "replaced meaningfully, since anything holding a reference to it keeps it."
            )
        sys.modules[name] = _stub(name, exceptions)
    interceptor.install(**interceptor_kwargs)
    return held()


def asked() -> dict:
    """What the held program actually asked of each surface. Evidence, not decoration.

    The device's claim is that no telemetry leaves the process. The strong form of that is
    'nothing was sent'; the honest form adds 'and here is what it TRIED to send'. Reading
    this after a live fire is how the filed-edge hazard stops being a paragraph.
    """
    out = {}
    for name in STUBS:
        mod = sys.modules.get(name)
        if mod is not None and getattr(mod, SURFACE_FLAG, False):
            out[name] = {"attributes_read": list(mod.__dict__.get("_cairn_asked", [])),
                         "calls": list(mod.__dict__.get("_cairn_calls", []))}
    surface = sys.modules.get("litellm")
    if interceptor.installed():
        out["litellm"] = {"attributes_read": sorted(surface._cairn_touched),
                          "asks": surface._cairn_log.entries}
    return out
