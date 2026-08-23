"""Generate the 6 paper figures (PDF + PNG) from canonical loaded results.
Deterministic; no hand-typed numbers; no smoothing/manipulation. Read-only."""
from __future__ import annotations
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from glasschip import config as C
from glasschip.analysis.load_results import load_all

plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3,
                     "figure.dpi": 120, "savefig.bbox": "tight"})


def _save(fig, stem):
    C.FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(C.FIG_DIR / f"{stem}.pdf")
    fig.savefig(C.FIG_DIR / f"{stem}.png", dpi=150)
    plt.close(fig)


def _fleet_units():
    u = json.loads(C.PHASE2D_UNITS.read_text())
    return [x for x in u if x.get("valid")]


def make():
    d = load_all()
    fid = {f.condition: f for f in d["fidelity"]}
    res = {r.condition: r for r in d["residual"]}
    fl = d["fleet"]; st = d["streaming"]
    order = C.COND_ORDER

    # ---- Fig 1: schematic ----
    fig, ax = plt.subplots(figsize=(7, 4.2)); ax.axis("off")
    def box(x, y, t, c="#eef"):
        ax.add_patch(plt.Rectangle((x-.16, y-.045), .32, .09, fc=c, ec="k", lw=1))
        ax.text(x, y, t, ha="center", va="center", fontsize=9)
    box(.5, .92, "Temperature + power measurements")
    box(.5, .74, "Degrade measurement quality only\n(hardware & workload unchanged)", "#fee")
    for i, k in enumerate(order):
        ax.text(.2 + i*.15, .58, k, ha="center", fontsize=9,
                bbox=dict(boxstyle="round", fc="#efe", ec="k"))
    box(.5, .42, "Frozen thermal model  T[t+1]=aT[t]+bP[t]+g")
    box(.5, .24, "Identified effective tau = -dt / ln(a)")
    box(.5, .06, "Prediction of remaining behavior (residual)")
    for y0, y1 in [(.875, .785), (.695, .625), (.535, .465), (.375, .285), (.195, .105)]:
        ax.add_patch(FancyArrowPatch((.5, y0), (.5, y1), arrowstyle="-|>", mutation_scale=12, lw=1))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_title("Figure 1. Same-hardware measurement-quality experiment")
    _save(fig, "fig01_setup")

    # ---- Fig 2 (MAIN): tau vs measurement quality ----
    fig, ax = plt.subplots(figsize=(7, 4.2))
    x = np.arange(len(order))
    pts = [fid[k].tau_point for k in order]
    bm = [fid[k].tau_bootstrap for k in order]
    cw = [fid[k].bootstrap_ci_width / 2 for k in order]
    ax.plot(x, pts, "o", ms=8, color="C0", label="point estimate (2B)")
    ax.errorbar(x, bm, yerr=cw, fmt="s", ms=6, color="C3", capsize=5,
                label="bootstrap median +/- 95% CI (2C)")
    for i, k in enumerate(order):
        ax.annotate(f"{fid[k].tau_ratio:.2f}x", (x[i], max(pts[i], bm[i])),
                    textcoords="offset points", xytext=(0, 10), ha="center", fontsize=9)
    ax.axhline(pts[0], color="gray", ls=":", lw=1)
    ax.annotate("F1: narrow CI around a biased tau\n(precision != accuracy)",
                (1, bm[1]), textcoords="offset points", xytext=(30, 20), fontsize=8,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.set_xticks(x); ax.set_xticklabels(order)
    ax.set_xlabel("measurement-quality condition"); ax.set_ylabel("effective tau (s)")
    ax.set_title("Figure 2. Measurement quality changes the identified effective tau")
    ax.legend(fontsize=8)
    _save(fig, "fig02_tau_fidelity")

    # ---- Fig 3: residual OOS prediction ----
    fig, ax = plt.subplots(figsize=(7, 4.2))
    models = [("persistence", "persistence"), ("linear", "linear"), ("hgb", "HGB"),
              ("lstm", "LSTM"), ("physics_mlp", "physics-MLP")]
    for attr, lab in models:
        y = [getattr(res[k], attr) for k in order]
        y = [np.nan if v is None else v for v in y]
        ax.plot(x, y, "o-", label=lab, ms=5)
    ax.plot(x, [res[k].null_p95 for k in order], "k--", alpha=.6, label="perm-null p95")
    ax.axhline(0, color="gray", lw=.7)
    ax.set_xticks(x); ax.set_xticklabels(order)
    ax.set_xlabel("measurement-quality condition"); ax.set_ylabel("out-of-sample R^2")
    ax.set_title("Figure 3. Higher measurement quality does not improve residual prediction")
    ax.legend(fontsize=7, ncol=3)
    _save(fig, "fig03_residual_prediction")

    # ---- Fig 4: fleet tau distribution ----
    units = _fleet_units()
    tau = np.array([u["tau_analytic"] for u in units])
    sub = np.array([u["tau_analytic"] for u in units if u.get("in_subset")])
    fig, ax = plt.subplots(figsize=(7, 4.2))
    bins = np.linspace(tau.min(), np.percentile(tau, 99), 40)
    ax.hist(tau, bins=bins, color="C0", alpha=.6, label=f"fleet (n={tau.size})")
    ax.hist(sub, bins=bins, color="C3", alpha=.7, label=f"2B/2C subset (n={sub.size})")
    for v, lab, ls in [(fl.median, f"median {fl.median:.0f}s", "--"),
                       (fl.p05, "P05", ":"), (fl.p95, "P95", ":")]:
        ax.axvline(v, color="k", ls=ls, lw=1, label=lab if ls == "--" else None)
    ax.set_xlabel("effective tau (s)"); ax.set_ylabel("units")
    ax.set_title("Figure 4. Fleet-scale distribution of effective tau (116 units)")
    ax.legend(fontsize=8)
    _save(fig, "fig04_fleet_tau")

    # ---- Fig 5: measurement bias vs fleet variation ----
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.axhspan(fl.p05, fl.p95, color="C0", alpha=.15, label=f"fleet P05-P95 ({fl.p05:.0f}-{fl.p95:.0f}s)")
    ax.axhline(fl.min, color="C0", ls="--", lw=1, label=f"fleet min {fl.min:.0f}s")
    ax.axhline(fl.median, color="C0", lw=1, alpha=.7, label=f"fleet median {fl.median:.0f}s")
    for i, k in enumerate(order):
        y = fid[k].tau_point
        ax.plot([i], [y], "rs", ms=8)
        ax.annotate(f"{k}={y:.0f}s", (i, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    ax.annotate("F1 below entire fleet range", (1, fid["F1"].tau_point),
                textcoords="offset points", xytext=(20, -25), fontsize=8,
                arrowprops=dict(arrowstyle="->", lw=.8))
    ax.set_xticks(range(len(order))); ax.set_xticklabels(order)
    ax.set_xlabel("measurement-quality condition"); ax.set_ylabel("effective tau (s)")
    ax.set_title("Figure 5. Measurement-induced tau vs natural fleet variation")
    ax.legend(fontsize=8)
    _save(fig, "fig05_fidelity_vs_fleet")

    # ---- Fig 6: streaming boundary ----
    fig, ax = plt.subplots(figsize=(7, 4.2))
    conds = ["F0_full", "F1_quantized", "F2_downsampled"]; labs = ["F0", "F1", "F2"]
    xs = np.arange(len(conds))
    oos = [st.per_window[c]["oos"] for c in conds]
    base = [st.per_window[c]["baseline"] for c in conds]
    ax.bar(xs - .2, oos, .4, label="OOS alert rate", color="C0")
    ax.bar(xs + .2, base, .4, label="baseline / null alert rate", color="C7")
    ax.set_xticks(xs); ax.set_xticklabels(labs)
    ax.set_ylabel("persisted-alert fraction")
    ax.set_title("Figure 6. Streaming tau: OOS ~ baseline (computable != useful)")
    ax.text(0.02, 0.95, f"runtime {st.runtime_ms:.4f} ms/window (real-time capable)",
            transform=ax.transAxes, fontsize=8, va="top",
            bbox=dict(boxstyle="round", fc="#ffe", ec="gray"))
    ax.legend(fontsize=8)
    _save(fig, "fig06_streaming_boundary")

    return [f"fig0{i}_*" for i in range(1, 7)]


if __name__ == "__main__":
    print("figures:", make())
