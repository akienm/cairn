"""cairn codemother retire <path>... — delete code, checking its callers in the same act (ticket
750ead1af9c1; outline 1.3.7.1.1, Akien 2026-11-17).

A caller is told from a mention by running proofs, never by reading text: the proofs among the
files that name a target, plus the proofs of each component whose code names it, run once with the
targets in place and once with them moved aside. A proof green before and red after is a caller,
and every target goes back. A proof already red before cannot measure anything and is reported as
such, as is a code namer with no proof to run. Nothing checks afterwards, and nothing is committed.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from cairn.tools.windowless_spawn.windowless_spawn import windowless_kwargs

USAGE = "usage: cairn codemother retire <path>...   (repo-relative paths to delete)"
_SKIP_DIRS = {"__pycache__", "validations"}
_RECORDS = {"history.json", "state.json"}
_CODE_SUFFIXES = {".py", ".sh"}


def _rel(repo: Path, p: Path) -> str:
    return p.relative_to(repo).as_posix()


def needles(target: str) -> list[str]:
    """What a namer would hold: the repo path, and for code under cairn/ or skills/ its dotted
    module."""
    out = [target.rstrip("/")]
    t = out[0]
    if t.split("/", 1)[0] in ("cairn", "skills"):
        mod = t[:-3] if t.endswith(".py") else t
        if not mod.endswith("__init__"):
            out.append(mod.replace("/", "."))
    return out


def _is_proof(rel: str) -> bool:
    parts = rel.split("/")
    return len(parts) >= 2 and parts[-2] == "proofs" and parts[-1].startswith("test_") \
        and parts[-1].endswith(".py")


def _is_code(rel: str) -> bool:
    return Path(rel).suffix in _CODE_SUFFIXES or "/bin/" in f"/{rel}"


def namers(repo: Path, targets: list[str]) -> list[str]:
    """Repo files whose text holds a target's needle. Records of truth (history.json, state.json,
    validations/, verdict-*.json), dot-files, dot-folders, caches and the targets themselves are
    never namers: they name what passed through, they do not call it."""
    repo = Path(repo)
    tset = {t.rstrip("/") for t in targets}
    ns = [n for t in targets for n in needles(t)]
    hits: list[str] = []
    for root, dirs, files in os.walk(repo):
        rr = Path(root)
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in _SKIP_DIRS
                         and not d.endswith(".egg-info") and _rel(repo, rr / d) not in tset)
        for f in sorted(files):
            if f.startswith(".") or f in _RECORDS or (f.startswith("verdict-") and f.endswith(".json")):
                continue
            p = rr / f
            rel = _rel(repo, p)
            if rel in tset:
                continue
            try:
                text = p.read_text(errors="ignore")
            except OSError:
                continue
            if any(n in text for n in ns):
                hits.append(rel)
    return hits


def _component_proofs(repo: Path, rel: str) -> list[str]:
    """Every proofs/test_*.py of the nearest ancestor holding intention+why.json."""
    d = (repo / rel).parent
    while d != repo and repo in d.parents:
        if (d / "intention+why.json").exists():
            pd = d / "proofs"
            return sorted(_rel(repo, p) for p in pd.glob("test_*.py")) if pd.is_dir() else []
        d = d.parent
    return []


def proofs_for(repo: Path, names: list[str]) -> tuple[list[str], list[str], list[str]]:
    """(proofs to run, code namers with no proof, prose namers not run)."""
    repo = Path(repo)
    proofs: list[str] = []
    unmeasured: list[str] = []
    not_run: list[str] = []
    for rel in names:
        if _is_proof(rel):
            found = [rel]
        elif _is_code(rel):
            found = _component_proofs(repo, rel)
            if not found:
                unmeasured.append(rel)
        else:
            not_run.append(rel)
            continue
        proofs.extend(p for p in found if p not in proofs)
    return proofs, unmeasured, not_run


def tester_runner(repo: Path, proofs: list[str]) -> dict[str, str]:
    """Each proof through the tester's door, one at a time; its exit code is the verdict."""
    out: dict[str, str] = {}
    for p in proofs:
        r = subprocess.run([str(Path(repo) / "bin" / "cairn"), "test", p], cwd=repo,
                           capture_output=True, text=True, **windowless_kwargs())
        out[p] = "green" if r.returncode == 0 else "red"
    return out


