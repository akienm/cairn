"""codemother/watch.py — the watcher face.

The builder face (the 8 chart machines) proves what CC needs to know before a
build begins. The watcher face monitors the codebase between and during builds,
driven by inference_proxy via the bus — NOT by Claude.

Reasoning path:
  1. Trigger fires (commit, file change, area question)
  2. Spreading activation → query codemother's graph trees
  3. Trees can't resolve → escalate to hex.local (via inference_proxy bus verb)
  4. hex.local produces nodes → re-query the graph trees
  5. Resolved → surface findings via bus post to the operator

The watcher has its own trees whose root questions are part of codemother's root
tree. The trees absorb curriculum (CC failure modes, codebase patterns, past
projects) via the reader + librarian.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cairn.tools.base.address import instance_path
from cairn.tools.base.bus_client import connect_bus

_INSTANCE_ROOT = instance_path("codemother", 0)
_WATCH_LOG = _INSTANCE_ROOT / "watch"
_ACTIVATIONS_DIR = _WATCH_LOG / "activations"

_BUS = None


def _bus():
    global _BUS
    if _BUS is None:
        _BUS = connect_bus(devices=["inference_domain"])
    return _BUS


def _embed(text: str) -> list[float]:
    from cairn.devices.librarian.live import embed_via_bus
    return embed_via_bus(_bus())(text)


def activate(area: str, reason: str, *, context: dict | None = None) -> dict:
    """Spreading activation: query codemother's trees for what matters in this
    area, escalate to hex.local if the trees can't resolve.

    Returns {findings: [...], escalated: bool, tree_hits: int}.
    """
    from cairn.tools.tree.tree import counsel as tree_counsel

    now = datetime.now(timezone.utc)
    record = {
        "timestamp": now.isoformat(),
        "area": area,
        "reason": reason,
        "context": context or {},
    }

    try:
        vector = _embed(area)
    except Exception as e:
        record["error"] = f"embed failed: {e}"
        _log_activation(record)
        return {"findings": [], "escalated": False, "tree_hits": 0, "error": str(e)}

    findings = []
    tree_hits = 0
    escalated = False

    try:
        hits = tree_counsel(
            vector=vector,
            query_text=area,
            owner="codemother",
            k=5,
        )
        tree_hits = len(hits) if hits else 0
        if hits:
            findings.extend(_extract_findings(hits, source="tree"))
    except Exception:
        tree_hits = 0

    if tree_hits == 0:
        escalated = True
        try:
            hex_result = _escalate_to_hex(area, reason, context)
            if hex_result.get("nodes"):
                findings.extend(_extract_findings(hex_result["nodes"], source="hex"))
        except Exception as e:
            record["escalation_error"] = str(e)

    record["findings_count"] = len(findings)
    record["tree_hits"] = tree_hits
    record["escalated"] = escalated
    _log_activation(record)

    return {
        "findings": findings,
        "escalated": escalated,
        "tree_hits": tree_hits,
    }


def on_commit(commit_hash: str, changed_files: list[str], message: str) -> dict:
    """Triggered when a commit lands. Fires spreading activations for the
    areas touched by the commit."""
    areas = _files_to_areas(changed_files)
    results = []
    for area in areas:
        result = activate(
            area,
            reason=f"commit {commit_hash[:8]}: {message[:80]}",
            context={"commit": commit_hash, "files": changed_files},
        )
        if result["findings"]:
            results.append({"area": area, **result})
    return {"commit": commit_hash, "areas_checked": len(areas), "results": results}


def on_question(question: str, area: str | None = None) -> dict:
    """Triggered when someone asks about an area. Fires spreading activation
    to double-check that area."""
    target = area or question
    return activate(
        target,
        reason=f"question: {question[:120]}",
        context={"question": question},
    )


def _escalate_to_hex(area: str, reason: str, context: dict | None) -> dict:
    """Ask hex.local (via inference_proxy) to produce nodes for an area the
    trees couldn't resolve."""
    bus = _bus()
    try:
        reply = bus.request(
            sender="codemother",
            to="inference_domain",
            channel="personal",
            why=f"watcher escalation: trees couldn't resolve area={area!r}",
            verb="infer",
            body={
                "kind": "completion",
                "prompt": (
                    f"As a code analysis assistant, examine the area: {area}\n"
                    f"Reason for check: {reason}\n"
                    f"What patterns, risks, or observations should the codebase "
                    f"watcher note about this area?"
                ),
                "domain": "codemother",
                "model": "qwen",
            },
            timeout=60.0,
        )
        return {"nodes": [{"content": reply.get("body", {}).get("answer", ""), "source": "hex"}]}
    except (TimeoutError, Exception) as e:
        return {"nodes": [], "error": str(e)}


def _files_to_areas(changed_files: list[str]) -> list[str]:
    """Map changed file paths to logical areas (device/machine/tool names)."""
    areas = set()
    for f in changed_files:
        parts = Path(f).parts
        if len(parts) >= 3 and parts[0] == "cairn":
            if parts[1] == "devices" and len(parts) >= 3:
                areas.add(f"cairn/devices/{parts[2]}")
            elif parts[1] == "machines" and len(parts) >= 3:
                areas.add(f"cairn/machines/{parts[2]}")
            elif parts[1] == "tools" and len(parts) >= 3:
                areas.add(f"cairn/tools/{parts[2]}")
        elif len(parts) >= 2 and parts[0] == "skills":
            areas.add(f"skills/{parts[1]}")
    return sorted(areas) if areas else [str(Path(changed_files[0]).parent)] if changed_files else []


def _extract_findings(hits: list, source: str) -> list[dict]:
    """Extract structured findings from tree hits or hex responses."""
    findings = []
    for hit in hits:
        if isinstance(hit, dict):
            findings.append({
                "content": hit.get("content", hit.get("text", str(hit))),
                "source": source,
                "relevance": hit.get("similarity", hit.get("score", None)),
            })
        else:
            findings.append({"content": str(hit), "source": source})
    return findings


def _log_activation(record: dict) -> None:
    """Append an activation record to the watch log."""
    _ACTIVATIONS_DIR.mkdir(parents=True, exist_ok=True)
    ts = record.get("timestamp", datetime.now(timezone.utc).isoformat())
    safe_ts = ts.replace(":", "").replace("+", "")[:20]
    path = _ACTIVATIONS_DIR / f"activation-{safe_ts}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
