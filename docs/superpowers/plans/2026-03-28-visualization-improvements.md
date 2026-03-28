# Visualization Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade conker-ledger's SVG chart generators with better styling, add three new chart types, and embed mermaid diagrams in the generated README.

**Architecture:** All changes are incremental within `src/conker_ledger/ledger.py`. A shared `_family_color()` helper provides deterministic color assignment. New SVG functions (`write_pie_svg`, `write_histogram_svg`, `write_grouped_bar_svg`) and mermaid renderers (`render_lineage_mermaid`, `render_survival_mermaid`) are added alongside the existing functions. `write_report_bundle` is extended to call them and embed mermaid in the README.

**Tech Stack:** Python 3.11+, stdlib only (no new dependencies). SVG generation via string building. Mermaid syntax embedded in markdown.

---

### Task 1: Add test infrastructure and baseline tests

**Files:**
- Create: `tests/test_viz.py`

- [ ] **Step 1: Create test file with baseline tests for existing SVG functions**

```python
from __future__ import annotations

import math
from pathlib import Path
from conker_ledger.ledger import (
    _family_color,
    _svg_escape,
    _truncate_label,
    write_bar_svg,
    write_scatter_svg,
    write_pie_svg,
    write_histogram_svg,
    write_grouped_bar_svg,
    render_lineage_mermaid,
    render_survival_mermaid,
)


def test_svg_escape():
    assert _svg_escape("a < b & c > d") == "a &lt; b &amp; c &gt; d"


def test_bar_svg_writes_file(tmp_path: Path):
    path = tmp_path / "bar.svg"
    write_bar_svg(path, "Test", ["alpha", "beta"], [0.5, 0.3])
    content = path.read_text()
    assert content.startswith("<svg")
    assert "Test" in content
    assert "alpha" in content
    assert "0.5000" in content


def test_bar_svg_empty(tmp_path: Path):
    path = tmp_path / "bar.svg"
    write_bar_svg(path, "Empty", [], [])
    content = path.read_text()
    assert "<svg" in content


def test_scatter_svg_writes_file(tmp_path: Path):
    path = tmp_path / "scatter.svg"
    rows = [
        {"x": 0.5, "y": 0.6, "label": "a", "family_id": "fam1"},
        {"x": 0.7, "y": 0.8, "label": "b", "family_id": "fam2"},
    ]
    write_scatter_svg(path, "Test", rows, x_key="x", y_key="y", label_key="label")
    content = path.read_text()
    assert content.startswith("<svg")
    assert "Test" in content


def test_scatter_svg_empty(tmp_path: Path):
    path = tmp_path / "scatter.svg"
    write_scatter_svg(path, "Test", [], x_key="x", y_key="y", label_key="label")
    content = path.read_text()
    assert "<svg" in content
```

- [ ] **Step 2: Verify tests fail (functions not yet updated)**

Run: `python -m pytest tests/test_viz.py -v`
Expected: ImportError for `_family_color`, `_truncate_label`, `write_pie_svg`, etc. The existing function tests may pass since they exist already. That's fine — these are baseline tests.

- [ ] **Step 3: Commit**

```bash
git add tests/test_viz.py
git commit -m "test: add baseline visualization test infrastructure"
```

---

### Task 2: Add shared helpers (`_family_color`, `_truncate_label`, `_nice_ticks`)

**Files:**
- Modify: `src/conker_ledger/ledger.py` (add after `_svg_escape` around line 277)

- [ ] **Step 1: Add helper functions to `ledger.py`**

Add these functions after `_svg_escape`:

```python
_PALETTE = [
    "#2f6fed", "#c23b22", "#2ca02c", "#9467bd", "#e377c2",
    "#8c564b", "#17becf", "#bcbd22", "#ff7f0e", "#7f7f7f",
    "#1f77b4", "#d62728", "#98df8a", "#aec7e8", "#ffbb78",
]


def _family_color(family_id: str) -> str:
    return _PALETTE[hash(family_id) % len(_PALETTE)]


def _truncate_label(label: str, max_chars: int = 32) -> str:
    if len(label) <= max_chars:
        return label
    return label[: max_chars - 1] + "\u2026"


def _nice_ticks(vmin: float, vmax: float, target_count: int = 5) -> list[float]:
    span = vmax - vmin
    if span <= 0:
        return [vmin]
    raw_step = span / max(target_count, 1)
    magnitude = 10 ** math.floor(math.log10(raw_step))
    for nice in [1, 2, 5, 10]:
        step = nice * magnitude
        if step >= raw_step:
            break
    start = math.ceil(vmin / step) * step
    ticks: list[float] = []
    val = start
    while val <= vmax + step * 0.001:
        ticks.append(round(val, 10))
        val += step
    return ticks
```

- [ ] **Step 2: Add tests for the new helpers**

Append to `tests/test_viz.py`:

```python
def test_family_color_deterministic():
    c1 = _family_color("conker4b_tandem")
    c2 = _family_color("conker4b_tandem")
    c3 = _family_color("conker7_bidir")
    assert c1 == c2
    assert c1.startswith("#")
    assert c3.startswith("#")


def test_truncate_label_short():
    assert _truncate_label("short", 32) == "short"


def test_truncate_label_long():
    result = _truncate_label("a" * 50, 32)
    assert len(result) == 32
    assert result.endswith("\u2026")


def test_nice_ticks_basic():
    ticks = _nice_ticks(0.5, 0.6, 5)
    assert len(ticks) >= 2
    assert all(0.5 <= t <= 0.61 for t in ticks)
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/test_viz.py -v`
Expected: All helper tests PASS. The import of `write_pie_svg` etc. will still fail, so the full file won't load. Temporarily comment out those imports in the test file, or split the imports so existing tests can run.

Actually — better approach: remove the not-yet-created imports from the top of the test file for now. Import only what exists. We'll add the new imports as we create each function.

Update the test file imports to only import what exists so far:

