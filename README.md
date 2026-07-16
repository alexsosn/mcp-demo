# mcp-demo: Ancient Corpora over MCP

This repository is a reproducible, client-neutral MCP setup for the summer-school
workshop. It gives agentic IDEs live access to ancient-text corpora through local
ContextFabric and SEDRA servers, plus Sefaria through its hosted MCP endpoint.

The primary student paths are Google Antigravity IDE and ChatGPT Codex, both of
which have free tiers. Claude remains supported, but is optional.

| Source | MCP access | Status |
|---|---|---|
| CUC, Copenhagen Ugaritic Corpus | local `cfabric-mcp` | verified |
| BHSA, ETCBC Hebrew Bible | local `cfabric-mcp` | verified with morphology |
| LXX, DSS, Extrabiblical, Peshitta, Syriac | local `cfabric-mcp` | verified |
| Old Babylonian and Old Assyrian | local `cfabric-mcp` | verified |
| selected Greek Literature works | local `cfabric-mcp` | verified |
| Sefaria library | hosted MCP, proxied for Codex | verified |
| SEDRA IV Syriac lexicons | optional local Node MCP | verified |

## Quick Start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```bash
git clone https://github.com/alexsosn/mcp-demo.git
cd mcp-demo
./setup.sh
```

The setup script:

1. Creates a Python 3.13 virtual environment.
2. Installs ContextFabric, the MCP SDK, and the Sefaria transport bridge.
3. Downloads the workshop-sized CUC and BHSA corpus set.
4. Generates machine-local MCP configs for Antigravity, Codex, and Claude.
5. Verifies local corpus searches and Sefaria access.

Generated configs contain absolute paths for the current checkout, are ignored
by Git, and can be recreated after moving the repository:

```bash
./.venv/bin/python generate_mcp_configs.py
```

The generator automatically includes every corpus that is installed at one of
the paths declared in `mcp_corpora.py`.

The two-corpus quick-start profile initializes in a few seconds. The full
17-corpus profile can take one or two minutes on its first load; the generated
Codex config allows three minutes for MCP startup.

## Use with Antigravity IDE

Antigravity discovers the generated workspace configuration at:

```text
.agents/mcp_config.json
```

1. Open this repository as an Antigravity project.
2. Open **MCP Servers** from the `...` menu in the agent panel.
3. Select **Manage MCP Servers**, then refresh the installed servers.
4. Confirm `ancient-corpora` and `sefaria` are connected.
5. Ask: `Using ancient-corpora, search CUC for word g_cons=aṯrt.`

Antigravity supports the local STDIO corpus server directly. Sefaria Texts still
uses the older GET-based SSE transport, while current Antigravity initializes a
`serverUrl` with Streamable HTTP POST requests. The generated config therefore
runs `mcp-proxy` locally and presents Sefaria Texts to Antigravity as STDIO. Its
workspace configuration format is documented in the
[Antigravity MCP guide](https://antigravity.google/docs/mcp).

Do not replace the Texts endpoint with `https://developers.sefaria.org/mcp`.
That Streamable HTTP endpoint is a different MCP server for Sefaria's developer
and API documentation; it does not expose the Jewish-text tools used by this demo.

## Use with ChatGPT Codex

Codex discovers the generated project configuration at:

```text
.codex/config.toml
```

1. Open or select this repository in the Codex app, CLI, or IDE extension.
2. Trust the project when prompted; Codex ignores project config in untrusted
   repositories.
3. Open **Settings → MCP servers**, or use `/mcp` in the CLI/TUI.
4. Confirm `ancient-corpora` and `sefaria` are enabled.
5. Ask: `Use ancient-corpora to list the installed corpora.`

