"""Proof: the packet index answers what the full scan answered, and goes stale for nobody.

WHY THIS PROOF EXISTS. ``claiming_packets`` used to open and parse every berthed packet on
every call. Measured on the live store 2026-09-07: 2,552 packets, and the heartbeat probe
``no_component_reaches_proved_with_an_uncharted_build`` asks the chain of all 196 PROVED
tickets on every beat — 1,568 full sweeps per beat, 55.6s of a 104.8s beat, for an answer
that cannot change unless somebody berths a packet. The index removes the sweep.

A CACHE IS A SECOND COPY OF A RECORD OF TRUTH, so the teeth here are pointed at the two ways
one goes wrong, not at the speed:

  - IT DISAGREES WITH DISK. The equivalence tooth compares the index's answers against a
    brute-force scan over a seeded store, for every ticket and every leg — not one sampled
    case, and not the live corpus, so the pass cannot be an accident of today's berths.
  - IT GOES STALE. A new berth, a deleted berth, and an EDITED berth each get their own
    tooth. The edited one is the sharp one: the index holds ADDRESSES and never bodies
    precisely so that a body can never be served from memory, and the tooth would fail if
    someone later "optimised" the packet dicts into the cache.

And one tooth that is about the cache being a cache at all: ``_INDEX_BUILDS`` must not move
across repeated calls over an unchanged store. A cache that silently rebuilds every time
returns identical answers to one that works, so nothing in the ANSWERS can tell them apart —
which is the shape of hollow green Law 8 refuses.
"""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from cairn.tools.chain import chain as SUT
from cairn.tools.chain.chain import (
    CHAIN_STAGES, chain_for_ticket, claiming_packet_paths, claiming_packets,
)

# Two tickets, so an answer for one can never be the whole store; stamps ascending so the
# LAST berth of a stage is a known one rather than whichever the filesystem hands back.
_SEED = [
    ("orient",   "20260901T090000", "aaaa11112222"),
    ("survey",   "20260901T090100", "aaaa11112222"),
    ("survey",   "20260902T090100", "aaaa11112222"),   # the one that stands at survey
    ("validate", "20260903T090200", "aaaa11112222"),
    ("verdict",  "20260904T090300", "aaaa11112222"),
    ("orient",   "20260901T100000", "bbbb33334444"),
    ("verdict",  "20260905T100300", "bbbb33334444"),
]


def _berth(root: str, stage: str, stamp: str, ticket: str, **extra) -> str:
    """Write one packet the way the /chart door writes them: a stamped filename, never
    edited in place, under ``<root>/<instance>/packets/``."""
    folder = os.path.join(root, "0", "packets")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{stage}-{stamp}-{ticket[:12]}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"ticket": ticket, "stage": stage, **extra}, fh)
    return path


@pytest.fixture
def store():
    """A seeded berth store, built for these teeth so no pass is an accident of the live one."""
    with tempfile.TemporaryDirectory() as root:
        for stage, stamp, ticket in _SEED:
            _berth(root, stage, stamp, ticket)
        SUT._INDEX_CACHE.pop(root, None)
        yield root


