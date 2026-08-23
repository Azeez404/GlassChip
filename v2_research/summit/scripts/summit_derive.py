"""GLASSCHIP-V2 Phase 1.5 - derived (cleaned) Summit dataset builder.

Read-only w.r.t. raw; V1 untouched. No modelling.

Established cause of duplicate timestamps (see chat / forensics):
  * 98.8% are INTRA-file: a 10 s timestamp carries 2+ ADJACENT rows that are
    fully populated with slightly different values -> two near-simultaneous
    sub-samples binned to the same 10 s label (all timestamps lie exactly on
    the 10 s grid; files are globally sorted with no concatenation boundary).
  * ~1.2% are INTER-file day-boundary spill.

Resolution policy (justified in --compare, applied in --build):
  MEAN-AGGREGATE each (host,timestamp) group with column-semantic reducers:
    *_mean / *_power / *_temp / ps*  -> mean   (matches the dataset's own
                                                 10 s-mean semantics; order-
                                                 independent, deterministic)
    *_min -> min,  *_max -> max      (preserve extreme semantics)
  Exact-duplicate groups collapse trivially (mean of equals = value).
  This never fabricates across the grid: one measured 10 s bin -> one row.

Dtype: all numeric sensors -> Float64 (some raw files store Float32/Float64
mix; unify). Nulls are PRESERVED (never interpolated here). Multi-sample bins
flagged (n_merged); collection gaps segment the series (never bridged).

Usage:
  python summit_derive.py --compare              # policy comparison, 5 nodes
  python summit_derive.py --build --nodes 5      # build derived for 5 pilots
  python summit_derive.py --build --all          # build derived for 58 hosts
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

RAW = Path("v2_research/summit/raw/a_fullperiod_10sec_58hosts_decomp")
DERIVED = Path("v2_research/summit/derived")
GRID_S = 10
GAP_BREAK_S = 30           # dt > 30 s (>2 missing) starts a new segment
SHORT_GAP_MAX_S = 30       # dt in (10, 30] = short gap (<=2 missing): maybe interpolable later
KEY_COLS = ["p0_core_temp_mean", "p1_core_temp_mean", "p0_power", "p1_power"]
TEMP_VALID = (0.0, 125.0)
DTDT_ABS_FLAG = 5.0        # |dT/dt| per 10 s beyond this is flagged (not removed)
try:
    SCAN_KW = {"cast_options": pl.ScanCastOptions(float_cast="downcast")}
except Exception:  # noqa: BLE001
    SCAN_KW = {}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def host_dirs() -> list[Path]:
    return sorted(p for p in RAW.iterdir() if p.is_dir())


def pilot_nodes(n: int = 5) -> list[str]:
    """Deterministic: rank by (most files, name), take top n, sorted. (Same
    rule as the phase-1 audit / inventory.)"""
    ranked = sorted(host_dirs(), key=lambda d: (-len(list(d.rglob("*.parquet"))), d.name))
    return sorted(d.name for d in ranked[:n])


def numeric_cols(cols: list[str]) -> list[str]:
    return [c for c in cols if c not in ("timestamp", "hostname")]


def agg_exprs(cols: list[str]) -> list[pl.Expr]:
    out = []
    for c in numeric_cols(cols):
        col = pl.col(c).cast(pl.Float64)
        if c.endswith("_min"):
            out.append(col.min().alias(c))
        elif c.endswith("_max"):
            out.append(col.max().alias(c))
        else:
            out.append(col.mean().alias(c))
    out.append(pl.len().alias("n_merged"))
    return out


def load_host(host: str) -> tuple[pl.DataFrame, list[str]]:
    files = sorted((RAW / host).rglob("*.parquet"))
    lf = pl.scan_parquet([str(f) for f in files], **SCAN_KW)
    cols = lf.collect_schema().names()
    return lf.collect(), cols


def clean_host(host: str) -> dict:
    """Apply the resolution policy to one host; return frame + stats."""
    raw, cols = load_host(host)
    rows_before = raw.height
    # aggregate conflicting/duplicate timestamps into one physical 10 s bin
    cleaned = (raw.group_by("timestamp")
               .agg([pl.col("hostname").first().alias("hostname"), *agg_exprs(cols)])
               .sort("timestamp"))
    rows_after = cleaned.height
    # temporal structure: dt, segments (never bridge large gaps)
    cleaned = cleaned.with_columns(
        pl.col("timestamp").diff().dt.total_seconds().alias("dt_s"))
    cleaned = cleaned.with_columns(
        (pl.col("dt_s") > GAP_BREAK_S).fill_null(False).cum_sum().alias("segment_id"))
    return {"host": host, "raw": raw, "cleaned": cleaned,
            "cols": cols, "rows_before": rows_before, "rows_after": rows_after}


# --------------------------------------------------------------------------- #
# policy comparison                                                           #
# --------------------------------------------------------------------------- #
def compare_policies(nodes: list[str]) -> dict:
    report = {"generated": now(), "nodes": nodes, "policies": {}, "per_host": {}}
    agg_spread = {c: [] for c in KEY_COLS}
    tot_before = tot_after = 0
    for host in nodes:
        raw, cols = load_host(host)
        before = raw.height
        # merged (mean) result + per-bin spread for key cols
        spread_exprs = [(pl.col(c).cast(pl.Float64).max()
                         - pl.col(c).cast(pl.Float64).min()).alias(f"spr_{c}")
                        for c in KEY_COLS]
        g = (raw.group_by("timestamp")
             .agg(pl.len().alias("n"), *spread_exprs,
                  *[pl.col(c).cast(pl.Float64).mean().alias(f"mean_{c}") for c in KEY_COLS],
                  *[pl.col(c).cast(pl.Float64).first().alias(f"first_{c}") for c in KEY_COLS]))
        after = g.height
        tot_before += before
        tot_after += after
        merged = g.filter(pl.col("n") > 1)
        host_stat = {"rows_before": before, "rows_after_dedup": after,
                     "removed": before - after,
                     "pct_removed": round(100 * (before - after) / before, 3),
                     "merged_bins": merged.height,
                     "max_multiplicity": int(g["n"].max()),
                     "node_hours": round(after * GRID_S / 3600, 1)}
        for c in KEY_COLS:
            if merged.height:
                spr = merged[f"spr_{c}"].drop_nulls().to_numpy()
                # |mean - first| = half the 2-sample spread; general proxy of
                # single-pick distortion vs the order-independent mean
                dev = np.abs((merged[f"mean_{c}"] - merged[f"first_{c}"]).drop_nulls().to_numpy())
                host_stat[f"{c}__mean_bin_spread"] = float(np.mean(spr)) if spr.size else 0.0
                host_stat[f"{c}__max_bin_spread"] = float(np.max(spr)) if spr.size else 0.0
                host_stat[f"{c}__first_vs_mean_rms"] = float(np.sqrt(np.mean(dev**2))) if dev.size else 0.0
                agg_spread[c].extend(spr.tolist())
        report["per_host"][host] = host_stat

    # policy-level rollup
    report["policies"]["A_exact_only"] = {
        "valid_final_grid": False,
        "note": "removes only exact-identical rows; conflicting same-ts bins REMAIN "
                "-> grid still has duplicate timestamps. Rejected."}
    report["policies"]["B_first_or_last"] = {
        "valid_final_grid": True,
        "note": "keeps one arbitrary sub-sample; order-DEPENDENT among near-"
                "simultaneous samples. Distortion vs mean below."}
    report["policies"]["C_mean_aggregate"] = {
        "valid_final_grid": True, "recommended": True,
        "note": "order-independent; matches the dataset's own 10 s-mean semantics; "
                "one measured bin -> one row; deterministic."}
    for c in KEY_COLS:
        arr = np.array(agg_spread[c]) if agg_spread[c] else np.array([0.0])
        unit = "C" if "temp" in c else "W"
        report["policies"]["C_mean_aggregate"][f"{c}_bin_spread_median_{unit}"] = float(np.median(arr))
        report["policies"]["C_mean_aggregate"][f"{c}_bin_spread_p99_{unit}"] = float(np.percentile(arr, 99))
    report["totals"] = {"rows_before": tot_before, "rows_after": tot_after,
                        "removed": tot_before - tot_after,
                        "pct_removed": round(100 * (tot_before - tot_after) / tot_before, 3)}
    return report


# --------------------------------------------------------------------------- #
# missing-data + physical audit on a cleaned host                             #
# --------------------------------------------------------------------------- #
def null_runs(mask: np.ndarray) -> dict:
    """Run-length stats of True (null) in a boolean array."""
    if not mask.any():
        return {"nulls": 0, "runs": 0, "max_run": 0, "isolated": 0, "clustered_gt2": 0}
    idx = np.flatnonzero(np.diff(np.concatenate(([0], mask.view(np.int8), [0]))))
    starts, ends = idx[::2], idx[1::2]
    lengths = ends - starts
    return {"nulls": int(mask.sum()), "runs": int(lengths.size),
            "max_run": int(lengths.max()), "isolated": int((lengths == 1).sum()),
            "clustered_gt2": int((lengths > 2).sum())}


def audit_cleaned(host: str, cleaned: pl.DataFrame, cols: list[str]) -> dict:
    ncols = numeric_cols(cols)
    a: dict = {"host": host, "rows": cleaned.height}
    # temporal validation
    dt = cleaned["dt_s"].drop_nulls().to_numpy()
    within = dt[dt <= GAP_BREAK_S]
    a["temporal"] = {
        "dominant_dt_s": int(np.bincount(within.astype(int)).argmax()) if within.size else None,
        "median_dt_s": float(np.median(within)) if within.size else None,
        "pct_dt_eq_10_within_seg": round(100 * np.mean(within == GRID_S), 3) if within.size else None,
        "remaining_duplicate_ts": int(cleaned.height - cleaned["timestamp"].n_unique()),
        "n_segments": int(cleaned["segment_id"].max() + 1),
        "n_short_gaps_le_30s": int(np.sum((dt > GRID_S) & (dt <= SHORT_GAP_MAX_S))),
        "n_large_gaps_gt_30s": int(np.sum(dt > GAP_BREAK_S)),
        "max_gap_s": int(dt.max()) if dt.size else 0,
        "monotonic": bool(np.all(np.diff(cleaned["timestamp"].to_numpy()).astype("int64") > 0)),
        "node_hours_total": round(cleaned.height * GRID_S / 3600, 1),
        "longest_segment_hours": round(
            cleaned.group_by("segment_id").len()["len"].max() * GRID_S / 3600, 1),
    }
    # missing-data audit (per key column: run lengths)
    md = {}
    for c in ncols:
        m = cleaned[c].is_null().to_numpy()
        if m.any():
            r = null_runs(m)
            r["null_pct"] = round(100 * r["nulls"] / cleaned.height, 3)
            md[c] = r
    a["missing"] = md
    # physical sanity (flag, never drop)
    phys = {}
    for c in [x for x in ncols if x.endswith("temp") or "temp" in x]:
        v = cleaned[c].drop_nulls().to_numpy()
        if v.size:
            phys[c] = {"min": float(v.min()), "max": float(v.max()),
                       "out_of_range": int(np.sum((v < TEMP_VALID[0]) | (v > TEMP_VALID[1])))}
    pows = {c: {"min": float(cleaned[c].drop_nulls().min() or 0),
                "neg": int((cleaned[c] < 0).sum())}
            for c in ncols if "power" in c}
    # dT/dt on p0_core_temp_mean within segments
    dtdt_stat = {}
    for tcol in ["p0_core_temp_mean", "p1_core_temp_mean"]:
        if tcol in cleaned.columns:
            df2 = cleaned.select(["segment_id", tcol]).with_columns(
                pl.col(tcol).diff().over("segment_id").alias("dT"))
            d = df2["dT"].drop_nulls().to_numpy()
            if d.size:
                dtdt_stat[tcol] = {"std": float(np.std(d)), "max_abs": float(np.max(np.abs(d))),
                                   "n_flagged_gt5C": int(np.sum(np.abs(d) > DTDT_ABS_FLAG))}
    # corr(P,T)
    corr = {}
    for tcol, pcol in [("p0_core_temp_mean", "p0_power"), ("p1_core_temp_mean", "p1_power")]:
        if tcol in cleaned.columns and pcol in cleaned.columns:
            sub = cleaned.select([tcol, pcol]).drop_nulls()
            if sub.height > 100 and sub[tcol].std() and sub[pcol].std():
                corr[f"{tcol}~{pcol}"] = float(np.corrcoef(sub[tcol], sub[pcol])[0, 1])
    a["physical"] = {"temperatures": phys, "powers": pows, "dTdt": dtdt_stat, "corr_PT": corr}
    return a


def fail_loud(audit: dict) -> list[str]:
    """Return list of hard failures that make the cleaned host physically suspect."""
    f = []
    t = audit["temporal"]
    if t["remaining_duplicate_ts"] != 0:
        f.append("duplicate timestamps remain after cleaning")
    if not t["monotonic"]:
        f.append("timestamps not strictly increasing")
    if t["dominant_dt_s"] not in (GRID_S, None):
        f.append(f"dominant dt != 10 s ({t['dominant_dt_s']})")
    for c, p in audit["physical"]["temperatures"].items():
        if p["out_of_range"] > 0:
            f.append(f"{c}: {p['out_of_range']} temps out of range")
    for c, p in audit["physical"]["powers"].items():
        if p["neg"] > 0:
            f.append(f"{c}: {p['neg']} negative power values")
    return f


# --------------------------------------------------------------------------- #
def build(nodes: list[str]) -> dict:
    (DERIVED / "cleaned").mkdir(parents=True, exist_ok=True)
    (DERIVED / "manifests").mkdir(parents=True, exist_ok=True)
    (DERIVED / "quality_masks").mkdir(parents=True, exist_ok=True)
    gsummary = {"generated": now(), "policy": "C_mean_aggregate", "grid_s": GRID_S,
                "gap_break_s": GAP_BREAK_S, "dtype": "Float64", "interpolation": "none",
                "nodes": [], "totals": {"rows_before": 0, "rows_after": 0},
                "failures": {}}
    for i, host in enumerate(nodes, 1):
        t0 = time.time()
        c = clean_host(host)
        cleaned, cols = c["cleaned"], c["cols"]
        audit = audit_cleaned(host, cleaned, cols)
        fails = fail_loud(audit)

        # write cleaned data partitioned by host (column-projected: keep all
        # aggregated sensors + provenance columns)
        hd = DERIVED / "cleaned" / f"host={host}"
        hd.mkdir(parents=True, exist_ok=True)
        cleaned.write_parquet(hd / "data.parquet")
        # compact quality mask
        (cleaned.select(["timestamp", "n_merged", "segment_id", "dt_s"])
         .with_columns((pl.col("n_merged") > 1).alias("was_merged"))
         .write_parquet(DERIVED / "quality_masks" / f"{host}.parquet"))
        # per-host manifest with provenance + audit
        src_files = sorted(str(p.relative_to(RAW)) for p in (RAW / host).rglob("*.parquet"))
        manifest = {"host": host, "generated": now(),
                    "provenance": {"raw_dir": str(RAW / host), "n_source_files": len(src_files),
                                   "source_files": src_files},
                    "cleaning": {"policy": "C_mean_aggregate",
                                 "rows_before": c["rows_before"], "rows_after": c["rows_after"],
                                 "removed": c["rows_before"] - c["rows_after"],
                                 "merged_bins": int((cleaned["n_merged"] > 1).sum()),
                                 "dtype_cast_to": "Float64", "interpolation": "none"},
                    "audit": audit, "failures": fails}
        (DERIVED / "manifests" / f"{host}.json").write_text(json.dumps(manifest, indent=2, default=str))

        gsummary["nodes"].append({"host": host, "rows_before": c["rows_before"],
                                  "rows_after": c["rows_after"], "failures": fails,
                                  "node_hours": audit["temporal"]["node_hours_total"],
                                  "corr_PT": audit["physical"]["corr_PT"]})
        gsummary["totals"]["rows_before"] += c["rows_before"]
        gsummary["totals"]["rows_after"] += c["rows_after"]
        if fails:
            gsummary["failures"][host] = fails
        print(f"  [{i:>2}/{len(nodes)}] {host:<8} {c['rows_before']:>8} -> {c['rows_after']:>8} "
              f"({100*(c['rows_before']-c['rows_after'])/c['rows_before']:.1f}% merged) "
              f"nh={audit['temporal']['node_hours_total']:.0f} "
              f"corr={list(audit['physical']['corr_PT'].values())} "
              f"{'FAIL:'+';'.join(fails) if fails else 'ok'} [{time.time()-t0:.1f}s]")
    (DERIVED / "derived_manifest.json").write_text(json.dumps(gsummary, indent=2, default=str))
    return gsummary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--nodes", type=int, default=5)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    nodes = [d.name for d in host_dirs()] if args.all else pilot_nodes(args.nodes)
    print(f"[{now()}] nodes ({len(nodes)}): {nodes if len(nodes) <= 10 else nodes[:10] + ['...']}")

    if args.compare:
        rep = compare_policies(pilot_nodes(5))
        DERIVED.mkdir(parents=True, exist_ok=True)
        (DERIVED / "policy_comparison.json").write_text(json.dumps(rep, indent=2, default=str))
        print(json.dumps(rep["policies"], indent=2, default=str))
        print("totals:", rep["totals"])
        print("saved v2_research/summit/derived/policy_comparison.json")
    if args.build:
        s = build(nodes)
        print(f"\nDERIVED BUILD COMPLETE  hosts={len(s['nodes'])}  "
              f"{s['totals']['rows_before']:,} -> {s['totals']['rows_after']:,}  "
              f"failures={len(s['failures'])}")
    if not (args.compare or args.build):
        print("nothing to do; pass --compare and/or --build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
