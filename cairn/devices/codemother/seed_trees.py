"""codemother/seed_trees.py — plant the cognition questions as root nodes.

Reads cognition_questions.json beside this file, embeds each question, and
deposits it into codemother's graph tree via the librarian's deposit door.
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
from cairn.tools.base.bus_client import connect_bus


QUESTIONS_FILE = Path(__file__).parent / "cognition_questions.json"
OWNER = "codemother"
NEXUS = "root"

EMBED_MODEL = "nomic-embed-text"
_SENDER = "codemother"


def _embed_fn():
    bus = connect_bus(devices=["inference_domain"])
    def embed(text: str):
        reply = bus.request(
            sender=_SENDER, to="inference_domain", verb="resolve",
            why="seed_trees embed", body={"kind": "embed", "prompt": text, "model": EMBED_MODEL},
        )
        return reply["body"]["answer"]["vector"]
    return embed


def seed(*, dry_run: bool = False) -> dict:
    data = json.loads(QUESTIONS_FILE.read_text())
    embed = _embed_fn()

    deposited = []
    skipped = []
    errors = []

    sections = [
        ("cognition", data.get("cognition_questions", [])),
        ("novelty_2026_07_14", data.get("novelty_matrix", {}).get("from_2026_07_14", [])),
        ("novelty_6angle", data.get("novelty_matrix", {}).get("six_angle_additions", [])),
        ("coding_domain", data.get("coding_domain", {}).get("questions", [])),
    ]

    for section_name, questions in sections:
        for q in questions:
            qid = q.get("id", "unknown")
            text = q["question"]
            content = f"{text}\n[{q.get('function', '')}]"

            if dry_run:
                deposited.append({"id": qid, "section": section_name, "content": content[:60]})
                continue

            try:
                got = embed(text)
                vector = got["vector"] if isinstance(got, dict) else got

                provenance = {
                    "source": f"cognition_questions.json#{qid}",
                    "section": section_name,
                    "function": q.get("function", ""),
                    "question_id": qid,
                }

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
    result = seed(dry_run=dry)
    print(json.dumps(result, indent=2))
    if result["errors"]:
        sys.exit(1)
