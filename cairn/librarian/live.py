"""live.py — the librarian's spine against the real embed seam, through the one door.

The composition: ``domain.resolve`` (metered, cached) wrapping ``host.ollama_resolver``
with ``kind: "embed"`` — vectors as a metered service — feeding ``LibrarianDevice``'s
provenance-gated deposit door and proximity walk. trees.py stays import-pure; this thin
edge is where the doors compose (the same shape as intention_extractor/live.py).

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

    python3 -m cairn.librarian.live                      # the founding demo
    python3 -m cairn.librarian.live "some query text"    # walk the founding tree yourself
    python3 -m cairn.librarian.live loop                 # the core loop, live
    python3 -m cairn.librarian.live loop "a question" [tree]   # ground your own question
    python3 -m cairn.librarian.live shelve               # acquire the founding collection
    python3 -m cairn.librarian.live learn <address> [tree]     # fold one shelved file in
    python3 -m cairn.librarian.live summarize <tree> "question"   # the transducer, live
    # exit 0 = the walk ranked / the verb returned; 1 = nothing surfaced
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cairn.inference_domain import domain, host
from cairn.librarian.library import learn as learn_verb
from cairn.librarian.library import shelve
from cairn.librarian.loop import resolve_query
from cairn.librarian.summarize import summarize
from cairn.librarian.trees import LibrarianDevice

DEFAULT_MODEL = "nomic-embed-text"
GENERATE_MODEL = "qwen2.5:7b"
TREE = "founding"

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


def embed_via_domain(model: str = DEFAULT_MODEL):
    """The embed seam, composed: text -> vector, metered and cached, host behind one door."""
    resolver = host.ollama_resolver(model=model)
    def embed(text: str) -> list[float]:
        return domain.resolve({"kind": "embed", "prompt": text},
                              resolver=resolver)["answer"]["vector"]
    return embed


def dual_seam(embed_model: str = DEFAULT_MODEL, generate_model: str = GENERATE_MODEL):
    """Both verbs, one door. The model is stamped ON THE REQUEST by kind — embed requests
    ride the embedding model, generate requests the drafting model — so the model is part
    of the canonical form and the two can never share a cache row. One resolver serves
    both: ollama_resolver honors the request's own ``model`` over its default."""
    resolver = host.ollama_resolver(model=generate_model)
    def resolve(request: dict) -> dict:
        request = dict(request)
        request.setdefault(
            "model", embed_model if request.get("kind") == "embed" else generate_model)
        return domain.resolve(request, resolver=resolver)
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
    resolve = dual_seam()
    dev = LibrarianDevice()
    _seed(dev, lambda text: resolve({"kind": "embed", "prompt": text})["answer"]["vector"])

    question = argv[0] if argv else LOOP_QUERY
    tree = argv[1] if len(argv) > 1 else TREE
    verdict = resolve_query(question, resolve=resolve, tree=tree, dev=dev)
    print(json.dumps({
        "verdict": {k: v for k, v in verdict.items() if k != "nodes"},
        "walk": [{"similarity": round(n["similarity"], 4), "content": n["content"],
                  "standing": n["standing"]} for n in verdict["nodes"]],
        "breadcrumbs": dev.held_diagnostics(),
        "yield": domain.yield_report(),
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
    print(json.dumps({"collection": str(root), "shelved": shelved,
                      "duplicates": duplicates, "failures": failures}, indent=2))
    return 0 if (shelved or duplicates) and not failures else 1


def _learn(argv: list[str]) -> int:
    """The LEARN verb, live: one shelved file folded into the graph. Deposit only."""
    if not argv:
        print("usage: live learn <shelf-address> [tree]", file=sys.stderr)
        return 1
    address, tree = argv[0], (argv[1] if len(argv) > 1 else "library")
    dev = LibrarianDevice()
    resolve = dual_seam()
    got = learn_verb(address, resolve=resolve, tree=tree, dev=dev)
    print(json.dumps({"learn": got, "breadcrumbs": dev.held_diagnostics(),
                      "yield": domain.yield_report()}, indent=2, default=str))
    return 0


def _summarize(argv: list[str]) -> int:
    """The SUMMARIZE verb, live: a dense region of a real tree rendered into cited prose
    by the drafting model, landing back in the graph. The verdict prints whole, whichever
    way it lands — a loud refusal here is a finding, not a failure of the wiring."""
    if len(argv) < 2:
        print("usage: live summarize <tree> \"question\"", file=sys.stderr)
        return 1
    tree, question = argv[0], argv[1]
    dev = LibrarianDevice()
    got = summarize(question, resolve=dual_seam(), tree=tree, dev=dev)
    print(json.dumps({"summarize": got, "breadcrumbs": dev.held_diagnostics(),
                      "yield": domain.yield_report()}, indent=2, default=str))
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
    embed = embed_via_domain()
    dev = LibrarianDevice()
    _seed(dev, embed)

    query = argv[0] if argv else DEFAULT_QUERY
    ranked = dev.nearest(embed(query), k=len(_SEEDS), tree=TREE)
    print(json.dumps({
        "query": query,
        "walk": [{"similarity": round(n["similarity"], 4), "content": n["content"],
                  "provenance": n["provenance"], "standing": n["standing"]}
                 for n in ranked],
        "breadcrumbs": dev.held_diagnostics(),
        "yield": domain.yield_report(),
    }, indent=2, default=str))
    return 0 if ranked else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
