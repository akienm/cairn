#!/usr/bin/env bash
# cairn/launchers/bootstrap_first_run.sh — the zero-to-librarian path.
#
# Called by bin/cairn when instance-space is not wired yet.
# Brings up everything a fresh download needs:
#   1. venv + editable install (delegates to bootstrap.sh)
#   2. cairn on PATH via ~/.local/bin
#   3. instance-space wiring (~/.cairn/devices/<dev>/<instance>/bin → class-space)
#   4. ground loop + web server (delegates to the librarian launcher)
#   5. opens the browser to the librarian's page
#
# Idempotent — safe to run again if something failed partway. Each step checks
# whether its work is already done before doing it.
#
# NOT set -e: same prime directive as superclaude — a broken step reports and
# continues rather than aborting the whole setup.
set -uo pipefail

HERE="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
INSTANCE_ROOT="${CAIRN_INSTANCE_ROOT:-$HOME/.cairn/devices}"

echo "cairn: first run detected — setting up."
echo ""

# ── Step 1: venv + editable install ─────────────────────────────────────────
echo "[1/5] venv + editable install..."
# shellcheck source=/dev/null
source "$HERE/bootstrap.sh" 2>/dev/null || true
if declare -F cairn_bootstrap_verify >/dev/null 2>&1; then
  if cairn_bootstrap_verify >/dev/null 2>&1; then
    echo "  already up."
  elif cairn_bootstrap_apply >/dev/null 2>&1; then
    echo "  done."
  else
    echo "  WARNING: could not bring up the venv. Continuing anyway." >&2
    echo "  findings: ${CAIRN_BOOTSTRAP_FINDINGS[*]:-none}" >&2
  fi
  venv_bin="$(cairn_venv_dir)/bin"
  [[ -d "$venv_bin" ]] && export PATH="$venv_bin:$PATH"
else
  echo "  WARNING: bootstrap.sh did not load. Continuing without venv." >&2
fi

# ── Step 2: cairn on PATH ───────────────────────────────────────────────────
echo "[2/5] cairn on PATH..."
LOCAL_BIN="$HOME/.local/bin"
CAIRN_LINK="$LOCAL_BIN/cairn"
if command -v cairn >/dev/null 2>&1; then
  echo "  already on PATH: $(command -v cairn)"
elif [[ -L "$CAIRN_LINK" || -f "$CAIRN_LINK" ]]; then
  echo "  link exists at $CAIRN_LINK but not on PATH."
  echo "  add $LOCAL_BIN to your PATH to use 'cairn' from anywhere."
else
  mkdir -p "$LOCAL_BIN" 2>/dev/null || true
  if ln -sf "$REPO_ROOT/bin/cairn" "$CAIRN_LINK" 2>/dev/null; then
    echo "  linked: $CAIRN_LINK -> $REPO_ROOT/bin/cairn"
    if ! echo "$PATH" | tr ':' '\n' | grep -qx "$LOCAL_BIN"; then
      echo "  NOTE: $LOCAL_BIN is not on your PATH yet."
      echo "  add to your shell profile: export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
  else
    echo "  WARNING: could not create symlink at $CAIRN_LINK" >&2
  fi
fi

# ── Step 3: instance-space wiring ───────────────────────────────────────────
echo "[3/5] instance-space device wiring..."
# The recipe lives in bootstrap.sh as cairn_wire_instances (lifted 2026-09-16, ticket
# 0853294fe972) so bin/cairn's floor check and this first run share it rather than copy it.
if declare -F cairn_wire_instances >/dev/null 2>&1; then
  echo "  $(CAIRN_INSTANCE_ROOT="$INSTANCE_ROOT" cairn_wire_instances) device(s)."
else
  echo "  WARNING: bootstrap.sh did not load — nothing wired." >&2
fi

# ── Step 4: ground loop + web server ────────────────────────────────────────
echo "[4/5] starting ground loop + web server..."
librarian_bin="$INSTANCE_ROOT/librarian/0/bin/librarian"
if [[ -x "$librarian_bin" ]]; then
  "$librarian_bin" 2>&1 | while IFS= read -r line; do echo "  $line"; done
else
  echo "  WARNING: librarian not wired at $librarian_bin" >&2
  echo "  the ground loop and web server were not started." >&2
fi

# ── Step 5: open the browser ───────────────────────────────────────────────
echo "[5/5] opening the librarian..."
LIBRARIAN_URL="http://10.0.0.229/device/librarian"
if command -v python3 >/dev/null 2>&1; then
  python3 -m webbrowser "$LIBRARIAN_URL" >/dev/null 2>&1 &
  disown 2>/dev/null || true
  echo "  opened $LIBRARIAN_URL in your browser."
else
  echo "  open $LIBRARIAN_URL in your browser to chat with the librarian."
fi

echo ""
echo "cairn is set up. from now on, just type 'cairn' to launch the librarian."
echo "for the builder's console: cairn superclaude"
