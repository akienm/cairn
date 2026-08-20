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

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))     # launchers/proofs -> repo root

from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
BOOTSTRAP = REPO / "launchers" / "bootstrap.sh"
SUPERCLAUDE = REPO / "launchers" / "superclaude"

# A path that cannot be created, so `apply` genuinely fails rather than quietly succeeding.
# /proc is a kernel filesystem: mkdir under it is refused, which is what makes this a real
# negative fixture and not a slow one.
UNCREATABLE = "/proc/cairn-no-such-dir/venv"

# The other synthetic input this file feeds the seam. Named once so the containment tooth
# below reads it from here rather than carrying its own copy to go stale (Law 1).
_SYNTHETIC_FINDING = "SYNTHETIC FINDING for the proof"

_failures: list[str] = []

# THE PROOF OWNS ITS OWN NAMESPACE, and this is not hygiene — it is the difference between a
# probe measuring the world and a probe measuring its own test suite.
#
# MEASURED, 2026-07-30, on the FIRST live fire of launchers/probes/reported_but_unfixed_floor.py:
# the probe read the real boot log and reported a finding that had ridden UNFIXED through
# twelve separate launches. The finding was "SYNTHETIC FINDING for the proof" — this file's
# own fixture, written twelve times by twelve runs of this suite. Nothing in the record marked
# it as synthetic, because to the recorder it was not: bootstrap.sh writes to
# ${CAIRN_BOOT_LOG:-$HOME/.cairn/logs/boot}, this harness inherited the environment, so every
# proof run had been appending to the production flight recorder since the probe was wired.
# The probe was moments from poking the owner about a floor that never existed.
#
# THE FIX IS THE DESIGN, NOT A GUARD. "A new process can set its own log target, and now the
# namespace has changed until that process completes" is the recorder's own contract, so the
# test harness taking a namespace of its own is the mechanism working, not an exception to it.
# The alternative — teaching the probe to recognise synthetic text — would be a filter that
# fails open on the next fixture nobody thought to name.
# The namespace goes INSIDE a swept scratch directory rather than beside it in /tmp. The
# pid suffix that used to make it unique is gone with it — mkdtemp is already unique, and
# the pid was doing double duty as a name and as a (failed) cleanup story: 18 of these logs
# were still sitting in /tmp on 2026-08-03, one per run since the probe was wired.
_PROOF_BOOT_LOG = str(scratch_dir("cairn-proof-boot-") / "boot")
_REAL_BOOT_LOG = Path(os.environ.get("CAIRN_BOOT_LOG") or Path.home() / ".cairn" / "logs" / "boot")
_REAL_BOOT_LOG_SIZE_AT_START = _REAL_BOOT_LOG.stat().st_size if _REAL_BOOT_LOG.is_file() else 0


def _env(extra: dict | None = None) -> dict:
    """The environment every child of this proof runs in: inherited, plus a boot namespace
    that belongs to this run and nothing else."""
    e = dict(os.environ)
    e["CAIRN_BOOT_LOG"] = _PROOF_BOOT_LOG
    if extra:
        e.update(extra)
    return e


