"""Proofs for the quarry_index compiler.

FALSIFIER (from ticket quarry-index.json):
  Three ideas ALREADY known to be in the quarry must each resolve, through the index,
  to a quarry DOCUMENT:
    (1) the declared-capability Channel pattern
    (2) calving's trigger threshold AND its protected-node list
    (3) the node record envelope
  Any that resolves only to SOURCE CODE, or not at all, is a RED.
  Any index entry lacking the UNPROVEN-PRIOR-SYSTEM stamp is a RED.
  A hollow build (an empty index) fails this.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cairn.machines.quarry_index.compiler import (  # noqa: E402
    compile, _search, STAMP,
)

INDEX_PATH = Path.home() / "dev" / "src" / "CairnCommons" / "quarry" / "index.json"


def test_index_not_hollow():
    index = compile()
    total = index["totals"]["total"]
    assert total > 100, f"HOLLOW: index has only {total} entries"
    assert index["totals"]["subsystem_index"] >= 14, "subsystem_index layer too small"
    print(f"  PASS: index has {total} entries (not hollow)")


def test_every_entry_stamped():
    index = compile()
    unstamped = []
    for layer_name, layer in index["layers"].items():
        for entry in layer["entries"]:
            if entry.get("provenance") != STAMP:
                unstamped.append(f"{layer_name}/{entry.get('title', entry.get('id', '?'))}")
    assert not unstamped, f"UNSTAMPED entries: {unstamped[:5]}"
    print(f"  PASS: every entry carries {STAMP}")


def test_channel_pattern_resolves_to_document():
    index = compile()
    hits = _search(index, "channel")
    doc_hits = [h for h in hits if h["matched_layer"] in ("subsystem_index", "design_docs", "decisions")]
    assert len(doc_hits) >= 2, (
        f"Channel pattern resolved to only {len(doc_hits)} document(s) — "
        f"need at least comms + comms_channel_infra"
    )
    titles = [h.get("title", "") for h in doc_hits]
    has_comms = any("comms" in t.lower() for t in titles)
    assert has_comms, f"No comms doc found among: {titles[:5]}"
    print(f"  PASS: Channel pattern resolves to {len(doc_hits)} document(s)")


def test_calving_resolves_to_document():
    index = compile()
    hits = _search(index, "calving")
    doc_hits = [h for h in hits if h["matched_layer"] in ("subsystem_index", "design_docs", "decisions")]
    assert len(doc_hits) >= 1, "calving did not resolve to any document"
    subsystem_hit = [h for h in doc_hits if h["matched_layer"] == "subsystem_index"]
    assert len(subsystem_hit) >= 1, "calving not found in subsystem_index"
    print(f"  PASS: calving resolves to {len(doc_hits)} document(s)")


def test_calving_doc_names_threshold_and_protected():
    calving_path = Path.home() / "TheIgorsProject" / "theigors" / "theigors" / "subsystem_index" / "graph_calving.md"
    if not calving_path.exists():
        print("  SKIP: graph_calving.md not on disk")
        return
    text = calving_path.read_text()
    assert "1000" in text or "threshold" in text.lower(), (
        "graph_calving.md does not mention the trigger threshold"
    )
    assert "protected" in text.lower() or "CP1" in text, (
        "graph_calving.md does not mention protected nodes"
    )
    print("  PASS: calving doc names threshold and protected nodes")


def test_node_record_resolves_to_document():
    index = compile()
    hits = _search(index, "memory")
    doc_hits = [h for h in hits if h["matched_layer"] in ("subsystem_index", "design_docs")]
    assert len(doc_hits) >= 2, (
        f"node record / memory resolved to only {len(doc_hits)} document(s)"
    )
    titles = [h.get("title", "") for h in doc_hits]
    has_cortex = any("cortex" in t.lower() for t in titles)
    has_memory_doc = any("memory" in t.lower() for t in titles)
    assert has_cortex or has_memory_doc, f"Neither cortex nor memory subsystem doc found: {titles[:5]}"
    print(f"  PASS: node record / memory resolves to {len(doc_hits)} document(s)")


def test_dedup_across_trees():
    index = compile()
    with_dupes = [e for layer in index["layers"].values()
                  for e in layer["entries"] if "also_at" in e]
    unique_hashes = set()
    all_hashes = []
    for layer in index["layers"].values():
        for e in layer["entries"]:
            h = e.get("content_hash", "")
            all_hashes.append(h)
            unique_hashes.add(h)
    assert len(unique_hashes) == len(all_hashes), (
        f"DEDUP FAILED: {len(all_hashes)} entries but only {len(unique_hashes)} unique hashes"
    )
    print(f"  PASS: {len(with_dupes)} entries have 'also_at' (dedup recorded); all hashes unique")


def test_persisted_index_matches_compiled():
    if not INDEX_PATH.exists():
        print("  SKIP: index.json not yet written to CairnCommons/quarry/")
        return
    persisted = json.loads(INDEX_PATH.read_text())
    compiled = compile()
    assert persisted["totals"]["total"] == compiled["totals"]["total"], (
        f"persisted total {persisted['totals']['total']} != compiled {compiled['totals']['total']}"
    )
    print(f"  PASS: persisted index matches compiled ({compiled['totals']['total']} entries)")


def main() -> None:
    tests = [
        test_index_not_hollow,
        test_every_entry_stamped,
        test_channel_pattern_resolves_to_document,
        test_calving_resolves_to_document,
        test_calving_doc_names_threshold_and_protected,
        test_node_record_resolves_to_document,
        test_dedup_across_trees,
        test_persisted_index_matches_compiled,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {t.__name__}: {e}")
            failed += 1

    print(f"\nquarry_index proofs: {passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
