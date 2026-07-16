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
uv pip install cfabric-mcp "mcp[cli]" httpx anyio

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

echo "==> Writing local launcher"
cat > "$HERE/run-mcp.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$HERE"
exec "$VENV/bin/cfabric-mcp" \\
  --corpus cuc="$CUC_TF" \\
  --corpus bhsa="$BHSA_TF" \\
  --features "g_cons g_word_utf8 lex book chapter verse language line tablet"
EOF
chmod +x "$HERE/run-mcp.sh"

echo "==> Writing client config examples"
mkdir -p "$HERE/clients"
cat > "$HERE/clients/claude_desktop_config.generated.json" <<EOF
{
  "mcpServers": {
    "cuc-bhsa": {
      "command": "$VENV/bin/cfabric-mcp",
      "args": [
        "--corpus", "cuc=$CUC_TF",
        "--corpus", "bhsa=$BHSA_TF",
        "--features", "g_cons g_word_utf8 lex book chapter verse language line tablet"
      ]
    }
  }
}
EOF

cat > "$HERE/clients/claude_code_setup.generated.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
claude mcp add cuc-bhsa -- "$VENV/bin/cfabric-mcp" \\
  --corpus cuc="$CUC_TF" \\
  --corpus bhsa="$BHSA_TF" \\
  --features "g_cons g_word_utf8 lex book chapter verse language line tablet"
claude mcp add --transport sse sefaria https://mcp.sefaria.org/sse
claude mcp list
EOF
chmod +x "$HERE/clients/claude_code_setup.generated.sh"

echo "==> Verifying through MCP clients"
"$VENV/bin/python" "$HERE/verify.py"

cat <<EOF

Setup complete.
Run ./run-mcp.sh to keep the local CUC+BHSA ContextFabric MCP server open,
or use one of the generated client configs in ./clients/.
Sefaria Texts MCP is hosted at https://mcp.sefaria.org/sse.
EOF
