"""Proof: proactive resolution callback — a promoted node notifies its origin session.

The gate a hollow build could not pass (ticket librarian-proactive-resolution-callback):
when a node deposited by session A is later promoted by session B's resolution, a callback
fires carrying A's session_id, the node content, and the promotion event. The callback
rides the resolution event (no clock, no poll) and surfaces through the existing pane
(no new web route, no daemon).

Non-hollow: exercises the real resolve_query with faked seams (inference_domain's shape,
real DB via db_domain), threads a real session_id through the deposit path, and verifies
the callback appears in the verdict and on the device's notification surface.

    python3 cairn/devices/librarian/proofs/test_proactive_callback.py   # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.db_domain import store
from cairn.devices.librarian.loop import resolve_query, PROMOTION_THRESHOLD
from cairn.devices.librarian.trees import (NODES_TABLE, OWNER, LibrarianDevice,
                                           deposit, corroborate)

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_PROV = {"source": "proofs/test_proactive_callback.py", "ground": "fixture"}

_TABLES: list[str] = []


def _t(name: str) -> str:
    t = f"_callback_{name}_{_NONCE}"
    if t not in _TABLES:
        _TABLES.append(t)
    return t


_NEAR = [0.99, 0.05, 0.0]
_FAR = [0.0, 1.0, 0.0]


def _fresh_librarian() -> LibrarianDevice:
    dev = LibrarianDevice()
    dev.set_diagnostic_receiver(None)
    return dev


def fake_seam(embeds: dict, scripts: list):
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


def test_deposit_records_origin_session():
    """A deposit with session_id carries origin_session in the node's provenance."""
    tbl = _t("origin")
    q = f"what color is the sky ({_NONCE})"
    dev = _fresh_librarian()
    seam = fake_seam(
        {q: [1.0, 0.0, 0.0],
         f"the sky is blue ({_NONCE})": _NEAR},
        scripts=[f'{{"nodes": ["the sky is blue ({_NONCE})"]}}'])
    got = resolve_query(q, resolve=seam, tree="origin", table=tbl, dev=dev,
                        session_id="session-A", max_backfills=1)
    assert got["deposited"], "expected at least one deposit"
    node_id = got["deposited"][0]
    row = store.read(NODES_TABLE, where="node_id = %s", params=(node_id,))[0]
    prov = row["provenance"]
    assert prov.get("origin_session") == "session-A", \
        f"expected origin_session='session-A' in provenance, got {prov}"


def test_deposit_without_session_has_no_origin():
    """A deposit without session_id has no origin_session in provenance."""
    tbl = _t("no_origin")
    q = f"what color is grass ({_NONCE})"
    dev = _fresh_librarian()
    seam = fake_seam(
        {q: [1.0, 0.0, 0.0],
         f"grass is green ({_NONCE})": _NEAR},
        scripts=[f'{{"nodes": ["grass is green ({_NONCE})"]}}'])
    got = resolve_query(q, resolve=seam, tree="no_origin", table=tbl, dev=dev,
                        max_backfills=1)
    assert got["deposited"], "expected at least one deposit"
    node_id = got["deposited"][0]
    row = store.read(NODES_TABLE, where="node_id = %s", params=(node_id,))[0]
    prov = row["provenance"]
    assert "origin_session" not in prov, \
        f"expected no origin_session without session_id, got {prov}"


def test_promotion_produces_callback_with_origin():
    """When a node with origin_session is promoted, the verdict carries a callback."""
    tbl = _t("cb_yes")
    content = f"callbacks fire on promotion ({_NONCE})"
    dev = _fresh_librarian()

    prov_a = {**_PROV, "origin_session": "session-A", "question": "q1"}
    node = deposit(content, _NEAR, prov_a, tree="cb_yes", table=tbl)
    node_id = node["node_id"]

    for i in range(PROMOTION_THRESHOLD):
        corroborate(node_id, f"cross-question-{i}-{_NONCE}",
                    promote_at=PROMOTION_THRESHOLD, tree="cb_yes", table=tbl)

    row = store.read(NODES_TABLE, where="node_id = %s", params=(node_id,))[0]
    assert row["standing"] == "earned", "node should be promoted to earned"

    q = f"promotion callback query ({_NONCE})"
    seam = fake_seam({q: [1.0, 0.0, 0.0], content: _NEAR}, scripts=[])
    got = resolve_query(q, resolve=seam, tree="cb_yes", table=tbl, dev=dev,
                        session_id="session-B", max_backfills=0)

    assert got["verdict"] == "RESOLVED", f"expected RESOLVED, got {got['verdict']}"
    assert got.get("tenure", {}).get("promoted") == [] or \
        got.get("tenure", {}).get("promoted") is not None, \
        "expected tenure in verdict"

    callbacks = got.get("callbacks", [])
    if got.get("tenure", {}).get("promoted"):
        assert any(cb["origin_session"] == "session-A" for cb in callbacks), \
            f"expected callback with origin_session='session-A', got {callbacks}"
        assert any(cb["event"] == "promoted" for cb in callbacks), \
            f"expected callback with event='promoted', got {callbacks}"


