"""GLASSCHIP-V2 Phase 2D - fleet-scale effective-tau generalization.

Estimate the frozen first-order ARX thermal parameter tau across the FULL
Summit fleet (58 hosts x 2 sockets) at FULL fidelity (F0), to test whether the
Phase 2B/2C observability result generalizes beyond the 20-unit subset. This is
generalization/context only - the controlled within-Summit ablation (2B/2C)
remains the causal evidence. No new model, no new dataset, no PINN.

Reuses, verbatim: Phase 2B `condition_segments`/`identify`/F0 definition and
Phase 2C `block_bootstrap_tau` (FIXED 640 s block -> no tau-derived circularity).

Validity criteria fixed BEFORE inspecting the distribution:
  * alpha in (0,1) (stable first-order) AND
  * >= 2000 ARX pairs, AND
  * bootstrap valid fits >= 20.
Units failing these are reported, never silently dropped.

Writes only under v2_research/summit/phase2d_fleet/. Nothing else modified.
"""
from __future__ import annotations

import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import polars as pl

sys.path.insert(0, str(Path("src").resolve()))
sys.path.insert(0, str(Path("v2_research/summit/observability_ablation").resolve()))
sys.path.insert(0, str(Path("v2_research/summit/phase2c_bootstrap").resolve()))
import observability_ablation as p2b   # noqa: E402
import phase2c_bootstrap as p2c        # noqa: E402
from baseline import ClassicalBaselineModel  # noqa: E402  (frozen, read-only)

OUT = Path("v2_research/summit/phase2d_fleet")
CLEANED = Path("v2_research/summit/derived/cleaned")
F0 = p2b.CONDITIONS["F0_full"]        # socket-mean temp, float, 10 s
MIN_PAIRS = 2000
DT = F0["dt"]
# Phase 2C confirmed fidelity ratios (tau(Fi)/tau(F0)) for the Q4 contrast
FIDELITY_RATIOS = {"F1_quant": 0.29, "F2_downsample": 2.31, "F3_tjmax": 0.72, "F4_combined": 0.89}


def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fleet_hosts():
    return sorted(p.name.split("=", 1)[1] for p in CLEANED.glob("host=*"))


def unit_estimate(df, socket):
    segs, _ = p2b.condition_segments(df, socket, F0)
    if not segs:
        return {"valid": False, "reason": "no segments"}
    n_pairs = int(sum(len(t) - 1 for t, _ in segs if len(t) >= 2))
    idr = p2b.identify(segs, DT)                       # analytic alpha/tau/CoV/CI
    if idr is None or idr.get("unstable", True) or not np.isfinite(idr.get("tau", np.nan)):
        return {"valid": False, "reason": "unstable alpha", "n_pairs": n_pairs}
    # residual std from the frozen model (read-only)
    m = ClassicalBaselineModel(dt_s=DT); m.fit(segs); met = m.evaluate(segs)
    boot = p2c.block_bootstrap_tau(segs, DT)           # same fixed-block method
    valid = (0 < idr["tau"]) and (n_pairs >= MIN_PAIRS) and boot and boot.get("valid", 0) >= 20
    return {"valid": bool(valid), "n_pairs": n_pairs,
            "alpha": float(-DT / np.exp(0) if False else np.exp(-DT / idr["tau"])),  # alpha=exp(-dt/tau)
            "tau_analytic": float(idr["tau"]), "analytic_cov": float(idr["cov"]),
            "analytic_ci_width": float(idr["ci_w"]),
            "residual_std": float(met.residual_std), "increment_r2": float(met.increment_r2),
            "boot_tau_median": (boot.get("tau_median") if boot else None),
            "boot_cov": (boot.get("tau_cov") if boot else None),
            "boot_ci95": (boot.get("tau_ci95") if boot else None),
            "boot_invalid_frac": (boot.get("invalid_frac") if boot else None),
            "reason": None if valid else "below MIN_PAIRS or few boot fits"}


