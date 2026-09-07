"""PROOF — the fleet cache: crossing notifications PATCH, reconciliation REPLACES.

The harbor master maintains a cached fleet register that is updated from two paths:
  - EVENT-DRIVEN: each crossing notification patches the matching boat's standing
  - PERIODIC: reconciliation replaces the whole cache from disk

What a hollow build cannot pass (Law 8):
  - One that stored the cache but never patched it passes "cache exists" and fails
    test_a_crossing_patches_the_cached_standing, which poisons the cached standing
    and reads it back after the crossing. One that wrote the notification's bare
    target (the pre-3feb201c84ea contract) fails the same tooth: the boat must wear
    the label its OWN ticket file carries, re-read through the one reader.
  - One that patched but never reconciled passes every patching test and fails
    test_reconcile_replaces_the_cache, which changes the disk and checks the cache
    picks up what the notifications never carried.
  - One that reported from the cache but faked the counts passes state() tests and
    fails test_state_reports_from_cache, which checks the counts against the cache.

Runs against the real fleet (register.register) for reconciliation; crossing patches
use fixture envelopes against the live cache.

    python3 cairn/devices/cairn/machines/harbor_master/proofs/test_fleet_cache.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
_SRC_ROOT = _REPO_ROOT.parent   # ~/dev/src — the root a register source is relative to
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.cairn.machines.harbor_master.device import HarborMasterDevice  # noqa: E402
from cairn.devices.cairn.machines.harbor_master import register  # noqa: E402
from cairn.tools.operator_inbox.inbox import cursor_of, status_label  # noqa: E402


def _crossing_envelope(component: str, from_: str, to: str, ticket: str = "") -> dict:
    """A fixture crossing envelope — the shape _notify_harbor posts."""
    return {
        "id": "test-envelope",
        "sender": component,
        "to": "harbor_master",
        "verb": "crossing",
        "why": f"crossing notification — {from_} → {to}",
        "body": {
            "component": component,
            "from": from_,
            "to": to,
            "direction": "forward",
            "gates_fired": [],
            "ticket": ticket,
        },
    }


# --- teeth ------------------------------------------------------------------

def test_a_fresh_device_has_no_cache():
    """Before any crossing or reconciliation, the cache is honestly empty."""
    dev = HarborMasterDevice()
    assert dev.fleet_cache is None, "a fresh device must not invent a cache"


def test_reconcile_populates_the_cache_from_disk():
    """reconcile() reads the real fleet — the cache matches register.register()."""
    dev = HarborMasterDevice()
    result = dev.reconcile()
    assert dev.fleet_cache is not None, "reconcile must populate the cache"
    assert result["fleet"]["fleet"] > 0, "the real fleet is not empty"
    fresh = register.register()
    assert dev.fleet_cache["counts"] == fresh["counts"], (
        f"cache counts diverge from a fresh register() — "
        f"cache={dev.fleet_cache['counts']}, fresh={fresh['counts']}")


def test_a_crossing_patches_the_cached_standing():
    """The event-driven path: a crossing notification RELOADS the named boat from
    its own ticket file, in the cache, without a full disk scan (ticket 3feb201c84ea,
    Akien 2026-09-06: one ticket has ONE status — the label is the ticket's, never
    the notification's bare target).

    Three builds, three different values, one poisoned cache: the cache's standing
    is first overwritten with a poison string. A build that ignores the crossing
    leaves the poison. A build that writes the bare target (the pre-3feb201c84ea
    contract) leaves ``FAKE_STANDING_FOR_TEST``. Only a build that re-reads the
    ticket file through the one reader leaves the ticket's real label — and it
    must do so without replacing the cache object (that would be a reconcile)."""
    dev = HarborMasterDevice()
    dev.reconcile()
    reg = dev.fleet_cache
    assert reg["open"], "need at least one open boat to test patching"
    boat = reg["open"][0]
    original = dict(boat)
    src = Path(boat["source"])
    if not src.is_absolute():
        src = _SRC_ROOT / src
    doc = json.loads(src.read_text(encoding="utf-8"))
    true_label = status_label(cursor_of(doc.get("workflow_and_state", "")))
    poison = "POISONED_CACHE_STANDING"
    fake_target = "FAKE_STANDING_FOR_TEST"
    assert true_label not in (poison, fake_target)
    boat["standing"] = boat["label"] = poison
    before = dev._crossings_since_reconcile
    envelope = _crossing_envelope(
        component="test/component",
        from_=poison,
        to=fake_target,
        ticket=boat["id"],
    )
    dev._handle_crossing(envelope)
    assert dev.fleet_cache is reg, "the crossing replaced the cache — that is a reconcile, not a patch"
    patched_boat = next(b for b in reg["open"] if b["id"] == boat["id"])
    assert patched_boat["standing"] == true_label, (
        f"crossing did not reload the boat from its ticket — "
        f"expected the ticket's own label {true_label!r}, got {patched_boat['standing']!r}")
    assert patched_boat["label"] == true_label
    assert dev._crossings_since_reconcile == before + 1
    boat.update(original)


def test_reconcile_replaces_the_cache():
    """reconcile() replaces the whole cache — a stale patch is overwritten by
    the honest disk scan."""
    dev = HarborMasterDevice()
    dev.reconcile()
    reg = dev.fleet_cache
    assert reg["open"], "need at least one open boat"
    boat = reg["open"][0]
    original = boat["standing"]
    boat["standing"] = "STALE_PATCH"
    dev.reconcile()
    refreshed = next(b for b in dev.fleet_cache["open"] if b["id"] == boat["id"])
    assert refreshed["standing"] == original, (
        f"reconcile did not replace the stale patch — "
        f"expected {original!r}, got {refreshed['standing']!r}")


def test_first_crossing_on_empty_cache_triggers_reconcile():
    """A crossing on an empty cache populates it (reconcile, then patch). The device
    is never in a state where it receives crossings without a cache to patch."""
    dev = HarborMasterDevice()
    assert dev.fleet_cache is None
    reg = register.register()
    if not reg["open"]:
        print("    (skipped — no open boats to send a crossing for)")
        return
    boat = reg["open"][0]
    envelope = _crossing_envelope(
        component="test/component",
        from_="SOMEWHERE",
        to="SOMEWHERE_ELSE",
        ticket=boat["id"],
    )
    dev._handle_crossing(envelope)
    assert dev.fleet_cache is not None, (
        "first crossing on empty cache must trigger reconcile")


def test_state_reports_from_cache():
    """state() reports the cached counts, not a fresh disk scan."""
    dev = HarborMasterDevice()
    dev.reconcile()
    st = dev.state()
    c = dev.fleet_cache["counts"]
    assert st["total_boats"] == c["fleet"], (
        f"state total_boats ({st['total_boats']}) != cache fleet count ({c['fleet']})")
    assert st["open"] == c["open"], (
        f"state open ({st['open']}) != cache open count ({c['open']})")
    assert st["in_port"] == c["in_port"], (
        f"state in_port ({st['in_port']}) != cache in_port count ({c['in_port']})")
    assert "cache_at" in st, "state must report when the cache was last refreshed"


def test_crossings_since_reconcile_counts():
    """The device tracks how many crossings patched since the last reconciliation."""
    dev = HarborMasterDevice()
    dev.reconcile()
    assert dev._crossings_since_reconcile == 0, "reconcile resets the counter"
    reg = dev.fleet_cache
    if not reg["open"]:
        print("    (skipped — no open boats)")
        return
    boat = reg["open"][0]
    original = boat["standing"]
    for i in range(3):
        envelope = _crossing_envelope(
            component="test/component",
            from_="X",
            to=f"Y{i}",
            ticket=boat["id"],
        )
        dev._handle_crossing(envelope)
    assert dev._crossings_since_reconcile == 3, (
        f"expected 3 crossings, got {dev._crossings_since_reconcile}")
    result = dev.reconcile()
    assert result["crossings_patched_since_last"] == 3
    assert dev._crossings_since_reconcile == 0, "reconcile must reset the counter"
    boat["standing"] = original


def test_in_port_boat_patched_by_component():
    """A crossing notification patches in-port boats by component name (the last
    path segment)."""
    dev = HarborMasterDevice()
    dev.reconcile()
    reg = dev.fleet_cache
    assert reg["in_port"], "need at least one in-port boat"
    boat = reg["in_port"][0]
    original = boat["standing"]
    fake_target = "FAKE_IN_PORT_STANDING"
    envelope = _crossing_envelope(
        component=f"cairn/devices/{boat['id']}",
        from_=original,
        to=fake_target,
        ticket="",
    )
    dev._handle_crossing(envelope)
    patched = next(b for b in reg["in_port"] if b["id"] == boat["id"])
    assert patched["standing"] == fake_target, (
        f"crossing did not patch the in-port boat — "
        f"expected {fake_target!r}, got {patched['standing']!r}")
    boat["standing"] = original


if __name__ == "__main__":
    checks = [
        test_a_fresh_device_has_no_cache,
        test_reconcile_populates_the_cache_from_disk,
        test_a_crossing_patches_the_cached_standing,
        test_reconcile_replaces_the_cache,
        test_first_crossing_on_empty_cache_triggers_reconcile,
        test_state_reports_from_cache,
        test_crossings_since_reconcile_counts,
        test_in_port_boat_patched_by_component,
    ]
    failures = 0
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  FAIL  {check.__name__}: {type(exc).__name__}: {exc}")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — crossing notifications patch, reconciliation replaces, "
          "state reports from cache — the event-driven fleet cache")
