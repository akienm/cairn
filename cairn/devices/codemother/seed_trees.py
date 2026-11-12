"""codemother/seed_trees.py — plant the cognition questions as root nodes.

Reads cognition_questions.json beside this file: the ids she HOLDS of the
librarian's cross-domain corpus (ticket d12fd9781fb6) plus her own coding_domain
starters. Each held id is found by key in the keyed tree the librarian plants the
corpus in, through the trees tool it publishes (trees.find over
trees.CROSS_DOMAIN_QUESTIONS); she never imports the librarian's corpus module and
never reads its file (RULE 1, outline 4.4.2: a delegate works its trees through
that tool). Embeds each question
and deposits it into codemother's graph tree via the librarian's deposit door.
Idempotent: the deposit door deduplicates by content hash, so re-running
after a corpus update deposits only the new questions.

Requires inference_domain to be reachable via the bus (hex.local running).
This is a CLI command, not an import-time side effect.

Usage:
    PYTHONPATH=~/dev/src/cairn python3 -m cairn.devices.codemother.seed_trees
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cairn.tools.tree.tree import deposit_learning
from cairn.tools.bus_client import reach


QUESTIONS_FILE = Path(__file__).parent / "cognition_questions.json"
OWNER = "codemother"
NEXUS = "root"

EMBED_MODEL = "nomic-embed-text"
_SENDER = "codemother"


def _embed_fn():
    bus = reach("inference_domain")
    def embed(text: str):
        reply = bus.request(
            sender=_SENDER, to="inference_domain", verb="resolve",
            why="seed_trees embed", body={"kind": "embed", "prompt": text, "model": EMBED_MODEL},
        )
        return reply["body"]["answer"]["vector"]
    return embed


def _sections(data: dict, errors: list, table: str) -> list:
    """Her held ids, each found by key in the librarian's keyed corpus tree, plus her
    coding_domain. A held id the tree does not carry is a loud error, never a silent skip."""
    from cairn.devices.librarian.tools.trees import trees

    held = []
    for qid in data.get("holds", []):
        found = trees.find(qid, table=table)
        if not found:
            errors.append({"id": qid, "error": f"held id {qid} resolves to no question in the librarian's tree {table}"})
            continue
        node = found[0]
        prov, meta = node["provenance"] or {}, node["meta"] or {}
        held.append({"id": qid, "question": node["content"], "function": meta.get("function", ""),
                     "origin": meta.get("origin") or prov.get("origin"), "said_by": prov.get("said_by", "")})
    return [("held", held), ("coding_domain", data.get("coding_domain", {}).get("questions", []))]


def seed(*, dry_run: bool = False, questions_file: Path | str | None = None,
         table: str | None = None) -> dict:
    """``table`` is the keyed tree the held ids are found in; the librarian's standing corpus
    tree when absent (a proof hands a scratch keyed leaf)."""
    from cairn.devices.librarian.tools.trees import trees

    data = json.loads(Path(questions_file or QUESTIONS_FILE).read_text())

    deposited = []
    skipped = []
    errors = []

    sections = _sections(data, errors, table or trees.CROSS_DOMAIN_QUESTIONS)
    embed = None if dry_run else _embed_fn()

    for section_name, questions in sections:
        for q in questions:
            qid = q.get("id", "unknown")
            text = q["question"]
            content = f"{text}\n[{q.get('function', '')}]"

            provenance = {
                "source": f"cognition_questions.json#{qid}",
                "section": section_name,
                "function": q.get("function", ""),
                "question_id": qid,
            }
            if section_name == "held":
                provenance["source"] = f"cairn/devices/librarian/cross_domain_questions.json#{qid}"
                provenance["origin"] = q["origin"]
                provenance["said_by"] = q.get("said_by", "")

            if dry_run:
                deposited.append({"id": qid, "section": section_name, "content": content,
                                  "provenance": provenance})
                continue

            try:
                got = embed(text)
                vector = got["vector"] if isinstance(got, dict) else got

                result = deposit_learning(
                    NEXUS, content, vector, provenance, owner=OWNER,
                )

                entry = {"id": qid, "section": section_name, "node_id": result.get("node_id")}
                if result.get("duplicate"):
                    entry["duplicate"] = True
                    skipped.append(entry)
                else:
                    deposited.append(entry)
            except Exception as e:
                errors.append({"id": qid, "error": str(e)})

    return {
        "deposited": len(deposited),
        "skipped_duplicates": len(skipped),
        "errors": len(errors),
        "details": {"deposited": deposited, "skipped": skipped, "errors": errors},
    }


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    qf = sys.argv[sys.argv.index("--questions") + 1] if "--questions" in sys.argv else None
    result = seed(dry_run=dry, questions_file=qf)
    print(json.dumps(result, indent=2))
    if result["errors"]:
        sys.exit(1)
