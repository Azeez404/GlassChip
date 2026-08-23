"""Phase 2F - F0-F4 measurement-quality ablation across ALL 116 sampled host-sockets.

ADDITIVE. This script imports the frozen Phase 2B ablation module and reuses its
condition definitions, segmentation, and identification verbatim. It does not modify
any frozen code, does not touch raw data, and writes only into this directory. The
canonical 20-unit Phase 2B artifact is left untouched.

Difference from Phase 2B: unit coverage only (116 host-sockets instead of 20), and
identifiability only (the pooled residual-learnability models are not re-run - they
are not needed for the paired per-unit analysis and are where the cost lies).

What this adds scientifically: Phase 2B reports condition-level medians. Here every
unit is tracked by (host, socket) so F0-F4 estimates are exactly PAIRED, which enables
  * the distribution of per-unit tau ratios (is the bias a constant factor?), and
  * rank preservation, Spearman rho(tau_F0, tau_Fk) (does a regime preserve the
    ORDERING of units?), which is invariant to monotone reparameterisation and so is
    immune to the tau-vs-alpha issue below.

Population-spread caution, enforced here: tau = -dt/ln(alpha) is strongly nonlinear
near alpha->1, so dispersion measured in tau-space can move for purely algebraic
reasons. Every spread statistic is therefore reported in BOTH tau-space and
alpha-space, plus the scale-free CV of (1-alpha).

Run:  python v2_research/summit/phase2f_fleet_ablation/phase2f_fleet_ablation.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

import phase2b_ablation as p2b  # noqa: E402  (frozen, imported read-only)

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

CLEANED = Path(os.environ.get("GLASSCHIP_SUMMIT_DERIVED", _REPO / "data/summit/derived/cleaned"))
OUT = _REPO / "artifacts/results"
SEED = 0
N_BOOT = 2000


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fleet_hosts() -> list[str]:
    return sorted(p.name.split("=", 1)[1] for p in CLEANED.glob("host=*"))


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Rank correlation without a scipy dependency (average ranks for ties)."""
    def rank(a):
        order = np.argsort(a, kind="mergesort")
        r = np.empty(len(a), float)
        r[order] = np.arange(len(a), dtype=float)
        # average ties
        sa = a[order]
        i = 0
        while i < len(sa):
            j = i
            while j + 1 < len(sa) and sa[j + 1] == sa[i]:
                j += 1
            if j > i:
                r[order[i:j + 1]] = np.mean(r[order[i:j + 1]])
            i = j + 1
        return r
    rx, ry = rank(np.asarray(x, float)), rank(np.asarray(y, float))
    rx = rx - rx.mean(); ry = ry - ry.mean()
    d = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / d) if d > 0 else float("nan")


