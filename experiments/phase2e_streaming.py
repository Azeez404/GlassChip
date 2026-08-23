"""GLASSCHIP-V2 Phase 2E - streaming rolling-tau monitoring (leakage-free).

Question: once identified, is the effective thermal time constant tau useful as
an ONLINE, host-specific indicator of changing thermal dynamics - or is it just
an interpretable number? This is an operationalisation test, NOT a failure
predictor and NOT a physical-RC claim.

Frozen ARX only (T[n+1]=a T[n]+b P[n]+g, tau=-dt/ln a). Reuses Phase 2B
`condition_segments` for F0/F1/F2 fidelity. No new model family, no PINN, no
future data in any estimate, no cross-host leakage.

ALL RULES PRE-REGISTERED (fixed before evaluating the OOS period):
  WINDOW_S primary = 2560 s (>= ~5x fleet-median tau -> identifiable); also
    640/1280 s for F0 window-sensitivity only.
  stride = window (non-overlapping); windows never cross a collection gap.
  a window is valid if it has >= 0.6*W pairs and yields alpha in (0,1).
  baseline = first 50% of a unit's chronological windows (frozen); OOS = last 50%.
  robust z = (tau - baseline_median) / (1.4826*MAD + EPS).
  ALERT window: |z| > Z_THRESH (=3.5). PERSISTED alert: >= PERSIST_N (=2) consecutive.
  unit included if >= MIN_WINDOWS (=12) total with >=4 baseline and >=4 OOS.
Null: apply the identical rule to the BASELINE windows -> natural false-alarm
rate under stable operation (block-preserving, same unit, no shuffling of rows).
Confound: correlation of |z| with |power_window - baseline_power_median|.

Writes only under v2_research/summit/phase2e_streaming/.
"""
from __future__ import annotations

import os
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import polars as pl

import phase2b_ablation as p2b  # noqa: E402

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

OUT = _REPO / "artifacts/results"
CLEANED = Path(os.environ.get("GLASSCHIP_SUMMIT_DERIVED", _REPO / "data/summit/derived/cleaned"))
CONDS = {k: p2b.CONDITIONS[k] for k in ("F0_full", "F1_quantized", "F2_downsampled")}
WINDOW_S_PRIMARY = 2560.0
WINDOW_S_SENS = [640.0, 1280.0]        # F0-only window sensitivity
Z_THRESH = 3.5
PERSIST_N = 2
MIN_WINDOWS = 12
EPS = 1e-9


def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fleet_hosts():
    return sorted(p.name.split("=", 1)[1] for p in CLEANED.glob("host=*"))


def ols_alpha(T, P, y):
    X = np.column_stack([T, P, np.ones_like(T)])
    try:
        return float(np.linalg.solve(X.T @ X, X.T @ y)[0])
    except np.linalg.LinAlgError:
        return np.nan


def rolling_windows(segs, dt, window_s):
    """Non-overlapping windows within contiguous segments -> list of
    (tau, mean_power, mean_temp) in chronological order. No gap crossing."""
    W = max(8, int(round(window_s / dt)))
    minp = int(0.6 * W)
    out = []
    for t, p in segs:
        L = len(t)
        for s in range(0, L - 1, W):            # step by W (non-overlapping)
            e = min(s + W, L)
            if e - s < minp + 1:
                continue
            T, P, yv = t[s:e - 1], p[s:e - 1], t[s + 1:e]
            a = ols_alpha(T, P, yv)
            if 0.0 < a < 1.0:
                out.append((-dt / np.log(a), float(np.mean(p[s:e])), float(np.mean(t[s:e]))))
    return out


