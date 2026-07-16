#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

VENV="$HERE/.venv"
CORPORA="$HERE/corpora"
CUC_TF="$CORPORA/cuc/tf/0.2.7"
BHSA_TF="$CORPORA/bhsa/tf/4b"

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

echo "==> Fetching corpora"
mkdir -p "$CORPORA"
if [ -d "$CORPORA/cuc/.git" ]; then
  echo "    CUC already cloned"
else
  git clone --depth 1 https://github.com/DT-UCPH/cuc.git "$CORPORA/cuc"
fi
if [ -d "$CORPORA/bhsa/.git" ]; then
  echo "    BHSA already cloned"
else
  git clone --depth 1 https://github.com/ETCBC/bhsa.git "$CORPORA/bhsa"
fi

for tf_dir in "$CUC_TF" "$BHSA_TF"; do
  if [ ! -f "$tf_dir/otype.tf" ]; then
    echo "ERROR: expected Text-Fabric data at $tf_dir"
    echo "       Available otype.tf files:"
    find "$CORPORA" -name otype.tf -print
    exit 1
  fi
done

echo "==> Writing MCP configs for Antigravity, Codex, and Claude"
"$VENV/bin/python" "$HERE/generate_mcp_configs.py"

echo "==> Verifying MCP services and transport compatibility"
"$VENV/bin/python" "$HERE/verify.py"

cat <<EOF

Setup complete.
Open this folder in Antigravity or Codex, refresh MCP servers, and try a prompt
from examples/tongues-of-fire.md. Generated client configs are machine-local.
EOF