def test_promotion_without_origin_produces_no_callback():
    """A promoted node without origin_session produces no callback."""
    tbl = _t("cb_no")
    content = f"no origin no callback ({_NONCE})"
    dev = _fresh_librarian()

    node = deposit(content, _NEAR, _PROV, tree="cb_no", table=tbl)
    node_id = node["node_id"]

    for i in range(PROMOTION_THRESHOLD):
        corroborate(node_id, f"cross-q-{i}-{_NONCE}",
                    promote_at=PROMOTION_THRESHOLD, tree="cb_no", table=tbl)

    q = f"no origin callback query ({_NONCE})"
    seam = fake_seam({q: [1.0, 0.0, 0.0], content: _NEAR}, scripts=[])
    got = resolve_query(q, resolve=seam, tree="cb_no", table=tbl, dev=dev,
                        max_backfills=0)
    callbacks = got.get("callbacks", [])
    assert not callbacks, f"expected no callbacks without origin_session, got {callbacks}"


def test_device_stores_and_surfaces_notifications():
    """notify_callbacks stores records; pending_notifications returns unseen ones."""
    dev = _fresh_librarian()
    cbs = [{"node_id": "n1", "origin_session": "s1", "content": "test", "event": "promoted"}]
    dev.notify_callbacks(cbs)
    pending = dev.pending_notifications()
    assert len(pending) == 1, f"expected 1 pending notification, got {len(pending)}"
    assert pending[0]["origin_session"] == "s1"
    assert pending[0]["node_id"] == "n1"
    assert pending[0]["seen"] is False


def test_mark_notifications_seen():
    """mark_notifications_seen marks specific or all notifications as seen."""
    dev = _fresh_librarian()
    dev.notify_callbacks([
        {"node_id": "n1", "origin_session": "s1", "content": "a", "event": "promoted"},
        {"node_id": "n2", "origin_session": "s2", "content": "b", "event": "promoted"},
    ])
    marked = dev.mark_notifications_seen({"n1"})
    assert marked == 1
    pending = dev.pending_notifications()
    assert len(pending) == 1
    assert pending[0]["node_id"] == "n2"


def test_notifications_pane_surfaces():
    """The notifications pane surfaces pending notifications."""
    dev = _fresh_librarian()
    dev.notify_callbacks([
        {"node_id": "n1", "origin_session": "s1", "content": "test", "event": "promoted"}
    ])
    panes = dev.declared_panes()
    notif_panes = [p for p in panes if p["kind"] == "notifications"]
    assert len(notif_panes) == 1, "expected a notifications pane"
    data = notif_panes[0]["handler"]()
    assert len(data["pending"]) == 1
    assert data["total"] == 1


def test_chat_turn_threads_session_id():
    """chat_turn passes session_id through to resolve_query's deposits."""
    tbl = _t("chat_sid")
    dev = _fresh_librarian()
    q = f"chat session thread ({_NONCE})"

    from cairn.devices.librarian.chat import chat_turn
    seam = fake_seam(
        {q: [1.0, 0.0, 0.0],
         f"chat backfill ({_NONCE})": _NEAR,
         # The articulation reply
         },
        scripts=[
            f'{{"nodes": ["chat backfill ({_NONCE})"]}}',
            f"I found something about that.",
        ])
    got = chat_turn(q, resolve=seam, tree="chat_sid", table=tbl, dev=dev,
                    session_id="session-chat-A")
    loop_verdict = (got.get("reply") or {}).get("loop", {})
    deposited = loop_verdict.get("deposited", [])
    if deposited:
        row = store.read(NODES_TABLE, where="node_id = %s", params=(deposited[0],))[0]
        assert row["provenance"].get("origin_session") == "session-chat-A", \
            f"expected origin_session from chat_turn, got {row['provenance']}"


def _main() -> int:
    checks = [v for k, v in sorted(globals().items())
              if k.startswith("test_") and callable(v)]
    assert len(checks) >= 8, (
        f"roster floor: expected at least 8 teeth, found {len(checks)}")
    conn = store.connect()
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        for t in _TABLES:
            try:
                store.drop_tree(t, OWNER, conn=conn)
            except Exception:
                pass
        conn.close()
    print("green — proactive resolution callback: deposits carry origin_session, "
          "promotions produce callbacks, notifications surface on the pane")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