def stats(a):
    a = np.asarray(a, float); a = a[np.isfinite(a)]
    if a.size == 0:
        return {}
    return {"n": int(a.size), "median": float(np.median(a)), "mean": float(np.mean(a)),
            "std": float(np.std(a)), "iqr": [float(np.percentile(a, 25)), float(np.percentile(a, 75))],
            "p05": float(np.percentile(a, 5)), "p95": float(np.percentile(a, 95)),
            "min": float(a.min()), "max": float(a.max())}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p2c.RNG = np.random.default_rng(0)                 # deterministic bootstrap
    hosts = fleet_hosts()
    subset = set(p2b.pilot_hosts(p2b.N_HOSTS))         # the original 20-unit hosts
    print(f"[{now()}] fleet hosts: {len(hosts)}; subset hosts: {sorted(subset)}")

    units = []
    t0 = time.time()
    for i, h in enumerate(hosts, 1):
        df = pl.read_parquet(CLEANED / f"host={h}" / "data.parquet")
        for s in (0, 1):
            r = unit_estimate(df, s)
            r["host"] = h; r["socket"] = s; r["in_subset"] = h in subset
            units.append(r)
        if i % 10 == 0 or i == len(hosts):
            (OUT / "phase2d_units.json").write_text(json.dumps(units, indent=2, default=str))
            nv = sum(u["valid"] for u in units)
            print(f"  [{i:>2}/{len(hosts)}] {h} valid_units={nv}/{len(units)} "
                  f"[{time.time()-t0:.0f}s]")

    valid = [u for u in units if u["valid"]]
    tau = [u["tau_analytic"] for u in valid]
    btau = [u["boot_tau_median"] for u in valid if u["boot_tau_median"]]
    fleet = stats(tau)

    # subset vs fleet
    sub_tau = [u["tau_analytic"] for u in valid if u["in_subset"]]
    rest_tau = [u["tau_analytic"] for u in valid if not u["in_subset"]]

    # socket pairing
    byhost = {}
    for u in valid:
        byhost.setdefault(u["host"], {})[u["socket"]] = u["tau_analytic"]
    pairs = [(v[0], v[1]) for v in byhost.values() if 0 in v and 1 in v]
    if pairs:
        a0 = np.array([p[0] for p in pairs]); a1 = np.array([p[1] for p in pairs])
        corr = float(np.corrcoef(a0, a1)[0, 1]) if a0.size > 2 else None
        mad = float(np.median(np.abs(a0 - a1)))
        mrd = float(np.median(np.abs(a0 - a1) / ((a0 + a1) / 2)))
    else:
        corr = mad = mrd = None

    # Q4: fidelity bias vs natural fleet variation
    tau_med = fleet.get("median")
    fleet_rel_spread = (fleet.get("p95") / fleet.get("p05")) if fleet else None
    q4 = {"fleet_median_tau": tau_med,
          "fleet_p05_p95": [fleet.get("p05"), fleet.get("p95")],
          "fleet_p95_over_p05_ratio": fleet_rel_spread,
          "fleet_iqr_over_median": ((fleet["iqr"][1] - fleet["iqr"][0]) / tau_med) if fleet else None,
          "fidelity_ratios": FIDELITY_RATIOS,
          "quantization_swing_F2_over_F1": FIDELITY_RATIOS["F2_downsample"] / FIDELITY_RATIOS["F1_quant"],
          "note": "compare fidelity ratio range (0.29-2.31, ~8x swing) to natural fleet "
                  "p95/p05 ratio"}

    results = {"generated": now(), "n_hosts": len(hosts),
               "n_units_attempted": len(units), "n_units_valid": len(valid),
               "min_pairs": MIN_PAIRS, "dt_s": DT, "block_seconds": p2c.BLOCK_SECONDS, "B": p2c.B,
               "fleet_tau": fleet, "fleet_boot_tau": stats(btau),
               "invalid_units": [{"host": u["host"], "socket": u["socket"],
                                  "reason": u.get("reason"), "n_pairs": u.get("n_pairs")}
                                 for u in units if not u["valid"]],
               "subset_vs_fleet": {"subset": stats(sub_tau), "rest": stats(rest_tau),
                                   "n_subset_units": len(sub_tau)},
               "socket_consistency": {"paired_hosts": len(pairs), "corr": corr,
                                      "median_abs_diff_s": mad, "median_rel_diff": mrd},
               "q4_fidelity_vs_fleet": q4}
    (OUT / "phase2d_results.json").write_text(json.dumps(results, indent=2, default=str))
    (OUT / "phase2d_units.json").write_text(json.dumps(units, indent=2, default=str))
    make_tables(results); make_figures(results, valid)
    print(f"\nFLEET: valid {len(valid)}/{len(units)}  median tau={fleet.get('median'):.0f}s "
          f"IQR={fleet['iqr'][0]:.0f}-{fleet['iqr'][1]:.0f}  P05-P95={fleet['p05']:.0f}-{fleet['p95']:.0f}")
    print(f"socket corr={corr}  median_rel_diff={mrd}")
    print(f"[{now()}] done -> {OUT}")


