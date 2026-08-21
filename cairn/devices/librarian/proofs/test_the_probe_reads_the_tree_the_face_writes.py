"""Proof for probes/standing_moves_under_live_use.py — the WATCHME instrument's SEAM.

Ticket ``a-probe-reads-the-tree-the-face-writes``, a kick-back into ``the-tenure-loop``'s
armed watch. The defect this pins: the probe held ``_TREE = 'commons'`` and censused only
that tree, while the live face composes its session with ``tree='library'``
(``shim.py:35``). The instrument surveyed an address the running system has never written
to — 88 rows live, distributed ``{'library': 84, 'founding': 4}``, and ``'commons'`` an
ABSENT KEY, not a small count (measured 2026-08-10). An armed probe reading a dead address
does not report ill health; it reports nothing, and silence at a watch reads as "nothing to
see". That is how a hollow watch passed a PROVED crossing.

THE TOOTH READS BOTH ENDS FROM THEIR DECLARATIONS, NEVER FROM A LITERAL. The face's tree
comes from ``inspect.signature(LibrarianShim.__init__)``; the census's tree comes from the
probe's own module global. A tooth that asserted ``_TREE == 'library'`` would re-encode the
repaired constant in a second place and go green on its own copy of the answer — it would
survive the day both ends move to a third tree together, which is exactly the day nothing
is broken. This one reds on DISAGREEMENT, whichever way either end moves.

Teeth a hollow instrument could not pass:

  - THE SEAM ITSELF: a node the face's tree holds is SEEN by the probe's own census.
    Reds today at ``_TREE = 'commons'``; the failure text names both ends.
  - THE CENSUS IS NOT A PASS-THROUGH: a node in a neighbouring tree of the same table is
    NOT seen. Paired with the first, only a correctly-aimed census clears both — a census
    hardwired to return every row passes the first and fails this; a census aimed at a dead
    tree fails the first and passes this vacuously.
  - THE PREDICATES ARE FED BY THE CENSUS: with a genuinely-promoted node and an aged
    uncorroborated shard in the face's tree, ``_enough`` CLEARS. This is what makes the seam
    load-bearing rather than cosmetic — a severed census does not merely mis-report, it
    disarms the watch.
  - AND A SEVERED CENSUS IS SILENT, NOT LOUD: aimed at a tree nothing writes, the survey is
    empty and BOTH predicates stand down — the exact serene green the live probe was
    reporting. This tooth is the defect's own signature, kept so it cannot come back
    unnamed.

The corpus is a NONCE TABLE through db_domain, self-cleaning — never the live
``librarian_nodes``. The ticket's bounds put "any WRITE to librarian_nodes from the probe or
from the proof against the live store" explicitly OUT (charter falsifier 4: the instrument
may not become its own evidence). The TABLE is substituted because it is a fixture concern;
the TREE never is, because it is the thing under test.

    python3 cairn/devices/librarian/proofs/test_the_probe_reads_the_tree_the_face_writes.py
    # exit 0 = green
"""

from __future__ import annotations

import inspect
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.db_domain import store
from cairn.devices.librarian.loop import DECAY_HORIZON, PROMOTION_THRESHOLD
from cairn.devices.librarian.probes import standing_moves_under_live_use as probe
from cairn.devices.librarian.shim import LibrarianShim
from cairn.devices.librarian import trees
from cairn.devices.librarian.trees import OWNER, corroborate, deposit, node_id_for

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLE = f"_probeseam_{_NONCE}"
_PROV_SOURCE = "proofs/test_the_probe_reads_the_tree_the_face_writes.py"
_VEC = [1.0, 0.0, 0.0]

# THE FACE'S TREE, read from the writing end's own signature — the one place the live
# wiring declares it. Never a literal: the point of this tooth is that the two ends are
# compared, not that either matches a string the proof carries.
_FACE_TREE = inspect.signature(LibrarianShim.__init__).parameters["tree"].default

# A neighbour in the same table that the census must NOT sweep up.
_DECOY_TREE = f"{_FACE_TREE}_decoy"


