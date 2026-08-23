"""Clean-room PINN prototype: single entry point.

Compares four models on the same held-out high-temperature GPU regime:
  A  Classical first-order RC
  B  Gradient-boosted trees
  C  Gradient-boosted trees, tail-weighted (the decisive imbalance control)
  D  Physics-informed neural model (+ ablations)

Run:  python research_pinn_chip/experiments/run_prototype.py
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import baseline_ml as bml                      # noqa: E402
import data_loader as dl                       # noqa: E402
import evaluation as ev                        # noqa: E402
from classical_rc import ClassicalRC           # noqa: E402
from pinn import ThermalPINN                   # noqa: E402

HORIZON = 30            # multi-step rollout length (30 x 10 s = 300 s)
SCAN_CACHE = os.path.join(ROOT, "data", "_trace_scan.csv")
RESULTS = os.path.join(ROOT, "results")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def rollout(predict_dT, df: pd.DataFrame, block: np.ndarray, mu, sd, horizon: int,
            standardise: bool):
    """Free-running multi-step prediction.

    Seeded with the observed temperature at the block start, then fed its own
    predictions. Only the OBSERVED POWER sequence is consumed thereafter; observed
    temperatures are never re-injected.
    """
    sub = df.iloc[block].reset_index(drop=True)
    T = float(sub.loc[0, "T"])
    T_l1, T_l2 = float(sub.loc[0, "T_l1"]), float(sub.loc[0, "T_l2"])
    out = []
    for k in range(horizon):
        P = float(sub.loc[k, "P"])
        P_l1, P_l2 = float(sub.loc[k, "P_l1"]), float(sub.loc[k, "P_l2"])
        raw = np.array([[T, T_l1, T_l2, P, P_l1, P_l2, P - P_l1, T - T_l1]])
        x = (raw - mu) / sd if standardise else raw
        dT = float(np.asarray(predict_dT(x)).ravel()[0])
        dT = float(np.clip(dT, -25.0, 25.0))    # guard against divergence blow-up
        T_l2, T_l1, T = T_l1, T, T + dT
        out.append(T)
    truth = sub.loc[1:horizon, "T"].to_numpy(dtype=float)
    return np.array(out), truth


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    log(f"Summit derived root: {dl.DEFAULT_SUMMIT_DERIVED}")

    # ---- 1. deterministic trace selection -------------------------------------
    if os.path.exists(SCAN_CACHE):
        scan = pd.read_csv(SCAN_CACHE)
        log(f"loaded trace scan cache ({len(scan)} traces)")
    else:
        log("scanning all traces (one-off)...")
        scan = dl.scan_traces()
        scan.to_csv(SCAN_CACHE, index=False)
    host, gpu = dl.select_trace(scan)
    log(f"selected trace: host={host} gpu={gpu} (max hot-regime count)")

    # ---- 2. load and build causal features ------------------------------------
    tr = dl.load_trace(host, gpu)
    log(f"trace rows raw={tr.n_raw:,} usable after causal filtering={len(tr.df):,}")
    split = dl.regime_split(tr.df)
    log(f"train(<45C)={split['n_train']:,}  test(>55C)={split['n_test']:,}  "
        f"excluded(45-55C)={split['n_excluded']:,}  hot={split['hot_pct']:.3f}%")

    train, test = split["train"], split["test"]
    if len(train) < 1000 or len(test) < 200:
        log("BLOCKER: insufficient data in one regime; aborting")
        return 2

    F = dl.FEATURES
    Xtr, ytr = train[F].to_numpy(float), train["target_dT"].to_numpy(float)
    Xte, yte = test[F].to_numpy(float), test["target_dT"].to_numpy(float)
    T_hot_true = test["T_next"].to_numpy(float)
    T_hot_cur = test["T"].to_numpy(float)

    # scaler fitted on TRAIN ONLY
    mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
    sd[sd == 0] = 1.0
    Xtr_s, Xte_s = (Xtr - mu) / sd, (Xte - mu) / sd

    # ---- 3. Model A: classical RC ---------------------------------------------
    log("fitting Model A (classical RC)...")
    rc = ClassicalRC().fit(train["T"].to_numpy(float), train["P"].to_numpy(float), ytr)
    f = rc.fit_
    log(f"  a={f.a:.4e}  b={f.b:.4e}  tau={f.tau_s:.1f}s  T_amb={f.T_amb:.2f}C  "
        f"admissible={f.admissible}  cond={f.cond:.2e}")

    # ---- 4/5. Models B and C ---------------------------------------------------
    log("fitting Model B (GBT)...")
    gbt = bml.make_model().fit(Xtr_s, ytr)
    log("fitting Model C (GBT tail-weighted)...")
    w = bml.tail_weights(train["T"].to_numpy(float))
    log(f"  weights: min={w.min():.2f} med={np.median(w):.2f} max={w.max():.2f}")
    gbt_w = bml.make_model().fit(Xtr_s, ytr, sample_weight=w)

    # ---- 6. Model D: PINN + ablations -----------------------------------------
    variants = {
        "PINN": dict(lam=1.0, collocation=True),
        "PINN-strict": dict(lam=1.0, collocation=False),
        "MLP (lam=0)": dict(lam=0.0, collocation=False),
        "PINN (lam=10)": dict(lam=10.0, collocation=True),
    }
    pinns = {}
    for name, kw in variants.items():
        log(f"training {name} ...")
        m = ThermalPINN(n_features=len(F), epochs=300, **kw).fit(Xtr_s, ytr, mu, sd)
        r = m.result_
        log(f"  data={r.data_loss:.5f} phys={r.physics_loss:.5f} total={r.total_loss:.5f} "
            f"a={r.a:.3e} b={r.b:.3e} tau={r.tau_s:.1f}s T_amb={r.T_amb:.2f}C")
        pinns[name] = m

    # ---- 7. one-step evaluation on the hot regime ------------------------------
    one_step = {
        "Classical RC": T_hot_cur + rc.predict_dT(T_hot_cur, test["P"].to_numpy(float)),
        "GBT": T_hot_cur + gbt.predict(Xte_s),
        "GBT (tail-weighted)": T_hot_cur + gbt_w.predict(Xte_s),
    }
    for name, m in pinns.items():
        one_step[name] = T_hot_cur + m.predict_dT(Xte_s)

    # ---- 8. multi-step free-running rollout ------------------------------------
    blocks = dl.hot_blocks(test, HORIZON)
    log(f"hot contiguous blocks with >= {HORIZON+1} steps: {len(blocks)}")
    multi = {k: {"pred": [], "true": []} for k in one_step}
    if blocks:
        preds_fn = {
            "Classical RC": (lambda x: rc.predict_dT(x[:, 0], x[:, 3]), False),
            "GBT": (gbt.predict, True),
            "GBT (tail-weighted)": (gbt_w.predict, True),
        }
        for name, m in pinns.items():
            preds_fn[name] = (m.predict_dT, True)
        for blk in blocks:
            for name, (fn, std) in preds_fn.items():
                p, t = rollout(fn, test, blk, mu, sd, HORIZON, std)
                multi[name]["pred"].append(p)
                multi[name]["true"].append(t)

    # ---- 9. sanity checks -------------------------------------------------------
    checks = ev.sanity_checks(split, tr.df, one_step, T_hot_true)
    log("sanity checks:")
    n_fail = 0
    for name, ok, detail in checks:
        if not ok:
            n_fail += 1
        log(f"  [{'PASS' if ok else 'FAIL'}] {name} {('- ' + detail) if detail else ''}")
    log(f"sanity: {len(checks)-n_fail}/{len(checks)} passed")

    # ---- 10. metrics ------------------------------------------------------------
    rows = []
    for name in one_step:
        m1 = ev.metrics(T_hot_true, one_step[name])
        rows.append(dict(model=name, task="one-step", **m1))
        if blocks:
            pt = np.concatenate(multi[name]["pred"])
            tt = np.concatenate(multi[name]["true"])
            mm = ev.metrics(tt, pt)
            rows.append(dict(model=name, task=f"multi-step (H={HORIZON})", **mm))
    mdf = pd.DataFrame(rows)
    mdf.to_csv(os.path.join(RESULTS, "metrics.csv"), index=False)

    log("\n=== HOT-REGIME METRICS (degC) ===")
    for task in mdf.task.unique():
        sub = mdf[mdf.task == task].sort_values("RMSE")
        log(f"\n-- {task} --")
        log(sub[["model", "RMSE", "MAE", "MaxAE", "n"]].to_string(
            index=False, float_format=lambda v: f"{v:.4f}"))

    # ---- 11. figure --------------------------------------------------------------
    if blocks:
        blk = blocks[int(np.argmax([len(b) for b in blocks]))]
        show = {}
        for name in ["Classical RC", "GBT", "GBT (tail-weighted)", "PINN"]:
            fn, std = ((lambda x: rc.predict_dT(x[:, 0], x[:, 3]), False) if name == "Classical RC"
                       else (gbt.predict, True) if name == "GBT"
                       else (gbt_w.predict, True) if name == "GBT (tail-weighted)"
                       else (pinns["PINN"].predict_dT, True))
            p, t = rollout(fn, test, blk, mu, sd, HORIZON, std)
            show[name] = p
        ev.plot_hot_regime(
            np.arange(1, HORIZON + 1), t, show,
            os.path.join(RESULTS, "hot_regime_predictions.png"),
            f"Free-running {HORIZON}-step prediction, hot regime (>55 degC) - "
            f"{host} GPU{gpu}",
        )
        log(f"figure written: {RESULTS}/hot_regime_predictions.png")

    # ---- 12. verdict ---------------------------------------------------------------
    def rmse(model: str, task: str) -> float:
        s = mdf[(mdf.model == model) & (mdf.task == task)]
        return float(s.RMSE.iloc[0]) if len(s) else float("nan")

    task = f"multi-step (H={HORIZON})" if blocks else "one-step"
    r_pinn = rmse("PINN", task)
    r_gbt = rmse("GBT", task)
    r_gbtw = rmse("GBT (tail-weighted)", task)
    r_rc = rmse("Classical RC", task)
    r_mlp = rmse("MLP (lam=0)", task)
    best_ml = min(r_gbt, r_gbtw)

    beats_both = r_pinn < r_gbt and r_pinn < r_gbtw
    margin = (best_ml - r_pinn) / best_ml * 100 if np.isfinite(best_ml) else np.nan
    physics_helps = np.isfinite(r_mlp) and r_pinn < r_mlp

    if n_fail > 0:
        verdict = "KILL (sanity checks failed)"
    elif beats_both and margin >= 10 and physics_helps:
        verdict = "GO"
    elif beats_both and margin > 0:
        verdict = "INVESTIGATE"
    elif abs(margin) < 5:
        verdict = "INVESTIGATE"
    else:
        verdict = "KILL"

    summary = dict(
        host=host, gpu=int(gpu), decision_task=task,
        n_train=split["n_train"], n_test=split["n_test"],
        n_excluded=split["n_excluded"], hot_pct=split["hot_pct"],
        n_blocks=len(blocks), horizon=HORIZON,
        rmse_classical=r_rc, rmse_gbt=r_gbt, rmse_gbt_weighted=r_gbtw,
        rmse_pinn=r_pinn, rmse_mlp_lam0=r_mlp,
        pinn_beats_both_ml=bool(beats_both),
        pinn_margin_vs_best_ml_pct=float(margin),
        physics_beats_same_net_without_physics=bool(physics_helps),
        sanity_failed=n_fail, verdict=verdict,
        rc_admissible=f.admissible, rc_tau_s=f.tau_s, rc_T_amb=f.T_amb,
    )
    with open(os.path.join(RESULTS, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    log("\n=== VERDICT ===")
    for k, v in summary.items():
        log(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
