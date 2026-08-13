"""librarian/chat.py — the CHAT verb: the conversational face over the loop and the transducer.

Akien's first-face ruling, 2026-07-27, verbatim: "the current goal is the librarian as
chat bot, learning, and summarizing. learning always and summarizing when asked." The two
halves map onto the spine directly and this module adds NO third mechanism:

  - LEARNING ALWAYS: every conversational turn is one crossing of the core loop
    (``resolve_query``) — always the graph first; a miss backfills the graph and the
    original question resubmits through structure. The chat's memory IS the graph: the
    transcript is runtime state and dies with the process, but what a turn taught the
    tree survives it — which is what makes "he'll already be ready to answer them
    immediately" true across sessions, not just across turns.
  - SUMMARIZING WHEN ASKED: an utterance that asks for a summary routes to the
    transducer (``summarize``) — a dense region rendered into cited prose that lands
    back in the same tree.

AND IT CHATS (Akien, 2026-08-09, after saying hello to a wall of resolution mechanics:
"the intentions say it should be chatting and it's not"). A resolve turn's reply is the
loop's walk ARTICULATED into conversational prose — one generate spent per turn on
articulation, never on routing and never on free facts. The distinction that reconciles
this with facts-from-structure: the loop still ANSWERS (walk, backfill, fold-in,
unchanged), the render only SAYS the answer to a human. The walk rides the render
prompt whole and numbered (the transducer's cache mechanism — same utterance + same
graph replays the cached render), citations are code-built from the [n] marks, a minted
citation refuses loudly, and the loop's whole verdict dict rides the reply as data
(Law 7: a surface may collapse it to a line; the turn record never loses it). The one
clause where chat differs from summarize: ZERO anchors are LEGAL — a greeting grounds
on nothing, and honest smalltalk is conversation, not invention. Reply prose is runtime
state: it never deposits into the tree (only summaries land).

AND IT TAKES CORRECTION (2026-08-10, ticket revision-with-receipts). Refutation is an
INPUT, never a discovery — cosine finds nodes that are ALIKE, and a statement and its
negation are alike, so nothing here goes looking for contradictions. The ``correct:``
prefix carries a stated retirement to ``trees.refute``: the correction is deposited as a
node (so the retirement cites something IN the record) and the named node is marked
``refuted``, keeping its content and its birth provenance. Invalidate, never delete —
a later reader must be able to tell "never known" from "known and retired" (Law 7).

THE ROUTE IS PHYSICS, NOT A GUESSED INTENT. "When asked" is a legible affordance — the
``summarize:`` and ``correct:`` prefixes — never an inference spent classifying the
utterance (Law 1: the resolver is for the novel, and a guessed intent is an unmeasured
hypothesis steering a real host call, Law 3). The surface SAYS the affordances exist;
nobody memorizes them. Routing costs two string comparisons, so a correction can still be
stated with the inference host face-down.

A REFUSAL IS A REPLY, NOT A CRASH. The verbs refuse loudly (``SummaryRefused``,
``BackfillRefused``) and a conversation is a diagnostic surface a human is standing at:
the refusal — raw draft and all, carried whole by the verbs themselves — becomes the
turn's reply, and the session continues. Nothing is swallowed; the breadcrumb records
the refused crossing like any other (Law 7).

ONE UTTERANCE IS ONE QUESTION (v0). Conversation -> questions decomposition stays the
core-loop ticket's filed edge (d) — grow against a measured need, not ahead of it.

Import-pure like the rest of the spine: both seams arrive through the one injected
``resolve`` callable (inference_domain's shape); live wiring in live.py / the librarian's
SHIM (which wakes the device and attaches this face), never here. The chat window itself
is a PANE the base shim class understands — the one web server displays it at the
librarian's own page; there is no chat route and no second server.
"""

from __future__ import annotations

import hashlib

from cairn.devices.librarian.loop import BackfillRefused, resolve_query
from cairn.devices.librarian.summarize import _MARKER, SUMMARY_REGION_K, SummaryRefused, summarize
from cairn.devices.librarian.trees import (NODES, DepositRefused, LibrarianDevice,
                                   RefutationRefused, deposit, refute)

# The affordances that route a turn away from the core loop — stated on the surface,
# matched case-insensitively here. A prefix, not an intent guess: deterministic, free,
# legible. Nothing below spends an inference to decide what an utterance MEANT.
SUMMARIZE_PREFIX = "summarize:"
# Refutation is an INPUT, never a discovery (settled at the /sorted cast): cosine finds
# nodes that are ALIKE, and a statement and its negation are alike, so nothing can go
# looking for contradictions. Somebody has to SAY it, and this is where they say it.
CORRECT_PREFIX = "correct:"
CORRECT_SHAPE = "correct: <node_id> <why it is wrong>"


