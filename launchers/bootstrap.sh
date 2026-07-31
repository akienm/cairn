#!/usr/bin/env bash
# cairn/launchers/bootstrap.sh — the HOST-SEAM that brings the floor up before Claude Code starts.
#
# Charter + why: cairn/launchers/intention+why.json
# Ticket:        CairnCommons/tickets/superclaude-starts-itself.json
#
# ── WHAT ─────────────────────────────────────────────────────────────────────
# Sourceable. Exposes four functions and owns one artifact (a venv in instance-space):
#
#   cairn_venv_dir        echo the venv path      (~/.cairn/venv, or $CAIRN_VENV)
#   cairn_python          echo the python to use  (venv's if usable, else system python3)
#   cairn_bootstrap_verify   re-runnable: is the floor up? 0 = yes. Writes findings, fixes nothing.
#   cairn_bootstrap_apply    replayable: bring the floor up. Never fatal, always reports.
#
# verify + apply are the two halves CLAUDE.md requires of a host-seam: the implementation
# lives where git cannot see it (a venv is machine-specific compiled bytes), so the seam
# carries a recipe to rebuild it and a check that re-measures it. The seal EXPIRES — the
# host drifts with nothing in git changing, which is exactly what happened here.
#
# ── WHY THIS EXISTS (measured 2026-07-30, not hypothesised) ──────────────────
# A session opened, tried to run one proof, and burned four tool calls finding out how:
# `cairn test` (right address, empty), pytest (nothing in this repo uses pytest — the
# tester runs proofs bare as [sys.executable, path]), a module path (absent), and finally
# reading the proof to find the answer in its docstring. Law 1: an answered question that
# did not become structure, re-derived. Underneath it sat a real defect — pyproject
# promised "`pip install -e .` stays green at all times" while the install had NEVER been
# performed, `cairn` imported only because cwd happened to be the repo root, and PEP 668
# refuses that install into system python outright. The promise could not have been kept
# where it was made.
#
# ── WHY THE VENV IS NOT IN THE REPO ──────────────────────────────────────────
# CLAUDE.md's three roots: class-space holds "no runtime state, ever". A tree of
# machine-specific compiled bytes is runtime state by any reading. The tell is decisive —
# a repo-local .venv/ would need gitignoring, and needing to hide something from git means
# it is in the wrong root. So it lives at ~/.cairn/venv (instance-space, never in git).
#
# ── WHY A CLEAN VENV, NOT --system-site-packages ─────────────────────────────
# Considered and refused. Inheriting system site-packages would let this box's existing
# psycopg2 satisfy the dependency with no download, which is tempting for an offline
# rescue. But it makes the floor's contents a function of what the host happens to have,
# which is the very hypothesis that put us here — and psycopg2 + psycopg2-binary in one
# import namespace is a documented shadowing footgun. Reproducibility over offline
# cleverness: a clean venv, a binary wheel, the same floor on every box.
#
# ── NEVER `set -e` IN THIS FILE ──────────────────────────────────────────────
# This is SOURCED by superclaude, whose prime directive is that nothing between parse and
# exec may abort the launch. `set -e` in a sourced file leaks into the CALLER's shell, so
# one failed probe here would kill the launch — the precise inverse of the rescue ethos
# (be the tier that still works when the machinery does not). Every function below RETURNS
# a code; not one of them exits.

CAIRN_BOOTSTRAP_SOURCED=1

# Resolve through symlinks before dirname — superclaude is linked into ~/.local/bin, and
# without readlink -f this would compute the LINK's directory. Same lesson bin/cairn
# learned on 2026-07-26; it is written down in both places because both places pay for it.
CAIRN_LAUNCHERS_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
CAIRN_REPO_ROOT="$(cd "$CAIRN_LAUNCHERS_DIR/.." && pwd)"

# Findings accumulate here — one line each, complete enough to act on (see the report
# contract below). Reset by verify, appended to by apply.
CAIRN_BOOTSTRAP_FINDINGS=()

# ── THE PROBE (WATCHME) ──────────────────────────────────────────────────────
# The report answers "what is broken NOW". This answers the question that needed TIME:
# does a floor this seam REPORTED but could not fix actually get fixed — or does the same
# finding ride in on --append-system-prompt launch after launch, a diagnostic everyone has
# learned to scroll past? That is unanswerable from any single run and from anything in
# git, so it is not a proof; it is a probe that lives where it watches (Law 3).
#
# It writes to its own namespace, ~/.cairn/logs/boot, so a boot's trail is greppable apart
# from ordinary shell traffic. Every launch appends what was tried, what came back, and
# what it cost; the last 1000 lines are the evidence.
if [[ -z "${CAIRN_LOGGER_SOURCED:-}" && -r "$CAIRN_REPO_ROOT/bin/logger_for_bash" ]]; then
  # shellcheck source=/dev/null
  source "$CAIRN_REPO_ROOT/bin/logger_for_bash" 2>/dev/null || true
