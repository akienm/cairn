"""Proof for the transition-grade diagnostic emission (``cairn/tools/base/diagnostic.py``).

Cairn had OUTCOME-grade evidence (VALIDATIONs say what passed) but no TRANSITION-grade surface —
so when ``system_rackmount`` went red 2/5 *silently*, nothing spoke. This is that surface: the
GATE issues a thin breadcrumb when something crosses, pointing to the ticket and stamped to the
microsecond, sent HOME to CC's shim (the diagnostic mailbox, for now). The intelligence lives in
the interpreter that crawls the mailbox — the emission stays dumb.

Teeth a hollow build could not pass:
  - THE 6th PLACE AFTER THE DECIMAL: the stamp carries the microsecond, zero-padded to 6 digits,
    tied to the ``now`` handed in — so entries never collide and the log index is exact.
  - THE GATE ISSUES A THIN BREADCRUMB POINTING TO THE TICKET: gate + pointer(ticket) carried, and
    ``values`` empty by default — a breadcrumb, not a payload ("don't add to the top of that").
  - IT SENDS HOME TO THE WIRED RECEIVER (CC's shim), landing in the mailbox in arrival order.
  - ENTRIES FOR ONE TICKET SHARE THE POINTER and order by their µs stamp — the tie + the crawl the
    interpreter needs to compile a ticket's slice.
  - UNWIRED EMIT IS HELD, NOT LOST: with no receiver (a torn-down instrument), the record is held
    and retrievable — loud even when home is unreachable (Law 7), never a silent drop.
  - A VALUE SNAPSHOT RIDES ONLY WHEN WATCHING VALUES: the narrow case carries ``values``; the norm
    does not.
  - EVERY DEVICE INHERITS emit STRUCTURALLY: a BaseDevice subclass that declares no diagnostics
    still has ``emit`` (DiagnosticBase in the MRO beside CoreValuesMixin) — Law 2, you can't be a
    device without it.
  - THE BREADCRUMB IS DATA THE INTERPRETER CAN CRAWL: the whole mailbox round-trips through
    json.dumps — no live objects leak, so it can be sorted / sliced / evaporated.

Runnable bare (no DB, no bus, no clock, no framework):
    python3 cairn/tools/base/proofs/test_diagnostic.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.core_values import CoreValuesMixin
from cairn.tools.base.device import BaseDevice
from cairn.tools.base.diagnostic import DiagnosticBase, TroubleRaiseRefused
from cairn.tools.base.shim import BaseShim


class _Device(BaseDevice):
    """A minimal device — it declares nothing about diagnostics, yet inherits ``emit``."""

    def intention(self) -> dict:
        return {"what": "a spec device", "why": "to prove the diagnostic surface"}

    def state(self) -> dict:
        return {"resting": "PROVED"}

    def settings(self) -> dict:
        return {"bind": "localhost"}

_Device.__module__ = "__main__"


class _CCShim(BaseShim):
    """Stands in for CC's own shim (``cc_0``) — the diagnostic mailbox, for now."""

    def __init__(self) -> None:
        super().__init__(bus=None)

    @property
    def device_id(self) -> str:
        return "cc_0"


# A fixed clock so the stamp is provable without a real one (like the heartbeat's `now`).
def _at(microsecond: int):
    return datetime(2026, 7, 22, 17, 0, 0, microsecond, tzinfo=timezone.utc)


def test_the_stamp_is_the_sixth_place_after_the_decimal():
    rec = _Device().emit("db_domain.write", pointer="T-flake", now=_at(12345))
    assert rec["us"] == "012345", "the microsecond is zero-padded to six digits — none lost"
    assert rec["ts"].endswith("+00:00"), "the full ISO stamp is carried too (UTC)"
    assert "000012345" not in rec["us"], "exactly six places, not nanoseconds"


def test_the_gate_issues_a_thin_breadcrumb_pointing_to_the_ticket():
    rec = _Device().emit("bus.deliver", pointer="T-flake", now=_at(1))
    assert rec["gate"] == "bus.deliver", "the gate names itself"
    assert rec["pointer"] == "T-flake", "it POINTS to the ticket — the tie"
    assert rec["values"] == {}, "thin by default — a breadcrumb, not a payload"


def test_it_sends_home_to_the_wired_receiver_in_order():
    dev, home = _Device(), _CCShim()
    dev.set_diagnostic_receiver(home)
    dev.emit("gate.a", pointer="T-1", now=_at(10))
    dev.emit("gate.b", pointer="T-1", now=_at(20))

    box = home.diagnostics()
    assert [r["gate"] for r in box] == ["gate.a", "gate.b"], "landed home in arrival order"
    assert all(r["home"] == "sent" for r in box), "each record says it was sent, not held"