def monitor_unit(windows):
    """Split 50/50, compute baseline med/MAD, robust z for OOS and baseline,
    persisted-alert rates, and power-confound correlation."""
    if len(windows) < MIN_WINDOWS:
        return None
    tau = np.array([w[0] for w in windows]); pw = np.array([w[1] for w in windows])
    h = len(windows) // 2
    base_t, oos_t = tau[:h], tau[h:]
    base_p = pw[:h], pw[h:]
    if len(base_t) < 4 or len(oos_t) < 4:
        return None
    med = np.median(base_t); mad = np.median(np.abs(base_t - med))
    scale = 1.4826 * mad + EPS

    def zrun(vals):
        z = np.abs(vals - med) / scale
        alert = z > Z_THRESH
        # persisted: mark windows that are part of a run of >=PERSIST_N consecutive alerts
        persisted = np.zeros_like(alert)
        i = 0
        while i < len(alert):
            if alert[i]:
                j = i
                while j < len(alert) and alert[j]:
                    j += 1
                if j - i >= PERSIST_N:
                    persisted[i:j] = True
                i = j
            else:
                i += 1
        return float(np.mean(persisted)), float(np.median(np.abs(vals - med)))

    oos_rate, oos_madev = zrun(oos_t)
    base_rate, _ = zrun(base_t)          # null: same rule on baseline windows
    # power confound: |z_oos| vs |power_oos - baseline power median|
    base_pmed = np.median(pw[:h])
    z_oos = np.abs(oos_t - med) / scale
    dpow = np.abs(pw[h:] - base_pmed)
    conf = float(np.corrcoef(z_oos, dpow)[0, 1]) if z_oos.std() > 0 and dpow.std() > 0 else np.nan
    return {"n_windows": len(windows), "baseline_tau_median": float(med),
            "baseline_tau_mad": float(mad), "oos_tau_median": float(np.median(oos_t)),
            "oos_tau_madev": oos_madev, "oos_alert_rate": oos_rate,
            "baseline_alert_rate": base_rate, "power_confound_corr": conf,
            "baseline_rel_spread": float(mad / (med + EPS))}


def run_condition(frames, hosts, cond, window_s):
    units = []
    for h in hosts:
        for s in (0, 1):
            segs, _ = p2b.condition_segments(frames[h], s, cond)
            if not segs:
                continue
            w = rolling_windows(segs, cond["dt"], window_s)
            m = monitor_unit(w)
            if m:
                m["host"] = h; m["socket"] = s; units.append(m)
    return units


