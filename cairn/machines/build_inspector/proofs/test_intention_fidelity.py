#!/usr/bin/env python3
"""Proof that the intention_fidelity sieve reds a charter that no longer translates its tickets.

Ticket 5dbc03e007c5. A charter's falsifier is meant to be a translation of the falsifiers of the
tickets that built the component; nothing measured whether it still is. The sieve pairs the
charter's falsifier with every ticket whose owning_intention names that charter, scores keyword
coverage of the ticket and invented scope of the charter, and reds the component whose best pair
falls past thresholds frozen from the 2026-11-05 census (open-9570fbb8e2af, Akien's approval of
the census proposal).

Teeth, each binding the inspector at call time and each building its own fixture world under the
scratch door (a cairn root and a CairnCommons/tickets beside it):
  (1) intention_fidelity is registered in SIEVES under its own name;
  (2) a charter whose falsifier is rewritten into unrelated words reds, over-hedging AND
      over-claiming, while charter_on_disk reads the same component green (the hollow green);
  (3) a charter whose falsifier equals its ticket's passes.

    bin/cairn test --exec 'python3 cairn/machines/build_inspector/proofs/test_intention_fidelity.py'
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"5dbc03e007c5": {
    "1": "test_the_sieve_is_registered",
    "2": "test_a_rewritten_falsifier_reds",
    "3": "test_a_faithful_falsifier_passes",
}}

TICKET_FALSIFIER = ("RED when the sieve intention_fidelity misses a rewritten charter falsifier; "
                    "GREEN when coverage of ticket keywords holds above the floor")
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _world(charter_falsifier: str) -> tuple[dict, Path]:
    """A scratch cairn root with one component, and one ticket in the commons beside it."""
    from cairn.tools.scratch.scratch import scratch_dir
    w = scratch_dir("testing-5dbc03e007c5-")
    comp = w / "cairn" / "cairn" / "machines" / "fixture_comp"
    comp.mkdir(parents=True)
    (comp / "intention+why.json").write_text(json.dumps(
        {"intention": "fixture", "why": "fixture", "falsifier": charter_falsifier}))
    tickets = w / "CairnCommons" / "tickets"
    tickets.mkdir(parents=True)
    (tickets / "aaaaaaaaaaaa-fixture.json").write_text(json.dumps(
        {"id": "aaaaaaaaaaaa", "title": "fixture",
         "owning_intention": "cairn/machines/fixture_comp/intention+why.json",
         "falsifier": TICKET_FALSIFIER}))
    (tickets / "aaaaaaaaaaaa-fixture.state.json").write_text(json.dumps(
        {"workflow_and_state": "code-seam@v2: [PROVED]"}))
    row = {"component": "fixture_comp", "dir": "machines/fixture_comp", "charter_on_disk": True}
    return row, comp


def test_the_sieve_is_registered() -> None:
    from cairn.machines.build_inspector import inspector
    fn = getattr(inspector, "intention_fidelity", None)
    check("test_the_sieve_is_registered",
          fn is not None and inspector.SIEVES.get("intention_fidelity") is fn,
          f"SIEVES['intention_fidelity'] = {inspector.SIEVES.get('intention_fidelity')!r}")


def test_a_rewritten_falsifier_reds() -> None:
    from cairn.machines.build_inspector import inspector
    row, comp = _world("Bananas ripen yellow quickly overnight")
    found = inspector.intention_fidelity(row, comp)
    reasons = {(f.get("values") or {}).get("reason") for f in found}
    hollow = inspector.charter_on_disk(row, comp)
    check("test_a_rewritten_falsifier_reds",
          {"over-hedging", "over-claiming"} <= reasons
          and all(f.get("method") == "intention_fidelity" for f in found) and hollow == [],
          f"reasons {sorted(r for r in reasons if r)}; charter_on_disk {hollow!r}")


def test_a_faithful_falsifier_passes() -> None:
    from cairn.machines.build_inspector import inspector
    row, comp = _world(TICKET_FALSIFIER)
    found = inspector.intention_fidelity(row, comp)
    check("test_a_faithful_falsifier_passes", found == [], f"{len(found)} finding(s): {found!r}")


TEETH = (test_the_sieve_is_registered, test_a_rewritten_falsifier_reds,
         test_a_faithful_falsifier_passes)


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
