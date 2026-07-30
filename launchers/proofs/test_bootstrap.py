"""Proof: the preflight brings the floor up, never lies about it, and never blocks the launch.

The falsifier this proof grips (tickets/superclaude-starts-itself.json): "the floor can be
reported UP while `import cairn` from outside the repo actually fails" — and its twin, "the
preflight can prevent Claude Code from starting."

Two halves, and the second is the one a hollow build fails:
  - MECHANISM, on synthetic paths: every refusal actually refuses, every finding carries
    enough to act on, and the report is SILENT when there is nothing to say.
  - IN SITU, against this host: the real floor is up, measured the only way that counts —
    importing `cairn` from a cwd that is NOT the repo root. Green over a box where the
    bootstrap never ran would be hollow (Law 8), so a down floor is a real red here. The
    repair is one command and the finding names it.

A host-seam's seal EXPIRES (CLAUDE.md): the host drifts with nothing in git changing. That
is not a flaw in this proof, it is its job — this file IS the re-runnable `verify` half.

Deliberately dependency-light: subprocess + bash + json. Runs bare.

    python3 launchers/proofs/test_bootstrap.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BOOTSTRAP = REPO / "launchers" / "bootstrap.sh"
SUPERCLAUDE = REPO / "launchers" / "superclaude"

# A path that cannot be created, so `apply` genuinely fails rather than quietly succeeding.
# /proc is a kernel filesystem: mkdir under it is refused, which is what makes this a real
# negative fixture and not a slow one.
UNCREATABLE = "/proc/cairn-no-such-dir/venv"

_failures: list[str] = []


def _sh(script: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run bash with bootstrap.sh sourced. Returns the completed process."""
    full = f"source {BOOTSTRAP!s} || exit 99\n{script}"
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(["bash", "-c", full], capture_output=True, text=True, env=e, timeout=120)


def check(name: str, fn) -> None:
    try:
        fn()
        print(f"  PASS  {name}")
    except AssertionError as exc:
        print(f"  FAIL  {name}: {exc}", file=sys.stderr)
        _failures.append(name)


# --- the non-vacuity guard, first -------------------------------------------
# My own leak-scan lesson, paid for again on 2026-07-30: a negative test whose fixture
# does not actually route to the failing branch passes VACUOUSLY, and the tell is that
# every case reports the same cheerful message. So assert the fixture is really absent
# BEFORE any test leans on it being absent.
def test_the_negative_fixture_is_genuinely_absent() -> None:
    assert not Path(UNCREATABLE).exists(), (
        f"{UNCREATABLE} exists — every negative case below would pass vacuously"
    )
    r = _sh(f'mkdir -p "{UNCREATABLE}" 2>/dev/null; [[ -d "{UNCREATABLE}" ]] && echo MADE || echo REFUSED')
    assert "REFUSED" in r.stdout, f"the uncreatable fixture was creatable — got {r.stdout!r}"


def test_verify_refuses_an_absent_venv_and_names_the_repair() -> None:
    r = _sh('cairn_bootstrap_verify; echo "RC=$?"; printf "%s\\n" "${CAIRN_BOOTSTRAP_FINDINGS[@]}"',
            env={"CAIRN_VENV": UNCREATABLE})
    assert "RC=1" in r.stdout, f"verify passed over an absent venv — stdout={r.stdout!r}"
    assert "VENV ABSENT" in r.stdout, f"no finding named the absent venv — {r.stdout!r}"
    # The complete-diagnostic contract: the FIRST report carries what a fixer needs, so
    # nobody has to re-run to gather more. Structurally: the path, and a repair.
    assert UNCREATABLE in r.stdout, "the finding does not name the path it measured"
    assert "Repair:" in r.stdout, "the finding carries no repair — it forces a second run"


def test_apply_cannot_fake_a_floor_it_did_not_lay() -> None:
    r = _sh('cairn_bootstrap_apply; echo "RC=$?"; printf "%s\\n" "${CAIRN_BOOTSTRAP_FINDINGS[@]}"',
            env={"CAIRN_VENV": UNCREATABLE})
    assert "RC=1" in r.stdout, f"apply reported success over an uncreatable venv — {r.stdout!r}"
    assert "VENV CREATE FAILED" in r.stdout, f"apply did not report the create failure — {r.stdout!r}"
    # The stamp is written LAST and only on success; a stamp here would mark a floor that
    # was never laid, and the fast path would then skip the repair forever.
    assert not Path(UNCREATABLE, ".cairn-stamp").exists(), "a stamp was written for a floor that does not exist"


