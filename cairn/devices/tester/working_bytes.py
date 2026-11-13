"""Working bytes that git calls unchanged but are not what a checkout writes today (ticket 8cc2a5752b6a).

MEASURED 2026-11-13. The Windows seal of cairn/tools/base/proofs/test_flock_stands_for_fcntl.py
(52890c2f8, fp 133032682e11) was the committed closure with cairn/tools/base/__init__.py alone in
CRLF, while Linux hashed 8318d78f2eda. The file last changed before the *.py eol=lf pin
(88e30cde9bd4); git rewrites a working file under a new attribute only when it writes the file
again, so the Windows working copy kept the CRLF it was checked out with. ``git status`` reads such
a tree clean, because git cleans before it compares. The fingerprint hashes raw bytes
(validation_store.source_fingerprint, deliberately not git), so that box's seals measured bytes no
commit carries, and a Linux reseal of the same commit read them as moved.

So the seal door asks one more question of a closure: is any tracked file one that git calls
unchanged (its cleaned hash is the index blob) whose raw bytes are still not what checking out that
blob for its path would write today? Such a seal would be the fingerprint of bytes nobody committed,
and it is refused, naming the file. A genuine uncommitted edit is NOT this: its cleaned hash moved,
and it seals as it always has. A path whose attributes intend CRLF in the working tree (``*.cmd``)
smudges to CRLF and is never named.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

__all__ = ["UnnormalizedClosure", "refusal_text", "unnormalized"]

_REGULAR = ("100644", "100755")


class UnnormalizedClosure(Exception):
    """A seal refused because its closure holds working bytes no checkout of the index writes."""

    def __init__(self, files: list[str]):
        self.files = list(files)
        super().__init__(refusal_text(self.files))


def refusal_text(files: list[str]) -> str:
    named = "\n".join(f"  {f}" for f in files)
    return (f"{len(files)} closure file(s) read unchanged to git but their working bytes are not "
            f"what a checkout of the index writes today (a checkout taken before an eol "
            f"attribute landed):\n{named}\nA seal over them would fingerprint bytes no commit "
            f"carries, so it does not reproduce on another box. Renormalise this working tree "
            f"once, on a clean tree: git rm --cached -r -q . && git reset --hard "
            f"(ticket 8cc2a5752b6a).")


def unnormalized(files, base) -> list[str]:
    """The repo-relative ``files`` under ``base`` whose raw working bytes are not what checking
    out their index blob writes today, while git calls them unchanged; sorted.

    Untracked files, symlinks and gitlinks have no regular blob to compare and are skipped
    (``dirty_against_index`` names the untracked). A repo git cannot read names nothing: this
    predicate refuses only on a positive measurement."""
    base = Path(base)
    wanted = sorted({str(f).replace("\\", "/") for f in files})
    if not wanted:
        return []
    listed = subprocess.run(["git", "-C", str(base), "ls-files", "-s", "-z", "--", *wanted],
                            capture_output=True)
    if listed.returncode != 0:
        return []
    index: dict[str, str] = {}
    for entry in listed.stdout.decode("utf-8", "surrogateescape").split("\0"):
        if not entry:
            continue
        meta, _, path = entry.partition("\t")
        mode, sha, stage = meta.split()
        if mode in _REGULAR and stage == "0" and (base / path).is_file():
            index[path] = sha
    paths = [p for p in wanted if p in index]
    if not paths:
        return []
    raw = subprocess.run(["git", "-C", str(base), "hash-object", "--no-filters", "--stdin-paths"],
                         input="\n".join(paths) + "\n", capture_output=True, text=True)
    if raw.returncode != 0:
        return []
    # Candidates: raw bytes are not the index blob. On a box whose tree is LF these are only the
    # genuinely edited files, so the per-file questions below stay few.
    candidates = [p for p, h in zip(paths, raw.stdout.split()) if h != index[p]]
    flagged = []
    for p in candidates:
        cleaned = subprocess.run(["git", "-C", str(base), "hash-object", "--", p],
                                 capture_output=True, text=True)
        if cleaned.returncode != 0 or cleaned.stdout.strip() != index[p]:
            continue                       # a genuine edit: git sees a change; it seals as ever
        smudged = subprocess.run(["git", "-C", str(base), "cat-file", "--filters",
                                  f"--path={p}", index[p]], capture_output=True)
        if smudged.returncode != 0:
            continue
        if smudged.stdout != (base / p).read_bytes():
            flagged.append(p)
    return sorted(flagged)
