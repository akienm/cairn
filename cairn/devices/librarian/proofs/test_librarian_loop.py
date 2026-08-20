"""Proof for librarian/loop.py — the core resolve-or-generate loop. Teeth a hollow loop
could not pass:

  - THE GRAPH ANSWERS FIRST: a question the walk already resolves NEVER touches the
    generate verb — the host is not in the answer path (Akien's ruling as physics).
  - THE HOME-FIELD SHAPE IS UNMANUFACTURABLE (ticket the-tenure-loop): a crossing whose
    only floor-clearers are its OWN mints returns the honest "learned", never RESOLVED —
    the 2026-08-09 measured defect (four same-turn mints cited as a resolved walk)
    replayed under proof must fail to reproduce. The mint stays in the walk, labeled.
  - A FIRST TOUCH LEARNS; A LATER CROSSING RESOLVES: the 2026-07-27 resubmit clause
    re-scoped — validation completes when standing structure answers, not same-turn.
  - TENURE IS EARNED, NOT BORN: a cross-question resolution corroborates; the birth
    question's echo is a touch; PROMOTION_THRESHOLD distinct cross-questions write
    standing='earned', read back from the row. A duplicate deposit appends provenance
    without growing the table.
  - DECAY IS LAZY AND SPARES THE CORROBORATED: an aged uncorroborated hypothesis no
    longer counts as evidence (computed from created at read — no clock anywhere);
    one attestation restores it whole.
  - THE LIVELOCK IS BROKEN BY KEY PHYSICS: after a round changes the tree, the next
    backfill prompt carries a DIFFERENT graph-state digest — inference_domain's
    canonicalize maps the two rounds to different cache keys, so 'same request, changed
    graph' is a genuine MISS, not a HIT returning the nodes that just failed.
  - THE PROGRESS GATE HOLDS: a round that grows the tree by nothing terminates LOUDLY —
    "no_progress" when the crossing landed nothing at all, "learned" when earlier
    rounds deposited. A zero-budget crossing is "exhausted".
  - REFUSALS RIDE THE VERDICT: a backfill node the deposit door turns back is carried
    complete in refused_at_door; an unparseable draft refuses loudly with the raw whole.
  - THE THRESHOLD IS VISIBLE: every verdict carries floor + best-among-EVIDENCE — the
    number the floor test actually read (Law 3).
  - CROSSINGS BREADCRUMB, RESOLVED AND UNRESOLVED ALIKE; import purity by AST allowlist.

Seams are FAKES injected in inference_domain's shape — no host; the DB is the real one
through db_domain (nonce table, self-cleaning), as in the trees proof.

Three-table migration (2026-08-19): each test "tree" is its own nonce leaf table; node-level
data (standing, provenance, created) is read from cairn_nodes (NODES_TABLE), not the leaf.

    python3 cairn/devices/librarian/proofs/test_librarian_loop.py     # exit 0 = green
"""

from __future__ import annotations

import ast
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.db_domain import store
from cairn.devices.inference_domain import domain
from cairn.devices.librarian import loop
from cairn.devices.librarian.loop import BackfillRefused, parse_backfill, resolve_query
from cairn.devices.librarian.trees import (NODES_TABLE, OWNER, LibrarianDevice, corroborate,
                                           deposit, node_id_for, refute)

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_PROV = {"source": "proofs/test_librarian_loop.py", "ground": "fixture"}

_TABLES: list[str] = []


def _t(name: str) -> str:
    """Per-test nonce leaf table — each test "tree" IS its own leaf table (three-table design)."""
    t = f"_loop_{name}_{_NONCE}"
    if t not in _TABLES:
        _TABLES.append(t)
    return t


def _node(node_id: str) -> dict:
    """Read a node from the shared cairn_nodes table."""
    return store.read(NODES_TABLE, where="node_id = %s", params=(node_id,))[0]


# Fake embedding space: the query points at [1,0,0]; "near" content lands beside it,
# everything unknown lands far away at [0,1,0] (valid direction, poor cosine).
_NEAR = [0.99, 0.05, 0.0]
_FAR = [0.0, 1.0, 0.0]


def _fresh_librarian() -> LibrarianDevice:
    dev = LibrarianDevice()
    dev.set_diagnostic_receiver(None)
    return dev


