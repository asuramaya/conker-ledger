# Public Backlog Report

- root: `/Users/asuramaya/Code/carving_machine_v3/conker/out`
- normalized records: `401`
- bridge rows: `366`
- full eval rows: `32`
- study rows: `3`
- experiment families: `229`

## Headline

- best normalized full eval in this backlog: `conker7_bidirectional_exact23_tw01_warmstart_tandem1500_seq256_steps1000` `fp16` at `0.528307 bpb`
- full-eval failures detected after optimistic bridge results: `3`

## Survival Pipeline

```mermaid
graph LR
    A["Bridge Runs<br/>363"]
    B["Full Eval Attempted<br/>14"]
    C["Survived<br/>11"]
    D["Failed<br/>3"]
    E["Bridge Only<br/>349"]
    A --> B
    A --> E
    B --> C
    B --> D
    style C fill:#2ca02c,color:#fff
    style D fill:#c23b22,color:#fff
    style E fill:#7f7f7f,color:#fff
```

## Lineage

```mermaid
graph TD
    conker4b_tandem_seq256_steps1500_lr5e4_seed42["conker4b_tandem_seq256_…"]
    conker7_bidirectional_exact23_tw01_start500_warmstart_tandem1500_seq256_steps1000_seed42["conker7_bidirectional_e…<br/>0.5122"]
    conker7_bidirectional_exact23_tw01_warmstart_tandem1500_seq256_steps1000_seed42_save["conker7_bidirectional_e…<br/>0.5183"]
    conker7_bidirectional_exact23_tw0p05_start500_warmstart_tandem1500_seq256_steps1000_seed42["conker7_bidirectional_e…<br/>0.5097"]
    conker7_bidirectional_exact23_tw0p05_warmstart_tandem1500_seq256_steps1000_seed42["conker7_bidirectional_e…<br/>0.5126"]
    conker4b_tandem_seq256_steps1500_lr5e4_seed42 --> conker7_bidirectional_exact23_tw01_start500_warmstart_tandem1500_seq256_steps1000_seed42
    conker4b_tandem_seq256_steps1500_lr5e4_seed42 --> conker7_bidirectional_exact23_tw01_warmstart_tandem1500_seq256_steps1000_seed42_save
    conker4b_tandem_seq256_steps1500_lr5e4_seed42 --> conker7_bidirectional_exact23_tw0p05_start500_warmstart_tandem1500_seq256_steps1000_seed42
    conker4b_tandem_seq256_steps1500_lr5e4_seed42 --> conker7_bidirectional_exact23_tw0p05_warmstart_tandem1500_seq256_steps1000_seed42
```

## Files

- `scan_summary.json`
- `top_full_eval.json` / `top_full_eval.csv` / `top_full_eval.svg`
- `top_bridge.json`
- `survival.json` / `survival.csv` / `survival_status.svg`
- `failed_full_eval.json` / `failed_full_eval.csv`
- `lineage.json`
- `bridge_vs_full_fp16.svg` / `bridge_vs_full_grouped.svg`
- `delta_fp16_histogram.svg`
- `conker7_bridge_fp16.svg`

## Visuals

### Survival Status

![Survival status](./survival_status.svg)

### Top Full-Eval Rows

![Top full eval rows](./top_full_eval.svg)

### Bridge vs Full-Eval FP16

![Bridge vs full fp16](./bridge_vs_full_fp16.svg)

### Bridge vs Full-Eval by Family

![Bridge vs full grouped](./bridge_vs_full_grouped.svg)

### Delta Distribution (FP16)

![Delta histogram](./delta_fp16_histogram.svg)

### Conker-7 Bridge Rows

![Conker-7 bridge rows](./conker7_bridge_fp16.svg)

## Failed Full-Eval Rows

- `conker7_bidirectional_exact23_tw01_start500_warmstart_tandem1500_seq256_steps1000` seed `42` bridge fp16 `0.5122250855951872` bridge int6 `0.524202795767721`
- `conker7_bidirectional_exact23_tw0p05_start500_warmstart_tandem1500_seq256_steps1000` seed `42` bridge fp16 `0.5097073605109663` bridge int6 `0.5220992522003182`
- `conker7_bidirectional_exact23_tw0p05_warmstart_tandem1500_seq256_steps1000` seed `42` bridge fp16 `0.5125641658720483` bridge int6 `0.5248642814343933`
