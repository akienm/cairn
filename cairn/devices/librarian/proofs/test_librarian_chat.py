"""Proof for librarian/chat.py — the CHAT verb, the conversational face. Teeth a chatbot
wearing a librarian's charter (the parent ticket's named wrong-shape) could not pass:

  - LEARNING ALWAYS, AND IT CHATS: a turn whose question the graph cannot resolve
    BACKFILLS the graph and says so honestly — under the tenure loop (ticket
    the-tenure-loop, Akien's "persistance!" ruling) a same-turn mint is labeled
    non-evidence, so the FIRST turn is UNRESOLVED-"learned" yet still ARTICULATES:
    conversational prose rendered from the walk, citations code-built from its [n]
    marks, the loop's whole verdict riding the reply as data; the SAME question in a
    LATER turn resolves by walk alone, zero backfills (the chat's memory is the graph,
    not the transcript — validation completes at the later crossing, 2026-08-09).
  - THE ROUTE IS PHYSICS: routing spends NO inference — a resolved turn spends exactly
    ONE generate, the articulation, never a classifier; and the ``summarize:`` prefix
    routes to the transducer deterministically, case-insensitive.
  - NO FREE ANSWERS: a draft citing a passage the walk never held refuses loudly with
    the raw carried whole and becomes a refused TURN; a draft with ZERO anchors is
    LEGAL (a greeting grounds on nothing — the one clause where chat differs from
    summarize); reply prose never deposits into the tree.
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

Three-table migration (2026-08-19): each test "tree" is its own nonce leaf table; node-level
data (standing, provenance, created) is read from cairn_nodes (NODES_TABLE), not the leaf.

    python3 cairn/devices/librarian/proofs/test_librarian_chat.py     # exit 0 = green
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.db_domain import store
from cairn.devices.librarian import chat as chat_module
from cairn.devices.librarian.chat import ChatRefused, ChatSession, chat_turn, parse_reply, route
from cairn.devices.librarian.shim import LibrarianShim
from cairn.devices.librarian.trees import NODES_TABLE, OWNER, LibrarianDevice

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"

_TABLES: list[str] = []


def _t(name: str) -> str:
    """Per-test nonce leaf table — each test "tree" IS its own leaf table (three-table design)."""
    t = f"_chat_{name}_{_NONCE}"
    if t not in _TABLES:
        _TABLES.append(t)
    return t


def _node(node_id: str) -> dict:
    """Read a node from the shared cairn_nodes table."""
    return store.read(NODES_TABLE, where="node_id = %s", params=(node_id,))[0]


def _leaf_count(table: str) -> int:
    """Count leaf rows in a nonce table."""
    return len(store.read(table))


def _fresh_librarian() -> LibrarianDevice:
    dev = LibrarianDevice()
    dev.set_diagnostic_receiver(None)
    return dev


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


def _seed(dev: LibrarianDevice, tree: str, table: str, rows: list[tuple[str, list[float]]]) -> list[str]:
    ids = []
    for content, vector in rows:
        r = dev.deposit(content, vector, {"source": f"seed:{tree}"},
                        tree=tree, table=table)
        ids.append(r["node_id"])
    return ids


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


def test_the_correction_prefix_routes_free_with_the_host_face_down():
    """Refutation is an INPUT. The route to it must cost two string comparisons and no
    model call — a person must be able to say 'that's wrong' when the host is down."""
    assert route("correct: abc123 the hours are six") == ("correct", "abc123 the hours are six")
    assert route("CORRECT:  abc123 the hours are six")[0] == "correct", "case does not gate it"
    assert route("please correct the record")[0] == "resolve", "no NLP guessing"

    assert list(inspect.signature(route).parameters) == ["utterance"], \
        "route must take no resolve seam — a routing decision is never inferred"
    for utterance, kind in (("correct: abc123 why", "correct"),
                            ("summarize: the topic", "summarize"),
                            ("an ordinary question", "resolve")):
        assert route(utterance)[0] == kind, utterance


