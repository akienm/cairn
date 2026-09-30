"""OPERATOR INBOX FIRES ITS OWN CLOCK PROBES ON ITS OWN PULSE — ticket 98e70e3c1677.

Since bae622881f03 (2026-09-30) the heartbeat no longer discovers probes/ folders; it calls
groundloop/pulse.py and nothing else. operator_inbox_matches_live_state and an_open_idea_that_went_stale are operator_inbox's clock
probes (Akien's group-2 list), so operator_inbox's pulse fires them, composing the shared firer
cairn/tools/base/beat_probes.py (32959e65ec5a), and fires nothing else:

  (1) the heartbeat's own discovery lists cairn/tools/operator_inbox/groundloop/pulse.py at class level;
  (2) the pulse's firer names exactly ['operator_inbox_matches_live_state', 'an_open_idea_that_went_stale'], and each resolves to a Probe;
  (3) the other modules in cairn/tools/operator_inbox/probes/ are not in its roster;
  (4) one pulse with a recording stub bus returns a record whose fired+held cover exactly those.

The pulse module is loaded by path inside the teeth, never imported at module level, so a
build with the pulse taken away reds these teeth instead of crashing the runner. Tooth (4)
binds a stub bus first, so no real bus is built by this proof.
"""
from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"98e70e3c1677": {
    "1": "the heartbeat's discovery lists operator_inbox's pulse at class level",
    "2": "the pulse names exactly operator_inbox's clock probes and each resolves to a Probe",
    "3": "no other probe in operator_inbox's probes folder is in the roster",
    "4": "one pulse covers exactly operator_inbox's clock probes in fired and held",
}}
DEVICE = _REPO / "cairn/tools/operator_inbox"
PULSE = DEVICE / "groundloop" / "pulse.py"
EXPECTED = ['operator_inbox_matches_live_state', 'an_open_idea_that_went_stale']
FAILURES: list[str] = []


def ok(name: str, passed: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if passed else 'RED '} {name}")
    if detail:
        print(f"         -> {detail}")
    if not passed:
        FAILURES.append(f"{name}: {detail}")


class StubBus:
    def __init__(self) -> None:
        self.posts: list[dict] = []

    def post(self, **kw) -> dict:
        self.posts.append(kw)
        return {"id": f"env-{len(self.posts)}"}

    def request(self, **kw) -> dict:
        raise TimeoutError("the stub bus answers nothing — the proof never asks a live lane")

    def flush(self) -> dict:
        return {"flushed": len(self.posts)}


def _load():
    spec = importlib.util.spec_from_file_location("cairn._proof.operator_inbox_groundloop_pulse", PULSE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _probe_whys() -> dict:
    """Each named probe's why, read from its own module, so the record can be matched by it."""
    out = {}
    for name in EXPECTED:
        spec = importlib.util.spec_from_file_location(f"cairn._proof.operator_inbox_probe_{name}",
                                                      DEVICE / "probes" / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out[name] = mod.PROBE.why
    return out


def main() -> int:
    print("operator_inbox fires its own clock probes on its own pulse")
    T = PROVES["98e70e3c1677"]
    try:
        from cairn.devices.cairn.machines.ground_loop.discovery import pulse_sites
        sites = [s for s in pulse_sites() if Path(s["path"]) == PULSE]
        ok(T["1"], len(sites) == 1 and sites[0]["level"] == "class"
           and sites[0]["device_id"] == "operator_inbox", f"sites={sites}")
    except Exception as e:  # noqa: BLE001
        ok(T["1"], False, f"{type(e).__name__}: {e}")

    try:
        mod = _load()
        firer = mod.FIRER
    except Exception as e:  # noqa: BLE001
        for k in ("2", "3", "4"):
            ok(T[k], False, f"{type(e).__name__}: {e}")
        return _verdict()

    from cairn.tools.base.probe import Probe
    roster = list(firer.roster())
    loaded = firer.probes()
    ok(T["2"], roster == EXPECTED and len(loaded) == len(EXPECTED)
       and all(isinstance(p, Probe) for p in loaded),
       f"roster={roster} loaded={len(loaded)}")
    others = sorted(p.stem for p in (DEVICE / "probes").glob("*.py")
                    if p.stem != "__init__" and p.stem not in EXPECTED)
    ok(T["3"], not set(others) & set(roster), f"others={others} roster={roster}")

    bus = StubBus()
    firer.bind(bus)
    record = mod.on_pulse(datetime.now(timezone.utc), {})
    whys = _probe_whys()
    covered = [e.get("why") for e in record.get("fired", []) + record.get("held", [])]
    ok(T["4"], sorted(covered) == sorted(whys.values()),
       f"covered {len(covered)} entries; missing={[n for n, w in whys.items() if w not in covered]}")
    return _verdict()


def _verdict() -> int:
    print()
    if FAILURES:
        print(f"RED — {len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("GREEN — operator_inbox's pulse fires operator_inbox_matches_live_state and an_open_idea_that_went_stale, and nothing else.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
