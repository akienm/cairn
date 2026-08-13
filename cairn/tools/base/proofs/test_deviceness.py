"""Proof for DEVICE-NESS — the ruled predicate, and the probe that makes its divergence loud.

Ticket ``device-ness-is-decided-at-the-shim``. Akien ruled the axis on 2026-08-11: a shim
fits TO the device, and the unit is the FOLDER — a device is a directory with a ``probes/``
subdirectory, its id the directory's own name. This proof holds the pieces to that ruling.

Teeth a hollow build could not pass:

  - THE CALIBRE TOOTH, ON A FIXTURE THIS FILE BUILDS. A directory with a ``probes/`` folder,
    no Python device object, no class, no import of anything in ``cairn`` — the external,
    inheriting-nothing member the old axis could not represent — is a device. This is the
    ticket's falsifier stated as a test rather than as a sentence, and it is run against a
    tree made for it so the pass cannot be an accident of the live corpus.
  - AND THE INVERSE, WHICH IS WHERE A HOLLOW BUILD WOULD PASS: a component that subclasses
    ``BaseDevice`` and has no ``probes/`` folder is NOT a device. A predicate that quietly
    ORed the two axes together would satisfy every other tooth here and fail this one.
  - IT COMPOSES, IT DOES NOT RE-DERIVE. ``fitted_device_ids`` is checked to agree exactly
    with ``ground_loop.discovery.device_folders`` on an arbitrary fixture tree — so a second,
    drifting roster cannot be introduced behind the predicate's back.
  - INVARIANTS, NOT SNAPSHOTS, over live data. The live-corpus teeth assert relationships
    (every discovered id answers true; the ruled set equals discovery's set; the axes are
    named per component) and never a frozen count. A proof that pinned "19" would go red the
    day the divergence improved — the failure shape where a check reds at the moment its
    condition is satisfied.
  - THE HALF-BUILT CLAUSE IS DECLARED, NOT OMITTED. ``HEALTH_QUERY_CLAUSE`` must exist, must
    say UNBUILT, and must ride in the probe's payload — because a predicate that silently
    implements half its own definition is the shape a reader mistakes for whole.
  - THE PROBE FIRES ON ARMING AND NAMES NAMES. Its trigger is TRUE now, it is a CROSSING on
    a virgin shim (``_was_true`` starts empty) so it actually pokes, and its payload carries
    per-component LISTS rather than a count — a count is what lets a divergence sit still.
  - THE ENOUGH-CONDITION IS REACHABLE. The cast's ``enough`` ("symmetric difference zero
    across three consecutive pokes") was unreachable by construction: a poke only happens
    when the difference is non-zero, and ``enough`` is asked only after a fire. The tooth
    holds the corrected condition to a standard the old one failed — there must EXIST a world
    in which the probe clears, and it is exhibited here rather than argued.
  - DISCOVERY ARMS IT WITH NO HAND-REGISTRATION, and imports clean. ``cairn/tools/base`` is itself
    a discovered device, so the pass that reports the divergence is the pass that arms the
    reporter.

Runnable bare (no DB, no framework, no network):
    python3 cairn/tools/base/proofs/test_deviceness.py     # exit 0 = green
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.deviceness import (
    HEALTH_QUERY_CLAUSE,
    claims_device_by_inheritance,
    divergence,
    fitted_device_ids,
    is_device,
)
from cairn.devices.ground_loop.discovery import device_folders


def _fixture_tree(root: Path) -> None:
    """A tiny corpus built for these teeth: one Calibre-shaped member, one inheritance-only
    member, one member that is both. Written as files because the predicate reads DISK — a
    fixture that monkeypatched the walk would prove the mock, not the rule."""
    # (1) CALIBRE: a probes/ folder and nothing else. No class, no import, not even Python
    #     beside it. This is the member the inheritance axis is structurally blind to.
    (root / "calibre" / "probes").mkdir(parents=True)

    # (2) INHERITANCE-ONLY: subclasses BaseDevice, owns no probes/ folder.
    (root / "legacy").mkdir(parents=True)
    (root / "legacy" / "legacy.py").write_text(
        "from cairn.tools.base.device import BaseDevice\n\n\nclass LegacyDevice(BaseDevice):\n    pass\n",
        encoding="utf-8",
    )

    # (3) BOTH — so the teeth below cannot pass by simply inverting the old axis.
    (root / "both" / "probes").mkdir(parents=True)
    (root / "both" / "both.py").write_text(
        "from cairn.tools.base.device import BaseDevice\n\n\nclass BothDevice(BaseDevice):\n    pass\n",
        encoding="utf-8",
    )


def test_a_calibre_shaped_member_is_a_device():
    """THE TICKET'S FALSIFIER, RUN: external, folder only, inheriting nothing — and it passes."""
    with tempfile.TemporaryDirectory() as tmp:
        # parents[1] is the root the census walks, so nest one level to mirror cairn/<comp>.
        root = Path(tmp)
        _fixture_tree(root / "pkg")

        assert is_device("calibre", root=root), "the Calibre shape must be admitted"
        assert "calibre" not in claims_device_by_inheritance(root=root), (
            "fixture is wrong if calibre inherits anything — the tooth would be vacuous"
        )