def test_a_stated_correction_retires_a_node_and_a_malformed_one_refuses_with_the_shape():
    dev = _fresh_librarian()
    tbl = _t("corrected")
    wrong = f"the reading room shuts at four on weekdays, per the old sign ({_NONCE})"
    (nid,) = _seed(dev, "corrected", tbl, [(wrong, [1.0, 0.0, 0.0])])
    seam = fake_seam(["unused — a correction turn spends NO generate"])

    turn = chat_turn(f"correct: {nid} the posted hours say six, not four",
                     resolve=seam, tree="corrected", table=tbl, dev=dev)
    assert turn["kind"] == "correct", turn
    assert seam.prompts == [], "a correction spends one embed and no generate"
    row = _node(nid)
    assert row["standing"] == "refuted" and row["content"] == wrong, \
        "invalidate, never delete — the content stays byte-identical"
    assert row["provenance"]["attestations"][-1]["source"] == "refutation"
    assert turn["reply"]["retired"]["was"] == "hypothesis"
    assert store.read(NODES_TABLE, where="node_id = %s",
                      params=(turn["reply"]["refuter"]["node_id"],))

    turn = chat_turn(f"correct: {nid}", resolve=seam, tree="corrected",
                     table=tbl, dev=dev)
    assert turn["kind"] == "refused", turn
    assert "correct: <node_id>" in turn["reply"]["refusal"], turn["reply"]["refusal"]

    turn = chat_turn(f"correct: {nid} saying it a second time", resolve=seam,
                     tree="corrected", table=tbl, dev=dev)
    assert turn["kind"] == "refused" and "already refuted" in turn["reply"]["refusal"], turn


def test_a_resolved_turn_converses_one_generate_spent_on_articulation():
    dev = _fresh_librarian()
    tbl = _t("warm")
    _seed(dev, "warm", tbl, [(_A, [0.95, 0.05, 0.0])])
    draft = "The record holds exactly that: the anchor fact, stated plainly [1]."
    seam = fake_seam([draft], {_Q: [1.0, 0.0, 0.0]})
    leaves_before = _leaf_count(tbl)
    got = chat_turn(_Q, resolve=seam, tree="warm", table=tbl, dev=dev)
    assert got["kind"] == "resolve" and got["reply"]["prose"] == draft
    loop = got["reply"]["loop"]
    assert loop["verdict"] == "RESOLVED" and loop["backfills"] == 0
    assert loop["nodes"][0]["content"] == _A, \
        "the loop still ANSWERS from structure — the render only SAYS the answer"
    assert [c["n"] for c in got["reply"]["citations"]] == [1]
    assert got["reply"]["citations"][0]["node_id"] == loop["nodes"][0]["node_id"], \
        "citations are code-built against the walk, never model-built"
    assert len(seam.prompts) == 1, \
        "exactly ONE generate — the articulation; none for routing, none for the answer"
    assert f"[1] {_A}" in seam.prompts[0] and _Q in seam.prompts[0], \
        "the walk rides the render prompt whole and numbered — the transducer's cache " \
        "mechanism: same utterance + same graph is a byte-identical prompt"
    assert _leaf_count(tbl) == leaves_before, \
        "reply prose is runtime state — nothing deposits from a chat reply"


