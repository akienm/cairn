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

    python3 -m cairn.librarian.live                      # the founding demo
    python3 -m cairn.librarian.live "some query text"    # walk the founding tree yourself
    # exit 0 = the walk ranked; 1 = nothing surfaced
"""

from __future__ import annotations

import json
import sys

from cairn.inference_domain import domain, host
from cairn.librarian.trees import LibrarianDevice

DEFAULT_MODEL = "nomic-embed-text"
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


def _main(argv: list[str]) -> int:
    embed = embed_via_domain()
    dev = LibrarianDevice()

    for content, provenance in _SEEDS:
        r = dev.deposit(content, embed(content), provenance, tree=TREE)
        print(f"  {'DUPLICATE' if r['duplicate'] else 'DEPOSITED'}  {r['node_id']}  "
              f"dim={r['dim']}  {content[:60]!r}")

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