class ChatRefused(RuntimeError):
    """A turn the chat face cannot honestly take — refused loudly at the caller."""


def _utterance_digest(utterance: str) -> str:
    return hashlib.sha256(utterance.encode("utf-8")).hexdigest()[:12]


def route(utterance: str) -> tuple[str, str]:
    """``(kind, question)`` for one utterance — physics, not a guessed intent. The
    ``summarize:`` prefix routes to the transducer, ``correct:`` to the retirement door,
    each with the remainder as the payload; everything else IS the question and rides the
    core loop. Two string comparisons, zero model calls: an utterance's ROUTE is never
    something the system infers about the person (Law 1, and the reason a correction can
    still be stated with the inference host face-down)."""
    text = utterance.strip()
    low = text.lower()
    if low.startswith(SUMMARIZE_PREFIX):
        return "summarize", text[len(SUMMARIZE_PREFIX):].strip()
    if low.startswith(CORRECT_PREFIX):
        return "correct", text[len(CORRECT_PREFIX):].strip()
    return "resolve", text


def correction_turn(payload: str, *, resolve, tree: str, table: str, conn=None) -> dict:
    """The correction arm: a stated retirement carried to ``trees.refute``.

    ``payload`` is ``<node_id> <why it is wrong>`` — the first whitespace-delimited token
    is the id, the remainder is the evidence. Deterministic split, never a parse the model
    is asked to perform: guessing which node a person meant is exactly the manufactured
    revision this behaviour exists to keep out. A malformed correction is refused with the
    SHAPE it wanted, never with a guessed id.

    The correction itself is deposited as a node before it retires anything, so the
    retirement cites something that is IN the record and a later reader can walk to the
    reason. That deposit is minted this turn, and it is passed to ``refute`` as a
    legitimate refuter anyway: crossing honesty guards against the system manufacturing
    its OWN evidence inside a resolve crossing, and this node is a verbatim record of an
    input that came from outside. The parameter stays on ``refute`` so that a resolve path
    which one day grows a refutation arm cannot quietly cheat.

    Returns the receipt — no articulation, no generate: one embed for the deposit and
    nothing else.
    """
    parts = payload.split(None, 1)
    if len(parts) < 2 or not parts[1].strip():
        raise ChatRefused(
            f"correction: expected {CORRECT_SHAPE!r}, got {payload!r} — "
            "refusing to guess which node was meant. State the node id, then the reason."
        )
    target_id, evidence = parts[0].strip(), parts[1].strip()

    vector = resolve({"kind": "embed", "prompt": evidence})["answer"]["vector"]
    minted = deposit(evidence, vector,
                     {"source": "correction", "retires": target_id},
                     tree=tree, table=table, conn=conn)
    receipt = refute(target_id, minted["node_id"], evidence,
                     tree=tree, table=table, conn=conn)
    return {"retired": receipt, "refuter": minted}


def reply_prompt(utterance: str, walk: list[dict]) -> str:
    """The articulation ask. The walk rides WHOLE and numbered — the transducer's
    Law 1 mechanism, composed: the prompt (hence the cache key) moves exactly when the
    utterance or the graph's walk does, and an unchanged pair replays its cached render
    instead of re-inferring."""
    passages = "\n".join(f"[{i}] {n['content']}" for i, n in enumerate(walk, start=1))
    return (
        "You are the librarian: the conversational face of a library of PASSAGES. "
        "Reply to the REMARK below in natural, direct prose — a short paragraph, "
        "spoken to the person. Any claim about what the library holds must come from "
        "the passages, cited inline as [n]. If the passages do not bear on the remark, "
        "say so plainly and reply in courtesy alone — cite nothing, and claim nothing "
        "about the library's contents. Output prose only.\n\n"
        f"REMARK: {utterance}\n"
        f"PASSAGES:\n{passages}"
    )


