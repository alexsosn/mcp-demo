# mcp-demo: Ancient Corpora over MCP

This folder contains the local MCP setup used for the summer-school workshop. The
active profile serves CUC, BHSA, LXX, ETCBC corpora, and a curated selection from
`pthu/greek_literature` through one local ContextFabric MCP server. Sefaria is
used through its hosted MCP endpoint.

| Source | MCP access | Status |
|---|---|---|
| CUC, Copenhagen Ugaritic Corpus | local `cfabric-mcp` | verified |
| BHSA, ETCBC Hebrew Bible | local `cfabric-mcp` | verified with morphology |
| LXX, CenterBLC | local `cfabric-mcp` | verified |
| DSS, Extrabiblical, Peshitta, Syriac | local `cfabric-mcp` | verified |
| Akkadian, Old Babylonian and Old Assyrian | local `cfabric-mcp` | verified |
| selected Greek Literature works | local `cfabric-mcp` | verified |
| Sefaria library | hosted `https://mcp.sefaria.org/sse` | verified |
| SEDRA IV Syriac lexicons | local Beth Mardutho MCP | verified |

## Environment

Use Python 3.13. `cfabric-mcp==0.1.7` requires Python `>=3.13`; Python 3.12
fails dependency resolution. Python 3.14 was not a good target for this setup
because some dependencies and corpus tooling were not ready for it.

The verified environment is:

```bash
cd ~/projects/mcp-demo
uv venv --python 3.13 .venv
uv pip install cfabric-mcp "mcp[cli]" httpx anyio
```

## Install Corpora

Create the corpus directory and clone each upstream repository:

```bash
cd ~/projects/mcp-demo
mkdir -p corpora

git clone --depth 1 https://github.com/DT-UCPH/cuc.git corpora/cuc
git clone --depth 1 https://github.com/ETCBC/bhsa.git corpora/bhsa
git clone --depth 1 https://github.com/CenterBLC/LXX.git corpora/lxx
git clone --depth 1 https://github.com/pthu/greek_literature.git corpora/greek_literature
git clone --depth 1 https://github.com/ETCBC/dss.git corpora/dss
git clone --depth 1 https://github.com/ETCBC/extrabiblical.git corpora/extrabiblical
git clone --depth 1 https://github.com/ETCBC/peshitta.git corpora/peshitta
git clone --depth 1 https://github.com/ETCBC/syriac.git corpora/syriac
git clone --depth 1 https://github.com/Nino-cunei/oldbabylonian.git corpora/oldbabylonian
git clone --depth 1 https://github.com/Nino-cunei/oldassyrian.git corpora/oldassyrian
```

Expected Text-Fabric paths for the active profile:

```text
corpora/cuc/tf/0.2.7
corpora/bhsa/tf/4b
corpora/lxx/tf/1935
corpora/dss/tf/2.0
corpora/extrabiblical/tf/0.2
corpora/peshitta/tf/0.2
corpora/syriac/tf/0.7
corpora/oldbabylonian/tf/1.0.6
corpora/oldassyrian/tf/0.1
```

`pthu/greek_literature` is not one aggregate corpus. It contains 1,779 separate
Text-Fabric corpora. Build the catalog and serve selected works as separate MCP
corpus names:

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

Add more works in `mcp_corpora.py`, regenerate configs, and verify the result.
Some Greek Literature corpora expose Text-Fabric edge cases under
`cfabric-mcp`, including non-reloadable caches for certain `unspecified-*.tf`
features and duplicate section levels in some Plato files.

## Run

Use the extended launcher for the current setup:

```bash
cd ~/projects/mcp-demo
./run-mcp-extended.sh
```

The launcher serves 17 corpora and intentionally has no global `--features`
filter. Do not add one: these corpora do not share one feature schema, and a
global filter can hide BHSA morphology or break Greek works that lack requested
features.

The older `./run-mcp.sh` and `./setup.sh` are the original minimal CUC+BHSA
profile. They are useful for a small smoke test, but not for the full current
Claude Desktop setup.

Sefaria is not run locally here. Use the hosted Texts MCP endpoint:

```text
https://mcp.sefaria.org/sse
```

## SEDRA Lexicons

Syriac lexicon access is provided by the Beth Mardutho SEDRA MCP server from
`ktmcp-cli/bethmardutho`. It is installed locally at:

```text
servers/bethmardutho
```

Install or refresh it with:

```bash
mkdir -p servers
git clone https://github.com/ktmcp-cli/bethmardutho.git servers/bethmardutho
cd servers/bethmardutho
npm install
```

The server is a Node stdio MCP server. It exposes two tools:

