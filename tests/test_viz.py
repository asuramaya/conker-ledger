from __future__ import annotations

import math
from pathlib import Path
from conker_ledger.ledger import (
    _svg_escape,
    _family_color,
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
    assert _svg_escape("a < b &amp; c > d") == "a &lt; b &amp;amp; c &gt; d"


def test_bar_svg_writes_file(tmp_path: Path):
    path = tmp_path / "bar.svg"
    write_bar_svg(path, "Test", ["alpha", "beta"], [0.5, 0.3])
    content = path.read_text()
    assert content.startswith("<svg")
    assert "Test" in content
    assert "alpha" in content


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
    from conker_ledger.ledger import _nice_ticks
    ticks = _nice_ticks(0.5, 0.6, 5)
    assert len(ticks) >= 2
    assert all(0.5 <= t <= 0.61 for t in ticks)


def test_bar_svg_has_gridlines(tmp_path: Path):
    path = tmp_path / "bar.svg"
    write_bar_svg(path, "Test", ["a", "b", "c"], [0.5, 0.3, 0.7])
    content = path.read_text()
    assert "stroke-dasharray" in content


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
    assert "-->" in result


def test_render_survival_mermaid_empty():
    result = render_survival_mermaid([])
    assert "graph LR" in result
