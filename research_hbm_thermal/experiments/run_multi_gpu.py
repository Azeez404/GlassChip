"""Confirmation across several diverse GPU traces.

Purpose: establish whether the single-GPU result is a property of that trace or of
the data/hypothesis. Run only to CONFIRM a finding, never to search for a trace
that produces a favourable one - all traces attempted are reported.
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np, pandas as pd

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT,"src"))
import analysis as an, data as dta
from models import OneNodeModel, TwoNodeModel, UnconstrainedModel, rollout

def main():
    cfg=dta.load_config(); dt=float(cfg["dataset"]["dt_s"]); H=int(cfg["experiment"]["horizon"])
    scan=pd.read_csv(os.path.join(ROOT,"results","trace_scan.csv"))
    scan=scan.sort_values(["p_std","host","gpu"],ascending=[False,True,True])
    # diverse: spread across the power-excitation ranking, distinct hosts
    picks, seen = [], set()
    for _,r in scan.iterrows():
        if r.host in seen: continue
        seen.add(r.host); picks.append((str(r.host),int(r.gpu)))
        if len(picks)>=int(cfg["experiment"]["n_probe_gpus"]): break
    rows=[]
    for host,gpu in picks:
        try:
            tr=dta.load_trace(cfg,host,gpu); sp=dta.chronological_split(tr.df,cfg)
            if len(sp["train"])<5000 or len(sp["test"])<2000: 
                print(f"skip {host} gpu{gpu}: too short"); continue
            samp=an.sampling_analysis(sp["train"],dt)
            out={}
            for M in (OneNodeModel,TwoNodeModel,UnconstrainedModel):
                m=M(dt=dt).fit(sp["train"])
                pg,pm,tg,tm=rollout(m,sp["test"],H)
                out[m.name]=dict(Tm=an.metrics(tm,pm)["RMSE"],Tg=an.metrics(tg,pg)["RMSE"],rep=m.report_)
            two=out["two-node"]["rep"]
            gain=(out["one-node"]["Tm"]-out["two-node"]["Tm"])/out["one-node"]["Tm"]*100
            rows.append(dict(host=host,gpu=gpu,n_train=len(sp["train"]),n_test=len(sp["test"]),
                corr_Tg_Tm=round(tr.audit["corr_Tg_Tm"],4),
                median_Tg_minus_Tm=round(tr.audit["median_Tg_minus_Tm"],2),
                rmse_Tm_one=round(out["one-node"]["Tm"],4), rmse_Tm_two=round(out["two-node"]["Tm"],4),
                rmse_Tm_unc=round(out["unconstrained"]["Tm"],4),
                rmse_Tg_one=round(out["one-node"]["Tg"],4), rmse_Tg_two=round(out["two-node"]["Tg"],4),
                gain_Tm_pct=round(gain,2), two_node_admissible=two.admissible,
                violations=";".join(two.violations), c_m=round(two.params.get("c_m",np.nan),6),
                c_g=round(two.params.get("c_g",np.nan),6),
                tau_m_two=round(two.params.get("tau_m",np.nan),1),
                partial_lag=samp["argmax_partial"], lag_resolvable=samp["coupling_lag_resolvable"]))
            print(f"{host} gpu{gpu}: gain_Tm={gain:+.2f}%  admissible={two.admissible} "
                  f"viol={two.violations} lag={samp['argmax_partial']}",flush=True)
        except Exception as e:
            print(f"FAILED {host} gpu{gpu}: {type(e).__name__}: {e}",flush=True)
    df=pd.DataFrame(rows); df.to_csv(os.path.join(ROOT,"results","multi_gpu_metrics.csv"),index=False)
    print("\n=== MULTI-GPU CONFIRMATION ===")
    print(df.to_string(index=False))
    print()
    n=len(df)
    print(f"traces: {n}")
    print(f"two-node BEATS one-node on HBM: {int((df.gain_Tm_pct>0).sum())}/{n}")
    print(f"two-node physically admissible: {int(df.two_node_admissible.sum())}/{n}")
    print(f"coupling lag resolvable at 10s: {int(df.lag_resolvable.sum())}/{n}")
    print(f"median gain_Tm: {df.gain_Tm_pct.median():+.2f}%   worst {df.gain_Tm_pct.min():+.2f}%  best {df.gain_Tm_pct.max():+.2f}%")
    print(f"unconstrained beats two-node on HBM: {int((df.rmse_Tm_unc<df.rmse_Tm_two).sum())}/{n}")
    return 0
if __name__=="__main__": raise SystemExit(main())
