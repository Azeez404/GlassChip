"""Generate the 4 publication tables (markdown) from canonical loaded results.
Numbers are never hand-typed here - all come from load_all()."""
from __future__ import annotations
from glasschip import config as C
from glasschip.analysis.load_results import load_all


def _w(name, lines):
    (C.TAB_DIR / name).write_text("\n".join(lines) + "\n")


def make():
    C.TAB_DIR.mkdir(parents=True, exist_ok=True)
    d = load_all()
    fid = {f.condition: f for f in d["fidelity"]}
    res = {r.condition: r for r in d["residual"]}

    # Table 1 - conditions
    t1 = ["# Table 1. Measurement-quality conditions", "",
          "| Cond | Temperature | Sampling | Spatial | Note |", "|---|---|---|---|---|"]
    for k in C.COND_ORDER:
        c = C.COND_DESC[k]
        t1.append(f"| {k} | {c['temp']} | {c['samp']} | {c['spatial']} | {c['note']} |")
    _w("table01_conditions.md", t1)

    # Table 2 - tau identification
    t2 = ["# Table 2. Effective-tau identification (F0-F4)", "",
          "| Cond | tau point (s) | Bootstrap median (s) | Analytic CoV | Analytic CI (s) | "
          "Bootstrap CoV | Bootstrap CI (s) | ratio vs F0 | Invalid boot % |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for k in C.COND_ORDER:
        f = fid[k]
        t2.append(f"| {k} | {f.tau_point:.0f} | {f.tau_bootstrap:.0f} | {f.analytic_cov:.4f} | "
                  f"{f.analytic_ci_width:.1f} | {f.bootstrap_cov:.4f} | {f.bootstrap_ci_width:.1f} | "
                  f"{f.tau_ratio:.2f} | {f.invalid_boot_pct:.1f} |")
    _w("table02_tau_identification.md", t2)

    # Table 3 - residual prediction
    t3 = ["# Table 3. Out-of-sample residual prediction (R^2)", "",
          "| Cond | Persistence | Linear | HGB | LSTM | Physics-MLP | Perm-null p95 |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for k in C.COND_ORDER:
        r = res[k]
        lstm = f"{r.lstm:.3f}" if r.lstm is not None else "n/a"
        t3.append(f"| {k} | {r.persistence:.3f} | {r.linear:.3f} | {r.hgb:.3f} | {lstm} | "
                  f"{r.physics_mlp:.3f} | {r.null_p95:.3f} |")
    t3 += ["", "Note: the strongest model (HGB) reaches at most "
           f"{max(r.hgb for r in res.values()):.3f} out-of-sample and is not improved by higher "
           "measurement quality (degraded conditions are sometimes higher). Reported as "
           "'not materially learnable', never 'unlearnable'."]
    _w("table03_residual_prediction.md", t3)

    # Table 4 - fleet + streaming
    fl = d["fleet"]; st = d["streaming"]; f0 = st.per_window["F0_full"]
    t4 = ["# Table 4. Sampled-population (116 host-sockets) and streaming summary", "", "| Metric | Value |", "|---|---:|",
          f"| Valid sampled host-sockets | {fl.n_valid} / 116 |",
          f"| Median tau (s) | {fl.median:.0f} |", f"| Mean tau (s) | {fl.mean:.0f} |",
          f"| Std (s) | {fl.std:.0f} |", f"| IQR (s) | {fl.iqr[0]:.0f}-{fl.iqr[1]:.0f} |",
          f"| P05 / P95 (s) | {fl.p05:.0f} / {fl.p95:.0f} |",
          f"| Min / Max (s) | {fl.min:.0f} / {fl.max:.0f} |",
          f"| Socket correlation | {fl.socket_corr:.3f} |",
          f"| Median socket relative difference | {fl.socket_rel_diff:.3f} |",
          f"| Quantized (F1) tau (s) | {fl.quantized_tau:.0f}  (below sampled min {fl.min:.0f}) |",
          f"| Streaming OOS alert rate (F0) | {f0['oos']:.3f} |",
          f"| Streaming baseline/null alert rate (F0) | {f0['baseline']:.3f} |",
          f"| OOS - baseline alert (F0) | {f0['diff']:.4f} |",
          f"| Rolling-tau relative spread (F0) | {f0['rel_spread']:.3f} |",
          f"| Power-confound correlation (F0) | {f0['power_confound']:.3f} |",
          f"| Runtime per rolling-tau (ms) | {st.runtime_ms:.4f} |"]
    _w("table04_fleet_streaming.md", t4)
    return ["table01_conditions.md", "table02_tau_identification.md",
            "table03_residual_prediction.md", "table04_fleet_streaming.md"]


if __name__ == "__main__":
    print("tables:", make())
