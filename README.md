# conker-ledger

`conker-ledger` is the public validity-bundle and result-analysis companion to `conker` and `conker-detect`.

The likely sharper long-term scope is not “general lab analysis,” but “validity bundle packaging.” A concrete proposal for that narrowing is in [`docs/VALIDITY_PACKAGER.md`](./docs/VALIDITY_PACKAGER.md).

Where `conker-detect` asks:

- is this checkpoint structurally suspicious?
- is this artifact legal or leaking?
- which tensor drift matters?

`conker-ledger` asks:

- which runs actually worked?
- which bridge wins survived full eval?
- which recipes die on honest replay?
- what warm-start lineage produced the current frontier?
- which artifact stories were boundary bugs, invalid models, or clean strict descendants?

It is built for the backlog that accumulates in `conker/out`, but it is generic enough for other JSON-first research labs with bridge/full-eval workflows.

## What It Does

`conker-ledger` currently supports six commands:

1. `bundle`
- assemble a manifest-first validity bundle
- package claim metadata, metric evidence, provenance, and copied detector outputs
- write a portable `claim.json` / `evidence/` / `report/README.md` bundle
- summarize attached `conker-detect` JSONs into human-readable detector lines inside the bundle README

2. `scan`
- walk a directory of JSON outputs
- normalize bridge runs, full evals, and study/ablation reports
- emit a machine-readable ledger summary

3. `table`
- rank normalized records by metric
- filter by kind (`bridge`, `full_eval`, `study`)
- get a quick top-k view without writing a notebook

4. `survival`
- join bridge rows with their full-eval descendants
- show which runs survived, worsened, or failed with `NaN`
- surface the exact gap between local search metrics and honest eval

5. `lineage`
- trace warm-start ancestry through `loaded_state_path -> saved_state_path`
- identify which branches descend from which checkpoints

6. `report`
- write a public report bundle with JSON, CSV, SVG, and a short README
- useful for publishing backlog state without a notebook

## Install

```bash
pip install .
```

Or run directly:

```bash
python -m conker_ledger.cli ...
```

## Usage

Assemble a validity bundle from explicit evidence:

```bash
conker-ledger bundle manifest.json out/validity-bundle
```

Detect-generated handoff shape:

```json
{
  "bundle_id": "parameter-golf-pr-1028",
  "claim": "claim.json",
  "metrics": "metrics.json",
  "provenance": "provenance.json",
  "audits": "audits.json",
  "attachments": [
    {
      "source": "../detect-out/submission.json",
      "dest": "audits/tier1/submission.json"
    },
    {
      "source": "../detect-out/provenance.json",
      "dest": "audits/tier1/provenance.json"
    },
    {
      "source": "../detect-out/legality.json",
      "dest": "audits/tier3/legality.json"
    },
    {
      "source": "../detect-out/replay.json",
      "dest": "audits/tier3/replay.json"
    }
  ]
}
```

That shape matches the detector-side handoff files:

- `submission.json`
- `provenance.json`
- `legality.json`
- `replay.json`

Scan a backlog:

```bash
conker-ledger scan /path/to/conker/out
```

Show top full-eval rows:

```bash
conker-ledger table /path/to/conker/out --kind full_eval --metric bpb --top 20
```

Show bridge-vs-full survival:

```bash
conker-ledger survival /path/to/conker/out
```

Show checkpoint lineage:

```bash
conker-ledger lineage /path/to/conker/out
```

Write a public report bundle:

```bash
conker-ledger report /path/to/conker/out examples/conker-backlog-YYYY-MM-DD
```

## Current Scope

This tool is intentionally validity-first and backlog-second, not notebook-first.

It does not replace:

- `conker-detect` for checkpoint forensics
- `conker-detect` for structural or behavioral legality audits
- branch docs for scientific interpretation
- full custom analysis when a question is genuinely new

But it should replace ad hoc one-off scripts for the recurring questions:

- “what is the live frontier?”
- “which bridge improvements died later?”
- “which family actually scales?”
- “what did this row warm-start from?”

## Public Examples

This repo can carry public quick-check and report bundles generated from real experiment backlogs under `examples/`.

Current examples:

- [`examples/carver-quick-check-2026-03-28`](./examples/carver-quick-check-2026-03-28/report/README.md)
- [`examples/conker-artifact-quick-check-2026-03-28`](./examples/conker-artifact-quick-check-2026-03-28/report/README.md)
- [`examples/conker-backlog-2026-03-28`](./examples/conker-backlog-2026-03-28/README.md)
- [`examples/conker-frontier-reset-2026-03-28`](./examples/conker-frontier-reset-2026-03-28/report/README.md)

The `conker` examples are intentionally split:

- `conker-artifact-quick-check` is the artifact-boundary and invalidation layer
- `conker-backlog` is the run-history, lineage, and survival layer
- `conker-frontier-reset` is the reset-era strict-anchor bundle after the contaminated frontier died

## Brutal Example

If you want the point of validity packaging in one page, read the `conker` quick check:

- [`examples/conker-artifact-quick-check-2026-03-28`](./examples/conker-artifact-quick-check-2026-03-28/report/README.md)

The short version is ugly, and it kills a real submission: [parameter-golf PR #998](https://github.com/openai/parameter-golf/pull/998), opened on March 28, 2026.

That PR packaged `Conker-5 Tandem Residual Exact Experts (MLX, non-record)` and claimed:

- full held-out fp16 `val_bpb = 0.57180453`
- full held-out int6 `val_bpb = 0.57546632`
- artifact bytes `= 3,720,359`
- a supposedly "boringly valid" packaged run

- `conker4b_tandem` looked strong on score at `0.5718232495381582 bpb` on full eval, but its extracted causal mask still carried forbidden-region structure with `upper_plus_diag_frac = 0.04358700722704721`.
- `conker4b_strict` removed that leak completely and the score collapsed to `2.0971244136143423 bpb`.
- `conker6_mask_geometry` had smaller-looking forbidden mass, `upper_frac = 0.011201489739837839` and `diag_frac = 0.017354798229237627`, but replacing the learned mask with its Toeplitz mean still detonated `full_test_bpb` from `0.07209327818598087` to `5.752106388513692`.

There was also a separate artifact-boundary failure in the same branch family:

- an old tandem packed artifact bloated to `11.87 MB` because it incorrectly serialized regenerated deterministic substrate
- the corrected packed tandem artifact dropped to about `3.72 MB`
- the strict packed artifact also landed around `3.73 MB`

That is why `conker-ledger` tracks more than scores. The important public question is not just “what number did this branch claim?” It is also “what exactly was stored, and what class of artifact was this?”

That is the whole reason this repo exists:

- a branch can look frontier on paper and still be invalid
- a tiny illegal region can carry most of the win
- once the leak is removed, the miracle often turns back into an ordinary bad model

If a result dies the moment you enforce the rule it was supposed to satisfy, it was not a breakthrough. It was a side channel.