def test_entries_for_one_ticket_share_the_pointer_and_order_by_stamp():
    dev, home = _Device(), _CCShim()
    dev.set_diagnostic_receiver(home)
    dev.emit("system_rackmount.acquire", pointer="T-flake", now=_at(30))
    dev.emit("db_domain.write", pointer="T-flake", now=_at(9))  # earlier µs, emitted later

    box = home.diagnostics()
    assert {r["pointer"] for r in box} == {"T-flake"}, "both tied to the one ticket — sliceable"
    by_stamp = sorted(box, key=lambda r: r["us"])
    assert [r["gate"] for r in by_stamp] == ["db_domain.write", "system_rackmount.acquire"], \
        "the µs stamp orders the crawl regardless of arrival order"


def test_unwired_emit_is_held_not_lost():
    dev = _Device()  # no receiver wired — a torn-down / never-wired instrument
    rec = dev.emit("db_domain.write", pointer="T-flake", now=_at(5))
    assert rec["home"] == "held", "loud about being homeless — not a silent send"
    assert dev.held_diagnostics() == [rec], "held and retrievable — Law 7, never a silent drop"


def test_a_value_snapshot_rides_only_when_watching_values():
    rec = _Device().emit("system_rackmount.threshold", pointer="T-flake",
                         values={"conns": 41, "limit": 40}, now=_at(7))
    assert rec["values"] == {"conns": 41, "limit": 40}, "the watch-values case carries the snapshot"


def test_every_device_inherits_emit_structurally():
    mro = _Device.__mro__
    assert DiagnosticBase in mro and CoreValuesMixin in mro, "both mixins are structurally present"
    # A brand-new device subclass that says nothing about diagnostics still has emit.
    assert callable(getattr(_Device(), "emit", None)), "emit is inherited, not per-device"
    assert _Device.emit is DiagnosticBase.emit, "it is the one canonical emit, not re-implemented"


def test_the_breadcrumb_is_data_the_interpreter_can_crawl():
    dev, home = _Device(), _CCShim()
    dev.set_diagnostic_receiver(home)
    dev.emit("gate.a", pointer="T-1", values={"n": 1}, now=_at(2))
    box = home.diagnostics()
    # If any live object leaked into a record, this raises — the mailbox is pure DATA, so the
    # interpreter can sort / slice / evaporate it (and the 30-day json tier is just this, on disk).
    assert json.loads(json.dumps(box)) == box, "the mailbox round-trips — pure data, crawlable"



# ---------------------------------------------------------------------------
# THE SEND DOORS THAT ARE NOT ``raise`` — clear_trouble and reconcile_troubles.
#
# Both cross the SAME seam as ``raise_trouble``: they emit, and the holder decides. Which
# means the sender's only real power is what it PUTS ON THE RECORD, and these teeth are
# over the one thing a sender can get wrong on its own — sending a resolution nobody can
# read a year later. A refusal here costs one fix; an emission here is a fold in the
# owner's store, and the store is a record of truth (Law 7).
#
# ``_Device`` sits under no rung (``__module__`` is ``"__main__"``), so its emissions HOLD
# in memory and reach no disk — which is what lets these teeth assert "nothing was sent"
# without a temp-root world.

def test_a_clear_WITHOUT_AN_IDENTITY_is_REFUSED_before_anything_is_sent():
    dev = _Device()
    try:
        dev.clear_trouble("   ", by="cc", what_changed="the sieve is green now")
    except TroubleRaiseRefused as exc:
        assert "identity" in str(exc), "the refusal names WHICH field is missing, not just that one is"
    else:
        raise AssertionError("an unnamed all-clear was sent — it cannot be matched to any defect")
    assert dev.held_diagnostics() == [], "the refusal fired BEFORE the emission — nothing crossed"


def test_a_clear_WITHOUT_WHAT_CHANGED_is_REFUSED_because_it_stopped_happening_is_not_a_fix():
    dev = _Device()
    try:
        dev.clear_trouble("inspector-new-finding-alpha", by="cc", what_changed="")
    except TroubleRaiseRefused as exc:
        assert "what_changed" in str(exc), "the refusal names the field"
    else:
        raise AssertionError("a clear landed with no account of the fix — the fault comes back unexplained")
    assert dev.held_diagnostics() == [], "nothing crossed the seam"


def test_a_reconcile_WITHOUT_A_SCOPE_is_REFUSED_because_scopeless_claims_the_whole_store():
    dev = _Device()
    try:
        dev.reconcile_troubles("", ["a"], by="cc", what_changed="the findings moved")
    except TroubleRaiseRefused as exc:
        assert "scope" in str(exc), "the refusal names the field"
    else:
        raise AssertionError("a scopeless reconcile was sent — it would clear troubles it "
                             "has no way to observe, including other reporters'")
    assert dev.held_diagnostics() == [], "nothing crossed the seam"