def boot_ci(fn, *arrays, n=N_BOOT, seed=SEED, lo=2.5, hi=97.5):
    """Percentile bootstrap CI over paired units."""
    rng = np.random.default_rng(seed)
    n_u = len(arrays[0])
    vals = []
    for _ in range(n):
        idx = rng.integers(0, n_u, n_u)
        v = fn(*[a[idx] for a in arrays])
        if np.isfinite(v):
            vals.append(v)
    if not vals:
        return (float("nan"), float("nan"))
    return (float(np.percentile(vals, lo)), float(np.percentile(vals, hi)))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    hosts = fleet_hosts()
    subset = set(p2b.pilot_hosts(p2b.N_HOSTS))
    print(f"[{now()}] Phase 2F: {len(hosts)} hosts x 2 sockets x "
          f"{len(p2b.CONDITIONS)} conditions", flush=True)

    # ---- per-unit identification under every condition, kept PAIRED ----------
    units: dict[tuple[str, int], dict] = {}
    t0 = time.time()
    for i, h in enumerate(hosts, 1):
        df = pl.read_parquet(CLEANED / f"host={h}" / "data.parquet")
        for s in (0, 1):
            rec = {"host": h, "socket": s, "in_subset": h in subset, "tau": {},
                   "alpha": {}, "cov": {}, "valid": {}}
            for cname, cond in p2b.CONDITIONS.items():
                segs, _ = p2b.condition_segments(df, s, cond)
                ok, tau, alpha, cov = False, None, None, None
                if segs:
                    idr = p2b.identify(segs, cond["dt"])
                    if (idr and not idr.get("unstable", True)
                            and np.isfinite(idr.get("tau", np.nan))):
                        ok = True
                        tau = float(idr["tau"])
                        cov = float(idr["cov"])
                        alpha = float(np.exp(-cond["dt"] / tau))
                rec["valid"][cname] = ok
                rec["tau"][cname] = tau
                rec["alpha"][cname] = alpha
                rec["cov"][cname] = cov
            units[(h, s)] = rec
        if i % 10 == 0 or i == len(hosts):
            print(f"  [{i:>2}/{len(hosts)}] {h}  [{time.time()-t0:.0f}s]", flush=True)
            (OUT / "phase2f_units.json").write_text(
                json.dumps(list(units.values()), indent=2, default=str))

    ulist = list(units.values())
    (OUT / "phase2f_units.json").write_text(json.dumps(ulist, indent=2, default=str))

    conds = list(p2b.CONDITIONS)
    n_valid_all = sum(all(u["valid"].values()) for u in ulist)
    print(f"\n[{now()}] units total={len(ulist)}  valid in ALL five conditions="
          f"{n_valid_all}")

    # ---- paired analysis, F0 vs each degraded condition ----------------------
    F0 = "F0_full"
    analysis = {}
    for cname in conds:
        pair = [u for u in ulist if u["valid"][F0] and u["valid"][cname]]
        t0v = np.array([u["tau"][F0] for u in pair], float)
        tkv = np.array([u["tau"][cname] for u in pair], float)
        a0v = np.array([u["alpha"][F0] for u in pair], float)
        akv = np.array([u["alpha"][cname] for u in pair], float)
        ratio = tkv / t0v

        rho = spearman(t0v, tkv)
        rho_ci = boot_ci(spearman, t0v, tkv)

        def iqr(a):
            return float(np.percentile(a, 75) - np.percentile(a, 25))

        def cv1ma(a):  # scale-free dispersion of the per-step decay fraction
            x = 1.0 - a
            return float(np.std(x) / np.mean(x)) if np.mean(x) != 0 else float("nan")

        tau_iqr_ratio = iqr(tkv) / iqr(t0v) if iqr(t0v) else float("nan")
        a_iqr_ratio = iqr(akv) / iqr(a0v) if iqr(a0v) else float("nan")
        analysis[cname] = {
            "n_paired": len(pair),
            "tau_median": float(np.median(tkv)),
            "tau_iqr": iqr(tkv),
            "ratio_median": float(np.median(ratio)),
            "ratio_p05": float(np.percentile(ratio, 5)),
            "ratio_p95": float(np.percentile(ratio, 95)),
            "ratio_min": float(ratio.min()),
            "ratio_max": float(ratio.max()),
            "ratio_median_ci": boot_ci(lambda r: float(np.median(r)), ratio),
            "spearman_rho": rho,
            "spearman_ci95": rho_ci,
            "tau_iqr_ratio_vs_F0": tau_iqr_ratio,
            "alpha_iqr_ratio_vs_F0": a_iqr_ratio,
            "cv_1_minus_alpha": cv1ma(akv),
            "cv_1_minus_alpha_F0": cv1ma(a0v),
        }

    results = {
        "generated": now(), "seed": SEED, "n_boot": N_BOOT,
        "source": "imports frozen experiments/phase2b_ablation.py "
                  "(conditions, segmentation, identification unchanged)",
        "scope": "identifiability only; pooled residual models not re-run",
        "n_hosts": len(hosts), "n_units": len(ulist),
        "n_units_valid_all_conditions": n_valid_all,
        "conditions": {c: p2b.CONDITIONS[c] for c in conds},
        "paired_analysis": analysis,
    }
    (OUT / "phase2f_ablation_116.json").write_text(json.dumps(results, indent=2, default=str))

    # ---- report --------------------------------------------------------------
    print("\n=== PAIRED PER-UNIT ANALYSIS (116 sampled host-sockets) ===")
    hdr = (f"{'cond':16s} {'n':>4s} {'tau_med':>8s} {'ratio_med':>9s} "
           f"{'ratio_p05':>9s} {'ratio_p95':>9s} {'rho':>6s} {'rho 95% CI':>18s}")
    print(hdr)
    for c in conds:
        a = analysis[c]
        ci = f"[{a['spearman_ci95'][0]:+.3f},{a['spearman_ci95'][1]:+.3f}]"
        print(f"{c:16s} {a['n_paired']:>4d} {a['tau_median']:>8.1f} "
              f"{a['ratio_median']:>9.3f} {a['ratio_p05']:>9.3f} {a['ratio_p95']:>9.3f} "
              f"{a['spearman_rho']:>6.3f} {ci:>18s}")

    print("\n=== DISPERSION IN BOTH PARAMETERISATIONS (guards the tau-transform trap) ===")
    print(f"{'cond':16s} {'tau_IQR/F0':>11s} {'alpha_IQR/F0':>13s} "
          f"{'CV(1-alpha)':>12s} {'CV(1-a) F0':>11s}")
    for c in conds:
        a = analysis[c]
        print(f"{c:16s} {a['tau_iqr_ratio_vs_F0']:>11.3f} "
              f"{a['alpha_iqr_ratio_vs_F0']:>13.3f} {a['cv_1_minus_alpha']:>12.3f} "
              f"{a['cv_1_minus_alpha_F0']:>11.3f}")
    print(f"\nwritten: {OUT}/phase2f_results.json, {OUT}/phase2f_units.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
