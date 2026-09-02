"""live.py — the librarian's spine against the real embed seam, through the bus.

The composition: ``bus.request(to="inference_domain", verb="resolve", ...)`` — vectors
as a metered service — feeding ``LibrarianDevice``'s provenance-gated deposit door and
proximity walk. trees.py stays import-pure; this thin edge is where the bus composes with
the librarian's own machinery (the same shape as intention_extractor/live.py).

The bus is the sole path for inter-device inference (ticket 87a7f1c7ae21). The librarian
never imports inference_domain directly — it posts requests on the bus, and
inference_domain's resolve verb handles them internally (building the resolver, running
the domain workflow, posting the result back).

The founding demo seeds the librarian's FIRST REAL NODES: Akien's own verbatim design
lines, each carrying its provenance, deposited into the tree ``founding``. The query then
asks a question none of them answers word-for-word — the walk must rank the RIGHT line
nearest by meaning alone. Run it twice and the second pass is all cache HITs: the same
text canonicalizes to the same key, the host goes untouched, and yield_report shows the
saving (the same interplay the extractor measured, one layer down).

THE LOOP MODE is the core loop live-fired: the same founding tree, a question its
residents cannot resolve, and BOTH verbs through the one door — a dual seam where
``kind: "embed"`` rides nomic-embed-text and ``kind: "generate"`` rides qwen2.5:7b. The
model is set ON THE REQUEST, so it is part of the cache key (two models never collide on
one canonical form). The verdict prints whole, whichever way it lands — an UNRESOLVED
here is a finding, not a failure of the wiring.

THE SHELVE MODE is the library's first acquisition job: the founding collection
(~/TheIgorsProject/Akien — curated by Akien, quarry-stamped until shelved) copied file by
file into the ratified room at ~/.cairn/devices/librarian/0/library/, each at a stable
citable address, each digest frozen in the register. THE LEARN MODE folds one shelved
file into the graph — deposit only, every passage anchored to shelf + passage + digest.

    python3 -m cairn.devices.librarian.live                      # the founding demo
    python3 -m cairn.devices.librarian.live "some query text"    # walk the founding tree yourself
    python3 -m cairn.devices.librarian.live loop                 # the core loop, live
    python3 -m cairn.devices.librarian.live loop "a question" [tree]   # ground your own question
    python3 -m cairn.devices.librarian.live shelve               # acquire the founding collection
    python3 -m cairn.devices.librarian.live learn <address> [tree]     # fold one shelved file in
    python3 -m cairn.devices.librarian.live summarize <tree> "question"   # the transducer, live
    # exit 0 = the walk ranked / the verb returned; 1 = nothing surfaced
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cairn.tools.base.bus_client import connect_bus
from cairn.devices.librarian.library import learn as learn_verb
from cairn.devices.librarian.library import shelve
from cairn.devices.librarian.loop import resolve_query
from cairn.devices.librarian.summarize import summarize
from cairn.devices.librarian.trees import LibrarianDevice

DEFAULT_MODEL = "nomic-embed-text"
GENERATE_MODEL = "qwen2.5:7b"
TREE = "founding"
_SENDER = "librarian"

# The librarian's first acquisitions: Akien verbatim, each line traceable to its record.
_SEEDS = [
    ("the current goal is the librarian as chat bot, learning, and summarizing. "
     "learning always and summarizing when asked",
     {"source": "CairnCommons/notes/held-librarian.json",
      "section": "first_face_2026_07_27_chatbot_learning_always_summarizing_when_asked"}),
    ("my suggestion is that the librarian also have A LIBRARY. In .cairn --- it can hold "
     "the various files we'll be rereading from in TheIgorsProject",
     {"source": "CairnCommons/notes/held-librarian.json",
      "section": "the_library_room_and_the_request_verbs_2026_07_27"}),
    ("every time we use it instead of the cloud, we saved that amount, and can appy it "
     "against the purchase price.",
     {"source": "CairnCommons/notes/held-hex-payback-meter.json", "section": "the_idea"}),
]

DEFAULT_QUERY = "what should the chat interface do when someone talks to the librarian?"


def _wire_bus():
    """Minimal bus for CLI scripts — inference_domain registered for resolve verbs."""
    return connect_bus(devices=["inference_domain"])


def _bus_resolve(bus: BusDevice, request: dict) -> dict:
    """Post a resolve request to inference_domain via the bus and return the result."""
    reply = bus.request(
        sender=_SENDER, to="inference_domain", verb="resolve",
        why="librarian resolve", body=request,
    )
    return reply["body"]


def _bus_yield(bus: BusDevice) -> dict:
    """Get inference_domain's yield report via the bus get verb."""
    reply = bus.request(
        sender=_SENDER, to="inference_domain", verb="get",
        why="yield report", body={"what": "yield"},
    )
    return reply.get("body", {}).get("data", {})


