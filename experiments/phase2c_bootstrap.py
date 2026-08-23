"""GLASSCHIP-V2 Phase 2C - degradation-robust block-bootstrap tau identifiability.

Refines Phase 2B: separate (1) tau point-estimate BIAS from telemetry
degradation, (2) genuine sampling variance, (3) the analytic delta-method CI
artifact under quantization. Same 20 units, same 5 fidelity conditions, same
frozen ARX and Phase 2B preprocessing (imported, not re-defined).

Method: MOVING-BLOCK bootstrap that respects temporal dependence -- resample
CONTIGUOUS blocks of consecutive ARX pairs (never crossing a collection gap),
refit OLS on each resample -> distribution of alpha and tau = -dt/ln(alpha).
Naive iid row resampling is NOT used. Block length ~ one thermal time constant
(~640 s) so each block carries a full relaxation:
    L = round(640 / dt)  -> 64 pairs @10 s, 32 @20 s.

OLS on each resample is O(#blocks) via per-segment PREFIX SUMS of the 9 cross-
products (no full re-fit over all rows). Physically invalid fits (alpha not in
(0,1)) are rejected exactly as Phase 2B; their fraction is reported.

Reads V1 (frozen) and the Phase 2B module read-only. Writes only under
v2_research/summit/phase2c_bootstrap/. Nothing else is modified.
"""
from __future__ import annotations

import os
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import polars as pl

# reuse Phase 2B preprocessing EXACTLY (same conditions, segmenting, host set)
import phase2b_ablation as p2b  # noqa: E402

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

OUT = _REPO / "artifacts/results"
CLEANED = Path(os.environ.get("GLASSCHIP_SUMMIT_DERIVED", _REPO / "data/summit/derived/cleaned"))
P2B_JSON = _REPO / "artifacts/results/phase2b_ablation.json"
B = 500                      # bootstrap resamples per unit/condition
BLOCK_SECONDS = 640.0        # ~ one full-fidelity thermal time constant
RNG = np.random.default_rng(0)


def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")


def seg_prefix(segs):
    """Per contiguous segment -> prefix sums (len+1, 9) of ARX cross-products.
    Columns: TT,TP,T,PP,P,1,Ty,Py,y  (T=T[n],P=P[n],y=T[n+1])."""
    prefs, lens = [], []
    for t, p in segs:
        if len(t) < 2:
            continue
        T, P, y = t[:-1], p[:-1], t[1:]
        cols = np.column_stack([T * T, T * P, T, P * P, P, np.ones_like(T), T * y, P * y, y])
        prefs.append(np.vstack([np.zeros(9), np.cumsum(cols, axis=0)]))
        lens.append(len(T))
    return prefs, np.array(lens, int)


def alpha_from_sums(s):
    A = np.array([[s[0], s[1], s[2]], [s[1], s[3], s[4]], [s[2], s[4], s[5]]])
    b = np.array([s[6], s[7], s[8]])
    try:
        return float(np.linalg.solve(A, b)[0])
    except np.linalg.LinAlgError:
        return np.nan


