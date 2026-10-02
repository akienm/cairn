"""Codemother hears the commit as an event (ticket e0f318650123).

Run by her tracked ``hooks/post-commit``, which the fan-out at ``cairn/tools/post_commit`` fires
once per main-tree commit. It reads the commit it was fired for — hash, changed files, subject —
and posts it to her own ``commit`` verb through her bus, where ``CodeMotherShim._handle_commit``
hands it to ``watch.on_commit``. This replaced ``groundloop/pulse.py``, which read git HEAD on
every beat to find commits; the commit is the event, the beat is not.

REACH, POST, FLUSH — the tester's ``_announce_seals`` is the precedent (cli.py). ``reach`` wires
her delivery in this process, so ``post`` fires her handler here; ``flush`` writes the ring to
the bus store before the process dies, so an envelope her handler did not take is still in her
mailbox (``bus.undelivered``) rather than gone with the hook.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]


def read_commit(repo: Path | str | None = None) -> dict:
    """``{hash, files, message}`` for HEAD of ``repo`` — files sorted, message the subject."""
    base = str(repo or _REPO)

    def git(*a: str) -> str:
        out = subprocess.run(["git", "-C", base, *a], capture_output=True, text=True, timeout=60)
        if out.returncode != 0:
            raise RuntimeError(f"git {' '.join(a)}: {out.stderr.strip()}")
        return out.stdout

    commit = git("rev-parse", "HEAD").strip()
    files = sorted(f for f in git("diff-tree", "--no-commit-id", "--name-only", "-r", "--root",
                                  commit).splitlines() if f)
    return {"hash": commit, "files": files, "message": git("log", "-1", "--format=%s").strip()}


def announce(bus, *, commit: str, files: list[str], message: str) -> dict:
    """Post one ``commit`` envelope to codemother and flush it into the bus store."""
    env = bus.post(sender="codemother", to="codemother", channel="personal", verb="commit",
                   why=f"commit {commit[:12]} landed",
                   body={"hash": commit, "files": list(files), "message": message})
    bus.flush()
    return env


def main() -> int:
    from cairn.tools.base.address import log_path

    got = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    try:
        from cairn.tools.bus_client import reach

        commit = read_commit()
        got["hash"] = commit["hash"]
        announce(reach("codemother"), commit=commit["hash"], files=commit["files"],
                 message=commit["message"])
        got["outcome"] = "posted"
    except Exception as exc:  # noqa: BLE001 — the commit has landed; this is the telling (Law 7)
        got["outcome"] = f"failed: {type(exc).__name__}: {exc}"
        print(f"codemother post-commit: {got['outcome']}", file=sys.stderr)
    trail = log_path("codemother") / "post_commit.jsonl"
    trail.parent.mkdir(parents=True, exist_ok=True)
    with trail.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(got) + "\n")
    return 0 if got["outcome"] == "posted" else 1


if __name__ == "__main__":
    sys.exit(main())
