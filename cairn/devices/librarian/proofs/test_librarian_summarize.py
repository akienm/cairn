"""Proof for librarian/summarize.py — the SUMMARIZE verb, the transducer. Teeth a hollow
transducer could not pass:

  - THE RENDER IS GROUNDED: citations are CODE-BUILT from the walked region — the model
    only marks; every citation traces to a real node with its source and similarity.
  - A draft that anchors to NOTHING (no marks) or cites a passage the region never held
    (a minted citation) is refused loudly, raw carried whole — and nothing deposits.
  - THE SUMMARY DEPOSITS BACK into the same tree, provenance naming the exact nodes it
    rendered + the region's digest — a view over the graph, never a document it forgets;
    a follow-up walk FINDS the summary as structure.
  - THE TRANSDUCER NEVER EATS ITS OWN OUTPUT: the landed summary is excluded from the
    next gather, so the verb is idempotent — same question + same source region builds
    the IDENTICAL render prompt (the cache-key mechanism, pinned) and the deposit-back
    is a duplicate; re-summarizing writes nothing (Law 1).
  - AN EMPTY REGION REFUSES — a summary of nothing is invention; learn first.
  - Depth travels with the artifact; the crossing breadcrumbs; a markdown fence is
    wrapping, not content; import purity by AST allowlist.

The dual seam is a fake in inference_domain's shape (deterministic embeds, scripted
drafts, every generate prompt recorded); the DB is the real one through db_domain
(nonce table, self-cleaning), as in the trees, loop, and library proofs.

    python3 cairn/devices/librarian/proofs/test_librarian_summarize.py     # exit 0 = green
"""

from __future__ import annotations

import ast
import hashlib
import itertools
import os
import pytest
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.db_domain import store
from cairn.devices.librarian import summarize as summarize_module
from cairn.devices.librarian.summarize import (
    SummaryRefused, gather, parse_summary, region_digest, render_prompt, summarize,
)
from cairn.devices.librarian import trees
from cairn.devices.librarian.trees import LibrarianDevice

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLE = f"_summary_{_NONCE}"
_test_seq = itertools.count()


@pytest.fixture(autouse=True)
def _fresh_table():
    """Each test gets its own leaf table to avoid cross-test state in the shared nonce."""
    global _TABLE
    _TABLE = f"_summary_{_NONCE}_{next(_test_seq)}"
    yield
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{_TABLE}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (_TABLE,))
    finally:
        conn.close()


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


def fake_seam(script: list[str], overrides: dict | None = None):
    """Both verbs, one fake door, inference_domain's shape. Embeds are deterministic —
    exact-text overrides for teeth needing controlled geometry, else a nonzero 3-dim
    direction from the content's hash. Generates pop the script (last entry repeats,
    which is what a cache would do for an identical request) and every prompt is
    RECORDED on ``resolve.prompts`` so a tooth can pin cache-key identity."""
    overrides = overrides or {}
    prompts: list[str] = []

    def resolve(request):
        if request["kind"] == "embed":
            text = request["prompt"]
            if text in overrides:
                return {"answer": {"vector": list(overrides[text])}}
            h = hashlib.sha256(text.encode("utf-8")).digest()
            return {"answer": {"vector": [h[0] + 1.0, h[1] + 1.0, h[2] + 1.0]}}
        assert request["kind"] == "generate", f"unexpected kind {request!r}"
        prompts.append(request["prompt"])
        return {"answer": {"text": script[min(len(prompts) - 1, len(script) - 1)]}}

    resolve.prompts = prompts
    return resolve


def _seed(dev: LibrarianDevice, tree: str, rows: list[tuple[str, list[float]]]) -> list[str]:
    ids = []
    for content, vector in rows:
        r = dev.deposit(content, vector, {"source": f"seed:{tree}"},
                        tree=tree, table=_TABLE)
        ids.append(r["node_id"])
    return ids


def _leaf_count() -> int:
    try:
        return len(store.read(_TABLE))
    except Exception:
        return 0


