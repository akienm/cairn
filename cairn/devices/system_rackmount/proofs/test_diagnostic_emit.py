"""Proof for system_rackmount's DIAGNOSTIC EMISSION — the first REAL producer, crawled in situ.

The diagnostic chain had a proven reader (``diagnostic_inspector``) but no live producer:
``BaseDevice`` composes ``DiagnosticBase`` so every device CAN ``emit()``, yet nothing called
it — the method was measured only against test-harness emissions (Law 3: unmeasured in situ).
This proof closes that: ``system_rackmount`` — the device DiagnosticBase was built for
(``base/diagnostic.py``: "what would have spoken when system_rackmount went red silently") —
now emits a thin breadcrumb at a real gate contact (``subscribe`` — a predicate is born), and
the inspector crawls it end to end. Producer → log → inspector → coherent findings, on the
real device, no synthetic emissions.

Deliberately dependency-light: the subscribe→emit→crawl path needs no bus and no Postgres (unlike
the heartbeat capstone in ``test_system_rackmount.py``). Runs bare.

Teeth a hollow instrumentation could not pass:
  - A REAL DEVICE EMITS AT A REAL GATE, AND THE INSPECTOR CRAWLS IT. Wire a Mailbox as the
    device's diagnostic receiver, subscribe, and ``inspect`` by the pointer: the findings carry
    exactly that subscription's ``subscribe`` breadcrumb, sourced to the device. (A device that
    did not emit yields an empty log → empty findings → this fails.)
  - LAW 6 — ISOLATION. A second subscription's breadcrumb does NOT bleed into the first's slice;
    each pointer's transaction is its own.
  - LAW 6 — THIN. The breadcrumb carries no owned reading (``values`` empty): the CPU number the
    device samples never rides the diagnostic surface, only the pointer does.
  - LAW 7 — HELD, NEVER DROPPED. With no receiver wired the breadcrumb HOLDS on the device
    (``held_diagnostics`` — home "held"), not silently lost. Since 2026-08-18 the un-wired
    device WRITES to its own trail instead of holding, and holding is a thing you ask for.

    python3 cairn/devices/system_rackmount/proofs/test_diagnostic_emit.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.machines.diagnostic_inspector import Inspector, Mailbox, by_pointer
from cairn.devices.system_rackmount.rackmount import SystemRackmountDevice


def test_a_real_device_emits_at_the_subscribe_gate_and_the_inspector_crawls_it():
    """Producer → log → inspector, on the real system device, end to end."""
    box = Mailbox()
    dev = SystemRackmountDevice(sampler=lambda: {"cpu": 10})
    dev.set_diagnostic_receiver(box)

    sub_id = dev.subscribe("cpu_threshold", address="ops/personal",
                           why="page me when CPU is high", value=80)

    findings = Inspector().inspect(box.records(), by_pointer(sub_id))
    assert findings["gates"] == ["subscribe"], "the crawl found exactly the subscribe gate contact"
    assert len(findings["steps"]) == 1, "one breadcrumb for one subscription"
    step = findings["steps"][0]
    assert step["pointer"] == sub_id, "the breadcrumb points to the subscription that was born"
    assert step["source"] == "SystemRackmountDevice", "sourced to the emitting device"
    assert step["home"] == "sent", "a receiver was wired — the breadcrumb went home (not held)"


def test_law6_isolation_another_subscription_does_not_bleed_in():
    box = Mailbox()
    dev = SystemRackmountDevice(sampler=lambda: {"cpu": 10})
    dev.set_diagnostic_receiver(box)

    sub_a = dev.subscribe("cpu_threshold", address="a/personal", why="a", value=80)
    sub_b = dev.subscribe("cpu_threshold", address="b/personal", why="b", value=50)

    findings_a = Inspector().inspect(box.records(), by_pointer(sub_a))
    pointers = {s["pointer"] for s in findings_a["steps"]}
    assert pointers == {sub_a}, "only sub_a's transaction is in sub_a's slice — no bleed (Law 6)"
    assert sub_b != sub_a and sub_b not in pointers, "sub_b's breadcrumb stayed out of sub_a's slice"


def test_law6_the_breadcrumb_is_thin_no_owned_reading_leaks():
    box = Mailbox()
    dev = SystemRackmountDevice(sampler=lambda: {"cpu": 95})   # hot host — a reading that MUST NOT leak
    dev.set_diagnostic_receiver(box)

    sub_id = dev.subscribe("cpu_threshold", address="ops/personal", why="w", value=80)

    step = Inspector().inspect(box.records(), by_pointer(sub_id))["steps"][0]
    assert step["values"] == {}, "thin by design — the breadcrumb carries no snapshot (the only place a reading could ride)"
    # Scope the leak-scan to the SEMANTIC content, excluding the microsecond stamp (ts/us): a
    # timestamp contains the substring "95" by pure chance on some runs, so scanning it would be a
    # red decided by a coin toss (Law 8) — the EXACT flake the capstone proof (test_system_rackmount.py)
    # already learned and fixed by excluding transport-assigned fields. A reading would leak into
    # `values` (asserted empty above); this guards source/gate/pointer/home too.
    import json
    authored = {k: v for k, v in step.items() if k not in ("ts", "us")}
    assert "95" not in json.dumps(authored), "the device's private reading never touches the diagnostic surface (Law 6)"


def test_law7_a_silenced_device_holds_and_an_unwired_one_reaches_disk():
    """REWRITTEN 2026-08-18 (ticket a-device-logs-without-being-wired), because the state this
    tooth was built on stopped existing. It read ``dev = SystemRackmountDevice(...)  # NO receiver
    wired`` and asserted the breadcrumb was HELD — true then, and the reason only two trails
    existed in the whole system. Un-wired now WRITES, to this device's own trail in the logs
    tree, so the old assertion would have gone red for the exact reason the ticket was cast.

    What Law 7 actually demanded is untouched and is still pinned below: a record is never
    silently dropped. Holding is now a thing you ASK for (``set_diagnostic_receiver(None)`` — how
    a temporary instrument is torn down) rather than the accident of nobody having assembled the
    device, and both halves are checked here so the sentinel is proved rather than assumed.

    THE ROOTS TABLE IS NOT OPTIONAL IN THIS FILE ANY MORE. This tooth constructs a REAL device,
    which now writes by default — and on the first run after the change it seeded
    ``~/.cairn/logs/system_rackmount/0/diagnostics.jsonl`` in the live tree. Measured, not
    hypothetical: it is the proof-writes-into-the-instrument failure, and the fix is to hand the
    device a temp world, which is what ``set_diagnostic_roots`` exists for."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        roots = {"repo": Path(__file__).resolve().parents[4], "commons": tmp, "instance": tmp}

        silenced = SystemRackmountDevice(sampler=lambda: {"cpu": 10})
        silenced.set_diagnostic_roots(roots)
        silenced.set_diagnostic_receiver(None)          # SILENCED, deliberately
        held_sub = silenced.subscribe("cpu_threshold", address="ops/personal", why="w", value=80)
        held = silenced.held_diagnostics()
        assert len(held) == 1 and held[0]["pointer"] == held_sub, \
            "a silenced device HOLDS the breadcrumb, never drops it (Law 7)"
        assert held[0]["home"] == "held"

        unwired = SystemRackmountDevice(sampler=lambda: {"cpu": 10})
        unwired.set_diagnostic_roots(roots)             # a world, not a receiver
        disk_sub = unwired.subscribe("cpu_threshold", address="ops/personal", why="w", value=85)
        trail_dir = tmp / "logs" / "system_rackmount" / "0"
        assert trail_dir.exists(), \
            f"a real device NOBODY wired must leave its own trail at {trail_dir} — the ticket"
        emission_files = sorted(trail_dir.glob("*.json"))
        assert len(emission_files) == 1, f"one emission, one file; got {len(emission_files)}"
        written = json.loads(emission_files[0].read_text())
        assert written["pointer"] == disk_sub, \
            "and the crossing on disk is the one that happened"
        assert unwired.held_diagnostics() == [], "nothing is held once there is a home"

        box = Mailbox()
        unwired.set_diagnostic_receiver(box)
        sent_sub = unwired.subscribe("cpu_threshold", address="ops/personal", why="w", value=90)
        assert [r["pointer"] for r in box.records()] == [sent_sub], \
            "an override still diverts the next gate contact away from the default trail"


def _main() -> int:
    checks = [
        test_a_real_device_emits_at_the_subscribe_gate_and_the_inspector_crawls_it,
        test_law6_isolation_another_subscription_does_not_bleed_in,
        test_law6_the_breadcrumb_is_thin_no_owned_reading_leaks,
        test_law7_a_silenced_device_holds_and_an_unwired_one_reaches_disk,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — system_rackmount is the diagnostic chain's first REAL producer: it emits a thin "
          "breadcrumb at the subscribe gate (Law 6, held-never-dropped Law 7) and the inspector "
          "crawls it into a coherent, isolated findings slice — the method measured in situ (Law 3)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