def test_learning_always_a_miss_teaches_the_graph_and_the_graph_remembers():
    dev = _fresh_librarian()
    tbl = _t("cold")
    fresh = "the freshly learned fact that grounds the anchor question"
    honest = "I have just learned the freshly learned fact [1] — ask me again."
    spoken = "It comes down to the freshly learned fact [1]."
    seam = fake_seam([json.dumps({"nodes": [fresh]}), json.dumps({"nodes": [fresh]}),
                      honest, spoken],
                     {_Q: [1.0, 0.0, 0.0], fresh: [0.98, 0.02, 0.0]})
    first = chat_turn(_Q, resolve=seam, tree="cold", table=tbl, dev=dev)
    loop = first["reply"]["loop"]
    assert first["kind"] == "resolve" and loop["verdict"] == "UNRESOLVED"
    assert loop["reason"] == "learned" and len(loop["deposited"]) == 1, \
        "the miss TAUGHT the graph — and the verdict says so instead of manufacturing " \
        "a resolution from the turn's own echo (ticket the-tenure-loop)"
    assert loop["nodes"][0]["content"] == fresh and loop["nodes"][0]["evidence"] is False, \
        "the mint rides the walk visible and LABELED — data, never same-turn evidence"
    assert first["reply"]["prose"] == honest, \
        "an honest UNRESOLVED turn still ARTICULATES — the chat converses about learning"
    generates_after_first = len(seam.prompts)

    second = chat_turn(_Q, resolve=seam, tree="cold", table=tbl, dev=dev)
    assert second["reply"]["loop"]["verdict"] == "RESOLVED"
    assert second["reply"]["loop"]["backfills"] == 0
    assert second["reply"]["prose"] == spoken
    assert len(seam.prompts) == generates_after_first + 1, \
        "the same question later is a WALK plus one articulation — the chat's memory " \
        "is the graph (Law 1); only the SAYING is spent again"


def test_the_chat_parse_zero_anchors_legal_minted_refused():
    prose, marks = parse_reply("Hello! What would you like to know?", 3)
    assert marks == [], "a greeting grounds on nothing — zero anchors are LEGAL in chat"
    prose, marks = parse_reply("```\nBoth facts stand [1, 3], one twice [1].\n```", 3)
    assert prose == "Both facts stand [1, 3], one twice [1]." and marks == [1, 3], \
        "the fence is wrapping and comma-grouping anchors — the transducer's discipline"
    msg = _refuses(ChatRefused, parse_reply, "A confident claim [7].", 3)
    assert "minted" in msg and "A confident claim [7]." in msg, \
        "a citation the walk never held refuses loudly with the raw carried whole"
    _refuses(ChatRefused, parse_reply, "```\n```", 3)


def test_a_minted_citation_becomes_a_loud_refused_turn():
    dev = _fresh_librarian()
    tbl = _t("minted")
    _seed(dev, "minted", tbl, [(_A, [0.95, 0.05, 0.0])])
    seam = fake_seam(["A claim the walk never held [9]."], {_Q: [1.0, 0.0, 0.0]})
    got = chat_turn(_Q, resolve=seam, tree="minted", table=tbl, dev=dev)
    assert got["kind"] == "refused" and "minted" in got["reply"]["refusal"], \
        "free-answering dies on the refusal-is-a-reply path — it never lands as prose"
    assert "A claim the walk never held [9]." in got["reply"]["refusal"], \
        "the raw draft rides the refusal whole — first-pass diagnostic (Law 7)"


def test_summarizing_when_asked_returns_cited_prose_that_lands():
    dev = _fresh_librarian()
    tbl = _t("shelfed")
    _seed(dev, "shelfed", tbl, [(_A, [0.95, 0.05, 0.0])])
    draft = "The anchor's why, carried into prose [1]."
    seam = fake_seam([draft], {"the anchor topic": [1.0, 0.0, 0.0]})
    got = chat_turn("summarize: the anchor topic", resolve=seam,
                    tree="shelfed", table=tbl, dev=dev)
    assert got["kind"] == "summarize" and got["reply"]["summary"] == draft
    assert [c["n"] for c in got["reply"]["citations"]] == [1], "citations code-built"
    leaf_nids = [r["node_id"] for r in store.read(tbl)]
    assert any(_node(nid)["provenance"].get("source") == "summary:shelfed"
               for nid in leaf_nids), "the summary landed back in the tree"