def test_a_finding_never_asserts_a_cause_it_did_not_measure() -> None:
    """Regression, measured 2026-07-30: the create-failure hint read 'usually the missing
    ensurepip package' while the actual error was ENOENT on the parent directory. A
    diagnostic surface that confidently names the wrong cause is worse than a quiet one."""
    r = _sh('cairn_bootstrap_apply >/dev/null 2>&1; printf "%s\\n" "${CAIRN_BOOTSTRAP_FINDINGS[@]}"',
            env={"CAIRN_VENV": UNCREATABLE})
    assert "usually the" not in r.stdout, "a finding asserts a probable cause instead of naming candidates"
    assert "candidates if it is unclear" in r.stdout, "the hint does not label itself as a guess"
    assert "Output:" in r.stdout, "the finding does not carry the measured output it is reasoning from"


def test_the_report_is_silent_when_the_floor_is_up() -> None:
    """The invisibility contract: the tool speaks only when there is something to fix."""
    r = _sh('CAIRN_BOOTSTRAP_FINDINGS=(); cairn_bootstrap_report; echo "RC=$?"')
    body = r.stdout.replace("RC=0", "").strip()
    assert "RC=0" in r.stdout, f"report returned non-zero over an empty finding list — {r.stdout!r}"
    assert body == "", f"the report spoke with nothing to report — {body!r}"


def test_the_report_is_loud_when_it_is_not() -> None:
    r = _sh('CAIRN_BOOTSTRAP_FINDINGS=("SYNTHETIC FINDING for the proof"); cairn_bootstrap_report; echo "RC=$?"')
    assert "RC=1" in r.stdout, "the report returned success while carrying a finding"
    assert "SYNTHETIC FINDING" in r.stdout, "the finding did not reach the report body"
    assert "CAIRN PREFLIGHT" in r.stdout, "the report has no header naming where it came from"


def test_the_report_leaves_a_durable_record() -> None:
    r = _sh('CAIRN_BOOTSTRAP_FINDINGS=("SYNTHETIC FINDING for the proof"); cairn_bootstrap_report >/dev/null')
    assert r.returncode in (0, 1), f"report crashed: {r.stderr!r}"
    rec = Path.home() / ".cairn" / "logs" / "preflight.json"
    assert rec.is_file(), f"no durable record at {rec}"
    d = json.loads(rec.read_text())
    assert d["floor_up"] is False, "the record claims the floor is up while carrying findings"
    assert any("SYNTHETIC" in f for f in d["findings"]), "the record dropped the finding"


def test_bootstrap_sets_no_errexit_because_it_is_sourced() -> None:
    """Physics, not policy (Law 4). `set -e` in a SOURCED file leaks into the caller's
    shell, so one failed probe would kill superclaude's launch — the precise inverse of
    the rescue ethos. This is the regression guard for that."""
    text = BOOTSTRAP.read_text()
    for bad in ("\nset -e", "\nset -eu", "\nset -euo"):
        assert bad not in text, f"bootstrap.sh contains a top-level '{bad.strip()}' — it is sourced by superclaude"


# --- THE PRIME DIRECTIVE ----------------------------------------------------
def test_a_broken_preflight_still_reaches_claude() -> None:
    """The one thing the launcher may never do is fail to launch. A preflight that cannot
    repair must still hand off, carrying its report — 'always reach Claude Code so it can
    help rebuild a broken box' (launchers/intention+why.json)."""
    e = dict(os.environ)
    e["CAIRN_VENV"] = UNCREATABLE
    r = subprocess.run([str(SUPERCLAUDE), "--dry-run"], capture_output=True, text=True, env=e, timeout=180)
    assert r.returncode == 0, f"superclaude exited {r.returncode} with a broken preflight — {r.stderr!r}"
    assert "exec claude" in r.stdout, f"the launch was aborted by the preflight — {r.stdout!r}"
    # ...and it does not go silently: the residue rides into the session.
    assert "--append-system-prompt" in r.stdout, "a broken floor produced no report for Claude"
    assert "VENV ABSENT" in r.stdout, "the report reached the launch without its findings"


