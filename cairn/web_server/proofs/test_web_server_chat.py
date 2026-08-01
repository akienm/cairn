"""Proof for the librarian's chat window ON the one web server (librarian-chat-surface
ticket, corrected shape 2026-07-28). THERE IS ONLY ONE WEB SERVER IN THE SYSTEM: the
librarian owns a PAGE it displays — its chat window is a pane the base shim class
understands (declared_panes), its shim rides the roster, and a POSTed utterance travels
web_server → shim.deliver → device.receive. No chat route, no injected chat source, no
second door.

No socket, no DB, no host: the shim's session factory is injected (a fake face in
ChatSession's shape), because THIS proof is about the carrying — the librarian's own
teeth live beside the librarian.

Teeth a hollow surface could not pass:
  - THE LIBRARIAN RIDES THE ROSTER like any device; its page carries the CHAT pane
    (transcript, the ask form, the ``summarize:`` affordance SAID, the hidden channel);
    and querying the page WAKES the device through its shim (start-if-not-running).
  - POST DELIVERS THROUGH THE SHIM: the form body is decoded and handed to the device's
    mail door; the new turn renders on the returned page.
  - AN EMPTY UTTERANCE TAKES NO TURN — the surface manufactures no crossing.
  - EVERYTHING THE LIBRARIAN SAYS IS ESCAPED (Law 7 — it is a device like any other).
  - A DYING DELIVERY IS A LEGIBLE 500 with the page still intact — and the crossing's
    breadcrumb records the 500 (the page may collapse, the record may not).
  - AN UNWOKEN FACE IS AN ABSENT PANE, not a missing page; and there is NO second door
    (the old /chat route is an ordinary 404).

Runnable bare:
    python3 cairn/web_server/proofs/test_web_server_chat.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# The trace wire fires on every serve(); a proof run is not a real firing, so its
# records go to a scratch berth — the live denominator stays honest.
import os, tempfile  # noqa: E401
os.environ["CAIRN_LB_TRACE_ROOT"] = tempfile.mkdtemp(prefix="ws-proof-traces-")

from cairn.ground_loop.loop import GroundLoopDevice
from cairn.librarian.shim import LibrarianShim
from cairn.web_server.server import WebServerDevice

_REPLY = {"verdict": "RESOLVED", "reason": None, "best": 0.9123, "floor": 0.65,
          "backfills": 0, "deposited": [],
          "nodes": [{"similarity": 0.9123, "content": "the anchor fact",
                     "standing": "hypothesis"}]}


class _FakeFace:
    """ChatSession's surface shape: ``turn(utterance) -> turn`` + ``page() -> data``."""

    def __init__(self, *, dies=False, reply=None) -> None:
        self.taken: list[str] = []
        self._dies = dies
        self._reply = reply or _REPLY

    def turn(self, utterance: str) -> dict:
        if self._dies:
            raise RuntimeError("the inference host is unreachable")
        self.taken.append(utterance)
        return {"utterance": utterance, "kind": "resolve", "reply": self._reply}

    def page(self) -> dict:
        return {"tree": "library",
                "turns": [{"utterance": u, "kind": "resolve", "reply": self._reply}
                          for u in self.taken]}


def _wired(face=None):
    """The real machinery end to end: a ground loop, the REAL LibrarianShim subscribed
    (its face injected), the ONE web server over the heartbeat that owns the shims."""
    heartbeat = GroundLoopDevice()
    shim = LibrarianShim(session_factory=lambda dev: face)
    heartbeat.subscribe(shim)
    return WebServerDevice(heartbeat, port=8799), shim