def fake_seam(embeds: dict, scripts: list):
    """A resolver seam in inference_domain's shape: embed looks up (default far),
    generate pops the next scripted draft. Records every generate prompt."""
    prompts = []

    def resolve(request):
        if request["kind"] == "embed":
            return {"answer": {"vector": list(embeds.get(request["prompt"], _FAR))},
                    "hit": False}
        prompts.append(request["prompt"])
        if not scripts:
            raise AssertionError("generate called more times than the tooth scripted")
        return {"answer": {"text": scripts.pop(0)}, "hit": False}

    resolve.prompts = prompts
    return resolve


def _refuses(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc as e:
        return str(e)
    raise AssertionError(f"{fn.__name__} must refuse with {exc.__name__} — it did not")


def test_a_refuted_node_stays_present_labelled_and_uncounted():
    """The falsifier the ticket actually turns on: PRESENT, LABELLED, NOT COUNTED.
    A deleted node would also 'fail to count' — that is the hollow build this excludes."""
    tbl = _t("retired")
    wrong = deposit(f"the reading room shuts at four ({_NONCE})", _NEAR, _PROV,
                    tree="retired", table=tbl)["node_id"]
    said = deposit(f"no — the posted hours say six ({_NONCE})", _FAR, {"source": "correction"},
                   tree="retired", table=tbl)["node_id"]
    refute(wrong, said, "the posted hours say six", tree="retired", table=tbl)

    q = "when does the reading room shut"
    seam = fake_seam({q: [1.0, 0.0, 0.0]},
                     scripts=['{"nodes": ["a backfilled node that lands nowhere near"]}'])
    got = resolve_query(q, resolve=seam, tree="retired", table=tbl, max_backfills=1)

    walked = {n["node_id"]: n for n in got["nodes"]}
    assert wrong in walked, "the refuted node must still be PRESENT in the walk, not deleted"
    assert f"the reading room shuts at four ({_NONCE})" in walked[wrong]["content"], "and readable"
    assert walked[wrong]["evidence"] is False, "a refuted node may never count as evidence"
    assert "refuted" in (walked[wrong].get("evidence_why") or ""), \
        f"the label must say WHY: {walked[wrong].get('evidence_why')!r}"
    assert got["verdict"] == "UNRESOLVED", \
        "the only above-floor node was retired — there is nothing left to resolve on"


def test_a_node_earned_then_refuted_is_still_uncounted():
    """The ONE tooth that distinguishes correct clause placement from incorrect: the
    earned pass-through short-circuits, so a refuted-but-previously-earned node would
    come back evidence:True if the refuted clause were placed after it."""
    tbl = _t("earned_then_wrong")
    nid = deposit(f"an earned claim that later turned out wrong ({_NONCE})", _NEAR, _PROV,
                  tree="earned-then-wrong", table=tbl)["node_id"]
    said = deposit(f"that claim does not survive the measurement ({_NONCE})", _FAR,
                   {"source": "correction"}, tree="earned-then-wrong", table=tbl)["node_id"]
    store.update(NODES_TABLE, OWNER, {"standing": "earned"},
                 where="node_id = %s", params=(nid,))
    out = refute(nid, said, "it does not survive the measurement",
                 tree="earned-then-wrong", table=tbl)
    assert out["was"] == "earned", "the fixture must retire a node that HAD earned tenure"

    row = _node(nid)
    walk = [dict(row, similarity=0.99)]
    loop._label_evidence(walk, deposited=[], now=datetime.now(timezone.utc))
    assert walk[0]["evidence"] is False, \
        "a previously-EARNED node that was refuted must not short-circuit to True"
    assert "refuted" in walk[0]["evidence_why"]


def test_the_receipts_cite_only_what_the_record_holds():
    """Akien's 'cite back to changes': the join names the earlier question each acted-on
    node was born from — and 19 of the 78 live rows carry no birth question, so the
    absence is REPORTED, never filled with a plausible invention."""
    tbl = _t("receipts")
    with_q = deposit("a node born of an earlier asking", _NEAR,
                     {**_PROV, "question": "what did they ask before"},
                     tree="receipts", table=tbl)["node_id"]
    without_q = deposit("a library fold that nobody asked for", [0.98, 0.06, 0.0],
                        {"source": "library-fold"}, tree="receipts", table=tbl)["node_id"]

    seam = fake_seam({"a fresh question about the same region": [1.0, 0.0, 0.0]}, scripts=[])
    got = resolve_query("a fresh question about the same region", resolve=seam,
                        tree="receipts", table=tbl)
    assert got["verdict"] == "RESOLVED"
    assert seam.prompts == [], "labelling and receipts add ZERO generates"

    receipts = {r["node_id"]: r for r in got["receipts"]}
    assert with_q in receipts and without_q in receipts, receipts
    assert receipts[with_q]["question"] == "what did they ask before"
    assert receipts[without_q]["question"] is None, \
        "a node with no birth question must come back None, never a manufactured one"
    held = {(_node(nid)["provenance"] or {}).get("question")
            for nid in (with_q, without_q)}
    for r in got["receipts"]:
        assert r["question"] is None or r["question"] in held, f"minted citation: {r}"


def test_the_graph_answers_first_and_the_host_stays_out():
    tbl = _t("warm")
    deposit("the resident node that already answers this", _NEAR, _PROV,
            tree="warm", table=tbl)
    seam = fake_seam({"the question": [1.0, 0.0, 0.0]}, scripts=[])
    got = resolve_query("the question", resolve=seam, tree="warm", table=tbl)
    assert got["verdict"] == "RESOLVED" and got["backfills"] == 0
    assert seam.prompts == [], "a resolved walk must NEVER touch the generate verb"
    assert got["nodes"][0]["content"] == "the resident node that already answers this"
    assert got["best"] >= got["floor"], "the verdict carries its own measurement"


def test_a_first_touch_learns_and_a_later_crossing_resolves():
    tbl = _t("cold")
    q = "a question the cold tree cannot answer"
    seam = fake_seam(
        {q: [1.0, 0.0, 0.0], "the supplied node that grounds it": _NEAR},
        scripts=['{"nodes": ["the supplied node that grounds it", "an unrelated aside"]}'],
    )
    got = resolve_query(q, resolve=seam, tree="cold", table=tbl, max_backfills=1)
    assert got["verdict"] == "UNRESOLVED" and got["reason"] == "learned", \
        "a first touch that only minted is UNRESOLVED-but-learned, never RESOLVED"
    assert len(got["deposited"]) == 2, "the supplied nodes took residence for the future"
    top = got["nodes"][0]
    assert top["node_id"] in got["deposited"] and top["similarity"] >= got["floor"], \
        "the mint IS the best walk hit — exactly the shape that used to manufacture RESOLVED"
    assert top["evidence"] is False, "…and it is labeled out of the evidence, not hidden"
    assert got["best"] is None, "best is best-among-EVIDENCE — nothing counted here"
    rows = [_node(nid) for nid in got["deposited"]]
    assert {r["provenance"]["source"] for r in rows} == {"llm-backfill"}
    assert all(r["standing"] == "hypothesis" for r in rows), "backfilled nodes are hypotheses (Law 3)"

    later = fake_seam({q: [1.0, 0.0, 0.0]}, scripts=[])
    got2 = resolve_query(q, resolve=later, tree="cold", table=tbl)
    assert got2["verdict"] == "RESOLVED" and got2["backfills"] == 0
    assert later.prompts == [], "standing structure answers — the host stays out"
    assert got2["tenure"] == {"corroborated": [], "promoted": []}


def test_the_livelock_is_broken_by_key_physics():
    tbl = _t("tworound")
    q = "a question needing two rounds"
    seam = fake_seam(
        {q: [1.0, 0.0, 0.0], "round two finally grounds it": _NEAR},
        scripts=['{"nodes": ["round one lands but far away"]}',
                 '{"nodes": ["round two finally grounds it"]}'])
    got = resolve_query(q, resolve=seam, tree="tworound", table=tbl, max_backfills=2)
    assert got["verdict"] == "UNRESOLVED" and got["reason"] == "learned" and got["backfills"] == 2
    p1, p2 = seam.prompts
    assert p1 != p2, "a changed graph must change the backfill prompt"
    assert "GRAPH-STATE: empty" in p1 and "GRAPH-STATE: empty" not in p2, \
        "the graph-state digest is what moved"
    k1 = domain.canonicalize({"kind": "generate", "prompt": p1})
    k2 = domain.canonicalize({"kind": "generate", "prompt": p2})
    assert k1 != k2, ("the two rounds must canonicalize to DIFFERENT cache keys — same "
                      "request + changed graph is a MISS, or the loop livelocks on its own cache")


def test_no_progress_terminates_loudly_instead_of_spinning():
    tbl = _t("stuck")
    q = "a question the model cannot ground"
    seam = fake_seam({q: [1.0, 0.0, 0.0]},
                     scripts=['{"nodes": ["the same far node, forever"]}',
                              '{"nodes": ["the same far node, forever"]}'])
    got = resolve_query(q, resolve=seam, tree="stuck", table=tbl)
    assert got["verdict"] == "UNRESOLVED" and got["reason"] == "learned"
    assert got["backfills"] == 2 and len(seam.prompts) == 2
    nid = got["deposited"][0]
    row = _node(nid)
    attests = row["provenance"].get("attestations") or []
    assert len(attests) == 1 and attests[0]["question"] == q, \
        "…but the duplicate's provenance LANDED as an attestation (edge b's switch, flipped)"

    tbl2 = _t("stuck2")
    q2 = "a question whose only draft is refused at the door"
    stuck = fake_seam({q2: [1.0, 0.0, 0.0]}, scripts=['{"nodes": ["tiny"]}'])
    got2 = resolve_query(q2, resolve=stuck, tree="stuck2", table=tbl2)
    assert got2["verdict"] == "UNRESOLVED" and got2["reason"] == "no_progress"
    assert got2["deposited"] == []


def test_exhaustion_is_a_named_verdict():
    tbl = _t("deep")
    deposit("a resident that points the wrong way", _FAR, _PROV, tree="deep", table=tbl)
    q = "a question the budget cannot reach"
    seam = fake_seam({q: [1.0, 0.0, 0.0]}, scripts=[])
    got = resolve_query(q, resolve=seam, tree="deep", table=tbl, max_backfills=0)
    assert got["verdict"] == "UNRESOLVED" and got["reason"] == "exhausted"
    assert got["best"] is not None and got["best"] < got["floor"], \
        "the verdict shows exactly how far short the walk fell"

    q2 = "a question three fresh-but-useless rounds cannot resolve"
    seam2 = fake_seam({q2: [1.0, 0.0, 0.0]},
                      scripts=[f'{{"nodes": ["fresh but far node number {i}"]}}' for i in (1, 2, 3)])
    got2 = resolve_query(q2, resolve=seam2, tree="deep", table=tbl, max_backfills=3)
    assert got2["verdict"] == "UNRESOLVED" and got2["reason"] == "learned"
    assert got2["backfills"] == 3 and len(got2["deposited"]) == 3


def test_door_refusals_ride_the_verdict():
    tbl = _t("mixed")
    q = "a question whose backfill includes an untenable node"
    seam = fake_seam(
        {q: [1.0, 0.0, 0.0], "the one node that lands and grounds it": _NEAR},
        scripts=['{"nodes": ["tiny", "the one node that lands and grounds it"]}'])
    got = resolve_query(q, resolve=seam, tree="mixed", table=tbl, max_backfills=1)
    assert got["verdict"] == "UNRESOLVED" and got["reason"] == "learned"
    assert len(got["refused_at_door"]) == 1 and got["refused_at_door"][0]["content"] == "tiny"
    assert "floor" in got["refused_at_door"][0]["refusal"], "the door's full refusal is carried"


def test_the_home_field_shape_is_unmanufacturable():
    tbl = _t("homefield")
    q = "what are your origins, librarian?"
    echo = "the librarian's origins are whatever the asker just said"
    seam = fake_seam({q: [1.0, 0.0, 0.0], echo: [1.0, 0.0, 0.0]},
                     scripts=[f'{{"nodes": ["{echo}"]}}'])
    got = resolve_query(q, resolve=seam, tree="homefield", table=tbl, max_backfills=1)
    assert got["verdict"] == "UNRESOLVED" and got["reason"] == "learned", \
        "the manufactured resolution of 2026-08-09 must be unmanufacturable"
    assert got["nodes"][0]["similarity"] > 0.99 and got["nodes"][0]["evidence"] is False, \
        "a perfect-cosine same-crossing mint is visible in the walk and counts for nothing"


def test_cross_question_corroboration_promotes_at_threshold():
    tbl = _t("tenure")
    fact = "the standing fact that answers several distinct questions"
    nid = node_id_for(fact)
    deposit(fact, _NEAR, {"source": "llm-backfill", "question": "the birth question"},
            tree="tenure", table=tbl)
    q1, q2 = "a first independent question", "a second independent question"
    embeds = {q1: [1.0, 0.0, 0.0], q2: [1.0, 0.0, 0.0], "the birth question": [1.0, 0.0, 0.0]}

    got1 = resolve_query(q1, resolve=fake_seam(embeds, []), tree="tenure", table=tbl)
    assert got1["verdict"] == "RESOLVED" and got1["tenure"]["corroborated"] == [nid]
    assert got1["tenure"]["promoted"] == [], "one corroboration is not tenure"
    row = _node(nid)
    assert row["standing"] == "hypothesis" and len(row["provenance"]["attestations"]) == 1

    again = resolve_query(q1, resolve=fake_seam(embeds, []), tree="tenure", table=tbl)
    assert again["tenure"] == {"corroborated": [], "promoted": []}

    birth = resolve_query("the birth question", resolve=fake_seam(embeds, []),
                          tree="tenure", table=tbl)
    assert birth["tenure"] == {"corroborated": [], "promoted": []}

    got2 = resolve_query(q2, resolve=fake_seam(embeds, []), tree="tenure", table=tbl)
    assert got2["tenure"]["promoted"] == [nid]
    row = _node(nid)
    assert row["standing"] == "earned", "promotion is a ROW fact, not a narration"
    assert len(row["provenance"]["attestations"]) == loop.PROMOTION_THRESHOLD
    assert row["provenance"]["question"] == "the birth question", "birth provenance survives whole"


def test_lazy_decay_fades_the_uncorroborated_only():
    tbl = _t("fade")
    aged = "an aged shard nobody ever walked back to"
    nid = deposit(aged, _NEAR, {"source": "llm-backfill", "question": "its own birth question"},
                  tree="fade", table=tbl)["node_id"]
    store.update(NODES_TABLE, OWNER,
                 {"created": datetime.now(timezone.utc) - loop.DECAY_HORIZON - timedelta(days=1)},
                 where="node_id = %s", params=(nid,))
    q = "a question the faded shard would have answered"
    embeds = {q: [1.0, 0.0, 0.0]}
    got = resolve_query(q, resolve=fake_seam(embeds, []), tree="fade", table=tbl,
                        max_backfills=0)
    assert got["verdict"] == "UNRESOLVED" and got["reason"] == "exhausted"
    assert got["nodes"][0]["node_id"] == nid and got["nodes"][0]["evidence"] is False, \
        "an uncorroborated hypothesis past the horizon no longer counts as evidence"
    assert got["best"] is None, "the floor test read no evidence at all"

    corroborate(nid, "an independent question that reached it", promote_at=loop.PROMOTION_THRESHOLD,
                tree="fade", table=tbl)
    got2 = resolve_query(q, resolve=fake_seam(embeds, []), tree="fade", table=tbl)
    assert got2["verdict"] == "RESOLVED" and got2["nodes"][0]["evidence"] is True
    assert _node(nid)["standing"] == "earned"


def test_an_unparseable_backfill_is_loud_with_the_raw_whole():
    for bad in ("not json at all", '{"nodes": []}', '{"nodes": ["", "x"]}', '["just", "a", "list"]'):
        msg = _refuses(BackfillRefused, parse_backfill, bad)
        assert bad in msg, "the raw draft rides the refusal whole (first-pass diagnostic)"
    assert parse_backfill('```json\n{"nodes": ["a fenced node"]}\n```') == ["a fenced node"]
    tbl = _t("garbage")
    q = "a question whose draft is garbage"
    seam = fake_seam({q: [1.0, 0.0, 0.0]}, scripts=["utter nonsense"])
    _refuses(BackfillRefused, resolve_query, q, resolve=seam, tree="garbage", table=tbl)


def test_crossings_breadcrumb_resolved_and_unresolved_alike():
    tbl = _t("crumbs")
    dev = _fresh_librarian()
    deposit("the resident node that already answers this", _NEAR, _PROV,
            tree="crumbs", table=tbl)
    resolve_query("the question", resolve=fake_seam({"the question": [1.0, 0.0, 0.0]}, []),
                  tree="crumbs", table=tbl, dev=dev)
    resolve_query("an ungroundable question",
                  resolve=fake_seam({"an ungroundable question": [0.0, 0.0, 1.0]},
                                    ['{"nodes": ["a far node that does not help"]}',
                                     '{"nodes": ["a far node that does not help"]}']),
                  tree="crumbs", table=tbl, dev=dev)
    crumbs = [c for c in dev.held_diagnostics() if c["gate"] == "resolve"]
    assert len(crumbs) == 2, "every loop crossing breadcrumbs — RESOLVED and UNRESOLVED alike"
    assert crumbs[0]["values"]["verdict"] == "RESOLVED"
    assert crumbs[1]["values"]["verdict"] == "UNRESOLVED" and crumbs[1]["values"]["reason"] == "learned"
    assert all(c["values"]["floor"] == loop.RESOLUTION_FLOOR for c in crumbs)


def test_no_seam_no_loop_and_no_empty_questions():
    tbl = _t("noseam")
    _refuses(BackfillRefused, resolve_query, "a question", resolve=None, table=tbl)
    _refuses(BackfillRefused, resolve_query, "   ", resolve=lambda r: r, table=tbl)


def test_loop_opens_no_door_of_its_own():
    allowed = ("__future__", "hashlib", "json", "datetime", "cairn.devices.librarian.trees")
    src = Path(loop.__file__).read_text(encoding="utf-8")
    seen = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            seen.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            seen.append(node.module or "")
    offenders = [m for m in seen if not any(m == p or m.startswith(p + ".") for p in allowed)]
    assert not offenders, (
        f"loop.py imports outside its allowlist: {offenders} — both verbs arrive through "
        "the ONE injected seam; even the DB is reached only via trees (sole-path, Law 4)")


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            for t in _TABLES:
                cur.execute("SELECT 1 FROM information_schema.tables "
                            "WHERE table_name = %s", (t,))
                if cur.fetchone():
                    cur.execute(
                        f'DELETE FROM "{NODES_TABLE}" WHERE node_id IN '
                        f'(SELECT node_id FROM "{t}")')
                    cur.execute(f'DROP TABLE "{t}"')
                cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (t,))
    finally:
        conn.close()


