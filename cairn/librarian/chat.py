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
``resolve`` callable (inference_domain's shape); live wiring in live.py / the web_server
daemon, never here.
"""

from __future__ import annotations

import hashlib

from cairn.librarian.loop import BackfillRefused, resolve_query
from cairn.librarian.summarize import SUMMARY_REGION_K, SummaryRefused, summarize
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


def chat_turn(utterance: str, *, resolve, tree: str = "commons", k: int = 5,
              summary_k: int = SUMMARY_REGION_K, table: str = NODES, conn=None,
              dev: LibrarianDevice | None = None) -> dict:
    """One conversational turn. Returns the TURN, whichever way it lands::

        {"utterance": what was said,
         "kind":      "resolve" | "summarize" | "refused",
         "reply":     resolve_query's verdict | summarize's rendering
                      | {"refusal": the verb's loud refusal, carried whole}}

    The answer always comes from structure: a resolve reply is the graph's walk (the
    generate answer is never returned, only folded in), a summarize reply is cited
    prose the graph keeps. A refusal is a legible reply — the conversation survives it.
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
            reply = resolve_query(question, resolve=resolve, tree=tree, k=k,
                                  table=table, conn=conn, dev=dev)
    except (SummaryRefused, BackfillRefused) as e:
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