def test_a_working_preflight_adds_nothing_to_the_launch() -> None:
    """Invisible when it works — the launch line is byte-identical to the pre-preflight one."""
    r = subprocess.run([str(SUPERCLAUDE), "--dry-run"], capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, f"superclaude exited {r.returncode} — {r.stderr!r}"
    assert "exec claude" in r.stdout, "no launch line"
    if "--append-system-prompt" in r.stdout:
        raise AssertionError(
            "the live floor is DOWN, so the launch carried a report. That is the preflight "
            f"working, but it means this host needs repair. Report:\n{r.stdout}"
        )


# --- IN SITU: the live floor ------------------------------------------------
def test_the_live_floor_is_up() -> None:
    r = _sh('cairn_bootstrap_verify; echo "RC=$?"; printf "%s\\n" ${CAIRN_BOOTSTRAP_FINDINGS+"${CAIRN_BOOTSTRAP_FINDINGS[@]}"}')
    assert "RC=0" in r.stdout, (
        "the floor on this host is DOWN. This is the host-seam's seal expiring, not a code "
        f"defect. Repair: run `superclaude` once, or source launchers/bootstrap.sh and call "
        f"cairn_bootstrap_apply.\nFindings:\n{r.stdout}"
    )


def test_cairn_imports_from_outside_the_repo() -> None:
    """The defect that started all of this, asserted directly. Importing from the repo root
    proves nothing — that is the cwd accident we are retiring. So import from elsewhere."""
    r = _sh('cd / && "$(cairn_python)" -c "import cairn; print(cairn.__file__)"')
    assert r.returncode == 0, f"`import cairn` from / failed: {r.stderr.strip()!r}"
    got = r.stdout.strip().splitlines()[-1]
    assert got.startswith(str(REPO)), f"cairn resolved to {got!r}, not to this checkout ({REPO})"


def test_the_declared_dependency_is_actually_installed() -> None:
    """pyproject declares psycopg2-binary because db_domain imports it at module scope. An
    undeclared-but-present import was the original defect; a declared-but-absent one is the
    same lie facing the other way."""
    r = _sh('cd / && "$(cairn_python)" -c "import psycopg2; print(psycopg2.__file__)"')
    assert r.returncode == 0, f"psycopg2 missing from the floor: {r.stderr.strip()!r}"
    got = r.stdout.strip().splitlines()[-1]
    r2 = _sh('cairn_venv_dir')
    venv = r2.stdout.strip()
    assert got.startswith(venv), (
        f"psycopg2 resolved to {got!r}, outside the venv ({venv}) — the floor is leaking from "
        "system site-packages, which makes its contents a function of what this host happens to have"
    )


def test_every_third_party_import_is_declared() -> None:
    """The GENERALISATION of the defect that started this, made physics (Law 4).

    psycopg2 was imported at module scope and declared nowhere; it worked only because this
    box happened to have it. That is not a psycopg2 bug, it is a class of bug — the next
    undeclared import will be added by someone who never reads this file. So the rule stops
    being prose: scan what cairn/ actually imports, subtract the standard library and our own
    package, and require the remainder to appear in pyproject's dependencies.

    Answerable RIGHT NOW, deterministically, from files in git — which is exactly why it is a
    proof and not a probe. A watch is for a question that needs time to answer; using one here
    would be waiting to discover something already knowable (Law 3 cuts both ways)."""
    import ast

    declared = set()
    for line in (REPO / "pyproject.toml").read_text().splitlines():
        s = line.strip().strip(",").strip('"').strip("'")
        if s and not s.startswith("#"):
            # crude but sufficient: 'psycopg2-binary>=2.9' -> 'psycopg2'
            head = s.split(">=")[0].split("==")[0].split("[")[0].strip()
            if head and head.replace("-", "").replace("_", "").isalnum():
                declared.add(head.lower().replace("-binary", "").replace("-", "_"))

    # Names that resolve to something IN this repo are not third-party, however they are
    # spelled. Proof files import their siblings by bare name after a sys.path tweak
    # (`import test_composition`), which an import-name-only scan reads as a missing
    # dependency — measured 2026-07-30, the first run of this very case. Resolving against
    # the tree is the general fix; excluding proofs/ would have hidden it rather than
    # understood it, and would have stopped scanning code that has real imports.
    local = {p.stem for p in REPO.rglob("*.py") if "__pycache__" not in p.parts}
    local |= {d.name for d in REPO.rglob("*") if d.is_dir() and (d / "__init__.py").exists()}

    undeclared: dict[str, str] = {}
    for py in (REPO / "cairn").rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        try:
            tree = ast.parse(py.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mods = [node.module.split(".")[0]]
            for m in mods:
                if m == "cairn" or m in sys.stdlib_module_names or m in declared or m in local:
                    continue
                undeclared.setdefault(m, str(py.relative_to(REPO)))

    assert not undeclared, (
        "third-party imports that pyproject does not declare — they work only if this host "
        "happens to have them, which is the defect this ticket was opened for: "
        + "; ".join(f"{m} (first seen {p})" for m, p in sorted(undeclared.items()))
    )


def _main() -> int:
    print(f"proof: the preflight floor — repo={REPO}")
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            check(name, fn)
    if _failures:
        print(f"\n{len(_failures)} FAILED: {', '.join(_failures)}", file=sys.stderr)
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
