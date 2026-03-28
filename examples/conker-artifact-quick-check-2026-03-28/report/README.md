# Conker Artifact Quick Check

- scope: selected artifact-level quick checks over `conker4b_tandem`, `conker4b_strict`, and `conker6_mask_geometry`
- strongest supported claim: Tier 1 with Tier 2 warnings attached
- reason the ladder stops here: this public bundle does not include a runtime replay adapter or behavioral legality run
- target of this postmortem: [parameter-golf PR #998](https://github.com/openai/parameter-golf/pull/998), opened on March 28, 2026

## Why This Kills The PR

PR #998 packaged `Conker-5 Tandem Residual Exact Experts (MLX, non-record)` and claimed:

- pre-quant full held-out `val_bpb = 0.57180453`
- packaged int6 full held-out `val_bpb = 0.57546632`
- `3,720,359` artifact bytes
- a supposedly "boringly valid" packaged run

This bundle is the answer to that claim. The score was real. The package was real. The causal cleanliness was not.

## Headline Findings

- `conker4b_tandem` bridge/full metrics stayed near `0.562359 -> 0.571823 bpb`, but its extracted causal mask shows forbidden-region structure with `upper_plus_diag_frac = 0.04358700722704721`.
- `conker4b_strict` is much worse on score (`2.058939 -> 2.097124 bpb`), but its extracted causal mask is clean in the quick check: `upper_plus_diag_frac = 0.0`.
- The strict and tandem causal masks remain close in cosine terms, but the max absolute deviation is still material: `0.5975669622421265`.
- `conker6_mask_geometry` shows explicit forbidden structure in the saved mask audit: `upper_frac = 0.011201489739837839`, `diag_frac = 0.017354798229237627`.
- In the attached `conker6_mask_geometry` source summary, replacing the learned mask with its Toeplitz mean blows up `full_test_bpb` from `0.07209327818598087` to `5.752106388513692`.

## Included Evidence

- [`claim.json`](../claim.json)
- [`evidence/metrics.json`](../evidence/metrics.json)
- [`evidence/provenance.json`](../evidence/provenance.json)
- [`evidence/audits.json`](../evidence/audits.json)
- [`audits/tier2/conker6_mask_matrix.json`](../audits/tier2/conker6_mask_matrix.json)
- [`audits/tier2/conker6_mask_geometry.json`](../audits/tier2/conker6_mask_geometry.json)
- [`audits/tier2/conker4b_tandem_bundle.json`](../audits/tier2/conker4b_tandem_bundle.json)
- [`audits/tier2/conker4b_tandem_mask_matrix.json`](../audits/tier2/conker4b_tandem_mask_matrix.json)
- [`audits/tier2/conker4b_strict_mask_matrix.json`](../audits/tier2/conker4b_strict_mask_matrix.json)
- [`audits/tier2/conker4b_mask_compare_strict_vs_tandem.json`](../audits/tier2/conker4b_mask_compare_strict_vs_tandem.json)
- [`artifacts/source/conker4b_tandem_bridge.json`](../artifacts/source/conker4b_tandem_bridge.json)
- [`artifacts/source/conker4b_tandem_fullval.json`](../artifacts/source/conker4b_tandem_fullval.json)
- [`artifacts/source/conker4b_strict_bridge.json`](../artifacts/source/conker4b_strict_bridge.json)
- [`artifacts/source/conker4b_strict_fullval.json`](../artifacts/source/conker4b_strict_fullval.json)
- [`artifacts/source/conker6_mask_geometry.json`](../artifacts/source/conker6_mask_geometry.json)
- [`artifacts/scan_summary.json`](../artifacts/scan_summary.json)
- [`artifacts/report_README.md`](../artifacts/report_README.md)

## Reading This Bundle

- This is a thin public quick-check layer over saved artifacts.
- It is strong enough to surface obvious structural problems quickly.
- It is not a runtime legality certificate.