def _refuses(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc as e:
        return str(e)
    raise AssertionError(f"{fn.__name__} must refuse with {exc.__name__} — it did not")


_Q = "what does the settled record say about the anchor topic?"
_A = "the anchor fact, stated plainly and comfortably above the content floor"
_B = "the supporting fact, also stated plainly and above the content floor"
_FAR = "an unrelated fact pointing somewhere else entirely, well above the floor"


def _geometry():
    """Question at [1,0,0]; anchor nearest, support next, the far node orthogonal."""
    return {_Q: [1.0, 0.0, 0.0]}, [
        (_A, [0.95, 0.05, 0.0]),
        (_B, [0.80, 0.20, 0.0]),
        (_FAR, [0.0, 0.0, 1.0]),
    ]


def test_the_transducer_renders_a_cited_summary():
    over, rows = _geometry()
    dev = _fresh_librarian()
    ids = _seed(dev, "render", rows)
    draft = "The anchor fact grounds the answer [1], and the support extends it [2]."
    seam = fake_seam([draft], over)
    got = summarize(_Q, resolve=seam, tree="render", k=3, table=_TABLE, dev=dev)
    assert got["summary"] == draft and got["tree"] == "render"
    assert [c["n"] for c in got["citations"]] == [1, 2], "only what the prose marked"
    assert [c["node_id"] for c in got["citations"]] == ids[:2], \
        "citations are CODE-BUILT from the walked region, in walk order"
    for c in got["citations"]:
        assert c["source"] == "seed:render" and 0.0 < c["similarity"] <= 1.0, \
            "each citation carries its node's own source and measured similarity"


def test_the_summary_deposits_back_and_a_walk_finds_it():
    over, rows = _geometry()
    dev = _fresh_librarian()
    ids = _seed(dev, "landed", rows)
    draft = "One landed line carrying the anchor's why [1]."
    # The landed prose embeds RIGHT AT the question — if it were walkable-only-in-theory
    # this tooth would miss it; a follow-up walk must rank it first.
    seam = fake_seam([draft], {**over, draft: [1.0, 0.0, 0.0]})
    got = summarize(_Q, resolve=seam, tree="landed", k=3, table=_TABLE, dev=dev)
    assert got["duplicate"] is False
    node = store.read(trees.NODES_TABLE, where="node_id = %s", params=(got["node_id"],))[0]
    assert node["content"] == draft and node["standing"] == "hypothesis"
    assert node["provenance"]["source"] == "summary:landed"
    assert node["provenance"]["question"] == _Q
    assert node["provenance"]["nodes"] == [ids[0]], \
        "the deposit-back names the EXACT nodes the prose cited"
    assert node["provenance"]["region_digest"] == got["depth"]["region_digest"]
    walk = dev.nearest([1.0, 0.0, 0.0], k=1, tree="landed", table=_TABLE)
    assert walk[0]["node_id"] == got["node_id"], \
        "a follow-up question walks TO the summary — structure, not a re-render"


def test_the_transducer_never_eats_its_own_output_and_rewrites_nothing():
    over, rows = _geometry()
    dev = _fresh_librarian()
    _seed(dev, "idem", rows)
    draft = "The idempotent line, grounded on the anchor [1]."
    # The summary embeds right at the question — the STRONGEST temptation for the next
    # gather to swallow it. It must be excluded, and the second pass must be identical.
    seam = fake_seam([draft], {**over, draft: [1.0, 0.0, 0.0]})
    first = summarize(_Q, resolve=seam, tree="idem", k=3, table=_TABLE, dev=dev)
    count_after_first = _leaf_count()
    second = summarize(_Q, resolve=seam, tree="idem", k=3, table=_TABLE, dev=dev)
    assert second["depth"]["region_digest"] == first["depth"]["region_digest"], \
        "the landed summary is NOT in the next region — the transducer renders ground only"
    assert seam.prompts[0] == seam.prompts[1], \
        "same question + same source region = the IDENTICAL render prompt (the cache key)"
    assert second["duplicate"] is True and _leaf_count() == count_after_first, \
        "re-summarizing an unchanged region writes nothing (Law 1)"
    region = gather([1.0, 0.0, 0.0], k=6, tree="idem", table=_TABLE, dev=dev)
    assert first["node_id"] not in [n["node_id"] for n in region], \
        "gather excludes summary-sourced nodes even when they rank nearest"


def test_an_empty_region_refuses():
    before = _leaf_count()
    seam = fake_seam(["never rendered"])
    msg = _refuses(SummaryRefused, summarize, _Q, resolve=seam, tree="vacant",
                   k=3, table=_TABLE)
    assert "Learn first" in msg and seam.prompts == [], \
        "nothing to transduce means NO render call — refusal precedes the host"
    assert _leaf_count() == before, "and nothing deposits"


def test_an_unanchored_draft_refuses_loudly():
    over, rows = _geometry()
    dev = _fresh_librarian()
    _seed(dev, "hollow", rows)
    after_seed = _leaf_count()
    raw = "Confident prose that cites nothing at all."
    msg = _refuses(SummaryRefused, summarize, _Q, resolve=fake_seam([raw], over),
                   tree="hollow", k=3, table=_TABLE, dev=dev)
    assert "anchors to nothing" in msg and raw in msg, \
        "the refusal carries the raw draft WHOLE (first-pass diagnostic)"
    assert _leaf_count() == after_seed, "the seeds stand alone — nothing deposited"


def test_a_minted_citation_refuses_loudly():
    over, rows = _geometry()
    dev = _fresh_librarian()
    _seed(dev, "minted", rows)
    after_seed = _leaf_count()
    raw = "A claim resting on a passage that does not exist [7]."
    msg = _refuses(SummaryRefused, summarize, _Q, resolve=fake_seam([raw], over),
                   tree="minted", k=3, table=_TABLE, dev=dev)
    assert "[7]" in msg and "[1..3]" in msg and raw in msg, \
        "the refusal names the minted mark against the region's real range"
    assert _leaf_count() == after_seed, "nothing deposited"


def test_depth_travels_with_the_artifact():
    over, rows = _geometry()
    dev = _fresh_librarian()
    _seed(dev, "depth", rows)
    draft = "A shallow cut, honestly labeled, resting on the anchor [1]."
    got = summarize(_Q, resolve=fake_seam([draft], over), tree="depth", k=2,
                    table=_TABLE, dev=dev)
    assert got["depth"] == {"region": 2, "region_digest": got["depth"]["region_digest"],
                            "tree_nodes": 3, "k": 2}, \
        "reached (2) vs exists (3) — a shallower cut is legible as shallower"
    assert len(got["depth"]["region_digest"]) == 16
    region = gather(over[_Q], k=2, tree="depth", table=_TABLE, dev=dev)
    assert region_digest(region) == got["depth"]["region_digest"], \
        "the digest is recomputable from the region — the ground is checkable later"


def test_a_fence_is_wrapping_not_content():
    prose, cited = parse_summary("```\nThe fenced line still cites [1].\n```", 2)
    assert prose == "The fenced line still cites [1]." and cited == [1]


def test_comma_grouped_marks_are_citations_not_invention():
    """Measured live 2026-07-28: qwen2.5:7b writes [1, 6] — one bracket, two anchors.
    That is grouping (a presentation quirk, like the fence), not an unanchored draft;
    and an out-of-range member of a group is still a minted citation."""
    _prose, cited = parse_summary("The board shows audit results [1, 3] and runs them [2].", 3)
    assert cited == [1, 2, 3], "every member of a grouped mark anchors"
    msg = _refuses(SummaryRefused, parse_summary, "A grouped mint [2, 9].", 3)
    assert "[9]" in msg, "grouping does not launder a mark the region never held"


def test_the_summarize_crossing_breadcrumbs():
    over, rows = _geometry()
    dev = _fresh_librarian()
    _seed(dev, "crumbs", rows)
    draft = "The breadcrumbed line rests on the anchor [1] and its support [2]."
    summarize(_Q, resolve=fake_seam([draft], over), tree="crumbs", k=3,
              table=_TABLE, dev=dev)
    crumbs = [c for c in dev.held_diagnostics() if c["gate"] == "summarize"]
    assert len(crumbs) == 1
    assert crumbs[0]["pointer"] == hashlib.sha256(_Q.encode("utf-8")).hexdigest()[:12]
    assert crumbs[0]["values"] == {"tree": "crumbs", "region": 3, "cited": 2,
                                   "duplicate": False}, \
        "the verb's summary line carries its counts"


def test_no_seam_and_no_question_refuse():
    _refuses(SummaryRefused, summarize, _Q, resolve=None, table=_TABLE)
    _refuses(SummaryRefused, summarize, "   ", resolve=fake_seam(["x"]), table=_TABLE)


def test_the_render_prompt_carries_the_region_whole():
    over, rows = _geometry()
    dev = _fresh_librarian()
    _seed(dev, "whole", rows)
    region = gather(over[_Q], k=3, tree="whole", table=_TABLE, dev=dev)
    prompt = render_prompt(_Q, region)
    for i, n in enumerate(region, start=1):
        assert f"[{i}] {n['content']}" in prompt, \
            "every passage rides numbered and WHOLE — the prompt IS the cache key"
    assert _Q in prompt


def test_summarize_opens_no_door_of_its_own():
    allowed = ("__future__", "hashlib", "re", "cairn.devices.librarian.trees")
    src = Path(summarize_module.__file__).read_text(encoding="utf-8")
    seen = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            seen.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            seen.append(node.module or "")
    offenders = [m for m in seen if not any(m == p or m.startswith(p + ".") for p in allowed)]
    assert not offenders, (
        f"summarize.py imports outside its allowlist: {offenders} — the DB is reached "
        "only through trees and the host only through the injected seam (sole-path, Law 4)")


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
        test_the_transducer_renders_a_cited_summary,
        test_the_summary_deposits_back_and_a_walk_finds_it,
        test_the_transducer_never_eats_its_own_output_and_rewrites_nothing,
        test_an_empty_region_refuses,
        test_an_unanchored_draft_refuses_loudly,
        test_a_minted_citation_refuses_loudly,
        test_depth_travels_with_the_artifact,
        test_a_fence_is_wrapping_not_content,
        test_comma_grouped_marks_are_citations_not_invention,
        test_the_summarize_crossing_breadcrumbs,
        test_no_seam_and_no_question_refuse,
        test_the_render_prompt_carries_the_region_whole,
        test_summarize_opens_no_door_of_its_own,
    ]
    tables_used = []
    try:
        for check in checks:
            global _TABLE
            _TABLE = f"_summary_{_NONCE}_{next(_test_seq)}"
            tables_used.append(_TABLE)
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        conn = store.connect()
        try:
            with conn.cursor() as cur:
                for t in tables_used:
                    cur.execute(f'DROP TABLE IF EXISTS "{t}"')
                    cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (t,))
        finally:
            conn.close()
    print("green — librarian/summarize: citations are code-built and traceable, the "
          "summary lands back in the graph and a walk finds it, the transducer never "
          "eats its own output and rewrites nothing, unanchored and minted drafts refuse "
          "loudly, depth travels with the artifact, and summarize opens no door of its own")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
