#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

VENV="$HERE/.venv"
PROFILE="workshop"

if [ "$#" -gt 1 ]; then
  echo "ERROR: expected at most one option"
  echo "Usage: ./setup.sh [--minimal]"
  exit 2
fi

case "${1:-}" in
  "") ;;
  --minimal) PROFILE="minimal" ;;
  --help|-h)
    echo "Usage: ./setup.sh [--minimal]"
    echo "  default: install CUC, BHSA, and the curated Greek workshop corpora"
    echo "  --minimal: install only CUC and BHSA"
    exit 0
    ;;
  *)
    echo "ERROR: unknown option: $1"
    echo "Usage: ./setup.sh [--minimal]"
    exit 2
    ;;
esac

echo "==> mcp-demo setup in: $HERE"

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is required for this setup. Install uv, then rerun ./setup.sh."
  exit 1
fi

echo "3.13" > "$HERE/.python-version"

echo "==> Creating Python 3.13 virtual environment"
uv venv --python 3.13 "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "==> Installing MCP packages"
uv pip install "cfabric-mcp==0.1.7" "mcp[cli]" "mcp-proxy==0.12.0" httpx anyio

echo "==> Fetching the $PROFILE corpus profile"
"$VENV/bin/python" "$HERE/install_corpora.py" --profile "$PROFILE"

echo "==> Writing MCP configs for Antigravity, Codex, and Claude"
"$VENV/bin/python" "$HERE/generate_mcp_configs.py"

echo "==> Verifying MCP services and transport compatibility"
"$VENV/bin/python" "$HERE/verify.py"

cat <<EOF

Setup complete.
Open this folder in Antigravity or Codex, refresh MCP servers, and try a prompt
from examples/tongues-of-fire.md. The default profile also includes the curated
Greek workshop corpora. Generated client configs are machine-local.
EOF