def _main() -> int:
    checks = [
        test_a_refuted_node_stays_present_labelled_and_uncounted,
        test_a_node_earned_then_refuted_is_still_uncounted,
        test_the_receipts_cite_only_what_the_record_holds,
        test_the_graph_answers_first_and_the_host_stays_out,
        test_a_first_touch_learns_and_a_later_crossing_resolves,
        test_the_home_field_shape_is_unmanufacturable,
        test_cross_question_corroboration_promotes_at_threshold,
        test_lazy_decay_fades_the_uncorroborated_only,
        test_the_livelock_is_broken_by_key_physics,
        test_no_progress_terminates_loudly_instead_of_spinning,
        test_exhaustion_is_a_named_verdict,
        test_door_refusals_ride_the_verdict,
        test_an_unparseable_backfill_is_loud_with_the_raw_whole,
        test_crossings_breadcrumb_resolved_and_unresolved_alike,
        test_no_seam_no_loop_and_no_empty_questions,
        test_loop_opens_no_door_of_its_own,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — librarian/loop: the graph answers first, a first touch learns and a "
          "later crossing resolves, the home-field shape is unmanufacturable, tenure is "
          "earned cross-question and read from the row, decay is lazy and spares the "
          "corroborated, the livelock is broken by key physics AND a progress gate, "
          "refusals ride the verdict, the threshold is visible, crossings breadcrumb, "
          "and the loop opens no door of its own")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
