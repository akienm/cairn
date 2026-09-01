"""THE ONE BERTHED PROBE, PROVED — a watch may never clear before it can fire.

Ticket ``watchme-emits-a-probe`` (2026-07-30), written AFTER the live fire, because the live
fire found what four green proofs had not.

THE GAP THIS FILLS, named plainly. ``test_probe.py``, ``test_probe_carry.py``,
``test_probe_crossing.py`` and ``test_probe_enough.py`` prove the Probe PRIMITIVE, and they
prove it well — with synthetic probes reading a dial the proof moves. Not one of them touches
``probes/does_optional_mean_never_carried.py``, the system's only real berthed probe. So the
mechanism was proved and its single instance was not, and the instance is where both bugs were.

WHAT THE LIVE FIRE FOUND. First pulse, driven by hand at the close of this voyage:
``survey_the_corpus()`` reported ``{carried: 1, declined: 0, eligible: 1}`` and ``_enough``
returned **True**. The watch was ready to retire on its first pulse, having measured nothing.
Two independent defects met at that line:

  1. THE CORPUS COUNTED ITS OWN TICKET. The one "carried" was ``watchme-emits-a-probe``
     itself — the node that invented the mechanism, counted as evidence that authors adopt
     the mechanism. Home-field advantage as a measurement: n=1, and the 1 is the author.
  2. THE CLEAR HAD NO SAMPLE-SIZE FLOOR. ``_trigger`` required ``eligible >= _ENOUGH``;
     ``_enough`` required only ``carried > 0``. The watch could clear at n=1 and could not
     fire until n=12, so it was guaranteed to retire before it could ever bite.

Either alone would have been enough to kill it. A watch that clears before it can fire is the
v1 ``LEARNME`` failure wearing this node's own clothes — a summons crossed by everybody and
satisfied by nobody — which is the exact thing this probe was berthed to detect. It would have
detected it everywhere except in itself.

WHAT THIS PROVES:
  - THE INVARIANT, and it is the tooth that would have caught this: over the whole corpus
    space, THERE IS NO STATE WHERE THE WATCH HAS CLEARED BUT COULD NEVER HAVE FIRED. Asserted
    by exhausting the space, not by sampling the state the code happens to be in today.
  - THE OWNING TICKET IS NOT IN ITS OWN CORPUS — measured against the real commons, as an
    invariant (the ticket is present and carries a watch, and the count still excludes it),
    never against a pinned number that normal motion would move.
  - THE FLOOR IS ON BOTH PREDICATES, and neither reduces to the other.
  - FIRE AND CLEAR ARE MUTUALLY EXCLUSIVE — a probe that pokes and retires on the same pulse
    would report a finding and then decline to be asked again.
  - THE PROBE IS ARMED IN THE SENSE THE EMISSION GATE MEANS — it is what the gate reads, so
    the proof reads it the same way rather than inventing a parallel notion of armed.
  - THE CARRIED DATUM POINTS AT THE TICKET AND DOES NOT COPY IT (Law 6).
  - IT READS CLASS-SPACE ONLY — no device, no bus, no network, so it is cheap on a pulse.

    python3 cairn/tools/base/proofs/test_does_optional_probe.py     # exit 0 = green
"""

from __future__ import annotations

import ast
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.tools.base.probe import Probe
from cairn.tools.base.probes import does_optional_mean_never_carried as SUT

NOW = datetime.datetime(2026, 7, 30, tzinfo=datetime.timezone.utc)


def _at(carried: int, declined: int) -> dict:
    """A corpus the predicates will read instead of the disk — the dial this proof moves."""
    return {"corpus": {"carried": carried, "declined": declined,
                       "eligible": carried + declined}}


# --- the invariant ---------------------------------------------------------------------

