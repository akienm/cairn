"""Proof for the web_server's /chat route — the librarian's conversation carried by the
surface (librarian-chat-surface ticket). No socket, no DB, no host: the chat source is a
fake in ChatSession's shape (``turn`` + ``page``), because THIS proof is about the
carrying, not the librarian — the librarian's own teeth live beside the librarian.

Teeth a hollow surface could not pass:
  - NO SOURCE IS A LOUD 404: an unwired chat says why, in a coherent shape, nav intact.
  - GET RENDERS THE CONVERSATION: transcript in order, the ask form, the ``summarize:``
    affordance SAID on the page — and the nav carries the 📚 entry only when wired.
  - POST TAKES A TURN: the form body is decoded (percent-encoding and all) and handed to
    the session's ``turn``; the new turn renders on the returned page.
  - AN EMPTY UTTERANCE TAKES NO TURN — the surface does not manufacture a crossing.
  - EVERYTHING THE LIBRARIAN SAYS IS ESCAPED: a reply carrying ``<script>`` renders as
    TEXT (Law 7 — same discipline as every device string).
  - A TURN THAT DIES IS A LEGIBLE 500 with the conversation still on screen — and the
    crossing's breadcrumb records the 500 (the page may collapse, the record may not).

Runnable bare:
    python3 cairn/web_server/proofs/test_web_server_chat.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.ground_loop.loop import GroundLoopDevice
from cairn.web_server.server import WebServerDevice


class _ChatSource:
    """ChatSession's surface shape: ``turn(utterance) -> turn`` + ``page() -> data``."""

    def __init__(self, *, dies=False, reply=None) -> None:
        self.taken: list[str] = []
        self._dies = dies
        self._reply = reply or {"verdict": "RESOLVED", "reason": None, "best": 0.9123,
                                "floor": 0.65, "backfills": 0, "deposited": [],
                                "nodes": [{"similarity": 0.9123, "content": "the anchor fact",
                                           "standing": "hypothesis"}]}

    def turn(self, utterance: str) -> dict:
        if self._dies:
            raise RuntimeError("the inference host is unreachable")
        self.taken.append(utterance)
        return {"utterance": utterance, "kind": "resolve", "reply": self._reply}

    def page(self) -> dict:
        return {"tree": "library",
                "turns": [{"utterance": u, "kind": "resolve", "reply": self._reply}
                          for u in self.taken]}


def _wired(chat=None):
    return WebServerDevice(GroundLoopDevice(), chat_source=chat, port=8799)


def test_no_source_is_a_loud_404_and_no_nav_entry():
    web = _wired(chat=None)
    status, _c, body = web.serve("/chat")
    assert status == 404, "an unwired chat is a loud 404, not a pretend conversation"
    assert "not wired" in body, "the 404 says why, coherently (Law 7)"
    assert "📚 Librarian" not in body, "the nav offers no door that does not exist"


def test_get_renders_the_conversation_and_the_affordance():
    src = _ChatSource()
    src.turn("what is the anchor?")
    web = _wired(chat=src)
    status, _c, body = web.serve("/chat")
    assert status == 200
    assert "📚 Librarian" in body, "the nav carries the chat entry when wired"
    assert "what is the anchor?" in body and "the anchor fact" in body, \
        "the transcript renders — utterance and the walk's content"
    assert "RESOLVED" in body and "0.65" in body, "the verdict shows its floor (Law 3)"
    assert 'name="utterance"' in body and "summarize:" in body, \
        "the ask form is there and the summarize: affordance is SAID, not memorized"


def test_post_takes_a_turn_with_the_body_decoded():
    src = _ChatSource()
    web = _wired(chat=src)
    status, _c, body = web.serve("/chat", method="POST",
                                 body="utterance=what+is+the+anchor%3F")
    assert status == 200
    assert src.taken == ["what is the anchor?"], \
        "the form body reaches the session decoded — plus-spaces and percent-escapes"
    assert "what is the anchor?" in body, "the new turn renders on the returned page"


def test_an_empty_utterance_takes_no_turn():
    src = _ChatSource()
    web = _wired(chat=src)
    status, _c, _b = web.serve("/chat", method="POST", body="utterance=++")
    assert status == 200 and src.taken == [], \
        "nothing said, nothing crossed — the surface manufactures no turn"


def test_everything_the_librarian_says_is_escaped():
    hostile = {"verdict": "RESOLVED", "reason": None, "best": 0.9, "floor": 0.65,
               "backfills": 0, "deposited": [],
               "nodes": [{"similarity": 0.9, "content": "<script>alert(1)</script>",
                          "standing": "hypothesis"}]}
    src = _ChatSource(reply=hostile)
    src.turn("say something hostile")
    web = _wired(chat=src)
    _s, _c, body = web.serve("/chat")
    assert "<script>alert(1)</script>" not in body and "&lt;script&gt;" in body, \
        "a node's content never becomes live markup — the librarian is a device too"


def test_a_dying_turn_is_a_legible_500_and_the_record_stands():
    web = _wired(chat=_ChatSource(dies=True))
    status, _c, body = web.serve("/chat", method="POST", body="utterance=hello")
    assert status == 500, "a dead turn is a loud 500, not a pretend 200"
    assert "unreachable" in body, "the trouble renders legibly (Law 7 collapse)"
    assert 'name="utterance"' in body, "the conversation page survives — you can retry"
    crumb = [h for h in web.held_diagnostics() if h["gate"] == "serve"][-1]
    assert crumb["values"] == {"status": 500}, \
        "the page collapsed the error into a coherent shape; the breadcrumb did not"


def _main() -> int:
    for check in (test_no_source_is_a_loud_404_and_no_nav_entry,
                  test_get_renders_the_conversation_and_the_affordance,
                  test_post_takes_a_turn_with_the_body_decoded,
                  test_an_empty_utterance_takes_no_turn,
                  test_everything_the_librarian_says_is_escaped,
                  test_a_dying_turn_is_a_legible_500_and_the_record_stands):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — web_server/chat: an unwired chat 404s loudly, GET renders the "
          "conversation with the affordance said, POST hands the decoded utterance to "
          "the session, empty says nothing, every librarian string is escaped, and a "
          "dying turn is a legible 500 whose breadcrumb stands")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
