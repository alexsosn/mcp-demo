from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TF_DIR = ROOT / "corpora" / "cuc" / "tf" / "0.2.7"
PARSING_DIR = ROOT / "corpora" / "cuc" / "auto_parsing" / "0.2.7"
CATALOG_PATH = Path(
    "/Users/alexandersosnovschenko/projects/summer_school_2026/"
    "Antiquity Studies Summer School/data/ugaritic_texts_catalog.tsv"
)
OUT_DIR = ROOT / "out"
OUT_HTML = OUT_DIR / "cuc_rare_word_heatmap.html"
OUT_JSON = OUT_DIR / "cuc_rare_word_heatmap_data.json"

SIGN_FIRST = 1
SIGN_LAST = 117_594
COLUMN_FIRST = 117_595
COLUMN_LAST = 117_928
TABLET_FIRST = 125_545
TABLET_LAST = 125_823
WORD_FIRST = 125_824
WORD_LAST = 153_284

THRESHOLDS = (1, 2, 5, 10)
DEFAULT_THRESHOLD = 5
MODES = {
    "all": {
        "label": "All words",
        "description": "All word tokens counted",
        "excludeBroken": False,
        "excludeUncertain": False,
    },
    "noBroken": {
        "label": "No broken words",
        "description": "Words with x-signs or restored/missing signs excluded",
        "excludeBroken": True,
        "excludeUncertain": False,
    },
    "noUncertain": {
        "label": "No uncertain letters",
        "description": "Words with visible uncertain letters excluded",
        "excludeBroken": False,
        "excludeUncertain": True,
    },
    "cleanOnly": {
        "label": "No broken or uncertain",
        "description": "Broken/restored/missing words and uncertain letters excluded",
        "excludeBroken": True,
        "excludeUncertain": True,
    },
}
DEFAULT_MODE = "all"


def data_lines(path: Path):
    data_started = False
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("@"):
                continue
            if not data_started and line == "":
                continue
            data_started = True
            yield line


def parse_node_feature(path: Path) -> dict[int, str]:
    values: dict[int, str] = {}
    current_node = 1
    for line in data_lines(path):
        if "\t" in line:
            left, value = line.split("\t", 1)
            if "-" in left:
                start_s, end_s = left.split("-", 1)
                start, end = int(start_s), int(end_s)
                for node in range(start, end + 1):
                    values[node] = value
                current_node = end + 1
            else:
                current_node = int(left)
                values[current_node] = value
                current_node += 1
        else:
            values[current_node] = line
            current_node += 1
    return values


def expand_slots(spec: str) -> list[int]:
    slots: list[int] = []
    for part in spec.split(","):
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            slots.extend(range(int(start_s), int(end_s) + 1))
        else:
            slots.append(int(part))
    return slots


def parse_oslots(path: Path) -> dict[int, list[int]]:
    edges: dict[int, list[int]] = {}
    current_node = None
    for line in data_lines(path):
        if "\t" in line:
            left, spec = line.split("\t", 1)
            current_node = int(left)
        else:
            if current_node is None:
                raise ValueError(f"Missing starting node in {path}")
            current_node += 1
            spec = line
        edges[current_node] = expand_slots(spec)
    return edges


def load_catalog_titles() -> dict[str, str]:
    titles: dict[str, str] = {}
    if not CATALOG_PATH.exists():
        return titles
    with CATALOG_PATH.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            title = (row.get("text_descriptive_title") or "").strip()
            note = row.get("text_or_publication_number_note") or ""
            if not title:
                continue
            for match in re.finditer(r"\bKTU\s+(\d+\.\d+)\b", note):
                titles[f"KTU {match.group(1)}"] = title
    return titles


def load_parsing_rows() -> dict[int, dict]:
    rows_by_id: dict[int, list[dict]] = defaultdict(list)
    for path in sorted(PARSING_DIR.glob("*.tsv")):
        lines = (line for line in path.open(encoding="utf-8") if not line.startswith("#"))
        reader = csv.DictReader(lines, delimiter="\t")
        for row in reader:
            node = row.get("id", "")
            if node.isdigit():
                rows_by_id[int(node)].append(row)

    result: dict[int, dict] = {}
    for node, rows in rows_by_id.items():
        first = rows[0]
        lex_key = ""
        for field in ("DULAT", "morphological parsing", "surface form"):
            lex_key = (first.get(field) or "").strip()
            if lex_key:
                break
        glosses = []
        for row in rows:
            gloss = (row.get("gloss") or "").strip()
            if gloss and gloss not in glosses:
                glosses.append(gloss)
        result[node] = {
            "surface": (first.get("surface form") or "").strip(),
            "lexKey": lex_key,
            "gloss": "; ".join(glosses[:3]),
        }
    return result