The Codex app, CLI, and IDE extension share the same configuration. Current
Codex supports local STDIO and remote Streamable HTTP servers, but Sefaria Texts
still uses the older SSE transport. The generated Codex config therefore runs
`mcp-proxy` locally to bridge Sefaria SSE to STDIO. See the official
[Codex MCP guide](https://learn.chatgpt.com/docs/extend/mcp).

You can inspect what Codex loaded with:

```bash
codex mcp list
```

## Optional Claude Setup

Claude remains available for instructors or students who already use it. The
generator writes:

```text
clients/claude_desktop_config.extended.generated.json
clients/claude_code_extended_setup.generated.sh
```

For Claude Desktop, merge the generated `mcpServers` object into the config
opened by **Settings → Developer → Edit Config**. For Claude Code, run the
generated setup script. Sefaria's own documentation notes that its custom
ChatGPT and Claude connector path may require a paid account; Antigravity and
local Codex use the MCP endpoint without that connector workflow.

## Client Compatibility

| Capability | Antigravity | Codex | Claude |
|---|---|---|---|
| Local ContextFabric corpora | workspace STDIO | project STDIO | local STDIO |
| Sefaria Texts MCP | SSE-to-STDIO proxy | SSE-to-STDIO proxy | custom connector or SSE |
| Local SEDRA server | workspace STDIO | project STDIO | local STDIO |
| Generated config location | `.agents/` | `.codex/` | `clients/` |

## Install the Extended Corpus Set

The quick start installs CUC and BHSA. To reproduce the full workshop profile,
clone the remaining repositories into `corpora/`:

```bash
git clone --depth 1 https://github.com/CenterBLC/LXX.git corpora/lxx
git clone --depth 1 https://github.com/pthu/greek_literature.git corpora/greek_literature
git clone --depth 1 https://github.com/ETCBC/dss.git corpora/dss
git clone --depth 1 https://github.com/ETCBC/extrabiblical.git corpora/extrabiblical
git clone --depth 1 https://github.com/ETCBC/peshitta.git corpora/peshitta
git clone --depth 1 https://github.com/ETCBC/syriac.git corpora/syriac
git clone --depth 1 https://github.com/Nino-cunei/oldbabylonian.git corpora/oldbabylonian
git clone --depth 1 https://github.com/Nino-cunei/oldassyrian.git corpora/oldassyrian
```

Expected Text-Fabric paths are listed in `corpora_manifest.md`. After cloning,
regenerate the catalog and client configs:

```bash
./.venv/bin/python build_greek_literature_catalog.py
./.venv/bin/python generate_mcp_configs.py
```

The curated Greek selection currently includes:

```text
greek_homer_iliad
greek_homer_odyssey
greek_sophocles_antigone
greek_aeschylus_agamemnon
greek_plato_euthyphro
greek_plato_phaedo
greek_plato_cratylus
greek_xenophon_hellenica
```

`pthu/greek_literature` contains many separate Text-Fabric corpora rather than
one aggregate corpus. Add or remove curated works in `mcp_corpora.py`, then
regenerate the configs.

## Optional SEDRA Lexicons

Syriac lexicon access comes from `ktmcp-cli/bethmardutho`:

```bash
mkdir -p servers
git clone https://github.com/ktmcp-cli/bethmardutho.git servers/bethmardutho
cd servers/bethmardutho
npm install
cd ../..
./.venv/bin/python generate_mcp_configs.py
```

The generator detects both the built server and the local Node executable. It
then adds `bethmardutho` to every client config. Available tools include:

```text
get__word__id_    lookup by SEDRA word id or Syriac word form
get__lexeme__id_  lookup by SEDRA lexeme id
```

Validated examples:

```text
get__word__id_ {"id": "30862"}
get__word__id_ {"id": "ܐܒܪܐ"}
get__lexeme__id_ {"id": "11820"}
```

## Feature Coverage

The generator loads each corpus without a shared global feature filter. The
schemas are heterogeneous, and a shared filter can hide BHSA morphology or ask
Greek works to load unavailable features.

Validated feature groups:

| Corpus | Feature status |
|---|---|
| `bhsa` | `sp`, `vt`, `vs`, `ps`, `gn`, `nu`, `st`, `pdp`, `typ`, `function`, `lex` |
| `dss` | `morpho`, `morph_etcbc`, `sp`, `ps`, `gn`, `nu`, `lex` |
| `extrabiblical` | ETCBC-style morphology including `sp`, `vt`, `vs`, `ps`, `gn`, `nu`, `st`, `pdp`, `lex` |
| `syriac` | morphology-style features including `sp`, `vt`, `vs`, `ps`, `gn`, `nu`, `st`, `lex` |
| `peshitta` | text, section, and witness features; no morphology in the installed version |

BHSA uses `tf/4b`, a stable native ETCBC Text-Fabric directory with working
morphological queries. Validated templates include:

```text
bhsa:          word sp=verb
bhsa:          word vt=perf
bhsa:          word ps=p1
dss:           word morpho
extrabiblical: word sp=verb
syriac:        word sp=verb
```

## Verification

Validate generated client schemas and the core MCP services with:

```bash
./.venv/bin/python generate_mcp_configs.py
./.venv/bin/python check_client_configs.py
./.venv/bin/python verify.py
```

Extended-profile checks:

```bash
./.venv/bin/python check_extended_mcp.py
./.venv/bin/python check_all_mcp.py
./.venv/bin/python check_greek_literature_mcp.py
./.venv/bin/python check_feature_exposure.py
./.venv/bin/python check_sefaria.py
./.venv/bin/python check_sedra_mcp.py
```

Observed smoke-test results include:

- CUC `word g_cons=aṯrt`: 63 hits, starting at `KTU 1.3 I:15`.
- BHSA `word lex=>CRH/`: 40 hits, starting at `Exodus 34:13`.
- LXX `word`: starts at `ἐν`, `Genesis 1:1`.
- Sefaria retrieves `Genesis 1:1` and `Deuteronomy 16:21` in Hebrew and English.
- SEDRA exposes `get__word__id_` and `get__lexeme__id_`.

First ContextFabric loads create `.cfm` caches inside downloaded corpus
directories. Sefaria keyword search is translation- and vocalization-sensitive;
for stable demonstrations, retrieve exact references with `get_text`.

The CUC heatmap can optionally enrich tablet names from a separate catalog. Put
the TSV at `data/ugaritic_texts_catalog.tsv`, or pass it explicitly:

```bash
./.venv/bin/python build_cuc_rare_word_heatmap.py --catalog path/to/catalog.tsv
```