def test_inheritance_alone_is_not_device_ness():
    """WHERE A HOLLOW BUILD PASSES EVERYTHING ELSE AND FAILS HERE. A predicate that ORed the
    two axes would satisfy every other tooth in this file."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _fixture_tree(root / "pkg")

        assert "legacy" in claims_device_by_inheritance(root=root), "fixture check"
        assert not is_device("legacy", root=root), (
            "subclassing BaseDevice must not confer device-ness — that is the axis the "
            "ruling replaced"
        )
        assert is_device("both", root=root), "carrying both must still be a device"


def test_the_predicate_composes_discovery_rather_than_re_deriving_it():
    """Law 1: the answered question became structure. A second roster is the stale-list
    failure the folder ruling was made to end, one layer up."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _fixture_tree(root / "pkg")

        assert fitted_device_ids(root) == {d for d, _ in device_folders(root)}, (
            "the predicate must ANSWER FROM discovery, not agree with it by coincidence"
        )


def test_the_unbuilt_half_is_declared_not_omitted():
    """A predicate that silently implements half its own definition is the shape a reader
    mistakes for whole. The ticket's falsifier has two clauses; one of them names nothing
    that exists, and that fact must be reachable from the code and from the wire."""
    assert "UNBUILT" in HEALTH_QUERY_CLAUSE
    assert "health" in HEALTH_QUERY_CLAUSE.lower()
    assert HEALTH_QUERY_CLAUSE in divergence()["health_query_clause"]

    # And it must actually ride: a declaration nobody transmits is a comment.
    from cairn.tools.base.probes.device_claims_match_shims import PROBE

    assert PROBE.payload({})["predicate_is_half_built"] == HEALTH_QUERY_CLAUSE


def test_the_live_axes_are_reported_as_invariants_never_as_a_snapshot():
    """Over LIVE data, so the assertions are relationships, not numbers. A proof pinning
    today's 19 would go red the day the divergence improved."""
    d = divergence()

    # Every ruled device answers the predicate true. This is the criterion's own instrument.
    for device_id in d["ruled_devices"]:
        assert is_device(device_id), f"{device_id} is discovered but the predicate denies it"

    # The two derived sets are exactly the set algebra they claim to be — so a future edit
    # cannot let the labels drift off the lists under them.
    ruled, inherited = set(d["ruled_devices"]), set(d["claims_device_by_inheritance"])
    assert set(d["inherits_but_not_ruled"]) == inherited - ruled
    assert set(d["ruled_but_inherits_nothing"]) == ruled - inherited
    assert d["symmetric_difference_ruled_vs_inherited"] == len(ruled ^ inherited)

    # NAMES, NOT A COUNT: whatever the numbers are, the report must be actionable.
    assert isinstance(d["inherits_but_not_ruled"], list)
    assert isinstance(d["ruled_but_inherits_nothing"], list)