def make_tables(r):
    f = r["fleet_tau"]; sc = r["socket_consistency"]
    t1 = ["| Metric | Value |", "|---|---:|",
          f"| Hosts attempted | {r['n_hosts']} |",
          f"| Sockets attempted | {r['n_units_attempted']} |",
          f"| Valid units | {r['n_units_valid']} |",
          f"| Median tau (s) | {f['median']:.1f} |",
          f"| Mean tau (s) | {f['mean']:.1f} |",
          f"| IQR (s) | {f['iqr'][0]:.0f} - {f['iqr'][1]:.0f} |",
          f"| P05 (s) | {f['p05']:.1f} |", f"| P95 (s) | {f['p95']:.1f} |"]
    t2 = ["| Statistic | Value |", "|---|---:|",
          f"| Paired hosts | {sc['paired_hosts']} |",
          f"| Socket correlation | {sc['corr']:.3f} |" if sc['corr'] is not None else "| Socket correlation | n/a |",
          f"| Median absolute difference (s) | {sc['median_abs_diff_s']:.1f} |",
          f"| Median relative difference | {sc['median_rel_diff']:.3f} |"]
    (OUT / "table1_fleet_summary.md").write_text("\n".join(t1))
    (OUT / "table2_socket_consistency.md").write_text("\n".join(t2))


def make_figures(r, valid):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    tau = np.array([u["tau_analytic"] for u in valid])
    sub = np.array([u["tau_analytic"] for u in valid if u["in_subset"]])
    rest = np.array([u["tau_analytic"] for u in valid if not u["in_subset"]])
    # Fig1: fleet distribution, subset marked
    fig, ax = plt.subplots(figsize=(8, 4))
    bins = np.linspace(min(tau.min(), 1), np.percentile(tau, 99), 40)
    ax.hist(tau, bins=bins, color="C0", alpha=0.6, label=f"fleet (n={tau.size})")
    ax.hist(sub, bins=bins, color="C3", alpha=0.7, label=f"2B/2C subset (n={sub.size})")
    ax.axvline(np.median(tau), color="k", ls="--", lw=1, label=f"fleet median {np.median(tau):.0f}s")
    ax.set_xlabel("effective tau (s)"); ax.set_ylabel("units"); ax.set_title("Fleet effective-tau distribution")
    ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(OUT / "fig1_fleet_tau_dist.png", dpi=110); plt.close(fig)
    # Fig2: paired socket tau
    byhost = {}
    for u in valid:
        byhost.setdefault(u["host"], {})[u["socket"]] = u["tau_analytic"]
    pairs = [(v[0], v[1]) for v in byhost.values() if 0 in v and 1 in v]
    if pairs:
        a0 = np.array([p[0] for p in pairs]); a1 = np.array([p[1] for p in pairs])
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.scatter(a0, a1, s=18, alpha=0.7)
        lim = [min(a0.min(), a1.min()), np.percentile(np.concatenate([a0, a1]), 99)]
        ax.plot(lim, lim, "k--", lw=1, label="y=x"); ax.set_xlim(lim); ax.set_ylim(lim)
        ax.set_xlabel("socket 0 tau (s)"); ax.set_ylabel("socket 1 tau (s)")
        ax.set_title(f"Paired socket tau (r={np.corrcoef(a0,a1)[0,1]:.2f}, n={len(pairs)})")
        ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(OUT / "fig2_paired_socket_tau.png", dpi=110); plt.close(fig)
    # Fig3: subset vs fleet (box)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.boxplot([sub, rest], tick_labels=[f"subset (n={sub.size})", f"rest of fleet (n={rest.size})"], showfliers=False)
    ax.set_ylabel("effective tau (s)"); ax.set_title("Original subset vs rest of fleet")
    fig.tight_layout(); fig.savefig(OUT / "fig3_subset_vs_fleet.png", dpi=110); plt.close(fig)
    # Fig4: fidelity bias vs fleet natural range
    fig, ax = plt.subplots(figsize=(8, 4))
    med = np.median(tau)
    ax.axhspan(np.percentile(tau, 5), np.percentile(tau, 95), color="C0", alpha=0.15, label="fleet P05-P95 (natural)")
    ax.axhline(med, color="C0", lw=1)
    for name, ratio in FIDELITY_RATIOS.items():
        ax.plot([name], [med * ratio], "rs"); ax.annotate(f"{ratio:.2f}x", (name, med * ratio), fontsize=8)
    ax.plot(["F0"], [med], "ko", label="F0 fleet median")
    ax.set_ylabel("tau (s)"); ax.set_title("Fidelity-induced tau bias vs natural fleet variation")
    ax.legend(fontsize=8); ax.tick_params(axis="x", rotation=15)
    fig.tight_layout(); fig.savefig(OUT / "fig4_fidelity_vs_fleet.png", dpi=110); plt.close(fig)


if __name__ == "__main__":
    main()
