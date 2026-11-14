"""home_reserver — how a box gets row slots and leaf tags from the home librarian (ticket
d32faaf16223, outline 4.3.1.5.1.1 and 4.3.1.5.1.6.9).

A row number is the same on every box, so only the home box's librarian hands one out. The trees
tool takes that as an injected ``reserver(kind)`` / ``reserver("tag", table)`` callable; this
module is the librarian device's two halves of it:

  - the HOME half: ``answer(body)``, what the librarian's ``reserve`` bus verb runs. It hands a
    block of slots out (``trees.reserve_block``) or a leaf table's tag (``trees.leaf_tag``).
  - the ASKING half: ``BlockReserver(ask)``, the callable a box that is not the home passes to
    the trees tool. It asks the home for a block of slots at a time, lays the block VOID locally
    (``trees.hold_reserved``) and hands the rows out one by one; a tag is asked for each time
    (the trees tool records it, so it is asked once per table).

``ask(body) -> reply body`` is the bus request to the home librarian's ``reserve`` verb;
``for_this_box()`` wires it to the home's LAN bus. On the home it returns None: the trees tool
reserves there by itself.
"""
from __future__ import annotations

import os
import threading

from cairn.devices.librarian.tools.trees import trees
from cairn.tools.base.diagnostic import DiagnosticBase

BLOCK = 1000   # outline 4.3.1.5.1.6.9's "eg 1,000"


class ReserveAnswerRefused(ValueError):
    """A ``reserve`` request the home will not answer, named whole (Law 7)."""


def answer(body: dict, *, conn=None) -> dict:
    """The home's answer to one ``reserve`` request: ``{"kind": k, "count": n}`` gets
    ``{"kind": k, "rows": [...]}``; ``{"kind": "tag", "table": t}`` gets ``{"tag": n}``."""
    body = body or {}
    kind = body.get("kind")
    if kind == "tag":
        table = body.get("table")
        if not isinstance(table, str) or not table:
            raise ReserveAnswerRefused(f"reserve: a tag request names no table: {body!r}")
        if not trees._is_home():
            raise trees.ReserveRefused(
                f"reserve: this box is not the home ({os.environ.get('CAIRN_HOME_HOST')!r} is); "
                f"a tag for {table!r} is handed out only there")
        return {"tag": trees.leaf_tag(table, conn=conn)}
    if kind not in trees.BLOCK_KINDS:
        raise ReserveAnswerRefused(
            f"reserve: kind {kind!r} is neither 'tag' nor one of {trees.BLOCK_KINDS}")
    count = body.get("count", BLOCK)
    return {"kind": kind, "rows": trees.reserve_block(kind, count, conn=conn)}


class BlockReserver(DiagnosticBase):
    """The reserver a box that is not the home hands the trees tool. One block per kind is
    held at a time; a used row is never handed out twice."""

    def __init__(self, ask, *, block: int = BLOCK, conn_factory=None) -> None:
        super().__init__()
        self._ask = ask
        self._block = block
        self._pool: dict[str, list[int]] = {}
        self._lock = threading.Lock()
        self._conn_factory = conn_factory
        self.asked = 0   # round trips to the home, for the proof and the diagnostic surface

    def __call__(self, kind: str, table: str | None = None) -> int:
        if kind == "tag":
            self.asked += 1
            return int(self._ask({"kind": "tag", "table": table})["tag"])
        with self._lock:
            pool = self._pool.setdefault(kind, [])
            if not pool:
                reply = self._ask({"kind": kind, "count": self._block})
                rows = [int(r) for r in reply.get("rows") or []]
                if not rows:
                    raise trees.ReserveRefused(
                        f"reserve: the home answered no {kind} rows ({reply!r}); nothing landed")
                self.asked += 1
                conn = self._conn_factory() if self._conn_factory else None
                try:
                    trees.hold_reserved(kind, rows, conn=conn)
                finally:
                    if conn is not None:
                        conn.close()
                pool.extend(sorted(rows))
            return pool.pop(0)

    def held(self, kind: str) -> list[int]:
        """The rows of ``kind`` reserved and not yet handed out."""
        return list(self._pool.get(kind, []))


def bus_ask(home: str):
    """``ask`` over the bus to the home librarian's ``reserve`` verb at ``home`` (a bus home:
    a folder, or ``host:port`` for another box's bus)."""
    from cairn.tools.bus_client.remote import RemoteBus
    bus = RemoteBus(home)

    def ask(body: dict) -> dict:
        reply = bus.request(sender="librarian", to="librarian", verb="reserve",
                            why="a slot only the home hands out", body=body)
        return reply["body"] if isinstance(reply, dict) and "body" in reply else reply
    return ask


def for_this_box() -> BlockReserver | None:
    """None on the home (the trees tool reserves there itself); elsewhere a BlockReserver that
    asks the home's bus at CAIRN_HOME_HOST over the LAN door."""
    if trees._is_home():
        return None
    from cairn.tools.bus_client import tls
    host = os.environ["CAIRN_HOME_HOST"].strip()
    return BlockReserver(bus_ask(f"{host}:{tls.lan_port()}"))