def _census() -> dict:
    """The probe's OWN survey, run against the nonce table. Only ``NODES`` is rebound —
    the probe's ``_TREE`` is left exactly as the module declares it, because that constant
    is the subject of every assertion below."""
    probe.NODES = _TABLE
    return probe.survey_the_tree()


def _seam_report(seen: dict) -> str:
    return (f"the face writes tree={_FACE_TREE!r} (LibrarianShim.__init__ default) and the "
            f"probe censuses tree={probe._TREE!r} (standing_moves_under_live_use._TREE). "
            f"The census returned: {seen}")


def test_the_census_sees_a_node_the_faces_tree_holds():
    """THE SEAM. A node deposited where the live face writes must appear in the census the
    armed probe runs. Nothing here asserts a tree NAME — only that the reader and the writer
    agree, so the tooth stays true if the whole librarian moves to a third tree tomorrow."""
    content = "a node the live face would have deposited"
    nid = node_id_for(content)
    deposit(content, _VEC, {"source": _PROV_SOURCE, "question": "what the face asked"},
            tree=_FACE_TREE, table=_TABLE)

    seen = _census()
    assert "unreadable" not in seen, f"the store must be reachable for this tooth: {seen}"
    assert seen["standing_distribution"].get("hypothesis"), (
        "THE PROBE IS AIMED AT A TREE THE FACE DOES NOT WRITE — a node just landed in the "
        f"face's own tree and the instrument's census does not see it. {_seam_report(seen)} "
        f"The deposited node is {nid!r}. An armed probe reading an address nothing writes "
        "reports silence, and silence at a watch is indistinguishable from health.")
    assert seen["crossings_since_landing"] >= 1, (
        "the census sees the row but counts no crossing — the era floor "
        f"(_LANDED = {probe._LANDED.date()}) has stranded the arithmetic: {seen}")


def test_the_census_is_not_a_pass_through():
    """NON-VACUITY, and it is the tooth above's other half. A census that ignored its tree
    filter and returned every row would satisfy the seam tooth while measuring nothing.
    Together the pair admits exactly one aim: the face's."""
    content = "a node in a neighbouring tree that the census must not sweep up"
    deposit(content, _VEC, {"source": _PROV_SOURCE, "question": "a decoy question"},
            tree=_DECOY_TREE, table=_TABLE)

    seen = _census()
    rows_in_face_tree = store.read(_TABLE)
    counted = sum(seen["standing_distribution"].values())
    assert counted == len(rows_in_face_tree), (
        f"the census counted {counted} rows but tree {_FACE_TREE!r} holds "
        f"{len(rows_in_face_tree)} — it is not filtering by tree, so its numbers are about "
        f"the table rather than about the librarian's corpus. {_seam_report(seen)}")


def test_the_predicates_are_fed_by_the_census():
    """WHY THE SEAM IS LOAD-BEARING. A severed census does not mis-report the tenure loop —
    it DISARMS the watch. Stage both halves of ``_enough`` in the face's tree (a node earned
    across PROMOTION_THRESHOLD distinct cross-questions, and an uncorroborated shard aged
    past DECAY_HORIZON) and the probe must clear. Both halves are staged through the
    librarian's own doors, so nothing here asserts a snapshot of the live corpus."""
    earned_content = f"a node that earned its standing across independent questions [{_NONCE}]"
    earned_id = node_id_for(earned_content)
    deposit(earned_content, _VEC, {"source": _PROV_SOURCE, "question": "its birth question"},
            tree=_FACE_TREE, table=_TABLE)
    for i in range(PROMOTION_THRESHOLD):
        corroborate(earned_id, f"an independent question, number {i}",
                    promote_at=PROMOTION_THRESHOLD, tree=_FACE_TREE, table=_TABLE)

    shard_content = f"an aged shard nobody ever walked back to [{_NONCE}]"
    shard_id = node_id_for(shard_content)
    deposit(shard_content, _VEC, {"source": _PROV_SOURCE, "question": "its own birth question"},
            tree=_FACE_TREE, table=_TABLE)
    store.update(trees.NODES_TABLE, OWNER,
                 {"created": datetime.now(timezone.utc) - DECAY_HORIZON - timedelta(days=1)},
                 where="node_id = %s", params=(shard_id,))

    seen = _census()
    assert any(e["node_id"] == earned_id and e["corroborating_questions"] >= PROMOTION_THRESHOLD
               for e in seen["earned"]), (
        "the census does not see the promoted node, so the probe cannot tell a live "
        f"promotion from an absent one. {_seam_report(seen)}")
    assert shard_id in seen["faded_shards"], (
        f"the census does not see the aged shard {shard_id!r}, so decay is invisible to the "
        f"watch. {_seam_report(seen)}")
    assert probe._enough({"survey": seen}) is True, (
        "both halves of the tenure loop are standing in the face's tree and the probe's own "
        f"_enough does not clear — the watch cannot be satisfied by the world. {seen}")
    assert probe._trigger(None, {"survey": seen}) is False, (
        "a genuinely-corroborated earned node is exactly what the trigger asserts the "
        f"absence of — it must not fire here: {seen}")