def forwarders(commons: Path, targets: list[str]) -> list[str]:
    """Tickets whose forwarding order sends a retired address TO a target. The census proofs read
    those orders as live pointers (cairn.tools.base.watchme_spec.forwarded_paths: `to` must be
    present), so each one is a caller no text search of the repo can see (measured 2026-11-17:
    ten ticket records forwarded to the stays-gone proof this command's first use retired)."""
    tset = {t.rstrip("/") for t in targets}
    out: list[str] = []
    td = Path(commons) / "tickets"
    for f in sorted(td.glob("*.json")) if td.is_dir() else []:
        try:
            doc = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        order = doc.get("forwarding") if isinstance(doc, dict) else None
        if not isinstance(order, dict):
            continue
        for old, entry in order.items():
            if isinstance(entry, dict) and str(entry.get("to", "")).rstrip("/") in tset:
                out.append(f"{f.relative_to(commons).as_posix()} forwards {old}")
    return out


def _is_record(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return "/validations/" in f"/{rel}" or name in _RECORDS or name == "intention+why.json"


def door_remover(repo: Path, rel: str) -> None:
    subprocess.run([str(Path(repo) / "bin" / "cairn"), "artifact", "remove", rel, "--why",
                    "retired by cairn codemother retire: its callers were checked in the act "
                    "(outline 1.3.7.1.1)"], cwd=repo, check=True, capture_output=True, text=True, **windowless_kwargs())


def retire(repo, targets: list[str], runner=None, commons=None, remover=None) -> dict:
    repo = Path(repo).resolve()
    commons = Path(commons) if commons is not None else repo.parent / "CairnCommons"
    runner = runner or tester_runner
    targets = [t.rstrip("/") for t in targets]
    rep = {"exit": 2, "retired": [], "restored": [], "namers": [], "proofs_green": [],
           "callers": [], "red_before": [], "unmeasured": [], "not_run": [], "missing": []}
    rep["missing"] = [t for t in targets if not (repo / t).exists()]
    if not targets or rep["missing"]:
        return rep
    rep["callers"] = forwarders(commons, targets)
    if rep["callers"]:
        rep["restored"] = targets          # nothing was moved: a forwarding order is a caller
        rep["exit"] = 1
        return rep
    rep["namers"] = namers(repo, targets)
    proofs, rep["unmeasured"], rep["not_run"] = proofs_for(repo, rep["namers"])
    before = runner(repo, proofs) if proofs else {}
    rep["red_before"] = [p for p in proofs if before.get(p) != "green"]
    live = [p for p in proofs if before.get(p) == "green"]
    with tempfile.TemporaryDirectory(prefix="cairn-retire-") as aside:
        moved = []
        for i, t in enumerate(targets):
            dst = Path(aside) / str(i)
            shutil.move(str(repo / t), str(dst))
            moved.append((t, dst))
        after = runner(repo, live) if live else {}
        rep["callers"] = [p for p in live if after.get(p) != "green"]
        if rep["callers"]:
            for t, dst in moved:
                shutil.move(str(dst), str(repo / t))
            rep["restored"] = targets
            rep["exit"] = 1
            return rep
        # a record of truth leaves only through its door, which journals the removal (ticket
        # 30531f6e1c5d): put it back and let the artifact door remove it
        for t, dst in moved:
            if _is_record(t):
                shutil.move(str(dst), str(repo / t))
                (remover or door_remover)(repo, t)
    rep["proofs_green"] = live
    rep["retired"] = targets
    rep["exit"] = 0
    return rep


def _report(rep: dict) -> str:
    lines = []
    if rep["exit"] == 2:
        lines.append(USAGE)
        for m in rep["missing"]:
            lines.append(f"  missing  {m}")
        return "\n".join(lines)
    head = "RETIRED" if rep["exit"] == 0 else "RESTORED — a caller turned red with the targets gone"
    lines.append(head)
    for t in rep["retired"] or rep["restored"]:
        lines.append(f"  {'deleted ' if rep['exit'] == 0 else 'restored'}  {t}")
    for c in rep["callers"]:
        lines.append(f"  CALLER   {c}")
    for p in rep["proofs_green"]:
        lines.append(f"  green    {p}")
    for p in rep["red_before"]:
        lines.append(f"  UNMEASURED (red before the deletion)  {p}")
    for p in rep["unmeasured"]:
        lines.append(f"  UNMEASURED (code with no proof)  {p}")
    for p in rep["not_run"]:
        lines.append(f"  names it, not run  {p}")
    if rep["exit"] == 0:
        lines.append("nothing committed: commit the deletion by path")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    targets = [a for a in argv if not a.startswith("-")]
    if not targets or any(a in ("-h", "--help") for a in argv):
        print(USAGE, file=sys.stderr)
        return 2
    repo = Path(__file__).resolve().parents[5]
    rep = retire(repo, targets)
    print(_report(rep), file=sys.stderr if rep["exit"] == 2 else sys.stdout)
    return rep["exit"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