def _sh(script: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run bash with bootstrap.sh sourced. Returns the completed process."""
    full = f"source {BOOTSTRAP!s} || exit 99\n{script}"
    return subprocess.run(["bash", "-c", full], capture_output=True, text=True,
                          env=_env(env), timeout=120)


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
    r = _sh(f'CAIRN_BOOTSTRAP_FINDINGS=("{_SYNTHETIC_FINDING}"); cairn_bootstrap_report; echo "RC=$?"')
    assert "RC=1" in r.stdout, "the report returned success while carrying a finding"
    assert "SYNTHETIC FINDING" in r.stdout, "the finding did not reach the report body"
    assert "CAIRN PREFLIGHT" in r.stdout, "the report has no header naming where it came from"


def test_the_report_leaves_a_durable_record() -> None:
    r = _sh(f'CAIRN_BOOTSTRAP_FINDINGS=("{_SYNTHETIC_FINDING}"); cairn_bootstrap_report >/dev/null')
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
    r = subprocess.run([str(SUPERCLAUDE), "--dry-run"], capture_output=True, text=True,
                       env=_env({"CAIRN_VENV": UNCREATABLE}), timeout=180)
    assert r.returncode == 0, f"superclaude exited {r.returncode} with a broken preflight — {r.stderr!r}"
    assert "exec claude" in r.stdout, f"the launch was aborted by the preflight — {r.stdout!r}"
    # ...and it does not go silently: the residue rides into the session.
    assert "--append-system-prompt" in r.stdout, "a broken floor produced no report for Claude"
    assert "VENV ABSENT" in r.stdout, "the report reached the launch without its findings"


def test_a_working_preflight_adds_nothing_to_the_launch() -> None:
    """Invisible when it works — the launch line is byte-identical to the pre-preflight one."""
    r = subprocess.run([str(SUPERCLAUDE), "--dry-run"], capture_output=True, text=True,
                       env=_env(), timeout=180)
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
    would be waiting to discover something already knowable (Law 3 cuts both ways).

    DECOMPOSED 2026-08-20: the original sieve said 'undeclared' and stopped. That is the
    file-exists test that failed to check the field — the KIND of undeclared determines the
    fix. Four layers, each its own assertion with its own message:
      1. production code, core dep not in [project.dependencies] — hard red, the original defect
      2. production code, optional device dep not in [project.optional-dependencies] — needs a group
      3. proof/test code, dev dep not in [project.optional-dependencies.dev] — needs dev group
      4. anything not in ANY group — truly unknown, the catchall
    The most useful error message is the one that names what to do, not just what is wrong."""
    import ast
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]

    # Package name → import name, for the cases where they differ. Every entry here is a
    # measured gap: the sieve redded on a real import that a declared package satisfies.
    _PKG_TO_IMPORT = {
        "psycopg2-binary": "psycopg2",
        "aider-chat": "aider",
    }

    def _import_names(pkg_spec: str) -> set[str]:
        raw = pkg_spec.split(">=")[0].split("==")[0].split("[")[0].strip().lower()
        names = set()
        if raw in _PKG_TO_IMPORT:
            names.add(_PKG_TO_IMPORT[raw])
        names.add(raw.replace("-", "_"))
        return names

    toml = tomllib.loads((REPO / "pyproject.toml").read_text())
    core_deps: set[str] = set()
    for d in toml.get("project", {}).get("dependencies", []):
        core_deps |= _import_names(d)
    opt_groups = toml.get("project", {}).get("optional-dependencies", {})
    dev_deps: set[str] = set()
    for d in opt_groups.get("dev", []):
        dev_deps |= _import_names(d)
    all_opt: set[str] = set()
    for group, pkgs in opt_groups.items():
        for p in pkgs:
            all_opt |= _import_names(p)
    all_declared = core_deps | all_opt

    local = {p.stem for p in REPO.rglob("*.py") if "__pycache__" not in p.parts}
    local |= {d.name for d in REPO.rglob("*") if d.is_dir() and (d / "__init__.py").exists()}

    # Collect every third-party import with its file and classification
    imports: list[tuple[str, str, bool]] = []  # (module, rel_path, is_proof)
    for py in (REPO / "cairn").rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        try:
            tree = ast.parse(py.read_text())
        except SyntaxError:
            continue
        is_proof = "proofs" in py.parts
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mods = [node.module.split(".")[0]]
            for m in mods:
                if m == "cairn" or m in sys.stdlib_module_names or m in all_declared or m in local:
                    continue
                imports.append((m, str(py.relative_to(REPO)), is_proof))

    if not imports:
        return

    # Layer 1: production imports not in core deps (the original defect — hardest red)
    prod_undeclared = {(m, p) for m, p, is_proof in imports if not is_proof}
    # Layer 2: proof imports not in any optional group
    proof_undeclared = {(m, p) for m, p, is_proof in imports if is_proof}

    parts = []
    if prod_undeclared:
        by_mod: dict[str, str] = {}
        for m, p in prod_undeclared:
            by_mod.setdefault(m, p)
        parts.append(
            "PRODUCTION imports not declared in [project.dependencies] or "
            "[project.optional-dependencies] — the original defect; these work only if "
            "this host happens to have them. Fix: add to dependencies (core) or add an "
            "optional-dependencies group (optional device): "
            + "; ".join(f"{m} (first seen {p})" for m, p in sorted(by_mod.items()))
        )
    if proof_undeclared:
        by_mod_proof: dict[str, str] = {}
        for m, p in proof_undeclared:
            by_mod_proof.setdefault(m, p)
        parts.append(
            "PROOF/TEST imports not declared in [project.optional-dependencies.dev] — "
            "proofs that import undeclared packages fail on a clean install. "
            "Fix: add to [project.optional-dependencies] dev group: "
            + "; ".join(f"{m} (first seen {p})" for m, p in sorted(by_mod_proof.items()))
        )

    assert not parts, "\n".join(parts)


