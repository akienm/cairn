"""intentions_model_compiler/compiler.py — ``intentions-congruency-lab/`` holds COPIES of
every intention+why in the system. That is the whole job.

  gather every intention -> copy each one into the lab, one file per source.

THE SEED CLAIM (the store charter, ``CairnCommons/intentions-congruency-lab/_charter+why.json``):
take this one folder to a bare machine and regrow the system. A folder of the actual
intention files satisfies that directly — you read them the way you read them anywhere
else. Nothing is aggregated, nothing is re-shaped, nothing is invented.

WHAT THIS USED TO DO, AND WHY IT DOESN'T (Akien, 2026-07-31, unambiguous): it compiled all
the sources into ONE artifact, ``_model.json``, embedding each source's content inside a
JSON envelope ordered by git birth date. That file is DELETED and does not come back. The
envelope was machinery the job never asked for — a second shape for the same bytes, which
is a thing that can drift from what it copies. Copies cannot.

The contract:
  - ONE write-door: ``copy_to_lab`` is the sole writer of ``intentions-congruency-lab/``.
    It never touches the store's own hand-authored ``_charter+why.json`` (that is a source,
    not a copy) and never touches anything prefixed ``_``.
  - THE LAB IS REGENERATED WHOLE. A copy whose source is gone is DELETED on the next run,
    so a removed intention removes its copy — no stale carry-over. A hand-edit to a copy is
    overwritten. The lab is never a record of truth (Law 7); the sources are.
  - EVERY intention+why IN THE REPO IS COPIED, not just ``cairn/*/``. Measured 2026-07-31:
    the old ``cairn/*/`` scan reached 19 of 32, leaving all nine ``skills/*/`` plus
    ``bin/``, ``learning/``, ``launchers/`` and ``press_office/`` out of the folder that
    claims it can regrow the system. A copier that misses 40% of what it copies fails its
    own charter, so the walk is the whole repo.
  - A NAME COLLISION IS LOUD, NEVER LAST-WRITE-WINS (Law 7). Two sources claiming one lab
    filename raises; it does not silently drop one.

Kin, not merged: ``cairn/tools/charter/projector.py`` compiles one component's state from its own
history — a real projection, with a bounded window and a shape of its own. This is not that.
This is a copy. Naming them the same thing is what grew ``_model.json``.
"""

from __future__ import annotations

import os
import shutil

# A homeless intention's filename already stands alone, so it is kept. A beside-code
# charter is always literally ``intention+why.json``, so it is prefixed by the component
# that owns it — otherwise every one of them would claim the same lab filename.
_CHARTER = "intention+why.json"

_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "proofs",
              "validations"}

_LAB = "intentions-congruency-lab"


def lab_filename(source: dict) -> str:
    """The one name a source claims in the lab. Pure — no disk."""
    if source["kind"] == "homeless":
        return os.path.basename(source["source"])
    return f"{source['id']}--{_CHARTER}"


def plan_copies(sources: list[dict]) -> dict[str, str]:
    """Pure core: sources -> {lab filename: absolute source path}.

    Raises on a name collision rather than picking a winner — two intentions cannot share
    one address, and a copier that quietly drops one is the silent-wrong-answer failure
    (Law 7). Deterministic: same sources in, same plan out.
    """
    plan: dict[str, str] = {}
    for s in sorted(sources, key=lambda x: x["source"]):
        name = lab_filename(s)
        if name in plan and plan[name] != s["path"]:
            raise ValueError(
                f"lab filename collision: {name!r} claimed by both {plan[name]!r} "
                f"and {s['path']!r}"
            )
        plan[name] = s["path"]
    return plan


# ── the today-shape: walk both source trees ───────────────────────────────────


