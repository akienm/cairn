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

THE ROUTE IS PHYSICS, NOT A GUESSED INTENT. "When asked" is a legible affordance — the
``summarize:`` prefix — never an inference spent classifying the utterance (Law 1: the
resolver is for the novel, and a guessed intent is an unmeasured hypothesis steering a
real host call, Law 3). The surface SAYS the affordance exists; nobody memorizes it.

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

from cairn.librarian.loop import BackfillRefused, resolve_query
from cairn.librarian.summarize import _MARKER, SUMMARY_REGION_K, SummaryRefused, summarize
from cairn.librarian.trees import NODES, LibrarianDevice

# The affordance that routes a turn to the transducer — stated on the surface, matched
# case-insensitively here. A prefix, not an intent guess: deterministic, free, legible.
SUMMARIZE_PREFIX = "summarize:"


class ChatRefused(RuntimeError):
    """A turn the chat face cannot honestly take — refused loudly at the caller."""


def _utterance_digest(utterance: str) -> str:
    return hashlib.sha256(utterance.encode("utf-8")).hexdigest()[:12]


def route(utterance: str) -> tuple[str, str]:
    """``(kind, question)`` for one utterance — physics, not a guessed intent. The
    ``summarize:`` prefix routes to the transducer with the remainder as the question;
    everything else IS the question and rides the core loop."""
    text = utterance.strip()
    if text.lower().startswith(SUMMARIZE_PREFIX):
        return "summarize", text[len(SUMMARIZE_PREFIX):].strip()
    return "resolve", text


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
         "kind":      "resolve" | "summarize" | "refused",
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
        else:
            verdict = resolve_query(question, resolve=resolve, tree=tree, k=k,
                                    table=table, conn=conn, dev=dev)
            reply = articulate(question, verdict, resolve=resolve)
    except (SummaryRefused, BackfillRefused, ChatRefused) as e:
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
