"""GLASSCHIP-V2 Phase 2B - within-Summit observability ablation.

Question: on the SAME Summit hardware/data, does degrading telemetry FIDELITY
reduce thermal-parameter identifiability (tau CoV / CI width) while leaving
out-of-sample residual learnability approximately unchanged (~null)?

This removes the M100-vs-Summit confound: same hosts, same period, same target,
same protocol; ONLY the observation fidelity changes.

V1 is imported read-only; nothing in V1 or Phase 2A is modified; raw data is
never written. Frozen model:  T[n+1] = a*T[n] + b*P[n] + g  (OLS); tau=-dt/ln a.

Conditions (identical hosts/sockets throughout):
  F0 FULL        : socket-mean temp, 10 s, float
  F1 QUANTIZED   : socket-mean temp rounded to 1 C, 10 s
  F2 DOWNSAMPLED : socket-mean temp, decimated 10->20 s (every 2nd sample), float
  F3 SPATIAL     : Tjmax = per-timestamp hottest-core temp (p*_core_temp_max),
                   10 s, float  [APPROXIMATION: the decomp archive has no fixed
                   per-core streams; Tjmax is the closest precisely-defined
                   single-sensor proxy - documented, not a fabricated core index]
  F4 COMBINED    : Tjmax, rounded 1 C, decimated 20 s

Residual learnability models: persistence (increment baseline), linear, HGB
(sklearn gradient boosting; xgboost unavailable), small LSTM, small
physics-anchored MLP. Strict chronological OOS (last collection block = test),
pooled across sockets, permutation-null tested.
"""
from __future__ import annotations

import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import polars as pl

sys.path.insert(0, str(Path("src").resolve()))
from baseline import ClassicalBaselineModel  # noqa: E402  (frozen, read-only)

CLEANED = Path("v2_research/summit/derived/cleaned")
OUT = Path("v2_research/summit/observability_ablation")
N_HOSTS = 10
RNG = np.random.default_rng(0)
CAP_TRAIN, CAP_TEST = 150_000, 50_000     # fair, seeded pooled cap (same all conds)
LSTM_WIN = 8

CONDITIONS = {
    "F0_full":        dict(temp="mean", quant=False, decimate=False, dt=10.0),
    "F1_quantized":   dict(temp="mean", quant=True,  decimate=False, dt=10.0),
    "F2_downsampled": dict(temp="mean", quant=False, decimate=True,  dt=20.0),
    "F3_spatial":     dict(temp="max",  quant=False, decimate=False, dt=10.0),
    "F4_combined":    dict(temp="max",  quant=True,  decimate=True,  dt=20.0),
}


def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")


def pilot_hosts(n):
    hs = []
    for mf in sorted(Path("v2_research/summit/derived/manifests").glob("*.json")):
        m = json.loads(mf.read_text()); hs.append((m["cleaning"]["rows_after"], m["host"]))
    hs.sort(key=lambda x: (-x[0], x[1]))
    return sorted(h for _, h in hs[:n])


def condition_segments(df, socket, cond):
    """Return (segments[(T,P)], blocks[YYYY-MM]) under a fidelity condition.
    Never bridges gaps; decimation happens WITHIN contiguous segments."""
    tcol = f"p{socket}_core_temp_{cond['temp']}"
    pcol = f"p{socket}_power"
    sub = df.select(["timestamp", "segment_id", tcol, pcol])
    segs, blocks = [], []
    for (_sid,), g in sub.group_by("segment_id", maintain_order=True):
        t = g[tcol].to_numpy().astype(float); p = g[pcol].to_numpy().astype(float)
        ts = g["timestamp"].to_numpy()
        ok = np.isfinite(t) & np.isfinite(p)
        idx = np.flatnonzero(np.diff(np.concatenate(([0], ok.view(np.int8), [0]))))
        for s, e in zip(idx[::2], idx[1::2]):
            tt, pp, tsb = t[s:e], p[s:e], ts[s:e]
            if cond["decimate"]:
                tt, pp, tsb = tt[::2], pp[::2], tsb[::2]   # 10->20 s, no interpolation
            if cond["quant"]:
                tt = np.round(tt)                           # 1 C quantization
            if len(tt) >= 2:
                segs.append((tt, pp)); blocks.append(str(tsb[0])[:7])
    return segs, blocks


