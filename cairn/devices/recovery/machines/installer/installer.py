"""The installer machine: a projection over host-seam intentions.

Walks CairnCommons/intentions-not-beside-code/ for node_class: host-seam
intentions, reads their apply/verify, runs verify-first (idempotent),
offers each applicable one through ask_user, and reports results.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

from cairn.tools.base.address import ROOTS

DEFAULT_INTENTIONS_DIR = ROOTS["commons"] / "intentions-not-beside-code"

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
        return {"id": "cairn-home", "status": "already_applied", "detail": f"{HOME_VAR}={have}",
                "home": have}
    if dry_run:
        return {"id": "cairn-home", "status": "offered",
                "detail": "ask: is this a cairn home, or which home does it attach to?"}
    ask = ask_text_fn if callable(ask_text_fn) else _ask_text
    me = hostname or platform.node().split(".")[0]
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
                "detail": f"{HOME_VAR}={home} set for this user (setx); new shells see it",
                "home": home}
    with rc.open("a") as f:
        f.write(f"\n{line_start}{home}   # the cairn home box (cairn install, outline 7.3.7.4)\n")
    return {"id": "cairn-home", "status": "applied", "detail": f"{HOME_VAR}={home} written to {rc}",
            "home": home}


def ask_box_identity(
    *,
    home: str | None = None,
    dry_run: bool = False,
    ask_text_fn: object = None,
    hostname: str | None = None,
    tls_dir: Path | None = None,
    port: int | None = None,
    first_contact_fn: object = None,
) -> dict:
    """Ticket 5183005fa134: the box's own TLS identity, and the fingerprint exchange — the
    one setup step pinned TLS adds, so it rides cairn install beside the cairn-home question.

    Every box: make ``<bus home>/tls/box.key`` + ``box.crt`` once (openssl), named by its
    hostname. An ATTACHING box (``home`` names another box): first contact with the home's
    bus — pin its certificate, leave this box's as an ask there, and print both fingerprints
    for the two operators to compare. The HOME: show each held ask and ask accept or decline.
    """
    from cairn.tools.bus_client import remote, tls

    d = Path(tls_dir) if tls_dir is not None else remote.tls_dir()
    me = (hostname or platform.node()).split(".")[0]
    home = (home if home is not None else os.environ.get(HOME_VAR, "")).strip()
    attaching = bool(home) and home.split(".")[0].lower() != me.lower()
    if dry_run:
        return {"id": "box-identity", "status": "offered" if not tls.has_identity(d) else
                "already_applied", "detail": f"the box identity at {d}"
                + (f"; first contact with {home}" if attaching else "; the home's held asks")}
    try:
        made = not tls.has_identity(d)
        fp = tls.make_identity(d, me)
    except (OSError, RuntimeError, ValueError) as exc:
        return {"id": "box-identity", "status": "failed", "detail": f"RED: {exc}"}
    said = [f"{'made' if made else 'have'} {me} {fp}"]
    if attaching:
        host = home.split(".")[0]
        if host in tls.known(d):
            return {"id": "box-identity", "status": "already_applied",
                    "detail": f"{said[0]}; {host} pinned {tls.known(d)[host]}"}
        contact = first_contact_fn if callable(first_contact_fn) else tls.first_contact
        try:
            got = contact(d, home, port or tls.lan_port())
        except (OSError, ValueError) as exc:
            return {"id": "box-identity", "status": "failed",
                    "detail": f"RED: {said[0]}; first contact with {home} failed: "
                              f"{type(exc).__name__}: {exc}"}
        print(f"\n  pinned {got['home']}: {got['home_fingerprint']}\n"
              f"  this box {me}:  {got['mine']}\n"
              f"  compare both on {got['home']} (cairn install there accepts this box)")
        return {"id": "box-identity", "status": "applied",
                "detail": f"{said[0]}; pinned {got['home']} {got['home_fingerprint']}; "
                          f"ask held there: {got['reply']}"}
    pending = tls.asks(d)
    if not pending:
        return {"id": "box-identity", "status": "applied" if made else "already_applied",
                "detail": f"{said[0]}; {len(tls.known(d))} pinned, no asks"}
    ask = ask_text_fn if callable(ask_text_fn) else _ask_text
    for name, afp in pending.items():
        yn = ask(f"Box {name} asks to join, fingerprint {afp}. Accept? [y/n]")
        if yn is None:
            said.append(f"{name} left waiting (no terminal)")
        elif yn.strip().lower() in ("y", "yes"):
            tls.accept(d, name)
            said.append(f"accepted {name}")
        elif yn.strip().lower() in ("n", "no"):
            tls.decline(d, name)
            said.append(f"declined {name}")
        else:
            said.append(f"{name} left waiting (expected y or n, got {yn!r})")
    return {"id": "box-identity", "status": "applied", "detail": "; ".join(said)}


MERGE_DRIVER = "cairn-journal"
_REPO = Path(__file__).resolve().parents[5]


def _driver_fault(root: Path) -> str | None:
    """Why this repo's journal merge driver is not good, or None when it is.

    Good = the string `cairn artifact install-merge-driver` writes, still true of this box:
    PYTHONPATH names this checkout, the interpreter exists, and it runs the merge-journal
    verb. A rebuilt venv or a moved checkout leaves a string that names what is gone."""
    got = subprocess.run(["git", "-C", str(root), "config", "--get", f"merge.{MERGE_DRIVER}.driver"],
                         capture_output=True, text=True)
    drv = got.stdout.strip()
    if not drv:
        return "not configured"
    import shlex
    try:
        words = shlex.split(drv)
    except ValueError as exc:
        return f"unreadable ({exc}): {drv}"
    if len(words) < 2 or not words[0].startswith("PYTHONPATH="):
        return f"not the artifact tool's driver: {drv}"
    if Path(words[0][len("PYTHONPATH="):]).resolve() != _REPO:
        return f"points at another checkout ({words[0]}), not {_REPO}"
    if not Path(words[1]).exists():
        return f"its interpreter {words[1]} does not exist (venv rebuilt or moved)"
    if not {"-m", "cairn.tools.artifact", "merge-journal"} <= set(words):
        return f"does not run cairn.tools.artifact merge-journal: {drv}"
    return None


def ensure_journal_merge_driver(*, roots: dict | None = None, dry_run: bool = False) -> dict:
    """Ticket 7cfbc64b2a67: every repo root on the box merges .artifact-journal.jsonl with the
    cairn-journal driver (ticket b7d2e05a1c93), so two sessions' journals meet re-linked.

    The driver lives in .git/config, which git does not carry, so it is a host change and
    goes through here (outline 6.3.5). The tracked .gitattributes line names it on every
    clone, and without the config git silently uses its text merge, which forks the chain.
    It is laid through the artifact tool's own verb (its public interface, RULE 1). No
    question is asked: a local git config is benign, as box-identity makes keys unasked."""
    if roots is None:
        from cairn.tools.artifact.artifact import roots as artifact_roots
        roots = artifact_roots()
    sid = "journal-merge-driver"
    skipped, bad, good = [], {}, []
    for name, d in roots.items():
        d = Path(d)
        if not (d / ".git").exists():
            skipped.append(f"{name} skipped ({d} is not a git repository)")
            continue
        fault = _driver_fault(d)
        if fault:
            bad[name] = (d, fault)
        else:
            good.append(name)
    tail = "".join(f"; {s}" for s in skipped)
    if not bad:
        return {"id": sid, "status": "already_applied",
                "detail": f"driver good in {', '.join(good) or 'no repo'}{tail}"}
    if dry_run:
        return {"id": sid, "status": "offered",
                "detail": "; ".join(f"{n}: {f}" for n, (_, f) in bad.items()) + tail}
    env = dict(os.environ, PYTHONPATH=str(_REPO))
    for name, (d, fault) in bad.items():
        r = subprocess.run([sys.executable, "-m", "cairn.tools.artifact", "install-merge-driver", str(d)],
                           capture_output=True, text=True, cwd=str(_REPO), env=env)
        after = _driver_fault(d)
        if r.returncode or after:
            return {"id": sid, "status": "failed",
                    "detail": f"RED: {name} ({d}) was {fault}; install-merge-driver exited "
                              f"{r.returncode}: {(r.stderr or r.stdout).strip()}; now {after or 'good'}"}
    return {"id": sid, "status": "applied",
            "detail": "laid in " + ", ".join(f"{n} (was {f})" for n, (_, f) in bad.items())
                      + (f"; already good in {', '.join(good)}" if good else "") + tail}


def _is_link(p: Path) -> bool:
    """A symlink, or a Windows directory junction (os.path.islink reads False for one)."""
    isj = getattr(os.path, "isjunction", None)
    return os.path.islink(p) or bool(isj and isj(p))


def _make_link(target: Path, at: Path) -> None:
    if os.name == "nt":
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(at), str(target)],
                           capture_output=True, text=True)
        if r.returncode:
            raise OSError(f"mklink /J exited {r.returncode}: {(r.stderr or r.stdout).strip()}")
    else:
        os.symlink(target, at, target_is_directory=True)


def _drop_link(at: Path) -> None:
    if os.path.islink(at):
        os.unlink(at)
    else:
        os.rmdir(at)  # a junction: rmdir removes the link, never the target's contents


def ensure_skill_links(*, skills_src: Path | None = None, skills_root: Path | None = None,
                       link=None, dry_run: bool = False) -> dict:
    """Ticket 53e7979f76e7: ~/.claude/skills/<s> links to <this checkout>/skills/<s> for every
    Cairn skill (a skills/<s>/ holding SKILL.md), so a fresh box can fire /idea, /intent,
    /sorted and /sail. Measured 2026-11-12: akienasus had none of 15, akiendell none of 16.

    The skills root is $CLAUDE_CONFIG_DIR/skills if set, else ~/.claude/skills. A correct link
    is left alone; a link elsewhere is re-pointed; a dangling link into a skills/ dir is
    removed; a same-named real directory is RED and never touched (it is someone's work).
    A symlink on POSIX, a directory junction on Windows (no admin needed). `link(target, at)`
    is injectable so the proof drives it over scratch dirs."""
    sid = "skill-links"
    src = Path(skills_src) if skills_src else _REPO / "skills"
    if skills_root is None:
        base = os.environ.get("CLAUDE_CONFIG_DIR")
        skills_root = (Path(base) if base else Path.home() / ".claude") / "skills"
    root = Path(skills_root)
    link = link or _make_link
    names = sorted(d.name for d in src.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
    make, repoint, red, good, dangling = [], [], [], [], []
    for n in names:
        at, target = root / n, (src / n).resolve()
        if _is_link(at):
            (good if at.resolve() == target else repoint).append(n)
        elif at.exists():
            red.append(n)
        else:
            make.append(n)
    if root.is_dir():
        for at in sorted(root.iterdir()):
            if at.name in names or not _is_link(at) or at.exists():
                continue
            if Path(os.readlink(at)).parent.name == "skills":
                dangling.append(at.name)
    acts = [(done, would, ns) for done, would, ns in (
        ("made", "would make", make), ("re-pointed", "would re-point", repoint),
        ("removed dangling", "would remove dangling", dangling)) if ns]
    reds = [f"RED: {root / n} is a real directory, not a link; left untouched" for n in red]
    if not acts:
        if reds:
            return {"id": sid, "status": "failed", "detail": "; ".join(reds)}
        return {"id": sid, "status": "already_applied",
                "detail": f"{len(good)} skill link(s) good in {root}"}
    if dry_run:
        return {"id": sid, "status": "failed" if reds else "offered",
                "detail": "; ".join(reds + [f"{w} {', '.join(ns)}" for _, w, ns in acts])}
    root.mkdir(parents=True, exist_ok=True)
    for n in dangling + repoint:
        _drop_link(root / n)
    for n in repoint + make:
        link((src / n).resolve(), root / n)
    wrong = [n for n in repoint + make if (root / n).resolve() != (src / n).resolve()]
    if wrong:
        reds.append(f"RED: {', '.join(wrong)} do not resolve to {src} after linking")
    return {"id": sid, "status": "failed" if reds else "applied",
            "detail": "; ".join(reds + [f"{d} {', '.join(ns)}" for d, _, ns in acts]) + f" (in {root})"}


def _venv_exe(venv: Path, name: str) -> Path:
    """The venv's own `name` on this OS: Scripts/<name>.exe on Windows, bin/<name> elsewhere."""
    if (venv / "Scripts").is_dir():
        return venv / "Scripts" / f"{name}.exe"
    return venv / "bin" / name


def _dev_extra_modules(repo: Path) -> list[str]:
    """Import names of pyproject's [project.optional-dependencies].dev, specifiers stripped."""
    import re
    import tomllib
    doc = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))
    reqs = doc.get("project", {}).get("optional-dependencies", {}).get("dev", [])
    names = [m.group(0).replace("-", "_") for r in reqs if (m := re.match(r"[A-Za-z0-9_.-]+", r.strip()))]
    return names