def embed_via_bus(bus: BusDevice, model: str = DEFAULT_MODEL):
    """The embed seam, composed: text -> vector, metered and cached, via the bus.
    Stamped ``domain='research'`` like every librarian seam — a declared fact about who is
    asking; an embed is never dressed (the vector must not move), so the stamp lands only
    in provenance and the canonical is untouched (warm cache rows still hit)."""
    def embed(text: str) -> list[float]:
        return _bus_resolve(bus, {"kind": "embed", "prompt": text,
                                  "model": model, "domain": "research"})["answer"]["vector"]
    return embed


def embed_metered_via_bus(bus: BusDevice, model: str = DEFAULT_MODEL):
    """The embed seam WITH ITS METER (2026-07-29, ticket a-node-holds-one-claim):
    text -> ``{"vector", "tokens"}``, where tokens is the host's own
    prompt_eval_count for that input.

    Why this exists beside embed_via_bus rather than replacing it: the embed
    ceiling has been FOLKLORE. The host has always reported the real token count
    (/api/embed is the door precisely because /api/embeddings reports no counters,
    measured 2026-07-26), the domain has always recorded it — and the seam threw it
    away, so every operator sizing a rendering against the ceiling guessed from
    character length. That guess is what left Stone C's close hand-trimmed and
    Stone A's verdict refused. Reading the number the host already sends is the
    difference between a measured bound and a rule of thumb (Law 3).

    ``tokens`` is None on a cache HIT — the served row carries served_from, not
    counters, and inventing a number for it would be a proxy metric wearing a
    measurement's clothes. None means "not reported on this path" and says so;
    it is never a zero and never a guess.

    embed_via_bus's vector-only contract is deliberately untouched, so nothing
    that depends on it moves."""
    def embed(text: str) -> dict:
        got = _bus_resolve(bus, {"kind": "embed", "prompt": text,
                                 "model": model, "domain": "research"})
        counters = (got.get("provenance") or {}).get("counters") or {}
        return {"vector": got["answer"]["vector"],
                "tokens": counters.get("prompt_eval_count"),
                "hit": got.get("hit")}
    return embed


def dual_seam(bus: BusDevice, embed_model: str = DEFAULT_MODEL,
              generate_model: str = GENERATE_MODEL):
    """Both verbs, one door — via the bus. The model is stamped ON THE REQUEST by kind —
    embed requests ride the embedding model, generate requests the drafting model — so the
    model is part of the canonical form and the two can never share a cache row.

    The librarian is the research vertical's first real consumer (ticket
    the-domain-carries-the-inference-side): every request through this seam is stamped
    ``domain='research'`` — a DECLARED fact about who is asking, set here by rule, never
    inferred from message content (chat tooth 15). The domains stack owns what the stamp
    means (prompts, walk-rule); this seam only names it."""
    def resolve(request: dict) -> dict:
        request = dict(request)
        request.setdefault(
            "model", embed_model if request.get("kind") == "embed" else generate_model)
        request.setdefault("domain", "research")
        return _bus_resolve(bus, request)
    return resolve


def _seed(dev: LibrarianDevice, embed) -> None:
    for content, provenance in _SEEDS:
        r = dev.deposit(content, embed(content), provenance, tree=TREE)
        print(f"  {'DUPLICATE' if r['duplicate'] else 'DEPOSITED'}  {r['node_id']}  "
              f"dim={r['dim']}  {content[:60]!r}")


LOOP_QUERY = "what does cosine similarity measure between two embedding vectors?"


def _loop(argv: list[str]) -> int:
    """The core loop against the founding tree: always the graph first; on a miss the
    host supplies NODES and the ORIGINAL question resubmits through structure."""
    bus = _wire_bus()
    resolve = dual_seam(bus)
    dev = LibrarianDevice()
    _seed(dev, lambda text: resolve({"kind": "embed", "prompt": text})["answer"]["vector"])

    question = argv[0] if argv else LOOP_QUERY
    tree = argv[1] if len(argv) > 1 else TREE
    verdict = resolve_query(question, resolve=resolve, tree=tree, dev=dev)
    print(json.dumps({
        "verdict": {k: v for k, v in verdict.items() if k != "nodes"},
        "walk": [{"similarity": round(n["similarity"], 4), "content": n["content"],
                  "standing": n["standing"]} for n in verdict["nodes"]],
        "trail": str(dev.diagnostic_trail()),
        "yield": _bus_yield(bus),
    }, indent=2, default=str))
    return 0