# ---- identifiability (analytic OLS delta method, same as Phase 2A) -----------
def identify(segs, dt):
    T, P, y = ClassicalBaselineModel._pairs(segs)
    n = len(y); X = np.column_stack([T, P, np.ones(n)])
    XtX = X.T @ X
    try: XtXi = np.linalg.inv(XtX)
    except np.linalg.LinAlgError: return None
    beta = XtXi @ (X.T @ y); a = float(beta[0])
    if not (0 < a < 1): return dict(tau=np.nan, cov=np.nan, ci_w=np.nan, unstable=True)
    resid = y - X @ beta; s2 = float(resid @ resid) / max(n - 3, 1)
    se_a = float(np.sqrt(s2 * XtXi[0, 0]))
    tau = -dt / np.log(a); se_tau = abs(dt / (a * np.log(a) ** 2)) * se_a
    return dict(tau=float(tau), se_tau=float(se_tau), cov=float(se_tau / tau),
                ci_w=float(2 * 1.96 * se_tau), n_pairs=n, unstable=False)


# ---- residual dataset (pooled across sockets, chronological block split) -----
def residual_rows(host_socket_segments, dt):
    """For each socket build residual r[n]=T[n+1]-That and features; pool.
    Returns X, y, block, seq_groups (for LSTM: list of (Xseq,yseq))."""
    Xs, ys, bs, seqs = [], [], [], []
    for segs, blocks in host_socket_segments:
        m = ClassicalBaselineModel(dt_s=dt); m.fit(segs)
        for (t, p), blk in zip(segs, blocks):
            if len(t) < 3: continue
            pred = m.predict_onestep(t[:-1], p[:-1]); r = t[1:] - pred
            nidx = np.arange(1, len(r))
            feat = np.column_stack([p[nidx], p[nidx] - p[nidx - 1], t[nidx],
                                    p[nidx - 1], t[nidx - 1]])
            Xs.append(feat); ys.append(r[nidx]); bs.append(np.array([blk] * len(nidx)))
            if len(nidx) > LSTM_WIN + 1:
                seqs.append((feat, r[nidx], blk))
    return (np.vstack(Xs), np.concatenate(ys), np.concatenate(bs), seqs)


def chrono_split(block):
    order = sorted(set(block)); test_b = order[-1]
    return (block != test_b), (block == test_b), test_b


def r2(y, p):
    ss = np.sum((y - p) ** 2); tot = np.sum((y - y.mean()) ** 2)
    return float(1 - ss / tot) if tot > 0 else float("nan")


def cap(idx, k):
    return idx if idx.sum() <= k else np.flatnonzero(idx)[RNG.permutation(int(idx.sum()))[:k]]


def perm_null(y_test, pred, n=200):
    base = r2(y_test, pred)
    nulls = [r2(RNG.permutation(y_test), pred) for _ in range(n)]
    return base, float(np.percentile(nulls, 95)), float(np.mean(nulls))


def fit_linear(Xtr, ytr, Xte):
    from sklearn.linear_model import LinearRegression
    return LinearRegression().fit(Xtr, ytr).predict(Xte)


def fit_hgb(Xtr, ytr, Xte):
    from sklearn.ensemble import HistGradientBoostingRegressor
    return HistGradientBoostingRegressor(max_depth=4, max_iter=200,
                                         random_state=0).fit(Xtr, ytr).predict(Xte)


def _torch_train(model, Xtr, ytr, epochs=6, bs=8192, lr=1e-2, wd=0.0):
    import torch
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
    lossf = torch.nn.MSELoss()
    Xtr = torch.tensor(Xtr, dtype=torch.float32); ytr = torch.tensor(ytr, dtype=torch.float32)
    n = len(Xtr)
    for _ in range(epochs):
        perm = torch.randperm(n)
        for i in range(0, n, bs):
            j = perm[i:i + bs]; opt.zero_grad()
            out = model(Xtr[j]).squeeze(-1); loss = lossf(out, ytr[j]); loss.backward(); opt.step()
    return model


def fit_mlp_physics(Xtr, ytr, Xte):
    """Small MLP predicting the residual, ANCHORED to physics via strong weight
    decay toward zero-correction (physics prior). Standardised inputs."""
    import torch
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-8
    Xtr_s, Xte_s = (Xtr - mu) / sd, (Xte - mu) / sd
    net = torch.nn.Sequential(torch.nn.Linear(5, 16), torch.nn.Tanh(), torch.nn.Linear(16, 1))
    _torch_train(net, Xtr_s, ytr, wd=1e-2)   # wd = anchor to physics baseline
    with torch.no_grad():
        return net(torch.tensor(Xte_s, dtype=torch.float32)).squeeze(-1).numpy()


