"""Metrics, sanity checks and the single results figure."""
from __future__ import annotations

import numpy as np
import pandas as pd


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ok = np.isfinite(y_true) & np.isfinite(y_pred)
    if ok.sum() == 0:
        return {"RMSE": np.nan, "MAE": np.nan, "MaxAE": np.nan, "n": 0,
                "n_nonfinite": int((~ok).sum())}
    e = y_pred[ok] - y_true[ok]
    return {
        "RMSE": float(np.sqrt(np.mean(e ** 2))),
        "MAE": float(np.mean(np.abs(e))),
        "MaxAE": float(np.max(np.abs(e))),
        "n": int(ok.sum()),
        "n_nonfinite": int((~ok).sum()),
    }


def sanity_checks(split: dict, trace_df: pd.DataFrame, preds: dict,
                  y_hot: np.ndarray) -> list[tuple[str, bool, str]]:
    """Automatic checks run before any result is declared valid."""
    out: list[tuple[str, bool, str]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        out.append((name, bool(ok), detail))

    tr, te = split["train"], split["test"]
    add("train non-empty", len(tr) > 0, f"n={len(tr)}")
    add("test non-empty", len(te) > 0, f"n={len(te)}")

    add("timestamps sorted", bool(trace_df["timestamp"].is_monotonic_increasing))
    add("no duplicate timestamps", int(trace_df["timestamp"].duplicated().sum()) == 0,
        f"dups={int(trace_df['timestamp'].duplicated().sum())}")

    # regime disjointness: the 45-55 degC gap must be respected on both sides
    tr_max = float(tr[["T", "T_l1", "T_l2", "T_next"]].to_numpy().max())
    te_min = float(te[["T", "T_l1", "T_l2", "T_next"]].to_numpy().min())
    add("train/test regimes disjoint", tr_max < te_min,
        f"train max {tr_max:.2f} C < test min {te_min:.2f} C")
    add("regime gap >= 10 C", (te_min - tr_max) >= 10.0,
        f"gap {te_min - tr_max:.2f} C")

    # no shared timestamps
    shared = len(set(tr["timestamp"]) & set(te["timestamp"]))
    add("no train/test timestamp overlap", shared == 0, f"shared={shared}")

    # feature finiteness
    fin_tr = bool(np.isfinite(tr.select_dtypes("number").to_numpy()).all())
    fin_te = bool(np.isfinite(te.select_dtypes("number").to_numpy()).all())
    add("train features finite", fin_tr)
    add("test features finite", fin_te)

    # prediction shapes and numerical sanity
    for name, p in preds.items():
        p = np.asarray(p, dtype=float)
        add(f"[{name}] shape matches target", p.shape == y_hot.shape,
            f"{p.shape} vs {y_hot.shape}")
        add(f"[{name}] all finite", bool(np.isfinite(p).all()),
            f"nonfinite={int((~np.isfinite(p)).sum())}")
        add(f"[{name}] no numerical explosion", bool(np.nanmax(np.abs(p)) < 1e4),
            f"max|pred|={np.nanmax(np.abs(p)):.3g}")
    return out


def plot_hot_regime(times, y_true, preds: dict, path: str, title: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.plot(times, y_true, color="black", lw=2.0, label="Observed", zorder=5)
    styles = {
        "Classical RC": dict(color="#0072B2", lw=1.4, ls="-"),
        "GBT": dict(color="#D55E00", lw=1.4, ls="--"),
        "GBT (tail-weighted)": dict(color="#CC79A7", lw=1.4, ls="-."),
        "PINN": dict(color="#009E73", lw=1.8, ls="-"),
    }
    for name, p in preds.items():
        ax.plot(times, p, label=name, **styles.get(name, dict(lw=1.2)))
    ax.set_xlabel("step within hot-regime rollout (10 s per step)")
    ax.set_ylabel("GPU core temperature (degC)")
    ax.set_title(title)
    ax.legend(loc="best", fontsize=9, framealpha=0.9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