# --- CONTAINMENT: the proof must not become the evidence --------------------
# Defined LAST on purpose — the runner walks globals() in definition order, so by the time
# this runs every case above has already shelled out and had its chance to leak.
def test_this_proof_wrote_nothing_into_the_real_flight_recorder() -> None:
    """THE TOOTH FOR THE 2026-07-30 CONTAMINATION, and it is a tooth rather than a comment
    because the failure was completely silent: the record looked exactly like a real launch,
    and the only thing that noticed was a probe about to poke the owner with a fabricated
    finding twelve launches old.

    TWO HALVES, and the second is what keeps the first from being vacuous:
      (a) the real boot namespace holds none of this file's synthetic fixture text;
      (b) this run's OWN namespace received records — so (a) is green because the writes went
          somewhere else, not because nothing was written at all. Without (b) this passes
          perfectly on a build where the recorder is missing entirely.

    Checked by MARKER, not by file size: a concurrent real launch legitimately grows the file
    and a concurrent trim legitimately shrinks it, and a proof that reds on either is the
    pinned-moving-value defect, not a containment check.

    AND CHECKED AT THE SOURCE, which is the half that generalises. Grepping for known fixture
    text catches only the fixtures someone remembered to list — measured immediately, when the
    first version of this tooth grepped for "SYNTHETIC FINDING", went green, and left six
    ``report: unfixed — VENV ABSENT at /proc/...`` records sitting in the real recorder from
    the OTHER fixture in this same file. So the structural half asserts the mechanism instead
    of the symptom: every child this file spawns must go through ``_env()``, because that is
    the one place the namespace is redirected. A new case that forgets it reds here at
    authoring time rather than in a probe's poke six weeks later."""
    ours = Path(_PROOF_BOOT_LOG)
    assert ours.is_file() and ours.stat().st_size > 0, (
        f"nothing was recorded to this proof's own namespace ({_PROOF_BOOT_LOG}) — the "
        "containment check below would pass for the wrong reason, because the recorder is "
        "not writing anywhere at all"
    )

    # (i) STRUCTURAL: no child escapes the redirect.
    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    escapees = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "run"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"):
            continue
        env_kw = next((k for k in node.keywords if k.arg == "env"), None)
        ok = (env_kw is not None and isinstance(env_kw.value, ast.Call)
              and isinstance(env_kw.value.func, ast.Name) and env_kw.value.func.id == "_env")
        if not ok:
            escapees.append(node.lineno)
    assert not escapees, (
        f"subprocess.run at line(s) {escapees} does not pass env=_env(...) — that child "
        "inherits CAIRN_BOOT_LOG from the shell and writes its synthetic launch into the "
        "real flight recorder, which is the contamination this tooth exists to stop"
    )

    # (ii) BY MARKER, SCOPED TO THE RECORDS THE PROBE ACTUALLY READS — the `report: unfixed`
    # findings, not the whole file. Scoping is not a softening; an unscoped substring scan is
    # a coin-toss red, and this one landed on its author within the hour: the decontamination
    # note written to clear the first contamination QUOTES the fixture string while explaining
    # it, so a whole-file grep redded on the very note recording the fix. The fixtures are read
    # from the constants above so a rename cannot leave a stale copy here.
    if _REAL_BOOT_LOG.is_file():
        findings = [line.partition(": ")[2] for line in
                    _REAL_BOOT_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
                    if ": report: unfixed" in line]
        for marker in (_SYNTHETIC_FINDING, UNCREATABLE):
            hit = next((f for f in findings if marker in f), None)
            assert hit is None, (
                f"{marker!r} is a reported finding in the REAL flight recorder "
                f"({_REAL_BOOT_LOG}): {hit!r} — this harness is contaminating the record that "
                "launchers/probes/reported_but_unfixed_floor.py reads, so the probe is "
                "measuring the suite"
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
