"""intentions_model_compiler/compiler.py — the ``intentions/`` MODEL is COMPILED
from its sources, never authored by hand.

This is the OUTER row of the three-scale projector recursion (the store charter,
``CairnCommons/intentions/_charter+why.json``, names it):

  - ticket scale:    a charter's ``history`` -> its bounded ``state`` window
                     (``cairn/charter/projector.py`` — the kin, built and green)
  - component scale:  a component's design -> its charter (authored precipitate)
  - SYSTEM scale:     ALL sources -> ``intentions/`` (this module)

Same move each time (Law 1): compile a bounded view over an append-only source so no
mind re-derives it by reading everything. Here the "source" is the whole intent corpus,
in two places at once:

  1. ``CairnCommons/intentions-other/``  — the homeless intentions (the roots, the
     concept-pieces, the host-seams, the spanning ones); the prose IS the implementation
     or the machine-readiness that a bare repo needs to actually RUN.
  2. ``cairn/*/intention+why.json``      — the beside-code charters (the code-seams).

The seed claim (the store charter): take this one folder to a bare machine and regrow the
system. That only works if BOTH sources compile in — the charters alone regrow a repo
that does not run. So the compiled model EMBEDS each source's content: the one artifact is
self-contained.

The contract (why this door exists):
  - ONE write-door: ``compile_to_disk`` is the sole writer of ``intentions/_model.json``
    (Law 6 — exactly one owner gates writes to the compiled view; the IOU in CLAUDE.md
    'Rules awaiting physics' is closed by physics the day the tester import-scans for a
    second writer). A hand-edit to the model is REVERTED on the next compile — the view
    is never a record of truth (Law 7); the sources are.
  - DETERMINISTIC + LOSSLESS: same sources -> same bytes; every source represented,
    nothing invented; a removed source removes its projection (the model is regenerated
    whole, so removal propagates for free — no stale carry-over).
  - ROOTS SURFACE FIRST BY PHYSICS (Law 4, the store charter, Akien 2026-07-22): the
    compile is ordered by each source's BORN timestamp, so ``telos.md`` and
    ``core-values.md`` (the oldest records, the day the repo was founded) sort to the top
    of the model — the frame is first by construction, not by a special case.

Kin, not merged (ticket intentions-model-compiler, cross-ref charter-state-history-split):
the projector compiles one component's state from its own history; this compiles the
system-wide model from all sources. Same pattern, different corpus and owner. If the two
ever share real projection machinery, factor the core out THEN — not before the second
member proves the seam.

The BORN timestamp's source is a today-shape (like the projector's file layer): git's
first-commit date for the file — deterministic, and it SURVIVES a fresh checkout (file
mtime does not; on a bare machine every file's mtime is checkout time). An uncommitted or
git-less file sorts LAST (a far-future sentinel): not yet born in the record. The pure
core does not know about git — it takes ``born`` as data, so it stays testable without a
repo, and the timestamp source is swappable.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile

# A source not yet in the git record sorts last — "not yet born" — deterministically.
_UNBORN = "9999-12-31T23:59:59+00:00"

_DO_NOT_EDIT = (
    "COMPILED VIEW — do not hand-edit. Written only by "
    "intentions_model_compiler.compile_to_disk; any edit here is reverted on the next "
    "compile. To change the model, change a source in intentions-other/ or a charter "
    "beside its code, then recompile (Law 4 / Law 7)."
)


# ── the pure core: the model is a function of its sources ─────────────────────


def compile_model(sources: list[dict]) -> dict:
    """Compile the system-scale model from ``sources`` — deterministic, lossless.

    Each source is ``{"id", "kind", "source", "born", "content"}``. The model orders them
    by (born, source) so the roots (oldest) surface first by physics (Law 4), ties broken
    by path for a stable, byte-deterministic result. Every source is represented and its
    content carried verbatim; nothing is invented. Same sources in -> same model out,
    which is exactly why the persisted view can never diverge from the truth.
    """
    ordered = sorted(sources, key=lambda s: (s.get("born", _UNBORN), s["source"]))
    return {
        "_do_not_edit": _DO_NOT_EDIT,
        "compiled_from": ["intentions-other/", "cairn/*/intention+why.json"],
        "count": len(ordered),
        "intentions": [
            {
                "id": s["id"],
                "kind": s["kind"],
                "source": s["source"],
                "born": s.get("born", _UNBORN),
                "content": s["content"],
            }
            for s in ordered
        ],
    }


# ── the today-shape: read the two source trees, born from git, one write-door ─


def _born(path: str) -> str:
    """The file's BIRTH (author) date, traced through renames — deterministic, and it
    survives a fresh checkout (file mtime does not).

    ``--follow`` is load-bearing, not a nicety: intentions RELOCATE. The roots were born
    2026-07-14 ('the Telos as first stone') and only MOVED into ``intentions-other/`` on
    2026-07-22 ('the roots come home'). Plain first-add sees the move (2026-07-22) and
    sinks the frame into the middle of the model; ``--follow`` traces past the rename to
    the true birth (2026-07-14), which is what makes 'roots surface first' hold by physics
    (Law 4) rather than needing a hand-placed born marker.

    Falls back to the far-future sentinel for an uncommitted or git-less file, so a
    not-yet-recorded source sorts last rather than crashing the compile (CP2 — a missing
    timestamp is a disposition, not a fatal).
    """
    directory = os.path.dirname(path) or "."
    try:
        out = subprocess.run(
            ["git", "-C", directory, "log", "--follow", "--format=%aI", "--",
             os.path.basename(path)],
            capture_output=True, text=True, check=True,
        ).stdout.strip().splitlines()
        return out[-1] if out else _UNBORN     # the LAST line is the earliest (birth) commit
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return _UNBORN


def _read_content(path: str):
    """Embed a source verbatim: a .json source as its parsed object, anything else as text.

    Parsing json keeps the model queryable; carrying prose (.md) as text keeps it lossless.
    """
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    if path.endswith(".json"):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw                          # a malformed json source is carried as-is,
    return raw                                  # loud by staying unparsed, never dropped


def gather_sources(commons_root: str, code_root: str) -> list[dict]:
    """Read both source trees into the pure core's source shape.

    intentions-other/  -> every file NOT prefixed ``_`` (the ``_charter+why.json`` that
                          governs the store is not itself an intention).
    cairn/*/            -> every ``intention+why.json`` beside a component's code.
    """
    sources: list[dict] = []

    other = os.path.join(commons_root, "intentions-other")
    if os.path.isdir(other):
        for name in sorted(os.listdir(other)):
            if name.startswith("_") or name.startswith("."):
                continue
            path = os.path.join(other, name)
            if not os.path.isfile(path):
                continue
            stem = name.rsplit(".", 1)[0]
            sources.append({
                "id": stem,
                "kind": "homeless",
                "source": f"intentions-other/{name}",
                "born": _born(path),
                "content": _read_content(path),
            })

    for component in sorted(os.listdir(code_root) if os.path.isdir(code_root) else []):
        charter = os.path.join(code_root, component, "intention+why.json")
        if os.path.isfile(charter):
            sources.append({
                "id": component,
                "kind": "component-charter",
                "source": f"{os.path.basename(code_root)}/{component}/intention+why.json",
                "born": _born(charter),
                "content": _read_content(charter),
            })

    return sources


def _atomic_write(path: str, data) -> None:
    """Write JSON via temp file + rename, so a reader never sees a half-written model."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _default_roots() -> tuple[str, str]:
    """code_root = the cairn PACKAGE dir (where components berth); commons_root = its
    sibling CairnCommons repo (both overridable).

    Derived from ``__file__`` so the door needs no absolute paths baked in — the same way
    the proofs compute their root — and works after a fresh clone. The beside-code charters
    live at ``<repo>/cairn/<component>/intention+why.json``, so the scan root is the
    package dir ``<repo>/cairn``, not the repo root.
    """
    code_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # <repo>/cairn
    repo_root = os.path.dirname(code_root)                                    # <repo>
    commons_root = os.path.join(os.path.dirname(repo_root), "CairnCommons")   # sibling repo
    return commons_root, code_root


def model_path(commons_root: str) -> str:
    """The single compiled artifact — beside the store's own charter, never overwriting it."""
    return os.path.join(commons_root, "intentions", "_model.json")


def compile_to_disk(
    commons_root: str | None = None,
    code_root: str | None = None,
    out_path: str | None = None,
) -> dict:
    """THE ONE WRITE-DOOR: gather both source trees, project, write the model. Returns it.

    This is the sole writer of ``intentions/_model.json``. It touches nothing else in
    ``intentions/`` — the store's ``_charter+why.json`` is a hand-authored source, left
    alone. Any prior model on disk (including a hand-edit) is overwritten by the fresh
    projection: the view is never authoritative (Law 7).
    """
    d_commons, d_code = _default_roots()
    commons_root = commons_root or d_commons
    code_root = code_root or d_code
    out_path = out_path or model_path(commons_root)

    model = compile_model(gather_sources(commons_root, code_root))
    _atomic_write(out_path, model)
    return model


if __name__ == "__main__":       # a bare hand-crank: `python3 -m ...compiler` compiles once
    m = compile_to_disk()
    print(f"compiled {m['count']} intentions -> intentions/_model.json "
          f"(roots first: {[i['id'] for i in m['intentions'][:2]]})")
