"""The librarian's device class — LibrarianDevice, its process face.

It left the graph-tree store (now the published tool cairn.devices.librarian.tools.trees)
because RULE 1 lets other components reach the trees only through a declared public interface,
and a device class inside that interface would hand them the device itself (ticket 883abe55d04c).
"""

from __future__ import annotations

from datetime import datetime, timezone

from cairn.tools.base.device import BaseDevice
from cairn.devices.librarian.tools.trees.trees import (
    CALVE_THRESHOLD, NODES, OWNER, _MIN_CONTENT_CHARS, attractor, calve, contradiction_scan, deposit,
    linked, nearest, neighbors, route)


# ── the device ───────────────────────────────────────────────────────────────


class LibrarianDevice(BaseDevice):
    """The librarian (carries CP1-CP6; reports the Form v0 #2 surface).

    v0 surface = the graph-tree spine: ``deposit`` (a write-crossing — breadcrumbed,
    DEPOSITED and DUPLICATE alike) and the walks ``nearest`` / ``neighbors`` (reads —
    silent, per the extractor's reads-silent rule). The core resolve-or-generate loop,
    the summarizer, and the chat face land on this same device as later stones.
    """

    def __init__(self) -> None:
        super().__init__()
        self._deposits = 0
        self._verdicts = {"DEPOSITED": 0, "DUPLICATE": 0}
        self._last_node: str | None = None
        self._chat = None        # the conversational face — attached by the shim at wake
        self._notifications: list[dict] = []

    @property
    def device_id(self) -> str:
        return "librarian"

    def deposit(self, content: str, vector, provenance: dict, *,
                tree: str = "commons", table: str = NODES,
                render_method: str = "embed:default",
                resolve=None, conn=None) -> dict:
        """One deposit crossing — judged at the door, breadcrumbed after it lands.

        If ``resolve`` is provided and the deposit is not a duplicate, runs
        contradiction_scan as a post-write side effect. The deposit always lands
        regardless of the scan result. A missing or failing resolve seam means a
        missed detection, not a data loss.
        """
        result = deposit(content, vector, provenance, tree=tree, table=table,
                         render_method=render_method, conn=conn)
        verdict = "DUPLICATE" if result["duplicate"] else "DEPOSITED"
        self._deposits += 1
        self._verdicts[verdict] += 1
        self._last_node = result["node_id"]
        self.emit("deposit", pointer=result["node_id"],
                  values={"verdict": verdict, "tree": tree, "dim": result["dim"]})
        if resolve is not None and not result["duplicate"]:
            try:
                refuted = contradiction_scan(
                    result["node_id"], vector, resolve=resolve,
                    tree=tree, table=table, conn=conn)
                if refuted:
                    self.emit("contradiction", pointer=result["node_id"],
                              values={"refuted": [r["refuted_node_id"]
                                                  for r in refuted]})
            except Exception:
                pass
        return result

    def nearest(self, vector, *, k: int = 5, tree: str = "commons",
                table: str = NODES,
                warm_node_ids: set[str] | None = None,
                time_window: tuple[datetime, datetime] | None = None,
                conn=None) -> list[dict]:
        return nearest(vector, k=k, tree=tree, table=table,
                        warm_node_ids=warm_node_ids, time_window=time_window,
                        conn=conn)

    def neighbors(self, node_id: str, *, k: int = 5, tree: str = "commons",
                  table: str = NODES, conn=None) -> list[dict]:
        return neighbors(node_id, k=k, tree=tree, table=table, conn=conn)

    def attractor(self, *, table: str = NODES, conn=None) -> list[float] | None:
        return attractor(table=table, conn=conn)

    def calve(self, *, table: str = NODES, threshold: int = CALVE_THRESHOLD,
              conn=None) -> dict | None:
        result = calve(table=table, threshold=threshold, conn=conn)
        if result:
            self.emit("calve", pointer=table,
                      values={"children": result["children"],
                              "sizes": result["sizes"]})
        return result

    def route(self, vector, *, tables: list[str], k: int = 3,
              conn=None) -> list[dict]:
        return route(vector, tables=tables, k=k, conn=conn)

    def linked(self, node_id: str, *, conn=None) -> list[dict]:
        return linked(node_id, conn=conn)

    # --- the chat window: a surface the base shim class understands ---------

    def attach_chat(self, session) -> None:
        """Wire the conversational face (a ChatSession). Live composition happens in
        the SHIM at wake time — this device stays import-pure toward the host. The
        chat window is a declared PANE (below): the librarian owns a page the ONE web
        server displays through the standard shim machinery — never a server, a
        route, or a port of its own."""
        self._chat = session

    def declared_panes(self) -> list[dict]:
        """The chat window and notifications, offered as panes."""
        panes = [{"kind": "chat", "label": "Chat",
                  "handler": None if self._chat is None else self._chat.page}]
        panes.append({"kind": "notifications", "label": "Notifications",
                      "handler": lambda: {"pending": self.pending_notifications(),
                                          "total": len(self._notifications)}})
        return panes

    def receive(self, envelope: dict) -> dict:
        """Incoming mail (web_server → shim → here: the designed path, in-process
        v0). Channel ``chat`` carries one utterance to the face. Anything this
        device cannot honestly process refuses loudly — mail never vanishes
        (Law 7)."""
        channel = envelope.get("channel")
        if channel != "chat":
            raise ValueError(
                f"librarian: no handler for channel {channel!r} — this device "
                "receives 'chat' (one utterance per envelope)")
        if self._chat is None:
            raise RuntimeError(
                "librarian: a chat envelope arrived but no face is attached — the "
                "shim wires the ChatSession at wake; an unwired face refuses, it "
                "does not pretend")
        session_id = (envelope.get("body") or {}).get("session_id")
        return self._chat.turn(
            str((envelope.get("body") or {}).get("utterance", "")),
            session_id=session_id)

    # --- proactive resolution callbacks ---------------------------------------

    def notify_callbacks(self, callbacks: list[dict]) -> None:
        """Record promotion callbacks — fired by the resolution event, never a clock.

        Each callback carries the origin_session that deposited the node and the
        node's content. The notification surfaces on the pane; a dead session's
        notifications surface the next time its user opens the librarian."""
        now = datetime.now(timezone.utc).isoformat()
        for cb in callbacks:
            self._notifications.append({**cb, "at": now, "seen": False})

    def pending_notifications(self) -> list[dict]:
        return [n for n in self._notifications if not n.get("seen")]

    def mark_notifications_seen(self, node_ids: set | None = None) -> int:
        marked = 0
        for n in self._notifications:
            if n.get("seen"):
                continue
            if node_ids is None or n.get("node_id") in node_ids:
                n["seen"] = True
                marked += 1
        return marked

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "The librarian: owner of the graph trees (db_domain's first tenant). "
            "v0 is the spine — a provenance-gated deposit door and proximity walks whose "
            "edges are derived from the vectors, never stored. The face it feeds: a "
            "chatbot, learning always, summarizing when asked.",
            "why": "A query answered from structure costs a walk; only the novel costs "
            "inference (Law 1 as runtime). The embedding IS the path — so the store "
            "holds O(n) vectors and the paths fall out. Every node is traceable at "
            "birth: an untraceable node would be fabricated attribution in permanent "
            "residence.",
        }

    def state(self) -> dict:
        return {
            "deposits": self._deposits,
            "verdicts": dict(self._verdicts),
            "last_node_id": self._last_node,
        }

    def settings(self) -> dict:
        return {
            "table": NODES,
            "owner": OWNER,
            "min_content_chars": _MIN_CONTENT_CHARS,
            "standing_at_birth": "hypothesis (Law 3; the tenure loop is a filed edge)",
            "edges": "derived from cosine proximity at walk time; stored links (cairn_links) "
                    "add a learned layer reinforced by traversal",
            "calve_threshold": CALVE_THRESHOLD,
            "seam": "vectors arrive as data; the embed call is the caller's, through "
                    "inference_domain (live wiring in live.py, never here)",
        }
