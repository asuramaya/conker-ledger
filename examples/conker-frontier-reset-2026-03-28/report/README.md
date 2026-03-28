# Conker Frontier Reset

- bundle id: `conker-frontier-reset-2026-03-28`
- strongest justified claim: `Tier 1: strict frontier reset and first memory-first restart`
- requested label: `Tier-2 structurally audited`

## Headline

The old `Conker-5/7` frontier died for two separate reasons:

- one tandem artifact incorrectly packed regenerated deterministic substrate
- even after that packer bug was fixed, the saved tandem line still carried a small but decisive structural-control payload that the strict branch removes

This bundle captures the reset point after the contaminated frontier collapsed and the first strict `Conker-10` memory-first restart landed.

## Reset Metrics

- strict `Conker-4b` anchor: bridge `2.0589387458211483`, full eval `2.0971244136143423`, full eval int6 `2.105479516818886`
- `Conker-10` first memory-first pilot: bridge `2.2397347450734397`, packed memory bytes `12599296`, int6 `2.2608215482672507`
- `Conker-10a` falsification: memory only `6.089214172588595`, fixed blend `2.84364327924912`, fixed blend int6 `2.87529217250881`

## Artifact Boundary Findings

- broken tandem artifact: compressed `11874832` bytes, with `674398244` raw bytes of deterministic substrate accidentally packed and `278528` raw bytes of structural-control payload
- corrected tandem artifact: compressed `3723959` bytes, with deterministic substrate reduced to `22564` raw bytes but the same `278528` raw bytes of structural-control payload still present
- strict artifact: compressed `3730410` bytes, with only `26` raw bytes of deterministic residue and no structural-control payload

So the old `11.87 MB` artifact was a packing bug, while the later `3.72 MB` tandem artifact was an honestly packed but still invalid model.

## Structural Findings

- tandem `causal_mask` still had forbidden-region mass: `upper_plus_diag_frac = 0.04358700722704721`
- strict `causal_mask` is exactly clean: `upper_plus_diag_frac = 0.0`
- tandem vs strict `causal_mask` drift is small in cosine but large in effect:
  - `cosine_to_reference = 0.9988050701217123`
  - `l2_deviation = 0.04797664797049938`
  - `max_abs_deviation = 0.5975669622421265`

The strict branch therefore removes both classes of failure:

- accidental artifact-boundary serialization
- learned structural-control tensors crossing the causal boundary

## Memory Restart

`Conker-10` stores a sparse packed bigram table:

- shape `(1024, 1024)`
- nonzero count `94958`
- nonzero fraction `0.09055900573730469`
- total count mass `999999.0`

But the first restart is weak:

- the learned memory-first mixer only reaches `2.2397 bpb`
- forcing memory harder makes the branch worse, not better

So the post-reset story is not “the strict rebuild recovered the old frontier.” It did not. The reset is real, and the first memory-first replacement is still behind the strict anchor.

## Audit Coverage

- tier1: `pass`
- tier2: `warn`
- tier3: `missing`

## Attachments

- `audits/tier2/conker5_broken_artifact.json`
- `audits/tier2/conker5_corrected_artifact.json`
- `audits/tier2/conker4b_strict_artifact.json`
- `audits/tier2/conker4b_strict_bundle.json`
- `audits/tier2/conker4b_tandem_vs_strict_compare.json`
- `audits/tier2/conker10_bundle.json`
- `artifacts/source/conker4b_strict_bridge.json`
- `artifacts/source/conker4b_strict_fullval.json`
- `artifacts/source/conker4b_strict_fullval_int6.json`
- `artifacts/source/conker10_bridge.json`
- `artifacts/source/conker10a_memoryonly.json`
- `artifacts/source/conker10a_fixedblend.json`
