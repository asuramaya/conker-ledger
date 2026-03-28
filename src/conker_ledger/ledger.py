from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import csv


DATE_SUFFIX_RE = re.compile(r"_\d{4}-\d{2}-\d{2}$")
FULL_EVAL_SUFFIX_RE = re.compile(r"_fullval_(?:train|test)_[a-z0-9]+$")
SEED_RE = re.compile(r"_seed(\d+)")


def _json_default(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def dumps_json(value: Any) -> str:
    return json.dumps(value, indent=2, default=_json_default)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def finite_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        if math.isfinite(float(value)):
            return float(value)
        return None
    return None


def infer_run_id_from_stem(stem: str) -> str:
    stem = FULL_EVAL_SUFFIX_RE.sub("", stem)
    stem = DATE_SUFFIX_RE.sub("", stem)
    return stem


def infer_family_id(run_id: str) -> str:
    run_id = re.sub(r"_seed\d+", "", run_id)
    run_id = re.sub(r"_save$", "", run_id)
    return run_id


def parse_bridge_record(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    model = data.get("model", {}) if isinstance(data.get("model"), dict) else {}
    quant_rows = data.get("quantization", [])
    saved_state_path = model.get("saved_state_path")
    loaded_state_path = model.get("loaded_state_path")
    run_id = infer_run_id_from_stem(Path(saved_state_path).stem) if saved_state_path else infer_run_id_from_stem(path.stem)
    seed_match = SEED_RE.search(run_id)
    quant_by_bits: dict[str, float | None] = {}
    for row in quant_rows if isinstance(quant_rows, list) else []:
        bits = row.get("bits")
        key = f"int{int(bits)}" if isinstance(bits, (int, float)) else None
        if key:
            quant_by_bits[key] = finite_or_none(row.get("test_bpb"))
    return {
        "kind": "bridge",
        "path": str(path),
        "title": data.get("title"),
        "run_id": run_id,
        "family_id": infer_family_id(run_id),
        "seed": int(seed_match.group(1)) if seed_match else model.get("seed"),
        "bpb": finite_or_none(model.get("test_bpb")),
        "bits_per_token": finite_or_none(model.get("test_bits_per_token")),
        "loss": finite_or_none(model.get("test_eval_loss")),
        "train_time_sec": finite_or_none(model.get("train_time_sec")),
        "params": model.get("params"),
        "saved_state_path": saved_state_path,
        "loaded_state_path": loaded_state_path,
        "int4_bpb": quant_by_bits.get("int4"),
        "int6_bpb": quant_by_bits.get("int6"),
        "raw": {
            "preset": model.get("preset"),
            "variant": model.get("variant"),
            "scale": model.get("scale"),
            "learning_rate": model.get("learning_rate"),
        },
    }


def parse_full_eval_record(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    state_npz = data.get("state_npz")
    run_id = infer_run_id_from_stem(Path(state_npz).stem) if isinstance(state_npz, str) else infer_run_id_from_stem(path.stem)
    seed_match = SEED_RE.search(run_id)
    quant_bits = int(data.get("quant_bits", 0) or 0)
    quant_label = "fp16" if quant_bits == 0 else f"int{quant_bits}"
    artifact_bytes = data.get("artifact_bytes_zlib")
    return {
        "kind": "full_eval",
        "path": str(path),
        "title": data.get("title"),
        "run_id": run_id,
        "family_id": infer_family_id(run_id),
        "seed": int(seed_match.group(1)) if seed_match else None,
        "quant_label": quant_label,
        "quant_bits": quant_bits,
        "bpb": finite_or_none(data.get("eval_bpb")),
        "bits_per_token": finite_or_none(data.get("eval_bits_per_token")),
        "loss": finite_or_none(data.get("eval_loss")),
        "eval_tokens": data.get("eval_tokens"),
        "artifact_bytes": int(artifact_bytes) if isinstance(artifact_bytes, (int, float)) and math.isfinite(float(artifact_bytes)) else None,
        "state_npz": state_npz,
        "summary_json": data.get("summary_json"),
    }


def parse_study_record(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    variants = data.get("variants", [])
    return {
        "kind": "study",
        "path": str(path),
        "title": data.get("title"),
        "run_id": infer_run_id_from_stem(path.stem),
        "family_id": infer_family_id(infer_run_id_from_stem(path.stem)),
        "variant_count": len(variants) if isinstance(variants, list) else 0,
    }


def classify_record(path: Path, data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    if "eval_bpb" in data:
        return parse_full_eval_record(path, data)
    model = data.get("model")
    if isinstance(model, dict) and "test_bpb" in model:
        return parse_bridge_record(path, data)
    if "variants" in data:
        return parse_study_record(path, data)
    return None


def scan_results(root: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    skipped: list[str] = []
    for path in sorted(root.glob("*.json")):
        try:
            data = load_json(path)
            record = classify_record(path, data)
        except Exception as exc:  # pragma: no cover - defensive scan path
            skipped.append(f"{path.name}: {exc}")
            continue
        if record is None:
            skipped.append(path.name)
            continue
        records.append(record)

    by_kind = Counter(record["kind"] for record in records)
    by_family = Counter(record["family_id"] for record in records)
    return {
        "root": str(root),
        "record_count": len(records),
        "by_kind": dict(by_kind),
        "family_count": len(by_family),
        "top_families": by_family.most_common(20),
        "records": records,
        "skipped": skipped,
    }


def sort_records(records: list[dict[str, Any]], metric: str, *, ascending: bool = True) -> list[dict[str, Any]]:
    def key_fn(record: dict[str, Any]) -> tuple[int, float]:
        value = record.get(metric)
        if value is None:
            return (1, float("inf"))
        return (0, float(value))

    return sorted(records, key=key_fn, reverse=not ascending)


def survival_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"bridge": None, "full": {}})
    for record in records:
        if record["kind"] == "bridge":
            grouped[record["run_id"]]["bridge"] = record
        elif record["kind"] == "full_eval":
            grouped[record["run_id"]]["full"][record.get("quant_label") or "unknown"] = record

    rows: list[dict[str, Any]] = []
    for run_id, group in sorted(grouped.items()):
        bridge = group["bridge"]
        full = group["full"]
        bridge_bpb = bridge.get("bpb") if bridge else None
        bridge_int6 = bridge.get("int6_bpb") if bridge else None
        full_fp16 = full.get("fp16", {}).get("bpb") if "fp16" in full else None
        full_int6 = full.get("int6", {}).get("bpb") if "int6" in full else None
        status = "bridge_only"
        if full:
            if any(v.get("bpb") is None for v in full.values()):
                status = "full_eval_failed"
            else:
                status = "survived_full_eval"
        rows.append(
            {
                "run_id": run_id,
                "family_id": infer_family_id(run_id),
                "seed": bridge.get("seed") if bridge else None,
                "bridge_fp16": bridge_bpb,
                "bridge_int6": bridge_int6,
                "full_fp16": full_fp16,
                "full_int6": full_int6,
                "delta_fp16": None if bridge_bpb is None or full_fp16 is None else full_fp16 - bridge_bpb,
                "delta_int6": None if bridge_int6 is None or full_int6 is None else full_int6 - bridge_int6,
                "status": status,
                "bridge_path": bridge.get("path") if bridge else None,
                "full_paths": {k: v.get("path") for k, v in full.items()},
            }
        )
    return rows


def lineage_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        if record["kind"] != "bridge":
            continue
        loaded = record.get("loaded_state_path")
        saved = record.get("saved_state_path")
        if not loaded or not saved:
            continue
        parent_id = infer_run_id_from_stem(Path(loaded).stem)
        child_id = infer_run_id_from_stem(Path(saved).stem)
        rows.append(
            {
                "parent_run_id": parent_id,
                "child_run_id": child_id,
                "family_id": record["family_id"],
                "seed": record.get("seed"),
                "child_bpb": record.get("bpb"),
                "child_path": record.get("path"),
            }
        )
    return rows


def render_table(rows: list[dict[str, Any]], columns: list[str], top: int | None = None) -> str:
    if top is not None:
        rows = rows[:top]
    if not rows:
        return "(no rows)"
    widths = {col: max(len(col), *(len(str(row.get(col, ""))) for row in rows)) for col in columns}
    header = "  ".join(col.ljust(widths[col]) for col in columns)
    sep = "  ".join("-" * widths[col] for col in columns)
    body = [
        "  ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        for row in rows
    ]
    return "\n".join([header, sep, *body])


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) for column in columns})


def _svg_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


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
    )

    conker7_rows = [row for row in survival if str(row["family_id"]).startswith("conker7_")]
    write_bar_svg(
        out_dir / "conker7_bridge_fp16.svg",
        "Conker-7 Bridge FP16 Rows",
        [row["family_id"] for row in conker7_rows],
        [row["bridge_fp16"] for row in conker7_rows if row.get("bridge_fp16") is not None],
    )

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
        summary_lines.extend(
            [
                f"- best normalized full eval in this backlog: `{best['family_id']}` `{best['quant_label']}` at `{best['bpb']:.6f} bpb`",
            ]
        )
    if failed:
        summary_lines.append(f"- full-eval failures detected after optimistic bridge results: `{len(failed)}`")
    summary_lines.extend(
        [
            "",
            "## Files",
            "",
            "- `scan_summary.json`",
            "- `top_full_eval.json` / `top_full_eval.csv` / `top_full_eval.svg`",
            "- `top_bridge.json`",
            "- `survival.json` / `survival.csv` / `bridge_vs_full_fp16.svg`",
            "- `failed_full_eval.json` / `failed_full_eval.csv`",
            "- `lineage.json`",
            "- `conker7_bridge_fp16.svg`",
            "",
            "## Visuals",
            "",
            "### Top Full-Eval Rows",
            "",
            "![Top full eval rows](./top_full_eval.svg)",
            "",
            "### Bridge vs Full-Eval FP16",
            "",
            "![Bridge vs full fp16](./bridge_vs_full_fp16.svg)",
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
