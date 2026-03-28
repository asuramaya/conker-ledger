# conker-ledger

`conker-ledger` is the public experiment-memory and result-analysis companion to `conker` and `conker-detect`.

Where `conker-detect` asks:

- is this checkpoint structurally suspicious?
- is this artifact legal or leaking?
- which tensor drift matters?

`conker-ledger` asks:

- which runs actually worked?
- which bridge wins survived full eval?
- which recipes die on honest replay?
- what warm-start lineage produced the current frontier?

It is built for the backlog that accumulates in `conker/out`, but it is generic enough for other JSON-first research labs with bridge/full-eval workflows.

## What It Does

`conker-ledger` currently supports four commands:

1. `scan`
- walk a directory of JSON outputs
- normalize bridge runs, full evals, and study/ablation reports
- emit a machine-readable ledger summary

2. `table`
- rank normalized records by metric
- filter by kind (`bridge`, `full_eval`, `study`)
- get a quick top-k view without writing a notebook

3. `survival`
- join bridge rows with their full-eval descendants
- show which runs survived, worsened, or failed with `NaN`
- surface the exact gap between local search metrics and honest eval

4. `lineage`
- trace warm-start ancestry through `loaded_state_path -> saved_state_path`
- identify which branches descend from which checkpoints

5. `report`
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

This tool is intentionally backlog-first, not notebook-first.

It does not replace:

- `conker-detect` for checkpoint forensics
- branch docs for scientific interpretation
- full custom analysis when a question is genuinely new

But it should replace ad hoc one-off scripts for the recurring questions:

- “what is the live frontier?”
- “which bridge improvements died later?”
- “which family actually scales?”
- “what did this row warm-start from?”

## Public Example

This repo can carry public report bundles generated from real experiment backlogs under `examples/`.

Current example:

- [`examples/conker-backlog-2026-03-28`](./examples/conker-backlog-2026-03-28/README.md)
