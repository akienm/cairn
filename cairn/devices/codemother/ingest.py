"""codemother/ingest.py — parse training data sources into negative types.

Reads CC memory files, transcripts, learning records, rulings, and git history
to produce negative types capturing failure modes, corrections, and constraints.
Each CC-- marker and each memory file's failure mode becomes at least one
negative type with a why.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from cairn.devices.codemother.types import negative, positive, PatternType, PatternSignal
from cairn.devices.codemother.project import ensure_project, save_type


def ingest_memory_files(memory_dir: str | Path) -> list[PatternType]:
    """Parse CC memory .md files with YAML frontmatter into negative types.

    Each file with metadata.type == 'feedback' becomes a negative type.
    The file body carries the why.
    """
    memory_dir = Path(memory_dir)
    types = []
    if not memory_dir.is_dir():
        return types

    for f in sorted(memory_dir.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        text = f.read_text(errors="replace")
        frontmatter, body = _parse_frontmatter(text)
        if not frontmatter:
            continue

        meta_type = (frontmatter.get("metadata", {}) or {}).get("type", "")
        if meta_type != "feedback":
            continue

        name = frontmatter.get("name", f.stem)
        description = frontmatter.get("description", "")
        signals = []
        if description:
            signals.append(PatternSignal(description=description))

        why = body.strip() if body.strip() else description
        types.append(negative(
            name=name,
            why=why,
            signals=tuple(signals),
            source=f"cc-memory:{f.name}",
            tags=("cc-feedback", "memory-file"),
        ))

    return types


def ingest_reflections(records: list[dict]) -> list[PatternType]:
    """Turn /sail's post-build reflections (ticket 68f563403c8f) into pattern types.

    ``records`` are data_recorder records as the held charter backpack returns them; the
    ones that count carry ``metadata.type == "feedback"`` and a dict ``reflection`` (the
    ``feedback`` verb on the shim writes exactly that). A below-par reflection becomes ONE
    negative type whose why is its flags; an at-par one becomes ONE positive type — the
    "packet was fine" data point codemother needs to know what is working. Both are tagged
    ``cc-feedback`` like the memory-file types above, because that is what they are: CC's
    own record of what its upstream got right and wrong.
    """
    types: list[PatternType] = []
    for rec in records or []:
        if not isinstance(rec, dict):
            continue
        meta = rec.get("metadata") or {}
        packet = rec.get("reflection")
        if (meta.get("type") if isinstance(meta, dict) else None) != "feedback" or not isinstance(packet, dict):
            continue
        ticket = str(packet.get("ticket", "?"))
        findings = [f for f in (packet.get("findings") or []) if isinstance(f, dict)]
        flags = [f for f in findings if f.get("kind") == "flag"]
        praise = [f for f in findings if f.get("kind") == "praise"]
        signals = tuple(PatternSignal(description=f"{f.get('artifact')}.{f.get('field')}: {f.get('text')}")
                        for f in (flags if packet.get("at_par") is False else praise))
        if packet.get("at_par") is False:
            why = "; ".join(f"{f.get('artifact')}.{f.get('field')}: {f.get('text')} — would change: "
                            f"{f.get('would_change')}" for f in flags) or "below par, no flag named"
            types.append(negative(name=f"reflection:{ticket}", why=why, signals=signals,
                                  source=f"cc-reflection:{ticket}", tags=("cc-feedback", "reflection")))
        else:
            why = "at par" + ("; " + "; ".join(f"{f.get('artifact')}.{f.get('field')}: {f.get('text')}"
                                             for f in praise) if praise else "")
            types.append(positive(name=f"reflection:{ticket}", why=why, signals=signals,
                                  source=f"cc-reflection:{ticket}", tags=("cc-feedback", "reflection", "at-par")))
    return types


def ingest_transcripts(transcript_dir: str | Path) -> list[PatternType]:
    """Scan JSONL transcripts for CC-- markers and extract negative types.

    Each CC-- marker in a user message becomes a negative type with the
    surrounding context as the why.
    """
    transcript_dir = Path(transcript_dir)
    types = []
    if not transcript_dir.is_dir():
        return types

    cc_minus_pattern = re.compile(r"CC\s*-{2,}", re.IGNORECASE)

    for f in sorted(transcript_dir.glob("*.jsonl")):
        try:
            for line in f.open(errors="replace"):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                content = _extract_content(record)
                if not content or not cc_minus_pattern.search(content):
                    continue
                snippet = content[:500]
                types.append(negative(
                    name=f"cc-minus-{f.stem}-{len(types)}",
                    why=snippet,
                    signals=(PatternSignal(description="CC-- correction marker"),),
                    source=f"transcript:{f.name}",
                    tags=("cc-correction", "transcript"),
                ))
        except OSError:
            continue

    return types


def ingest_all(memory_dir: str | Path, transcript_dirs: list[str | Path],
               project: str) -> list[PatternType]:
    """Run all ingestion sources and deposit to the project's type library."""
    all_types = []

    all_types.extend(ingest_memory_files(memory_dir))

    for td in transcript_dirs:
        all_types.extend(ingest_transcripts(td))

    ensure_project(project)
    for t in all_types:
        save_type(project, t)

    return all_types


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter from markdown body.

    Parses simple key: value YAML without requiring pyyaml.
    Handles nested metadata.type by looking for indented keys.
    """
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        fm: dict = {}
        current_key = None
        current_sub: dict = {}
        for line in parts[1].strip().split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if line.startswith("  ") and current_key and ":" in stripped:
                k, _, v = stripped.partition(":")
                current_sub[k.strip()] = v.strip()
            else:
                if current_key and current_sub:
                    fm[current_key] = current_sub
                    current_sub = {}
                if ":" in stripped:
                    k, _, v = stripped.partition(":")
                    v = v.strip()
                    if v:
                        fm[k.strip()] = v
                        current_key = None
                    else:
                        current_key = k.strip()
                        current_sub = {}
        if current_key and current_sub:
            fm[current_key] = current_sub
        return fm, parts[2]
    except Exception:
        return {}, text


def _extract_content(record: dict) -> str:
    """Extract text content from a transcript JSONL record."""
    if isinstance(record.get("content"), str):
        return record["content"]
    if isinstance(record.get("message"), dict):
        msg = record["message"]
        if isinstance(msg.get("content"), str):
            return msg["content"]
        if isinstance(msg.get("content"), list):
            return " ".join(
                b.get("text", "") for b in msg["content"]
                if isinstance(b, dict) and b.get("type") == "text"
            )
    return ""
