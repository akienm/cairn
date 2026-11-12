#!/usr/bin/env python3
"""Proof that bus_client's harbor_source asks harbor_master over the bus (RULE 1, ticket a433ced0b6e8).

The build inspector's encapsulation_holds filed, 2026-11-11, bus_client.py:93 importing
cairn.devices.cairn.machines.harbor_master.voyage. harbor_master answers get traffic since
cd36b8e86cd3; harbor_source now asks it.

NOT BLIND BY ITS OWN PLANT (ticket bfa522282b17). The first guard asked for at least one breach
anywhere else in the live tree, and the tree went clean: measured 2026-11-12, the tooth red with
"0 breach(es) in all". Now the sieve is first run over a scratch tree holding one planted
bus_client file that imports harbor_master, and must name exactly that file, line and target.
7806309a8018's planted tooth is the pattern. The plant carries harbor_master's charter file:
measured 2026-11-12, without one the sieve names the row's target 'cairn/devices/cairn' (the
deepest component it can see), which TARGETS would filter out, and the tooth would read blind.

Teeth:
  (0) the sieve, run over a planted fixture tree, names the planted file, line 1 and target
      cairn/devices/cairn/machines/harbor_master, and nothing else;
  (1) no RULE 1 breach from a file under cairn/tools/bus_client lands on cairn/devices/cairn/machines/harbor_master;
  (2) the edited files name none of the forbidden modules.

    bin/cairn test cairn/tools/bus_client/proofs/test_the_harbor_source_asks_over_the_bus.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"a433ced0b6e8": {"1": "test_no_breach_from_bus_client_lands_on_harbor_master", "2": "test_bus_client_names_no_harbor_master_module",
                           "3": "test_the_source_asks_get_traffic_and_raises_a_refusal",
                           "4": "test_the_live_source_answers_a_traffic_image"},
          "bfa522282b17": {"1": "test_the_sieve_names_a_planted_harbor_breach",
                           "2": "test_no_breach_from_bus_client_lands_on_harbor_master"}}

COMP = "cairn/tools/bus_client"
TARGETS = ('cairn/devices/cairn/machines/harbor_master',)
FORBID = {'cairn/tools/bus_client/bus_client.py': ['cairn.devices.cairn.machines.harbor_master']}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_the_sieve_names_a_planted_harbor_breach() -> None:
    """Not blind: over a scratch tree with one planted breach, the sieve names exactly it."""
    from cairn.machines.build_inspector import inspector
    from cairn.tools.scratch.scratch import scratch_dir
    root = Path(scratch_dir("testing-bfa522282b17-planted-breach-"))
    for d in ("cairn", "cairn/devices", "cairn/tools", COMP,
              "cairn/devices/cairn", "cairn/devices/cairn/machines", TARGETS[0]):
        (root / d).mkdir(parents=True, exist_ok=True)
        (root / d / "__init__.py").touch()
    (root / TARGETS[0] / "intention+why.json").write_text("{}\n", encoding="utf-8")
    (root / COMP / "planted.py").write_text(
        "from cairn.devices.cairn.machines.harbor_master import x\n", encoding="utf-8")
    found = [(b["file"], b["line"], b["target"])
             for b in inspector.encapsulation_breaches(str(root))
             if str(b.get("file", "")).startswith(COMP + "/")
             and str(b.get("target", "")).startswith(TARGETS)]
    want = [(COMP + "/planted.py", 1, TARGETS[0])]
    check("test_the_sieve_names_a_planted_harbor_breach", found == want, f"found {found!r}")


def test_no_breach_from_bus_client_lands_on_harbor_master() -> None:
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        breaches = inspector.encapsulation_breaches(".")
    finally:
        os.chdir(here)
    mine = [b for b in breaches if str(b.get("file", "")).startswith(COMP + "/")
            and str(b.get("target", "")).startswith(TARGETS)]
    # Not blind is test_the_sieve_names_a_planted_harbor_breach's job (ticket bfa522282b17): a
    # clean live tree is the goal, so this tooth no longer needs a breach elsewhere to pass.
    check("test_no_breach_from_bus_client_lands_on_harbor_master", not mine,
          f"{len(breaches)} breach(es) in all; these: "
          + "; ".join(f"{b['file']}:{b['line']} imports {b['module']}" for b in mine))


def test_bus_client_names_no_harbor_master_module() -> None:
    named = {}
    for f, bad in FORBID.items():
        text = (_REPO / f).read_text(encoding="utf-8")
        hits = sorted({m for m in re.findall(r"cairn\.devices(?:\.[A-Za-z_0-9]+)+", text)
                       if m.startswith(tuple(bad))})
        if hits:
            named[f] = hits
    check("test_bus_client_names_no_harbor_master_module", not named, "; ".join(f"{f}: {h}" for f, h in named.items()))


def test_the_source_asks_get_traffic_and_raises_a_refusal() -> None:
    from cairn.tools.bus_client import harbor_source
    image = {"gates": [], "at_anchor": [], "berthed": [], "counts": {"fleet": 0}}
    asked: list[dict] = []

    def ask(**kw):
        asked.append(kw)
        return {"body": {"accepted": True, "verb": "get", "view": "traffic", "data": image}}

    got = harbor_source(ask=ask)()
    sent = asked[0] if asked else {}
    ok_ask = (got == image and len(asked) == 1 and sent.get("to") == "harbor_master"
              and sent.get("verb") == "get" and (sent.get("body") or {}).get("what") == "traffic")

    def refuse(**kw):
        return {"body": {"accepted": False, "reason": "no view 'traffic'"}}

    try:
        harbor_source(ask=refuse)()
        raised = ""
    except RuntimeError as exc:
        raised = str(exc)
    check("test_the_source_asks_get_traffic_and_raises_a_refusal",
          ok_ask and "no view 'traffic'" in raised,
          f"asked {asked}; got {got!r}; refusal raised {raised!r}")


def test_the_live_source_answers_a_traffic_image() -> None:
    from cairn.tools.bus_client import harbor_source
    img = harbor_source()()
    check("test_the_live_source_answers_a_traffic_image",
          isinstance(img, dict) and {"gates", "at_anchor", "berthed", "counts"} <= set(img)
          and img["counts"].get("fleet", 0) > 0,
          f"keys {sorted(img) if isinstance(img, dict) else type(img).__name__}")


TEETH = (test_the_sieve_names_a_planted_harbor_breach, test_no_breach_from_bus_client_lands_on_harbor_master, test_bus_client_names_no_harbor_master_module,
         test_the_source_asks_get_traffic_and_raises_a_refusal, test_the_live_source_answers_a_traffic_image)


def main() -> int:
    for tooth in TEETH:
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