def test_the_watch_can_never_clear_before_it_could_fire():
    """THE LOAD-BEARING TOOTH. Exhaust the corpus space up to well past the floor and assert
    the ordering that makes a watch honest: if it has CLEARED, the corpus was always big
    enough that it COULD have fired. The old code failed this at (1, 0) — cleared, on a
    corpus of one, having never been fireable. Exhaustive, so no sampled state can hide it."""
    bad = []
    for carried in range(0, SUT._ENOUGH * 2):
        for declined in range(0, SUT._ENOUGH * 2):
            ctx = _at(carried, declined)
            if SUT._enough(ctx) and ctx["corpus"]["eligible"] < SUT._ENOUGH:
                bad.append((carried, declined))
    assert not bad, (
        "the watch clears on a corpus too small to have ever fired it, at "
        f"(carried, declined) = {bad[:6]}{'...' if len(bad) > 6 else ''} — a watch that "
        "retires before it can bite is the v1 failure this probe exists to detect")


def test_fire_and_clear_are_mutually_exclusive():
    """No corpus may both poke the owner and retire the watch. That state would report a
    finding and simultaneously refuse to be asked again — the finding would be the last
    thing the watch ever said, which is not a watch, it is a one-shot."""
    both = [(c, d)
            for c in range(0, SUT._ENOUGH * 2)
            for d in range(0, SUT._ENOUGH * 2)
            if SUT._trigger(NOW, _at(c, d)) and SUT._enough(_at(c, d))]
    assert not both, f"fires AND clears on the same corpus at {both[:6]}"


def test_the_floor_binds_both_predicates_and_neither_is_redundant():
    """Both clauses of each predicate are load-bearing — drop either and the probe is wrong
    in a direction this ticket already paid for once."""
    big = SUT._ENOUGH
    # below the floor: silent in both directions, whatever the counts say
    assert not SUT._trigger(NOW, _at(0, big - 1)), "fired below the floor — pokes about noise"
    assert not SUT._enough(_at(big - 1, 0)), "cleared below the floor — the original defect"
    # at the floor: the two answers separate cleanly on `carried`
    assert SUT._trigger(NOW, _at(0, big)), "did not fire on a full corpus that carried nothing"
    assert not SUT._enough(_at(0, big)), "cleared on a corpus where nobody carried a watch"
    assert SUT._enough(_at(1, big - 1)), "did not clear once a real corpus carried one"
    assert not SUT._trigger(NOW, _at(1, big - 1)), "poked about a mechanism that is working"


# --- the corpus itself, read against the live commons -----------------------------------

def _find_ticket(slug: str) -> Path:
    exact = SUT._TICKETS / (slug + ".json")
    if exact.is_file():
        return exact
    hits = list(SUT._TICKETS.glob(f"*-{slug}.json"))
    assert len(hits) == 1, f"expected exactly one ticket matching *-{slug}.json, got {len(hits)}"
    return hits[0]


def _is_owning_ticket(stem: str) -> bool:
    return stem == SUT._OWNING_TICKET or stem.endswith("-" + SUT._OWNING_TICKET)


def test_the_owning_ticket_is_not_in_its_own_corpus():
    """MEASURED AGAINST THE REAL COMMONS, as an invariant. The owning ticket must be on file
    AND must carry a watch (else this proves nothing — an absent ticket is excluded for the
    wrong reason), and the survey must still not count it. No pinned totals: the corpus is
    live and legitimately moves, and pinning a moving value is the spurious-red defect."""
    from cairn.tools.base.watchme_spec import workflow_objects

    filed = _find_ticket(SUT._OWNING_TICKET)
    assert filed.is_file(), f"the owning ticket is not on file at {filed} — nothing is proved"
    ticket = json.loads(filed.read_text(encoding="utf-8"))
    assert "@v1:" not in ticket["workflow_and_state"], (
        "the owning ticket claims v1, whose vocabulary cannot carry a watch — it would be "
        "excluded from the corpus by version, not by the self-exclusion this proves")
    assert workflow_objects(ticket["workflow_and_state"]), (
        "the owning ticket carries no WATCHME, so excluding it proves nothing about "
        "self-counting")

    surveyed = SUT.survey_the_corpus()
    counted_here = sum(1 for p in sorted(SUT._TICKETS.glob("*.json"))
                       if not p.name.startswith("_") and not _is_owning_ticket(p.stem)
                       and _carries(p))
    assert surveyed["carried"] == counted_here, (
        f"survey counted {surveyed['carried']} carriers; excluding the owning ticket by hand "
        f"gives {counted_here} — the exclusion is not doing what it says")


