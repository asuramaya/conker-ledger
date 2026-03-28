# Conker-Ledger As A Validity Packager

## Thesis

`conker-ledger` should not compete with `conker-detect` as a general-purpose lab analysis tool.

It fits better as a packager for validity evidence:

- gather the evidence a submission actually has
- normalize it into a portable bundle
- make the claim ladder legible
- surface what was audited and what was not

In that framing:

- `conker-detect` is the detector
- `conker-ledger` is the packager

## Why This Fits The Current Code

The existing `conker-ledger` implementation already does the packaging part better than the detection part:

- it scans JSON-first outputs into a normalized ledger
- it joins bridge rows with full-eval rows
- it traces lineage through warm-start ancestry
- it writes public report bundles with JSON, CSV, SVG, and a README

That is already close to a submission-validity bundle. The mismatch is the current product language:

- today: public experiment-memory and backlog-analysis companion
- better scope: validity-oriented packager for submission evidence

## Product Boundary

### Conker-Detect

Questions it should answer:

- is this tensor structurally suspicious?
- does this runtime protocol fail behavioral legality probes?
- is this checkpoint likely leaking or illegal?

Primary outputs:

- structural audit JSON
- behavioral legality JSON
- alerts on suspicious tensors or score-path behavior

### Conker-Ledger

Questions it should answer:

- what exactly is the claim?
- what evidence supports it?
- what survived honest replay?
- what audits were actually run?
- what remains unverified?

Primary outputs:

- a portable validity bundle
- a claim ladder
- provenance / lineage
- references to detector outputs
- a public-facing README that distinguishes verified facts from open risk

## Proposed Scope

`conker-ledger` should narrow from “general backlog analytics” to “validity bundle assembly.”

The main unit should be:

- one candidate
- one family
- one submission PR
- or one frontier report window

The key is explicit evidence packaging, not unconstrained exploratory analysis.

## Proposed Data Model

### Validity Bundle

A validity bundle should contain:

- `claim.json`
  - claimed score
  - claimed artifact bytes
  - claimed protocol
  - track / record status

- `evidence/metrics.json`
  - bridge metrics
  - fresh-process full metrics
  - packed-artifact metrics
  - eval timing
  - token counts

- `evidence/provenance.json`
  - run ids
  - seed
  - loaded state path
  - saved state path
  - parent lineage
  - source JSON paths

- `evidence/audits.json`
  - Tier-1 review status
  - Tier-2 structural audit references
  - Tier-3 behavioral audit references
  - explicit unrun / unavailable checks

- `artifacts/`
  - copied or linked summaries, not necessarily full checkpoints

- `report/README.md`
  - short narrative summary
  - claim ladder
  - pass / warn / fail style status

## Claim Ladder

This should be the core abstraction.

Every bundle should state the strongest surviving claim, in order:

1. bridge metric only
2. fresh-process held-out replay
3. packed-artifact replay
4. structural audit passed
5. behavioral legality audit passed

This is the validity equivalent of the current bridge/full survival view.

The bundle should say explicitly where the ladder stops.

Examples:

- “Bridge win only; no honest replay yet”
- “Fresh-process full eval confirmed; no packed artifact replay”
- “Packed replay confirmed; no behavioral legality audit”
- “Behaviorally audited under score-first TTT profile”

## Proposed Commands

The current commands are close, but validity packaging wants a more explicit surface.

### Keep

- `scan`
- `lineage`
- `report`

These remain useful internals.

### Reframe

- `table` becomes less central
- `survival` becomes a claim-ladder primitive, not a general chart

### Add

- `bundle`
  - create a validity bundle for one run, family, or manifest

- `claim`
  - summarize the highest justified claim level

- `audit-status`
  - merge available `conker-detect` outputs into the bundle

- `manifest init`
  - create a bundle manifest with explicit evidence paths

The important shift is:

- from open-ended backlog browsing
- to explicit packaging of a validity case

## Manifest-First Input

Today `conker-ledger` is scan-first:

- point it at a directory of JSON files

For validity packaging, it should also support manifest-first mode:

- explicit list of bridge JSONs
- explicit full-eval JSONs
- explicit audit JSONs
- optional lineage roots
- optional submission metadata

That matters because public submission repos often do not expose a whole lab backlog.

## Tier Mapping

This repo should align with the audit tiers proposed in `conker-detect`.

### Tier 1

Package:

- claim metadata
- logs
- protocol declaration
- reproducibility notes

### Tier 2

Package:

- structural audit reports from `conker-detect`
- checkpoint or tensor references

### Tier 3

Package:

- behavioral legality reports from `conker-detect`
- replay profile
- scope of replay, e.g. prefix-only vs full

The bundle should never blur these together. Missing evidence should stay visible.

## Recommended Positioning

Suggested product sentence:

`conker-ledger` is a validity-bundle packager for Conker-style submission workflows. It turns bridge metrics, honest replay results, lineage, and detector outputs into one portable evidence bundle.

That is a better fit than:

- “generic lab analysis tool”
- “notebook replacement”
- “public experiment memory”

Those are too broad and compete with many other tools. Validity packaging is narrower and sharper.

## Near-Term Refactor Path

The least disruptive path is:

1. Keep the current scanner and normalizers.
2. Add a manifest-aware bundle command.
3. Change report output to emphasize claim ladder and audit coverage.
4. Treat charts as supporting evidence, not the product center.
5. Link `conker-detect` audit outputs instead of re-implementing legality logic here.

This preserves the useful code while tightening the scope.

## Current Status

The first concrete step now exists:

- `conker-ledger bundle manifest.json out/validity-bundle`

That command packages:

- `claim.json`
- `evidence/metrics.json`
- `evidence/provenance.json`
- `evidence/audits.json`
- copied attachments such as `conker-detect` reports
- `report/README.md` with the inferred claim ladder

So the remaining work is no longer whether this direction is viable, but how much of the current scan/report surface should be reworded around validity instead of backlog browsing.

## What Not To Do

Do not turn `conker-ledger` into:

- another tensor-forensics tool
- another benchmark dashboard
- a universal notebook replacement
- a challenge-specific rules engine

Those either duplicate `conker-detect` or drag the repo back into general-purpose lab tooling.

## Bottom Line

If `conker-detect` becomes the community detector, `conker-ledger` should become the community packager for validity.

That gives a clean split:

- detect suspicious structure or runtime behavior
- package the evidence into a claim ladder
- show exactly what was verified, and what was not
