"""The installer machine: a projection over host-seam intentions.

Walks CairnCommons/intentions-not-beside-code/ for node_class: host-seam
intentions, reads their apply/verify, runs verify-first (idempotent),
offers each applicable one through ask_user, and reports results.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_INTENTIONS_DIR = Path(os.path.expanduser(
    "~/dev/src/CairnCommons/intentions-not-beside-code"
))

ASK_USER = Path(__file__).parent / "ask_user.sh"


def gather_host_seams(intentions_dir: Path) -> list[dict]:
    """Discover host-seam intentions from the corpus."""
    seams = []
    for f in sorted(intentions_dir.iterdir()):
        if f.suffix != ".json" or f.name.startswith("_"):
            continue
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        if data.get("node_class") == "host-seam":
            seams.append(data)
    return seams


def run_verify(seam: dict) -> tuple[bool, str]:
    """Run a seam's verify.command.  Returns (passed, output)."""
    verify = seam.get("verify", {})
    cmd = verify.get("command")
    if not cmd:
        return False, "no verify command declared"
    try:
        result = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True, text=True, timeout=30,
        )
        output = result.stdout.strip() or result.stderr.strip()
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "verify timed out (30s)"
    except OSError as exc:
        return False, str(exc)


def present_apply(seam: dict) -> list[tuple[str, str]]:
    """Extract numbered apply steps, skipping note/optional."""
    apply_block = seam.get("apply", {})
    steps = []
    for key in sorted(apply_block):
        if key in ("note", "optional"):
            continue
        steps.append((key, apply_block[key]))
    return steps


def _ask_interactive(question: str) -> bool:
    if not sys.stdin.isatty():
        return False
    print(f"\n{question} [Y/N] ", end="", flush=True)
    answer = input().strip().upper()
    return answer in ("Y", "YES")


def install(
    *,
    intentions_dir: Path | None = None,
    dry_run: bool = False,
    ask_fn: object = None,
) -> list[dict]:
    """Run the installer projection.

    Returns a list of result dicts, each with: id, status, detail.
    Statuses: already_applied, offered, skipped, failed, applied.
    """
    d = intentions_dir or DEFAULT_INTENTIONS_DIR
    seams = gather_host_seams(d)
    results: list[dict] = []

    for seam in seams:
        sid = seam.get("id", "<unknown>")

        passed, output = run_verify(seam)
        if passed:
            results.append({
                "id": sid,
                "status": "already_applied",
                "detail": f"verify passed: {output}",
            })
            continue

        if dry_run:
            results.append({
                "id": sid,
                "status": "offered",
                "detail": seam.get("intention", ""),
            })
            continue

        question = f"Apply host-seam '{sid}'?"
        if callable(ask_fn):
            answer = ask_fn(question)
        else:
            answer = _ask_interactive(question)

        if not answer:
            results.append({
                "id": sid,
                "status": "skipped",
                "detail": "operator declined",
            })
            continue

        steps = present_apply(seam)
        if steps:
            print(f"\n--- apply steps for {sid} ---")
            for key, text in steps:
                print(f"  [{key}] {text}")
            print("--- end ---\n")

        passed, output = run_verify(seam)
        if not passed:
            results.append({
                "id": sid,
                "status": "failed",
                "detail": f"RED: verify failed after apply: {output}",
            })
            continue

        results.append({
            "id": sid,
            "status": "applied",
            "detail": f"applied and verified: {output}",
        })

    return results


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(
        prog="cairn install",
        description="Apply host-seam intentions to this machine.",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="list applicable seams without applying",
    )
    p.add_argument(
        "--intentions-dir", type=Path,
        help="override the intentions directory",
    )
    args = p.parse_args(argv)

    results = install(
        intentions_dir=args.intentions_dir,
        dry_run=args.dry_run,
    )

    if not results:
        print("no host-seam intentions found")
        return 0

    any_failed = False
    for r in results:
        tag = r["status"].upper()
        if r["status"] == "failed":
            any_failed = True
            tag = "RED"
        print(f"  [{tag}] {r['id']}: {r['detail']}")

    if any_failed:
        print("\nRED: one or more seams failed verification after apply")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