```python
from conker_ledger.ledger import (
    _family_color,
    _svg_escape,
    _truncate_label,
    write_bar_svg,
    write_scatter_svg,
)
```

- [ ] **Step 4: Run tests and verify all pass**

Run: `python -m pytest tests/test_viz.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/conker_ledger/ledger.py tests/test_viz.py
git commit -m "feat: add _family_color, _truncate_label, _nice_ticks helpers"
```

---

### Task 3: Improve `write_bar_svg`

**Files:**
- Modify: `src/conker_ledger/ledger.py` (replace `write_bar_svg` function, lines 279-306)

- [ ] **Step 1: Write tests for improved bar SVG features**

Append to `tests/test_viz.py`:

```python
def test_bar_svg_has_gridlines(tmp_path: Path):
    path = tmp_path / "bar.svg"
    write_bar_svg(path, "Test", ["a", "b", "c"], [0.5, 0.3, 0.7])
    content = path.read_text()
    assert "stroke-dasharray" in content  # gridlines are dashed


def test_bar_svg_has_tick_labels(tmp_path: Path):
    path = tmp_path / "bar.svg"
    write_bar_svg(path, "Test", ["a", "b"], [0.5, 0.3])
    content = path.read_text()
    assert 'class="tick"' in content


def test_bar_svg_truncates_long_labels(tmp_path: Path):
    path = tmp_path / "bar.svg"
    long_label = "a" * 60
    write_bar_svg(path, "Test", [long_label], [0.5])
    content = path.read_text()
    assert "\u2026" in content


def test_bar_svg_4dp_values(tmp_path: Path):
    path = tmp_path / "bar.svg"
    write_bar_svg(path, "Test", ["a"], [0.123456])
    content = path.read_text()
    assert "0.1235" in content
    assert "0.123456" not in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_viz.py::test_bar_svg_has_gridlines tests/test_viz.py::test_bar_svg_has_tick_labels tests/test_viz.py::test_bar_svg_truncates_long_labels tests/test_viz.py::test_bar_svg_4dp_values -v`
Expected: FAIL

- [ ] **Step 3: Replace `write_bar_svg` implementation**

Replace the entire `write_bar_svg` function in `ledger.py` with:

```python
def write_bar_svg(path: Path, title: str, labels: list[str], values: list[float], *, width: int = 960, height: int = 480) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not labels or not values:
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="960" height="120"></svg>\n', encoding="utf-8")
        return
    margin_left = 260
    margin_right = 80
    margin_top = 50
    margin_bottom = 40
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    bar_gap = 6
    bar_height = max(8, (plot_height - bar_gap * (len(values) - 1)) // max(len(values), 1))
    vmax = max(max(values), 1e-12)
    ticks = _nice_ticks(0, vmax, 5)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>text{font-family:Menlo,Monaco,monospace;font-size:11px;fill:#333}'
        ' .title{font-size:16px;font-weight:700;fill:#111}'
        ' .axis{stroke:#888;stroke-width:1}'
        ' .grid{stroke:#ddd;stroke-width:1;stroke-dasharray:4,4}'
        ' .tick{font-size:10px;fill:#666}'
        ' .val{font-size:10px;fill:#333}</style>',
        f'<text class="title" x="{margin_left}" y="28">{_svg_escape(title)}</text>',
    ]
    # gridlines and tick labels
    for tick in ticks:
        x = margin_left + plot_width * (tick / vmax) if vmax > 0 else margin_left
        parts.append(f'<line class="grid" x1="{x:.1f}" y1="{margin_top}" x2="{x:.1f}" y2="{margin_top + plot_height}"/>')
        parts.append(f'<text class="tick" x="{x:.1f}" y="{margin_top + plot_height + 16}" text-anchor="middle">{tick:.4f}</text>')
    # bottom axis
    parts.append(f'<line class="axis" x1="{margin_left}" y1="{margin_top + plot_height}" x2="{width - margin_right}" y2="{margin_top + plot_height}"/>')
    # bars
    for idx, (label, value) in enumerate(zip(labels, values)):
        y = margin_top + idx * (bar_height + bar_gap)
        bar_w = plot_width * (value / vmax) if vmax > 0 else 0
        color = _family_color(label.split(":")[0])
        truncated = _truncate_label(_svg_escape(label), 36)
        parts.append(f'<text x="{margin_left - 8}" y="{y + bar_height - 2}" text-anchor="end">{truncated}</text>')
        parts.append(f'<rect fill="{color}" x="{margin_left}" y="{y}" width="{bar_w:.2f}" height="{bar_height}" rx="2"/>')
        parts.append(f'<text class="val" x="{margin_left + bar_w + 6:.2f}" y="{y + bar_height - 2}">{value:.4f}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run tests and verify all pass**

Run: `python -m pytest tests/test_viz.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/conker_ledger/ledger.py tests/test_viz.py
git commit -m "feat: improve write_bar_svg with gridlines, ticks, colors, label truncation"
```

---

### Task 4: Improve `write_scatter_svg`

**Files:**
- Modify: `src/conker_ledger/ledger.py` (replace `write_scatter_svg` function, lines 309-355)

- [ ] **Step 1: Write tests for improved scatter SVG features**

Append to `tests/test_viz.py`:

```python
def test_scatter_svg_has_gridlines(tmp_path: Path):
    path = tmp_path / "scatter.svg"
    rows = [
        {"x": 0.5, "y": 0.6, "label": "a", "family_id": "fam1"},
        {"x": 0.7, "y": 0.8, "label": "b", "family_id": "fam2"},
    ]
    write_scatter_svg(path, "Test", rows, x_key="x", y_key="y", label_key="label")
    content = path.read_text()
    assert "stroke-dasharray" in content


def test_scatter_svg_has_tick_labels(tmp_path: Path):
    path = tmp_path / "scatter.svg"
    rows = [
        {"x": 0.5, "y": 0.6, "label": "a", "family_id": "fam1"},
        {"x": 0.7, "y": 0.8, "label": "b", "family_id": "fam2"},
    ]
    write_scatter_svg(path, "Test", rows, x_key="x", y_key="y", label_key="label")
    content = path.read_text()
    assert 'class="tick"' in content