def test_a_reconcile_WITHOUT_WHAT_CHANGED_is_REFUSED():
    dev = _Device()
    try:
        dev.reconcile_troubles("inspector-new-finding-", [], by="cc", what_changed="  ")
    except TroubleRaiseRefused as exc:
        assert "what_changed" in str(exc), "the refusal names the field"
    else:
        raise AssertionError("a reconcile landed with no resolution sentence — and that "
                             "sentence stands on EVERY ticket it clears, not just one")
    assert dev.held_diagnostics() == [], "nothing crossed the seam"


def test_a_WELL_FORMED_clear_and_reconcile_EMIT_ON_THEIR_OWN_GATES_and_say_they_were_HELD():
    # The other half of the refusals above: the doors are strict, not shut. Each rides its own
    # gate name, because the drain scans one lane per gate and keeps a watermark per lane.
    dev = _Device()
    cleared = dev.clear_trouble("inspector-new-finding-alpha", by="cc",
                                what_changed="the sieve no longer reports it", now=_at(1))
    recon = dev.reconcile_troubles("inspector-new-finding-", ["inspector-new-finding-beta"],
                                   by="cc", what_changed="reconciled against the current findings",
                                   now=_at(2))
    assert cleared["gate"] == "clear_trouble" and recon["gate"] == "reconcile_troubles", \
        "each door emits on its OWN gate — a shared gate would share a watermark"
    assert cleared["pointer"] == "inspector-new-finding-alpha", "the clear points at what it clears"
    assert recon["pointer"] == "inspector-new-finding-", "the reconcile points at its SCOPE"
    assert recon["values"]["still"] == ["inspector-new-finding-beta"], \
        "the complete current picture rides the record — the holder clears the rest"
    assert cleared["home"] == "held" and recon["home"] == "held", \
        "unwired, both are HELD and loud — never silently dropped (Law 7)"
    assert cleared["poke"].startswith("held for the beat"), \
        "with no notifier wired the record SAYS so, rather than claiming it was sent"


def test_EVERY_TEST_IN_THIS_FILE_IS_IN_THE_ROSTER():
    # THE TOOTH OVER THE ROSTER ITSELF. This file's checks are a hand-written tuple, and a
    # hand-written roster has exactly one failure mode: a tooth is added, the file prints
    # "N/N green", and the new tooth never ran. It has happened in this corpus before. So the
    # roster is now a module-level name, and this compares it against the module.
    defined = {name for name in globals() if name.startswith("test_")}
    listed = {c.__name__ for c in _CHECKS}
    missing = sorted(defined - listed)
    assert not missing, (f"defined but NEVER RUN — add to _CHECKS: {missing}. A green from a "
                         f"roster that skipped them is a false green, worse than a red (Law 8)")
    assert listed <= defined, f"the roster names checks this module does not define: {sorted(listed - defined)}"


_CHECKS = (
    test_the_stamp_is_the_sixth_place_after_the_decimal,
    test_the_gate_issues_a_thin_breadcrumb_pointing_to_the_ticket,
    test_it_sends_home_to_the_wired_receiver_in_order,
    test_entries_for_one_ticket_share_the_pointer_and_order_by_stamp,
    test_unwired_emit_is_held_not_lost,
    test_a_value_snapshot_rides_only_when_watching_values,
    test_every_device_inherits_emit_structurally,
    test_the_breadcrumb_is_data_the_interpreter_can_crawl,
    test_a_clear_WITHOUT_AN_IDENTITY_is_REFUSED_before_anything_is_sent,
    test_a_clear_WITHOUT_WHAT_CHANGED_is_REFUSED_because_it_stopped_happening_is_not_a_fix,
    test_a_reconcile_WITHOUT_A_SCOPE_is_REFUSED_because_scopeless_claims_the_whole_store,
    test_a_reconcile_WITHOUT_WHAT_CHANGED_is_REFUSED,
    test_a_WELL_FORMED_clear_and_reconcile_EMIT_ON_THEIR_OWN_GATES_and_say_they_were_HELD,
    test_EVERY_TEST_IN_THIS_FILE_IS_IN_THE_ROSTER,
)


def _main() -> int:
    for check in _CHECKS:
        check()
        print(f"  PASS  {check.__name__}")
    print(f"green ({len(_CHECKS)}) — the gate issues a thin breadcrumb (pointer to the ticket, "
          "µs-stamped), sends it home to CC's mailbox, holds it loud when homeless, and the whole "
          "mailbox is DATA the interpreter crawls — every device inherits emit structurally "
          "(Law 2). The clear and reconcile doors cross the same seam and refuse a resolution "
          "nobody could read a year later.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