def block_bootstrap_tau(segs, dt):
    """Return dict of bootstrap tau/alpha stats for one unit under one condition."""
    prefs, lens = seg_prefix(segs)
    if lens.size == 0:
        return None
    L = max(8, int(round(BLOCK_SECONDS / dt)))
    usable = lens >= L
    if not usable.any():                      # segments too short for this block length
        L = max(4, int(lens.max() // 2))
        usable = lens >= L
        if not usable.any():
            return {"valid": 0, "note": "segments shorter than min block"}
    # global PREF stack + per-segment global offsets
    offs = np.concatenate([[0], np.cumsum([p.shape[0] for p in prefs])])[:-1]
    PREF = np.vstack(prefs)
    total = int(lens[usable].sum())
    K = max(1, round(total / L))
    starts_max = np.maximum(lens - L, 0)      # inclusive max start per seg
    w = np.where(usable, starts_max + 1, 0).astype(float); w /= w.sum()
    seg_ids_all = np.arange(len(lens))

    taus, alphas = [], []
    for _ in range(B):
        sids = RNG.choice(seg_ids_all, size=K, p=w)
        st = (RNG.random(K) * (starts_max[sids] + 1)).astype(int)
        lo = offs[sids] + st
        hi = offs[sids] + st + L
        block = PREF[hi] - PREF[lo]           # (K,9)
        a = alpha_from_sums(block.sum(0))
        if 0.0 < a < 1.0:
            alphas.append(a); taus.append(-dt / np.log(a))
    taus = np.array(taus); alphas = np.array(alphas)
    valid = taus.size
    if valid < 20:
        return {"valid": int(valid), "block_len": L, "K": K, "note": "too few valid fits"}
    lo, hi = np.percentile(taus, [2.5, 97.5])
    return {"valid": int(valid), "invalid_frac": float(1 - valid / B),
            "block_len_pairs": L, "block_seconds": L * dt, "K_blocks": K,
            "tau_median": float(np.median(taus)), "tau_mean": float(np.mean(taus)),
            "tau_std": float(np.std(taus)), "tau_cov": float(np.std(taus) / np.mean(taus)),
            "tau_ci95": [float(lo), float(hi)], "tau_ci_width": float(hi - lo),
            "alpha_median": float(np.median(alphas)), "alpha_std": float(np.std(alphas))}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p2b_res = json.loads(P2B_JSON.read_text())
    hosts = p2b.pilot_hosts(p2b.N_HOSTS)      # identical unit selection
    print(f"[{now()}] hosts: {hosts}")
    frames = {h: pl.read_parquet(CLEANED / f"host={h}" / "data.parquet") for h in hosts}

    results = {"generated": now(), "hosts": hosts, "B": B,
               "block_seconds": BLOCK_SECONDS, "method": "moving-block bootstrap of "
               "consecutive ARX pairs within contiguous segments; OLS via per-segment "
               "prefix sums; alpha in (0,1) required; seed=0", "conditions": {}}
    table = []
    for cname, cond in p2b.CONDITIONS.items():
        t0 = time.time()
        boot_tau_meds, covs, ciws, invalids = [], [], [], []
        per_unit = []
        for h in hosts:
            for s in (0, 1):
                segs, _blocks = p2b.condition_segments(frames[h], s, cond)
                if len(segs) < 1:
                    continue
                r = block_bootstrap_tau(segs, cond["dt"])
                if r and r.get("valid", 0) >= 20:
                    boot_tau_meds.append(r["tau_median"]); covs.append(r["tau_cov"])
                    ciws.append(r["tau_ci_width"]); invalids.append(r["invalid_frac"])
                    per_unit.append({"host": h, "socket": s, **{k: r[k] for k in
                                     ("tau_median", "tau_cov", "tau_ci95", "tau_ci_width",
                                      "invalid_frac", "block_len_pairs")}})
        boot_tau_meds = np.array(boot_tau_meds); covs = np.array(covs); ciws = np.array(ciws)
        p2b_tau = p2b_res["conditions"][cname]["identifiability"]["tau_median"]
        p2b_cov = p2b_res["conditions"][cname]["identifiability"]["cov_median"]
        p2b_ciw = p2b_res["conditions"][cname]["identifiability"]["ci_width_median"]
        results["conditions"][cname] = {
            "dt_s": cond["dt"], "n_units": int(boot_tau_meds.size),
            "boot_tau_median_of_units": float(np.median(boot_tau_meds)),
            "boot_cov_median": float(np.median(covs)),
            "boot_ci_width_median": float(np.median(ciws)),
            "mean_invalid_frac": float(np.mean(invalids)),
            "phase2b_tau_median": p2b_tau, "phase2b_analytic_cov": p2b_cov,
            "phase2b_analytic_ci_width": p2b_ciw,
            "per_unit": per_unit}
        results["conditions"][cname]["boot_tau_dist_across_units"] = boot_tau_meds.tolist()
        print(f"  {cname:<15} bootTau_med={np.median(boot_tau_meds):.0f}s "
              f"bootCoV={np.median(covs):.4f} bootCIw={np.median(ciws):.1f}s "
              f"| p2bTau={p2b_tau:.0f} p2bCoV={p2b_cov:.4f} p2bCIw={p2b_ciw:.1f} "
              f"inval={np.mean(invalids):.3f} [{time.time()-t0:.0f}s]")

    # ratios vs F0
    f0 = results["conditions"]["F0_full"]["boot_tau_median_of_units"]
    for cname, c in results["conditions"].items():
        c["tau_ratio_vs_F0_bootstrap"] = float(c["boot_tau_median_of_units"] / f0)
        p2b_f0 = results["conditions"]["F0_full"]["phase2b_tau_median"]
        c["tau_ratio_vs_F0_phase2b"] = float(c["phase2b_tau_median"] / p2b_f0)
        table.append({"condition": cname, "tau_phase2b": round(c["phase2b_tau_median"], 1),
                      "tau_boot_median": round(c["boot_tau_median_of_units"], 1),
                      "boot_cov": round(c["boot_cov_median"], 4),
                      "boot_ci_width_s": round(c["boot_ci_width_median"], 1),
                      "analytic_cov_p2b": round(c["phase2b_analytic_cov"], 4),
                      "analytic_ci_width_p2b": round(c["phase2b_analytic_ci_width"], 1),
                      "tau_ratio_vs_F0": round(c["tau_ratio_vs_F0_bootstrap"], 3),
                      "invalid_boot_pct": round(100 * c["mean_invalid_frac"], 2)})
    results["table"] = table
    (OUT / "phase2c_bootstrap.json").write_text(json.dumps(results, indent=2, default=str))
    import csv
    with open(OUT / "phase2c_bootstrap_table.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0].keys())); w.writeheader(); w.writerows(table)
    make_figures(results)
    print(f"[{now()}] done -> {OUT}")


def make_figures(results):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    conds = list(results["conditions"]); C = results["conditions"]
    # Fig1: tau by condition - phase2b point vs bootstrap median + 95% CI
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(conds))
    p2b = [C[c]["phase2b_tau_median"] for c in conds]
    bm = [C[c]["boot_tau_median_of_units"] for c in conds]
    # CI band = median across units of per-unit CI endpoints
    lo = [np.median([u["tau_ci95"][0] for u in C[c]["per_unit"]]) for c in conds]
    hi = [np.median([u["tau_ci95"][1] for u in C[c]["per_unit"]]) for c in conds]
    ax.plot(x, p2b, "o-", label="Phase 2B point tau")
    ax.errorbar(x, bm, yerr=[np.array(bm) - lo, np.array(hi) - bm], fmt="s--",
                capsize=4, label="Phase 2C bootstrap median +/-95% CI")
    ax.set_xticks(x); ax.set_xticklabels(conds, rotation=20); ax.set_ylabel("tau (s)")
    ax.set_title("tau by fidelity: Phase 2B point vs robust bootstrap")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(OUT / "fig1_tau_p2b_vs_bootstrap.png", dpi=110); plt.close(fig)
    # Fig2: bootstrap tau distributions across units
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.boxplot([C[c]["boot_tau_dist_across_units"] for c in conds],
               tick_labels=conds, showfliers=False)
    ax.set_ylabel("bootstrap tau median per unit (s)")
    ax.set_title("Bootstrap tau distribution across Summit units by condition")
    ax.tick_params(axis="x", rotation=20); fig.tight_layout()
    fig.savefig(OUT / "fig2_bootstrap_tau_dist.png", dpi=110); plt.close(fig)
    # Fig3: analytic vs bootstrap CI width (the artifact-exposing figure)
    fig, ax = plt.subplots(figsize=(8, 4))
    an = [C[c]["phase2b_analytic_ci_width"] for c in conds]
    bo = [C[c]["boot_ci_width_median"] for c in conds]
    ax.plot(x, an, "o-", label="analytic delta-method CI width (2B)")
    ax.plot(x, bo, "s--", label="block-bootstrap CI width (2C)")
    ax.set_xticks(x); ax.set_xticklabels(conds, rotation=20); ax.set_ylabel("tau CI width (s)")
    ax.set_title("Analytic vs bootstrap uncertainty (exposes the quantization artifact)")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(OUT / "fig3_analytic_vs_bootstrap_ci.png", dpi=110); plt.close(fig)


if __name__ == "__main__":
    main()