def test_the_probe_fires_at_arming_and_names_names():
    """The resting state here is a LIVE CROSSING, not a quiet watch — and the shim's memory
    (``_was_true`` starts empty) is what makes a first-pulse TRUE a crossing rather than a
    level. Asserted against the firer, not assumed."""
    from cairn.tools.base.probe import Probe
    from cairn.tools.base.probes.device_claims_match_shims import PROBE
    from cairn.tools.base.shim import BaseShim

    assert isinstance(PROBE, Probe)
    assert PROBE.fires(None, {}) is True, "the divergence is real today; the probe must say so"

    payload = PROBE.payload({})
    for key in ("ruled_devices", "claims_device_by_inheritance", "inherits_but_not_ruled",
                "ruled_but_inherits_nothing"):
        assert isinstance(payload[key], list), f"{key} must ride as NAMES, never a count"
    assert payload["ticket"].endswith("device-ness-is-decided-at-the-shim.json")

    # A virgin shim has fired nothing, so a true trigger CROSSES and pokes.
    class _Shim(BaseShim):
        @property
        def device_id(self) -> str:
            return "base"

        def probes(self):
            return [PROBE]

    shim = _Shim()
    assert shim._was_true == set(), "a fresh shim must remember no line position"
    record = shim.on_pulse(now=None)
    assert record["fired"], "a true trigger on a virgin shim must FIRE, not hold"
    assert record["fired"][0]["why"] == PROBE.why


def test_the_enough_condition_is_reachable():
    """THE TOOTH THE CAST'S OWN ``enough`` FAILED. It read "symmetric difference zero across
    three consecutive pokes" — but a poke only happens when the difference is NON-zero, and
    ``enough`` is asked only after a fire, so no world existed in which the watch cleared.
    A stopping condition must be EXHIBITED as reachable, not argued to be."""
    import json

    from cairn.tools.base.probes import device_claims_match_shims as m

    assert m._enough({}) is False, "the axis is not ruled today; the watch must stand"

    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp)
        (fake / f"{m._RULING_TICKET}.json").write_text(
            json.dumps({"state": "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME "
                                 "-> WATCHME(no-improvised-class-strings) -> [PROVED]"}),
            encoding="utf-8",
        )
        original, m._TICKETS = m._TICKETS, fake
        try:
            assert m._enough({}) is True, (
                "once the axis is RULED the watch must be able to retire — a watch that "
                "cannot clear is the standing cost the shrinking-footprint discipline refuses"
            )
        finally:
            m._TICKETS = original

    # And an unreadable ruling is not a ruling: it must not clear by accident.
    with tempfile.TemporaryDirectory() as tmp:
        original, m._TICKETS = m._TICKETS, Path(tmp)
        try:
            assert m._enough({}) is False
        finally:
            m._TICKETS = original


def test_discovery_arms_the_probe_with_no_hand_registration():
    """``cairn/tools/base`` is itself a discovered device, so the pass that reports the divergence
    is the pass that arms the reporter. No subscribe call, no list to go stale."""
    from cairn.devices.ground_loop.discovery import discover

    found = discover()
    assert "base" in found, "cairn/tools/base must be discovered as a device"
    assert found["base"]["failures"] == [], f"import failures: {found['base']['failures']}"
    whys = [p.why for p in found["base"]["probes"]]
    assert any("CLAIM device-hood" in w for w in whys), (
        "the divergence probe must be armed by discovery, not by a hand"
    )


if __name__ == "__main__":
    failures = []
    for name, fn in sorted(dict(globals()).items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  ok  {name}")
        except AssertionError as exc:
            failures.append((name, exc))
            print(f"  RED {name}: {exc}")
    if failures:
        print(f"\n{len(failures)} RED")
        sys.exit(1)
    print("\ngreen")