def agg(units, key):
    v = np.array([u[key] for u in units if u.get(key) is not None and np.isfinite(u[key])])
    return {"n": int(v.size), "median": float(np.median(v)) if v.size else None,
            "p90": float(np.percentile(v, 90)) if v.size else None,
            "max": float(v.max()) if v.size else None} if v.size else {"n": 0}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    hosts = fleet_hosts()
    print(f"[{now()}] hosts: {len(hosts)}; primary window {WINDOW_S_PRIMARY:.0f}s")
    frames = {h: pl.read_parquet(CLEANED / f"host={h}" / "data.parquet") for h in hosts}

    results = {"generated": now(), "preregistered": {
        "window_s_primary": WINDOW_S_PRIMARY, "window_s_sensitivity": WINDOW_S_SENS,
        "z_thresh": Z_THRESH, "persist_n": PERSIST_N, "min_windows": MIN_WINDOWS,
        "baseline_split": "first 50% chronological", "stride": "non-overlapping",
        "null": "same rule applied to baseline windows (natural false-alarm rate)"},
        "conditions": {}, "window_sensitivity_F0": {}}
    example = None
    for cname, cond in CONDS.items():
        t0 = time.time()
        units = run_condition(frames, hosts, cond, WINDOW_S_PRIMARY)
        rates_oos = [u["oos_alert_rate"] for u in units]
        rates_base = [u["baseline_alert_rate"] for u in units]
        confs = [u["power_confound_corr"] for u in units if np.isfinite(u.get("power_confound_corr", np.nan))]
        spreads = [u["baseline_rel_spread"] for u in units]
        results["conditions"][cname] = {
            "n_units": len(units),
            "oos_alert_rate": agg(units, "oos_alert_rate"),
            "baseline_alert_rate": agg(units, "baseline_alert_rate"),
            "baseline_rel_spread_median": float(np.median(spreads)) if spreads else None,
            "power_confound_corr_median": float(np.median(confs)) if confs else None,
            "oos_minus_baseline_alert_median": float(np.median(np.array(rates_oos) - np.array(rates_base))),
            "frac_units_oos_gt_baseline": float(np.mean(np.array(rates_oos) > np.array(rates_base))),
            "units": units}
        if cname == "F0_full" and units:
            example = max(units, key=lambda u: u["n_windows"])  # host with most windows
        print(f"  {cname:<15} units={len(units)} oosAlert_med={np.median(rates_oos):.3f} "
              f"baseAlert_med={np.median(rates_base):.3f} relSpread={np.median(spreads):.3f} "
              f"powConf={np.median(confs) if confs else float('nan'):.3f} [{time.time()-t0:.0f}s]")
    # F0 window sensitivity
    for ws in WINDOW_S_SENS:
        units = run_condition(frames, hosts, CONDS["F0_full"], ws)
        rates = [u["oos_alert_rate"] for u in units]
        results["window_sensitivity_F0"][f"{int(ws)}s"] = {
            "n_units": len(units), "oos_alert_rate_median": float(np.median(rates)) if rates else None,
            "baseline_rel_spread_median": float(np.median([u["baseline_rel_spread"] for u in units])) if units else None}
        print(f"  [sens] F0 window {int(ws)}s units={len(units)} oosAlert_med="
              f"{np.median(rates) if rates else float('nan'):.3f}")

    # runtime feasibility (single rolling-tau cost)
    seg = p2b.condition_segments(frames[hosts[0]], 0, CONDS["F0_full"])[0]
    W = int(WINDOW_S_PRIMARY / 10); t, p = seg[0]
    T, P, y = t[:W - 1], p[:W - 1], t[1:W]
    t0 = time.perf_counter()
    for _ in range(1000):
        ols_alpha(T, P, y)
    results["runtime"] = {"per_rolling_tau_ms": (time.perf_counter() - t0) / 1000 * 1000,
                          "window_samples": W, "online": True,
                          "note": "single OLS on one window; no future data; trivially real-time "
                                  "vs 10 s arrival"}
    results["example_host"] = ({"host": example["host"], "socket": example["socket"]} if example else None)

    (OUT / "phase2e_streaming.json").write_text(json.dumps(results, indent=2, default=str))
    make_tables(results); make_figures(results, frames)
    print(f"[{now()}] done -> {OUT}")


def make_tables(r):
    c = r["conditions"]; f0 = c["F0_full"]
    t1 = ["| Metric (F0, primary window) | Value |", "|---|---:|",
          f"| Units evaluated | {f0['n_units']} |",
          f"| Baseline rel. spread (MAD/median) | {f0['baseline_rel_spread_median']:.3f} |",
          f"| OOS alert rate (median) | {f0['oos_alert_rate']['median']:.3f} |",
          f"| Baseline alert rate (median) | {f0['baseline_alert_rate']['median']:.3f} |",
          f"| OOS-minus-baseline alert (median) | {f0['oos_minus_baseline_alert_median']:.3f} |",
          f"| Units OOS>baseline alert | {100*f0['frac_units_oos_gt_baseline']:.0f}% |"]
    t2 = ["| Condition | OOS alert med | Baseline alert med | rel spread | power-confound corr |",
          "|---|---:|---:|---:|---:|"]
    for cn in ("F0_full", "F1_quantized", "F2_downsampled"):
        x = c[cn]
        t2.append(f"| {cn} | {x['oos_alert_rate']['median']:.3f} | "
                  f"{x['baseline_alert_rate']['median']:.3f} | {x['baseline_rel_spread_median']:.3f} | "
                  f"{x['power_confound_corr_median']:.3f} |")
    t3 = ["| F0 window | units | OOS alert med | baseline rel spread |", "|---|---:|---:|---:|",
          f"| {int(WINDOW_S_PRIMARY)}s | {f0['n_units']} | {f0['oos_alert_rate']['median']:.3f} | {f0['baseline_rel_spread_median']:.3f} |"]
    for ws, x in r["window_sensitivity_F0"].items():
        t3.append(f"| {ws} | {x['n_units']} | {x['oos_alert_rate_median']:.3f} | {x['baseline_rel_spread_median']:.3f} |")
    (OUT / "table1_fleet_streaming.md").write_text("\n".join(t1))
    (OUT / "table2_fidelity.md").write_text("\n".join(t2))
    (OUT / "table3_window_sensitivity.md").write_text("\n".join(t3))


