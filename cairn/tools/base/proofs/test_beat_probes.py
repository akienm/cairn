"""A DEVICE FIRES ITS OWN CLOCK PROBES ON ITS OWN PULSE — the shared firer, ticket 32959e65ec5a.

Since bae622881f03 (2026-09-30) the heartbeat calls groundloop/pulse.py and nothing else, so a
device that owns clock probes fires them from its pulse. ``BeatProbes`` is the one firer every
such pulse composes, written once so the crossing memory is not re-derived per device (Law 1).
It fires THROUGH BaseShim, so these teeth read the shim's semantics as they arrive at a pulse:

  (a) a trigger that stays true pokes once, at the crossing, not every beat;
  (b) a ``while_true`` probe pokes every beat it holds;
  (c) a raising trigger is recorded refused and the others still fire;
  (d) a probe whose ``enough`` holds is cleared, and held as cleared on the next beat;
  (e) a named probe with no module is recorded missing, never raised;
  (f) the bus rides the pulse context, because a probe that asks over the bus needs it;
  (g) the firer flushes its own bus once per beat — nothing else does since the loop lost it;
  (h) a bus given as a factory is built on the first beat, never at construction.

Everything runs against a temp folder of stub probes and a stub bus. The firer is imported
inside each tooth, never at module level, so a build with the firer taken away reds teeth
rather than crashing this runner.
"""
from __future__ import annotations

import sys
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"32959e65ec5a": {
    "helper-a": "a trigger that stays true pokes once across two beats",
    "helper-b": "a while_true probe pokes on every beat",
    "helper-c": "a raising trigger is recorded refused and the rest still fire",
    "helper-d": "a probe whose enough holds is cleared and then held as cleared",
    "helper-e": "a named probe with no module is recorded missing, never raised",
    "helper-f": "the bus rides the pulse context",
    "helper-g": "the firer flushes its bus once per beat and records it",
    "helper-h": "a bus factory is called on the first beat, never at construction",
}}
FAILURES: list[str] = []

STUBS = {
    "standing": "trigger=lambda now, ctx: True",
    "chatty": "trigger=lambda now, ctx: True, while_true=True",
    "broken": "trigger=_boom",
    "done": "trigger=lambda now, ctx: True, enough=lambda ctx: True",
    "needs_bus": "trigger=lambda now, ctx: ctx.get('bus') is not None",
}


def ok(name: str, passed: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if passed else 'RED '} {name}")
    if detail:
        print(f"         -> {detail}")
    if not passed:
        FAILURES.append(f"{name}: {detail}")


class StubBus:
    def __init__(self) -> None:
        self.posts: list[dict] = []
        self.flushes = 0

    def post(self, **kw) -> dict:
        self.posts.append(kw)
        return {"id": f"env-{len(self.posts)}"}

    def flush(self) -> dict:
        self.flushes += 1
        return {"flushed": self.flushes}


def _folder(tmp: Path) -> Path:
    probes = tmp / "fixture_device" / "probes"
    probes.mkdir(parents=True)
    for name, args in STUBS.items():
        (probes / f"{name}.py").write_text(textwrap.dedent(f"""\
            from cairn.tools.base.probe import Probe

            def _boom(now, ctx):
                raise RuntimeError("the fixture trigger raises on purpose")

            PROBE = Probe(why="fixture probe {name} for test_beat_probes", to="fixture_target",
                          {args})
            """), encoding="utf-8")
    return probes.parent


def _whys(entries: list[dict]) -> list[str]:
    return [e.get("why", "") for e in entries]


def _named(entries: list[dict], name: str) -> list[dict]:
    return [e for e in entries if f"fixture probe {name} " in e.get("why", "")]


def main() -> int:
    print("a device fires its own clock probes on its own pulse — the shared firer")
    now = datetime.now(timezone.utc)
    with tempfile.TemporaryDirectory(prefix="test_beat_probes-") as tmp:
        folder = _folder(Path(tmp))
        names = list(STUBS) + ["no_such_probe"]
        try:
            from cairn.tools.base.beat_probes import BeatProbes
            bus = StubBus()
            firer = BeatProbes("fixture_device", folder, names, bus=bus)
            one = firer.on_pulse(now, {})
            two = firer.on_pulse(now, {})
        except Exception as e:  # noqa: BLE001 — every tooth below reds on an absent firer
            for tooth in PROVES["32959e65ec5a"].values():
                ok(tooth, False, f"{type(e).__name__}: {e}")
            return _verdict()

        ok(PROVES["32959e65ec5a"]["helper-a"],
           len(_named(one["fired"], "standing")) == 1 and not _named(two["fired"], "standing")
           and any("still true" in h.get("reason", "") for h in _named(two["held"], "standing")),
           f"beat1 fired={len(_named(one['fired'], 'standing'))} beat2 held={_named(two['held'], 'standing')}")
        ok(PROVES["32959e65ec5a"]["helper-b"],
           len(_named(one["fired"], "chatty")) == 1 and len(_named(two["fired"], "chatty")) == 1,
           f"beat1={_named(one['fired'], 'chatty')} beat2={_named(two['fired'], 'chatty')}")
        broken = _named(one["fired"], "broken")
        others = [n for n in ("standing", "chatty", "done", "needs_bus") if _named(one["fired"], n)]
        ok(PROVES["32959e65ec5a"]["helper-c"],
           len(broken) == 1 and broken[0].get("outcome") == "refused" and len(others) == 4,
           f"broken={broken} others_fired={others}")
        done1, done2 = _named(one["fired"], "done"), _named(two["held"], "done")
        ok(PROVES["32959e65ec5a"]["helper-d"],
           len(done1) == 1 and "cleared" in done1[0]
           and len(done2) == 1 and done2[0].get("reason", "").startswith("cleared"),
           f"beat1={done1} beat2={done2}")
        missing = one.get("missing") or []
        ok(PROVES["32959e65ec5a"]["helper-e"],
           [m.get("name") for m in missing] == ["no_such_probe"],
           f"missing={missing}")
        ok(PROVES["32959e65ec5a"]["helper-f"],
           len(_named(one["fired"], "needs_bus")) == 1
           and _named(one["fired"], "needs_bus")[0].get("outcome") == "ok",
           f"needs_bus={_named(one['fired'], 'needs_bus')}")
        ok(PROVES["32959e65ec5a"]["helper-g"],
           bus.flushes == 2 and one.get("flush") == {"flushed": 1} and two.get("flush") == {"flushed": 2},
           f"flushes={bus.flushes} one={one.get('flush')} two={two.get('flush')}")

        calls: list[int] = []

        def factory():
            calls.append(1)
            return StubBus()

        try:
            lazy = BeatProbes("fixture_device", folder, ["standing"], bus=factory)
            before = len(calls)
            lazy.on_pulse(now, {})
            lazy.on_pulse(now, {})
            ok(PROVES["32959e65ec5a"]["helper-h"], before == 0 and len(calls) == 1,
               f"calls at construction={before}, after two beats={len(calls)}")
        except Exception as e:  # noqa: BLE001
            ok(PROVES["32959e65ec5a"]["helper-h"], False, f"{type(e).__name__}: {e}")
    return _verdict()


def _verdict() -> int:
    print()
    if FAILURES:
        print(f"RED — {len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("GREEN — crossings, while_true, refusal, clearing, missing, bus, flush, lazy bus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