def parse_reply(raw: str, walk_size: int) -> tuple[str, list[int]]:
    """The draft's prose and its cited positions, or a loud refusal carrying the raw
    WHOLE — parse_summary's chat-shaped sibling, differing in exactly one clause:
    ZERO anchors are LEGAL. A greeting grounds on nothing, so an unanchored draft is
    honest conversation, not invention; a mark the walk never held stays the minted-
    attribution defect either way. The markdown fence is wrapping, not content."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    text = text.strip()
    if not text:
        raise ChatRefused(
            "chat: the draft renders to nothing — an empty reply is a wall, not a "
            f"conversation. Raw draft, carried whole: {raw!r}")
    marks = [int(n) for group in _MARKER.findall(text) for n in group.split(",")]
    bogus = sorted({m for m in marks if not 1 <= m <= walk_size})
    if bogus:
        raise ChatRefused(
            f"chat: the draft cites {bogus} but the walk holds passages "
            f"[1..{walk_size}] — a citation the walk never held is minted "
            f"attribution. Raw draft, carried whole: {raw!r}")
    return text, sorted(set(marks))


def articulate(utterance: str, verdict: dict, *, resolve) -> dict:
    """A resolve turn's REPLY: the loop's walk rendered into conversational prose —
    one generate spent on ARTICULATION, after the loop has already answered from
    structure. Citations are code-built from the draft's [n] marks against the walk;
    the loop's verdict dict rides the reply untouched under ``loop`` (Law 7: the
    record keeps it whole; a surface may collapse it). Nothing deposits — reply
    prose is runtime state."""
    walk = verdict["nodes"]
    drafted = resolve({"kind": "generate", "prompt": reply_prompt(utterance, walk)})
    prose, cited = parse_reply(drafted["answer"]["text"], len(walk))
    citations = [{"n": i, "node_id": walk[i - 1]["node_id"],
                  "source": walk[i - 1]["provenance"].get("source"),
                  "similarity": walk[i - 1]["similarity"]} for i in cited]
    return {"prose": prose, "citations": citations, "loop": verdict}


def chat_turn(utterance: str, *, resolve, tree: str = "commons", k: int = 5,
              summary_k: int = SUMMARY_REGION_K, table: str = NODES, conn=None,
              dev: LibrarianDevice | None = None) -> dict:
    """One conversational turn. Returns the TURN, whichever way it lands::

        {"utterance": what was said,
         "kind":      "resolve" | "summarize" | "correct" | "refused",
         "reply":     {"prose", "citations", "loop": resolve_query's verdict, whole}
                      | summarize's rendering
                      | {"refusal": the verb's loud refusal, carried whole}}

    The answer always comes from structure — the loop walks, backfills, folds in,
    unchanged; what the reply carries is that answer ARTICULATED: conversational
    prose whose library claims anchor to the walk, with the loop's verdict riding
    beside it as data. A refusal is a legible reply — the conversation survives it.
    """
    if not callable(resolve):
        raise ChatRefused(
            "chat_turn: no resolve seam injected — both verbs (embed, generate) come "
            "through inference_domain.resolve or not at all (sole path).")
    if not isinstance(utterance, str) or not utterance.strip():
        raise ChatRefused(f"chat_turn: utterance must be a non-empty string, got {utterance!r}")

    dev = dev or LibrarianDevice()
    kind, question = route(utterance)
    try:
        if kind == "summarize":
            reply = summarize(question, resolve=resolve, tree=tree, k=summary_k,
                              table=table, conn=conn, dev=dev)
        elif kind == "correct":
            reply = correction_turn(question, resolve=resolve, tree=tree,
                                    table=table, conn=conn)
        else:
            verdict = resolve_query(question, resolve=resolve, tree=tree, k=k,
                                    table=table, conn=conn, dev=dev)
            reply = articulate(question, verdict, resolve=resolve)
    except (SummaryRefused, BackfillRefused, ChatRefused, RefutationRefused,
            DepositRefused) as e:
        # The verb already carried the raw draft whole; here it becomes the reply.
        kind, reply = "refused", {"refusal": str(e)}

    # GATE CONTACT: one conversational crossing — thin, because the loop and the
    # transducer each breadcrumb their own detail; this records the conversation's.
    dev.emit("chat", pointer=_utterance_digest(utterance),
             values={"kind": kind, "tree": tree})
    return {"utterance": utterance, "kind": kind, "reply": reply}


class ChatSession:
    """The chatbot face a surface holds: turns accumulate here, knowledge accumulates
    in the graph. The transcript is RUNTIME state (in-process, instance-space if it
    ever persists); everything durable a conversation produces lives in the tree,
    which is why a dead session loses only its scrollback, never its learning."""

    def __init__(self, *, resolve, tree: str = "commons", k: int = 5,
                 summary_k: int = SUMMARY_REGION_K, table: str = NODES, conn=None,
                 dev: LibrarianDevice | None = None) -> None:
        self._resolve = resolve
        self._tree = tree
        self._k = k
        self._summary_k = summary_k
        self._table = table
        self._conn = conn
        self._dev = dev or LibrarianDevice()
        self._turns: list[dict] = []

    @property
    def dev(self) -> LibrarianDevice:
        return self._dev

    def turn(self, utterance: str) -> dict:
        got = chat_turn(utterance, resolve=self._resolve, tree=self._tree, k=self._k,
                        summary_k=self._summary_k, table=self._table, conn=self._conn,
                        dev=self._dev)
        self._turns.append(got)
        return got

    def page(self) -> dict:
        """The session as DATA for a presentation surface (web_server renders, never
        reaches in): the tree it converses over and the transcript so far."""
        return {"tree": self._tree, "turns": list(self._turns)}
