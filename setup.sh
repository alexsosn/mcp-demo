#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

VENV="$HERE/.venv"
PROFILE="workshop"
INSTALL_ANTIGRAVITY_GLOBAL=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --minimal) PROFILE="minimal" ;;
    --antigravity-global) INSTALL_ANTIGRAVITY_GLOBAL=1 ;;
    --help|-h)
      echo "Usage: ./setup.sh [--minimal] [--antigravity-global]"
      echo "  default: install CUC, BHSA, and the curated Greek workshop corpora"
      echo "  --minimal: install only CUC and BHSA"
      echo "  --antigravity-global: merge project servers into Antigravity's global config"
      exit 0
      ;;
    *)
      echo "ERROR: unknown option: $1"
      echo "Usage: ./setup.sh [--minimal] [--antigravity-global]"
      exit 2
      ;;
  esac
  shift
done

echo "==> mcp-demo setup in: $HERE"

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is required for this setup. Install uv, then rerun ./setup.sh."
  exit 1
fi

echo "3.13" > "$HERE/.python-version"

if [ -x "$VENV/bin/python" ] && "$VENV/bin/python" -c \
  'import sys; raise SystemExit(sys.version_info[:2] != (3, 13))'; then
  echo "==> Reusing existing Python 3.13 virtual environment"
else
  echo "==> Creating Python 3.13 virtual environment"
  if [ -e "$VENV" ]; then
    uv venv --clear --python 3.13 "$VENV"
  else
    uv venv --python 3.13 "$VENV"
  fi
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "==> Installing MCP packages"
uv pip install "cfabric-mcp==0.1.7" "mcp[cli]" "mcp-proxy==0.12.0" httpx anyio

echo "==> Fetching the $PROFILE corpus profile"
"$VENV/bin/python" "$HERE/install_corpora.py" --profile "$PROFILE"

echo "==> Writing MCP configs for Antigravity, Codex, and Claude"
"$VENV/bin/python" "$HERE/generate_mcp_configs.py"

if [ "$INSTALL_ANTIGRAVITY_GLOBAL" -eq 1 ]; then
  echo "==> Merging project servers into Antigravity's global MCP config"
  "$VENV/bin/python" "$HERE/install_antigravity_config.py"
fi

echo "==> Verifying MCP services and transport compatibility"
"$VENV/bin/python" "$HERE/verify.py"

if [ "$PROFILE" = "workshop" ]; then
  PROFILE_NOTE="The workshop profile includes the curated Greek corpora."
else
  PROFILE_NOTE="The minimal profile installs CUC and BHSA only."
fi

cat <<EOF

Setup complete.
Open this folder in Antigravity or Codex, refresh MCP servers, and try a prompt
from examples/tongues-of-fire.md. $PROFILE_NOTE Generated client configs are
machine-local.
EOF
