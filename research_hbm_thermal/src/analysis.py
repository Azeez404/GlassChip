"""Metrics, sampling-resolution analysis, and the falsification tests."""
from __future__ import annotations

import numpy as np
import pandas as pd


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    ok = np.isfinite(y_true) & np.isfinite(y_pred)
    if ok.sum() == 0:
        return dict(RMSE=np.nan, MAE=np.nan, MaxAE=np.nan, n=0)
    e = y_pred[ok] - y_true[ok]
    return dict(RMSE=float(np.sqrt(np.mean(e ** 2))), MAE=float(np.mean(np.abs(e))),
                MaxAE=float(np.max(np.abs(e))), n=int(ok.sum()))


def xcorr(a: np.ndarray, b: np.ndarray, lags) -> dict:
    a = (a - a.mean()) / (a.std() + 1e-12)
    b = (b - b.mean()) / (b.std() + 1e-12)
    n = len(a)
    out = {}
    for L in lags:
        out[int(L)] = float(np.mean(a[:n - L] * b[L:]) if L >= 0
                            else np.mean(a[-L:] * b[:n + L]))
    return out


def sampling_analysis(seg: pd.DataFrame, dt_s: float = 10.0) -> dict:
    """PHASE 7. Can 10 s sampling distinguish die->HBM coupling from a common driver?

    Raw signals share a slow trend, so correlation is computed on DIFFERENCES, and
    then again after regressing the power change out of both. If a directional
    coupling exists, the residual cross-correlation should peak at a POSITIVE lag
    (HBM responds after the die). A peak at lag 0 means the two temperatures move
    within the same sample, i.e. any coupling is faster than the sampling interval
    and its dynamics are NOT resolvable in this data.
    """
    P, Tg, Tm = (seg.P.to_numpy(float), seg.Tg.to_numpy(float), seg.Tm.to_numpy(float))
    dP, dTg, dTm = np.diff(P), np.diff(Tg), np.diff(Tm)
    lags = list(range(-4, 9))
    X = np.column_stack([dP, np.ones_like(dP)])
    beta_g, *_ = np.linalg.lstsq(X, dTg, rcond=None)
    beta_m, *_ = np.linalg.lstsq(X, dTm, rcond=None)
    rg, rm = dTg - X @ beta_g, dTm - X @ beta_m
    c_raw = xcorr(dTg, dTm, lags)
    c_par = xcorr(rg, rm, lags)
    c_pg = xcorr(dP, dTg, lags)
    argmax_par = max(c_par, key=c_par.get)
    return dict(
        dP_to_dTg=c_pg, argmax_dP_to_dTg=int(max(c_pg, key=c_pg.get)),
        dTg_to_dTm=c_raw, argmax_dTg_to_dTm=int(max(c_raw, key=c_raw.get)),
        partial_dTg_to_dTm=c_par, argmax_partial=int(argmax_par),
        peak_partial=float(c_par[argmax_par]),
        coupling_lag_resolvable=bool(argmax_par > 0),
        note=("Peak at lag 0 => die and HBM move within one 10 s sample; coupling "
              "dynamics are faster than the sampling interval and cannot be timed. "
              "Peak at lag>0 => HBM measurably follows the die."),
    )


def falsification(res: pd.DataFrame, fits: dict, sampling: dict,
                  primary: str = "multi-step") -> dict:
    """Explicit KILL conditions, evaluated on results rather than on impressions."""
    def rmse(model, task, target):
        r = res[(res.model == model) & (res.task == task) & (res.target == target)]
        return float(r.RMSE.iloc[0]) if len(r) else np.nan

    one_m = rmse("one-node", primary, "Tm")
    two_m = rmse("two-node", primary, "Tm")
    unc_m = rmse("unconstrained", primary, "Tm")
    one_g = rmse("one-node", primary, "Tg")
    two_g = rmse("two-node", primary, "Tg")

    gain_m = (one_m - two_m) / one_m * 100 if np.isfinite(one_m) and one_m > 0 else np.nan
    gain_g = (one_g - two_g) / one_g * 100 if np.isfinite(one_g) and one_g > 0 else np.nan

    rep = fits.get("two-node")
    c_m = rep.params.get("c_m", np.nan) if rep else np.nan
    cond_hbm = rep.cond.get("hbm", np.nan) if rep else np.nan

    k = {}
    k["K1_two_node_not_better"] = not (np.isfinite(gain_m) and gain_m > 0)
    k["K2_coupling_not_identifiable"] = bool(
        not np.isfinite(c_m) or c_m <= 0 or (np.isfinite(cond_hbm) and cond_hbm > 1e4))
    k["K3_physics_violated"] = bool(rep is not None and not rep.admissible)
    k["K4_explained_by_common_power"] = bool(
        np.isfinite(unc_m) and np.isfinite(two_m) and unc_m < two_m * 0.95)
    k["K5_sampling_artefact"] = bool(not sampling["coupling_lag_resolvable"])
    return dict(kill_flags=k, n_triggered=int(sum(k.values())),
                gain_Tm_pct=gain_m, gain_Tg_pct=gain_g,
                rmse_Tm=dict(one_node=one_m, two_node=two_m, unconstrained=unc_m),
                rmse_Tg=dict(one_node=one_g, two_node=two_g),
                coupling_c_m=float(c_m) if np.isfinite(c_m) else None,
                cond_hbm=float(cond_hbm) if np.isfinite(cond_hbm) else None)


def plot_result(seg, preds: dict, path: str, title: str, n_show: int = 400) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    idx = np.arange(min(n_show, len(preds["one-node"]["Tg_true"])))
    fig, ax = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    ax[0].plot(idx, preds["one-node"]["Tg_true"][idx], "k-", lw=2, label="Observed", zorder=5)
    ax[1].plot(idx, preds["one-node"]["Tm_true"][idx], "k-", lw=2, label="Observed", zorder=5)
    style = {"one-node": dict(color="#D55E00", ls="--", lw=1.4),
             "two-node": dict(color="#009E73", ls="-", lw=1.6)}
    for m in ("one-node", "two-node"):
        ax[0].plot(idx, preds[m]["Tg_pred"][idx], label=m, **style[m])
        ax[1].plot(idx, preds[m]["Tm_pred"][idx], label=m, **style[m])
    ax[0].set_ylabel("GPU die temp (degC)")
    ax[1].set_ylabel("HBM memory temp (degC)")
    ax[1].set_xlabel("step in held-out free-running rollout (10 s per step)")
    ax[0].set_title(title)
    for a in ax:
        a.legend(loc="best", fontsize=9)
        a.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=155)
    plt.close(fig)