def tablet_sort_key(name: str) -> tuple:
    nums = tuple(int(part) for part in re.findall(r"\d+", name))
    return nums or (9999, name)


def word_flags(
    slots: list[int],
    *,
    sign: dict[int, str],
    cert: dict[int, str],
    emen: dict[int, str],
) -> tuple[bool, bool]:
    has_broken = any(
        sign.get(slot) == "x" or emen.get(slot) in {"restored", "missing"}
        for slot in slots
    )
    has_uncertain = any(
        cert.get(slot) == "False"
        and bool(sign.get(slot, "").strip())
        and sign.get(slot) != "x"
        and emen.get(slot) not in {"restored", "missing"}
        for slot in slots
    )
    return has_broken, has_uncertain


def column_metric(
    word_nodes: list[int],
    *,
    mode: dict,
    word_meta: dict[int, dict],
    lex_freq: Counter,
    has_broken: dict[int, bool],
    has_uncertain: dict[int, bool],
) -> dict:
    counted = [
        node
        for node in word_nodes
        if not (mode["excludeBroken"] and has_broken[node])
        and not (mode["excludeUncertain"] and has_uncertain[node])
    ]
    total = len(counted)
    rare_counts = {
        threshold: sum(1 for node in counted if lex_freq[word_meta[node]["lexKey"]] <= threshold)
        for threshold in THRESHOLDS
    }
    rare_lexemes: dict[str, dict] = {}
    for node in counted:
        meta = word_meta[node]
        lex_key = meta["lexKey"]
        freq = lex_freq[lex_key]
        if freq > max(THRESHOLDS):
            continue
        if lex_key not in rare_lexemes:
            rare_lexemes[lex_key] = {
                "form": meta["surface"],
                "lexKey": lex_key,
                "gloss": meta["gloss"],
                "freq": freq,
                "columnCount": 0,
            }
        rare_lexemes[lex_key]["columnCount"] += 1
    rare_words = sorted(
        rare_lexemes.values(),
        key=lambda item: (item["freq"], item["lexKey"], item["form"]),
    )
    rates = {
        str(threshold): round((rare_counts[threshold] / total) * 1000, 3)
        if total
        else 0
        for threshold in THRESHOLDS
    }
    return {
        "totalWords": total,
        "rareCounts": {str(k): v for k, v in rare_counts.items()},
        "rates": rates,
        "rareWords": rare_words,
    }


