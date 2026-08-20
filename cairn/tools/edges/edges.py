"""cairn/tools/edges/edges.py — the frontier projector, compiled from charters and questions.

The cairnmap move applied to the frontier: gather every charter's ``filed_edges``
plus the open-*.json questions from CairnCommons, compile one surface. Zero
inference, mutates nothing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from cairn.tools.cairnmap import cairnmap

WIDTH = 78


def gather_edges(repo: Path | None = None) -> tuple[list[dict], list[str]]:
    """Every filed_edge from every charter, tagged with its source component.

    Returns ``(edges, reds)``.  Each edge is ``{"component": str, "label": str,
    "text": str}`` where *label* is the ``(a)``-style prefix if present and
    *text* is the full edge string.
    """
    charters, reds = cairnmap.gather(repo)
    edges: list[dict] = []
    for c in charters:
        filed = c["data"].get("filed_edges", [])
        if not isinstance(filed, list):
            reds.append(f"filed_edges is not a list: {c['rel']}")
            continue
        comp = c["data"].get("component", c["dir"])
        for raw in filed:
            if not isinstance(raw, str):
                reds.append(f"non-string edge in {c['rel']}: {raw!r}")
                continue
            m = re.match(r"^\(([a-z])\)\s*", raw)
            label = m.group(1) if m else ""
            edges.append({"component": comp, "label": label, "text": raw})
    return edges, reds


def gather_questions(commons: Path | None = None) -> tuple[list[dict], list[str]]:
    """Every open-*.json in CairnCommons/questions/.

    Returns ``(questions, reds)``.  Each question carries its parsed data plus
    a ``"resolved"`` key (truthy when the question has a resolution).
    """
    root = commons or cairnmap.commons_root()
    qdir = root / "questions"
    questions: list[dict] = []
    reds: list[str] = []
    if not qdir.is_dir():
        return questions, reds
    for path in sorted(qdir.glob("open-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            reds.append(f"unreadable question: {path.name} — {type(exc).__name__}: {exc}")
            continue
        questions.append({
            "id": data.get("id", path.stem),
            "question": data.get("question", ""),
            "date": data.get("date", ""),
            "raised_by": data.get("raised_by", ""),
            "resolved": data.get("resolved"),
            "path": str(path.name),
        })
    return questions, reds


def render(repo: Path | None = None, commons: Path | None = None) -> str:
    """One frontier surface — filed edges grouped by component, then open questions."""
    edges, reds_e = gather_edges(repo)
    questions, reds_q = gather_questions(commons)
    reds = reds_e + reds_q

    lines: list[str] = []
    lines.append("=" * WIDTH)
    lines.append("FRONTIER — compiled from charters + open questions")
    lines.append("=" * WIDTH)

    # ── filed edges, grouped by component ──
    by_comp: dict[str, list[dict]] = {}
    for e in edges:
        by_comp.setdefault(e["component"], []).append(e)

    lines.append("")
    lines.append(f"── filed edges ({len(edges)} across {len(by_comp)} components) "
                 + "─" * max(0, WIDTH - 50))

    for comp in sorted(by_comp):
        lines.append("")
        lines.append(f"  {comp}")
        for e in by_comp[comp]:
            text = e["text"]
            if len(text) > WIDTH - 6:
                text = text[:WIDTH - 9] + "..."
            lines.append(f"    {text}")

    # ── open questions ──
    still_open = [q for q in questions if not q["resolved"]]
    resolved = [q for q in questions if q["resolved"]]

    lines.append("")
    lines.append(f"── open questions ({len(still_open)} open, {len(resolved)} resolved, "
                 f"{len(questions)} total) " + "─" * max(0, WIDTH - 60))

    if still_open:
        lines.append("")
        for q in still_open:
            lines.append(f"  OPEN  {q['id']}")
            if q["question"]:
                qtext = q["question"]
                if len(qtext) > WIDTH - 10:
                    qtext = qtext[:WIDTH - 13] + "..."
                lines.append(f"        {qtext}")
    if resolved:
        lines.append("")
        for q in resolved:
            lines.append(f"  done  {q['id']}")

    # ── reds ──
    if reds:
        lines.append("")
        lines.append(f"── reds ({len(reds)}) " + "─" * max(0, WIDTH - 20))
        for r in reds:
            lines.append(f"  RED: {r}")

    # ── summary ──
    lines.append("")
    lines.append("─" * WIDTH)
    lines.append(f"{len(edges)} edges · {len(still_open)} open questions · "
                 f"{len(resolved)} resolved · {len(reds)} reds")
    lines.append("")
    return "\n".join(lines)