fi

# Saves and restores CAIRN_LOGTARGET around every call rather than exporting it once.
# This file is SOURCED — setting the namespace globally would hijack the logging of any
# interactive shell that sourced it, and keep it hijacked. A child process gets its own
# namespace for free by exporting; a sourced file has to put it back.
_cairn_boot_log() {
  declare -F lognote >/dev/null 2>&1 || return 0
  local _save="${CAIRN_LOGTARGET:-}" _had="${CAIRN_LOGTARGET+set}"
  CAIRN_LOGTARGET="${CAIRN_BOOT_LOG:-$HOME/.cairn/logs/boot}"
  lognote "$@" 2>/dev/null
  if [[ -n "$_had" ]]; then CAIRN_LOGTARGET="$_save"; else unset CAIRN_LOGTARGET; fi
  return 0
}

cairn_venv_dir() {
  echo "${CAIRN_VENV:-$HOME/.cairn/venv}"
}

cairn_python() {
  local vpy
  vpy="$(cairn_venv_dir)/bin/python3"
  if [[ -x "$vpy" ]]; then echo "$vpy"; else echo "python3"; fi
}

# The stamp gates only the EXPENSIVE half (a pip install costs seconds). It is not itself
# the verify — a matching stamp over a broken venv is a lie, and Law 3 says the floor is
# not known to be up until it is measured. So verify does both: the stamp decides whether
# a REBUILD is owed, and a real import decides whether the floor is actually there.
_cairn_stamp_want() {
  local py_version
  py_version="$(python3 -V 2>&1)"
  # Repo path is in the stamp because the editable install points AT it: the same venv
  # against a moved checkout is stale even with an identical pyproject.
  printf '%s\n%s\n%s\n' \
    "$CAIRN_REPO_ROOT" \
    "$py_version" \
    "$(sha256sum "$CAIRN_REPO_ROOT/pyproject.toml" 2>/dev/null | cut -d' ' -f1)"
}

_cairn_stamp_file() { echo "$(cairn_venv_dir)/.cairn-stamp"; }

