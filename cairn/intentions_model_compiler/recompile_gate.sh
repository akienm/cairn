#!/usr/bin/env bash
# recompile_gate.sh — child c of intentions-model-compiler: the WRITE GATE's command.
#
# A source changed (a beside-code intention+why.json, or an intentions-other/ entry); this
# pokes the compile door so intentions/_model.json regenerates. Shrinking-footprint: the
# WRITER pokes the door, no poller. Invoked by the WRITE-THROUGH CONTRACT — the skills
# (/sorted) poke it in the same act that writes a source — and by the NIGHTLY REBUILD cron
# backstop. The host_seam recorded in this component's charter is the full contract.
#
# The prior FileChanged host hook is RETIRED (measured 2026-07-23 not to fire on CC's own
# writes); the semantic writer poking the door replaced it.
#
# HOST-NOTICING-BY-DISCIPLINE for the beside-code case (the IOU, named in the charter): CC
# poking the door after writing a charter is convention, not physics — standing in for the
# not-yet-built owner-gate emit (the emit-chokepoint state-machine-physics.json tracks). A
# stopgap that labels itself one; the nightly rebuild backstops it until that physics lands,
# and its seal expires on host drift (nothing in git changes).
#
# Safe for a trigger that fires often: it NEVER blocks its caller (always exits 0), adds no
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
