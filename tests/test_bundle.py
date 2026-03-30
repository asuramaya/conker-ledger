from __future__ import annotations

import json
from pathlib import Path

import pytest

from conker_ledger.ledger import write_validity_bundle


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def test_write_validity_bundle_packages_detector_outputs(tmp_path: Path):
    manifest_dir = tmp_path / "manifest"
    _write_json(
        manifest_dir / "claim.json",
        {
            "candidate_id": "demo-submission",
            "requested_label": "Tier-3 behaviorally audited",
        },
    )
    _write_json(
        manifest_dir / "metrics.json",
        {
            "bridge": {"bpb": 0.78},
            "fresh_process_full": {"bpb": 0.79},
            "packed_artifact_full": {"bpb": 0.8},
        },
    )
    _write_json(
        manifest_dir / "provenance.json",
        {
            "run_id": "demo_seed7",
            "family_id": "demo_family",
            "submission_pr": "#123",
        },
    )
    _write_json(
        manifest_dir / "audits.json",
        {
            "tier1": {"status": "pass"},
            "tier2": {"status": "pass"},
            "tier3": {
                "status": "warn",
                "scope": "one_shot_runtime_handoff",
                "trust_level_requested": "strict",
                "trust_level_achieved": "basic",
                "trust_satisfied": False,
            },
        },
    )
    _write_json(
        manifest_dir / "legality.json",
        {
            "tool": "conker-detect",
            "profile": "parameter-golf",
            "trust": {"requested": "strict", "achieved": "basic", "satisfied": False},
            "checks": {"normalization": {"covered": True, "pass": True}},
            "obligations": {"prefix_causal_distribution": {"status": "partially_covered"}},
        },
    )
    _write_json(
        manifest_dir / "submission_report.json",
        {
            "profile": "parameter-golf",
            "verdict": "warn",
            "submission": {"name": "Demo Submission"},
            "checks": {
                "presence": {"pass": True},
                "claim_consistency": {"pass": False},
            },
        },
    )
    _write_json(
        manifest_dir / "provenance_report.json",
        {
            "profile": "parameter-golf",
            "verdict": "warn",
            "provenance": {"submitted_run_id": "run-7", "selection_mode": "best_of_k"},
            "checks": {
                "selection_disclosure": {"pass": True},
                "dataset_fingerprints": {"pass": False},
            },
        },
    )
    _write_json(
        manifest_dir / "replay_report.json",
        {
            "profile": "parameter-golf",
            "aggregate": {"mean_bpb": 0.8},
            "repeatability": {"covered": True, "pass": True},
        },
    )
    _write_json(
        manifest_dir / "manifest.json",
        {
            "bundle_id": "demo-submission",
            "claim": "claim.json",
            "metrics": "metrics.json",
            "provenance": "provenance.json",
            "audits": "audits.json",
            "attachments": [
                {
                    "source": "submission_report.json",
                    "dest": "audits/tier1/submission.json",
                },
                {
                    "source": "provenance_report.json",
                    "dest": "audits/tier1/provenance.json",
                },
                {
                    "source": "legality.json",
                    "dest": "audits/tier3/legality.json",
                },
                {
                    "source": "replay_report.json",
                    "dest": "audits/tier3/replay.json",
                }
            ],
        },
    )

    out_dir = tmp_path / "bundle"
    result = write_validity_bundle(manifest_dir / "manifest.json", out_dir)

    assert result["bundle_id"] == "demo-submission"
    assert result["claim_level"]["level"] == 4
    assert (out_dir / "claim.json").exists()
    assert (out_dir / "evidence" / "metrics.json").exists()
    assert (out_dir / "evidence" / "provenance.json").exists()
    assert (out_dir / "evidence" / "audits.json").exists()
    assert (out_dir / "audits" / "tier3" / "legality.json").exists()
    assert (out_dir / "audits" / "tier1" / "submission.json").exists()
    assert (out_dir / "audits" / "tier1" / "provenance.json").exists()
    assert (out_dir / "audits" / "tier3" / "replay.json").exists()
    readme = (out_dir / "report" / "README.md").read_text(encoding="utf-8")
    assert "Tier 4: Structural audit passed" in readme
    assert "audits/tier3/legality.json" in readme
    assert "audits/tier1/submission.json" in readme
    assert "audits/tier1/provenance.json" in readme
    assert "audits/tier3/replay.json" in readme
    assert "tier3 scope: `one_shot_runtime_handoff`" in readme
    assert "tier3 trust: requested=`strict`, achieved=`basic`, satisfied=`False`" in readme
    assert "kind=`submission`" in readme
    assert "kind=`provenance`" in readme
    assert "kind=`replay`" in readme
    assert "trust: requested=`strict`, achieved=`basic`, satisfied=`False`" in readme


def test_write_validity_bundle_rejects_escape_destinations(tmp_path: Path):
    manifest_dir = tmp_path / "manifest"
    _write_json(manifest_dir / "source.json", {"ok": True})
    _write_json(
        manifest_dir / "manifest.json",
        {
            "claim": {},
            "metrics": {},
            "provenance": {},
            "audits": {},
            "attachments": [
                {
                    "source": "source.json",
                    "dest": "../escape.json",
                }
            ],
        },
    )

    with pytest.raises(ValueError):
        write_validity_bundle(manifest_dir / "manifest.json", tmp_path / "bundle")
