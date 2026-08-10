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

    python3 cairn/librarian/proofs/test_librarian_loop.py     # exit 0 = green
"""

from __future__ import annotations

import ast
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.db_domain import store
from cairn.inference_domain import domain
from cairn.librarian import loop
from cairn.librarian.loop import BackfillRefused, parse_backfill, resolve_query
from cairn.librarian.trees import OWNER, LibrarianDevice, corroborate, deposit, node_id_for

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLE = f"_loop_{_NONCE}"
_PROV = {"source": "proofs/test_librarian_loop.py", "ground": "fixture"}

# Fake embedding space: the query points at [1,0,0]; "near" content lands beside it,
# everything unknown lands far away at [0,1,0] (valid direction, poor cosine).
_NEAR = [0.99, 0.05, 0.0]
_FAR = [0.0, 1.0, 0.0]


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


def test_the_graph_answers_first_and_the_host_stays_out():
    deposit("the resident node that already answers this", _NEAR, _PROV,
            tree="warm", table=_TABLE)
    seam = fake_seam({"the question": [1.0, 0.0, 0.0]}, scripts=[])
    got = resolve_query("the question", resolve=seam, tree="warm", table=_TABLE)
    assert got["verdict"] == "RESOLVED" and got["backfills"] == 0
    assert seam.prompts == [], "a resolved walk must NEVER touch the generate verb"
    assert got["nodes"][0]["content"] == "the resident node that already answers this"
    assert got["best"] >= got["floor"], "the verdict carries its own measurement"


def test_a_first_touch_learns_and_a_later_crossing_resolves():
    # THE RE-SCOPED CLAUSE (ticket the-tenure-loop): the mint lands, the crossing says
    # so honestly, and validation completes at the NEXT crossing — through structure.
    q = "a question the cold tree cannot answer"
    seam = fake_seam(
        {q: [1.0, 0.0, 0.0], "the supplied node that grounds it": _NEAR},
        scripts=['{"nodes": ["the supplied node that grounds it", "an unrelated aside"]}'],
    )
    got = resolve_query(q, resolve=seam, tree="cold", table=_TABLE, max_backfills=1)
    assert got["verdict"] == "UNRESOLVED" and got["reason"] == "learned", \
        "a first touch that only minted is UNRESOLVED-but-learned, never RESOLVED"
    assert len(got["deposited"]) == 2, "the supplied nodes took residence for the future"
    top = got["nodes"][0]
    assert top["node_id"] in got["deposited"] and top["similarity"] >= got["floor"], \
        "the mint IS the best walk hit — exactly the shape that used to manufacture RESOLVED"
    assert top["evidence"] is False, "…and it is labeled out of the evidence, not hidden"
    assert got["best"] is None, "best is best-among-EVIDENCE — nothing counted here"
    rows = store.read(_TABLE, where="tree = %s", params=("cold",))
    assert {r["provenance"]["source"] for r in rows} == {"llm-backfill"}
    assert all(r["standing"] == "hypothesis" for r in rows), "backfilled nodes are hypotheses (Law 3)"

    # The LATER crossing: same question, standing structure, zero backfills — RESOLVED.
    later = fake_seam({q: [1.0, 0.0, 0.0]}, scripts=[])
    got2 = resolve_query(q, resolve=later, tree="cold", table=_TABLE)
    assert got2["verdict"] == "RESOLVED" and got2["backfills"] == 0
    assert later.prompts == [], "standing structure answers — the host stays out"
    # The birth-question echo is a TOUCH, not a corroboration — no tenure on self-echoes.
    assert got2["tenure"] == {"corroborated": [], "promoted": []}


def test_the_livelock_is_broken_by_key_physics():
    q = "a question needing two rounds"
    seam = fake_seam(
        {q: [1.0, 0.0, 0.0], "round two finally grounds it": _NEAR},
        scripts=['{"nodes": ["round one lands but far away"]}',
                 '{"nodes": ["round two finally grounds it"]}'])
    got = resolve_query(q, resolve=seam, tree="tworound", table=_TABLE, max_backfills=2)
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
    q = "a question the model cannot ground"
    # Every round re-supplies the same far node: round 1 deposits it (fresh), round 2
    # gets DUPLICATE-only — the progress gate must fire there, not spin to exhaustion.
    # The crossing DID learn (round 1 landed), so the honest reason is "learned".
    seam = fake_seam({q: [1.0, 0.0, 0.0]},
                     scripts=['{"nodes": ["the same far node, forever"]}',
                              '{"nodes": ["the same far node, forever"]}'])
    got = resolve_query(q, resolve=seam, tree="stuck", table=_TABLE)
    assert got["verdict"] == "UNRESOLVED" and got["reason"] == "learned"
    assert got["backfills"] == 2 and len(seam.prompts) == 2
    rows = store.read(_TABLE, where="tree = %s", params=("stuck",))
    assert len(rows) == 1, "the duplicate round grew the table by nothing"
    attests = rows[0]["provenance"].get("attestations") or []
    assert len(attests) == 1 and attests[0]["question"] == q, \
        "…but the duplicate's provenance LANDED as an attestation (edge b's switch, flipped)"

    # A crossing that lands NOTHING at all is the plain progress-gate verdict.
    q2 = "a question whose only draft is refused at the door"
    stuck = fake_seam({q2: [1.0, 0.0, 0.0]}, scripts=['{"nodes": ["tiny"]}'])
    got2 = resolve_query(q2, resolve=stuck, tree="stuck2", table=_TABLE)
    assert got2["verdict"] == "UNRESOLVED" and got2["reason"] == "no_progress"
    assert got2["deposited"] == []


def test_exhaustion_is_a_named_verdict():
    # "exhausted" is the ZERO-LEARNING budget-out: the walk fell short and no backfill
    # was allowed to land anything. With deposits, the honest reason is "learned".
    deposit("a resident that points the wrong way", _FAR, _PROV, tree="deep", table=_TABLE)
    q = "a question the budget cannot reach"
    seam = fake_seam({q: [1.0, 0.0, 0.0]}, scripts=[])
    got = resolve_query(q, resolve=seam, tree="deep", table=_TABLE, max_backfills=0)
    assert got["verdict"] == "UNRESOLVED" and got["reason"] == "exhausted"
    assert got["best"] is not None and got["best"] < got["floor"], \
        "the verdict shows exactly how far short the walk fell"

    q2 = "a question three fresh-but-useless rounds cannot resolve"
    seam2 = fake_seam({q2: [1.0, 0.0, 0.0]},
                      scripts=[f'{{"nodes": ["fresh but far node number {i}"]}}' for i in (1, 2, 3)])
    got2 = resolve_query(q2, resolve=seam2, tree="deep", table=_TABLE, max_backfills=3)
    assert got2["verdict"] == "UNRESOLVED" and got2["reason"] == "learned"
    assert got2["backfills"] == 3 and len(got2["deposited"]) == 3


def test_door_refusals_ride_the_verdict():
    q = "a question whose backfill includes an untenable node"
    seam = fake_seam(
        {q: [1.0, 0.0, 0.0], "the one node that lands and grounds it": _NEAR},
        scripts=['{"nodes": ["tiny", "the one node that lands and grounds it"]}'])
    got = resolve_query(q, resolve=seam, tree="mixed", table=_TABLE, max_backfills=1)
    assert got["verdict"] == "UNRESOLVED" and got["reason"] == "learned"
    assert len(got["refused_at_door"]) == 1 and got["refused_at_door"][0]["content"] == "tiny"
    assert "floor" in got["refused_at_door"][0]["refusal"], "the door's full refusal is carried"


def test_the_home_field_shape_is_unmanufacturable():
    # THE 2026-08-09 REPLAY (the ticket's falsifier, clause 1): an echo mint scoring
    # near-perfect against its own birth question must not read as RESOLVED.
    q = "what are your origins, librarian?"
    echo = "the librarian's origins are whatever the asker just said"
    seam = fake_seam({q: [1.0, 0.0, 0.0], echo: [1.0, 0.0, 0.0]},
                     scripts=[f'{{"nodes": ["{echo}"]}}'])
    got = resolve_query(q, resolve=seam, tree="homefield", table=_TABLE, max_backfills=1)
    assert got["verdict"] == "UNRESOLVED" and got["reason"] == "learned", \
        "the manufactured resolution of 2026-08-09 must be unmanufacturable"
    assert got["nodes"][0]["similarity"] > 0.99 and got["nodes"][0]["evidence"] is False, \
        "a perfect-cosine same-crossing mint is visible in the walk and counts for nothing"


def test_cross_question_corroboration_promotes_at_threshold():
    fact = "the standing fact that answers several distinct questions"
    nid = node_id_for("tenure", fact)
    deposit(fact, _NEAR, {"source": "llm-backfill", "question": "the birth question"},
            tree="tenure", table=_TABLE)
    q1, q2 = "a first independent question", "a second independent question"
    embeds = {q1: [1.0, 0.0, 0.0], q2: [1.0, 0.0, 0.0], "the birth question": [1.0, 0.0, 0.0]}

    got1 = resolve_query(q1, resolve=fake_seam(embeds, []), tree="tenure", table=_TABLE)
    assert got1["verdict"] == "RESOLVED" and got1["tenure"]["corroborated"] == [nid]
    assert got1["tenure"]["promoted"] == [], "one corroboration is not tenure"
    row = store.read(_TABLE, where="node_id = %s", params=(nid,))[0]
    assert row["standing"] == "hypothesis" and len(row["provenance"]["attestations"]) == 1

    # The SAME question again corroborates nothing — distinctness is the count.
    again = resolve_query(q1, resolve=fake_seam(embeds, []), tree="tenure", table=_TABLE)
    assert again["tenure"] == {"corroborated": [], "promoted": []}

    # The birth question's own echo is a touch, never a corroboration.
    birth = resolve_query("the birth question", resolve=fake_seam(embeds, []),
                          tree="tenure", table=_TABLE)
    assert birth["tenure"] == {"corroborated": [], "promoted": []}

    # A SECOND distinct question crosses PROMOTION_THRESHOLD — earned, read from the row.
    got2 = resolve_query(q2, resolve=fake_seam(embeds, []), tree="tenure", table=_TABLE)
    assert got2["tenure"]["promoted"] == [nid]
    row = store.read(_TABLE, where="node_id = %s", params=(nid,))[0]
    assert row["standing"] == "earned", "promotion is a ROW fact, not a narration"
    assert len(row["provenance"]["attestations"]) == loop.PROMOTION_THRESHOLD
    assert row["provenance"]["question"] == "the birth question", "birth provenance survives whole"


def test_lazy_decay_fades_the_uncorroborated_only():
    aged = "an aged shard nobody ever walked back to"
    nid = node_id_for("fade", aged)
    deposit(aged, _NEAR, {"source": "llm-backfill", "question": "its own birth question"},
            tree="fade", table=_TABLE)
    # Back-date the birth PAST the horizon — through the owner's own update face. The
    # assertions below are INVARIANTS (aged-uncorroborated excluded, corroborated
    # restored), never snapshots of a moving clock.
    store.update(_TABLE, OWNER,
                 {"created": datetime.now(timezone.utc) - loop.DECAY_HORIZON - timedelta(days=1)},
                 where="node_id = %s", params=(nid,))
    q = "a question the faded shard would have answered"
    embeds = {q: [1.0, 0.0, 0.0]}
    got = resolve_query(q, resolve=fake_seam(embeds, []), tree="fade", table=_TABLE,
                        max_backfills=0)
    assert got["verdict"] == "UNRESOLVED" and got["reason"] == "exhausted"
    assert got["nodes"][0]["node_id"] == nid and got["nodes"][0]["evidence"] is False, \
        "an uncorroborated hypothesis past the horizon no longer counts as evidence"
    assert got["best"] is None, "the floor test read no evidence at all"

    # ONE attestation restores it whole — corroboration, not age, is what decides.
    corroborate(nid, "an independent question that reached it", promote_at=loop.PROMOTION_THRESHOLD,
                tree="fade", table=_TABLE)
    got2 = resolve_query(q, resolve=fake_seam(embeds, []), tree="fade", table=_TABLE)
    assert got2["verdict"] == "RESOLVED" and got2["nodes"][0]["evidence"] is True
    # …and that resolution was itself the second distinct cross-question: earned.
    assert store.read(_TABLE, where="node_id = %s", params=(nid,))[0]["standing"] == "earned"


def test_an_unparseable_backfill_is_loud_with_the_raw_whole():
    for bad in ("not json at all", '{"nodes": []}', '{"nodes": ["", "x"]}', '["just", "a", "list"]'):
        msg = _refuses(BackfillRefused, parse_backfill, bad)
        assert bad in msg, "the raw draft rides the refusal whole (first-pass diagnostic)"
    assert parse_backfill('```json\n{"nodes": ["a fenced node"]}\n```') == ["a fenced node"]
    q = "a question whose draft is garbage"
    seam = fake_seam({q: [1.0, 0.0, 0.0]}, scripts=["utter nonsense"])
    _refuses(BackfillRefused, resolve_query, q, resolve=seam, tree="garbage", table=_TABLE)


def test_crossings_breadcrumb_resolved_and_unresolved_alike():
    dev = LibrarianDevice()
    deposit("the resident node that already answers this", _NEAR, _PROV,
            tree="crumbs", table=_TABLE)
    resolve_query("the question", resolve=fake_seam({"the question": [1.0, 0.0, 0.0]}, []),
                  tree="crumbs", table=_TABLE, dev=dev)
    # This question points ORTHOGONALLY to everything resident and everything supplied —
    # nothing in the space can clear the floor for it.
    resolve_query("an ungroundable question",
                  resolve=fake_seam({"an ungroundable question": [0.0, 0.0, 1.0]},
                                    ['{"nodes": ["a far node that does not help"]}',
                                     '{"nodes": ["a far node that does not help"]}']),
                  tree="crumbs", table=_TABLE, dev=dev)
    crumbs = [c for c in dev.held_diagnostics() if c["gate"] == "resolve"]
    assert len(crumbs) == 2, "every loop crossing breadcrumbs — RESOLVED and UNRESOLVED alike"
    assert crumbs[0]["values"]["verdict"] == "RESOLVED"
    assert crumbs[1]["values"]["verdict"] == "UNRESOLVED" and crumbs[1]["values"]["reason"] == "learned"
    assert all(c["values"]["floor"] == loop.RESOLUTION_FLOOR for c in crumbs)


def test_no_seam_no_loop_and_no_empty_questions():
    _refuses(BackfillRefused, resolve_query, "a question", resolve=None, table=_TABLE)
    _refuses(BackfillRefused, resolve_query, "   ", resolve=lambda r: r, table=_TABLE)


def test_loop_opens_no_door_of_its_own():
    allowed = ("__future__", "hashlib", "json", "datetime", "cairn.librarian.trees")
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
            cur.execute(f'DROP TABLE IF EXISTS "{_TABLE}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (_TABLE,))
    finally:
        conn.close()


def _main() -> int:
    checks = [
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
