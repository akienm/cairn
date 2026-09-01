"""quarry_index compiler — one-time, deduped index of TheIgorsProject's articulated layer.

Reads the prior system's design docs, decisions, subsystem_index, rules, and tickets
(as pointers only). Deduplicates across the 4+ duplicate trees by content hash. Every
entry carries an UNPROVEN-PRIOR-SYSTEM stamp (Law 8 — nothing enters proven-space
without a proof a hollow build couldn't pass).

Inference-free: pure Python, no LLM calls. The index is a lookup table compiled once.

Provenance: ticket quarry-index, cast 2026-07-26 — three stumbles on already-solved
work in one session (the Channel pattern, calving thresholds, and the node record
envelope all existed in ~/TheIgorsProject and were re-derived from scratch).

CLI:
  python3 -m cairn.machines.quarry_index.compiler           # compile and write
  python3 -m cairn.machines.quarry_index.compiler --dry-run  # compile and print stats
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

QUARRY_ROOT = Path.home() / "TheIgorsProject"
CANONICAL_TREES = [
    QUARRY_ROOT / "theigors" / "theigors",
    QUARRY_ROOT / "design_docs",
]
OUTPUT_DIR = Path.home() / "dev" / "src" / "CairnCommons" / "quarry"

STAMP = "UNPROVEN-PRIOR-SYSTEM"


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _extract_title(text: str, path: Path) -> str:
    for line in text.split("\n")[:5]:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def _extract_summary(text: str, max_len: int = 300) -> str:
    lines = text.split("\n")
    for line in lines[:10]:
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("**Path"):
            return line[:max_len]
    return ""


def _read_md(path: Path) -> dict | None:
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return None
    return {
        "title": _extract_title(text, path),
        "summary": _extract_summary(text),
        "content_hash": _hash(text),
        "size_bytes": len(text.encode()),
        "path": str(path),
    }


def _read_json_ticket(path: Path) -> dict | None:
    try:
        text = path.read_text(errors="replace")
        data = json.loads(text)
    except (OSError, json.JSONDecodeError):
        return None
    return {
        "id": data.get("id", path.stem),
        "title": data.get("intention", data.get("title", path.stem))[:200],
        "status": data.get("status", data.get("workflow_and_state", data.get("state", "unknown")))[:100],
        "content_hash": _hash(text),
        "path": str(path),
    }


def _find_all_trees(root: Path, dir_name: str) -> list[Path]:
    return sorted(p for p in root.rglob(dir_name) if p.is_dir()
                  and "__pycache__" not in str(p))


def _dedup_entries(entries: list[dict], key: str = "content_hash") -> tuple[list[dict], int]:
    seen: dict[str, dict] = {}
    dupes = 0
    for entry in entries:
        h = entry[key]
        if h in seen:
            existing = seen[h]
            if "also_at" not in existing:
                existing["also_at"] = []
            existing["also_at"].append(entry["path"])
            dupes += 1
        else:
            seen[h] = entry
    return list(seen.values()), dupes


def compile_subsystem_index() -> list[dict]:
    entries = []
    for tree in _find_all_trees(QUARRY_ROOT, "subsystem_index"):
        for md in sorted(tree.glob("*.md")):
            info = _read_md(md)
            if info:
                info["layer"] = "subsystem_index"
                info["provenance"] = STAMP
                entries.append(info)
    deduped, n = _dedup_entries(entries)
    return deduped


def compile_design_docs() -> list[dict]:
    entries = []
    for tree in _find_all_trees(QUARRY_ROOT, "design_docs"):
        for md in sorted(tree.rglob("*.md")):
            if "decisions" in str(md.relative_to(tree)):
                continue
            info = _read_md(md)
            if info:
                info["layer"] = "design_docs"
                info["provenance"] = STAMP
                entries.append(info)
        for jf in sorted(tree.rglob("*.json")):
            if "decisions" in str(jf.relative_to(tree)):
                continue
            info = _read_md(jf)
            if info:
                info["layer"] = "design_docs"
                info["provenance"] = STAMP
                entries.append(info)
    deduped, n = _dedup_entries(entries)
    return deduped


def compile_decisions() -> list[dict]:
    entries = []
    for tree in _find_all_trees(QUARRY_ROOT, "decisions"):
        for f in sorted(tree.iterdir()):
            if f.suffix in (".md", ".json") and f.is_file():
                info = _read_md(f)
                if info:
                    info["layer"] = "decisions"
                    info["provenance"] = STAMP
                    entries.append(info)
    deduped, n = _dedup_entries(entries)
    return deduped


def compile_rules() -> list[dict]:
    entries = []
    rules_dir = QUARRY_ROOT / "theigors" / "theigors" / "rules"
    if rules_dir.is_dir():
        for f in sorted(rules_dir.iterdir()):
            if f.suffix == ".md" and f.is_file():
                info = _read_md(f)
                if info:
                    info["layer"] = "rules"
                    info["provenance"] = STAMP
                    entries.append(info)
    return entries


def compile_tickets() -> list[dict]:
    entries = []
    for tree in _find_all_trees(QUARRY_ROOT, "tickets"):
        for jf in sorted(tree.glob("*.json")):
            info = _read_json_ticket(jf)
            if info:
                info["layer"] = "tickets"
                info["provenance"] = STAMP
                entries.append(info)
        for md in sorted(tree.glob("*.md")):
            info = _read_md(md)
            if info:
                info["layer"] = "tickets"
                info["provenance"] = STAMP
                entries.append(info)
    deduped, n = _dedup_entries(entries)
    return deduped


def compile() -> dict:
    subsystem = compile_subsystem_index()
    design = compile_design_docs()
    decisions = compile_decisions()
    rules = compile_rules()
    tickets = compile_tickets()

    index = {
        "quarry": "TheIgorsProject",
        "compiled": "2026-08-20",
        "provenance": STAMP,
        "note": "Ideas to steal, not code (Akien 2026-07-26). Every entry is "
                "hypothesis-class by construction. Grafting requires a ticket and proof.",
        "layers": {
            "subsystem_index": {
                "description": "TheIgorsProject's own compiled subsystem summaries (14 subsystems)",
                "count": len(subsystem),
                "entries": subsystem,
            },
            "design_docs": {
                "description": "Design documents, standards, gap analyses, architecture docs",
                "count": len(design),
                "entries": design,
            },
            "decisions": {
                "description": "Recorded design decisions (D-prefix)",
                "count": len(decisions),
                "entries": decisions,
            },
            "rules": {
                "description": "Operational rules and conventions",
                "count": len(rules),
                "entries": rules,
            },
            "tickets": {
                "description": "Tickets as pointers only (id, title, status, path) — not summarized",
                "count": len(tickets),
                "entries": tickets,
            },
        },
        "totals": {
            "subsystem_index": len(subsystem),
            "design_docs": len(design),
            "decisions": len(decisions),
            "rules": len(rules),
            "tickets": len(tickets),
            "total": len(subsystem) + len(design) + len(decisions) + len(rules) + len(tickets),
        },
    }
    return index


def _search(index: dict, query: str) -> list[dict]:
    query_lower = query.lower()
    results = []
    for layer_name, layer in index["layers"].items():
        for entry in layer["entries"]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            if query_lower in title.lower() or query_lower in summary.lower():
                results.append({**entry, "matched_layer": layer_name})
    return results


def write_index(index: dict, output: Path | None = None) -> Path:
    out = output or OUTPUT_DIR / "index.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, indent=2, ensure_ascii=False))
    return out


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    if not QUARRY_ROOT.is_dir():
        print(f"quarry_index: quarry not found at {QUARRY_ROOT}", file=sys.stderr)
        sys.exit(1)

    index = compile()

    print(f"quarry_index: compiled {index['totals']['total']} entries")
    for layer, count in index["totals"].items():
        if layer != "total":
            print(f"  {layer}: {count}")

    for pattern_name, query in [
        ("Channel pattern", "channel"),
        ("calving", "calving"),
        ("node record / memory", "memory"),
    ]:
        hits = _search(index, query)
        print(f"\n  falsifier check '{pattern_name}': {len(hits)} hit(s)")
        for h in hits[:3]:
            print(f"    [{h['matched_layer']}] {h.get('title', h.get('id', '?'))[:80]}")

    if dry_run:
        print("\n  --dry-run: not writing.")
    else:
        out = write_index(index)
        print(f"\n  written to {out}")