def ensure_dev_extra(*, dry_run: bool = False, venv: Path | None = None, repo: Path | None = None,
                     run=subprocess.run) -> dict:
    """Ticket b3ecebdf9695: every box's ~/.cairn/venv carries pyproject's dev extra.

    A venv that cannot import pytest cannot run `cairn test`, so it proves nothing (measured
    2026-11-12 on akienasus). Each dev-extra name is asked of the venv's own python; a missing one
    is offered on a dry run, and otherwise the editable checkout is installed with [dev] through
    the venv's own pip and measured again. `run` is the one seam to the OS, so a proof can hand
    it a recording stub."""
    venv = Path(venv) if venv else ROOTS["instance"] / "venv"
    repo = Path(repo) if repo else _REPO
    sid = "dev_extra"
    try:
        wanted = _dev_extra_modules(repo)
    except (OSError, ValueError) as exc:
        return {"id": sid, "status": "failed", "detail": f"RED: cannot read the dev extra from {repo / 'pyproject.toml'}: {exc}"}
    py = _venv_exe(venv, "python")

    def missing() -> list[str]:
        return [m for m in wanted if run([str(py), "-c", f"import {m}"], capture_output=True, text=True).returncode]

    lacking = missing()
    if not lacking:
        return {"id": sid, "status": "already_applied", "detail": f"{venv} imports {', '.join(wanted)}"}
    if dry_run:
        return {"id": sid, "status": "offered", "detail": f"{venv} cannot import: {', '.join(lacking)}"}
    pip = _venv_exe(venv, "pip")
    r = run([str(pip), "install", "--editable", f"{repo}[dev]"], capture_output=True, text=True)
    after = missing()
    if r.returncode or after:
        return {"id": sid, "status": "failed",
                "detail": f"RED: {venv} could not import {', '.join(lacking)}; pip install --editable "
                          f"'{repo}[dev]' exited {r.returncode}: {(r.stderr or r.stdout or '').strip()[-300:]}; "
                          f"still missing: {', '.join(after) or 'none'}"}
    return {"id": sid, "status": "applied", "detail": f"installed {repo}[dev]; was missing {', '.join(lacking)}"}


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
    if not d.is_dir():
        # Law 7: an absent commons is a named result, not a traceback.
        return [{"id": "intentions-dir", "status": "failed",
                 "detail": f"RED: the intentions directory {d} does not exist — "
                           "clone CairnCommons beside the cairn repo, then re-run"}]
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

    home = ask_cairn_home(dry_run=args.dry_run)
    results = [home, ask_box_identity(home=home.get("home"), dry_run=args.dry_run),
               ensure_journal_merge_driver(dry_run=args.dry_run),
               ensure_skill_links(dry_run=args.dry_run),
               ensure_dev_extra(dry_run=args.dry_run)] + install(
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
