"""librarian/summarize.py — the SUMMARIZE verb: the transducer across the storage axis.

Akien's parts inventory, 2026-07-27, catching the omission himself: "oh! summarizing!"
The frame is held-librarian's two_axes: the librarian is the TRANSDUCER — a dense region
of the graph (db, tacit, statistical) rendered into articulated, why-carrying prose
(nameable, shareable). One move, three callers: summarize research, find-the-pattern-in-
a-clump, de-instance for the exchange. Different triggers, same transduction.

THE PHYSICS: a summary is a VIEW over the graph, never a document the graph forgets.

  - CITATIONS ARE CODE-BUILT, NEVER MODEL-BUILT. The region is gathered by the walk; the
    model only MARKS which passages ground which prose (``[n]``). A draft that anchors to
    nothing, or marks a passage the region never held, is refused loudly with the raw
    carried whole — minted citations are fabricated attribution wearing a bibliography.
  - THE SUMMARY DEPOSITS BACK. The rendered prose lands in the SAME tree through the same
    provenance gate, anchored ``{"source": "summary:<tree>", "question", "nodes": [the
    cited ids], "region_digest"}`` — so the summary itself is resolvable structure and a
    follow-up question is a graph walk, not a re-render. ("We can also ask deeper
    questions from [the summary]... and he'll already be ready" — true by structure.)
  - THE TRANSDUCER NEVER EATS ITS OWN OUTPUT. ``gather`` excludes summary-sourced nodes
    from the region — a summary of summaries is a photocopy of a photocopy. This is also
    what makes the verb idempotent: the region rides the render prompt WHOLE, so the
    cache key moves exactly when the source region does — same question + same region is
    a cached render and a duplicate deposit; nothing written, nothing re-inferred (Law 1).
  - DEPTH TRAVELS WITH THE ARTIFACT (Law 3, pre-wiring the by-time verb): every summary
    carries what was reached (region size, its digest) against what exists (tree size),
    so a shallower cut is legible as shallower, never as a different truth.

Import-pure like the rest of the spine: both verbs arrive through the one injected
``resolve`` callable (inference_domain's shape); live wiring in ``live.py``, never here.
"""

from __future__ import annotations

import hashlib
import re

from cairn.librarian.trees import LibrarianDevice, NODES, tree_state

# The region a summary renders: the k nearest source nodes around the question. A labeled
# guess (n=0 live summaries at pick time); tunes against real use. Multi-hop expansion
# via neighbors() is a filed edge — grow against need.
SUMMARY_REGION_K = 8

# A citation mark: [3] — and the comma-grouped form [1, 6] the drafting model actually
# produces (measured live 2026-07-28: a genuinely anchored draft was refused as unanchored
# under the single-number pattern). Like the markdown fence, grouping is a presentation
# quirk, not content: [1, 6] anchors to passages 1 and 6.
_MARKER = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")


class SummaryRefused(RuntimeError):
    """A summary the transducer cannot honestly stand behind — refused loudly, raw whole."""


def _question_digest(question: str) -> str:
    return hashlib.sha256(question.encode("utf-8")).hexdigest()[:12]


def region_digest(region: list[dict]) -> str:
    """The region's fingerprint: same members, same digest. This is what the deposited
    summary's provenance carries — the exact ground it rendered, checkable later."""
    ids = sorted(n["node_id"] for n in region)
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()[:16]


def gather(question_vector, *, k: int = SUMMARY_REGION_K, tree: str = "commons",
           table: str = NODES, conn=None, dev: LibrarianDevice | None = None) -> list[dict]:
    """The dense region around a question: the k nearest SOURCE nodes by walk.

    Summary-sourced nodes are excluded — the transducer renders ground, not its own
    prior renderings. (The walk over-fetches to keep the region at k after the filter;
    a tree so summary-heavy that k source nodes cannot be found returns what there is.)
    """
    dev = dev or LibrarianDevice()
    walk = dev.nearest(question_vector, k=2 * k, tree=tree, table=table, conn=conn)
    source = [n for n in walk
              if not str(n["provenance"].get("source", "")).startswith("summary:")]
    return source[:k]


def render_prompt(question: str, region: list[dict]) -> str:
    """The transduction ask. The region rides WHOLE and numbered — which IS the Law 1
    mechanism here: the prompt (hence the cache key) moves exactly when the region does,
    and an unchanged region replays its cached render instead of re-inferring."""
    passages = "\n".join(f"[{i}] {n['content']}" for i, n in enumerate(region, start=1))
    return (
        "Distill the PASSAGES below into a short, articulated summary that answers the "
        "REQUEST — carry the WHY, not just the what. Use ONLY the passages; after each "
        "claim, cite the passage(s) grounding it inline as [n]. Output prose only.\n\n"
        f"REQUEST: {question}\n"
        f"PASSAGES:\n{passages}"
    )