def test_the_librarian_rides_the_roster_and_its_page_carries_the_chat_pane():
    face = _FakeFace()
    web, shim = _wired(face)
    assert not shim.running, "before any poke the device sleeps — the shim is the front"
    status, _c, body = web.serve("/device/librarian")
    assert status == 200 and shim.running, \
        "querying the page IS a poke — the shim starts its device if it is not running"
    assert '/device/librarian' in body, "the librarian is in the nav BECAUSE it is on the roster"
    assert 'data-kind="chat"' in body and 'name="utterance"' in body, "the chat pane renders"
    assert 'name="channel" value="chat"' in body, "the form names the device's mail channel"
    assert "summarize:" in body, "the affordance is SAID on the surface, not memorized"
    assert ">Status<" in body and ">Settings<" in body, \
        "the chat pane joins the floor — one page, standard machinery, no special route"


def test_a_post_delivers_through_the_shim_decoded():
    face = _FakeFace()
    web, _shim = _wired(face)
    status, _c, body = web.serve("/device/librarian", method="POST",
                                 body="channel=chat&utterance=what+is+the+anchor%3F")
    assert status == 200
    assert face.taken == ["what is the anchor?"], \
        "the form body reaches the device's face decoded — through shim.deliver, not a route"
    assert "what is the anchor?" in body and "the anchor fact" in body, \
        "the new turn renders on the returned page — the reply is the walk"


def test_an_empty_utterance_takes_no_turn():
    face = _FakeFace()
    web, _shim = _wired(face)
    status, _c, _b = web.serve("/device/librarian", method="POST",
                               body="channel=chat&utterance=++")
    assert status == 200 and face.taken == [], \
        "nothing said, nothing crossed — the surface manufactures no turn"


def test_everything_the_librarian_says_is_escaped():
    hostile = dict(_REPLY, nodes=[{"similarity": 0.9, "standing": "hypothesis",
                                   "content": "<script>alert(1)</script>"}])
    face = _FakeFace(reply=hostile)
    face.turn("say something hostile")
    web, _shim = _wired(face)
    _s, _c, body = web.serve("/device/librarian")
    assert "<script>alert(1)</script>" not in body and "&lt;script&gt;" in body, \
        "a node's content never becomes live markup — the librarian is a device too"


def test_a_dying_delivery_is_a_legible_500_and_the_record_stands():
    web, _shim = _wired(_FakeFace(dies=True))
    status, _c, body = web.serve("/device/librarian", method="POST",
                                 body="channel=chat&utterance=hello")
    assert status == 500, "a dead delivery is a loud 500, not a pretend 200"
    assert "unreachable" in body, "the trouble renders legibly (Law 7 collapse)"
    assert 'name="utterance"' in body, "the page survives — you can retry"
    crumb = [h for h in web.held_diagnostics() if h["gate"] == "serve"][-1]
    assert crumb["values"] == {"status": 500}, \
        "the page collapsed the error into a coherent shape; the breadcrumb did not"


def test_an_unwoken_face_is_an_absent_pane_and_there_is_no_second_door():
    web, _shim = _wired(face=None)  # the factory yields no face — offered but unwired
    status, _c, body = web.serve("/device/librarian")
    assert status == 200 and "absent" in body and "unwired" in body, \
        "no face means an ABSENT chat pane with its reason — never a missing page"
    status, _c, _b = web.serve("/chat")
    assert status == 404, \
        "the old bespoke route is an ordinary 404 — one web server, one door per device PAGE"


def _main() -> int:
    for check in (test_the_librarian_rides_the_roster_and_its_page_carries_the_chat_pane,
                  test_a_post_delivers_through_the_shim_decoded,
                  test_an_empty_utterance_takes_no_turn,
                  test_everything_the_librarian_says_is_escaped,
                  test_a_dying_delivery_is_a_legible_500_and_the_record_stands,
                  test_an_unwoken_face_is_an_absent_pane_and_there_is_no_second_door):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — web_server/chat pane: the librarian rides the roster and its page "
          "carries the chat pane through the STANDARD shim machinery, a page query wakes "
          "the device, POST delivers decoded through shim.deliver, empty says nothing, "
          "every librarian string is escaped, a dying delivery is a legible 500 whose "
          "breadcrumb stands, an unwoken face is absent-with-reason, and there is no "
          "second door")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
