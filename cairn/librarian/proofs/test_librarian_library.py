"""Proof for librarian/library.py — the library room and the LEARN verb. Teeth a hollow
shelf could not pass:

  - SHELVED IS FROZEN: a copy lands at a stable address with its digest in the register;
    re-shelving the same content writes nothing; DIFFERENT content at a standing address
    is refused loudly (citations anchor here — an address must not change meaning).
  - ROT IS LOUD: learning an unshelved address, a missing file, or a shelved copy whose
    bytes drifted from the register is refused BEFORE any deposit — a rotted address
    fails its citations, it never quietly grounds new ones.
  - CITATIONS ARE POSITIONS IN THE FROZEN FILE: the blank-line split counts RAW slots,
    so dropping an under-floor fragment never renumbers its neighbors.
  - LEARN IS DEPOSIT-ONLY AND ANCHORED: every passage lands through the same provenance
    gate as everything else — source ``library:<address>``, passage ``p<n>``, the frozen
    digest — born a hypothesis; re-learning is all duplicates and writes nothing (Law 1).
  - LEARNED NODES RESOLVE AS STRUCTURE, citation intact through the walk.
  - Room addresses are disciplined (no traversal, no underscore shelves); binary refuses
    loudly at learn; the learn crossing breadcrumbs; import purity by AST allowlist.

The shelf is a TEMP directory (instance-space physics without touching the real room);
the embed seam is a fake in inference_domain's shape; the DB is the real one through
db_domain (nonce table, self-cleaning), as in the trees and loop proofs.

    python3 cairn/librarian/proofs/test_librarian_library.py     # exit 0 = green
"""

from __future__ import annotations

import ast
import hashlib
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.db_domain import store
from cairn.librarian import library
from cairn.librarian.library import (
    LearnRefused, ShelfRefused, learn, passages, shelf_entry, shelve,
)
from cairn.librarian.trees import LibrarianDevice
from cairn.tester.scratch import scratch_dir  # noqa: E402

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLE = f"_library_{_NONCE}"
_TMP = scratch_dir(f"cairn_library_{_NONCE}_")
_SHELF = _TMP / "library"
_SRC = _TMP / "sources"
_SRC.mkdir(parents=True)


def _source(name: str, text: str) -> Path:
    p = _SRC / name
    p.write_text(text, encoding="utf-8")
    return p


def fake_embed(overrides: dict | None = None):
    """An embed-only seam in inference_domain's shape: exact-text overrides for teeth
    that need controlled geometry, else a deterministic nonzero 3-dim direction from the
    content's hash (distinct text, distinct direction — no host)."""
    overrides = overrides or {}

    def resolve(request):
        assert request["kind"] == "embed", "learn must never ask the shelf seam to generate"
        text = request["prompt"]
        if text in overrides:
            return {"answer": {"vector": list(overrides[text])}, "hit": False}
        h = hashlib.sha256(text.encode("utf-8")).digest()
        return {"answer": {"vector": [h[0] + 1.0, h[1] + 1.0, h[2] + 1.0]}, "hit": False}

    return resolve