def make_figures(r, frames):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    c = r["conditions"]; conds = list(c)
    # Fig1: example host rolling tau
    ex = r.get("example_host")
    if ex:
        segs, _ = p2b.condition_segments(frames[ex["host"]], ex["socket"], CONDS["F0_full"])
        w = rolling_windows(segs, 10.0, WINDOW_S_PRIMARY)
        tau = [x[0] for x in w]; pw = [x[1] for x in w]
        fig, ax = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
        ax[0].plot(tau, ".-", ms=3); ax[0].axvline(len(tau)//2, color="k", ls="--", lw=1, label="baseline|OOS")
        ax[0].set_ylabel("rolling tau (s)"); ax[0].legend(fontsize=7)
        ax[1].plot(pw, ".-", ms=3, color="C1"); ax[1].set_ylabel("window mean power (W)")
        ax[1].set_xlabel("window index (chronological)")
        fig.suptitle(f"Rolling tau - {ex['host']} p{ex['socket']}"); fig.tight_layout()
        fig.savefig(OUT / "fig1_example_rolling_tau.png", dpi=110); plt.close(fig)
    # Fig2: baseline vs OOS tau across fleet
    u0 = c["F0_full"]["units"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter([u["baseline_tau_median"] for u in u0], [u["oos_tau_median"] for u in u0], s=16, alpha=0.7)
    lim = [150, 1600]; ax.plot(lim, lim, "k--", lw=1, label="y=x"); ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("baseline tau median (s)"); ax.set_ylabel("OOS tau median (s)")
    ax.set_title("Baseline vs OOS rolling-tau (F0)"); ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(OUT / "fig2_baseline_vs_oos.png", dpi=110); plt.close(fig)
    # Fig3: alert rate across units
    fig, ax = plt.subplots(figsize=(8, 4))
    oos = sorted(u["oos_alert_rate"] for u in u0); base = sorted(u["baseline_alert_rate"] for u in u0)
    ax.plot(oos, label="OOS alert rate"); ax.plot(base, label="baseline alert rate (null)")
    ax.set_xlabel("unit (sorted)"); ax.set_ylabel("persisted-alert fraction")
    ax.set_title("Per-unit alert rate: OOS vs baseline null (F0)"); ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(OUT / "fig3_alert_rates.png", dpi=110); plt.close(fig)
    # Fig4: fidelity comparison
    fig, ax = plt.subplots(figsize=(7, 4))
    oosm = [c[cn]["oos_alert_rate"]["median"] for cn in conds]
    basem = [c[cn]["baseline_alert_rate"]["median"] for cn in conds]
    x = np.arange(len(conds)); ax.bar(x - 0.2, oosm, 0.4, label="OOS"); ax.bar(x + 0.2, basem, 0.4, label="baseline")
    ax.set_xticks(x); ax.set_xticklabels(conds, rotation=15); ax.set_ylabel("median alert rate")
    ax.set_title("Monitoring alert rate under telemetry fidelity"); ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(OUT / "fig4_fidelity_alerts.png", dpi=110); plt.close(fig)
    # Fig5: power confound distribution
    fig, ax = plt.subplots(figsize=(7, 4))
    confs = [u["power_confound_corr"] for u in u0 if u.get("power_confound_corr") is not None and np.isfinite(u["power_confound_corr"])]
    ax.hist(confs, bins=20, color="C2", alpha=0.7)
    ax.axvline(np.median(confs), color="k", ls="--", label=f"median {np.median(confs):.2f}")
    ax.set_xlabel("corr(|tau z|, |power deviation|) per unit"); ax.set_ylabel("units")
    ax.set_title("Is tau deviation explained by power regime? (F0)"); ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(OUT / "fig5_power_confound.png", dpi=110); plt.close(fig)


if __name__ == "__main__":
    main()
