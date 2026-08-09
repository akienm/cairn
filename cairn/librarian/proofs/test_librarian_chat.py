"""Proof for librarian/chat.py — the CHAT verb, the conversational face. Teeth a chatbot
wearing a librarian's charter (the parent ticket's named wrong-shape) could not pass:

  - LEARNING ALWAYS: a turn whose question the graph cannot resolve BACKFILLS the graph
    and answers from STRUCTURE — the reply is the walk, never the generate text; and the
    SAME question in a later turn resolves by walk alone, zero backfills (the chat's
    memory is the graph, not the transcript).
  - THE ROUTE IS PHYSICS: a turn the graph resolves on the first walk spends NO generate
    call at all — no inference is burned classifying intent; and the ``summarize:``
    prefix routes to the transducer deterministically, case-insensitive.
  - SUMMARIZING WHEN ASKED: the summarize turn returns cited prose (citations code-built
    by the transducer) and the summary lands back in the tree.
  - A REFUSAL IS A REPLY: summarize over an empty tree becomes a loud "refused" turn
    carrying the verb's refusal whole — and the SESSION SURVIVES it; the next turn works.
  - The transcript accumulates in order and ``page()`` is DATA a surface can render;
    the chat crossing breadcrumbs thin (the loop and transducer carry their own detail);
    no seam / empty utterance refuse at the caller; import purity by AST allowlist.
  - THE WINDOW IS A SURFACE THE BASE SHIM UNDERSTANDS: the device DECLARES the chat
    pane (absent-with-reason until a face is attached), routes ``chat`` mail to the
    face and refuses every other channel loudly — and the SHIM starts the device if it
    is not running (wake-to-a-poke), attaching the live face at the wake. One web
    server displays this; the librarian owns a page, never a route or a port.

The dual seam is a fake in inference_domain's shape (deterministic embeds, scripted
drafts); the DB is the real one through db_domain (nonce table, self-cleaning), as in
the trees, loop, library, and summarize proofs.

    python3 cairn/librarian/proofs/test_librarian_chat.py     # exit 0 = green
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.db_domain import store
from cairn.librarian import chat as chat_module
from cairn.librarian.chat import ChatRefused, ChatSession, chat_turn, route
from cairn.librarian.shim import LibrarianShim
from cairn.librarian.trees import LibrarianDevice

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLE = f"_chat_{_NONCE}"


def fake_seam(script: list[str], overrides: dict | None = None):
    """Both verbs, one fake door, inference_domain's shape — the summarize proof's
    harness: deterministic embeds (exact-text overrides for controlled geometry, else a
    nonzero 3-dim direction from the content's hash), scripted generates with every
    prompt RECORDED on ``resolve.prompts``."""
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


def _rows(tree: str) -> list[dict]:
    return store.read(_TABLE, where="tree = %s", params=(tree,))


def _refuses(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc as e:
        return str(e)
    raise AssertionError(f"{fn.__name__} must refuse with {exc.__name__} — it did not")


_Q = "what does the settled record say about the anchor topic?"
_A = "the anchor fact, stated plainly and comfortably above the content floor"


def test_the_route_is_physics_not_a_guessed_intent():
    assert route("  what is the anchor?  ") == ("resolve", "what is the anchor?")
    assert route("summarize: the anchor topic") == ("summarize", "the anchor topic")
    assert route("SUMMARIZE:   the anchor topic") == ("summarize", "the anchor topic"), \
        "the prefix is an affordance, not a shibboleth — case does not gate it"
    assert route("please summarize the anchor")[0] == "resolve", \
        "no NLP guessing — only the stated prefix routes; everything else IS the question"


def test_a_resolved_turn_answers_from_structure_and_spends_no_generate():
    dev = LibrarianDevice()
    _seed(dev, "warm", [(_A, [0.95, 0.05, 0.0])])
    seam = fake_seam(["never needed"], {_Q: [1.0, 0.0, 0.0]})
    got = chat_turn(_Q, resolve=seam, tree="warm", table=_TABLE, dev=dev)
    assert got["kind"] == "resolve" and got["reply"]["verdict"] == "RESOLVED"
    assert got["reply"]["nodes"][0]["content"] == _A, "the reply IS the graph's walk"
    assert got["reply"]["backfills"] == 0 and seam.prompts == [], \
        "a warm graph spends NOTHING — no generate for the answer, none for routing"


def test_learning_always_a_miss_teaches_the_graph_and_the_graph_remembers():
    dev = LibrarianDevice()
    fresh = "the freshly learned fact that grounds the anchor question"
    # The graph starts empty; the backfill supplies the node that lets it resolve.
    seam = fake_seam([json.dumps({"nodes": [fresh]})],
                     {_Q: [1.0, 0.0, 0.0], fresh: [0.98, 0.02, 0.0]})
    first = chat_turn(_Q, resolve=seam, tree="cold", table=_TABLE, dev=dev)
    assert first["kind"] == "resolve" and first["reply"]["verdict"] == "RESOLVED"
    assert first["reply"]["backfills"] == 1 and len(first["reply"]["deposited"]) == 1
    assert first["reply"]["nodes"][0]["content"] == fresh, \
        "the answer came from STRUCTURE the turn just taught, not from the generate text"
    generates_after_first = len(seam.prompts)

    second = chat_turn(_Q, resolve=seam, tree="cold", table=_TABLE, dev=dev)
    assert second["reply"]["verdict"] == "RESOLVED" and second["reply"]["backfills"] == 0
    assert len(seam.prompts) == generates_after_first, \
        "the same question later is a WALK — the chat's memory is the graph (Law 1)"


def test_summarizing_when_asked_returns_cited_prose_that_lands():
    dev = LibrarianDevice()
    _seed(dev, "shelfed", [(_A, [0.95, 0.05, 0.0])])
    draft = "The anchor's why, carried into prose [1]."
    seam = fake_seam([draft], {"the anchor topic": [1.0, 0.0, 0.0]})
    got = chat_turn("summarize: the anchor topic", resolve=seam,
                    tree="shelfed", table=_TABLE, dev=dev)
    assert got["kind"] == "summarize" and got["reply"]["summary"] == draft
    assert [c["n"] for c in got["reply"]["citations"]] == [1], "citations code-built"
    assert any(n["provenance"].get("source") == "summary:shelfed"
               for n in _rows("shelfed")), "the summary landed back in the tree"


def test_a_refusal_is_a_reply_and_the_session_survives_it():
    seam = fake_seam(["never rendered"], {_Q: [1.0, 0.0, 0.0], _A: [0.95, 0.05, 0.0]})
    session = ChatSession(resolve=seam, tree="vacant", table=_TABLE)
    got = session.turn("summarize: anything at all")
    assert got["kind"] == "refused" and "Learn first" in got["reply"]["refusal"], \
        "the verb's loud refusal becomes the turn's legible reply — nothing swallowed"
    assert seam.prompts == [], "the refusal preceded the host"
    # The conversation continues: seed the tree through a later turn's walk target.
    _seed(session.dev, "vacant", [(_A, [0.95, 0.05, 0.0])])
    after = session.turn(_Q)
    assert after["kind"] == "resolve" and after["reply"]["verdict"] == "RESOLVED", \
        "the session survived the refusal — a refused turn is a turn, not a crash"
    assert [t["kind"] for t in session.page()["turns"]] == ["refused", "resolve"], \
        "the transcript keeps both, in order"


def test_the_page_is_data_a_surface_can_render():
    dev = LibrarianDevice()
    _seed(dev, "paged", [(_A, [0.95, 0.05, 0.0])])
    seam = fake_seam(["unused"], {_Q: [1.0, 0.0, 0.0]})
    session = ChatSession(resolve=seam, tree="paged", table=_TABLE, dev=dev)
    session.turn(_Q)
    page = session.page()
    assert page["tree"] == "paged" and len(page["turns"]) == 1
    turn = page["turns"][0]
    assert set(turn) == {"utterance", "kind", "reply"} and turn["utterance"] == _Q
    page["turns"].clear()
    assert len(session.page()["turns"]) == 1, \
        "page() hands out a copy — a surface cannot reach back into the transcript"


def test_the_chat_crossing_breadcrumbs_thin():
    dev = LibrarianDevice()
    _seed(dev, "crumbed", [(_A, [0.95, 0.05, 0.0])])
    seam = fake_seam(["unused"], {_Q: [1.0, 0.0, 0.0]})
    chat_turn(_Q, resolve=seam, tree="crumbed", table=_TABLE, dev=dev)
    crumbs = [c for c in dev.held_diagnostics() if c["gate"] == "chat"]
    assert len(crumbs) == 1
    assert crumbs[0]["pointer"] == hashlib.sha256(_Q.encode("utf-8")).hexdigest()[:12]
    assert crumbs[0]["values"] == {"kind": "resolve", "tree": "crumbed"}, \
        "thin on purpose — the loop and the transducer breadcrumb their own detail"


def test_the_chat_window_is_a_declared_pane():
    dev = LibrarianDevice()
    panes = dev.declared_panes()
    assert panes == [{"kind": "chat", "label": "Chat", "handler": None}], \
        "the window is OFFERED from birth — unattached, its handler is honestly None " \
        "(the shim machinery renders that absent-with-reason, never a missing surface)"
    session = ChatSession(resolve=fake_seam(["unused"]), tree="paned", table=_TABLE, dev=dev)
    dev.attach_chat(session)
    handler = dev.declared_panes()[0]["handler"]
    assert handler() == session.page(), \
        "attached, the pane's DATA is the session's page — the one web server renders it"


def test_receive_routes_chat_mail_and_refuses_the_rest():
    dev = LibrarianDevice()
    _seed(dev, "mailed", [(_A, [0.95, 0.05, 0.0])])
    session = ChatSession(resolve=fake_seam(["unused"], {_Q: [1.0, 0.0, 0.0]}),
                          tree="mailed", table=_TABLE, dev=dev)
    dev.attach_chat(session)
    turn = dev.receive({"sender": "web_server", "to": "librarian", "channel": "chat",
                        "why": "a POST crossed the web surface", "body": {"utterance": _Q}})
    assert turn["kind"] == "resolve" and turn["reply"]["verdict"] == "RESOLVED"
    assert session.page()["turns"] == [turn], "the delivered turn landed in the transcript"
    msg = _refuses(ValueError, dev.receive, {"channel": "bogus", "body": {}})
    assert "bogus" in msg, "mail the device cannot process refuses loudly, never vanishes"
    _refuses(RuntimeError, LibrarianDevice().receive,
             {"channel": "chat", "body": {"utterance": _Q}})


def test_the_shim_wakes_the_device_on_demand():
    seam = fake_seam(["unused"], {_Q: [1.0, 0.0, 0.0]})
    shim = LibrarianShim(session_factory=lambda dev: ChatSession(
        resolve=seam, tree="woken", table=_TABLE, dev=dev))
    assert not shim.running, "the shim is the always-on front; the device sleeps"
    page = shim.active_page()
    assert shim.running, "querying the page is a poke — the shim STARTS its device"
    assert [p["kind"] for p in page["panes"]] == ["status", "settings", "chat"], \
        "the woken device's page carries the floor + the declared chat window"
    dev = shim.device()
    _seed(dev, "woken", [(_A, [0.95, 0.05, 0.0])])
    shim.deliver({"sender": "web_server", "to": "librarian", "channel": "chat",
                  "why": "a POST crossed the web surface", "body": {"utterance": _Q}})
    assert shim.device() is dev, "one wake — every poke after it reaches the SAME device"
    chat_pane = shim.active_page()["panes"][2]
    assert len(chat_pane["data"]["turns"]) == 1, \
        "the delivered turn shows on the page the surface will render"


def test_no_seam_and_no_utterance_refuse():
    _refuses(ChatRefused, chat_turn, _Q, resolve=None, table=_TABLE)
    _refuses(ChatRefused, chat_turn, "   ", resolve=fake_seam(["x"]), table=_TABLE)


def test_the_seam_stamps_the_research_domain_declared_never_inferred():
    """The librarian is the research vertical's first real consumer (ticket
    the-domain-carries-the-inference-side): every request through dual_seam carries
    ``domain='research'`` — a DECLARED fact about who is asking, set by rule at the seam.
    The falsifier is chat tooth 15's guessed-intent defect wearing a new coat: a prompt
    whose content screams another vertical must STILL stamp research, and a caller's own
    declaration must survive (setdefault, never overwrite)."""
    from cairn.inference_domain import domain as domain_module
    from cairn.librarian import live

    captured: list[dict] = []
    real = domain_module.resolve

    def capture(request, *, resolver, **kw):
        captured.append(dict(request))
        return {"answer": {"text": "x", "vector": [1.0, 0.0, 0.0]},
                "hit": False, "provenance": {}}

    domain_module.resolve = capture
    try:
        seam = live.dual_seam()
        seam({"kind": "generate",
              "prompt": "please write a python function that reverses a linked list"})
        seam({"kind": "embed", "prompt": "what does the settled record say?"})
        seam({"kind": "generate", "prompt": "x", "domain": "coding"})
    finally:
        domain_module.resolve = real

    assert captured[0]["domain"] == "research", \
        "content that screams another vertical must still stamp research — the domain " \
        "is who is asking, never what the words look like (the guessed-intent defect)"
    assert captured[1]["domain"] == "research", \
        "the stamp rides embeds too — all verbs cross the seam domained"
    assert captured[2]["domain"] == "coding", \
        "a caller's own declaration outranks the seam's default — setdefault, never overwrite"


def test_chat_opens_no_door_of_its_own():
    allowed = ("__future__", "hashlib", "cairn.librarian.loop",
               "cairn.librarian.summarize", "cairn.librarian.trees")
    src = Path(chat_module.__file__).read_text(encoding="utf-8")
    seen = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            seen.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            seen.append(node.module or "")
    offenders = [m for m in seen if not any(m == p or m.startswith(p + ".") for p in allowed)]
    assert not offenders, (
        f"chat.py imports outside its allowlist: {offenders} — the face adds no third "
        "mechanism; it composes the loop and the transducer, nothing else (Law 4)")


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
        test_the_route_is_physics_not_a_guessed_intent,
        test_a_resolved_turn_answers_from_structure_and_spends_no_generate,
        test_learning_always_a_miss_teaches_the_graph_and_the_graph_remembers,
        test_summarizing_when_asked_returns_cited_prose_that_lands,
        test_a_refusal_is_a_reply_and_the_session_survives_it,
        test_the_page_is_data_a_surface_can_render,
        test_the_chat_crossing_breadcrumbs_thin,
        test_the_chat_window_is_a_declared_pane,
        test_receive_routes_chat_mail_and_refuses_the_rest,
        test_the_shim_wakes_the_device_on_demand,
        test_no_seam_and_no_utterance_refuse,
        test_the_seam_stamps_the_research_domain_declared_never_inferred,
        test_chat_opens_no_door_of_its_own,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — librarian/chat: the route is physics, a warm turn spends nothing, a "
          "miss teaches the graph and the graph remembers, summarize-when-asked lands "
          "cited prose, a refusal is a reply the session survives, the window is a "
          "declared pane whose mail routes through the shim that wakes the device, and "
          "chat opens no door of its own")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
