"""librarian/library.py — the library room and the LEARN verb: the shelf, and the fold.

Akien, 2026-07-27, verbatim: "my suggestion is that the librarian also have A LIBRARY.
In .cairn --- it can hold the various files we'll be rereading from in TheIgorsProject...
Dewey decimal system or some other organization... i dunno. whatever will work." And the
verbs: "he learn, or learn and summarize, or learn and summarize by x time."

THE SHELF IS NOT THE CATALOG. The graph is the catalog — the embedding is the path, and
retrieval is a walk, never a shelf scan. What the shelves supply is STABLE, CITABLE
ADDRESSES: provenance-on-deposit anchors point INTO the library ("this came from shelf X,
passage Y") and that address must not rot. So the physics here are freezing physics:

  - A shelved file is a FROZEN COPY. Its address is its room-relative path; its digest is
    recorded in the shelf register (``_manifest.json``) at shelving time. Re-shelving the
    same content writes nothing (Law 1); shelving DIFFERENT content at a standing address
    is refused loudly — an address that silently changed meaning would rot every citation
    pointing at it (Law 7 at the shelf).
  - A PASSAGE is cited by its raw paragraph position (``p<n>`` over the blank-line split,
    BEFORE any filtering) — dropping a too-small fragment never renumbers its neighbors.
  - LEARN is deposit-only ("learn: densify the graph, no artifact"): every passage of a
    shelved file embeds and deposits through the SAME provenance gate as everything else,
    each node anchored ``{"source": "library:<address>", "passage": "p<n>", "sha256": …}``.
    Learning an unshelved file, or a shelved file whose bytes no longer match the
    register, is refused — a citation must anchor into the frozen shelf or not exist.

The library lives in INSTANCE-SPACE at ``~/.cairn/devices/librarian/0/library/`` (the
ratified address; the singleton carries the /0/). Rooms are subdirectories, as many as
needed; names starting with ``_`` are registers, not shelves. This module owns file
physics (the shelf IS files) but reaches the DB only through trees and the host not at
all — vectors arrive through the injected ``resolve`` seam, as everywhere.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from cairn.librarian.trees import DepositRefused, LibrarianDevice, NODES

LIBRARY_ROOT = Path.home() / ".cairn" / "devices" / "librarian" / "0" / "library"
MANIFEST = "_manifest.json"

# The floor under a passage: shorter fragments (a heading, a stray line) are dropped —
# their POSITIONS are still counted, so surviving citations never renumber. A labeled
# guess (n=0 live files at pick time); tunes against real shelving.
MIN_PASSAGE_CHARS = 40


class ShelfRefused(RuntimeError):
    """A shelving the register cannot honestly absorb — refused loudly, nothing shelved."""


class LearnRefused(RuntimeError):
    """A learn that cannot anchor into the frozen shelf — refused before any deposit."""


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_manifest(library: Path) -> dict:
    p = library / MANIFEST
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _write_manifest(library: Path, manifest: dict) -> None:
    tmp = library / (MANIFEST + ".tmp")
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(library / MANIFEST)


def _check_room(room: str) -> str:
    r = str(room).strip()
    if Path(r).is_absolute():
        raise ShelfRefused(
            f"shelve: room {room!r} is absolute — a shelf address is relative to the "
            "library root; an absolute room is a different intent, not sloppy spelling.")
    parts = [p for p in r.split("/") if p]
    if not parts or any(p in (".", "..") for p in parts):
        raise ShelfRefused(
            f"shelve: room {room!r} is not a plain relative path — a shelf address must "
            "be stable and derivable, not a traversal.")
    if any(p.startswith("_") for p in parts):
        raise ShelfRefused(
            f"shelve: room {room!r} starts a segment with '_' — underscore names are "
            "registers (the manifest, the desk), not shelves.")
    return "/".join(parts)


def shelve(src, room: str, *, library: Path | None = None) -> dict:
    """One file onto the shelf: a frozen copy at a stable citable address.

    Returns ``{"address", "sha256", "bytes", "duplicate"}``. Same content at the same
    address writes nothing; different content at a standing address is refused (frozen
    means frozen — citations point here).
    """
    library = Path(library) if library else LIBRARY_ROOT
    src = Path(src)
    if not src.is_file():
        raise ShelfRefused(
            f"shelve: {src} is not a file on disk — the shelf holds copies of real "
            "sources, one file at a time (a directory shelves file-by-file).")
    room = _check_room(room)
    address = f"{room}/{src.name}"
    digest = _sha256_file(src)

    library.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest(library)
    standing = manifest.get(address)
    if standing:
        if standing["sha256"] == digest:
            return {"address": address, "sha256": digest,
                    "bytes": standing["bytes"], "duplicate": True}
        raise ShelfRefused(
            f"shelve: address {address!r} already holds sha256:{standing['sha256'][:12]} "
            f"and the incoming file is sha256:{digest[:12]} — a shelved file is FROZEN "
            "(citations anchor here); shelve the new content under a new name.")

    dest = library / address
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    manifest[address] = {
        "sha256": digest,
        "bytes": dest.stat().st_size,
        "origin": str(src),
        "shelved": datetime.now(timezone.utc).isoformat(),
    }
    _write_manifest(library, manifest)
    return {"address": address, "sha256": digest,
            "bytes": manifest[address]["bytes"], "duplicate": False}


def shelf_entry(address: str, *, library: Path | None = None) -> dict:
    """The register's word on an address, VERIFIED against the bytes on the shelf.

    Loud if the address was never shelved, the file is gone, or the bytes no longer
    match the recorded digest — a rotted address must fail every citation pointing at
    it, not quietly ground new ones.
    """
    library = Path(library) if library else LIBRARY_ROOT
    entry = _load_manifest(library).get(address)
    if not entry:
        raise LearnRefused(
            f"learn: {address!r} is not in the shelf register — citations anchor into "
            "the frozen shelf; shelve it first.")
    path = library / address
    if not path.is_file():
        raise LearnRefused(
            f"learn: {address!r} is registered but MISSING from the shelf "
            f"(sha256:{entry['sha256'][:12]}) — the shelf rotted; nothing cited.")
    actual = _sha256_file(path)
    if actual != entry["sha256"]:
        raise LearnRefused(
            f"learn: {address!r} on the shelf is sha256:{actual[:12]} but the register "
            f"froze sha256:{entry['sha256'][:12]} — the copy changed under its "
            "citations; refusing to ground anything on a rotted address.")
    return {**entry, "address": address, "path": path}


def passages(text: str) -> list[tuple[int, str]]:
    """``(position, passage)`` pairs: the blank-line split, whitespace-normalized.

    Positions count RAW paragraphs — a fragment under the floor is dropped but its slot
    is still counted, so ``p7`` means the 7th paragraph of the frozen file forever.
    """
    out = []
    for i, block in enumerate(text.split("\n\n")):
        p = " ".join(block.split())
        if len(p) >= MIN_PASSAGE_CHARS:
            out.append((i, p))
    return out


def learn(address: str, *, resolve, tree: str = "library", library: Path | None = None,
          table: str = NODES, conn=None, dev: LibrarianDevice | None = None) -> dict:
    """The LEARN verb: one shelved file folded into the graph. Deposit only, no artifact.

    Every passage embeds (through the injected seam) and deposits through the provenance
    gate, anchored to shelf + passage + frozen digest. Returns::

        {"address", "passages", "deposited", "duplicates", "refused", "tree"}

    Re-learning a shelved file is all duplicates and writes nothing (Law 1) — the graph
    already holds it, and the register's digest guarantees it is the SAME it.
    """
    if not callable(resolve):
        raise LearnRefused(
            "learn: no resolve seam injected — vectors come through inference_domain's "
            "resolve or not at all (sole path).")
    entry = shelf_entry(address, library=library)
    try:
        text = entry["path"].read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise LearnRefused(
            f"learn: {address!r} is not utf-8 text — it shelves fine, but the learn verb "
            "reads text; a binary needs a reader in front of it (filed edge, not a "
            "silent skip).") from None

    dev = dev or LibrarianDevice()
    found = passages(text)
    deposited, duplicates, refused = [], 0, []
    for pos, content in found:
        provenance = {"source": f"library:{address}", "passage": f"p{pos}",
                      "sha256": entry["sha256"][:12]}
        vector = resolve({"kind": "embed", "prompt": content})["answer"]["vector"]
        try:
            r = dev.deposit(content, vector, provenance, tree=tree, table=table, conn=conn)
        except DepositRefused as e:
            refused.append({"passage": f"p{pos}", "refusal": str(e)})
            continue
        if r["duplicate"]:
            duplicates += 1
        else:
            deposited.append(r["node_id"])

    # GATE CONTACT: one learn crossing — a whole file folded (or found already folded).
    # Each deposit breadcrumbed itself; this is the verb's own summary line.
    dev.emit("learn", pointer=address,
             values={"tree": tree, "passages": len(found), "deposited": len(deposited),
                     "duplicates": duplicates, "refused": len(refused)})
    return {"address": address, "passages": len(found), "deposited": deposited,
            "duplicates": duplicates, "refused": refused, "tree": tree}
