"""Proof for librarian/trees.py — the graph-tree spine. Teeth a hollow store could not pass:

  - THE DOOR REFUSES THE UNTRACEABLE: a deposit without provenance (or with a sourceless
    one) never lands — fabricated attribution cannot take up permanent residence.
  - VECTORS ARE PHYSICS: empty, non-numeric, non-finite, and zero vectors are refused at
    both doors; a dimension mismatch (deposit or query) is refused, not answered.
  - BORN A HYPOTHESIS: a landed node reads back with its content, structured provenance,
    and standing = "hypothesis" (Law 3 — tenure is a later measurement, not a birthright).
  - A DUPLICATE GROWS NOTHING, BUT ITS PROVENANCE LANDS: same tree + content returns the
    standing node, flagged, row count unmoved (Law 1 stops redundant STRUCTURE) — and the
    incoming provenance appends as a timestamped attestation (ticket the-tenure-loop:
    redundant ARRIVAL is evidence). The shared walk never decays a tenant's node.
  - THE EMBEDDING IS THE PATH: nearest ranks by cosine, provably in proximity order;
    neighbors derives a node's edges and excludes the node itself; NO edge table exists —
    nothing edge-named is ever registered with db_domain.
  - TREES DO NOT CROSS: a walk of one tree never surfaces another tree's nodes.
  - THE OWNER-GATE HOLDS THROUGH THE STACK: a non-librarian write to the nodes table is
    refused by db_domain's physics, not by this module's manners.
  - CROSSINGS BREADCRUMB, READS STAY SILENT: every deposit emits (DEPOSITED and DUPLICATE
    alike); walks emit nothing.
  - DEVICE-HOOD: BaseDevice + CP1-CP6 + the ordered Form v0 #2 surface.
  - IMPORT PURITY BY AST ALLOWLIST: trees.py reaches the DB only through db_domain and
    the network not at all — psycopg2, urllib, socket and friends cannot appear.

Requires the one-time DB provisioning (as db_domain's proof does). Self-cleaning: the
nonce table and its registry row are dropped. The netns seal does not sever the DB — the
Unix socket is a file (db_domain's documented asymmetry, exercised for real here).

    python3 cairn/devices/librarian/proofs/test_librarian_trees.py     # exit 0 = green
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.device import BaseDevice
from cairn.devices.db_domain import store
from cairn.devices.db_domain.store import OwnershipError
from cairn.devices.librarian import trees
from cairn.devices.librarian.trees import (
    DepositRefused, LibrarianDevice, WalkRefused, deposit, nearest, neighbors,
)

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLE = f"_trees_{_NONCE}"
_TABLE2 = f"_trees2_{_NONCE}"
_TABLE_TENANT = f"_tenant_{_NONCE}"
_TABLE_EMPTY = f"_empty_{_NONCE}"
_TABLE_RETIRE = f"_retire_{_NONCE}"
_CREATED_NODES: list[str] = []

_PROV = {"source": "proofs/test_librarian_trees.py", "ground": "fixture"}


def _fresh_librarian() -> LibrarianDevice:
    """A LibrarianDevice, SILENCED — the proof reads its breadcrumbs off the device.

    Ticket a-device-logs-without-being-wired (2026-08-18): a device with no receiver used to HOLD
    its breadcrumbs, so a proof got the held list for free. It now derives its own component name
    and WRITES to ``~/.cairn/logs/librarian/0/`` — which would empty every held-list assertion in this
    file and seed the live tree from a proof in the same stroke. ``set_diagnostic_receiver(None)``
    asks for the holding that used to be an accident. Law 7 is untouched: the record is never
    silently dropped, only its default home moved.
    """
    dev = LibrarianDevice()
    dev.set_diagnostic_receiver(None)
    return dev


def _refuses(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc as e:
        return str(e)
    raise AssertionError(f"{fn.__name__} must refuse with {exc.__name__} — it did not")


def test_the_door_refuses_the_untraceable():
    # No provenance at all, a non-dict, and a sourceless dict: none may land.
    _refuses(DepositRefused, deposit, "a perfectly good sentence", [1.0, 0.0], None, table=_TABLE)
    _refuses(DepositRefused, deposit, "a perfectly good sentence", [1.0, 0.0], "held-librarian", table=_TABLE)
    msg = _refuses(DepositRefused, deposit, "a perfectly good sentence", [1.0, 0.0],
                   {"source": "  "}, table=_TABLE)
    assert "provenance" in msg and "source" in msg, "the refusal must name what was missing"
    # And content under the floor is invention, refused before any write.
    _refuses(DepositRefused, deposit, "tiny", [1.0, 0.0], _PROV, table=_TABLE)


def test_vectors_are_physics_at_both_doors():
    for bad in ([], ["a", "b"], [float("nan"), 1.0], [0.0, 0.0]):
        _refuses(DepositRefused, deposit, "content long enough to land", bad, _PROV, table=_TABLE)
        _refuses(WalkRefused, nearest, bad, tree="commons", table=_TABLE)
    _refuses(WalkRefused, nearest, [1.0, 0.0], k=0, table=_TABLE)


def test_a_node_lands_and_is_born_a_hypothesis():
    r = deposit("the embedding is the path through the graph trees",
                [1.0, 0.0, 0.0], _PROV, tree="t1", table=_TABLE)
    _CREATED_NODES.append(r["node_id"])
    assert r["duplicate"] is False and r["dim"] == 3
    node_rows = store.read(trees.NODES_TABLE, where="node_id = %s", params=(r["node_id"],))
    assert len(node_rows) == 1, "the node must land in cairn_nodes"
    node = node_rows[0]
    assert node["standing"] == "hypothesis", "every node is born a hypothesis (Law 3)"
    assert node["provenance"]["source"] == _PROV["source"], "provenance must round-trip as structure"
    emb_rows = store.read(trees.EMBEDDINGS_TABLE, where="node_id = %s", params=(r["node_id"],))
    assert len(emb_rows) == 1, "an embedding must land in cairn_embeddings"
    assert emb_rows[0]["vector"] == [1.0, 0.0, 0.0], "the vector must round-trip exactly"
    leaf_rows = store.read(_TABLE, where="node_id = %s", params=(r["node_id"],))
    assert len(leaf_rows) == 1, "a leaf must land in the caller's table"


def test_a_duplicate_grows_nothing_but_its_provenance_lands():
    content = "the embedding is the path through the graph trees"
    conn = store.connect()
    cur = conn.cursor()
    cur.execute(f"SELECT count(*) FROM {trees.NODES_TABLE}")
    nodes_before = cur.fetchone()[0]
    cur.execute(f"SELECT count(*) FROM {_TABLE}")
    leaves_before = cur.fetchone()[0]
    r = deposit(content, [1.0, 0.0, 0.0], {"source": "a-second-witness"}, tree="t1", table=_TABLE, conn=conn)
    assert r["duplicate"] is True, "the standing node must come back flagged"
    assert r["provenance_appended"] is True
    cur.execute(f"SELECT count(*) FROM {trees.NODES_TABLE}")
    assert cur.fetchone()[0] == nodes_before, "a duplicate must grow cairn_nodes by NOTHING (Law 1)"
    cur.execute(f"SELECT count(*) FROM {_TABLE}")
    assert cur.fetchone()[0] == leaves_before, "a duplicate must grow the leaf table by NOTHING"
    node = store.read(trees.NODES_TABLE, where="node_id = %s", params=(r["node_id"],), conn=conn)[0]
    attests = node["provenance"].get("attestations") or []
    assert len(attests) >= 1 and attests[-1]["source"] == "a-second-witness" and attests[-1]["at"], \
        "the incoming provenance must land WHOLE as an attestation, timestamped"
    assert node["provenance"]["source"] == _PROV["source"], "the birth provenance survives untouched"
    conn.close()


def test_dimension_mismatch_is_refused_not_answered():
    _refuses(DepositRefused, deposit, "a node of the wrong dimension",
             [1.0, 0.0], _PROV, tree="t1", table=_TABLE)
    _refuses(WalkRefused, nearest, [1.0, 0.0], tree="t1", table=_TABLE)


def test_nearest_ranks_by_proximity_and_derives_the_path():
    r1 = deposit("east-pointing node, the close one", [1.0, 0.1, 0.0], _PROV, tree="t1", table=_TABLE)
    _CREATED_NODES.append(r1["node_id"])
    r2 = deposit("up-pointing node, the far one", [0.0, 0.0, 1.0], _PROV, tree="t1", table=_TABLE)
    _CREATED_NODES.append(r2["node_id"])
    got = nearest([1.0, 0.05, 0.0], k=2, tree="t1", table=_TABLE)
    assert [n["content"] for n in got][0] == "east-pointing node, the close one"
    assert got[0]["similarity"] > got[1]["similarity"], "ranked by cosine, descending"
    assert all(-1.0 <= n["similarity"] <= 1.0 for n in got), "cosine stays in [-1, 1]"
    assert nearest([1.0], k=3, tree="empty", table=_TABLE_EMPTY) == []


def test_the_walk_itself_never_decays_a_tenant():
    aged = "an old resident a tenant's walk must still surface first"
    r = deposit(aged, [1.0, 0.02, 0.0], _PROV, tree="tenant", table=_TABLE_TENANT)
    _CREATED_NODES.append(r["node_id"])
    r2 = deposit("a nearer-in-time but farther-in-space node", [0.3, 0.9, 0.0], _PROV,
                 tree="tenant", table=_TABLE_TENANT)
    _CREATED_NODES.append(r2["node_id"])
    store.update(trees.NODES_TABLE, trees.OWNER,
                 {"created": datetime.now(timezone.utc) - timedelta(days=365)},
                 where="node_id = %s", params=(r["node_id"],))
    got = nearest([1.0, 0.0, 0.0], k=2, tree="tenant", table=_TABLE_TENANT)
    assert got[0]["node_id"] == r["node_id"], \
        "a year-old node still ranks FIRST by raw cosine — no decay at the shared walk"
    assert got[0]["created"] is not None, "created rides the walk as data for the reader"


def test_trees_do_not_cross():
    r = deposit("a node that lives in another tree entirely", [1.0, 0.09, 0.0],
                _PROV, tree="t2", table=_TABLE2)
    _CREATED_NODES.append(r["node_id"])
    surfaced = nearest([1.0, 0.09, 0.0], k=50, tree="t1", table=_TABLE)
    assert all("another tree" not in n["content"] for n in surfaced), \
        "a walk of _TABLE must never surface a _TABLE2 node — leaf tables are separate trees"


def test_neighbors_are_derived_and_exclude_self():
    nid = trees.node_id_for("east-pointing node, the close one")
    got = neighbors(nid, k=2, tree="t1", table=_TABLE)
    assert got, "a node among siblings has derived neighbors"
    assert all(n["node_id"] != nid for n in got), "a node is not its own neighbor"
    _refuses(WalkRefused, neighbors, "no-such-node", tree="t1", table=_TABLE)


def test_tree_state_moves_with_the_tree_and_only_with_it():
    # The livelock-fix primitive: same members -> same digest; a deposit moves it; a
    # DUPLICATE deposit (nothing written) leaves it exactly where it stood.
    before = trees.tree_state("t1", table=_TABLE)
    again = trees.tree_state("t1", table=_TABLE)
    assert before == again, "the fingerprint is a pure function of the tree's members"
    assert before["nodes"] > 0 and before["digest"] != "empty"
    r = deposit("a node that moves the fingerprint", [0.2, 0.9, 0.0], _PROV, tree="t1", table=_TABLE)
    _CREATED_NODES.append(r["node_id"])
    moved = trees.tree_state("t1", table=_TABLE)
    assert moved["digest"] != before["digest"] and moved["nodes"] == before["nodes"] + 1
    deposit("a node that moves the fingerprint", [0.2, 0.9, 0.0], _PROV, tree="t1", table=_TABLE)
    assert trees.tree_state("t1", table=_TABLE) == moved, \
        "a duplicate writes nothing, so the fingerprint must not move"
    assert trees.tree_state("never-touched", table=_TABLE_EMPTY) == {"digest": "empty", "nodes": 0}


def test_no_edge_table_exists():
    # The derived-edges claim, pinned in the registry: nothing edge-named was ever
    # registered by this build (a hollow store quietly persisting adjacency trips this).
    for name in ("librarian_edges", f"{_TABLE}_edges"):
        assert store.owner_of(name) is None, f"an edge table {name!r} must NOT exist — edges are derived"


def test_the_owner_gate_holds_through_the_stack():
    try:
        store.write(_TABLE, "impostor", {
            "leaf_id": "forced", "node_id": "forced", "embedding_id": "forced"})
        raise AssertionError("a non-librarian write must be REFUSED by db_domain (Law 6)")
    except OwnershipError:
        pass


def test_crossings_breadcrumb_and_reads_stay_silent():
    dev = _fresh_librarian()
    r1 = dev.deposit("a breadcrumbed crossing, observed end to end",
                     [0.5, 0.5, 0.0], _PROV, tree="t1", table=_TABLE)
    dev.deposit("a breadcrumbed crossing, observed end to end",
                [0.5, 0.5, 0.0], _PROV, tree="t1", table=_TABLE)
    crumbs = dev.held_diagnostics()
    assert len(crumbs) == 2, "every deposit crossing breadcrumbs — DEPOSITED and DUPLICATE alike"
    assert [c["values"]["verdict"] for c in crumbs] == ["DEPOSITED", "DUPLICATE"]
    assert crumbs[0]["pointer"] == r1["node_id"], "the pointer is the node that crossed"
    assert crumbs[0]["gate"] == "deposit" and crumbs[0]["source"] == "LibrarianDevice"

    dev.nearest([1.0, 0.0, 0.0], tree="t1", table=_TABLE)
    dev.neighbors(r1["node_id"], tree="t1", table=_TABLE)
    assert len(dev.held_diagnostics()) == 2, "walks are reads — silent, no breadcrumb"
    assert dev.state()["deposits"] == 2 and dev.state()["verdicts"]["DUPLICATE"] == 1


def test_device_hood_and_the_ordered_surface():
    dev = _fresh_librarian()
    assert isinstance(dev, BaseDevice) and dev.device_id == "librarian"
    surface = dev.introspect()
    assert list(surface) == ["intention", "state", "settings", "other"], "Form v0 #2 order is the contract"
    assert "chatbot" in surface["intention"]["what"], "the reported intention names the face"
    from cairn.tools.base.core_values import CoreValuesMixin
    assert isinstance(dev, CoreValuesMixin), "a device carries CP1-CP6 structurally (Law 2)"


def test_trees_opens_no_door_of_its_own():
    # Allowlist, not blocklist: an import outside these prefixes is a second door and reds.
    allowed = ("__future__", "hashlib", "math", "datetime", "cairn.tools.base", "cairn.devices.db_domain",
               "psycopg2")
    src = Path(trees.__file__).read_text(encoding="utf-8")
    seen = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            seen.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            seen.append(node.module or "")
    offenders = [m for m in seen if not any(m == p or m.startswith(p + ".") for p in allowed)]
    assert not offenders, (
        f"trees.py imports outside its allowlist: {offenders} — the DB is reached only "
        "through db_domain and the network not at all (Law 4; sole-path)")


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            for t in (_TABLE, _TABLE2, _TABLE_TENANT, _TABLE_EMPTY, _TABLE_RETIRE):
                cur.execute(f'DROP TABLE IF EXISTS "{t}"')
                cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (t,))
            for nid in _CREATED_NODES:
                cur.execute(f'DELETE FROM "{trees.EMBEDDINGS_TABLE}" WHERE node_id = %s', (nid,))
                cur.execute(f'DELETE FROM "{trees.NODES_TABLE}" WHERE node_id = %s', (nid,))
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# THE RETIREMENT DOOR (ticket revision-with-receipts) — the fifth tenure behaviour.
# ---------------------------------------------------------------------------

_RETIRE_TREE = "retire"


def _row(nid):
    rows = store.read(trees.NODES_TABLE, where="node_id = %s", params=(nid,))
    return rows[0] if rows else None


def _fingerprint(nid) -> str:
    """A hash of the WHOLE node row — so a refused call cannot have moved one byte of it."""
    return hashlib.sha256(
        json.dumps(_row(nid), sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _land(content, vector, source="llm-backfill", **extra):
    prov = {"source": source, **extra}
    r = deposit(content + f" [{_NONCE}]", vector, prov, tree=_RETIRE_TREE, table=_TABLE_RETIRE)
    _CREATED_NODES.append(r["node_id"])
    return r["node_id"]


def _make_earned(nid):
    store.update(trees.NODES_TABLE, trees.OWNER, {"standing": "earned"},
                 where="node_id = %s", params=(nid,))


def test_a_retirement_is_one_owner_gated_act_that_deletes_nothing():
    target = _land("the library closes at four on weekdays", [1.0, 0.0])
    refuter = _land("the posted hours say six, not four", [0.9, 0.1], source="correction")
    before = _row(target)

    # ONE store.update — the standing change and the receipt cannot land separately, or a
    # reader could see a node retired with no reason attached to it (Law 6, one owner moment).
    calls = []
    real_update = store.update

    def counting_update(*a, **kw):
        calls.append((a, kw))
        return real_update(*a, **kw)

    trees.store.update = counting_update
    try:
        out = trees.refute(target, refuter, "the posted hours say six",
                           tree=_RETIRE_TREE, table=_TABLE_RETIRE)
    finally:
        trees.store.update = real_update
    assert len(calls) == 1, f"the retirement must be ONE update, saw {len(calls)}"

    after = _row(target)
    assert out["refuted"] and out["was"] == "hypothesis", out
    assert after["standing"] == "refuted", after["standing"]
    assert after["content"] == before["content"], "content must not move"
    assert after["provenance"]["source"] == before["provenance"]["source"], "birth provenance must not move"
    att = after["provenance"]["attestations"][-1]
    assert att["source"] == "refutation" and att["refuter"] == refuter, att
    assert att["evidence"] == "the posted hours say six" and att["at"], att


def test_the_retirement_door_names_every_lack_in_one_pass():
    target = _land("mondays are for the archive stacks", [0.5, 0.5])
    refuter = _land("the stacks are shut on mondays entirely", [0.4, 0.6], source="correction")
    dead = _land("a claim that will itself be retired", [0.1, 0.9], source="correction")
    trees.refute(dead, refuter, "this one goes first", tree=_RETIRE_TREE, table=_TABLE_RETIRE)

    # Each refusal raises BEFORE any write — the row's whole fingerprint is unmoved.
    before = _fingerprint(target)
    cases = {
        "empty evidence": (target, refuter, "   "),
        "unknown target": ("0" * 16, refuter, "a fine reason"),
        "unknown refuter": (target, "f" * 16, "a fine reason"),
        "self-refutation": (target, target, "a fine reason"),
        "an already-refuted refuter": (target, dead, "a fine reason"),
    }
    for name, (n, r, e) in cases.items():
        msg = _refuses(trees.RefutationRefused, trees.refute, n, r, e,
                       tree=_RETIRE_TREE, table=_TABLE_RETIRE)
        assert "Nothing landed" in msg, f"{name}: the refusal must say nothing landed"
        assert _fingerprint(target) == before, f"{name}: the row moved on a REFUSED call"

    # Crossing honesty, unchanged: a node minted DURING this crossing cannot be the refuter.
    msg = _refuses(trees.RefutationRefused, trees.refute, target, refuter, "a fine reason",
                   tree=_RETIRE_TREE, table=_TABLE, minted_this_crossing=(refuter,))
    assert "crossing honesty" in msg, msg

    # ONE PASS, not one per run: a call wrong in three ways names all three at once.
    msg = _refuses(trees.RefutationRefused, trees.refute, "0" * 16, "f" * 16, "",
                   tree=_RETIRE_TREE, table=_TABLE_RETIRE)
    for expected in ("evidence is empty", "0" * 16, "f" * 16):
        assert expected in msg, f"the door must name {expected!r} in the same pass: {msg}"

    # And the doubled retirement: the first receipt is who the record owes.
    trees.refute(target, refuter, "the stacks are shut", tree=_RETIRE_TREE, table=_TABLE_RETIRE)
    after_first = _fingerprint(target)
    msg = _refuses(trees.RefutationRefused, trees.refute, target, refuter, "again",
                   tree=_RETIRE_TREE, table=_TABLE_RETIRE)
    assert "already refuted" in msg, msg
    assert _fingerprint(target) == after_first, "a doubled retirement overwrote the first receipt"


def test_the_standing_gate_lets_the_signature_through_and_stops_the_guess():
    """cairn/machines/ruling's supersession rule, BORROWED (cited in the charter's entry, never
    imported): a guess does not outvote a signature. The fourth case is Law 9's — no past
    artifact outranks Akien now, and every node is born a hypothesis, so a gate keyed on
    standing ALONE would protect the corpus from its own author."""
    earned_a = _land("an earned claim about opening hours", [0.7, 0.3])
    _make_earned(earned_a)
    guess = _land("a backfilled guess that contradicts it", [0.6, 0.4])   # source llm-backfill

    before = _fingerprint(earned_a)
    msg = _refuses(trees.RefutationRefused, trees.refute, earned_a, guess, "I reckon not",
                   tree=_RETIRE_TREE, table=_TABLE_RETIRE)
    assert "standing gate" in msg and "outvote" in msg, msg
    assert _fingerprint(earned_a) == before, "the earned node moved on a refused call"

    # earned -> earned passes: tenure outvotes tenure.
    earned_b = _land("a second earned claim, later found wrong", [0.3, 0.7])
    _make_earned(earned_b)
    earned_r = _land("an earned refuter with standing of its own", [0.2, 0.8])
    _make_earned(earned_r)
    assert trees.refute(earned_b, earned_r, "measured otherwise",
                        tree=_RETIRE_TREE, table=_TABLE_RETIRE)["was"] == "earned"

    # hypothesis -> hypothesis passes: the gate guards EARNED knowledge, nothing else.
    hyp = _land("an ordinary hypothesis nobody corroborated", [0.55, 0.45])
    hyp_r = _land("another ordinary hypothesis that disagrees", [0.45, 0.55])
    assert trees.refute(hyp, hyp_r, "disagrees on the facts",
                        tree=_RETIRE_TREE, table=_TABLE_RETIRE)["was"] == "hypothesis"

    # LAW 9: a STATED CORRECTION is an input from outside, not the system's own guess —
    # it retires an earned node even though it is itself born a hypothesis.
    earned_c = _land("a third earned claim Akien says is wrong", [0.8, 0.2])
    _make_earned(earned_c)
    said = _land("no, that is not what the charter says", [0.75, 0.25], source="correction")
    out = trees.refute(earned_c, said, "no, that is not what the charter says",
                       tree=_RETIRE_TREE, table=_TABLE_RETIRE)
    assert out["was"] == "earned" and _row(earned_c)["standing"] == "refuted", out


def test_the_borrow_is_cited_not_grafted():
    """Ideas are free and cited; bytes are a graft with a ticket and a proof. The measure
    is the IMPORT, not the word — the module names cairn/machines/ruling in a comment on purpose,
    which is what a citation IS (a grep for the bare word reds on the honest citation)."""
    src = Path(trees.__file__).read_text()
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    assert not any("ruling" in m for m in imported), f"cairn/machines/ruling was grafted: {imported}"
    assert "cairn/machines/ruling" in src, "the borrow must be CITED in the module that composes it"


def _main() -> int:
    checks = [
        test_the_door_refuses_the_untraceable,
        test_vectors_are_physics_at_both_doors,
        test_a_node_lands_and_is_born_a_hypothesis,
        test_a_duplicate_grows_nothing_but_its_provenance_lands,
        test_the_walk_itself_never_decays_a_tenant,
        test_dimension_mismatch_is_refused_not_answered,
        test_nearest_ranks_by_proximity_and_derives_the_path,
        test_trees_do_not_cross,
        test_neighbors_are_derived_and_exclude_self,
        test_tree_state_moves_with_the_tree_and_only_with_it,
        test_no_edge_table_exists,
        test_the_owner_gate_holds_through_the_stack,
        test_crossings_breadcrumb_and_reads_stay_silent,
        test_device_hood_and_the_ordered_surface,
        test_trees_opens_no_door_of_its_own,
        test_a_retirement_is_one_owner_gated_act_that_deletes_nothing,
        test_the_retirement_door_names_every_lack_in_one_pass,
        test_the_standing_gate_lets_the_signature_through_and_stops_the_guess,
        test_the_borrow_is_cited_not_grafted,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — librarian/trees: the untraceable never lands, vectors are physics, "
          "nodes are born hypotheses, a duplicate grows nothing but its provenance lands "
          "as an attestation, the embedding is the path "
          "(edges derived, never stored), trees do not cross, the owner-gate holds, "
          "crossings breadcrumb, a retirement invalidates in ONE owner-gated act "
          "and never deletes, the door names every lack in one pass, the standing gate "
          "stops the guess and lets the signature through, and the module opens no door "
          "of its own")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
