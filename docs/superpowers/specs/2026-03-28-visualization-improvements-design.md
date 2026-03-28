# Visualization Improvements Design

## Summary

Improve conker-ledger's report visualizations by upgrading existing SVG chart generators, adding three new SVG chart types, and embedding mermaid diagrams in the generated README. All changes are incremental within `ledger.py`. No new dependencies.

## Constraints

- Output must render natively on GitHub (SVGs inline, mermaid fenced blocks)
- No HTML/JS — pure SVG for charts, mermaid for structural diagrams
- No new Python dependencies — stdlib only
- All changes in `ledger.py` (Approach A: incremental, no module extraction)

## Section 1: SVG Styling Improvements

### Bar charts (`write_bar_svg`)

- Horizontal gridlines at regular intervals (light gray, dashed)
- Axis tick labels with actual values along the bottom axis
- Label truncation with ellipsis when labels exceed the left margin width
- Color coding: deterministic hash-based palette assigns a consistent fill color per family
- Value labels formatted to 4 decimal places (currently 6)

### Scatter plots (`write_scatter_svg`)

- X and Y axis tick labels at regular intervals (currently only min/max in footer)
- Light gray gridlines
- Diagonal y=x reference line for bridge-vs-full charts (shows gap direction)
- Color coding by family (same palette as bar charts)
- Label collision offset: labels that would overlap get nudged vertically

## Section 2: New SVG Chart Types

### Survival status pie chart (`write_pie_svg`)

- Segments: `survived_full_eval` (green), `full_eval_failed` (red), `bridge_only` (gray)
- Count and percentage labels on each segment
- Output file: `survival_status.svg`

### Delta histogram (`write_histogram_svg`)

- X axis: `delta_fp16` values (full_fp16 - bridge_fp16)
- Y axis: count of runs per bin
- Shows distribution of bridge-to-full degradation
- Output file: `delta_fp16_histogram.svg`

### Grouped bar chart (`write_grouped_bar_svg`)

- For each family with both bridge and full-eval data: two side-by-side horizontal bars
- Bridge bpb bar and full-eval bpb bar, color distinguished
- Limited to top N families (sorted by full-eval bpb)
- Output file: `bridge_vs_full_grouped.svg`

## Section 3: Mermaid Diagrams

### Lineage tree (`render_lineage_mermaid`)

- `graph TD` (top-down) flowchart
- Nodes: `run_id` (truncated for readability), annotated with bpb where available
- Edges: warm-start ancestry (`loaded_state_path` to `saved_state_path`)
- Limited to top lineage chains (longest/deepest) to stay readable
- Embedded as fenced `mermaid` block in generated README

### Survival status flow (`render_survival_mermaid`)

- `graph LR` (left-right) flowchart
- Shows: `bridge runs (N)` -> `full eval attempted (M)` -> branches to `survived (X)` / `failed (Y)`
- Aggregate-count Sankey-style pipeline funnel
- Embedded as fenced `mermaid` block in generated README

## Section 4: Integration

### Modified functions

- `write_bar_svg` — gridlines, tick labels, label truncation, color palette, 4dp formatting
- `write_scatter_svg` — gridlines, axis ticks, y=x reference line, color coding, label collision offset

### New functions

- `write_pie_svg(path, title, labels, values, colors)` — pie/doughnut chart
- `write_histogram_svg(path, title, values, bins)` — histogram chart
- `write_grouped_bar_svg(path, title, rows, key_a, key_b, label_key)` — grouped horizontal bar chart
- `render_lineage_mermaid(lineage_rows, max_chains)` — returns mermaid string
- `render_survival_mermaid(survival_rows)` — returns mermaid string

### Changes to `write_report_bundle`

- Calls `write_pie_svg` for survival status breakdown
- Calls `write_histogram_svg` for delta_fp16 distribution
- Calls `write_grouped_bar_svg` for bridge-vs-full family comparison
- Calls `render_lineage_mermaid` and `render_survival_mermaid`, embeds output in README
- Updates README template to reference new SVG files and include mermaid blocks

### New output files in report bundle

- `survival_status.svg`
- `delta_fp16_histogram.svg`
- `bridge_vs_full_grouped.svg`

### Files in README

Updated file listing and visuals section to include the three new SVGs and two mermaid blocks.
