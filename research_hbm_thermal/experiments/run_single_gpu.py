"""First scientific experiment: one-node vs two-node GPU/HBM thermal model.

    Summit GPU trace -> chronological split -> Model A / B / C
    -> held-out one-step and free-running multi-step -> metrics -> figure -> verdict

Run:  python research_hbm_thermal/experiments/run_single_gpu.py
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

import analysis as an                                     # noqa: E402
import data as dta                                        # noqa: E402
from models import (OneNodeModel, TwoNodeModel, UnconstrainedModel,  # noqa: E402
                    one_step, rollout)

RESULTS = os.path.join(ROOT, "results")
DOCS = os.path.join(ROOT, "docs")


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def select_trace(cfg: dict) -> tuple[str, int, pd.DataFrame]:
    """Deterministic: the trace with the widest GPU power range (most thermal
    excitation), which is what makes the coupling identifiable at all.
    Selection never depends on model performance."""
    root = cfg["dataset"]["root_abs"]
    pm = cfg["dataset"]["gpu_power_map"]
    rows = []
    for f in dta.host_files(root):
        host = dta.host_name(f)
        cols = [pm[i] for i in range(6)] + [f"gpu{i}_core_temp" for i in range(6)] \
               + [f"gpu{i}_mem_temp" for i in range(6)]
        d = pd.read_parquet(f, columns=cols)
        for g in range(6):
            P, Tg, Tm = d[pm[g]], d[f"gpu{g}_core_temp"], d[f"gpu{g}_mem_temp"]
            ok = P.notna() & Tg.notna() & Tm.notna()
            if ok.sum() < 10000:
                continue
            rows.append(dict(host=host, gpu=g, n=int(ok.sum()),
                             p_range=float(P[ok].max() - P[ok].min()),
                             p_std=float(P[ok].std()),
                             tg_range=float(Tg[ok].max() - Tg[ok].min())))
    scan = pd.DataFrame(rows)
    scan.to_csv(os.path.join(ROOT, "results", "trace_scan.csv"), index=False)
    scan = scan.sort_values(["p_std", "host", "gpu"], ascending=[False, True, True])
    top = scan.iloc[0]
    return str(top.host), int(top.gpu), scan


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    os.makedirs(DOCS, exist_ok=True)
    cfg = dta.load_config()
    dt = float(cfg["dataset"]["dt_s"])
    H = int(cfg["experiment"]["horizon"])
    log(f"dataset root: {cfg['dataset']['root_abs']}")

    # ---- PHASE 1: channel map verification ---------------------------------
    log("verifying GPU power<->temperature channel mapping (naming not trusted)...")
    cmap = dta.verify_channel_map(cfg)
    log(f"  channel map agreement: {cmap['agree']}/{cmap['checked']} "
        f"({cmap['agreement_rate']:.1%})")
    if cmap["agreement_rate"] < 0.9:
        log("BLOCKER: channel mapping unreliable; aborting")
        return 2

    # ---- trace selection ----------------------------------------------------
    scan_path = os.path.join(RESULTS, "trace_scan.csv")
    if os.path.exists(scan_path):
        scan = pd.read_csv(scan_path)
        scan = scan.sort_values(["p_std", "host", "gpu"], ascending=[False, True, True])
        host, gpu = str(scan.iloc[0].host), int(scan.iloc[0].gpu)
        log(f"loaded trace scan cache ({len(scan)} traces)")
    else:
        log("scanning traces for usability and power excitation...")
        host, gpu, scan = select_trace(cfg)
    log(f"selected trace: host={host} gpu={gpu} (max power std -> most excitation)")
    log(f"usable GPU traces: {len(scan)}")

    tr = dta.load_trace(cfg, host, gpu)
    a = tr.audit
    log(f"  usable rows {a['n_usable']:,} of {a['n_raw']:,}; segments {a['n_segments']}; "
        f"dup timestamps {a['n_duplicate_timestamps']}; monotonic {a['timestamps_monotonic']}")
    log(f"  Tg {a['Tg']['min']:.1f}-{a['Tg']['max']:.1f}C  "
        f"Tm {a['Tm']['min']:.1f}-{a['Tm']['max']:.1f}C  "
        f"P {a['P']['min']:.0f}-{a['P']['max']:.0f}W")
    log(f"  median(Tg-Tm) = {a['median_Tg_minus_Tm']:.2f} C  (die hotter => heat can flow die->HBM)")
    log(f"  corr(Tg,Tm)={a['corr_Tg_Tm']:.3f}  corr(P,Tg)={a['corr_P_Tg']:.3f}")

    sp = dta.chronological_split(tr.df, cfg)
    log(f"chronological split on segment {sp['segment_id']}: "
        f"train {len(sp['train']):,} / val {len(sp['val']):,} / test {len(sp['test']):,}")

    # ---- PHASE 7: sampling / resolvability ---------------------------------
    log("sampling-resolution analysis (can 10 s distinguish coupling from common power?)...")
    samp = an.sampling_analysis(sp["train"], dt)
    log(f"  argmax dP->dTg lag = {samp['argmax_dP_to_dTg']}")
    log(f"  argmax dTg->dTm lag = {samp['argmax_dTg_to_dTm']}")
    log(f"  argmax PARTIAL (power removed) = {samp['argmax_partial']} "
        f"peak={samp['peak_partial']:.4f}")
    log(f"  coupling lag resolvable at 10 s: {samp['coupling_lag_resolvable']}")

    # ---- PHASES 2-4: fit on TRAIN only --------------------------------------
    fits, models = {}, {}
    for M in (OneNodeModel, TwoNodeModel, UnconstrainedModel):
        m = M(dt=dt).fit(sp["train"])
        models[m.name] = m
        fits[m.name] = m.report_
        log(f"fitted {m.name}: admissible={m.report_.admissible} "
            f"violations={m.report_.violations} cond={ {k: round(v,1) for k,v in m.report_.cond.items()} }")
        if m.name != "unconstrained":
            log("   params: " + ", ".join(
                f"{k}={v:.4g}" for k, v in m.report_.params.items()))

    # ---- PHASE 3: evaluate on held-out TEST ---------------------------------
    rows, preds = [], {}
    for name, m in models.items():
        pg, pm, tg, tm = one_step(m, sp["test"])
        rows += [dict(model=name, task="one-step", target="Tg", **an.metrics(tg, pg)),
                 dict(model=name, task="one-step", target="Tm", **an.metrics(tm, pm))]
        pg, pm, tg, tm = rollout(m, sp["test"], H)
        rows += [dict(model=name, task="multi-step", target="Tg", **an.metrics(tg, pg)),
                 dict(model=name, task="multi-step", target="Tm", **an.metrics(tm, pm))]
        preds[name] = dict(Tg_pred=pg, Tm_pred=pm, Tg_true=tg, Tm_true=tm)
    res = pd.DataFrame(rows)
    res.insert(0, "host", host); res.insert(1, "gpu", gpu)
    res.to_csv(os.path.join(RESULTS, "single_gpu_metrics.csv"), index=False)

    log("\n=== HELD-OUT TEST METRICS (degC) ===")
    for task in ("one-step", "multi-step"):
        for tgt in ("Tg", "Tm"):
            sub = res[(res.task == task) & (res.target == tgt)].sort_values("RMSE")
            log(f"\n-- {task} / {tgt} --")
            log(sub[["model", "RMSE", "MAE", "MaxAE", "n"]].to_string(
                index=False, float_format=lambda v: f"{v:.4f}"))

    # ---- PHASE 6: falsification --------------------------------------------
    fal = an.falsification(res, fits, samp, primary="multi-step")
    log("\n=== FALSIFICATION TESTS ===")
    for k, v in fal["kill_flags"].items():
        log(f"  [{'TRIGGERED' if v else 'passed   '}] {k}")
    log(f"  HBM RMSE gain from coupling: {fal['gain_Tm_pct']:+.2f}%")
    log(f"  die RMSE gain from coupling: {fal['gain_Tg_pct']:+.2f}%")

    an.plot_result(sp["test"], preds,
                   os.path.join(RESULTS, "single_gpu_prediction.png"),
                   f"Held-out free-running prediction (H={H}) - {host} GPU{gpu}")
    log(f"figure: {RESULTS}/single_gpu_prediction.png")

    n_trig = fal["n_triggered"]
    if n_trig == 0 and fal["gain_Tm_pct"] > 10:
        verdict = "GO"
    elif fal["kill_flags"]["K1_two_node_not_better"] or fal["kill_flags"]["K2_coupling_not_identifiable"]:
        verdict = "KILL"
    elif n_trig <= 1 and fal["gain_Tm_pct"] > 0:
        verdict = "INVESTIGATE"
    else:
        verdict = "KILL"

    summary = dict(host=host, gpu=gpu, n_usable_traces=int(len(scan)),
                   channel_map=cmap["agreement_rate"], audit=a,
                   split={k: int(len(sp[k])) for k in ("train", "val", "test")},
                   horizon=H, sampling=samp, falsification=fal,
                   two_node_params=fits["two-node"].params,
                   two_node_admissible=fits["two-node"].admissible,
                   verdict=verdict)
    with open(os.path.join(RESULTS, "single_gpu_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2, default=str)
    with open(os.path.join(DOCS, "DATA_AUDIT.json"), "w") as fh:
        json.dump(dict(channel_map=cmap, trace_audit=a), fh, indent=2, default=str)

    log(f"\n=== VERDICT: {verdict} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