def test_a_refusal_is_a_reply_and_the_session_survives_it():
    tbl = _t("vacant")
    seam = fake_seam(["a courteous reply, grounded on nothing"],
                     {_Q: [1.0, 0.0, 0.0], _A: [0.95, 0.05, 0.0]})
    session = ChatSession(resolve=seam, tree="vacant", table=tbl)
    got = session.turn("summarize: anything at all")
    assert got["kind"] == "refused" and "Learn first" in got["reply"]["refusal"], \
        "the verb's loud refusal becomes the turn's legible reply — nothing swallowed"
    assert seam.prompts == [], "the refusal preceded the host"
    _seed(session.dev, "vacant", tbl, [(_A, [0.95, 0.05, 0.0])])
    after = session.turn(_Q)
    assert after["kind"] == "resolve" and after["reply"]["loop"]["verdict"] == "RESOLVED", \
        "the session survived the refusal — a refused turn is a turn, not a crash"
    assert [t["kind"] for t in session.page()["turns"]] == ["refused", "resolve"], \
        "the transcript keeps both, in order"


def test_the_page_is_data_a_surface_can_render():
    dev = _fresh_librarian()
    tbl = _t("paged")
    _seed(dev, "paged", tbl, [(_A, [0.95, 0.05, 0.0])])
    seam = fake_seam(["a spoken line, grounded on nothing"], {_Q: [1.0, 0.0, 0.0]})
    session = ChatSession(resolve=seam, tree="paged", table=tbl, dev=dev)
    session.turn(_Q)
    page = session.page()
    assert page["tree"] == "paged" and len(page["turns"]) == 1
    turn = page["turns"][0]
    assert set(turn) == {"utterance", "kind", "reply"} and turn["utterance"] == _Q
    page["turns"].clear()
    assert len(session.page()["turns"]) == 1, \
        "page() hands out a copy — a surface cannot reach back into the transcript"


def test_the_chat_crossing_breadcrumbs_thin():
    dev = _fresh_librarian()
    tbl = _t("crumbed")
    _seed(dev, "crumbed", tbl, [(_A, [0.95, 0.05, 0.0])])
    seam = fake_seam(["a spoken line, grounded on nothing"], {_Q: [1.0, 0.0, 0.0]})
    chat_turn(_Q, resolve=seam, tree="crumbed", table=tbl, dev=dev)
    crumbs = [c for c in dev.held_diagnostics() if c["gate"] == "chat"]
    assert len(crumbs) == 1
    assert crumbs[0]["pointer"] == hashlib.sha256(_Q.encode("utf-8")).hexdigest()[:12]
    assert crumbs[0]["values"] == {"kind": "resolve", "tree": "crumbed"}, \
        "thin on purpose — the loop and the transducer breadcrumb their own detail"


def test_the_chat_window_is_a_declared_pane():
    dev = _fresh_librarian()
    panes = dev.declared_panes()
    assert panes == [{"kind": "chat", "label": "Chat", "handler": None}], \
        "the window is OFFERED from birth — unattached, its handler is honestly None " \
        "(the shim machinery renders that absent-with-reason, never a missing surface)"
    tbl = _t("paned")
    session = ChatSession(resolve=fake_seam(["a spoken line"]), tree="paned", table=tbl, dev=dev)
    dev.attach_chat(session)
    handler = dev.declared_panes()[0]["handler"]
    assert handler() == session.page(), \
        "attached, the pane's DATA is the session's page — the one web server renders it"


