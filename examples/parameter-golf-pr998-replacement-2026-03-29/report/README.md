# Validity Bundle

- bundle id: `parameter-golf-pr998-replacement-2026-03-29`
- strongest justified claim: `Tier 2: Fresh-process held-out replay confirmed`
- requested label: `Tier-2 targeted structural evidence attached`

## Audit Coverage

- tier1: `warn`
- tier2: `warn`
- tier3: `missing`

## Metrics

- fresh-process full bpb: `2.0124189795892984`

## Provenance

- run_id: `source_submission`
- submission_pr: `https://github.com/openai/parameter-golf/pull/998`
- source_repo: `https://github.com/asuramaya/conker`
- source_root: `/Users/asuramaya/Code/carving_machine_v3/conker-detect/examples/parameter-golf-pr998-replacement-2026-03-29/source_submission`
- source_commit: `c278523d8ea5a2dcb4e342d5c428ac389a50af6d`

## Attachments

- `audits/tier1/submission.json` <= `/Users/asuramaya/Code/carving_machine_v3/conker-detect/examples/parameter-golf-pr998-replacement-2026-03-29/handoff/reports/submission.json`
- `audits/tier1/provenance.json` <= `/Users/asuramaya/Code/carving_machine_v3/conker-detect/examples/parameter-golf-pr998-replacement-2026-03-29/handoff/reports/provenance.json`
- `audits/tier2/causal_mask_matrix.json` <= `/Users/asuramaya/Code/carving_machine_v3/conker-detect/examples/conker11_pr998_replacement_causal_matrix_2026-03-29.json`
- `audits/tier2/causal_mask_geometry.json` <= `/Users/asuramaya/Code/carving_machine_v3/conker-detect/examples/conker11_pr998_replacement_causal_geometry_2026-03-29.json`
- `artifacts/pr998_update.md` <= `/Users/asuramaya/Code/carving_machine_v3/conker-detect/examples/parameter-golf-pr998-replacement-2026-03-29/pr998_update.md`

## Detector Summaries

- `audits/tier1/submission.json` kind=`submission`
  verdict: `pass`
  checks: presence=pass, claim_consistency=pass, artifact_bytes=pass, protocol_shape=pass, data_boundary_signals=pass, reproducibility_surface=pass, patch_triage=unknown
- `audits/tier1/provenance.json` kind=`provenance`
  verdict: `warn`
  selection: submitted_run_id=`conker11_seed43_replacement_2026-03-29`, selection_mode=`best_of_k`
  checks: selection_disclosure=pass, dataset_fingerprints=pass, held_out_identity=pass

## Files

- `claim.json`
- `evidence/metrics.json`
- `evidence/provenance.json`
- `evidence/audits.json`
- `bundle_manifest.json`
- `report/README.md`
