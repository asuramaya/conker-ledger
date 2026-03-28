from __future__ import annotations

import math
from pathlib import Path
from conker_ledger.ledger import (
    _svg_escape,
    write_bar_svg,
    write_scatter_svg,
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
