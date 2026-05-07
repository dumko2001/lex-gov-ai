#!/bin/bash
# Source this file before running project commands to keep caches/temp on external drive.

set -euo pipefail

if [ -n "${BASH_VERSION:-}" ]; then
  SCRIPT_PATH="${BASH_SOURCE[0]}"
elif [ -n "${ZSH_VERSION:-}" ]; then
  SCRIPT_PATH="${(%):-%N}"
else
  SCRIPT_PATH="$0"
fi

ROOT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
CACHE_ROOT="$ROOT_DIR/.external-cache"
TMP_ROOT="$ROOT_DIR/.external-tmp"

mkdir -p "$CACHE_ROOT" "$TMP_ROOT"
mkdir -p \
  "$CACHE_ROOT/pip" \
  "$CACHE_ROOT/npm" \
  "$CACHE_ROOT/pycache" \
  "$CACHE_ROOT/huggingface" \
  "$CACHE_ROOT/torch" \
  "$CACHE_ROOT/matplotlib" \
  "$CACHE_ROOT/xdg"

export TMPDIR="$TMP_ROOT"
export PIP_CACHE_DIR="$CACHE_ROOT/pip"
export npm_config_cache="$CACHE_ROOT/npm"
export PYTHONPYCACHEPREFIX="$CACHE_ROOT/pycache"
export HF_HOME="$CACHE_ROOT/huggingface"
export TRANSFORMERS_CACHE="$CACHE_ROOT/huggingface/transformers"
export TORCH_HOME="$CACHE_ROOT/torch"
export MPLCONFIGDIR="$CACHE_ROOT/matplotlib"
export XDG_CACHE_HOME="$CACHE_ROOT/xdg"

echo "External env active"
echo "  ROOT_DIR=$ROOT_DIR"
echo "  CACHE_ROOT=$CACHE_ROOT"
echo "  TMPDIR=$TMPDIR"