def build_data() -> dict:
    oslots = parse_oslots(TF_DIR / "oslots.tf")
    tablet_feature = parse_node_feature(TF_DIR / "tablet.tf")
    column_feature = parse_node_feature(TF_DIR / "column.tf")
    g_cons = parse_node_feature(TF_DIR / "g_cons.tf")
    sign = parse_node_feature(TF_DIR / "sign.tf")
    cert = parse_node_feature(TF_DIR / "cert.tf")
    emen = parse_node_feature(TF_DIR / "emen.tf")
    title_by_tablet = load_catalog_titles()
    parsing = load_parsing_rows()

    sign_to_tablet: dict[int, int] = {}
    for tablet_node in range(TABLET_FIRST, TABLET_LAST + 1):
        for slot in oslots[tablet_node]:
            sign_to_tablet[slot] = tablet_node

    sign_to_column: dict[int, int] = {}
    for column_node in range(COLUMN_FIRST, COLUMN_LAST + 1):
        for slot in oslots[column_node]:
            sign_to_column[slot] = column_node

    columns_by_tablet_node: dict[int, list[int]] = defaultdict(list)
    for column_node in range(COLUMN_FIRST, COLUMN_LAST + 1):
        slots = oslots[column_node]
        if not slots:
            continue
        tablet_node = sign_to_tablet.get(slots[0])
        if tablet_node is not None:
            columns_by_tablet_node[tablet_node].append(column_node)

    word_meta: dict[int, dict] = {}
    words_by_column: dict[int, list[int]] = defaultdict(list)
    has_broken: dict[int, bool] = {}
    has_uncertain: dict[int, bool] = {}
    for word_node in range(WORD_FIRST, WORD_LAST + 1):
        slots = oslots[word_node]
        column_node = sign_to_column.get(slots[0])
        if column_node is None:
            continue
        parsed = parsing.get(word_node, {})
        surface = parsed.get("surface") or g_cons.get(word_node, "")
        lex_key = parsed.get("lexKey") or g_cons.get(word_node, "") or surface or f"word-{word_node}"
        word_meta[word_node] = {
            "surface": surface,
            "lexKey": lex_key,
            "gloss": parsed.get("gloss", ""),
        }
        broken, uncertain = word_flags(slots, sign=sign, cert=cert, emen=emen)
        has_broken[word_node] = broken
        has_uncertain[word_node] = uncertain
        words_by_column[column_node].append(word_node)

    lex_freq = Counter(meta["lexKey"] for meta in word_meta.values())

    tablet_nodes = sorted(
        range(TABLET_FIRST, TABLET_LAST + 1),
        key=lambda node: tablet_sort_key(tablet_feature[node]),
    )
    tablets = []
    columns: dict[str, list[dict]] = {}
    all_rates_by_mode: dict[str, dict[int, list[float]]] = {
        mode: {threshold: [] for threshold in THRESHOLDS} for mode in MODES
    }

    for tablet_node in tablet_nodes:
        tablet = tablet_feature[tablet_node]
        title = title_by_tablet.get(tablet, "")
        label = f"{tablet} - {title}" if title else tablet
        tablets.append({"id": tablet, "label": label, "title": title})
        rows = []
        for ordinal, column_node in enumerate(columns_by_tablet_node[tablet_node], start=1):
            modes = {}
            for mode_name, mode_config in MODES.items():
                metric = column_metric(
                    words_by_column[column_node],
                    mode=mode_config,
                    word_meta=word_meta,
                    lex_freq=lex_freq,
                    has_broken=has_broken,
                    has_uncertain=has_uncertain,
                )
                modes[mode_name] = metric
                for threshold in THRESHOLDS:
                    all_rates_by_mode[mode_name][threshold].append(metric["rates"][str(threshold)])
            rows.append(
                {
                    "tablet": tablet,
                    "tabletLabel": label,
                    "column": column_feature[column_node],
                    "ordinal": ordinal,
                    "label": f"{tablet} {column_feature[column_node]}",
                    "modes": modes,
                }
            )
        columns[tablet] = rows

    max_columns = max((len(rows) for rows in columns.values()), default=0)
    return {
        "meta": {
            "corpus": "CUC 0.2.7",
            "metric": "rare lexical tokens per 1,000 column words",
            "defaultMode": DEFAULT_MODE,
            "modes": MODES,
            "defaultThreshold": DEFAULT_THRESHOLD,
            "thresholds": list(THRESHOLDS),
            "tabletCount": len(tablets),
            "columnCount": sum(len(rows) for rows in columns.values()),
            "wordCount": len(word_meta),
            "brokenWordCount": sum(has_broken.values()),
            "uncertainWordCount": sum(has_uncertain.values()),
            "maxColumns": max_columns,
            "maxRateByMode": {
                mode: {
                    str(threshold): max(values) if values else 0
                    for threshold, values in thresholds.items()
                }
                for mode, thresholds in all_rates_by_mode.items()
            },
        },
        "tablets": tablets,
        "columns": columns,
    }