def _brute(root: str, ticket: str, stage: str) -> list[str]:
    """The scan the index replaces, spelled out here so the comparison is against an
    INDEPENDENT reading rather than against the thing under test."""
    import glob
    found = []
    for path in sorted(glob.glob(os.path.join(root, "*", "packets", f"{stage}-*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                packet = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(packet, dict) and packet.get("ticket") == ticket:
            found.append(path)
    return found


def test_the_index_answers_exactly_what_a_full_scan_answers(store):
    """Every ticket, every leg — not a sampled case."""
    for ticket in ("aaaa11112222", "bbbb33334444", "cccc55556666"):
        for stage in CHAIN_STAGES:
            want = _brute(store, ticket, stage)
            got = claiming_packet_paths(ticket, stage, berths_root=store)
            assert got == want, f"{ticket}/{stage}: index said {got}, the scan said {want}"
            bodies = claiming_packets(ticket, stage, berths_root=store)
            assert [p for p, _ in bodies] == want, f"{ticket}/{stage}: bodies came from {bodies}"
    # and the resolver over the top of it agrees leg by leg
    chain = chain_for_ticket("aaaa11112222", berths_root=store)
    assert chain["survey"] == _brute(store, "aaaa11112222", "survey")[-1], chain
    assert chain["triage"] is None, chain


def test_a_newly_berthed_packet_is_seen_on_the_VERY_NEXT_call(store):
    """THE STALENESS TOOTH. A chain run berths a packet and then reads the chain; an index
    that needed a restart to notice would refuse a crossing whose chart is on disk."""
    before = chain_for_ticket("aaaa11112222", berths_root=store)
    assert before["triage"] is None, before
    fresh = _berth(store, "triage", "20260906T110000", "aaaa11112222")
    after = chain_for_ticket("aaaa11112222", berths_root=store)
    assert after["triage"] == fresh, f"the new berth was invisible: {after}"


def test_a_deleted_berth_leaves_the_answer(store):
    """The other direction: an index that only ever grows is a different way of being stale."""
    standing = chain_for_ticket("bbbb33334444", berths_root=store)["verdict"]
    assert standing is not None
    os.remove(standing)
    assert chain_for_ticket("bbbb33334444", berths_root=store)["verdict"] is None


def test_the_body_is_RE_READ_from_disk_and_never_served_from_the_index(store):
    """The index holds ADDRESSES, never packet bodies. Edited in place — which changes the
    FILE's mtime but not the DIRECTORY's, so the index is deliberately not rebuilt — and the
    caller must still get what is on disk. This tooth fails the moment anyone caches the
    parsed dicts."""
    path = claiming_packet_paths("aaaa11112222", "orient", berths_root=store)[0]
    claiming_packets("aaaa11112222", "orient", berths_root=store)      # warm the index
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"ticket": "aaaa11112222", "stage": "orient", "refs": ["EDITED"]}, fh)
    (_p, packet), = claiming_packets("aaaa11112222", "orient", berths_root=store)
    assert packet["refs"] == ["EDITED"], f"a stale body came back from memory: {packet}"


def test_the_index_is_built_ONCE_over_an_unchanged_store(store):
    """A cache that rebuilds every call returns identical ANSWERS to one that works — so
    nothing in the answers can tell them apart, and only the build counter can."""
    claiming_packet_paths("aaaa11112222", "orient", berths_root=store)
    builds = SUT._INDEX_BUILDS
    for _ in range(20):
        for stage in CHAIN_STAGES:
            claiming_packet_paths("aaaa11112222", stage, berths_root=store)
            claiming_packet_paths("bbbb33334444", stage, berths_root=store)
    assert SUT._INDEX_BUILDS == builds, (
        f"the store never moved and the index rebuilt {SUT._INDEX_BUILDS - builds} time(s) — "
        "that is a scan wearing a cache's name")
    _berth(store, "constrain", "20260907T120000", "aaaa11112222")
    claiming_packet_paths("aaaa11112222", "constrain", berths_root=store)
    assert SUT._INDEX_BUILDS == builds + 1, (
        "the store moved and the index did NOT rebuild — the token stopped watching")


def test_an_unreadable_packet_is_absent_from_the_answer_not_fatal(store):
    """A corrupt berth must not take down every reader of the store. Same disposition the
    scan had; asserted so a future rewrite cannot quietly turn it into a raise."""
    folder = os.path.join(store, "0", "packets")
    with open(os.path.join(folder, "survey-20260908T130000-broken.json"), "w") as fh:
        fh.write("{not json")
    got = claiming_packet_paths("aaaa11112222", "survey", berths_root=store)
    assert len(got) == 2 and all("broken" not in p for p in got), got


def test_a_packet_naming_NO_ticket_indexes_under_nothing(store):
    """The index is keyed by the packet's own ``ticket`` field; a packet without one belongs
    to no ticket and must not be attributed to whoever asks first."""
    folder = os.path.join(store, "0", "packets")
    with open(os.path.join(folder, "survey-20260908T140000-orphan.json"), "w") as fh:
        json.dump({"stage": "survey"}, fh)
    for ticket in ("aaaa11112222", "bbbb33334444"):
        assert all("orphan" not in p
                   for p in claiming_packet_paths(ticket, "survey", berths_root=store))


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