def _refuses(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc as e:
        return str(e)
    raise AssertionError(f"{fn.__name__} must refuse with {exc.__name__} — it did not")


def test_shelve_freezes_a_copy_and_registers_its_digest():
    src = _source("first.txt", "a source line worth keeping around\n")
    got = shelve(src, "room-a", library=_SHELF)
    assert got == {"address": "room-a/first.txt", "sha256": got["sha256"],
                   "bytes": src.stat().st_size, "duplicate": False}
    assert (_SHELF / "room-a" / "first.txt").read_text(encoding="utf-8") == \
        src.read_text(encoding="utf-8"), "the shelf holds a faithful copy"
    assert src.is_file(), "shelving copies — the source is untouched"
    entry = shelf_entry("room-a/first.txt", library=_SHELF)
    assert entry["sha256"] == got["sha256"] and entry["origin"] == str(src)


def test_reshelve_same_content_writes_nothing():
    src = _source("first_again.txt", "a source line worth keeping around\n")
    shutil.copy2(src, _SRC / "first.txt")
    got = shelve(_SRC / "first.txt", "room-a", library=_SHELF)
    assert got["duplicate"] is True, "same content at the same address is Law 1, not a write"


def test_a_standing_address_never_changes_meaning():
    src = _source("first.txt", "DIFFERENT content wearing the same filename\n")
    msg = _refuses(ShelfRefused, shelve, src, "room-a", library=_SHELF)
    assert "FROZEN" in msg and "sha256:" in msg, "the refusal names both digests' clash"
    assert (_SHELF / "room-a" / "first.txt").read_text(encoding="utf-8") == \
        "a source line worth keeping around\n", "the frozen copy survived the attempt"


def test_room_addresses_are_disciplined():
    src = _source("addr.txt", "content long enough to be worth shelving\n")
    for bad in ("", "..", "a/../b", "/abs", "_registers", "rooms/_desk"):
        _refuses(ShelfRefused, shelve, src, bad, library=_SHELF)
    got = shelve(src, " rooms//nested/ ", library=_SHELF)
    assert got["address"] == "rooms/nested/addr.txt", "addresses normalize to plain relative paths"
    _refuses(ShelfRefused, shelve, _SRC / "not-there.txt", "room-a", library=_SHELF)
    _refuses(ShelfRefused, shelve, _SRC, "room-a", library=_SHELF)  # a directory


def test_passages_cite_raw_positions_forever():
    text = ("# tiny\n\n"
            "the first passage, long enough to clear the floor easily\n\n"
            "-\n\n"
            "the third passage, also long enough to clear the floor\n")
    got = passages(text)
    assert got == [
        (1, "the first passage, long enough to clear the floor easily"),
        (3, "the third passage, also long enough to clear the floor"),
    ], "dropped fragments keep their slots — p3 means the 4th raw paragraph forever"
    assert passages("short\n\nbits") == [], "nothing above the floor is an honest empty"


def test_learn_deposits_every_passage_anchored_to_the_shelf():
    src = _source("teach.txt",
                  "alpha passage that is comfortably long enough to keep\n\n"
                  "beta passage that is also comfortably long enough to keep\n")
    shelved = shelve(src, "lessons", library=_SHELF)
    got = learn("lessons/teach.txt", resolve=fake_embed(), tree="taught",
                library=_SHELF, table=_TABLE)
    assert got["passages"] == 2 and len(got["deposited"]) == 2
    assert got["duplicates"] == 0 and got["refused"] == []
    rows = store.read(_TABLE, where="tree = %s", params=("taught",))
    assert len(rows) == 2
    for r in rows:
        assert r["provenance"]["source"] == "library:lessons/teach.txt"
        assert r["provenance"]["sha256"] == shelved["sha256"][:12], \
            "the citation carries the FROZEN digest — it can be checked against the register"
        assert r["standing"] == "hypothesis", "learned nodes are hypotheses (Law 3)"
    assert {r["provenance"]["passage"] for r in rows} == {"p0", "p1"}


def test_relearn_writes_nothing():
    got = learn("lessons/teach.txt", resolve=fake_embed(), tree="taught",
                library=_SHELF, table=_TABLE)
    assert got["duplicates"] == 2 and got["deposited"] == [], \
        "the graph already holds the frozen file — re-learning is all duplicates (Law 1)"
    assert len(store.read(_TABLE, where="tree = %s", params=("taught",))) == 2


def test_learn_refuses_the_unshelved_the_missing_and_the_rotted():
    _refuses(LearnRefused, learn, "nowhere/ghost.txt", resolve=fake_embed(),
             library=_SHELF, table=_TABLE)
    _refuses(LearnRefused, learn, "lessons/teach.txt", resolve=None,
             library=_SHELF, table=_TABLE)
    # Rot the shelf under the register: the frozen copy's bytes drift.
    shelved_path = _SHELF / "lessons" / "teach.txt"
    frozen = shelved_path.read_text(encoding="utf-8")
    shelved_path.write_text(frozen + "a drifted line\n", encoding="utf-8")
    msg = _refuses(LearnRefused, learn, "lessons/teach.txt", resolve=fake_embed(),
                   library=_SHELF, table=_TABLE)
    assert "rotted" in msg and "sha256:" in msg, "rot is loud and names both digests"
    shelved_path.write_text(frozen, encoding="utf-8")  # restore the frozen copy
    # And gone entirely:
    src = _source("gone.txt", "content long enough to be shelved then lost\n")
    shelve(src, "lessons", library=_SHELF)
    (_SHELF / "lessons" / "gone.txt").unlink()
    _refuses(LearnRefused, learn, "lessons/gone.txt", resolve=fake_embed(),
             library=_SHELF, table=_TABLE)


def test_binary_shelves_but_refuses_to_learn():
    src = _SRC / "opaque.bin"
    src.write_bytes(bytes(range(256)) * 4)
    shelve(src, "lessons", library=_SHELF)
    msg = _refuses(LearnRefused, learn, "lessons/opaque.bin", resolve=fake_embed(),
                   library=_SHELF, table=_TABLE)
    assert "utf-8" in msg, "a binary needs a reader, not a silent skip"


def test_learned_nodes_resolve_with_their_citation_intact():
    a = "the anchor passage this tooth will walk straight back to"
    b = "the decoy passage pointing in an orthogonal direction entirely"
    src = _source("walkback.txt", f"{a}\n\n{b}\n")
    shelve(src, "lessons", library=_SHELF)
    seam = fake_embed({a: [1.0, 0.0, 0.0], b: [0.0, 1.0, 0.0]})
    learn("lessons/walkback.txt", resolve=seam, tree="walkback",
          library=_SHELF, table=_TABLE)
    dev = LibrarianDevice()
    walk = dev.nearest([0.99, 0.05, 0.0], k=2, tree="walkback", table=_TABLE)
    assert walk[0]["content"] == a, "the learned passage is reachable as structure"
    assert walk[0]["provenance"] == {"source": "library:lessons/walkback.txt",
                                     "passage": "p0",
                                     "sha256": shelf_entry("lessons/walkback.txt",
                                                           library=_SHELF)["sha256"][:12]}, \
        "the citation survives the round trip — a walk answer can point back to its shelf"


def test_the_learn_crossing_breadcrumbs():
    dev = LibrarianDevice()
    learn("lessons/teach.txt", resolve=fake_embed(), tree="taught",
          library=_SHELF, table=_TABLE, dev=dev)
    crumbs = [c for c in dev.held_diagnostics() if c["gate"] == "learn"]
    assert len(crumbs) == 1 and crumbs[0]["pointer"] == "lessons/teach.txt"
    assert crumbs[0]["values"] == {"tree": "taught", "passages": 2, "deposited": 0,
                                   "duplicates": 2, "refused": 0}, \
        "the verb's summary line carries its counts — a re-learn is visibly a no-op"


def test_library_opens_no_door_of_its_own():
    # cairn.base.address joined 2026-08-12 (one-owner-for-the-instance-address): LIBRARY_ROOT
    # used to spell ~/.cairn/devices/librarian/0/library by hand — one of ten such spellings
    # in class-space — and now calls the one rung that owns that address. The admission does
    # not touch this tooth's why: address.py imports pathlib and nothing else (measured:
    # import_map says ['__future__', 'pathlib']), so it is neither a DB door nor a host door,
    # and it REMOVES a re-derivation rather than adding a reach. Admitted by name and dated,
    # per the precedent every prior widening in this corpus followed — an entry that arrives
    # without one is the defect the-inspectors-allowlist-tooth-is-red trouble is open about.
    allowed = ("__future__", "hashlib", "json", "shutil", "datetime", "pathlib",
               "cairn.base.address", "cairn.librarian.trees")
    src = Path(library.__file__).read_text(encoding="utf-8")
    seen = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            seen.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            seen.append(node.module or "")
    offenders = [m for m in seen if not any(m == p or m.startswith(p + ".") for p in allowed)]
    assert not offenders, (
        f"library.py imports outside its allowlist: {offenders} — file physics are the "
        "shelf's own medium, but the DB is reached only through trees and the host only "
        "through the injected seam (sole-path, Law 4)")


def _cleanup():
    shutil.rmtree(_TMP, ignore_errors=True)
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{_TABLE}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (_TABLE,))
    finally:
        conn.close()


def _main() -> int:
    checks = [
        test_shelve_freezes_a_copy_and_registers_its_digest,
        test_reshelve_same_content_writes_nothing,
        test_a_standing_address_never_changes_meaning,
        test_room_addresses_are_disciplined,
        test_passages_cite_raw_positions_forever,
        test_learn_deposits_every_passage_anchored_to_the_shelf,
        test_relearn_writes_nothing,
        test_learn_refuses_the_unshelved_the_missing_and_the_rotted,
        test_binary_shelves_but_refuses_to_learn,
        test_learned_nodes_resolve_with_their_citation_intact,
        test_the_learn_crossing_breadcrumbs,
        test_library_opens_no_door_of_its_own,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — librarian/library: shelved is frozen, rot is loud, citations are "
          "positions in the frozen file, learn is deposit-only and anchored, learned "
          "nodes resolve as structure with their citations intact, and the library "
          "opens no door of its own")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