def fit_lstm(seqs, dt, test_b):
    """Tiny LSTM over feature windows -> residual. Pooled sockets, chronological."""
    import torch
    Xtr, ytr, Xte, yte = [], [], [], []
    for feat, r, blk in seqs:
        mu = feat.mean(0); sd = feat.std(0) + 1e-8; fs = (feat - mu) / sd
        for k in range(LSTM_WIN, len(r)):
            win = fs[k - LSTM_WIN:k]
            (Xte if blk == test_b else Xtr).append(win)
            (yte if blk == test_b else ytr).append(r[k])
    if len(Xtr) < 500 or len(Xte) < 200:
        return None
    Xtr = np.asarray(Xtr, np.float32); ytr = np.asarray(ytr, np.float32)
    Xte = np.asarray(Xte, np.float32); yte = np.asarray(yte, np.float32)
    # fair cap
    if len(Xtr) > CAP_TRAIN:
        s = RNG.permutation(len(Xtr))[:CAP_TRAIN]; Xtr, ytr = Xtr[s], ytr[s]
    if len(Xte) > CAP_TEST:
        s = RNG.permutation(len(Xte))[:CAP_TEST]; Xte, yte = Xte[s], yte[s]

    class L(torch.nn.Module):
        def __init__(s):
            super().__init__(); s.l = torch.nn.LSTM(5, 16, batch_first=True); s.o = torch.nn.Linear(16, 1)
        def forward(s, x): h, _ = s.l(x); return s.o(h[:, -1])
    net = L()
    opt = torch.optim.Adam(net.parameters(), lr=1e-2); lossf = torch.nn.MSELoss()
    Xt = torch.tensor(Xtr); yt = torch.tensor(ytr)
    for _ in range(6):
        perm = torch.randperm(len(Xt))
        for i in range(0, len(Xt), 8192):
            j = perm[i:i + 8192]; opt.zero_grad()
            loss = lossf(net(Xt[j]).squeeze(-1), yt[j]); loss.backward(); opt.step()
    with torch.no_grad():
        pred = net(torch.tensor(Xte)).squeeze(-1).numpy()
    return r2(yte, pred), yte, pred


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    hosts = pilot_hosts(N_HOSTS)
    print(f"[{now()}] hosts: {hosts}")
    frames = {h: pl.read_parquet(CLEANED / f"host={h}" / "data.parquet") for h in hosts}
    results = {"generated": now(), "hosts": hosts, "conditions": {},
               "note": "within-Summit controlled ablation; F3/F4 use Tjmax (max-core) "
                       "as the single-sensor proxy - no fixed per-core streams exist in "
                       "the decomp archive.", "cap_train": CAP_TRAIN, "cap_test": CAP_TEST}
    table = []
    for cname, cond in CONDITIONS.items():
        t0 = time.time()
        # --- identifiability per socket ---
        taus, covs, ciw, hs_segs = [], [], [], []
        for h in hosts:
            for s in (0, 1):
                segs, blocks = condition_segments(frames[h], s, cond)
                if len(segs) < 1: continue
                idr = identify(segs, cond["dt"])
                if idr and not idr["unstable"] and np.isfinite(idr["tau"]):
                    taus.append(idr["tau"]); covs.append(idr["cov"]); ciw.append(idr["ci_w"])
                hs_segs.append((segs, blocks))
        taus, covs, ciw = map(lambda a: np.array(a, float), (taus, covs, ciw))
        # --- residual learnability (pooled) ---
        X, y, blk, seqs = residual_rows(hs_segs, cond["dt"])
        tr, te, test_b = chrono_split(blk)
        tri, tei = cap(tr, CAP_TRAIN), cap(te, CAP_TEST)
        Xtr, ytr, Xte, yte = X[tri], y[tri], X[tei], y[tei]
        res = {}
        # persistence: residual model predicts 0 (physics already applied)
        res["persistence"] = r2(yte, np.zeros_like(yte))
        pl_lin = fit_linear(Xtr, ytr, Xte); res["linear"] = r2(yte, pl_lin)
        pl_hgb = fit_hgb(Xtr, ytr, Xte); res["hgb"] = r2(yte, pl_hgb)
        pl_mlp = fit_mlp_physics(Xtr, ytr, Xte); res["mlp_physics"] = r2(yte, pl_mlp)
        lstm = fit_lstm(seqs, cond["dt"], test_b)
        res["lstm"] = (lstm[0] if lstm else None)
        # permutation null on the linear model (representative)
        base, null95, nullmean = perm_null(yte, pl_lin)
        res["perm_null"] = {"linear_r2": base, "null_p95": null95, "null_mean": nullmean,
                            "significant": bool(base > null95)}
        cond_res = {"fidelity": cond,
                    "identifiability": {
                        "n_units": int(len(taus)),
                        "tau_median": float(np.median(taus)) if taus.size else None,
                        "tau_min": float(taus.min()) if taus.size else None,
                        "tau_max": float(taus.max()) if taus.size else None,
                        "cov_median": float(np.median(covs)) if covs.size else None,
                        "ci_width_median": float(np.median(ciw)) if ciw.size else None,
                        "taus": taus.tolist(), "covs": covs.tolist(), "ciws": ciw.tolist()},
                    "residual_oos_r2": res,
                    "n_train": int(len(ytr)), "n_test": int(len(yte)), "test_block": test_b}
        results["conditions"][cname] = cond_res
        table.append({
            "condition": cname, "temp": cond["temp"], "quant_1C": cond["quant"],
            "dt_s": cond["dt"], "n_units": int(len(taus)),
            "tau_median": round(float(np.median(taus)), 1) if taus.size else None,
            "cov_median": round(float(np.median(covs)), 4) if covs.size else None,
            "ci_width_median": round(float(np.median(ciw)), 1) if ciw.size else None,
            "res_r2_persist": round(res["persistence"], 4),
            "res_r2_linear": round(res["linear"], 4),
            "res_r2_hgb": round(res["hgb"], 4),
            "res_r2_lstm": (round(res["lstm"], 4) if res["lstm"] is not None else None),
            "res_r2_mlp_physics": round(res["mlp_physics"], 4),
            "null_p95": round(null95, 4), "linear_significant": res["perm_null"]["significant"]}
        )
        (OUT / "observability_ablation_results.json").write_text(json.dumps(results, indent=2, default=str))
        print(f"  {cname:<15} tauCoV={np.median(covs):.4f} CIw={np.median(ciw):.1f}s "
              f"| resR2 lin={res['linear']:.4f} hgb={res['hgb']:.4f} "
              f"lstm={res['lstm']} mlp={res['mlp_physics']:.4f} null95={null95:.4f} "
              f"[{time.time()-t0:.0f}s]")
    results["table"] = table
    (OUT / "observability_ablation_results.json").write_text(json.dumps(results, indent=2, default=str))
    # CSV table
    import csv
    with open(OUT / "observability_ablation_table.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0].keys())); w.writeheader(); w.writerows(table)
    make_figures(results)
    print(f"[{now()}] done -> {OUT}")


def make_figures(results):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    conds = list(results["conditions"]); C = results["conditions"]
    # Fig1: CoV + CI width vs fidelity
    fig, ax1 = plt.subplots(figsize=(8, 4))
    cov = [C[c]["identifiability"]["cov_median"] for c in conds]
    ciw = [C[c]["identifiability"]["ci_width_median"] for c in conds]
    ax1.plot(conds, cov, "o-", color="C0", label="tau CoV median"); ax1.set_ylabel("tau CoV", color="C0")
    ax2 = ax1.twinx(); ax2.plot(conds, ciw, "s--", color="C3", label="tau CI width median")
    ax2.set_ylabel("tau CI width (s)", color="C3")
    ax1.set_title("Identifiability degrades as telemetry fidelity drops"); ax1.tick_params(axis="x", rotation=20)
    fig.tight_layout(); fig.savefig(OUT / "fig1_identifiability_vs_fidelity.png", dpi=110); plt.close(fig)
    # Fig2: tau distributions
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.boxplot([C[c]["identifiability"]["taus"] for c in conds], tick_labels=conds, showfliers=False)
    ax.set_ylabel("tau (s)"); ax.set_title("tau distribution across Summit sockets per condition")
    ax.tick_params(axis="x", rotation=20); fig.tight_layout()
    fig.savefig(OUT / "fig2_tau_distributions.png", dpi=110); plt.close(fig)
    # Fig3: residual OOS R2 per model + null band
    fig, ax = plt.subplots(figsize=(8, 4))
    models = ["persistence", "linear", "hgb", "lstm", "mlp_physics"]
    for mi, mdl in enumerate(models):
        vals = [C[c]["residual_oos_r2"].get(mdl) for c in conds]
        vals = [v if v is not None else np.nan for v in vals]
        ax.plot(conds, vals, "o-", label=mdl)
    null95 = [C[c]["residual_oos_r2"]["perm_null"]["null_p95"] for c in conds]
    ax.plot(conds, null95, "k--", alpha=0.6, label="perm-null p95")
    ax.axhline(0, color="gray", lw=0.6)
    ax.set_ylabel("residual OOS R2"); ax.set_title("Residual learnability stays ~null across fidelity")
    ax.legend(fontsize=7, ncol=3); ax.tick_params(axis="x", rotation=20); fig.tight_layout()
    fig.savefig(OUT / "fig3_residual_oos_r2.png", dpi=110); plt.close(fig)


if __name__ == "__main__":
    main()
