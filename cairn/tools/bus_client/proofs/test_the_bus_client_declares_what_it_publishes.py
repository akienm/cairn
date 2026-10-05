"""Proof for ticket 80434313b6de — the bus client declares the modules it publishes.

RULE 1 (Akien, 2026-10-01): a component is reached only through its DECLARED public interface.
roster.py (efb670ff1dd8's build 4313a42d) and remote.py (48519f4789b1's build 1a141757) were born
on 2026-10-02 to be imported by the CLI, the web server and every shim — a day after
56d1aff4455e's first declarations — and neither build declared them. Measured before this
ticket: 24 encapsulation_breaches rows 'undeclared' on cairn/tools/bus_client (18 roster, 6
remote).

One tooth per numbered falsifier clause, over the LIVE repo (invariants, never snapshots):

  1. THE CHARTER DECLARES BOTH. public_interface contains cairn.tools.bus_client.remote and
     cairn.tools.bus_client.roster.
  2. NOTHING REACHES BUS_CLIENT UNDECLARED. No encapsulation_breaches row has target
     cairn/tools/bus_client and reason 'undeclared'.

    python3 cairn/tools/bus_client/proofs/test_the_bus_client_declares_what_it_publishes.py   # exit 0 = green
"""
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


class _Late:
    """The inspector resolves AT CALL TIME, so `cairn test --hollow` reads as red teeth
    rather than an import that never ran."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._module), name)


_inspector = _Late("cairn.machines.build_inspector.inspector")

PROVES = {"80434313b6de": {"1": "the_charter_declares_both",
                           "2": "nothing_reaches_bus_client_undeclared"}}

TOOL_DIR = _REPO_ROOT / "cairn" / "tools" / "bus_client"
PUBLISHED = ("cairn.tools.bus_client.remote", "cairn.tools.bus_client.roster")

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  ok    {name}")


def the_charter_declares_both():
    charter = json.loads((TOOL_DIR / ("intention+" + "why.json")).read_text(encoding="utf-8"))
    declared = charter.get("public_interface") or []
    missing = [m for m in PUBLISHED if m not in declared]
    assert not missing, f"public_interface does not declare {missing}: {declared}"


def nothing_reaches_bus_client_undeclared():
    rows = [r for r in _inspector.encapsulation_breaches(str(_REPO_ROOT))
            if r["target"] == "cairn/tools/bus_client" and r["reason"] == "undeclared"]
    assert not rows, f"{len(rows)} undeclared reach(es) into bus_client: " \
        f"{sorted({r['module'] for r in rows})} from {sorted({r['file'] for r in rows})[:6]}"


TEETH = [the_charter_declares_both, nothing_reaches_bus_client_undeclared]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
