#!/usr/bin/env bash
set -euo pipefail

# --- paths ---
THIS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
ROOT_DIR="$(cd "$THIS_DIR/.." && pwd)"     # -> .../ai-agent
SRC_DIR="$THIS_DIR/src"                    # -> .../ai-agent/py/src
ENV_NAME="${AI_AGENT_CONDA_ENV:-ai-agent-py}"

# --- load env vars ---
if [[ -f "$ROOT_DIR/.env" ]]; then
set -a
. "$ROOT_DIR/.env"
set +a
fi

run_python() {
  # Make both ai-agent/py/src and ai-agent/ visible to imports
  local PYTHONPATH_VAL="$SRC_DIR:$ROOT_DIR:${PYTHONPATH:-}"

  if [[ -n "${CONDA_PREFIX:-}" && -x "$CONDA_PREFIX/bin/python" ]]; then
    PYTHONPATH="$PYTHONPATH_VAL" "$CONDA_PREFIX/bin/python" "$@"
  elif command -v mamba >/dev/null 2>&1; then
    PYTHONPATH="$PYTHONPATH_VAL" mamba run -n "$ENV_NAME" python "$@"
  elif command -v conda >/dev/null 2>&1; then
    PYTHONPATH="$PYTHONPATH_VAL" conda run -n "$ENV_NAME" python "$@"
  else
    PYTHONPATH="$PYTHONPATH_VAL" python "$@"
  fi
}

usage() {
  cat <<USAGE
Usage:
  $0 <script> [args...]
  ask | sync | last_change | - | path/to/file.py
USAGE
}

TARGET="${1:-}"; shift || true
[[ -z "$TARGET" ]] && usage && exit 1

case "$TARGET" in
  ask)         SCRIPT="$SRC_DIR/ask.py" ;;
  sync)        SCRIPT="$SRC_DIR/sync.py" ;;
  last_change) SCRIPT="$SRC_DIR/last_change.py" ;;
  -)           run_python - "$@"; exit 0 ;;
  *)
    if   [[ -f "$TARGET" ]]; then SCRIPT="$TARGET"
    elif [[ -f "$ROOT_DIR/$TARGET" ]]; then SCRIPT="$ROOT_DIR/$TARGET"
    elif [[ -f "$SRC_DIR/$TARGET" ]]; then SCRIPT="$SRC_DIR/$TARGET"
    else echo "Error: cannot find script '$TARGET'." >&2; usage; exit 1; fi
    ;;
esac

run_python "$SCRIPT" "$@"
