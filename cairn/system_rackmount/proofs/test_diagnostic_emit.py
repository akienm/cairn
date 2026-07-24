"""Proof for system_rackmount's DIAGNOSTIC EMISSION — the first REAL producer, crawled in situ.

The diagnostic chain had a proven reader (``diagnostic_interpreter``) but no live producer:
``BaseDevice`` composes ``DiagnosticBase`` so every device CAN ``emit()``, yet nothing called
it — the method was measured only against test-harness emissions (Law 3: unmeasured in situ).
This proof closes that: ``system_rackmount`` — the device DiagnosticBase was built for
(``base/diagnostic.py``: "what would have spoken when system_rackmount went red silently") —
now emits a thin breadcrumb at a real gate contact (``subscribe`` — a predicate is born), and
the interpreter crawls it end to end. Producer → mailbox → interpreter → coherent slice, on the
real device, no synthetic emissions.

Deliberately dependency-light: the subscribe→emit→crawl path needs no bus and no Postgres (unlike
the heartbeat capstone in ``test_system_rackmount.py``). Runs bare.

Teeth a hollow instrumentation could not pass:
  - A REAL DEVICE EMITS AT A REAL GATE, AND THE INTERPRETER CRAWLS IT. Wire a Mailbox as the
    device's diagnostic receiver, subscribe, and ``assemble`` the pointer: the slice carries
    exactly that subscription's ``subscribe`` breadcrumb, sourced to the device. (A device that
    did not emit yields an empty mailbox → an empty slice → this fails.)
  - LAW 6 — ISOLATION. A second subscription's breadcrumb does NOT bleed into the first's slice;
    each pointer's transaction is its own.
  - LAW 6 — THIN. The breadcrumb carries no owned reading (``values`` empty): the CPU number the
    device samples never rides the diagnostic surface, only the pointer does.
  - LAW 7 — HELD, NEVER DROPPED. With no receiver wired the breadcrumb HOLDS on the device
    (``held_diagnostics`` — home "held"), not silently lost; once a receiver is wired it sends.

    python3 cairn/system_rackmount/proofs/test_diagnostic_emit.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.diagnostic_interpreter import Mailbox, assemble
from cairn.system_rackmount.rackmount import SystemRackmountDevice


def test_a_real_device_emits_at_the_subscribe_gate_and_the_interpreter_crawls_it():
    """Producer → mailbox → interpreter, on the real system device, end to end."""
    box = Mailbox()
    dev = SystemRackmountDevice(sampler=lambda: {"cpu": 10})
    dev.set_diagnostic_receiver(box)

    sub_id = dev.subscribe("cpu_threshold", address="ops/personal",
                           why="page me when CPU is high", value=80)

    report = assemble(box.records(), sub_id)
    assert report["gates"] == ["subscribe"], "the crawl found exactly the subscribe gate contact"
    assert len(report["steps"]) == 1, "one breadcrumb for one subscription"
    step = report["steps"][0]
    assert step["pointer"] == sub_id, "the breadcrumb points to the subscription that was born"
    assert step["source"] == "SystemRackmountDevice", "sourced to the emitting device"
    assert step["home"] == "sent", "a receiver was wired — the breadcrumb went home (not held)"


def test_law6_isolation_another_subscription_does_not_bleed_in():
    box = Mailbox()
    dev = SystemRackmountDevice(sampler=lambda: {"cpu": 10})
    dev.set_diagnostic_receiver(box)

    sub_a = dev.subscribe("cpu_threshold", address="a/personal", why="a", value=80)
    sub_b = dev.subscribe("cpu_threshold", address="b/personal", why="b", value=50)

    report_a = assemble(box.records(), sub_a)
    pointers = {s["pointer"] for s in report_a["steps"]}
    assert pointers == {sub_a}, "only sub_a's transaction is in sub_a's slice — no bleed (Law 6)"
    assert sub_b != sub_a and sub_b not in pointers, "sub_b's breadcrumb stayed out of sub_a's slice"


def test_law6_the_breadcrumb_is_thin_no_owned_reading_leaks():
    box = Mailbox()
    dev = SystemRackmountDevice(sampler=lambda: {"cpu": 95})   # hot host — a reading that MUST NOT leak
    dev.set_diagnostic_receiver(box)

    sub_id = dev.subscribe("cpu_threshold", address="ops/personal", why="w", value=80)

    step = assemble(box.records(), sub_id)["steps"][0]
    assert step["values"] == {}, "thin by design — the breadcrumb carries no snapshot (the only place a reading could ride)"
    # Scope the leak-scan to the SEMANTIC content, excluding the microsecond stamp (ts/us): a
    # timestamp contains the substring "95" by pure chance on some runs, so scanning it would be a
    # red decided by a coin toss (Law 8) — the EXACT flake the capstone proof (test_system_rackmount.py)
    # already learned and fixed by excluding transport-assigned fields. A reading would leak into
    # `values` (asserted empty above); this guards source/gate/pointer/home too.
    import json
    authored = {k: v for k, v in step.items() if k not in ("ts", "us")}
    assert "95" not in json.dumps(authored), "the device's private reading never touches the diagnostic surface (Law 6)"


def test_law7_held_never_dropped_when_no_receiver_then_sends_once_wired():
    dev = SystemRackmountDevice(sampler=lambda: {"cpu": 10})   # NO receiver wired

    held_sub = dev.subscribe("cpu_threshold", address="ops/personal", why="w", value=80)
    held = dev.held_diagnostics()
    assert len(held) == 1 and held[0]["pointer"] == held_sub, "no home wired → the breadcrumb HELD, not lost (Law 7)"
    assert held[0]["home"] == "held"

    box = Mailbox()
    dev.set_diagnostic_receiver(box)
    sent_sub = dev.subscribe("cpu_threshold", address="ops/personal", why="w", value=90)
    assert [r["pointer"] for r in box.records()] == [sent_sub], "once wired, the next gate contact sends home"


def _main() -> int:
    checks = [
        test_a_real_device_emits_at_the_subscribe_gate_and_the_interpreter_crawls_it,
        test_law6_isolation_another_subscription_does_not_bleed_in,
        test_law6_the_breadcrumb_is_thin_no_owned_reading_leaks,
        test_law7_held_never_dropped_when_no_receiver_then_sends_once_wired,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — system_rackmount is the diagnostic chain's first REAL producer: it emits a thin "
          "breadcrumb at the subscribe gate (Law 6, held-never-dropped Law 7) and the interpreter "
          "crawls it into a coherent, isolated slice — the method measured in situ (Law 3)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
