"""The installer machine: a projection over host-seam intentions.

Walks CairnCommons/intentions-not-beside-code/ for node_class: host-seam
intentions, reads their apply/verify, runs verify-first (idempotent),
offers each applicable one through ask_user, and reports results.
"""

from __future__ import annotations

import json
import os
import socket
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


HOME_VAR = "CAIRN_HOME_HOST"
SHELL_RC = Path(os.path.expanduser("~/.bashrc"))


def _ask_text(question: str) -> str | None:
    if not sys.stdin.isatty():
        return None
    print(f"\n{question} ", end="", flush=True)
    return input().strip()


def ask_cairn_home(
    *,
    rc: Path | None = None,
    dry_run: bool = False,
    ask_text_fn: object = None,
    hostname: str | None = None,
) -> dict:
    """Outline 7.3.7.4: is this box a cairn home, or which home does it attach to?

    The answer is CAIRN_HOME_HOST, beside CAIRN_ROOT and CAIRN_RUNTIME in the shell rc
    (on Windows a user environment variable, set with setx, so every shell sees it):
    the home box's name, the same value on every box of the install (the home writes
    its own hostname). superclaude reads it to start the web server on the home only.
    """
    windows = os.name == "nt" and rc is None
    rc = rc or SHELL_RC
    line_start = f"export {HOME_VAR}="
    have = os.environ.get(HOME_VAR, "")
    if not have and windows:   # a user env var: every shell sees it (PowerShell, cmd, Git Bash)
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                have = winreg.QueryValueEx(k, HOME_VAR)[0]
        except OSError:
            pass
    if not have and not windows and rc.exists():
        for ln in rc.read_text(errors="replace").splitlines():
            if ln.strip().startswith(line_start):
                have = ln.strip()[len(line_start):].strip("'\"")
    if have:
        return {"id": "cairn-home", "status": "already_applied", "detail": f"{HOME_VAR}={have}"}
    if dry_run:
        return {"id": "cairn-home", "status": "offered",
                "detail": "ask: is this a cairn home, or which home does it attach to?"}
    ask = ask_text_fn if callable(ask_text_fn) else _ask_text
    me = hostname or socket.gethostname().split(".")[0]
    yn = ask(f"Is this box ({me}) a cairn home? [y/n]")
    if yn is None:
        return {"id": "cairn-home", "status": "skipped", "detail": "no terminal to ask on"}
    if yn.strip().lower() in ("y", "yes"):
        home = me
    elif yn.strip().lower() in ("n", "no"):
        home = (ask("Then what's the hostname or IP of the cairn home this box should attach to?")
                or "").strip()
        if not home:
            return {"id": "cairn-home", "status": "skipped", "detail": "no home named"}
    else:
        return {"id": "cairn-home", "status": "skipped", "detail": f"expected y or n, got {yn!r}"}
    if windows:
        r = subprocess.run(["setx", HOME_VAR, home], capture_output=True, text=True)
        if r.returncode:
            return {"id": "cairn-home", "status": "failed",
                    "detail": f"RED: setx {HOME_VAR} failed: {r.stderr.strip() or r.stdout.strip()}"}
        return {"id": "cairn-home", "status": "applied",
                "detail": f"{HOME_VAR}={home} set for this user (setx); new shells see it"}
    with rc.open("a") as f:
        f.write(f"\n{line_start}{home}   # the cairn home box (cairn install, outline 7.3.7.4)\n")
    return {"id": "cairn-home", "status": "applied", "detail": f"{HOME_VAR}={home} written to {rc}"}


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

    results = [ask_cairn_home(dry_run=args.dry_run)] + install(
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
