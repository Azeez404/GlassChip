"""Canonical paper data model: load the locked Phase 2 JSON artifacts ONCE into
typed structures. All tables/figures derive from these - numbers are never
duplicated by hand. Read-only."""
from __future__ import annotations

import json, hashlib
from dataclasses import dataclass, field, asdict
from pathlib import Path
from glasschip import config as C


def _load(phase):
    return json.loads(C.SRC[phase].read_text())


def _sha12(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


@dataclass
class FidelityResult:
    condition: str
    tau_point: float           # 2B analytic point
    tau_bootstrap: float       # 2C bootstrap median (of units)
    analytic_cov: float
    analytic_ci_width: float
    bootstrap_cov: float
    bootstrap_ci_width: float
    tau_ratio: float           # vs F0 (bootstrap)
    invalid_boot_pct: float


@dataclass
class ResidualResult:
    condition: str
    persistence: float
    linear: float
    hgb: float
    lstm: float | None
    physics_mlp: float
    null_p95: float


@dataclass
class FleetResult:
    n_valid: int
    median: float; mean: float; std: float
    iqr: list; p05: float; p95: float; min: float; max: float
    socket_corr: float; socket_rel_diff: float; socket_abs_diff_s: float
    quantized_tau: float       # F1 point (for the below-fleet-min comparison)


@dataclass
class StreamingResult:
    n_units: int
    per_window: dict           # cond -> {oos, baseline, diff, rel_spread, power_confound}
    runtime_ms: float
    window_sensitivity: dict


def load_all():
    a, b, c, d, e = (_load(p) for p in ("2A", "2B", "2C", "2D", "2E"))

    fid, res = [], []
    for k in C.COND_ORDER:
        bk = C.COND_KEY[k]
        bi = b["conditions"][bk]["identifiability"]
        br = b["conditions"][bk]["residual_oos_r2"]
        ci = c["conditions"][bk]
        fid.append(FidelityResult(
            condition=k, tau_point=bi["tau_median"],
            tau_bootstrap=ci["boot_tau_median_of_units"],
            analytic_cov=ci["phase2b_analytic_cov"], analytic_ci_width=ci["phase2b_analytic_ci_width"],
            bootstrap_cov=ci["boot_cov_median"], bootstrap_ci_width=ci["boot_ci_width_median"],
            tau_ratio=ci["tau_ratio_vs_F0_bootstrap"], invalid_boot_pct=100 * ci["mean_invalid_frac"]))
        res.append(ResidualResult(condition=k, persistence=br["persistence"], linear=br["linear"],
                                  hgb=br["hgb"], lstm=br["lstm"], physics_mlp=br["mlp_physics"],
                                  null_p95=br["perm_null"]["null_p95"]))

    ft = d["fleet_tau"]; sc = d["socket_consistency"]
    f1_point = b["conditions"]["F1_quantized"]["identifiability"]["tau_median"]
    fleet = FleetResult(n_valid=d["n_units_valid"], median=ft["median"], mean=ft["mean"],
                        std=ft["std"], iqr=ft["iqr"], p05=ft["p05"], p95=ft["p95"],
                        min=ft["min"], max=ft["max"], socket_corr=sc["corr"],
                        socket_rel_diff=sc["median_rel_diff"], socket_abs_diff_s=sc["median_abs_diff_s"],
                        quantized_tau=f1_point)

    per = {}
    for cn in ("F0_full", "F1_quantized", "F2_downsampled"):
        x = e["conditions"][cn]
        per[cn] = dict(oos=x["oos_alert_rate"]["median"], baseline=x["baseline_alert_rate"]["median"],
                       diff=x["oos_minus_baseline_alert_median"],
                       rel_spread=x["baseline_rel_spread_median"],
                       power_confound=x["power_confound_corr_median"])
    stream = StreamingResult(n_units=e["conditions"]["F0_full"]["n_units"], per_window=per,
                             runtime_ms=e["runtime"]["per_rolling_tau_ms"],
                             window_sensitivity=e.get("window_sensitivity_F0", {}))

    ctx = {"phase2a_tau_med": a["rollup"]["tau_point_s"]["median"],
           "phase2a_oos_increment_r2": a["rollup"]["oos_increment_r2"]["median"]}
    return dict(fidelity=fid, residual=res, fleet=fleet, streaming=stream, context=ctx)


def write_manifest(data, path):
    """paper_results_manifest.json: metric -> value/phase/dest/claim/classification."""
    rows = []

    def add(metric, value, phase, fig, table, claim, cls):
        rows.append(dict(metric=metric, value=value, phase=phase, figure=fig,
                         table=table, claim=claim, classification=cls))

    for f in data["fidelity"]:
        add(f"tau_point_{f.condition}", f.tau_point, "2B", "fig02_tau_fidelity",
            "table02_tau_identification", "Measurement quality changes identified effective tau", "V")
        add(f"tau_boot_{f.condition}", f.tau_bootstrap, "2C", "fig02_tau_fidelity",
            "table02_tau_identification", "Bootstrap confirms the tau shift is not an analytic artifact", "V")
        add(f"tau_ratio_{f.condition}", f.tau_ratio, "2C", "fig02_tau_fidelity",
            "table02_tau_identification", "Measurement quality biases effective tau", "V")
    for r in data["residual"]:
        add(f"residual_hgb_{r.condition}", r.hgb, "2B", "fig03_residual_prediction",
            "table03_residual_prediction",
            "Higher measurement quality does not materially improve residual prediction", "V")
    fl = data["fleet"]
    for m in ("median", "mean", "std", "p05", "p95", "min", "max", "n_valid",
              "socket_corr", "socket_rel_diff"):
        add(f"fleet_{m}", getattr(fl, m), "2D", "fig04_fleet_tau", "table04_fleet_streaming",
            "Fleet-scale natural variation of effective tau", "V")
    add("quantized_below_fleet_min", f"{fl.quantized_tau} < {fl.min}", "2C+2D",
        "fig05_fidelity_vs_fleet", "table04_fleet_streaming",
        "The quantization-induced estimate falls below the observed full-fidelity fleet range", "V")
    st = data["streaming"]
    add("streaming_runtime_ms", st.runtime_ms, "2E", "fig06_streaming_boundary",
        "table04_fleet_streaming", "tau is computable online at negligible cost", "V")
    add("streaming_oos_vs_baseline", st.per_window["F0_full"], "2E", "fig06_streaming_boundary",
        "table04_fleet_streaming", "computable does not mean useful as a standalone monitor", "V")

    Path(path).write_text(json.dumps({"generated_from": {k: str(v) for k, v in C.SRC.items()},
                                      "source_hashes": {k: _sha12(v) for k, v in C.SRC.items()},
                                      "raw_sha256": C.RAW_SHA256, "rows": rows}, indent=2))
    return len(rows)
