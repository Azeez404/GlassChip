# Phase 2 Artifact Inventory (source of truth for the paper)

Read-only. No Phase 2 artifact is modified by the paper-analysis layer.

| Phase | Artifact | Type | Used by paper? | Source metric |
|---|---|---|---|---|
| 2A | counterfactual/phase2a_results.json | JSON | context only | τ median (394 s), OOS increment R² (~0.006) |
| 2B | observability_ablation/observability_ablation_results.json | JSON | **yes** | τ point per condition; residual OOS R² (5 models) + perm-null |
| 2B | observability_ablation/observability_ablation_table.csv | CSV | supplementary | per-condition summary |
| 2B | observability_ablation/fig1-3_*.png | PNG | superseded by fig02/03 | exploratory |
| 2C | phase2c_bootstrap/phase2c_bootstrap_results.json | JSON | **yes** | bootstrap τ median/CoV/CI; ratios vs F0; invalid % |
| 2C | phase2c_bootstrap/phase2c_bootstrap_table.csv | CSV | supplementary | analytic vs bootstrap |
| 2C | phase2c_bootstrap/fig1-3_*.png | PNG | superseded by fig02 | exploratory |
| 2D | phase2d_fleet/phase2d_results.json | JSON | **yes** | fleet τ stats; socket consistency; fidelity-vs-fleet |
| 2D | phase2d_fleet/phase2d_units.json | JSON | **yes** | per-unit τ (fig04/05 histogram) |
| 2D | phase2d_fleet/table1/2_*.md | MD | superseded by table04 | fleet + socket |
| 2D | phase2d_fleet/fig1-4_*.png | PNG | superseded by fig04/05 | exploratory |
| 2E | phase2e_streaming/phase2e_results.json | JSON | **yes** | OOS vs baseline alert; rel spread; power confound; runtime |
| 2E | phase2e_streaming/table1-3_*.md | MD | superseded by table04 | streaming |
| 2E | phase2e_streaming/fig1-5_*.png | PNG | superseded by fig06 | exploratory |
| raw | raw/a_fullperiod_10sec_58hosts_decomp/ | Parquet | never redistributed | SHA-256 9898170b…996e |
| V1 | src/baseline/classical_baseline.py | code | frozen model | ARX T[t+1]=αT[t]+βP[t]+γ |

The paper-analysis layer re-derives all paper tables/figures from the JSON source-of-truth files (never from the exploratory PNGs).
