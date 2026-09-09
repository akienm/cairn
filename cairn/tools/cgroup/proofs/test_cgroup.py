#!/usr/bin/env python3
"""Teeth for cairn.tools.cgroup — the corpus's one reader of /proc/<pid>/cgroup.

A hollow build could not pass these: the parse is pinned in BOTH directions over
synthetic text (found and not-found), the ' (deleted)' strip is pinned against a path
that merely ends in similar bytes, the live read is checked against the kernel's own
file for this very process, and the census that makes "one reader" true is re-run here
rather than left to a proof under another component's directory-scoped seal.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.tools.cgroup.cgroup import cgroup_of, parse  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def main() -> int:
    print("THE PARSE — over text, so the verdict does not depend on where the runner lives")
    check("a unified line is the answer",
          parse("0::/user.slice/x.scope\n") == "/user.slice/x.scope")
    check("a v1-only file has no answer, and that is None rather than a raise",
          parse("1:name=systemd:/y\n2:cpu:/z\n") is None)
    check("the unified line is found among v1 lines, not just at the top",
          parse("1:cpu:/a\n0::/b\n") == "/b")
    check("an empty file is None",
          parse("") is None)
    check("the kernel's ' (deleted)' marker is not part of the identity",
          parse("0::/user.slice/dead.scope (deleted)\n") == "/user.slice/dead.scope")
    # THE STRIP MUST NOT BE A SUBSTRING HABIT. A path whose own last segment merely ends
    # in those bytes is a different fact from a cgroup the kernel marked removed.
    check("a path that merely ends in similar bytes is left whole",
          parse("0::/user.slice/x-(deleted)\n") == "/user.slice/x-(deleted)")
    check("the root cgroup survives the parse as '/'",
          parse("0::/\n") == "/")

    print("\nTHE LIVE READ — against the kernel's own file for this very process")
    ours = cgroup_of()
    raw = Path("/proc/self/cgroup").read_text()   # the proof's own eyes, not the module's
    expected = next((ln[3:].removesuffix(" (deleted)")
                     for ln in raw.splitlines() if ln.startswith("0::")), None)
    check("cgroup_of() reports what /proc/self/cgroup says", ours == expected, f"{ours!r}")
    check("and on this v2 host that is a real path, not the None branch",
          isinstance(ours, str) and ours.startswith("/"), f"{ours!r}")
    check("a pid given explicitly reads the same as 'self'",
          cgroup_of(os.getpid()) == ours)

    # A pid that cannot be there: pid_max + 1 is never allocated.
    gone = int(Path("/proc/sys/kernel/pid_max").read_text().strip()) + 1
    check("a pid that does not exist is None, not an exception", cgroup_of(gone) is None)

    print("\nTHE CENSUS — the claim 'one reader' is measured, not asserted")
    hits = subprocess.run(["grep", "-rn", "--include=*.py", r"/proc/[^\"']*cgroup", str(REPO)],
                          capture_output=True, text=True).stdout
    reads: set[str] = set()
    for line in hits.splitlines():
        if not line.strip():
            continue
        path, _, text = line.split(":", 2)
        if re.search(r"read_text\(|open\(|readlines\(", text):
            reads.add(str(Path(path).resolve().relative_to(REPO)))
    # This proof reads the file itself, deliberately, to check the module against the
    # kernel — a proof that took the module's word for it would be the hollow floor.
    me = str(Path(__file__).resolve().relative_to(REPO))
    mine = str((REPO / "cairn" / "tools" / "cgroup" / "cgroup.py").relative_to(REPO))
    check("exactly one NON-PROOF file reads /proc/<pid>/cgroup, and it is this tool",
          reads - {me} == {mine}, f"readers: {sorted(reads)}")
    check("and the census is not vacuous — it found this tool",
          mine in reads)

    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
