#!/usr/bin/env bash
# recompile_gate.sh — child c of intentions-model-compiler: the WRITE GATE's command.
#
# A source changed (a beside-code intention+why.json, or an intentions-other/ entry); this
# pokes the copy door so intentions-congruency-lab/ regenerates. Shrinking-footprint: the
# WRITER pokes the door, no poller. Invoked by EVENTS only — /sorted pokes it on a source
# write (write-through) and /intent pokes it before consulting the model (read-refresh); the
# read and the write are the events, never a clock. The host_seam in this charter is the full
# contract.
#
# The prior FileChanged host hook is RETIRED (measured 2026-07-23 not to fire on CC's own
# writes); the semantic writer poking the door replaced it.
#
# HOST-NOTICING-BY-DISCIPLINE for the beside-code case (named in the charter): CC
# poking the door after writing a charter is convention, not physics — standing in for the
# not-yet-built owner-gate emit (the emit-chokepoint state-machine-physics.json tracks). A
# stopgap that labels itself one; the read-refresh at /intent backstops it until that physics
# lands — the read is the event, no daemon.
#
# Safe for a trigger that fires often: it NEVER blocks its caller (always exits 0), adds no
# noise on success, and — Law 7 — a compile that fails is not swallowed but RECORDED to the
# instance-space log (loud in the record even as the surface stays quiet).
#
# Testable + real-by-default: with no env set it compiles the real model; the proof points
# CAIRN_COMMONS_ROOT / CAIRN_CODE_ROOT / CAIRN_LAB_OUT (and CAIRN_LOG_DIR) at a temp tree.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"       # component -> tools -> cairn package -> repo root
LOG="${CAIRN_LOG_DIR:-$HOME/.cairn/logs}/recompile-gate.log"

# INSTALL MODE (ticket f09cd0588ceb): `recompile_gate.sh install <repo>` lays hooks/post-merge
# into the repo's common hooks dir with this gate's absolute path baked in, so a merge that
# changes a lab source pokes this gate. Idempotent: a second install writes the same bytes. A
# post-merge that is not ours is refused, never overwritten. Any other argument compiles as before.
if [ "${1:-}" = "install" ]; then
  repo="${2:?usage: recompile_gate.sh install <repo>}"
  hooks="$(git -C "$repo" rev-parse --path-format=absolute --git-common-dir)/hooks" || exit 1
  dest="$hooks/post-merge"
  if [ -e "$dest" ] && ! grep -q "ticket f09cd0588ceb" "$dest"; then
    echo "recompile_gate install: $dest is not this gate's hook; refusing to overwrite it" >&2
    exit 1
  fi
  mkdir -p "$hooks" && tmp="$hooks/.post-merge.$$" \
    && sed "s|@GATE@|$HERE/recompile_gate.sh|" "$HERE/hooks/post-merge" > "$tmp" \
    && chmod +x "$tmp" && mv -f "$tmp" "$dest" || exit 1
  echo "$dest"
  exit 0
fi

mkdir -p "$(dirname "$LOG")" 2>/dev/null || true

# THE INTERPRETER (ticket 2dda7060d84e). A bare `python3` is not always a Python: on Windows
# it can be the Store alias stub, which prints an install hint and exits 9009 (measured
# 2026-11-16 on akienyoga9i, where the lab never regenerated). So try the box's cairn venv
# first, in the order bootstrap.sh's cairn_python uses (cited, not sourced: RULE 1). Then
# try each PATH name, but only one that really runs Python 3.
_gate_venv="${CAIRN_VENV:-$HOME/.cairn/venv}"
_gate_python() {
  local c
  for c in "$_gate_venv/bin/python3" "$_gate_venv/Scripts/python.exe"; do
    if [ -x "$c" ]; then echo "$c"; return 0; fi
  done
  for c in python3 python py; do
    if "$c" -c 'import sys; sys.exit(0 if sys.version_info[0]==3 else 1)' >/dev/null 2>&1; then
      echo "$c"; return 0
    fi
  done
  return 1
}

if ! PY="$(_gate_python)"; then
  printf '%s recompile-gate FAILED: no Python 3 interpreter found (tried %s %s python3 python py)\n' \
    "$(date -Iseconds)" "$_gate_venv/bin/python3" "$_gate_venv/Scripts/python.exe" >> "$LOG" 2>/dev/null || true
  exit 0
fi

if ! out="$(cd "$REPO" && "$PY" -c 'import os
from cairn.tools.intentions_model_compiler.compiler import copy_to_lab, lab_path, _default_roots
commons = os.environ.get("CAIRN_COMMONS_ROOT") or _default_roots()[0]
out_dir = os.environ.get("CAIRN_LAB_OUT") or lab_path(commons)
copy_to_lab(
    commons_root=os.environ.get("CAIRN_COMMONS_ROOT") or None,
    code_root=os.environ.get("CAIRN_CODE_ROOT") or None,
    out_dir=out_dir,
)
print(out_dir)' 2>&1)"; then
  printf '%s recompile-gate FAILED: %s
' "$(date -Iseconds)" "$out" >> "$LOG" 2>/dev/null || true
  exit 0
fi

# THE LAB RIDES WITH ITS CHARTER (ticket 09b1565a2045). The regenerated lab copies are tracked
# in the commons; left uncommitted they abort the next `git pull --ff-only` on every box that
# merges a charter change. So the gate commits what it regenerated, path-limited to the lab
# (never anything else staged), and a failed commit is RECORDED naming the files left
# uncommitted (Law 7) — it still never blocks its caller.
lab="$(printf '%s
' "$out" | tail -n 1)"
if [ -d "$lab" ] && git -C "$lab" rev-parse --git-dir >/dev/null 2>&1; then
  dirt="$(git -C "$lab" status --porcelain -- . 2>/dev/null)"
  if [ -n "$dirt" ]; then
    if ! cerr="$(git -C "$lab" add -A -- . 2>&1 && git -C "$lab" commit -q -m "intentions-congruency-lab: regenerated from changed charters (recompile_gate, ticket 09b1565a2045)" -- . 2>&1)"; then
      printf '%s recompile-gate FAILED: lab commit refused, left uncommitted: %s :: %s
' "$(date -Iseconds)"         "$(printf '%s' "$dirt" | sed 's/^...//' | tr '
' ' ')" "$cerr" >> "$LOG" 2>/dev/null || true
    fi
  fi
fi
exit 0
