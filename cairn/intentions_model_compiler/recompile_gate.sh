#!/usr/bin/env bash
# recompile_gate.sh — child c of intentions-model-compiler: the WRITE GATE's command.
#
# A source changed on disk (a beside-code intention+why.json, or an intentions-other/
# entry); this pokes the compile door so intentions/_model.json regenerates with no human
# running anything. Shrinking-footprint: the write IS the event, no poller. It is wired to
# a FileChanged host hook in .claude/settings.local.json (instance-space, not git) — the
# host_seam recorded in this component's charter.
#
# HOST-NOTICING, NOT OWNER-EMITTING (the IOU, named in the charter): this is a host
# filesystem watcher standing in for the not-yet-built owner-gate emit (the emit-chokepoint
# state-machine-physics.json tracks). A stopgap that labels itself one; it retires when that
# physics lands, and its seal expires on host drift (nothing in git changes).
#
# Safe for a hook that fires on saves: it NEVER blocks the session (always exits 0), adds no
# noise on success, and — Law 7 — a compile that fails is not swallowed but RECORDED to the
# instance-space log (loud in the record even as the surface stays quiet).
#
# Testable + real-by-default: with no env set it compiles the real model; the proof points
# CAIRN_COMMONS_ROOT / CAIRN_CODE_ROOT / CAIRN_MODEL_OUT (and CAIRN_LOG_DIR) at a temp tree.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"          # component -> cairn package -> repo root
LOG="${CAIRN_LOG_DIR:-$HOME/.cairn/logs}/recompile-gate.log"

mkdir -p "$(dirname "$LOG")" 2>/dev/null || true

if ! out="$(cd "$REPO" && python3 -c 'import os
from cairn.intentions_model_compiler.compiler import compile_to_disk
compile_to_disk(
    commons_root=os.environ.get("CAIRN_COMMONS_ROOT") or None,
    code_root=os.environ.get("CAIRN_CODE_ROOT") or None,
    out_path=os.environ.get("CAIRN_MODEL_OUT") or None,
)' 2>&1)"; then
  printf '%s recompile-gate FAILED: %s\n' "$(date -Iseconds)" "$out" >> "$LOG" 2>/dev/null || true
fi
exit 0