def test_scatter_svg_has_reference_line(tmp_path: Path):
    path = tmp_path / "scatter.svg"
    rows = [
        {"x": 0.5, "y": 0.6, "label": "a", "family_id": "fam1"},
        {"x": 0.7, "y": 0.8, "label": "b", "family_id": "fam2"},
    ]
    write_scatter_svg(path, "Test", rows, x_key="x", y_key="y", label_key="label", reference_line=True)
    content = path.read_text()
    assert "ref" in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_viz.py::test_scatter_svg_has_gridlines tests/test_viz.py::test_scatter_svg_has_tick_labels tests/test_viz.py::test_scatter_svg_has_reference_line -v`
Expected: FAIL

- [ ] **Step 3: Replace `write_scatter_svg` implementation**

Replace the entire `write_scatter_svg` function in `ledger.py` with:

```python
def write_scatter_svg(
    path: Path,
    title: str,
    rows: list[dict[str, Any]],
    *,
    x_key: str,
    y_key: str,
    label_key: str,
    reference_line: bool = False,
    width: int = 960,
    height: int = 480,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    points = [(row.get(x_key), row.get(y_key), row.get(label_key), row.get("family_id", "")) for row in rows]
    points = [(float(x), float(y), str(label), str(fam)) for x, y, label, fam in points if x is not None and y is not None]
    if not points:
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="960" height="120"></svg>\n', encoding="utf-8")
        return
    margin_left = 70
    margin_right = 40
    margin_top = 50
    margin_bottom = 50
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    if max_x == min_x:
        max_x += 1e-9
    if max_y == min_y:
        max_y += 1e-9
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>text{font-family:Menlo,Monaco,monospace;font-size:11px;fill:#333}'
        ' .title{font-size:16px;font-weight:700;fill:#111}'
        ' .axis{stroke:#888;stroke-width:1}'
        ' .grid{stroke:#ddd;stroke-width:1;stroke-dasharray:4,4}'
        ' .tick{font-size:10px;fill:#666}'
        ' .ref{stroke:#bbb;stroke-width:1;stroke-dasharray:6,3}</style>',
        f'<text class="title" x="{margin_left}" y="28">{_svg_escape(title)}</text>',
    ]
    # gridlines and ticks — x axis
    for tick in _nice_ticks(min_x, max_x, 5):
        px = margin_left + (tick - min_x) / (max_x - min_x) * plot_width
        parts.append(f'<line class="grid" x1="{px:.1f}" y1="{margin_top}" x2="{px:.1f}" y2="{margin_top + plot_height}"/>')
        parts.append(f'<text class="tick" x="{px:.1f}" y="{margin_top + plot_height + 16}" text-anchor="middle">{tick:.4f}</text>')
    # gridlines and ticks — y axis
    for tick in _nice_ticks(min_y, max_y, 5):
        py = margin_top + plot_height - (tick - min_y) / (max_y - min_y) * plot_height
        parts.append(f'<line class="grid" x1="{margin_left}" y1="{py:.1f}" x2="{width - margin_right}" y2="{py:.1f}"/>')
        parts.append(f'<text class="tick" x="{margin_left - 6}" y="{py + 4:.1f}" text-anchor="end">{tick:.4f}</text>')
    # axes
    parts.append(f'<line class="axis" x1="{margin_left}" y1="{margin_top + plot_height}" x2="{width - margin_right}" y2="{margin_top + plot_height}"/>')
    parts.append(f'<line class="axis" x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}"/>')
    # y=x reference line
    if reference_line:
        ref_min = max(min_x, min_y)
        ref_max = min(max_x, max_y)
        if ref_min < ref_max:
            rx1 = margin_left + (ref_min - min_x) / (max_x - min_x) * plot_width
            ry1 = margin_top + plot_height - (ref_min - min_y) / (max_y - min_y) * plot_height
            rx2 = margin_left + (ref_max - min_x) / (max_x - min_x) * plot_width
            ry2 = margin_top + plot_height - (ref_max - min_y) / (max_y - min_y) * plot_height
            parts.append(f'<line class="ref" x1="{rx1:.1f}" y1="{ry1:.1f}" x2="{rx2:.1f}" y2="{ry2:.1f}"/>')
    # points — collect y positions for collision offset
    rendered: list[float] = []
    for x, y, label, fam in points:
        px = margin_left + (x - min_x) / (max_x - min_x) * plot_width
        py = margin_top + plot_height - (y - min_y) / (max_y - min_y) * plot_height
        color = _family_color(fam)
        parts.append(f'<circle fill="{color}" opacity="0.8" cx="{px:.2f}" cy="{py:.2f}" r="5"/>')
        # offset label if it collides with a previous label
        label_y = py - 6
        for prev_y in rendered:
            if abs(label_y - prev_y) < 14:
                label_y = prev_y - 14
        rendered.append(label_y)
        truncated = _truncate_label(_svg_escape(label), 28)
        parts.append(f'<text x="{px + 7:.2f}" y="{label_y:.2f}">{truncated}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run tests and verify all pass**

Run: `python -m pytest tests/test_viz.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/conker_ledger/ledger.py tests/test_viz.py
git commit -m "feat: improve write_scatter_svg with gridlines, ticks, y=x reference line, colors"
```

---

### Task 5: Add `write_pie_svg`

**Files:**
- Modify: `src/conker_ledger/ledger.py` (add after `write_scatter_svg`)

- [ ] **Step 1: Write tests for pie SVG**

Append to `tests/test_viz.py` and add `write_pie_svg` to the import:

```python
def test_pie_svg_writes_file(tmp_path: Path):
    path = tmp_path / "pie.svg"
    write_pie_svg(
        path, "Status",
        labels=["survived", "failed", "bridge_only"],
        values=[10, 3, 50],
        colors=["#2ca02c", "#c23b22", "#7f7f7f"],
    )
    content = path.read_text()
    assert content.startswith("<svg")
    assert "Status" in content
    assert "survived" in content


def test_pie_svg_single_segment(tmp_path: Path):
    path = tmp_path / "pie.svg"
    write_pie_svg(path, "One", labels=["all"], values=[100], colors=["#2ca02c"])
    content = path.read_text()
    assert "<svg" in content
    assert "all" in content


def test_pie_svg_empty(tmp_path: Path):
    path = tmp_path / "pie.svg"
    write_pie_svg(path, "Empty", labels=[], values=[], colors=[])
    content = path.read_text()
    assert "<svg" in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_viz.py::test_pie_svg_writes_file -v`
Expected: ImportError or AttributeError

- [ ] **Step 3: Implement `write_pie_svg`**

Add to `ledger.py` after `write_scatter_svg`:

```python
def write_pie_svg(
    path: Path,
    title: str,
    labels: list[str],
    values: list[float],
    colors: list[str],
    *,
    width: int = 480,
    height: int = 400,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not values or sum(values) == 0:
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="120"></svg>\n', encoding="utf-8")
        return
    cx, cy = width // 2, height // 2 + 10
    r = min(cx, cy) - 60
    total = sum(values)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>text{font-family:Menlo,Monaco,monospace;font-size:12px;fill:#333}'
        ' .title{font-size:16px;font-weight:700;fill:#111}'
        ' .legend{font-size:11px}</style>',
        f'<text class="title" x="{cx}" y="24" text-anchor="middle">{_svg_escape(title)}</text>',
    ]
    angle = -math.pi / 2  # start at 12 o'clock
    for i, (label, value, color) in enumerate(zip(labels, values, colors)):
        frac = value / total
        sweep = frac * 2 * math.pi
        if len(values) == 1:
            # full circle
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>')
        else:
            x1 = cx + r * math.cos(angle)
            y1 = cy + r * math.sin(angle)
            x2 = cx + r * math.cos(angle + sweep)
            y2 = cy + r * math.sin(angle + sweep)
            large = 1 if sweep > math.pi else 0
            parts.append(
                f'<path d="M{cx},{cy} L{x1:.2f},{y1:.2f} A{r},{r} 0 {large},1 {x2:.2f},{y2:.2f} Z" fill="{color}"/>'
            )
        # label at midpoint of arc
        mid_angle = angle + sweep / 2
        lx = cx + (r * 0.65) * math.cos(mid_angle)
        ly = cy + (r * 0.65) * math.sin(mid_angle)
        pct = f"{frac * 100:.0f}%"
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" fill="#fff" font-weight="700">{int(value)}</text>')
        # legend entry
        legend_y = height - 20 * (len(values) - i)
        parts.append(f'<rect x="10" y="{legend_y - 10}" width="12" height="12" fill="{color}"/>')
        parts.append(f'<text class="legend" x="28" y="{legend_y}">{_svg_escape(label)} ({pct})</text>')
        angle += sweep
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run tests and verify all pass**

Run: `python -m pytest tests/test_viz.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/conker_ledger/ledger.py tests/test_viz.py
git commit -m "feat: add write_pie_svg for survival status breakdown"
```

---

### Task 6: Add `write_histogram_svg`

**Files:**
- Modify: `src/conker_ledger/ledger.py` (add after `write_pie_svg`)

- [ ] **Step 1: Write tests for histogram SVG**

Append to `tests/test_viz.py` and add `write_histogram_svg` to the import:

```python
def test_histogram_svg_writes_file(tmp_path: Path):
    path = tmp_path / "hist.svg"
    write_histogram_svg(path, "Deltas", [0.01, 0.02, 0.015, 0.008, 0.025, 0.01, 0.012])
    content = path.read_text()
    assert content.startswith("<svg")
    assert "Deltas" in content


def test_histogram_svg_single_value(tmp_path: Path):
    path = tmp_path / "hist.svg"
    write_histogram_svg(path, "One", [0.5])
    content = path.read_text()
    assert "<svg" in content


def test_histogram_svg_empty(tmp_path: Path):
    path = tmp_path / "hist.svg"
    write_histogram_svg(path, "Empty", [])
    content = path.read_text()
    assert "<svg" in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_viz.py::test_histogram_svg_writes_file -v`
Expected: ImportError

- [ ] **Step 3: Implement `write_histogram_svg`**

Add to `ledger.py` after `write_pie_svg`:

```python
def write_histogram_svg(
    path: Path,
    title: str,
    values: list[float],
    *,
    bins: int = 10,
    width: int = 960,
    height: int = 400,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not values:
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="960" height="120"></svg>\n', encoding="utf-8")
        return
    margin_left = 60
    margin_right = 40
    margin_top = 50
    margin_bottom = 50
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    vmin, vmax = min(values), max(values)
    if vmax == vmin:
        vmax = vmin + 1e-9
    bin_width = (vmax - vmin) / bins
    counts = [0] * bins
    for v in values:
        idx = min(int((v - vmin) / bin_width), bins - 1)
        counts[idx] += 1
    max_count = max(counts) if counts else 1
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>text{font-family:Menlo,Monaco,monospace;font-size:11px;fill:#333}'
        ' .title{font-size:16px;font-weight:700;fill:#111}'
        ' .axis{stroke:#888;stroke-width:1}'
        ' .grid{stroke:#ddd;stroke-width:1;stroke-dasharray:4,4}'
        ' .tick{font-size:10px;fill:#666}'
        ' .bar{fill:#2f6fed;opacity:0.85}</style>',
        f'<text class="title" x="{margin_left}" y="28">{_svg_escape(title)}</text>',
    ]
    # y-axis gridlines
    for tick in _nice_ticks(0, max_count, 4):
        py = margin_top + plot_height - (tick / max(max_count, 1)) * plot_height
        parts.append(f'<line class="grid" x1="{margin_left}" y1="{py:.1f}" x2="{width - margin_right}" y2="{py:.1f}"/>')
        parts.append(f'<text class="tick" x="{margin_left - 6}" y="{py + 4:.1f}" text-anchor="end">{int(tick)}</text>')
    # axes
    parts.append(f'<line class="axis" x1="{margin_left}" y1="{margin_top + plot_height}" x2="{width - margin_right}" y2="{margin_top + plot_height}"/>')
    parts.append(f'<line class="axis" x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}"/>')
    # bars
    rect_w = plot_width / bins - 2
    for i, count in enumerate(counts):
        x = margin_left + i * (plot_width / bins) + 1
        bar_h = (count / max(max_count, 1)) * plot_height
        y = margin_top + plot_height - bar_h
        parts.append(f'<rect class="bar" x="{x:.1f}" y="{y:.1f}" width="{rect_w:.1f}" height="{bar_h:.1f}" rx="1"/>')
    # x-axis tick labels
    for tick in _nice_ticks(vmin, vmax, 5):
        px = margin_left + (tick - vmin) / (vmax - vmin) * plot_width
        parts.append(f'<text class="tick" x="{px:.1f}" y="{margin_top + plot_height + 16}" text-anchor="middle">{tick:.4f}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run tests and verify all pass**

Run: `python -m pytest tests/test_viz.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/conker_ledger/ledger.py tests/test_viz.py
git commit -m "feat: add write_histogram_svg for delta distribution"
```

---

### Task 7: Add `write_grouped_bar_svg`

**Files:**
- Modify: `src/conker_ledger/ledger.py` (add after `write_histogram_svg`)

- [ ] **Step 1: Write tests for grouped bar SVG**

Append to `tests/test_viz.py` and add `write_grouped_bar_svg` to the import:

```python
def test_grouped_bar_svg_writes_file(tmp_path: Path):
    path = tmp_path / "grouped.svg"
    rows = [
        {"label": "fam_a", "bridge": 0.55, "full": 0.57},
        {"label": "fam_b", "bridge": 0.52, "full": 0.53},
    ]
    write_grouped_bar_svg(path, "Bridge vs Full", rows, key_a="bridge", key_b="full", label_key="label")
    content = path.read_text()
    assert content.startswith("<svg")
    assert "Bridge vs Full" in content
    assert "fam_a" in content


def test_grouped_bar_svg_empty(tmp_path: Path):
    path = tmp_path / "grouped.svg"
    write_grouped_bar_svg(path, "Empty", [], key_a="a", key_b="b", label_key="l")
    content = path.read_text()
    assert "<svg" in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_viz.py::test_grouped_bar_svg_writes_file -v`
Expected: ImportError

- [ ] **Step 3: Implement `write_grouped_bar_svg`**

Add to `ledger.py` after `write_histogram_svg`:

```python
def write_grouped_bar_svg(
    path: Path,
    title: str,
    rows: list[dict[str, Any]],
    *,
    key_a: str,
    key_b: str,
    label_key: str,
    width: int = 960,
    height: int = 480,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    filtered = [r for r in rows if r.get(key_a) is not None and r.get(key_b) is not None]
    if not filtered:
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="960" height="120"></svg>\n', encoding="utf-8")
        return
    margin_left = 260
    margin_right = 80
    margin_top = 50
    margin_bottom = 40
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    group_gap = 10
    bar_gap = 2
    group_height = max(16, (plot_height - group_gap * (len(filtered) - 1)) // max(len(filtered), 1))
    sub_bar = (group_height - bar_gap) // 2
    all_vals = [r[key_a] for r in filtered] + [r[key_b] for r in filtered]
    vmax = max(all_vals) if all_vals else 1e-12
    ticks = _nice_ticks(0, vmax, 5)
    color_a = "#2f6fed"
    color_b = "#c23b22"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>text{font-family:Menlo,Monaco,monospace;font-size:11px;fill:#333}'
        ' .title{font-size:16px;font-weight:700;fill:#111}'
        ' .axis{stroke:#888;stroke-width:1}'
        ' .grid{stroke:#ddd;stroke-width:1;stroke-dasharray:4,4}'
        ' .tick{font-size:10px;fill:#666}'
        ' .val{font-size:10px;fill:#333}'
        ' .legend{font-size:11px}</style>',
        f'<text class="title" x="{margin_left}" y="28">{_svg_escape(title)}</text>',
        # legend
        f'<rect x="{width - 200}" y="10" width="12" height="12" fill="{color_a}"/>',
        f'<text class="legend" x="{width - 184}" y="21">{_svg_escape(key_a)}</text>',
        f'<rect x="{width - 200}" y="28" width="12" height="12" fill="{color_b}"/>',
        f'<text class="legend" x="{width - 184}" y="39">{_svg_escape(key_b)}</text>',
    ]
    # gridlines
    for tick in ticks:
        x = margin_left + plot_width * (tick / vmax) if vmax > 0 else margin_left
        parts.append(f'<line class="grid" x1="{x:.1f}" y1="{margin_top}" x2="{x:.1f}" y2="{margin_top + plot_height}"/>')
        parts.append(f'<text class="tick" x="{x:.1f}" y="{margin_top + plot_height + 16}" text-anchor="middle">{tick:.4f}</text>')
    parts.append(f'<line class="axis" x1="{margin_left}" y1="{margin_top + plot_height}" x2="{width - margin_right}" y2="{margin_top + plot_height}"/>')
    for idx, row in enumerate(filtered):
        y = margin_top + idx * (group_height + group_gap)
        label = _truncate_label(_svg_escape(str(row.get(label_key, ""))), 36)
        va, vb = float(row[key_a]), float(row[key_b])
        wa = plot_width * (va / vmax) if vmax > 0 else 0
        wb = plot_width * (vb / vmax) if vmax > 0 else 0
        parts.append(f'<text x="{margin_left - 8}" y="{y + group_height // 2 + 4}" text-anchor="end">{label}</text>')
        parts.append(f'<rect fill="{color_a}" x="{margin_left}" y="{y}" width="{wa:.2f}" height="{sub_bar}" rx="2"/>')
        parts.append(f'<text class="val" x="{margin_left + wa + 4:.2f}" y="{y + sub_bar - 2}">{va:.4f}</text>')
        parts.append(f'<rect fill="{color_b}" x="{margin_left}" y="{y + sub_bar + bar_gap}" width="{wb:.2f}" height="{sub_bar}" rx="2"/>')
        parts.append(f'<text class="val" x="{margin_left + wb + 4:.2f}" y="{y + group_height - 2}">{vb:.4f}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run tests and verify all pass**

Run: `python -m pytest tests/test_viz.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/conker_ledger/ledger.py tests/test_viz.py
git commit -m "feat: add write_grouped_bar_svg for bridge vs full comparison"
```

---

### Task 8: Add `render_lineage_mermaid`

**Files:**
- Modify: `src/conker_ledger/ledger.py` (add after `write_grouped_bar_svg`)

- [ ] **Step 1: Write tests for lineage mermaid**

Append to `tests/test_viz.py` and add `render_lineage_mermaid` to the import:

```python
def test_render_lineage_mermaid_basic():
    rows = [
        {"parent_run_id": "parent_seed42", "child_run_id": "child_a_seed42", "child_bpb": 0.51},
        {"parent_run_id": "parent_seed42", "child_run_id": "child_b_seed42", "child_bpb": 0.52},
        {"parent_run_id": "child_a_seed42", "child_run_id": "grandchild_seed42", "child_bpb": 0.50},
    ]
    result = render_lineage_mermaid(rows)
    assert result.startswith("graph TD")
    assert "parent_seed42" in result or "parent" in result
    assert "-->" in result


def test_render_lineage_mermaid_empty():
    result = render_lineage_mermaid([])
    assert "graph TD" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_viz.py::test_render_lineage_mermaid_basic -v`
Expected: ImportError

- [ ] **Step 3: Implement `render_lineage_mermaid`**

Add to `ledger.py`:

```python
def _mermaid_id(run_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", run_id)


def render_lineage_mermaid(rows: list[dict[str, Any]], *, max_nodes: int = 30) -> str:
    if not rows:
        return "graph TD\n    empty[No lineage data]"
    # build adjacency and find longest chains
    children: dict[str, list[str]] = defaultdict(list)
    bpb_map: dict[str, float | None] = {}
    for row in rows:
        p, c = row["parent_run_id"], row["child_run_id"]
        children[p].append(c)
        bpb_map[c] = row.get("child_bpb")
    # collect all unique nodes up to max_nodes
    seen: set[str] = set()
    edges: list[tuple[str, str]] = []
    for row in rows:
        p, c = row["parent_run_id"], row["child_run_id"]
        if len(seen) >= max_nodes:
            break
        seen.add(p)
        seen.add(c)
        edges.append((p, c))
    lines = ["graph TD"]
    for node in sorted(seen):
        mid = _mermaid_id(node)
        short = _truncate_label(node, 24)
        bpb = bpb_map.get(node)
        if bpb is not None:
            lines.append(f'    {mid}["{short}<br/>{bpb:.4f}"]')
        else:
            lines.append(f'    {mid}["{short}"]')
    for p, c in edges:
        lines.append(f"    {_mermaid_id(p)} --> {_mermaid_id(c)}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests and verify all pass**

Run: `python -m pytest tests/test_viz.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/conker_ledger/ledger.py tests/test_viz.py
git commit -m "feat: add render_lineage_mermaid for warm-start ancestry diagrams"
```

---

### Task 9: Add `render_survival_mermaid`

**Files:**
- Modify: `src/conker_ledger/ledger.py` (add after `render_lineage_mermaid`)

- [ ] **Step 1: Write tests for survival mermaid**

Append to `tests/test_viz.py` and add `render_survival_mermaid` to the import:

```python
def test_render_survival_mermaid_basic():
    rows = [
        {"status": "bridge_only"},
        {"status": "bridge_only"},
        {"status": "survived_full_eval"},
        {"status": "survived_full_eval"},
        {"status": "survived_full_eval"},
        {"status": "full_eval_failed"},
    ]
    result = render_survival_mermaid(rows)
    assert result.startswith("graph LR")
    assert "6" in result  # total bridge
    assert "3" in result  # full eval attempted
    assert "-->" in result


def test_render_survival_mermaid_empty():
    result = render_survival_mermaid([])
    assert "graph LR" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_viz.py::test_render_survival_mermaid_basic -v`
Expected: ImportError

- [ ] **Step 3: Implement `render_survival_mermaid`**

Add to `ledger.py`:

```python
def render_survival_mermaid(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "graph LR\n    empty[No survival data]"
    total = len(rows)
    survived = sum(1 for r in rows if r.get("status") == "survived_full_eval")
    failed = sum(1 for r in rows if r.get("status") == "full_eval_failed")
    bridge_only = sum(1 for r in rows if r.get("status") == "bridge_only")
    attempted = survived + failed
    lines = [
        "graph LR",
        f'    A["Bridge Runs<br/>{total}"]',
        f'    B["Full Eval Attempted<br/>{attempted}"]',
        f'    C["Survived<br/>{survived}"]',
        f'    D["Failed<br/>{failed}"]',
        f'    E["Bridge Only<br/>{bridge_only}"]',
        "    A --> B",
        "    A --> E",
        "    B --> C",
        "    B --> D",
        "    style C fill:#2ca02c,color:#fff",
        "    style D fill:#c23b22,color:#fff",
        "    style E fill:#7f7f7f,color:#fff",
    ]
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests and verify all pass**

Run: `python -m pytest tests/test_viz.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/conker_ledger/ledger.py tests/test_viz.py
git commit -m "feat: add render_survival_mermaid for pipeline funnel diagram"
```

---

### Task 10: Update `write_report_bundle` and README template

**Files:**
- Modify: `src/conker_ledger/ledger.py` (update `write_report_bundle` function, lines 358-483)

- [ ] **Step 1: Write test for updated report bundle**

Append to `tests/test_viz.py`:

```python
import json
from conker_ledger.ledger import scan_results, write_report_bundle


def test_report_bundle_produces_new_files(tmp_path: Path):
    # Create minimal test data: one bridge + one full_eval for the same run
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    bridge = {
        "model": {
            "test_bpb": 0.55,
            "saved_state_path": "/tmp/fam_a_seed42.npz",
            "loaded_state_path": "/tmp/parent_seed42.npz",
            "seed": 42,
        },
        "quantization": [],
    }
    full_eval = {
        "eval_bpb": 0.56,
        "state_npz": "/tmp/fam_a_seed42.npz",
        "quant_bits": 0,
    }
    (src_dir / "fam_a_seed42_2026-03-28.json").write_text(json.dumps(bridge))
    (src_dir / "fam_a_seed42_fullval_test_none_2026-03-28.json").write_text(json.dumps(full_eval))

    out_dir = tmp_path / "report"
    write_report_bundle(src_dir, out_dir)

    assert (out_dir / "survival_status.svg").exists()
    assert (out_dir / "delta_fp16_histogram.svg").exists()
    assert (out_dir / "bridge_vs_full_grouped.svg").exists()
    readme = (out_dir / "README.md").read_text()
    assert "```mermaid" in readme
    assert "graph TD" in readme
    assert "graph LR" in readme
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_viz.py::test_report_bundle_produces_new_files -v`
Expected: FAIL — new files not yet produced

- [ ] **Step 3: Update `write_report_bundle`**

Replace the `write_report_bundle` function in `ledger.py` with:

```python
def write_report_bundle(root: Path, out_dir: Path, *, top: int = 20) -> dict[str, Any]:
    scanned = scan_results(root)
    records = scanned["records"]
    top_full_eval = sort_records([r for r in records if r["kind"] == "full_eval"], "bpb")[:top]
    top_bridge = sort_records([r for r in records if r["kind"] == "bridge"], "bpb")[:top]
    survival = survival_rows(records)
    survival_non_bridge = [row for row in survival if row["status"] != "bridge_only"]
    failed = [row for row in survival if row["status"] == "full_eval_failed"]
    lineage = lineage_rows(records)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "scan_summary.json").write_text(
        dumps_json(
            {
                "root": scanned["root"],
                "record_count": scanned["record_count"],
                "by_kind": scanned["by_kind"],
                "family_count": scanned["family_count"],
                "top_families": scanned["top_families"],
                "skipped": scanned["skipped"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (out_dir / "top_full_eval.json").write_text(dumps_json(top_full_eval) + "\n", encoding="utf-8")
    (out_dir / "top_bridge.json").write_text(dumps_json(top_bridge) + "\n", encoding="utf-8")
    (out_dir / "survival.json").write_text(dumps_json(survival_non_bridge) + "\n", encoding="utf-8")
    (out_dir / "failed_full_eval.json").write_text(dumps_json(failed) + "\n", encoding="utf-8")
    (out_dir / "lineage.json").write_text(dumps_json(lineage) + "\n", encoding="utf-8")

    write_csv(out_dir / "top_full_eval.csv", top_full_eval, ["family_id", "run_id", "seed", "quant_label", "bpb", "artifact_bytes", "path"])
    write_csv(out_dir / "survival.csv", survival_non_bridge, ["family_id", "run_id", "seed", "bridge_fp16", "full_fp16", "bridge_int6", "full_int6", "delta_fp16", "delta_int6", "status"])
    write_csv(out_dir / "failed_full_eval.csv", failed, ["family_id", "run_id", "seed", "bridge_fp16", "bridge_int6", "status", "bridge_path"])

    # --- existing SVG charts (improved) ---
    full_labels = [f"{row['family_id']}:{row.get('quant_label')}" for row in top_full_eval[: min(12, len(top_full_eval))]]
    full_values = [row["bpb"] for row in top_full_eval[: min(12, len(top_full_eval))] if row.get("bpb") is not None]
    if full_values:
        write_bar_svg(out_dir / "top_full_eval.svg", "Top Full-Eval Rows", full_labels[: len(full_values)], full_values)

    gap_rows = [row for row in survival_non_bridge if row.get("bridge_fp16") is not None and row.get("full_fp16") is not None][:20]
    write_scatter_svg(
        out_dir / "bridge_vs_full_fp16.svg",
        "Bridge FP16 vs Full FP16",
        gap_rows,
        x_key="bridge_fp16",
        y_key="full_fp16",
        label_key="family_id",
        reference_line=True,
    )

    conker7_rows = [row for row in survival if str(row["family_id"]).startswith("conker7_")]
    conker7_with_bpb = [row for row in conker7_rows if row.get("bridge_fp16") is not None]
    write_bar_svg(
        out_dir / "conker7_bridge_fp16.svg",
        "Conker-7 Bridge FP16 Rows",
        [row["family_id"] for row in conker7_with_bpb],
        [row["bridge_fp16"] for row in conker7_with_bpb],
    )

    # --- new SVG charts ---
    # survival status pie
    survived_count = sum(1 for r in survival if r["status"] == "survived_full_eval")
    failed_count = len(failed)
    bridge_only_count = sum(1 for r in survival if r["status"] == "bridge_only")
    pie_labels = []
    pie_values: list[float] = []
    pie_colors = []
    if survived_count:
        pie_labels.append("survived_full_eval")
        pie_values.append(survived_count)
        pie_colors.append("#2ca02c")
    if failed_count:
        pie_labels.append("full_eval_failed")
        pie_values.append(failed_count)
        pie_colors.append("#c23b22")
    if bridge_only_count:
        pie_labels.append("bridge_only")
        pie_values.append(bridge_only_count)
        pie_colors.append("#7f7f7f")
    write_pie_svg(out_dir / "survival_status.svg", "Survival Status", pie_labels, pie_values, pie_colors)

    # delta histogram
    deltas = [row["delta_fp16"] for row in survival_non_bridge if row.get("delta_fp16") is not None]
    write_histogram_svg(out_dir / "delta_fp16_histogram.svg", "Bridge-to-Full Delta (FP16)", deltas)

    # grouped bar: bridge vs full by family
    family_best: dict[str, dict[str, Any]] = {}
    for row in survival_non_bridge:
        fid = row["family_id"]
        if row.get("bridge_fp16") is not None and row.get("full_fp16") is not None:
            if fid not in family_best or (row["full_fp16"] < family_best[fid]["full_fp16"]):
                family_best[fid] = row
    grouped_rows = sort_records(list(family_best.values()), "full_fp16")[:12]
    write_grouped_bar_svg(
        out_dir / "bridge_vs_full_grouped.svg",
        "Bridge vs Full-Eval by Family",
        grouped_rows,
        key_a="bridge_fp16",
        key_b="full_fp16",
        label_key="family_id",
    )

    # --- mermaid diagrams ---
    lineage_mermaid = render_lineage_mermaid(lineage)
    survival_mermaid = render_survival_mermaid(survival)

    # --- README ---
    summary_lines = [
        "# Public Backlog Report",
        "",
        f"- root: `{root}`",
        f"- normalized records: `{scanned['record_count']}`",
        f"- bridge rows: `{scanned['by_kind'].get('bridge', 0)}`",
        f"- full eval rows: `{scanned['by_kind'].get('full_eval', 0)}`",
        f"- study rows: `{scanned['by_kind'].get('study', 0)}`",
        f"- experiment families: `{scanned['family_count']}`",
        "",
        "## Headline",
        "",
    ]
    if top_full_eval:
        best = top_full_eval[0]
        summary_lines.append(
            f"- best normalized full eval in this backlog: `{best['family_id']}` `{best['quant_label']}` at `{best['bpb']:.6f} bpb`"
        )
    if failed:
        summary_lines.append(f"- full-eval failures detected after optimistic bridge results: `{len(failed)}`")
    summary_lines.extend(
        [
            "",
            "## Survival Pipeline",
            "",
            "```mermaid",
            survival_mermaid,
            "```",
            "",
            "## Lineage",
            "",
            "```mermaid",
            lineage_mermaid,
            "```",
            "",
            "## Files",
            "",
            "- `scan_summary.json`",
            "- `top_full_eval.json` / `top_full_eval.csv` / `top_full_eval.svg`",
            "- `top_bridge.json`",
            "- `survival.json` / `survival.csv` / `survival_status.svg`",
            "- `failed_full_eval.json` / `failed_full_eval.csv`",
            "- `lineage.json`",
            "- `bridge_vs_full_fp16.svg` / `bridge_vs_full_grouped.svg`",
            "- `delta_fp16_histogram.svg`",
            "- `conker7_bridge_fp16.svg`",
            "",
            "## Visuals",
            "",
            "### Survival Status",
            "",
            "![Survival status](./survival_status.svg)",
            "",
            "### Top Full-Eval Rows",
            "",
            "![Top full eval rows](./top_full_eval.svg)",
            "",
            "### Bridge vs Full-Eval FP16",
            "",
            "![Bridge vs full fp16](./bridge_vs_full_fp16.svg)",
            "",
            "### Bridge vs Full-Eval by Family",
            "",
            "![Bridge vs full grouped](./bridge_vs_full_grouped.svg)",
            "",
            "### Delta Distribution (FP16)",
            "",
            "![Delta histogram](./delta_fp16_histogram.svg)",
            "",
            "### Conker-7 Bridge Rows",
            "",
            "![Conker-7 bridge rows](./conker7_bridge_fp16.svg)",
        ]
    )
    if failed:
        summary_lines.extend(["", "## Failed Full-Eval Rows", ""])
        for row in failed[:20]:
            summary_lines.append(
                f"- `{row['family_id']}` seed `{row.get('seed')}` bridge fp16 `{row.get('bridge_fp16')}` bridge int6 `{row.get('bridge_int6')}`"
            )
    (out_dir / "README.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return {
        "scan_summary": {
            "record_count": scanned["record_count"],
            "by_kind": scanned["by_kind"],
            "family_count": scanned["family_count"],
        },
        "best_full_eval": top_full_eval[0] if top_full_eval else None,
        "failed_full_eval_count": len(failed),
        "report_dir": str(out_dir),
    }
```

- [ ] **Step 4: Run all tests**

Run: `python -m pytest tests/test_viz.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/conker_ledger/ledger.py tests/test_viz.py
git commit -m "feat: update write_report_bundle with new charts and mermaid diagrams"
```

---

### Task 11: Regenerate example report bundle and final verification

**Files:**
- Modify: `examples/conker-backlog-2026-03-28/*` (regenerated output)

Note: This task can only run if the original `conker/out` source data directory is available. If not, skip the regeneration and just verify the code works with test data.

- [ ] **Step 1: Check if source data is available**

Run: `ls conker/out/*.json 2>/dev/null | head -5`

If the directory doesn't exist, skip to step 3.

- [ ] **Step 2: Regenerate report (only if source data exists)**

Run: `python -m conker_ledger.cli report conker/out examples/conker-backlog-2026-03-28`

Verify the new files exist:

Run: `ls examples/conker-backlog-2026-03-28/*.svg`
Expected: Should show `survival_status.svg`, `delta_fp16_histogram.svg`, `bridge_vs_full_grouped.svg` in addition to existing SVGs.

Run: `grep "mermaid" examples/conker-backlog-2026-03-28/README.md`
Expected: Should show mermaid fence markers.

- [ ] **Step 3: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add examples/ tests/
git commit -m "chore: regenerate example report with improved visualizations"
```