def build_html(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CUC Dark Corners: Rare Words by Tablet Column</title>
<style>
:root {{
  color-scheme: dark;
  --bg: #0e1116;
  --panel: #151a21;
  --panel-2: #1c222b;
  --ink: #e8edf2;
  --muted: #9aa7b5;
  --grid: #2b3440;
  --accent: #22a699;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font: 14px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
main {{ width: min(1480px, calc(100vw - 32px)); margin: 24px auto 40px; }}
.topbar {{ display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; margin-bottom: 14px; }}
h1 {{ margin: 0 0 4px; font-size: 24px; font-weight: 700; letter-spacing: 0; }}
.sub {{ margin: 0; color: var(--muted); }}
.controls {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }}
.segmented {{ display: inline-grid; grid-auto-flow: column; border: 1px solid var(--grid); border-radius: 8px; overflow: hidden; background: var(--panel); }}
.segmented button {{ border: 0; border-right: 1px solid var(--grid); background: transparent; color: var(--ink); min-width: 46px; height: 34px; padding: 0 12px; font: inherit; cursor: pointer; }}
.segmented button:last-child {{ border-right: 0; }}
.segmented button[aria-pressed="true"] {{ background: var(--accent); color: #fff; font-weight: 650; }}
.switch-control {{ display: inline-flex; align-items: center; gap: 8px; color: var(--ink); cursor: pointer; user-select: none; white-space: nowrap; }}
.switch-control input {{ position: absolute; opacity: 0; pointer-events: none; }}
.switch-track {{ position: relative; width: 44px; height: 24px; border: 1px solid var(--grid); border-radius: 999px; background: #293240; transition: background 120ms ease; }}
.switch-track::after {{ content: ""; position: absolute; top: 2px; left: 2px; width: 18px; height: 18px; border-radius: 999px; background: #fff; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.24); transition: transform 120ms ease; }}
.switch-control input:checked + .switch-track {{ background: var(--accent); border-color: var(--accent); }}
.switch-control input:checked + .switch-track::after {{ transform: translateX(20px); }}
.switch-control input:focus-visible + .switch-track {{ outline: 2px solid #f8fafc; outline-offset: 2px; }}
.legend {{ display: flex; align-items: center; gap: 8px; color: var(--muted); white-space: nowrap; }}
.ramp {{ width: 160px; height: 12px; border-radius: 999px; border: 1px solid var(--grid); background: linear-gradient(90deg, #16251f, #255f4e, #22a699, #f59e0b, #f97316); }}
.viz-wrap {{ background: var(--panel); border: 1px solid var(--grid); border-radius: 8px; padding: 14px; overflow: auto; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.28); max-height: 72vh; }}
svg {{ display: block; min-width: 760px; }}
.axis-label {{ fill: var(--muted); font-size: 11px; }}
.tablet-label {{ fill: var(--ink); font-size: 10.5px; }}
.cell {{ stroke: rgba(14, 17, 22, 0.82); stroke-width: 1; }}
.cell:focus {{ outline: none; stroke: #f8fafc; stroke-width: 2; }}
.cell.selected {{ stroke: #f8fafc; stroke-width: 2; }}
.details-panel {{ display: grid; grid-template-columns: minmax(240px, 340px) 1fr; gap: 14px; background: var(--panel); border: 1px solid var(--grid); border-radius: 8px; margin-top: 12px; min-height: 170px; overflow: hidden; }}
.details-summary {{ border-right: 1px solid var(--grid); padding: 14px; }}
.details-summary h2 {{ margin: 0 0 8px; font-size: 18px; line-height: 1.2; }}
.details-summary p {{ margin: 0 0 5px; color: var(--muted); }}
.word-list {{ overflow: auto; max-height: 380px; }}
.word-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
.word-table th, .word-table td {{ border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }}
.word-table th {{ position: sticky; top: 0; z-index: 1; background: var(--panel-2); color: var(--muted); font-size: 12px; font-weight: 650; }}
.word-table td {{ font-size: 13px; }}
.word-table .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.empty-detail {{ display: flex; align-items: center; min-height: 170px; color: var(--muted); padding: 18px; }}
.stats {{ display: grid; grid-template-columns: repeat(5, minmax(140px, 1fr)); gap: 10px; margin-top: 12px; }}
.stat {{ background: var(--panel); border: 1px solid var(--grid); border-radius: 8px; padding: 10px 12px; }}
.stat b {{ display: block; font-size: 18px; }}
.stat span {{ color: var(--muted); font-size: 12px; }}
.tooltip {{ position: fixed; z-index: 10; pointer-events: none; opacity: 0; transform: translate(-50%, -110%); background: #05070a; color: #fff; border-radius: 6px; padding: 8px 10px; min-width: 230px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.22); transition: opacity 80ms ease; }}
.tooltip b {{ display: block; margin-bottom: 3px; }}
.tooltip span {{ display: block; color: #cbd5e1; font-size: 12px; }}
@media (max-width: 760px) {{
  main {{ width: min(100vw - 20px, 1480px); margin-top: 14px; }}
  .topbar {{ align-items: flex-start; flex-direction: column; }}
  .controls {{ justify-content: flex-start; }}
  .details-panel {{ grid-template-columns: 1fr; }}
  .details-summary {{ border-right: 0; border-bottom: 1px solid var(--grid); }}
  .stats {{ grid-template-columns: 1fr 1fr; }}
}}
</style>
</head>
<body>
<main>
  <div class="topbar">
    <div>
      <h1>CUC Dark Corners: Rare Words by Tablet Column</h1>
      <p class="sub">CUC 0.2.7; tablets as books, columns as chapters; normalized per 1,000 column words.</p>
    </div>
    <div class="controls">
      <label class="switch-control">
        <input type="checkbox" id="brokenToggle">
        <span class="switch-track" aria-hidden="true"></span>
        <span>Exclude broken words</span>
      </label>
      <label class="switch-control">
        <input type="checkbox" id="uncertainToggle">
        <span class="switch-track" aria-hidden="true"></span>
        <span>Exclude uncertain letters</span>
      </label>
      <span class="legend">Rare if global lexeme frequency <=</span>
      <div class="segmented" id="thresholds" aria-label="Rare word threshold"></div>
      <span class="legend"><span>low</span><span class="ramp" aria-hidden="true"></span><span>high</span></span>
    </div>
  </div>
  <div class="viz-wrap">
    <svg id="heatmap" role="img" aria-label="Heatmap of rare Ugaritic words by tablet column"></svg>
  </div>
  <section class="details-panel" aria-live="polite">
    <div class="details-summary" id="detailsSummary">
      <h2>Click a column</h2>
      <p>Select any heatmap cell to see its rare lexical items sorted from rarest to least rare.</p>
    </div>
    <div class="word-list" id="wordList">
      <div class="empty-detail">Rare-word details will appear here.</div>
    </div>
  </section>
  <div class="stats">
    <div class="stat"><b id="tabletCount"></b><span>tablets</span></div>
    <div class="stat"><b id="columnCount"></b><span>columns</span></div>
    <div class="stat"><b id="maxRate"></b><span>highest rate per 1,000 words</span></div>
    <div class="stat"><b id="meanRate"></b><span>mean rate per 1,000 words</span></div>
    <div class="stat"><b id="selectedMode"></b><span>counting mode</span></div>
  </div>
</main>
<div class="tooltip" id="tooltip"></div>
<script>
const DATA = {payload};
const svg = document.getElementById("heatmap");
const tooltip = document.getElementById("tooltip");
const brokenToggle = document.getElementById("brokenToggle");
const uncertainToggle = document.getElementById("uncertainToggle");
const thresholdButtons = document.getElementById("thresholds");
const detailsSummary = document.getElementById("detailsSummary");
const wordList = document.getElementById("wordList");
const margin = {{ left: 360, top: 30, right: 18, bottom: 20 }};
const cellW = 24;
const cellH = 12;
const gap = 2;
let activeMode = DATA.meta.defaultMode;
let threshold = String(DATA.meta.defaultThreshold);
let selectedColumn = null;

function escapeHtml(value) {{
  return String(value ?? "").replace(/[&<>"']/g, char => ({{
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }}[char]));
}}
function lerp(a, b, t) {{ return a + (b - a) * t; }}
function hexToRgb(hex) {{
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}}
function rgbToHex(rgb) {{
  return "#" + rgb.map(v => Math.round(v).toString(16).padStart(2, "0")).join("");
}}
function interpolate(c1, c2, t) {{
  const a = hexToRgb(c1), b = hexToRgb(c2);
  return rgbToHex([lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)]);
}}
function colorFor(value, max) {{
  if (!value) return "#16251f";
  const t = Math.max(0, Math.min(1, value / max));
  const stops = [
    [0.00, "#16251f"],
    [0.28, "#255f4e"],
    [0.55, "#22a699"],
    [0.78, "#f59e0b"],
    [1.00, "#f97316"],
  ];
  for (let i = 1; i < stops.length; i++) {{
    if (t <= stops[i][0]) {{
      const [p0, c0] = stops[i - 1];
      const [p1, c1] = stops[i];
      return interpolate(c0, c1, (t - p0) / (p1 - p0));
    }}
  }}
  return stops[stops.length - 1][1];
}}
function allColumns() {{
  return DATA.tablets.flatMap(tablet => DATA.columns[tablet.id]);
}}
function metricFor(column) {{
  return column.modes?.[activeMode] ?? column;
}}
function modeLabel() {{
  return DATA.meta.modes[activeMode]?.label ?? activeMode;
}}
function modeFromToggles() {{
  if (brokenToggle.checked && uncertainToggle.checked) return "cleanOnly";
  if (brokenToggle.checked) return "noBroken";
  if (uncertainToggle.checked) return "noUncertain";
  return "all";
}}
function setStats() {{
  const columns = allColumns();
  const rates = columns.map(d => metricFor(d).rates[threshold]);
  const max = Math.max(...rates);
  const mean = rates.reduce((a, b) => a + b, 0) / rates.length;
  document.getElementById("tabletCount").textContent = DATA.meta.tabletCount.toLocaleString();
  document.getElementById("columnCount").textContent = DATA.meta.columnCount.toLocaleString();
  document.getElementById("maxRate").textContent = max.toFixed(1);
  document.getElementById("meanRate").textContent = mean.toFixed(1);
  document.getElementById("selectedMode").textContent = modeLabel();
}}
function setupModeToggles() {{
  brokenToggle.checked = DATA.meta.modes[activeMode]?.excludeBroken ?? false;
  uncertainToggle.checked = DATA.meta.modes[activeMode]?.excludeUncertain ?? false;
  const updateMode = () => {{
    activeMode = modeFromToggles();
    render();
    renderDetails();
  }};
  brokenToggle.addEventListener("change", updateMode);
  uncertainToggle.addEventListener("change", updateMode);
}}
function renderThresholdButtons() {{
  thresholdButtons.innerHTML = "";
  for (const item of DATA.meta.thresholds) {{
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = item;
    button.setAttribute("aria-pressed", String(String(item) === threshold));
    button.addEventListener("click", () => {{
      threshold = String(item);
      renderThresholdButtons();
      render();
      renderDetails();
    }});
    thresholdButtons.appendChild(button);
  }}
}}
function showTip(event, d) {{
  const metric = metricFor(d);
  tooltip.innerHTML = `<b>${{escapeHtml(d.tabletLabel)}}<br>${{escapeHtml(d.column)}}</b>
    <span>${{modeLabel()}}</span>
    <span>${{metric.rareCounts[threshold]}} rare tokens / ${{metric.totalWords}} words</span>
    <span>${{metric.rates[threshold].toFixed(1)}} per 1,000 words</span>`;
  tooltip.style.left = event.clientX + "px";
  tooltip.style.top = event.clientY + "px";
  tooltip.style.opacity = "1";
}}
function hideTip() {{
  tooltip.style.opacity = "0";
}}
function selectColumn(d) {{
  selectedColumn = d;
  render();
  renderDetails();
}}
function rareWordsForSelection() {{
  if (!selectedColumn) return [];
  const thresholdNumber = Number(threshold);
  return metricFor(selectedColumn).rareWords
    .filter(word => word.freq <= thresholdNumber)
    .sort((a, b) =>
      a.freq - b.freq ||
      String(a.lexKey).localeCompare(String(b.lexKey)) ||
      String(a.form).localeCompare(String(b.form))
    );
}}
function renderDetails() {{
  if (!selectedColumn) {{
    detailsSummary.innerHTML = `<h2>Click a column</h2>
      <p>Select any heatmap cell to see its rare lexical items sorted from rarest to least rare.</p>
      <p>${{escapeHtml(modeLabel())}}</p>`;
    wordList.innerHTML = `<div class="empty-detail">Rare-word details will appear here.</div>`;
    return;
  }}
  const words = rareWordsForSelection();
  const metric = metricFor(selectedColumn);
  detailsSummary.innerHTML = `<h2>${{escapeHtml(selectedColumn.tabletLabel)}}</h2>
    <p>Column ${{escapeHtml(selectedColumn.column)}}; ${{escapeHtml(modeLabel())}}</p>
    <p>${{metric.rareCounts[threshold]}} rare-token occurrences across ${{words.length}} lexical items.</p>
    <p>${{metric.rates[threshold].toFixed(1)}} per 1,000 words; ${{metric.totalWords.toLocaleString()}} counted words.</p>`;
  if (!words.length) {{
    wordList.innerHTML = `<div class="empty-detail">No lexical items meet the current threshold in this column.</div>`;
    return;
  }}
  const rows = words.map(word => `
    <tr>
      <td>${{escapeHtml(word.form || word.lexKey)}}</td>
      <td>${{escapeHtml(word.lexKey)}}</td>
      <td>${{escapeHtml(word.gloss || "—")}}</td>
      <td class="num">${{word.freq.toLocaleString()}}</td>
      <td class="num">${{word.columnCount.toLocaleString()}}</td>
    </tr>`).join("");
  wordList.innerHTML = `<table class="word-table">
    <thead>
      <tr>
        <th style="width: 18%">Form</th>
        <th style="width: 26%">DULAT / Parse</th>
        <th>Gloss</th>
        <th class="num" style="width: 88px">CUC freq</th>
        <th class="num" style="width: 84px">Column</th>
      </tr>
    </thead>
    <tbody>${{rows}}</tbody>
  </table>`;
}}
function render() {{
  setStats();
  svg.innerHTML = "";
  const width = margin.left + DATA.meta.maxColumns * (cellW + gap) + margin.right;
  const height = margin.top + DATA.tablets.length * (cellH + gap) + margin.bottom;
  svg.setAttribute("viewBox", `0 0 ${{width}} ${{height}}`);
  svg.setAttribute("width", width);
  svg.setAttribute("height", height);
  const maxRate = DATA.meta.maxRateByMode[activeMode][threshold];

  for (let column = 1; column <= DATA.meta.maxColumns; column++) {{
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("class", "axis-label");
    text.setAttribute("x", margin.left + (column - 1) * (cellW + gap) + cellW / 2);
    text.setAttribute("y", 18);
    text.setAttribute("text-anchor", "middle");
    text.textContent = column;
    svg.appendChild(text);
  }}

  DATA.tablets.forEach((tablet, row) => {{
    const y = margin.top + row * (cellH + gap);
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("class", "tablet-label");
    label.setAttribute("x", margin.left - 8);
    label.setAttribute("y", y + cellH - 2);
    label.setAttribute("text-anchor", "end");
    label.textContent = tablet.label.length > 54 ? tablet.label.slice(0, 51) + "..." : tablet.label;
    svg.appendChild(label);

    DATA.columns[tablet.id].forEach(d => {{
      const metric = metricFor(d);
      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("class", selectedColumn?.label === d.label ? "cell selected" : "cell");
      rect.setAttribute("x", margin.left + (d.ordinal - 1) * (cellW + gap));
      rect.setAttribute("y", y);
      rect.setAttribute("width", cellW);
      rect.setAttribute("height", cellH);
      rect.setAttribute("rx", 1.5);
      rect.setAttribute("fill", colorFor(metric.rates[threshold], maxRate));
      rect.setAttribute("tabindex", "0");
      rect.setAttribute("aria-label", `${{d.label}}: ${{metric.rates[threshold].toFixed(1)}} rare words per 1,000 words, ${{modeLabel()}}`);
      rect.addEventListener("mousemove", event => showTip(event, d));
      rect.addEventListener("mouseleave", hideTip);
      rect.addEventListener("focus", event => showTip(event, d));
      rect.addEventListener("blur", hideTip);
      rect.addEventListener("click", () => selectColumn(d));
      rect.addEventListener("keydown", event => {{
        if (event.key === "Enter" || event.key === " ") {{
          event.preventDefault();
          selectColumn(d);
        }}
      }});
      svg.appendChild(rect);
    }});
  }});
}}
setupModeToggles();
renderThresholdButtons();
render();
renderDetails();
</script>
</body>
</html>
"""


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    data = build_data()
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_HTML.write_text(build_html(data), encoding="utf-8")
    print(OUT_HTML)
    print(OUT_JSON)


if __name__ == "__main__":
    main()