```text
get__word__id_    lookup by SEDRA word id or Syriac word form
get__lexeme__id_  lookup by SEDRA lexeme id
```

The active Claude Desktop config runs it as:

```json
{
  "bethmardutho": {
    "command": "/usr/local/bin/node",
    "args": [
      "/Users/alexandersosnovschenko/projects/mcp-demo/servers/bethmardutho/dist/index.js"
    ]
  }
}
```

Validated examples:

```text
get__word__id_ {"id": "30862"}
get__word__id_ {"id": "ܐܒܪܐ"}
get__lexeme__id_ {"id": "11820"}
```

## Client Config

Generated files:

```text
clients/claude_desktop_config.extended.generated.json
clients/claude_code_extended_setup.generated.sh
```

For Claude Desktop, merge the generated `mcpServers.ancient-corpora` block into:

```text
/Users/alexandersosnovschenko/Library/Application Support/Claude/claude_desktop_config.json
```

The active Claude Desktop config has already been refreshed from the generated
extended config. It points at:

```text
/Users/alexandersosnovschenko/projects/mcp-demo/.venv/bin/cfabric-mcp
```

and configures all 17 corpora with no `--features` filter. Fully restart Claude
Desktop after changing this file so it starts a fresh MCP process.

For Claude Code:

```bash
./clients/claude_code_extended_setup.generated.sh
claude mcp list
```

## Feature Coverage

The current setup is not the earlier stripped-down feature profile. The extended
launcher loads each corpus without a shared feature filter.

Validated through `check_feature_exposure.py`:

| Corpus | Feature status |
|---|---|
| `bhsa` | exposes morphology/syntax features including `sp`, `vt`, `vs`, `ps`, `gn`, `nu`, `st`, `pdp`, `typ`, `function`, `lex` |
| `dss` | exposes `morpho`, `morph_etcbc`, `sp`, `ps`, `gn`, `nu`, `lex` |
| `extrabiblical` | exposes ETCBC-style morphology features including `sp`, `vt`, `vs`, `ps`, `gn`, `nu`, `st`, `pdp`, `lex` |
| `syriac` | exposes morphology-style features including `sp`, `vt`, `vs`, `ps`, `gn`, `nu`, `st`, `lex` |
| `peshitta` | text/section/witness only in the installed repo version; no `lex` or morphology |

BHSA currently uses `tf/4b`, not the newest `tf/c` or `tf/2021`. It is still a
native ETCBC Text-Fabric directory and supports morphological queries through
MCP. `tf/2021` loaded too slowly during setup, so `tf/4b` is the stable workshop
choice.

Validated query examples:

```text
bhsa:          word sp=verb
bhsa:          word vt=perf
bhsa:          word ps=p1
dss:           word morpho
extrabiblical: word sp=verb
syriac:        word sp=verb
```

## Verification

Run these checks after installing or changing corpus selections:

```bash
./.venv/bin/python check_extended_mcp.py
./.venv/bin/python check_all_mcp.py
./.venv/bin/python check_greek_literature_mcp.py
./.venv/bin/python check_feature_exposure.py
./.venv/bin/python check_sefaria.py
./.venv/bin/python check_sedra_mcp.py
./.venv/bin/python check_sedra_config_mcp.py
```

Observed smoke-test results:

- ContextFabric lists all 17 local corpora from `run-mcp-extended.sh`.
- CUC query `word g_cons=aṯrt` returns 63 hits, starting at `KTU 1.3 I:15`.
- BHSA query `word lex=>CRH/` returns 40 hits, starting at `Exodus 34:13`.
- BHSA morphology queries such as `word sp=verb` and `word vt=perf` work.
- LXX query `word` starts at `ἐν`, `Genesis 1:1`.
- Sefaria lists `get_text`, `text_search`, `search_in_book`, and related tools.
- Sefaria `get_text` retrieves `Genesis 1:1` and `Deuteronomy 16:21` in Hebrew
  and English.
- Beth Mardutho SEDRA lists `get__word__id_` and `get__lexeme__id_`.
- SEDRA `get__word__id_ {"id": "ܐܒܪܐ"}` returns lexicon entries and English
  glosses including `lead.` and `feather`.

## Notes

- First ContextFabric loads create `.cfm` caches inside the corpus TF
  directories.
- CUC word-form searches use `g_cons`, for example `word g_cons=aṯrt`.
- BHSA lexeme searches use `lex`, for example `word lex=>CRH/`.
- BHSA morphology searches use features such as `sp`, `vt`, `vs`, `ps`, `gn`,
  `nu`, and `st`.
- Sefaria keyword search is translation- and vocalization-sensitive; for stable
  demos, retrieve exact references with `get_text`.