def parse_summary(raw: str, region_size: int) -> tuple[str, list[int]]:
    """The draft's prose and its cited positions, or a loud refusal carrying the raw
    WHOLE (first-pass diagnostic). Two ways to fail the contract: anchoring to nothing
    (no markers — prose the region cannot vouch for), and marking a passage the region
    never held (a minted citation). One tolerated presentation quirk, as everywhere:
    a markdown fence is wrapping, not content."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    text = text.strip()
    marks = [int(n) for group in _MARKER.findall(text) for n in group.split(",")]
    if not text or not marks:
        raise SummaryRefused(
            "summarize: the draft anchors to nothing — no [n] citation marks a passage, "
            "so no line of it can be traced to the region (prose without ground is "
            f"invention). Raw draft, carried whole: {raw!r}")
    bogus = sorted({m for m in marks if not 1 <= m <= region_size})
    if bogus:
        raise SummaryRefused(
            f"summarize: the draft cites {bogus} but the region holds passages "
            f"[1..{region_size}] — a citation the region never held is minted "
            f"attribution. Raw draft, carried whole: {raw!r}")
    return text, sorted(set(marks))


def summarize(question: str, *, resolve, tree: str = "commons",
              k: int = SUMMARY_REGION_K, table: str = NODES, conn=None,
              dev: LibrarianDevice | None = None) -> dict:
    """One transduction: dense region in, why-carrying prose out, the graph keeping both.

    Returns::

        {"summary":   the rendered prose, citation marks intact,
         "citations": code-built — [{"n", "node_id", "source", "similarity"}], only
                      what the prose actually marked, each traceable to a real node,
         "depth":     {"region", "region_digest", "tree_nodes", "k"} — reached vs exists,
         "node_id", "duplicate": the deposit-back (a re-summarize writes nothing),
         "question", "tree"}

    An empty region refuses — there is nothing to transduce, and a summary of nothing
    would be pure invention; learn first. The deposit door's judgment outranks the
    render's enthusiasm: a refusal there propagates loud, it is never swallowed.
    """
    if not callable(resolve):
        raise SummaryRefused(
            "summarize: no resolve seam injected — both verbs (embed, generate) come "
            "through inference_domain.resolve or not at all (sole path).")
    if not isinstance(question, str) or not question.strip():
        raise SummaryRefused(f"summarize: question must be a non-empty string, got {question!r}")

    dev = dev or LibrarianDevice()
    embed = lambda text: resolve({"kind": "embed", "prompt": text})["answer"]["vector"]

    region = gather(embed(question), k=k, tree=tree, table=table, conn=conn, dev=dev)
    if not region:
        raise SummaryRefused(
            f"summarize: tree {tree!r} holds no source region for this question — "
            "nothing to transduce; a summary of nothing is invention. Learn first.")
    rdigest = region_digest(region)

    drafted = resolve({"kind": "generate", "prompt": render_prompt(question, region)})
    prose, cited = parse_summary(drafted["answer"]["text"], len(region))
    citations = [{"n": i, "node_id": region[i - 1]["node_id"],
                  "source": region[i - 1]["provenance"].get("source"),
                  "similarity": region[i - 1]["similarity"]} for i in cited]

    state = tree_state(tree, table=table, conn=conn)
    depth = {"region": len(region), "region_digest": rdigest,
             "tree_nodes": state["nodes"], "k": k}

    # THE DEPOSIT-BACK: the summary becomes structure in the same tree it viewed, its
    # provenance naming the exact nodes it rendered — never a document the graph forgets.
    landed = dev.deposit(
        prose, embed(prose),
        {"source": f"summary:{tree}", "question": question,
         "nodes": [c["node_id"] for c in citations], "region_digest": rdigest},
        tree=tree, table=table, conn=conn)

    # GATE CONTACT: one transduction, rendered and landed (or found already landed).
    dev.emit("summarize", pointer=_question_digest(question),
             values={"tree": tree, "region": len(region), "cited": len(citations),
                     "duplicate": landed["duplicate"]})
    return {"summary": prose, "citations": citations, "depth": depth,
            "node_id": landed["node_id"], "duplicate": landed["duplicate"],
            "question": question, "tree": tree}