def test_a_severed_census_stands_down_silently():
    """THE DEFECT'S OWN SIGNATURE, kept so it cannot return unnamed. Aim the census at a
    table nothing writes and the probe does not go loud — the survey comes back empty and
    BOTH predicates stand down. Serene green from a dead address is the failure mode this
    ticket exists to close, and it is a property of the design, not of today's data.

    Three-table schema: tree-level filtering is now at the TABLE level (each tree gets
    its own leaf table), so a severed address means an empty or non-existent table."""
    _DEAD = f"_probeseam_dead_{_NONCE}"
    store.create_owned_table(_DEAD, OWNER, trees._LEAF_COLUMNS)
    try:
        probe.NODES = _DEAD
        seen = probe.survey_the_tree()
        assert seen["standing_distribution"] == {} and seen["crossings_since_landing"] == 0, \
            f"the dead-table census must be empty, not merely small: {seen}"
        assert probe._trigger(None, {"survey": seen}) is False, \
            "a severed census stands the trigger DOWN — it never reports ill health"
        assert probe._enough({"survey": seen}) is False, \
            "and it never clears either: the watch is simply disarmed, in silence"
    finally:
        probe.NODES = _TABLE
        conn = store.connect()
        try:
            with conn.cursor() as cur:
                cur.execute(f'DROP TABLE IF EXISTS "{_DEAD}"')
                cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (_DEAD,))
        finally:
            conn.close()


def test_the_probe_declares_a_probe_and_stays_a_reader():
    """The instrument is still the thing the emission gate resolved ARMED: a module-level
    frozen PROBE at the berth the ticket named, carrying both a carry and an enough. And it
    stays a READER — charter falsifier (4) forbids a non-librarian write, so the probe's
    source may not reach for the store's write face."""
    assert probe.PROBE.carry is not None and probe.PROBE.enough is not None, \
        "the emission gate resolves ARMED from a PROBE carrying both — this must not decay"
    src = Path(probe.__file__).read_text()
    for write_verb in ("store.write", "store.update", "store.delete", "deposit(", "corroborate("):
        assert write_verb not in src, (
            f"the probe reaches for {write_verb!r} — an instrument that writes to the corpus "
            "it measures is its own evidence (charter falsifier 4)")


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{_TABLE}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (_TABLE,))
    finally:
        conn.close()


def _main() -> int:
    checks = [
        test_the_census_sees_a_node_the_faces_tree_holds,
        test_the_census_is_not_a_pass_through,
        test_the_predicates_are_fed_by_the_census,
        test_a_severed_census_stands_down_silently,
        test_the_probe_declares_a_probe_and_stays_a_reader,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print(f"green — the probe's census reads tree={_FACE_TREE!r}, the same tree "
          "LibrarianShim's own signature declares the live face writes: a node the face's "
          "tree holds is seen, a neighbour's is not, both halves of the tenure loop reach "
          "the predicates, and a severed census is proved to stand down in silence rather "
          "than go loud")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