def _carries(path: Path) -> bool:
    """Mirrors survey_the_corpus's own tolerance deliberately. A ticket may carry a `workflow_and_state`
    that is not a workflow string at all (`"building"` is on file today), so the parse is
    inside the guard — a corpus this cannot read is not a finding, and a hand-count that
    reds where the survey shrugs would be measuring the proof, not the probe."""
    from cairn.tools.base.watchme_spec import workflow_objects
    try:
        state = json.loads(path.read_text(encoding="utf-8")).get("workflow_and_state")
        if not isinstance(state, str) or "@v1:" in state:
            return False
        return bool(workflow_objects(state))
    except Exception:  # noqa: BLE001 — an unreadable ticket is not a carrier
        return False


def test_the_survey_is_internally_consistent():
    """eligible is carried + declined, always — a total that can disagree with its parts is
    a surface that can report a floor as met when it is not."""
    s = SUT.survey_the_corpus()
    assert s["eligible"] == s["carried"] + s["declined"], s
    assert all(v >= 0 for v in s.values()), s


# --- the declaration ---------------------------------------------------------------------

def test_the_probe_is_armed_the_way_the_emission_gate_means_it():
    """Read armed through the gate's own instrument, not a parallel notion of it — else this
    proof could pass a probe the door refuses."""
    from cairn.tools.base import watchme_spec

    ticket = json.loads(_find_ticket(SUT._OWNING_TICKET).read_text("utf-8"))
    assert watchme_spec.watchme_spec_error(ticket) is None
    spec = watchme_spec.spec_for(ticket, "does-optional-mean-never-carried")
    assert spec is not None, "no spec for the object the workflow string names"
    assert watchme_spec.armed_error(spec) is None, watchme_spec.armed_error(spec)
    assert isinstance(SUT.PROBE, Probe) and SUT.PROBE.carry and SUT.PROBE.enough


def test_the_datum_points_at_the_ticket_and_does_not_copy_it():
    """Law 6 — the ticket belongs to the commons; a probe carries a pointer to it.

    AND SINCE 2026-08-05 THE POINTER IS THE PATH (Akien: "the carriers are all files. so the
    file path is the link"). Before, this shipped the bare id and the receiver had to know
    where tickets live before it could open one — a resolver, which is a registry in
    disguise. The tooth now demands an address that opens, not a name that looks right."""
    got = SUT._carry(_at(0, SUT._ENOUGH))
    assert got["ticket"].endswith(f"{SUT._OWNING_TICKET}.json"), got["ticket"]
    assert Path(got["ticket"]).is_file(), \
        f"the pointer must be openable by the receiver as handed: {got['ticket']}"
    blob = json.dumps(got)
    for owned in ("intention", "falsifier", "provenance", "children"):
        assert f'"{owned}"' not in blob, f"the datum copied the ticket's {owned!r} field"


def test_it_reads_class_space_only():
    """No device, no bus, no network — the cost that lets it sit on every pulse. Checked over
    the AST, so a prose mention of `requests` in a docstring cannot red it and a real import
    cannot hide in one."""
    tree = ast.parse(Path(SUT.__file__).read_text(encoding="utf-8"))
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            names.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            names.add(n.module.split(".")[0])
    forbidden = {"socket", "http", "urllib", "requests", "psycopg", "psycopg2", "subprocess"}
    assert not (names & forbidden), f"reaches outward: {sorted(names & forbidden)}"


TESTS = [
    test_the_watch_can_never_clear_before_it_could_fire,
    test_fire_and_clear_are_mutually_exclusive,
    test_the_floor_binds_both_predicates_and_neither_is_redundant,
    test_the_owning_ticket_is_not_in_its_own_corpus,
    test_the_survey_is_internally_consistent,
    test_the_probe_is_armed_the_way_the_emission_gate_means_it,
    test_the_datum_points_at_the_ticket_and_does_not_copy_it,
    test_it_reads_class_space_only,
]

if __name__ == "__main__":
    failures = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} green")
    sys.exit(1 if failures else 0)
