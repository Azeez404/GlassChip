"""GLASSCHIP-V2 Phase 2 - residual observability test.

Question: do the M100 metrics that V1 EXCLUDED contain information about the
V1 residual that V1's three inputs could not provide?

Method (OBSERVATIONS -> OBSERVABILITY, no model built):
  1. Reconstruct V1's FROZEN residual per PASS node using V1's own locked
     ClassicalBaselineModel:  r[n] = T0[n+1] - (a*T0[n] + b*P[n] + c).
  2. Assemble candidate predictors at time n (causal - never uses n+1):
       control      : P, dP, fan, T0            (V1 observables -> expect R2<=0.04)
       same_grid    : other IPMI temps on the exact 20 s grid, same plugin,
                      same node namespace (methodologically clean)
       workload     : ganglia cpu_user/system/idle/speed/load_one, causally
                      ASOF-aligned to the 20 s grid (CONDITIONAL: cross-plugin
                      node identity is UNVERIFIED per V1)
  3. Predict r[n] with a temporal 70/30 split (no shuffle). Report TEST R2 for
     linear and random-forest models, plus mutual information.

Reads V1 read-only. Writes only into v2_research/. Does not modify V1.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import mutual_info_regression
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from baseline import ClassicalBaselineModel  # noqa: E402  (V1 frozen, read-only)

BASE = "data/raw/21-03/year_month=21-03"
DT_S = 20.0


def mp(metric: str) -> str:
    import glob
    return glob.glob(f"{BASE}/plugin=*/metric={metric}/*.parquet")[0]


def load_node(con, node: str):
    """Exact-join V1 triple + same-grid IPMI extras; ASOF-join ganglia."""
    ipmi_extra = ["ambient", "p0_vdd_temp", "p1_power", "total_power",
                  "p0_core1_temp", "p1_core0_temp"]
    gang = ["cpu_user", "cpu_system", "cpu_idle", "cpu_speed", "load_one"]

    # base: V1 triple, exact timestamp inner join (same as locked pipeline)
    sel = ["t.timestamp ts", "CAST(t.value AS DOUBLE) T0",
           "CAST(p.value AS DOUBLE) P", "CAST(f.value AS DOUBLE) fan"]
    joins = [f"'{mp('p0_power')}' p ON t.timestamp=p.timestamp AND t.node=p.node",
             f"'{mp('fan0_0')}' f ON t.timestamp=f.timestamp AND t.node=f.node"]
    for m in ipmi_extra:
        sel.append(f"CAST({m}.value AS DOUBLE) {m}")
        joins.append(f"LEFT JOIN '{mp(m)}' {m} "
                     f"ON t.timestamp={m}.timestamp AND t.node={m}.node")
    q = (f"SELECT {', '.join(sel)} FROM '{mp('p0_core0_temp')}' t "
         f"JOIN {joins[0]} JOIN {joins[1]} " + " ".join(joins[2:]) +
         f" WHERE t.node='{node}' ORDER BY t.timestamp")
    df = con.execute(q).df()

    # ganglia: causal ASOF (last value at or before each 20 s timestamp)
    for m in gang:
        gq = (f"SELECT l.ts, CAST(r.value AS DOUBLE) {m} FROM df l "
              f"ASOF LEFT JOIN '{mp(m)}' r "
              f"ON r.node='{node}' AND r.timestamp <= l.ts ORDER BY l.ts")
        df = df.merge(con.execute(gq).df(), on="ts", how="left")
    return df, ipmi_extra, gang


def longest_segment(df):
    dt = df["ts"].diff().dt.total_seconds().to_numpy()
    med = np.nanmedian(dt)
    brk = list(np.where(dt > med * 3)[0])
    b = [0] + brk + [len(df)]
    lo, hi = max([(b[i], b[i + 1]) for i in range(len(b) - 1)],
                 key=lambda x: x[1] - x[0])
    return df.iloc[lo:hi].reset_index(drop=True)


def test_set(X, y):
    """Blocked time-series CV (5 expanding folds). Returns mean TEST R2
    (linear, RF) and the RF TRAIN R2 (to diagnose overfitting)."""
    from sklearn.model_selection import TimeSeriesSplit
    tss = TimeSeriesSplit(n_splits=5)
    lin_te, rf_te, rf_tr = [], [], []
    for tr, te in tss.split(X):
        lin = LinearRegression().fit(X[tr], y[tr])
        lin_te.append(r2_score(y[te], lin.predict(X[te])))
        rf = RandomForestRegressor(n_estimators=60, max_depth=6, n_jobs=-1,
                                   random_state=0).fit(X[tr], y[tr])
        rf_te.append(r2_score(y[te], rf.predict(X[te])))
        rf_tr.append(r2_score(y[tr], rf.predict(X[tr])))
    return (max(float(np.mean(lin_te)), -1.0),
            max(float(np.mean(rf_te)), -1.0),
            float(np.mean(rf_tr)))


def main():
    con = duckdb.connect(); con.execute("SET TimeZone='UTC'")
    pass_nodes = json.load(open("data/exports/screening_results.json"))["pass_nodes"]
    # representative subset spanning the fleet
    nodes = pass_nodes[:: max(1, len(pass_nodes) // 10)][:10]
    print(f"testing {len(nodes)} representative PASS nodes: {nodes}\n")

    agg = {k: {"lin": [], "rf": []} for k in
           ["control", "same_grid", "workload", "combined"]}
    mi_scores: dict[str, list] = {}

    for node in nodes:
        df, ipmi_extra, gang = load_node(con, node)
        df = longest_segment(df)
        if len(df) < 500:
            continue
        T0 = df["T0"].to_numpy(); P = df["P"].to_numpy(); fan = df["fan"].to_numpy()

        # V1 frozen residual
        bf = ClassicalBaselineModel(dt_s=DT_S).fit([(T0, P)])
        pred = bf.alpha * T0[:-1] + bf.beta * P[:-1] + bf.gamma
        r = T0[1:] - pred                      # residual, aligned to index n
        dP = np.diff(P, prepend=P[0])

        # predictors at time n (causal)
        feat = {"P": P[:-1], "dP": dP[:-1], "fan": fan[:-1], "T0": T0[:-1]}
        for m_ in ipmi_extra:
            v = df[m_].to_numpy()[:-1]
            if np.isfinite(v).mean() > 0.9 and np.nanstd(v) > 0:
                feat[m_] = np.nan_to_num(v, nan=np.nanmedian(v))
        for m_ in gang:
            v = df[m_].to_numpy()[:-1]
            if np.isfinite(v).mean() > 0.9 and np.nanstd(v) > 0:
                feat[m_] = np.nan_to_num(v, nan=np.nanmedian(v))

        control = ["P", "dP", "fan", "T0"]
        same = [c for c in ipmi_extra if c in feat]
        work = [c for c in gang if c in feat]

        def X(cols):
            return np.column_stack([feat[c] for c in cols])

        for key, cols in [("control", control), ("same_grid", control + same),
                          ("workload", control + work),
                          ("combined", control + same + work)]:
            extra = cols[len(control):]
            if key != "control" and not extra:
                continue
            l, rf, tr = test_set(X(cols), r)
            agg[key]["lin"].append(l); agg[key]["rf"].append(rf)
            agg[key].setdefault("rf_train", []).append(tr)

        # mutual information of each single candidate with the residual
        for c in same + work:
            mi = mutual_info_regression(feat[c].reshape(-1, 1), r,
                                        random_state=0)[0]
            mi_scores.setdefault(c, []).append(mi)

    print(f"{'predictor set':<12} {'linear testR2':>14} {'RF testR2':>12} "
          f"{'RF trainR2':>12}")
    for k, v in agg.items():
        if v["lin"]:
            print(f"{k:<12} {np.median(v['lin']):>14.3f} "
                  f"{np.median(v['rf']):>12.3f} "
                  f"{np.median(v.get('rf_train', [np.nan])):>12.3f}")
    print("\nmutual information with residual (median over nodes):")
    for c, s in sorted(mi_scores.items(), key=lambda kv: -np.median(kv[1])):
        print(f"  {c:<16} MI={np.median(s):.4f}")

    out = {"nodes": nodes,
           "median_test_r2": {k: {"linear": float(np.median(v["lin"])) if v["lin"] else None,
                                  "rf": float(np.median(v["rf"])) if v["rf"] else None}
                              for k, v in agg.items()},
           "mutual_information": {c: float(np.median(s)) for c, s in mi_scores.items()}}
    Path("v2_research/phase2_results.json").write_text(json.dumps(out, indent=2))
    print("\nsaved v2_research/phase2_results.json")


if __name__ == "__main__":
    main()