def test_receive_routes_chat_mail_and_refuses_the_rest():
    dev = _fresh_librarian()
    tbl = _t("mailed")
    _seed(dev, "mailed", tbl, [(_A, [0.95, 0.05, 0.0])])
    session = ChatSession(resolve=fake_seam(["a spoken line, grounded on nothing"], {_Q: [1.0, 0.0, 0.0]}),
                          tree="mailed", table=tbl, dev=dev)
    dev.attach_chat(session)
    turn = dev.receive({"sender": "web_server", "to": "librarian", "channel": "chat",
                        "why": "a POST crossed the web surface", "body": {"utterance": _Q}})
    assert turn["kind"] == "resolve" and turn["reply"]["loop"]["verdict"] == "RESOLVED"
    assert session.page()["turns"] == [turn], "the delivered turn landed in the transcript"
    msg = _refuses(ValueError, dev.receive, {"channel": "bogus", "body": {}})
    assert "bogus" in msg, "mail the device cannot process refuses loudly, never vanishes"
    _refuses(RuntimeError, _fresh_librarian().receive,
             {"channel": "chat", "body": {"utterance": _Q}})


def test_the_shim_wakes_the_device_on_demand():
    tbl = _t("woken")
    seam = fake_seam(["a spoken line, grounded on nothing"], {_Q: [1.0, 0.0, 0.0]})
    shim = LibrarianShim(session_factory=lambda dev: ChatSession(
        resolve=seam, tree="woken", table=tbl, dev=dev))
    assert not shim.running, "the shim is the always-on front; the device sleeps"
    page = shim.active_page()
    assert shim.running, "querying the page is a poke — the shim STARTS its device"
    assert [p["kind"] for p in page["panes"]] == ["status", "settings", "chat"], \
        "the woken device's page carries the floor + the declared chat window"
    dev = shim.device()
    _seed(dev, "woken", tbl, [(_A, [0.95, 0.05, 0.0])])
    shim.deliver({"sender": "web_server", "to": "librarian", "channel": "chat",
                  "why": "a POST crossed the web surface", "body": {"utterance": _Q}})
    assert shim.device() is dev, "one wake — every poke after it reaches the SAME device"
    chat_pane = shim.active_page()["panes"][2]
    assert len(chat_pane["data"]["turns"]) == 1, \
        "the delivered turn shows on the page the surface will render"


def test_no_seam_and_no_utterance_refuse():
    tbl = _t("noseam")
    _refuses(ChatRefused, chat_turn, _Q, resolve=None, table=tbl)
    _refuses(ChatRefused, chat_turn, "   ", resolve=fake_seam(["x"]), table=tbl)


def test_the_seam_stamps_the_research_domain_declared_never_inferred():
    """The librarian is the research vertical's first real consumer (ticket
    the-domain-carries-the-inference-side): every request through dual_seam carries
    ``domain='research'`` — a DECLARED fact about who is asking, set by rule at the seam.
    The falsifier is chat tooth 15's guessed-intent defect wearing a new coat: a prompt
    whose content screams another vertical must STILL stamp research, and a caller's own
    declaration must survive (setdefault, never overwrite)."""
    from cairn.devices.inference_domain import domain as domain_module
    from cairn.devices.librarian import live

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
    allowed = ("__future__", "hashlib", "cairn.devices.librarian.loop",
               "cairn.devices.librarian.summarize", "cairn.devices.librarian.trees")
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
        test_the_route_is_physics_not_a_guessed_intent,
        test_the_correction_prefix_routes_free_with_the_host_face_down,
        test_a_stated_correction_retires_a_node_and_a_malformed_one_refuses_with_the_shape,
        test_a_resolved_turn_converses_one_generate_spent_on_articulation,
        test_learning_always_a_miss_teaches_the_graph_and_the_graph_remembers,
        test_the_chat_parse_zero_anchors_legal_minted_refused,
        test_a_minted_citation_becomes_a_loud_refused_turn,
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
    print("green — librarian/chat: the route is physics, a resolved turn CONVERSES with "
          "one generate spent on articulation, a miss teaches the graph and the graph "
          "remembers, zero anchors are legal and minted citations refuse loud, "
          "summarize-when-asked lands cited prose, a refusal is a reply the session "
          "survives, the window is a declared pane whose mail routes through the shim "
          "that wakes the device, and chat opens no door of its own")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