# The founding collection: Akien's curated folder, quarry-stamped until shelved here.
COLLECTION = Path.home() / "TheIgorsProject" / "Akien"


def _shelve_collection(argv: list[str]) -> int:
    """The first acquisition job: every file of the founding collection onto the shelf,
    rooms mirroring its own layout (DATED/, ideas/, Readings/...) — shallow stable
    shelving; the graph is the catalog."""
    root = Path(argv[0]) if argv else COLLECTION
    shelved = duplicates = 0
    failures = []
    for src in sorted(p for p in root.rglob("*") if p.is_file()):
        room = str(src.parent.relative_to(root)) if src.parent != root else "unfiled"
        try:
            r = shelve(src, room)
        except Exception as e:  # a refusal is a finding, not a stop — report complete
            failures.append({"source": str(src), "refusal": str(e)})
            continue
        duplicates += r["duplicate"]
        shelved += not r["duplicate"]
    # ATTENDANCE, not only objections (ruled 2026-08-13, "EVERYTHING ALWAYS PROVED AND
    # LISTING WHAT IT PROVED"). This is an operation report over a real-world walk, not a
    # gate — it may not import cairn.tools.gate, because the librarian reaches the oracle
    # and bin/cmd/determinism reads gate-ness at COMPONENT granularity. What it CAN do is
    # state its own completeness: every walked file lands in exactly one of the three
    # buckets, so `walked` is the number a reader would otherwise have to derive, and a
    # walk that silently stopped early shows a SMALLER walked count rather than a cleaner
    # failures list.
    print(json.dumps({"collection": str(root), "walked": shelved + duplicates + len(failures),
                      "shelved": shelved, "duplicates": duplicates, "failures": failures},
                     indent=2))
    return 0 if (shelved or duplicates) and not failures else 1


def _learn(argv: list[str]) -> int:
    """The LEARN verb, live: one shelved file folded into the graph. Deposit only."""
    if not argv:
        print("usage: live learn <shelf-address> [tree]", file=sys.stderr)
        return 1
    address, tree = argv[0], (argv[1] if len(argv) > 1 else "library")
    bus = _wire_bus()
    dev = LibrarianDevice()
    resolve = dual_seam(bus)
    got = learn_verb(address, resolve=resolve, tree=tree, dev=dev)
    print(json.dumps({"learn": got, "trail": str(dev.diagnostic_trail()),
                      "yield": _bus_yield(bus)}, indent=2, default=str))
    return 0


def _summarize(argv: list[str]) -> int:
    """The SUMMARIZE verb, live: a dense region of a real tree rendered into cited prose
    by the drafting model, landing back in the graph. The verdict prints whole, whichever
    way it lands — a loud refusal here is a finding, not a failure of the wiring."""
    if len(argv) < 2:
        print("usage: live summarize <tree> \"question\"", file=sys.stderr)
        return 1
    tree, question = argv[0], argv[1]
    bus = _wire_bus()
    dev = LibrarianDevice()
    got = summarize(question, resolve=dual_seam(bus), tree=tree, dev=dev)
    print(json.dumps({"summarize": got, "trail": str(dev.diagnostic_trail()),
                      "yield": _bus_yield(bus)}, indent=2, default=str))
    return 0


def _main(argv: list[str]) -> int:
    if argv and argv[0] == "loop":
        return _loop(argv[1:])
    if argv and argv[0] == "shelve":
        return _shelve_collection(argv[1:])
    if argv and argv[0] == "learn":
        return _learn(argv[1:])
    if argv and argv[0] == "summarize":
        return _summarize(argv[1:])
    bus = _wire_bus()
    embed = embed_via_bus(bus)
    dev = LibrarianDevice()
    _seed(dev, embed)

    query = argv[0] if argv else DEFAULT_QUERY
    ranked = dev.nearest(embed(query), k=len(_SEEDS), tree=TREE)
    print(json.dumps({
        "query": query,
        "walk": [{"similarity": round(n["similarity"], 4), "content": n["content"],
                  "provenance": n["provenance"], "standing": n["standing"]}
                 for n in ranked],
        "trail": str(dev.diagnostic_trail()),
        "yield": _bus_yield(bus),
    }, indent=2, default=str))
    return 0 if ranked else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