def gather_sources(commons_root: str, code_root: str) -> list[dict]:
    """Read both source trees into the pure core's source shape.

    ``intentions-not-beside-code/`` -> every file NOT prefixed ``_`` (the ``_charter+why.json``
    that governs the store is a source of its own, not an intention to copy).
    ``<repo>/**/intention+why.json`` -> every beside-code charter, anywhere in the repo.
    """
    sources: list[dict] = []

    homeless_dir = os.path.join(commons_root, "intentions-not-beside-code")
    if os.path.isdir(homeless_dir):
        for name in sorted(os.listdir(homeless_dir)):
            if name.startswith("_") or name.startswith("."):
                continue
            path = os.path.join(homeless_dir, name)
            if not os.path.isfile(path):
                continue
            sources.append({
                "id": name.rsplit(".", 1)[0],
                "kind": "homeless",
                "source": f"intentions-not-beside-code/{name}",
                "path": path,
            })

    for dirpath, dirnames, filenames in os.walk(code_root):
        dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS
                             and not d.startswith("."))
        if _CHARTER not in filenames:
            continue
        path = os.path.join(dirpath, _CHARTER)
        rel = os.path.relpath(dirpath, code_root)
        # The owning component's address, flattened whole: cairn/devices/librarian ->
        # cairn-devices-librarian. THE RUNG RIDES THE NAME (2026-08-13) because the name is
        # the address with its separators swapped — it is not a label anyone chose, and
        # dropping the middle segment to keep the old spelling would make two components
        # named `base` in different rungs collide in one flat folder.
        component = "repo-root" if rel == "." else rel.replace(os.sep, "-")
        sources.append({
            "id": component,
            "kind": "component-charter",
            "source": os.path.relpath(path, code_root),
            "path": path,
        })

    return sources


def lab_path(commons_root: str) -> str:
    return os.path.join(commons_root, _LAB)


def _default_roots() -> tuple[str, str]:
    """code_root = the REPO (charters berth all over it, not only under the package);
    commons_root = its sibling CairnCommons. Derived from ``__file__`` so the door needs no
    absolute paths baked in and works after a fresh clone."""
    package_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # <repo>/cairn
    repo_root = os.path.dirname(package_dir)                                   # <repo>
    commons_root = os.path.join(os.path.dirname(repo_root), "CairnCommons")
    return commons_root, repo_root


def copy_to_lab(
    commons_root: str | None = None,
    code_root: str | None = None,
    out_dir: str | None = None,
) -> dict:
    """THE ONE WRITE-DOOR: gather every intention, copy each into the lab, delete the stale.

    Returns ``{"copied": [...], "removed": [...], "count": n}``. Anything in the lab that is
    not a current copy is REMOVED, so the folder is exactly the corpus — except names
    prefixed ``_``, which are the store's own hand-authored records and are never touched.
    """
    d_commons, d_code = _default_roots()
    commons_root = commons_root or d_commons
    code_root = code_root or d_code
    out_dir = out_dir or lab_path(commons_root)

    # THE TRACE WIRE (deploy pass, approved 2026-08-01): the write-door is a firing.
    # A clean copy traces door_pass; a refusal (the collision raise) traces send_back
    # with the lack named, and still raises exactly as before — the wire observes,
    # never swallows.
    from cairn.machines.learning_block.learning_block import traced
    with traced("intentions_model_compiler", "copy_to_lab"):
        plan = plan_copies(gather_sources(commons_root, code_root))
        os.makedirs(out_dir, exist_ok=True)

        for name, src in plan.items():
            shutil.copyfile(src, os.path.join(out_dir, name))

        removed = []
        for name in sorted(os.listdir(out_dir)):
            if name.startswith("_") or name.startswith("."):
                continue
            if name not in plan:
                target = os.path.join(out_dir, name)
                if os.path.isfile(target):
                    os.remove(target)
                    removed.append(name)

    return {"copied": sorted(plan), "removed": removed, "count": len(plan)}


if __name__ == "__main__":       # a bare hand-crank: `python3 -m ...compiler` copies once
    r = copy_to_lab()
    print(f"copied {r['count']} intention+why files -> {_LAB}/"
          + (f"; removed {len(r['removed'])} stale: {r['removed']}" if r["removed"] else ""))