# ── verify — re-runnable, measures, repairs nothing ──────────────────────────
# Returns 0 when the floor is up. Every failure appends a finding carrying what a fixer
# needs on the FIRST report: what was probed, what came back, and where it lives. Akien's
# framework — a diagnostic that forces a second run to gather more has failed at its job.
cairn_bootstrap_verify() {
  CAIRN_BOOTSTRAP_FINDINGS=()
  local venv vpy rc out
  venv="$(cairn_venv_dir)"
  vpy="$venv/bin/python3"
  _cairn_boot_log "verify: begin — venv=$venv root=$CAIRN_REPO_ROOT"

  if ! command -v python3 >/dev/null 2>&1; then
    CAIRN_BOOTSTRAP_FINDINGS+=("NO PYTHON3 ON PATH — nothing below can be measured. PATH=$PATH")
    _cairn_boot_log "verify: FAIL no-python3 — PATH=$PATH"
    return 1
  fi

  if [[ ! -x "$vpy" ]]; then
    _cairn_boot_log "verify: FAIL venv-absent — $vpy is not executable"
    CAIRN_BOOTSTRAP_FINDINGS+=("VENV ABSENT at $venv (no $vpy). Nothing is installed; \`cairn\` imports only from the repo root, and only by cwd accident. Repair: cairn_bootstrap_apply, or \`python3 -m venv $venv && $venv/bin/pip install -e $CAIRN_REPO_ROOT\`.")
    return 1
  fi

  # The real measurement: does the import root actually resolve, from a cwd that is NOT
  # the repo? Running this from / is the whole point — importing from the repo root proves
  # nothing, because that is the accident we are trying to stop relying on.
  out="$(cd / && "$vpy" -c 'import cairn, sys; print(cairn.__file__)' 2>&1)"; rc=$?
  _cairn_boot_log "verify: probe import-cairn-from-/ -> rc=$rc out=${out//$'\n'/ | }"
  if [[ $rc -ne 0 ]]; then
    CAIRN_BOOTSTRAP_FINDINGS+=("IMPORT ROOT BROKEN — \`$vpy -c 'import cairn'\` run from / exited $rc. Output: ${out//$'\n'/ | }. The venv exists but the editable install is missing or points elsewhere. Repair: $venv/bin/pip install -e $CAIRN_REPO_ROOT")
    return 1
  fi
  # A venv that imports SOME OTHER checkout's cairn is a subtler wrong than none at all.
  case "$out" in
    "$CAIRN_REPO_ROOT"/*) : ;;
    *) CAIRN_BOOTSTRAP_FINDINGS+=("IMPORT ROOT POINTS ELSEWHERE — \`import cairn\` resolves to $out but this launcher lives under $CAIRN_REPO_ROOT. The venv is installed against a different checkout. Repair: $venv/bin/pip install -e $CAIRN_REPO_ROOT")
       _cairn_boot_log "verify: FAIL import-points-elsewhere — $out is not under $CAIRN_REPO_ROOT"
       return 1 ;;
  esac

  out="$(cd / && "$vpy" -c 'import psycopg2; print(psycopg2.__version__)' 2>&1)"; rc=$?
  _cairn_boot_log "verify: probe import-psycopg2 -> rc=$rc out=${out//$'\n'/ | }"
  if [[ $rc -ne 0 ]]; then
    CAIRN_BOOTSTRAP_FINDINGS+=("psycopg2 MISSING from the venv — exited $rc. Output: ${out//$'\n'/ | }. cairn/db_domain/ imports it at module scope, so the db domain will fail far from this cause. Repair: $venv/bin/pip install -e $CAIRN_REPO_ROOT")
    return 1
  fi

  if [[ "$(cat "$(_cairn_stamp_file)" 2>/dev/null)" != "$(_cairn_stamp_want)" ]]; then
    CAIRN_BOOTSTRAP_FINDINGS+=("FLOOR IS STALE — the venv works but its stamp does not match the current pyproject.toml / python / checkout path. Dependencies may have moved since it was built. Repair: cairn_bootstrap_apply")
    _cairn_boot_log "verify: FAIL stamp-mismatch — a rebuild is owed"
    return 1
  fi

  _cairn_boot_log "verify: OK floor is up"
  return 0
}

# ── apply — replayable, brings the floor up, never fatal ─────────────────────
# Returns 0 if the floor is up when it finishes. Findings survive for the report.
cairn_bootstrap_apply() {
  local venv vpy rc out
  venv="$(cairn_venv_dir)"
  vpy="$venv/bin/python3"
  # The probe's sharpest signal: apply running AT ALL means the previous launch's floor did
  # not survive. Two applies in a row for the same reason is a repair that is not repairing.
  _cairn_boot_log "apply: begin — the floor was not up"

  if ! command -v python3 >/dev/null 2>&1; then
    CAIRN_BOOTSTRAP_FINDINGS+=("CANNOT REPAIR — no python3 on PATH to build a venv with. This is below Cairn's floor; it needs a host fix (apt install python3) before anything here can run.")
    return 1
  fi

  if [[ ! -x "$vpy" ]]; then
    # `python3 -m venv` does NOT create intermediate directories — measured 2026-07-30,
    # it exits 1 with ENOENT on the parent. On a genuinely bare box ~/.cairn does not
    # exist yet, which is precisely the box this tier exists to serve, so the seam makes
    # its own parent rather than reporting a failure it could have prevented.
    mkdir -p "$(dirname "$venv")" 2>/dev/null
    out="$(python3 -m venv "$venv" 2>&1)"; rc=$?
    _cairn_boot_log "apply: step create-venv \`python3 -m venv $venv\` -> rc=$rc out=${out//$'\n'/ | }"
    if [[ $rc -ne 0 ]]; then
      # The hint names CANDIDATES, never a cause. An earlier draft asserted "usually the
      # missing ensurepip package" and was measured saying exactly that over an ENOENT on
      # the parent directory — a diagnostic surface that confidently names the wrong cause
      # is worse than one that stays quiet (Law 7). The measured Output above is the fact;
      # everything after it is labelled as a guess.
      CAIRN_BOOTSTRAP_FINDINGS+=("VENV CREATE FAILED — \`python3 -m venv $venv\` exited $rc. Output: ${out//$'\n'/ | }. Read that output first; candidates if it is unclear: ensurepip absent (apt install python3-venv), the path not writable, or the disk full.")
      return 1
    fi
  fi

  # --editable: the import root must FOLLOW the working tree, not snapshot it. A regular
  # install would freeze today's bytes and every later edit would be invisible to anything
  # importing cairn from outside the repo — a silent lie, the worst kind (Law 7).
  out="$("$vpy" -m pip install --quiet --editable "$CAIRN_REPO_ROOT" 2>&1)"; rc=$?
  _cairn_boot_log "apply: step editable-install \`$vpy -m pip install -e $CAIRN_REPO_ROOT\` -> rc=$rc out=${out//$'\n'/ | }"
  if [[ $rc -ne 0 ]]; then
    CAIRN_BOOTSTRAP_FINDINGS+=("EDITABLE INSTALL FAILED — \`$vpy -m pip install -e $CAIRN_REPO_ROOT\` exited $rc. Output: ${out//$'\n'/ | }. If this is a network failure the box is offline and the floor cannot be built from PyPI; the venv itself is fine and the repo-root cwd path still works.")
    return 1
  fi

  # Stamp LAST and only on success — a stamp written before the install would mark a floor
  # that was never laid, and the fast path would then skip the repair forever.
  _cairn_stamp_want > "$(_cairn_stamp_file)" 2>/dev/null

  cairn_bootstrap_verify
  rc=$?
  _cairn_boot_log "apply: end -> rc=$rc (0 = the floor is up after repair)"
  return $rc
}

# ── the report — what reaches Claude ─────────────────────────────────────────
# Two destinations, because they answer different questions:
#   (1) ~/.cairn/logs/preflight.json — durable, forensic, survives the session.
#   (2) stdout of this function      — the text superclaude hands to Claude Code via
#                                      --append-system-prompt, so the session OPENS
#                                      already knowing what is broken.
# Silence when the floor is up is the whole design: the tool is invisible when it works,
# and speaks only when there is something for Claude to fix.
cairn_bootstrap_report() {
  local venv logdir
  venv="$(cairn_venv_dir)"
  logdir="$HOME/.cairn/logs"
  mkdir -p "$logdir" 2>/dev/null

  # JSON through python3's own encoder — hand-rolled escaping in bash is how a report
  # becomes unparseable at the exact moment someone needs it.
  if command -v python3 >/dev/null 2>&1; then
    CAIRN_RPT_VENV="$venv" CAIRN_RPT_ROOT="$CAIRN_REPO_ROOT" \
    CAIRN_RPT_FINDINGS="$(printf '%s\n' ${CAIRN_BOOTSTRAP_FINDINGS+"${CAIRN_BOOTSTRAP_FINDINGS[@]}"})" \
    python3 -c '
import json, os, sys, datetime
findings = [f for f in os.environ.get("CAIRN_RPT_FINDINGS", "").split("\n") if f.strip()]
json.dump({
    "component": "launchers/bootstrap.sh",
    "measured_at": datetime.datetime.now().isoformat(timespec="seconds"),
    "venv": os.environ["CAIRN_RPT_VENV"],
    "repo_root": os.environ["CAIRN_RPT_ROOT"],
    "floor_up": not findings,
    "findings": findings,
}, open(sys.argv[1], "w"), indent=2)
' "$logdir/preflight.json" 2>/dev/null
  fi

  # The probe's payload line. Findings here are the ones that SURVIVED apply — the set that
  # reaches Claude and asks to be fixed. Grep `report:` in ~/.cairn/logs/boot and the same
  # finding text recurring across launches is the measurement: reported, and not fixed.
  _cairn_boot_log "report: findings=${#CAIRN_BOOTSTRAP_FINDINGS[@]} floor_up=$([[ ${#CAIRN_BOOTSTRAP_FINDINGS[@]} -eq 0 ]] && echo yes || echo no)"
  local f
  for f in ${CAIRN_BOOTSTRAP_FINDINGS+"${CAIRN_BOOTSTRAP_FINDINGS[@]}"}; do
    _cairn_boot_log "report: unfixed — $f"
  done

  [[ ${#CAIRN_BOOTSTRAP_FINDINGS[@]} -eq 0 ]] && return 0

  echo "CAIRN PREFLIGHT — the launcher tried to bring the floor up and could not finish."
  echo "These are MEASURED at launch (host-seam: cairn/launchers/bootstrap.sh), not guesses."
  echo "Full record: $logdir/preflight.json  ·  re-measure: cairn_bootstrap_verify"
  echo
  local f
  for f in "${CAIRN_BOOTSTRAP_FINDINGS[@]}"; do echo "  - $f"; done
  echo
  echo "Until these are fixed, python3 outside $CAIRN_REPO_ROOT cannot import cairn."
  return 1
}
