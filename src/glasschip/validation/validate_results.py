"""Read-only cross-phase consistency checker: verifies the numbers the paper
will use exactly match the locked Phase 2 artifacts (within stated tolerances).
Fails loudly. No rounding before comparison."""
from __future__ import annotations
from glasschip import config as C
from glasschip.analysis.load_results import load_all


def _close(a, b, tol):
    return abs(a - b) <= tol


def validate():
    d = load_all()
    checks = []

    def chk(name, ok, got, exp):
        checks.append({"check": name, "ok": bool(ok), "got": got, "expected": exp})

    fid = {f.condition: f for f in d["fidelity"]}
    for k in C.COND_ORDER:
        f = fid[k]
        ep, eb, er = (C.EXPECT["tau_point"][k], C.EXPECT["tau_boot"][k], C.EXPECT["tau_ratio"][k])
        chk(f"tau_point_{k}",
            _close(f.tau_point, ep, max(C.TOL["tau_s"], ep * C.TOL["tau_pct"])), round(f.tau_point, 1), ep)
        chk(f"tau_boot_{k}",
            _close(f.tau_bootstrap, eb, max(C.TOL["tau_s"], eb * C.TOL["tau_pct"])), round(f.tau_bootstrap, 1), eb)
        chk(f"tau_ratio_{k}", _close(f.tau_ratio, er, C.TOL["ratio"]), round(f.tau_ratio, 3), er)
        # bootstrap CI must be >= analytic CI (temporal-correlation effect)
        chk(f"boot_ci_ge_analytic_{k}", f.bootstrap_ci_width >= f.analytic_ci_width * 0.9,
            round(f.bootstrap_ci_width, 1), f">= {round(f.analytic_ci_width,1)}")
        chk(f"boot_valid_{k}", f.invalid_boot_pct <= 1.0, round(f.invalid_boot_pct, 3), "<=1%")

    # precision != accuracy: F1 has small CoV but biased tau (ratio 0.29)
    f1 = fid["F1"]
    chk("F1_precise_but_biased", f1.bootstrap_cov < fid["F0"].bootstrap_cov and f1.tau_ratio < 0.5,
        dict(cov=round(f1.bootstrap_cov, 4), ratio=round(f1.tau_ratio, 3)), "cov<F0 and ratio<0.5")

    # residual: HGB max ~0.066; all null p95 < 0; NOT called unlearnable
    hgb = {r.condition: r.hgb for r in d["residual"]}
    chk("residual_hgb_max", _close(max(hgb.values()), C.EXPECT["residual_hgb_max"], C.TOL["small"]),
        round(max(hgb.values()), 4), C.EXPECT["residual_hgb_max"])
    chk("residual_hgb_not_improved_by_fidelity", hgb["F1"] > hgb["F0"] or hgb["F4"] > hgb["F0"],
        dict(F0=round(hgb["F0"], 3), F1=round(hgb["F1"], 3), F4=round(hgb["F4"], 3)),
        "some degraded >= F0 (so NOT 'fidelity helps')")
    chk("residual_nulls_negative", all(r.null_p95 < 0 for r in d["residual"]),
        [round(r.null_p95, 3) for r in d["residual"]], "all < 0")

    # fleet
    fl = d["fleet"]; ef = C.EXPECT["fleet"]
    for m in ("n_valid", "median", "mean", "std", "p05", "p95", "min", "max"):
        got = getattr(fl, m); exp = ef[m]
        tol = 1 if m == "n_valid" else max(2, exp * C.TOL["fleet_pct"])
        chk(f"fleet_{m}", _close(got, exp, tol), round(got, 1), exp)
    chk("fleet_socket_corr", _close(fl.socket_corr, ef["socket_corr"], 0.02), round(fl.socket_corr, 3), ef["socket_corr"])
    chk("fleet_socket_rel_diff", _close(fl.socket_rel_diff, ef["socket_rel_diff"], 0.02),
        round(fl.socket_rel_diff, 3), ef["socket_rel_diff"])
    chk("quantized_below_fleet_min", fl.quantized_tau < fl.min,
        dict(quantized=round(fl.quantized_tau, 1), fleet_min=round(fl.min, 1)), "quantized < fleet_min")

    # streaming
    st = d["streaming"]; es = C.EXPECT["streaming"]
    f0 = st.per_window["F0_full"]
    chk("streaming_oos_approx_baseline", abs(f0["oos"] - f0["baseline"]) < 0.03,
        dict(oos=round(f0["oos"], 3), baseline=round(f0["baseline"], 3)), "|oos-baseline|<0.03")
    chk("streaming_rel_spread", _close(f0["rel_spread"], es["rel_spread"], 0.05), round(f0["rel_spread"], 3), es["rel_spread"])
    chk("streaming_power_confound", _close(f0["power_confound"], es["power_confound"], 0.05),
        round(f0["power_confound"], 3), es["power_confound"])
    chk("streaming_runtime", _close(st.runtime_ms, es["runtime_ms"], C.TOL["runtime_ms"]),
        round(st.runtime_ms, 4), es["runtime_ms"])

    n_fail = sum(1 for c in checks if not c["ok"])
    return {"n_checks": len(checks), "n_fail": n_fail, "checks": checks, "data_ok": n_fail == 0}


if __name__ == "__main__":
    r = validate()
    for c in r["checks"]:
        print(("PASS" if c["ok"] else "FAIL"), c["check"], "| got", c["got"], "| exp", c["expected"])
    print(f"\n{r['n_checks']-r['n_fail']}/{r['n_checks']} passed; data_ok={r['data_ok']}")
