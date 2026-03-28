from __future__ import annotations

import json
from pathlib import Path

from conker_ledger.ledger import scan_results, write_report_bundle


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def test_scan_results_classifies_model_list_studies(tmp_path: Path):
    _write_json(
        tmp_path / "look4_boundary_2000_2026-03-20.json",
        {
            "title": "look4 boundary",
            "models": [
                {"label": "carver_base", "test_mean": 1.57},
                {"label": "carver_boundary", "test_mean": 2.45},
            ],
        },
    )

    scanned = scan_results(tmp_path)

    assert scanned["record_count"] == 1
    row = scanned["records"][0]
    assert row["kind"] == "study"
    assert row["best_label"] == "carver_base"
    assert row["best_metric"] == 1.57
    assert row["metric_name"] == "test_mean"


def test_write_report_bundle_includes_top_study_outputs(tmp_path: Path):
    _write_json(
        tmp_path / "look4_boundary_2000_2026-03-20.json",
        {
            "title": "look4 boundary",
            "models": [
                {"label": "carver_base", "test_mean": 1.57},
                {"label": "carver_boundary", "test_mean": 2.45},
            ],
        },
    )

    out_dir = tmp_path / "report"
    result = write_report_bundle(tmp_path, out_dir, top=10)

    assert result["scan_summary"]["record_count"] == 1
    assert (out_dir / "top_study.json").exists()
    assert (out_dir / "top_study.csv").exists()
    assert (out_dir / "top_study.svg").exists()
    readme = (out_dir / "README.md").read_text(encoding="utf-8")
    assert "best study quick-check" in readme
