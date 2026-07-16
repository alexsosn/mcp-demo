# ContextFabric Corpora

The active local MCP server is `ancient-corpora`, launched by
`run-mcp-extended.sh`. It serves each Text-Fabric corpus separately. The Greek
Literature repository is a collection of many corpus directories, not one corpus.

## Installation Sources

Clone these repositories under `~/projects/mcp-demo/corpora`:

| Directory | Source repo |
|---|---|
| `corpora/cuc` | `https://github.com/DT-UCPH/cuc.git` |
| `corpora/bhsa` | `https://github.com/ETCBC/bhsa.git` |
| `corpora/lxx` | `https://github.com/CenterBLC/LXX.git` |
| `corpora/greek_literature` | `https://github.com/pthu/greek_literature.git` |
| `corpora/dss` | `https://github.com/ETCBC/dss.git` |
| `corpora/extrabiblical` | `https://github.com/ETCBC/extrabiblical.git` |
| `corpora/peshitta` | `https://github.com/ETCBC/peshitta.git` |
| `corpora/syriac` | `https://github.com/ETCBC/syriac.git` |
| `corpora/oldbabylonian` | `https://github.com/Nino-cunei/oldbabylonian.git` |
| `corpora/oldassyrian` | `https://github.com/Nino-cunei/oldassyrian.git` |

After cloning:

```bash
./.venv/bin/python build_greek_literature_catalog.py
./.venv/bin/python generate_mcp_configs.py
```

## Active MCP Corpora

| MCP name | Source repo | Text-Fabric path | Smoke result |
|---|---|---|---|
| `cuc` | `DT-UCPH/cuc` | `corpora/cuc/tf/0.2.7` | `word g_cons=aṯrt` returned 63 hits |
| `bhsa` | `ETCBC/bhsa` | `corpora/bhsa/tf/4b` | `word lex=>CRH/` returned 40 hits; morphology works |
| `lxx` | `CenterBLC/LXX` | `corpora/lxx/tf/1935` | `word` returned `ἐν`, `Gen 1:1` |
| `dss` | `ETCBC/dss` | `corpora/dss/tf/2.0` | `word` returned `ו`, `CD 1:1`; `word morpho` works |
| `extrabiblical` | `ETCBC/extrabiblical` | `corpora/extrabiblical/tf/0.2` | `word` returned `ו`, `1QH 3:1`; `word sp=verb` works |
| `peshitta` | `ETCBC/peshitta` | `corpora/peshitta/tf/0.2` | `word` returned `ܒܪܫܝܬ`, `Genesis 1:1`; no lex/morph features in this repo version |
| `syriac` | `ETCBC/syriac` | `corpora/syriac/tf/0.7` | `word` returned `ܒ`, `Genesis 1:1`; `word sp=verb` works |
| `akkadian_oldbabylonian` | `Nino-cunei/oldbabylonian` | `corpora/oldbabylonian/tf/1.0.6` | loaded: 6 node types, 64 node features; `word` count smoke-tested |
| `akkadian_oldassyrian` | `Nino-cunei/oldassyrian` | `corpora/oldassyrian/tf/0.1` | loaded: 6 node types, 64 node features; `word` count smoke-tested |
| `greek_homer_iliad` | `pthu/greek_literature` | `corpora/greek_literature/canonical-greekLit/tlg0012/tlg001/perseus-grc2/1/tf/1.0` | loaded in `check_all_mcp.py` |
| `greek_homer_odyssey` | `pthu/greek_literature` | `corpora/greek_literature/canonical-greekLit/tlg0012/tlg002/perseus-grc2/1/tf/1.0` | loaded in `check_all_mcp.py` |
| `greek_sophocles_antigone` | `pthu/greek_literature` | `corpora/greek_literature/canonical-greekLit/tlg0011/tlg002/perseus-grc2/1/tf/1.0` | loaded in `check_all_mcp.py` |
| `greek_aeschylus_agamemnon` | `pthu/greek_literature` | `corpora/greek_literature/canonical-greekLit/tlg0085/tlg005/perseus-grc2/1/tf/1.0` | loaded in `check_all_mcp.py` |
| `greek_plato_euthyphro` | `pthu/greek_literature` | `corpora/greek_literature/canonical-greekLit/tlg0059/tlg001/perseus-grc1/1/tf/1.0` | loaded in `check_all_mcp.py` |
| `greek_plato_phaedo` | `pthu/greek_literature` | `corpora/greek_literature/canonical-greekLit/tlg0059/tlg004/perseus-grc2/1/tf/1.0` | loaded in `check_all_mcp.py` |
| `greek_plato_cratylus` | `pthu/greek_literature` | `corpora/greek_literature/canonical-greekLit/tlg0059/tlg005/perseus-grc2/1/tf/1.0` | loaded in `check_all_mcp.py` |
| `greek_xenophon_hellenica` | `pthu/greek_literature` | `corpora/greek_literature/canonical-greekLit/tlg0032/tlg001/perseus-grc2/1/tf/1.0` | loaded in `check_all_mcp.py` |

## Feature Validation

Do not use a global `--features` list for the extended server. The corpus schemas
are heterogeneous, and a shared filter either hides important features or asks
some corpora to load unavailable ones.

The current extended MCP exposes these feature groups:

| Corpus | Validated features |
|---|---|
| `bhsa` | `sp`, `vt`, `vs`, `ps`, `gn`, `nu`, `st`, `pdp`, `typ`, `function`, `lex` |
| `dss` | `morpho`, `morph_etcbc`, `sp`, `ps`, `gn`, `nu`, `lex` |
| `extrabiblical` | `sp`, `vt`, `vs`, `ps`, `gn`, `nu`, `st`, `pdp`, `lex` |
| `syriac` | `sp`, `vt`, `vs`, `ps`, `gn`, `nu`, `st`, `lex` |
| `peshitta` | `book`, `chapter`, `verse`, `witness`, `word`, `word_etcbc`; no `lex` or morphology |

Observed MCP feature counts during validation:

| Corpus | MCP-loaded feature count |
|---|---:|
| `bhsa` | 97 node features, 4 edge features |
| `dss` | 74 node features, 2 edge features |
| `extrabiblical` | 64 node features, 3 edge features |
| `peshitta` | 9 node features, 0 edge features |
| `syriac` | 31 node features, 0 edge features |

BHSA is not stripped down in the current extended setup. The earlier limited
behavior came from a global feature filter used by the original CUC+BHSA demo.
The stable workshop BHSA directory is `tf/4b`; it is not the newest BHSA edition,
but it is a native ETCBC Text-Fabric dataset and supports morphological queries.

## Greek Literature Notes

`pthu/greek_literature` contains 1,779 separate Text-Fabric corpora. The catalog
is stored in `greek_literature_catalog.tsv`. Add more works in `mcp_corpora.py`,
then run:

```bash
./.venv/bin/python generate_mcp_configs.py
./.venv/bin/python check_all_mcp.py
```

Known `cfabric-mcp` edge cases from exploration:

- Herodotus created a non-reloadable cache around an `unspecified-true.tf`
  feature.
- Several Plato files have duplicate section levels.
- Some works have unusual feature filenames or section models, so additions
  should be curated and smoke-tested instead of exposing the whole repository as
  one MCP corpus.
