from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TF_DIR = ROOT / "corpora" / "bhsa" / "tf" / "2021"
OUT_DIR = ROOT / "out"
OUT_HTML = OUT_DIR / "bhsa_rare_word_heatmap.html"
OUT_JSON = OUT_DIR / "bhsa_rare_word_heatmap_data.json"

THRESHOLDS = (1, 2, 5, 10)
DEFAULT_THRESHOLD = 5
MODES = {
    "all": {
        "label": "All words",
        "description": "All word tokens counted",
        "excludeProperNouns": False,
        "excludeAramaic": False,
    },
    "noProperNouns": {
        "label": "No proper nouns",
        "description": "BHSA sp=nmpr tokens excluded",
        "excludeProperNouns": True,
        "excludeAramaic": False,
    },
    "noAramaic": {
        "label": "No Aramaic",
        "description": "BHSA Aramaic-language tokens excluded",
        "excludeProperNouns": False,
        "excludeAramaic": True,
    },
    "noProperNounsNoAramaic": {
        "label": "No proper nouns or Aramaic",
        "description": "BHSA sp=nmpr and Aramaic-language tokens excluded",
        "excludeProperNouns": True,
        "excludeAramaic": True,
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


def parse_otype_ranges(path: Path) -> dict[str, tuple[int, int]]:
    ranges: dict[str, tuple[int, int]] = {}
    for line in data_lines(path):
        left, node_type = line.split("\t", 1)
        if "-" in left:
            start_s, end_s = left.split("-", 1)
            ranges[node_type] = (int(start_s), int(end_s))
        else:
            node = int(left)
            ranges[node_type] = (node, node)
    return ranges


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


def format_label(book: str, chapter: int) -> str:
    return f"{book.replace('_', ' ')} {chapter}"


def chapter_metric(
    slots: list[int],
    *,
    exclude_proper_nouns: bool,
    exclude_aramaic: bool,
    word_freq: dict[int, int],
    word_sp: dict[int, str],
    word_language: dict[int, str],
    lex_raw: dict[int, str],
    lex_utf8_raw: dict[int, str],
    g_lex_utf8_raw: dict[int, str],
    gloss_raw: dict[int, str],
) -> dict:
    counted_slots = [
        slot
        for slot in slots
        if not (exclude_proper_nouns and word_sp.get(slot) == "nmpr")
        and not (
            exclude_aramaic
            and word_language.get(slot, "").lower() in {"arc", "aramaic"}
        )
    ]
    total = len(counted_slots)
    rare_counts = {
        threshold: sum(1 for slot in counted_slots if word_freq[slot] <= threshold)
        for threshold in THRESHOLDS
    }
    rare_lexemes: dict[str, dict] = {}
    for slot in counted_slots:
        freq = word_freq[slot]
        if freq > max(THRESHOLDS):
            continue
        lex = lex_raw.get(slot, "")
        lex_utf8 = lex_utf8_raw.get(slot, "")
        hebrew = g_lex_utf8_raw.get(slot, "")
        gloss = gloss_raw.get(slot, "")
        lex_key = "\u001f".join([lex, str(freq), lex_utf8, hebrew, gloss])
        if lex_key not in rare_lexemes:
            rare_lexemes[lex_key] = {
                "lex": lex,
                "lexUtf8": lex_utf8,
                "hebrew": hebrew,
                "gloss": gloss,
                "freq": freq,
                "chapterCount": 0,
            }
        rare_lexemes[lex_key]["chapterCount"] += 1
    rare_words = sorted(
        rare_lexemes.values(),
        key=lambda item: (
            item["freq"],
            item["hebrew"] or item["lexUtf8"] or item["lex"],
            item["gloss"],
        ),
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
    node_ranges = parse_otype_ranges(TF_DIR / "otype.tf")
    word_first, word_last = node_ranges["word"]
    book_first, book_last = node_ranges["book"]
    chapter_first, chapter_last = node_ranges["chapter"]

    book_en = parse_node_feature(TF_DIR / "book@en.tf")
    chapter_num_raw = parse_node_feature(TF_DIR / "chapter.tf")
    freq_lex_raw = parse_node_feature(TF_DIR / "freq_lex.tf")
    sp_raw = parse_node_feature(TF_DIR / "sp.tf")
    language_raw = parse_node_feature(TF_DIR / "language.tf")
    lex_raw = parse_node_feature(TF_DIR / "lex.tf")
    lex_utf8_raw = parse_node_feature(TF_DIR / "lex_utf8.tf")
    g_lex_utf8_raw = parse_node_feature(TF_DIR / "g_lex_utf8.tf")
    gloss_raw = parse_node_feature(TF_DIR / "gloss.tf")
    oslots = parse_oslots(TF_DIR / "oslots.tf")

    word_freq = {
        node: int(freq)
        for node, freq in freq_lex_raw.items()
        if word_first <= node <= word_last
    }
    word_sp = {
        node: sp
        for node, sp in sp_raw.items()
        if word_first <= node <= word_last
    }
    word_language = {
        node: language
        for node, language in language_raw.items()
        if word_first <= node <= word_last
    }

    slot_to_book: dict[int, str] = {}
    for book_node in range(book_first, book_last + 1):
        book = book_en[book_node]
        for slot in oslots[book_node]:
            slot_to_book[slot] = book

    rows_by_book: dict[str, list[dict]] = defaultdict(list)
    all_rates_by_mode: dict[str, dict[int, list[float]]] = {
        mode: {threshold: [] for threshold in THRESHOLDS} for mode in MODES
    }

    for chapter_node in range(chapter_first, chapter_last + 1):
        slots = oslots[chapter_node]
        if not slots:
            continue
        book = slot_to_book[slots[0]]
        chapter = int(chapter_num_raw[chapter_node])
        modes = {}
        for mode, config in MODES.items():
            metric = chapter_metric(
                slots,
                exclude_proper_nouns=config["excludeProperNouns"],
                exclude_aramaic=config["excludeAramaic"],
                word_freq=word_freq,
                word_sp=word_sp,
                word_language=word_language,
                lex_raw=lex_raw,
                lex_utf8_raw=lex_utf8_raw,
                g_lex_utf8_raw=g_lex_utf8_raw,
                gloss_raw=gloss_raw,
            )
            modes[mode] = metric
            for threshold in THRESHOLDS:
                all_rates_by_mode[mode][threshold].append(metric["rates"][str(threshold)])
        rows_by_book[book].append(
            {
                "book": book,
                "chapter": chapter,
                "label": format_label(book, chapter),
                "modes": modes,
            }
        )

    books = [book_en[node] for node in range(book_first, book_last + 1)]
    max_chapters = max(len(rows_by_book[book]) for book in books)

    return {
        "meta": {
            "corpus": "BHSA 2021",
            "metric": "rare word tokens per 1,000 chapter words",
            "defaultMode": DEFAULT_MODE,
            "modes": MODES,
            "defaultThreshold": DEFAULT_THRESHOLD,
            "thresholds": list(THRESHOLDS),
            "chapterCount": sum(len(rows_by_book[book]) for book in books),
            "wordCount": word_last - word_first + 1,
            "maxChapters": max_chapters,
            "maxRateByThreshold": {
                str(threshold): max(values)
                for threshold, values in all_rates_by_mode[DEFAULT_MODE].items()
            },
            "maxRateByMode": {
                mode: {
                    str(threshold): max(values)
                    for threshold, values in thresholds.items()
                }
                for mode, thresholds in all_rates_by_mode.items()
            },
        },
        "books": books,
        "chapters": {book: rows_by_book[book] for book in books},
    }


def build_html(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hebrew Bible Dark Corners: Rare Words by Chapter</title>
<style>
:root {{
  color-scheme: dark;
  --bg: #0e1116;
  --panel: #151a21;
  --panel-2: #1c222b;
  --ink: #e8edf2;
  --muted: #9aa7b5;
  --grid: #2b3440;
  --empty: #202731;
  --accent: #22a699;
  --hot: #f97316;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font: 14px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
main {{
  width: min(1760px, calc(100vw - 32px));
  margin: 24px auto 40px;
}}
.topbar {{
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 14px;
}}
h1 {{
  margin: 0 0 4px;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0;
}}
.sub {{
  margin: 0;
  color: var(--muted);
}}
.controls {{
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}}
.segmented {{
  display: inline-grid;
  grid-auto-flow: column;
  border: 1px solid var(--grid);
  border-radius: 8px;
  overflow: hidden;
  background: var(--panel);
}}
.segmented button {{
  border: 0;
  border-right: 1px solid var(--grid);
  background: transparent;
  color: var(--ink);
  min-width: 46px;
  height: 34px;
  padding: 0 12px;
  font: inherit;
  cursor: pointer;
}}
.segmented button:last-child {{ border-right: 0; }}
.segmented button[aria-pressed="true"] {{
  background: var(--accent);
  color: #fff;
  font-weight: 650;
}}
.switch-control {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--ink);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}}
.switch-control input {{
  position: absolute;
  opacity: 0;
  pointer-events: none;
}}
.switch-track {{
  position: relative;
  width: 44px;
  height: 24px;
  border: 1px solid var(--grid);
  border-radius: 999px;
  background: #293240;
  transition: background 120ms ease;
}}
.switch-track::after {{
  content: "";
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.24);
  transition: transform 120ms ease;
}}
.switch-control input:checked + .switch-track {{
  background: var(--accent);
  border-color: var(--accent);
}}
.switch-control input:checked + .switch-track::after {{
  transform: translateX(20px);
}}
.switch-control input:focus-visible + .switch-track {{
  outline: 2px solid #f8fafc;
  outline-offset: 2px;
}}
.legend {{
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  white-space: nowrap;
}}
.ramp {{
  width: 160px;
  height: 12px;
  border-radius: 999px;
  border: 1px solid var(--grid);
  background: linear-gradient(90deg, #16251f, #255f4e, #22a699, #f59e0b, #f97316);
}}
.viz-wrap {{
  background: var(--panel);
  border: 1px solid var(--grid);
  border-radius: 8px;
  padding: 14px;
  overflow: auto;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.28);
}}
svg {{
  display: block;
  min-width: 1460px;
}}
.axis-label {{
  fill: var(--muted);
  font-size: 11px;
}}
.book-label {{
  fill: var(--ink);
  font-size: 12px;
}}
.cell {{
  stroke: rgba(14, 17, 22, 0.82);
  stroke-width: 1;
}}
.cell.empty {{
  fill: var(--empty);
  stroke: transparent;
}}
.cell:focus {{
  outline: none;
  stroke: #f8fafc;
  stroke-width: 2;
}}
.cell.selected {{
  stroke: #f8fafc;
  stroke-width: 2;
}}
.details-panel {{
  display: grid;
  grid-template-columns: minmax(220px, 300px) 1fr;
  gap: 14px;
  background: var(--panel);
  border: 1px solid var(--grid);
  border-radius: 8px;
  margin-top: 12px;
  min-height: 170px;
  overflow: hidden;
}}
.details-summary {{
  border-right: 1px solid var(--grid);
  padding: 14px;
}}
.details-summary h2 {{
  margin: 0 0 8px;
  font-size: 18px;
  line-height: 1.2;
}}
.details-summary p {{
  margin: 0;
  color: var(--muted);
}}
.word-list {{
  overflow: auto;
  max-height: 380px;
}}
.word-table {{
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}}
.word-table th,
.word-table td {{
  border-bottom: 1px solid var(--grid);
  padding: 8px 10px;
  text-align: left;
  vertical-align: top;
}}
.word-table th {{
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--panel-2);
  color: var(--muted);
  font-size: 12px;
  font-weight: 650;
}}
.word-table td {{
  font-size: 13px;
}}
.word-table .hebrew {{
  direction: rtl;
  font-size: 18px;
  line-height: 1.2;
}}
.word-table .num {{
  text-align: right;
  font-variant-numeric: tabular-nums;
}}
.empty-detail {{
  display: flex;
  align-items: center;
  min-height: 170px;
  color: var(--muted);
  padding: 18px;
}}
.stats {{
  display: grid;
  grid-template-columns: repeat(5, minmax(140px, 1fr));
  gap: 10px;
  margin-top: 12px;
}}
.stat {{
  background: var(--panel);
  border: 1px solid var(--grid);
  border-radius: 8px;
  padding: 10px 12px;
}}
.stat b {{
  display: block;
  font-size: 18px;
}}
.stat span {{
  color: var(--muted);
  font-size: 12px;
}}
.tooltip {{
  position: fixed;
  z-index: 10;
  pointer-events: none;
  opacity: 0;
  transform: translate(-50%, -110%);
  background: #05070a;
  color: #fff;
  border-radius: 6px;
  padding: 8px 10px;
  min-width: 210px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.22);
  transition: opacity 80ms ease;
}}
.tooltip b {{
  display: block;
  margin-bottom: 3px;
}}
.tooltip span {{
  display: block;
  color: #cbd5e1;
  font-size: 12px;
}}
@media (max-width: 760px) {{
  main {{ width: min(100vw - 20px, 1760px); margin-top: 14px; }}
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
      <h1>Hebrew Bible Dark Corners: Rare Words by Chapter</h1>
      <p class="sub">BHSA 2021; normalized as rare word tokens per 1,000 chapter words.</p>
    </div>
    <div class="controls">
      <label class="switch-control">
        <input type="checkbox" id="properNounToggle">
        <span class="switch-track" aria-hidden="true"></span>
        <span>Exclude proper nouns</span>
      </label>
      <label class="switch-control">
        <input type="checkbox" id="aramaicToggle">
        <span class="switch-track" aria-hidden="true"></span>
        <span>Exclude Aramaic</span>
      </label>
      <span class="legend">Rare if total lexeme frequency <=</span>
      <div class="segmented" id="thresholds" aria-label="Rare word threshold"></div>
      <span class="legend"><span>low</span><span class="ramp" aria-hidden="true"></span><span>high</span></span>
    </div>
  </div>
  <div class="viz-wrap">
    <svg id="heatmap" role="img" aria-label="Heatmap of rare words by chapter"></svg>
  </div>
  <section class="details-panel" aria-live="polite">
    <div class="details-summary" id="detailsSummary">
      <h2>Click a chapter</h2>
      <p>Select any heatmap cell to see its rare lexemes sorted from rarest to least rare.</p>
    </div>
    <div class="word-list" id="wordList">
      <div class="empty-detail">Rare-word details will appear here.</div>
    </div>
  </section>
  <div class="stats">
    <div class="stat"><b id="chapterCount"></b><span>chapters</span></div>
    <div class="stat"><b id="maxRate"></b><span>highest rate per 1,000 words</span></div>
    <div class="stat"><b id="meanRate"></b><span>mean rate per 1,000 words</span></div>
    <div class="stat"><b id="selectedThreshold"></b><span>frequency threshold</span></div>
    <div class="stat"><b id="selectedMode"></b><span>counting mode</span></div>
  </div>
</main>
<div class="tooltip" id="tooltip"></div>
<script>
const DATA = {payload};
const svg = document.getElementById("heatmap");
const tooltip = document.getElementById("tooltip");
const properNounToggle = document.getElementById("properNounToggle");
const aramaicToggle = document.getElementById("aramaicToggle");
const thresholdButtons = document.getElementById("thresholds");
const detailsSummary = document.getElementById("detailsSummary");
const wordList = document.getElementById("wordList");
const margin = {{ left: 116, top: 30, right: 14, bottom: 20 }};
const cellW = 8;
const cellH = 17;
const gap = 1;
let activeMode = DATA.meta.defaultMode;
let threshold = String(DATA.meta.defaultThreshold);
let selectedChapter = null;

function lerp(a, b, t) {{ return a + (b - a) * t; }}
function escapeHtml(value) {{
  return String(value ?? "").replace(/[&<>"']/g, char => ({{
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }}[char]));
}}
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
function allChapters() {{
  return DATA.books.flatMap(book => DATA.chapters[book]);
}}
function metricFor(chapter) {{
  return chapter.modes?.[activeMode] ?? chapter;
}}
function modeLabel() {{
  return DATA.meta.modes[activeMode]?.label ?? activeMode;
}}
function modeFromToggles() {{
  if (properNounToggle.checked && aramaicToggle.checked) return "noProperNounsNoAramaic";
  if (properNounToggle.checked) return "noProperNouns";
  if (aramaicToggle.checked) return "noAramaic";
  return "all";
}}
function setStats() {{
  const chapters = allChapters();
  const rates = chapters.map(d => metricFor(d).rates[threshold]);
  const max = Math.max(...rates);
  const mean = rates.reduce((a, b) => a + b, 0) / rates.length;
  document.getElementById("chapterCount").textContent = DATA.meta.chapterCount.toLocaleString();
  document.getElementById("maxRate").textContent = max.toFixed(1);
  document.getElementById("meanRate").textContent = mean.toFixed(1);
  document.getElementById("selectedThreshold").textContent = "<= " + threshold;
  document.getElementById("selectedMode").textContent = modeLabel();
}}
function setupModeToggle() {{
  properNounToggle.checked = DATA.meta.modes[activeMode]?.excludeProperNouns ?? false;
  aramaicToggle.checked = DATA.meta.modes[activeMode]?.excludeAramaic ?? false;
  const updateMode = () => {{
    activeMode = modeFromToggles();
    render();
    renderDetails();
  }};
  properNounToggle.addEventListener("change", updateMode);
  aramaicToggle.addEventListener("change", updateMode);
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
  tooltip.innerHTML = `<b>${{d.label}}</b>
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
function selectChapter(d) {{
  selectedChapter = d;
  render();
  renderDetails();
}}
function rareWordsForSelection() {{
  if (!selectedChapter) return [];
  const thresholdNumber = Number(threshold);
  return metricFor(selectedChapter).rareWords
    .filter(word => word.freq <= thresholdNumber)
    .sort((a, b) =>
      a.freq - b.freq ||
      String(a.hebrew || a.lexUtf8 || a.lex).localeCompare(String(b.hebrew || b.lexUtf8 || b.lex)) ||
      String(a.gloss).localeCompare(String(b.gloss))
    );
}}
function renderDetails() {{
  if (!selectedChapter) {{
    detailsSummary.innerHTML = `<h2>Click a chapter</h2>
      <p>Select any heatmap cell to see its rare lexemes sorted from rarest to least rare.</p>
      <p>${{escapeHtml(modeLabel())}}</p>`;
    wordList.innerHTML = `<div class="empty-detail">Rare-word details will appear here.</div>`;
    return;
  }}
  const words = rareWordsForSelection();
  const metric = metricFor(selectedChapter);
  detailsSummary.innerHTML = `<h2>${{escapeHtml(selectedChapter.label)}}</h2>
    <p>${{escapeHtml(modeLabel())}}</p>
    <p>${{metric.rareCounts[threshold]}} rare-token occurrences across ${{words.length}} unique lexemes.</p>
    <p>${{metric.rates[threshold].toFixed(1)}} per 1,000 words; ${{metric.totalWords.toLocaleString()}} counted words.</p>`;
  if (!words.length) {{
    wordList.innerHTML = `<div class="empty-detail">No lexemes meet the current threshold in this chapter.</div>`;
    return;
  }}
  const rows = words.map(word => `
    <tr>
      <td class="hebrew">${{escapeHtml(word.hebrew || word.lexUtf8 || word.lex)}}</td>
      <td>${{escapeHtml(word.gloss || "—")}}</td>
      <td class="num">${{word.freq.toLocaleString()}}</td>
      <td class="num">${{word.chapterCount.toLocaleString()}}</td>
    </tr>`).join("");
  wordList.innerHTML = `<table class="word-table">
    <thead>
      <tr>
        <th style="width: 30%">Hebrew</th>
        <th>Gloss</th>
        <th class="num" style="width: 88px">BHSA freq</th>
        <th class="num" style="width: 84px">Chapter</th>
      </tr>
    </thead>
    <tbody>${{rows}}</tbody>
  </table>`;
}}
function render() {{
  setStats();
  svg.innerHTML = "";
  const maxChapters = DATA.meta.maxChapters;
  const width = margin.left + maxChapters * (cellW + gap) + margin.right;
  const height = margin.top + DATA.books.length * (cellH + gap) + margin.bottom;
  svg.setAttribute("viewBox", `0 0 ${{width}} ${{height}}`);
  svg.setAttribute("width", width);
  svg.setAttribute("height", height);
  const maxRate = DATA.meta.maxRateByMode[activeMode][threshold];

  for (let chapter = 1; chapter <= maxChapters; chapter += 10) {{
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("class", "axis-label");
    text.setAttribute("x", margin.left + (chapter - 1) * (cellW + gap));
    text.setAttribute("y", 18);
    text.textContent = chapter;
    svg.appendChild(text);
  }}

  DATA.books.forEach((book, row) => {{
    const y = margin.top + row * (cellH + gap);
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("class", "book-label");
    label.setAttribute("x", margin.left - 8);
    label.setAttribute("y", y + cellH - 4);
    label.setAttribute("text-anchor", "end");
    label.textContent = book.replaceAll("_", " ");
    svg.appendChild(label);

    const chapters = DATA.chapters[book];
    chapters.forEach(d => {{
      const metric = metricFor(d);
      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("class", selectedChapter?.label === d.label ? "cell selected" : "cell");
      rect.setAttribute("x", margin.left + (d.chapter - 1) * (cellW + gap));
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
      rect.addEventListener("click", () => selectChapter(d));
      rect.addEventListener("keydown", event => {{
        if (event.key === "Enter" || event.key === " ") {{
          event.preventDefault();
          selectChapter(d);
        }}
      }});
      svg.appendChild(rect);
    }});
  }});
}}
setupModeToggle();
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
