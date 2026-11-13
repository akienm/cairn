"""The outside-readers census (ticket 46851816800f, child 1 of e78c9858f5fb).

Lists, per box, every file OUTSIDE cairn and CairnCommons that names a record of truth by its
.json name. It splits them into READERS (code or config: any hit outside prose) and MENTIONS
(.md/.txt prose), and reports every declared root as scanned or absent. Read-only: it opens
files and runs ``crontab -l``, and writes nothing.

The record names come from ``jurisdiction.json`` (the door's one spelling of the record set),
restricted to the names ending in .json, because those are the names the rename changes.

DECLARED, so a later reader can disagree by name:
- the outside roots (``default_roots``): ~/.claude minus the stores that are conversation or
  edit records rather than readers (SKIP_UNDER_CLAUDE), ~/bin, ~/.local/bin,
  ~/.config/systemd/user, /etc/systemd/system, the user crontab, ~/.akien, and every repo
  under ~/dev/src except cairn and CairnCommons;
- inside: anything whose resolved path lies in the cairn repo or CairnCommons. A symlink into
  them, such as a skill under ~/.claude/skills, is inside;
- skipped: files over 2 MB, binary files (a NUL in the first 8 KB), credential files (their
  lines would be printed), and the directories in SKIP_DIRS;
- a hit in PROSE_SUFFIXES is a mention, and any other hit is a reader.

CLI: ``python3 -m cairn.tools.artifact.outside_readers`` prints the census as JSON.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
from pathlib import Path

from cairn.tools.base.address import ROOTS

JURISDICTION = Path(__file__).resolve().parent / "jurisdiction.json"
MAX_BYTES = 2 * 1024 * 1024
PROSE_SUFFIXES = {".md", ".txt"}
SKIP_DIRS = {".git", "__pycache__", "node_modules"}
# Under ~/.claude: projects/ holds transcripts (named by the ticket), file-history/ holds Claude's
# backup copies of files it edited (copies of our own code, not readers), and history.jsonl is
# the prompt log. All three record conversation, and none reads a record.
SKIP_UNDER_CLAUDE = ("projects", "file-history", "history.jsonl")
CREDENTIAL_GLOBS = ("*.credentials.cfg", ".env", "*.env", "*secret*", "*.key", "*.pem")


def default_inside() -> list[Path]:
    return [Path(ROOTS["repo"]).resolve(), Path(ROOTS["commons"]).resolve()]


def default_roots(home: Path | None = None) -> list[dict]:
    """The declared outside roots, each {root, skip}. The crontab is reported separately."""
    home = Path(home or Path.home())
    roots = [{"root": home / ".claude", "skip": [home / ".claude" / s for s in SKIP_UNDER_CLAUDE]},
             {"root": home / "bin"}, {"root": home / ".local" / "bin"},
             {"root": home / ".config" / "systemd" / "user"},
             {"root": Path("/etc/systemd/system")}, {"root": home / ".akien"}]
    src = home / "dev" / "src"
    inside = default_inside()
    if src.is_dir():
        for p in sorted(src.iterdir()):
            if p.is_dir() and not _is_inside(p, inside):
                roots.append({"root": p})
    return [{"root": r["root"], "skip": r.get("skip", [])} for r in roots]


def record_pattern(jurisdiction: Path = JURISDICTION) -> re.Pattern:
    """One regex over every record name in the jurisdiction that ends in .json."""
    doc = json.loads(Path(jurisdiction).read_text())
    alts: list[str] = []
    for root in doc["roots"].values():
        for rec in root["records"]:
            name = rec["name"]
            if not name.endswith(".json"):
                continue
            stem = re.escape(name).replace(r"\*", r"[\w.+\-]*")
            prefix = rec.get("parent") or (rec["under"].rsplit("/", 1)[-1] if "under" in rec else None)
            if "*" in name and prefix:
                alts.append(rf"{re.escape(prefix)}/(?:[\w.+\-]+/)*{stem}")
            else:
                alts.append(stem)
    return re.compile(r"(?<![\w\-])(?:" + "|".join(sorted(set(alts))) + r")(?![\w])")


def _is_inside(p: Path, inside: list[Path]) -> bool:
    try:
        r = p.resolve()
    except OSError:
        return False
    return any(r == i or i in r.parents for i in inside)


def _skippable_file(p: Path) -> bool:
    return any(fnmatch.fnmatch(p.name, g) for g in CREDENTIAL_GLOBS)


def _scan_text(path: str, text: str, pat: re.Pattern, kind: str, out: dict) -> None:
    for n, line in enumerate(text.splitlines(), 1):
        if pat.search(line):
            out[kind].append({"path": path, "line": n, "text": line.strip()[:200]})


def _scan_file(f: Path, pat: re.Pattern, out: dict) -> None:
    try:
        if f.stat().st_size > MAX_BYTES:
            return
        raw = f.read_bytes()
    except OSError:
        return
    if b"\0" in raw[:8192]:
        return
    kind = "mentions" if f.suffix.lower() in PROSE_SUFFIXES else "readers"
    _scan_text(str(f), raw.decode("utf-8", errors="replace"), pat, kind, out)


def _walk(root: Path, skip: list[Path], inside: list[Path], pat: re.Pattern, out: dict) -> None:
    seen: set[Path] = set()
    skip_r = {s.resolve() for s in skip}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        here = Path(dirpath)
        real = here.resolve()
        if real in seen or _is_inside(here, inside):
            dirnames[:] = []
            continue
        seen.add(real)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS
                       and (here / d).resolve() not in skip_r and not _is_inside(here / d, inside)
                       and not (here / d / "pyvenv.cfg").exists()]
        for name in filenames:
            f = here / name
            if f.resolve() in skip_r or _skippable_file(f) or _is_inside(f, inside) or not f.is_file():
                continue
            _scan_file(f, pat, out)


def census(roots=None, inside=None, with_crontab: bool | None = None,
           jurisdiction: Path = JURISDICTION) -> dict:
    """Scan the outside roots. ``roots`` is a list of paths or {root, skip} dicts (default: the
    declared roots); ``inside`` the paths that are ours (default: cairn and CairnCommons). The
    crontab is read by default only when the roots are the declared ones."""
    if with_crontab is None:
        with_crontab = roots is None
    roots = default_roots() if roots is None else roots
    inside = default_inside() if inside is None else [Path(i).resolve() for i in inside]
    pat = record_pattern(jurisdiction)
    out: dict = {"roots": [], "readers": [], "mentions": []}
    for r in roots:
        r = r if isinstance(r, dict) else {"root": r}
        root = Path(r["root"])
        if not root.exists():
            out["roots"].append({"root": str(root), "status": "absent"})
            continue
        if root.is_file():
            if not _is_inside(root, inside):
                _scan_file(root, pat, out)
        else:
            _walk(root, [Path(s) for s in r.get("skip", [])], inside, pat, out)
        out["roots"].append({"root": str(root), "status": "scanned"})
    if with_crontab:
        try:
            p = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10)
            text = p.stdout if p.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            text = None
        if text is None:
            out["roots"].append({"root": "crontab", "status": "absent"})
        else:
            _scan_text("crontab", text, pat, "readers", out)
            out["roots"].append({"root": "crontab", "status": "scanned"})
    return out


def main() -> int:
    print(json.dumps(census(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
