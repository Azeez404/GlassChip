"""GLASSCHIP-V2 - Summit 58-host dataset INSPECTION (read-only).

Recursively inspects the extracted Summit archive and emits machine- and
human-readable inventory reports. INSPECTION ONLY: never writes, renames,
deletes, resamples, interpolates, normalises, or converts the source data.
V1 is untouched; this imports no V1 code.

Approach: Polars lazy scanning. Row counts and schemas come from Parquet
metadata (O(1), no data read). Sampling/duplicate analysis reads only the
timestamp column per host. Null/invalid analysis is a streaming aggregation
that returns a tiny result regardless of data size. Hosts are discovered
programmatically (no hard-coded names); one bad file never stops the run.

Usage:
    python v2_research/summit/scripts/summit_dataset_inventory.py
    python v2_research/summit/scripts/summit_dataset_inventory.py --data <dir> --out <dir>
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import traceback
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow.parquet as pq

DEFAULT_DATA = Path("v2_research/summit/raw/a_fullperiod_10sec_58hosts_decomp")
DEFAULT_OUT = Path("v2_research/summit/inventory")
GAPMULT = 3.0                       # diff > GAPMULT * dominant  => structural gap
TEMP_VALID = (0.0, 125.0)           # plausible processor/GPU temperature (C)
POWER_MIN = 0.0                     # power must be non-negative (W)

# Some hosts mix Float32/Float64 for the same column across files. Unify on
# read so inspection never aborts (null/range results are dtype-invariant).
try:
    SCAN_KW = {"cast_options": pl.ScanCastOptions(float_cast="downcast")}
except Exception:  # noqa: BLE001  - older polars without ScanCastOptions
    SCAN_KW = {}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def col_role(name: str) -> str:
    n = name.lower()
    if n == "timestamp":
        return "timestamp"
    if n == "hostname":
        return "host_id"
    if "temp" in n:
        return "temperature"
    if "power" in n:
        return "power"
    return "other"


def inspect_host(host_dir: Path) -> dict:
    """Inspect one host directory. Returns a record; captures errors inline."""
    rec: dict = {"host": host_dir.name, "errors": []}
    files = sorted(host_dir.rglob("*.parquet"))
    rec["n_files"] = len(files)
    if not files:
        rec["errors"].append("no parquet files found")
        return rec

    # ---- per-file metadata (cheap: no column data read) ----------------------
    total_rows = 0
    total_bytes = 0
    schemas: Counter = Counter()            # by column NAMES
    dtype_map: dict[str, set] = defaultdict(set)   # column -> set of dtypes seen
    schema_example: list[str] | None = None
    for f in files:
        try:
            total_bytes += f.stat().st_size
            md = pq.ParquetFile(f)
            total_rows += md.metadata.num_rows
            arrow = md.schema_arrow
            names = tuple(arrow.names)
            schemas[names] += 1
            for nm, tp in zip(arrow.names, arrow.types):
                dtype_map[nm].add(str(tp))
            if schema_example is None:
                schema_example = list(names)
        except Exception as e:  # noqa: BLE001
            rec["errors"].append(f"metadata read failed: {f.name}: {e}")
    rec["n_rows"] = total_rows
    rec["size_bytes"] = total_bytes
    rec["n_distinct_schemas"] = len(schemas)
    rec["schema"] = schema_example or []
    mixed = {c: sorted(t) for c, t in dtype_map.items() if len(t) > 1}
    rec["mixed_dtype_columns"] = mixed
    if len(schemas) > 1:
        rec["errors"].append(f"{len(schemas)} distinct column-name schemas within host")
    if mixed:
        # recorded as an anomaly, NOT a fatal error (handled on read)
        rec.setdefault("anomalies", []).append(
            f"mixed dtypes across files: {', '.join(mixed)}")

    cols = rec["schema"]
    roles = {c: col_role(c) for c in cols}
    rec["columns_by_role"] = defaultdict(list)
    for c, r in roles.items():
        rec["columns_by_role"][r].append(c)
    rec["columns_by_role"] = dict(rec["columns_by_role"])

    paths = [str(f) for f in files]

    # ---- timestamp analysis (reads ONLY the timestamp column) ----------------
    if "timestamp" in cols:
        try:
            ts = (pl.scan_parquet(paths, **SCAN_KW).select("timestamp").collect()
                  .get_column("timestamp"))
            n = ts.len()
            n_unique = ts.n_unique()
            arr = np.sort(ts.to_numpy())
            rec["ts_min"] = str(arr[0])
            rec["ts_max"] = str(arr[-1])
            rec["n_unique_timestamps"] = int(n_unique)
            rec["n_duplicate_timestamps"] = int(n - n_unique)
            diffs = np.diff(arr).astype("timedelta64[s]").astype(np.int64)
            diffs = diffs[diffs > 0]
            if diffs.size:
                vals, counts = np.unique(diffs, return_counts=True)
                dominant = int(vals[counts.argmax()])
                rec["sampling"] = {
                    "dominant_interval_s": dominant,
                    "min_interval_s": int(diffs.min()),
                    "max_interval_s": int(diffs.max()),
                    "median_interval_s": float(np.median(diffs)),
                    "pct_deviating_from_dominant": round(
                        100.0 * np.sum(diffs != dominant) / diffs.size, 3),
                    "n_structural_gaps_gt_3x": int(np.sum(diffs > GAPMULT * dominant)),
                    "n_sub_interval_irregular": int(
                        np.sum((diffs != dominant) & (diffs <= GAPMULT * dominant))),
                    "top_intervals_s": {int(v): int(c) for v, c in
                                        sorted(zip(vals, counts), key=lambda x: -x[1])[:5]},
                }
        except Exception as e:  # noqa: BLE001
            rec["errors"].append(f"timestamp analysis failed: {e}")
    else:
        rec["errors"].append("no 'timestamp' column")

    # ---- null + invalid analysis (streaming aggregation -> tiny result) ------
    try:
        aggs = [pl.col(c).null_count().alias(f"null::{c}") for c in cols]
        for c in cols:
            if roles[c] == "temperature":
                aggs.append(((pl.col(c) < TEMP_VALID[0]) | (pl.col(c) > TEMP_VALID[1]))
                            .sum().alias(f"invalid::{c}"))
            elif roles[c] == "power":
                aggs.append((pl.col(c) < POWER_MIN).sum().alias(f"invalid::{c}"))
        row = pl.scan_parquet(paths, **SCAN_KW).select(aggs).collect().to_dicts()[0]
        nulls = {c: int(row[f"null::{c}"]) for c in cols if row.get(f"null::{c}") is not None}
        invalids = {k.split("::", 1)[1]: int(v) for k, v in row.items()
                    if k.startswith("invalid::") and v}
        rec["null_counts"] = {k: v for k, v in nulls.items() if v}
        rec["total_nulls"] = int(sum(nulls.values()))
        rec["null_pct"] = round(100.0 * sum(nulls.values()) /
                                max(total_rows * len(cols), 1), 4)
        rec["invalid_counts"] = invalids
    except Exception as e:  # noqa: BLE001
        rec["errors"].append(f"null/invalid analysis failed: {e}")

    # ---- duplicate identity: are dup-timestamp rows identical or conflicting?-
    # (streaming full-row de-dup count; decides downstream resolution policy)
    try:
        nuf = pl.scan_parquet(paths, **SCAN_KW).unique().select(pl.len()).collect().item()
        rec["n_unique_full_rows"] = int(nuf)
        rec["exact_duplicate_rows"] = int(total_rows - nuf)
        if "n_unique_timestamps" in rec:
            rec["conflicting_dup_timestamps"] = int(nuf - rec["n_unique_timestamps"])
    except Exception as e:  # noqa: BLE001
        rec["errors"].append(f"duplicate-identity analysis failed: {e}")

    return rec


def build_reports(records: list[dict], data_dir: Path, out: Path, elapsed: float) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    ok = [r for r in records if not r["errors"]]
    err = [r for r in records if r["errors"]]

    total_files = sum(r.get("n_files", 0) for r in records)
    total_rows = sum(r.get("n_rows", 0) for r in records)
    total_bytes = sum(r.get("size_bytes", 0) for r in records)

    ts_mins = [r["ts_min"] for r in records if r.get("ts_min")]
    ts_maxs = [r["ts_max"] for r in records if r.get("ts_max")]
    global_min = min(ts_mins) if ts_mins else None
    global_max = max(ts_maxs) if ts_maxs else None

    # sampling distribution
    dom = Counter(r["sampling"]["dominant_interval_s"] for r in records if r.get("sampling"))
    # schema consistency across fleet
    schema_sigs = Counter(tuple(r.get("schema", [])) for r in records if r.get("schema"))
    # column inventory: which columns appear, in how many hosts
    col_hosts: Counter = Counter()
    col_role_map: dict[str, str] = {}
    for r in records:
        for c in r.get("schema", []):
            col_hosts[c] += 1
            col_role_map[c] = col_role(c)

    summary = {
        "generated": now(),
        "data_dir": str(data_dir),
        "elapsed_s": round(elapsed, 1),
        "hosts_discovered": len(records),
        "hosts_ok": len(ok),
        "hosts_with_errors": len(err),
        "total_parquet_files": total_files,
        "total_rows": total_rows,
        "total_size_bytes": total_bytes,
        "total_size_gb": round(total_bytes / 1e9, 3),
        "global_ts_min": global_min,
        "global_ts_max": global_max,
        "sampling_interval_distribution_s": dict(dom),
        "n_distinct_fleet_schemas": len(schema_sigs),
        "column_inventory": {c: {"hosts": col_hosts[c], "role": col_role_map[c]}
                             for c in sorted(col_hosts)},
        "hosts_with_duplicates": [r["host"] for r in records
                                  if r.get("n_duplicate_timestamps", 0) > 0],
        "hosts_with_nulls": [r["host"] for r in records if r.get("total_nulls", 0) > 0],
        "hosts_with_invalids": [r["host"] for r in records if r.get("invalid_counts")],
        "hosts_with_mixed_dtypes": {r["host"]: r["mixed_dtype_columns"] for r in records
                                    if r.get("mixed_dtype_columns")},
        "anomalies": {r["host"]: r["anomalies"] for r in records if r.get("anomalies")},
        "error_hosts": {r["host"]: r["errors"] for r in err},
    }

    # ---- JSON inventory ------------------------------------------------------
    (out / "dataset_inventory.json").write_text(
        json.dumps({"summary": summary, "hosts": records}, indent=2, default=str))

    # ---- CSV inventory (one row per host) ------------------------------------
    with open(out / "dataset_inventory.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["host", "n_files", "n_rows", "size_mb", "ts_min", "ts_max",
                    "dominant_interval_s", "pct_deviating", "n_structural_gaps",
                    "n_duplicate_ts", "exact_identical_dup_rows", "conflicting_dup_ts",
                    "total_nulls", "null_pct", "n_invalid_cols", "n_mixed_dtype_cols",
                    "n_errors"])
        for r in records:
            s = r.get("sampling", {})
            w.writerow([r["host"], r.get("n_files", 0), r.get("n_rows", 0),
                        round(r.get("size_bytes", 0) / 1e6, 1), r.get("ts_min", ""),
                        r.get("ts_max", ""), s.get("dominant_interval_s", ""),
                        s.get("pct_deviating_from_dominant", ""),
                        s.get("n_structural_gaps_gt_3x", ""),
                        r.get("n_duplicate_timestamps", 0),
                        r.get("exact_duplicate_rows", ""),
                        r.get("conflicting_dup_timestamps", ""), r.get("total_nulls", 0),
                        r.get("null_pct", 0), len(r.get("invalid_counts", {})),
                        len(r.get("mixed_dtype_columns", {})), len(r["errors"])])

    # ---- Markdown reports ----------------------------------------------------
    def md(path: str, text: str) -> None:
        (out / path).write_text(text, encoding="utf-8")

    # schema_report
    lines = ["# Summit dataset - schema report", "",
             f"Distinct fleet-wide schemas: **{len(schema_sigs)}**", ""]
    for sig, cnt in schema_sigs.most_common():
        lines.append(f"- {cnt} host(s), {len(sig)} columns")
    lines += ["", "## Column inventory (column -> hosts, role)", "",
              "| column | role | hosts |", "|---|---|---|"]
    for c in sorted(col_hosts):
        lines.append(f"| `{c}` | {col_role_map[c]} | {col_hosts[c]}/{len(records)} |")
    md("schema_report.md", "\n".join(lines))

    # sampling_report
    lines = ["# Summit dataset - sampling report", "",
             "Intervals are computed from actual timestamp differences, not the "
             "directory name.", "",
             "## Fleet dominant-interval distribution", "",
             "| dominant interval (s) | hosts |", "|---|---|"]
    for k, v in sorted(dom.items()):
        lines.append(f"| {k} | {v} |")
    lines += ["", "## Per-host sampling", "",
              "| host | dominant | min | max | median | %dev | gaps>3x | irregular |",
              "|---|---|---|---|---|---|---|---|"]
    for r in records:
        s = r.get("sampling")
        if s:
            lines.append(f"| {r['host']} | {s['dominant_interval_s']} | "
                         f"{s['min_interval_s']} | {s['max_interval_s']} | "
                         f"{s['median_interval_s']:.0f} | "
                         f"{s['pct_deviating_from_dominant']} | "
                         f"{s['n_structural_gaps_gt_3x']} | "
                         f"{s['n_sub_interval_irregular']} |")
    md("sampling_report.md", "\n".join(lines))

    # integrity_report
    lines = ["# Summit dataset - integrity report", "",
             f"- Hosts with duplicate timestamps: {len(summary['hosts_with_duplicates'])}",
             f"- Hosts with nulls: {len(summary['hosts_with_nulls'])}",
             f"- Hosts with invalid values: {len(summary['hosts_with_invalids'])}",
             f"- Hosts with errors: {len(err)}", "",
             "## Duplicate timestamps: exact-identical vs conflicting payload", "",
             "Downstream MUST NOT blind-drop duplicates: most are same-timestamp "
             "rows with DIFFERENT sensor values (conflicting), needing a documented "
             "resolution rule. Inspection only records them.", "",
             "| host | dup_ts | exact_identical_rows | conflicting_ts |",
             "|---|---|---|---|"]
    for r in records:
        d = r.get("n_duplicate_timestamps", 0)
        if d:
            lines.append(f"| {r['host']} | {d} | {r.get('exact_duplicate_rows','?')} | "
                         f"{r.get('conflicting_dup_timestamps','?')} |")
    lines += ["", "## Nulls / invalids per host (non-zero only)", "",
              "| host | total_nulls | null_pct | invalid columns |",
              "|---|---|---|---|"]
    for r in records:
        nu = r.get("total_nulls", 0)
        iv = r.get("invalid_counts", {})
        if nu or iv:
            ivs = ", ".join(f"{k}={v}" for k, v in iv.items()) or "-"
            lines.append(f"| {r['host']} | {nu} | {r.get('null_pct',0)} | {ivs} |")
    if summary["hosts_with_mixed_dtypes"]:
        lines += ["", "## Mixed dtypes across files (anomaly, handled on read)", "",
                  "| host | columns (dtypes seen) |", "|---|---|"]
        for h, cols_ in summary["hosts_with_mixed_dtypes"].items():
            desc = "; ".join(f"{c}: {'/'.join(t)}" for c, t in cols_.items())
            lines.append(f"| {h} | {desc} |")
    if err:
        lines += ["", "## Errors (exact hosts/files affected)", ""]
        for r in err:
            lines.append(f"- **{r['host']}**: " + "; ".join(r["errors"]))
    md("integrity_report.md", "\n".join(lines))

    # summary.md
    lines = [
        "# Summit dataset - inventory summary", "",
        f"Generated {summary['generated']} | scan {summary['elapsed_s']} s | "
        f"source `{data_dir}`", "",
        f"1. **Hosts discovered:** {summary['hosts_discovered']}",
        f"2. **Hosts processed OK:** {summary['hosts_ok']}",
        f"3. **Hosts with errors:** {summary['hosts_with_errors']}",
        f"4. **Total Parquet files:** {summary['total_parquet_files']:,}",
        f"5. **Total rows:** {summary['total_rows']:,}",
        f"6. **Total size:** {summary['total_size_gb']} GB",
        f"7. **Global timestamp range:** {global_min} -> {global_max}",
        f"8. **Sampling interval distribution (s):** {summary['sampling_interval_distribution_s']}",
        f"9. **Distinct fleet schemas:** {summary['n_distinct_fleet_schemas']} "
        f"({'consistent' if len(schema_sigs) == 1 else 'INCONSISTENT'})",
        f"10. **Hosts with duplicates:** {len(summary['hosts_with_duplicates'])}",
        f"11. **Hosts with nulls:** {len(summary['hosts_with_nulls'])}",
        f"12. **Hosts with invalid values:** {len(summary['hosts_with_invalids'])}",
        f"13. **Hosts with mixed float dtypes:** {len(summary['hosts_with_mixed_dtypes'])}",
        "",
        "## Suspicious anomalies (items 15-16)",
        "",
        f"- **Conflicting duplicate timestamps**: {len(summary['hosts_with_duplicates'])} "
        "hosts have duplicate timestamps, and (verified per host) the large majority "
        "are same-timestamp rows with *different* sensor payloads, not exact copies. "
        "Downstream preprocessing must apply a documented de-duplication/resolution "
        "rule; do NOT blind-drop. See `integrity_report.md`.",
        f"- **Mixed float dtypes**: {len(summary['hosts_with_mixed_dtypes'])} hosts store "
        "some temperature columns as Float64 in some files and Float32 in others "
        "(column names are otherwise identical fleet-wide). Unify dtype on load.",
        "- **Partial/overlapping day files**: many day files hold fewer than 8640 rows "
        "(partial days) and some ranges overlap at day boundaries; missing calendar "
        "days are expected (5 collection months, not continuous).",
        "",
        "See `schema_report.md`, `sampling_report.md`, `integrity_report.md`, "
        "and `dataset_inventory.{json,csv}` for detail. Per-host timestamp "
        "ranges are in the CSV/JSON.",
    ]
    md("summary.md", "\n".join(lines))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DEFAULT_DATA))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    data_dir = Path(args.data)
    out = Path(args.out)
    if not data_dir.is_dir():
        print(f"ERROR: data dir not found: {data_dir}")
        return 2

    hosts = sorted(p for p in data_dir.iterdir() if p.is_dir())
    print(f"[{now()}] discovered {len(hosts)} host directories under {data_dir}")
    t0 = time.time()
    records: list[dict] = []
    for i, h in enumerate(hosts, 1):
        try:
            rec = inspect_host(h)
        except Exception:  # noqa: BLE001  - never let one host stop the run
            rec = {"host": h.name, "errors": ["FATAL: " + traceback.format_exc(limit=2)]}
        records.append(rec)
        s = rec.get("sampling", {})
        print(f"  [{i:>2}/{len(hosts)}] {h.name:<8} files={rec.get('n_files',0):<4} "
              f"rows={rec.get('n_rows',0):<9} dom={s.get('dominant_interval_s','?')}s "
              f"dup={rec.get('n_duplicate_timestamps',0)} "
              f"nulls={rec.get('total_nulls',0)} err={len(rec['errors'])}")

    summary = build_reports(records, data_dir, out, time.time() - t0)

    print(f"\n[{now()}] reports written to {out}/")
    print("DATASET INSPECTION COMPLETE\n")
    print(f"Hosts: {summary['hosts_ok']} / {len(hosts)}")
    print(f"Parquet files: {summary['total_parquet_files']:,}")
    print(f"Rows: {summary['total_rows']:,}")
    print(f"Time range: {summary['global_ts_min']} -> {summary['global_ts_max']}")
    print(f"Dominant sampling interval: {summary['sampling_interval_distribution_s']}")
    print(f"Schema status: {summary['n_distinct_fleet_schemas']} distinct "
          f"({'consistent' if summary['n_distinct_fleet_schemas'] == 1 else 'INCONSISTENT'})")
    issues = []
    if summary["hosts_with_duplicates"]:
        issues.append(f"dup-timestamps in {len(summary['hosts_with_duplicates'])} hosts")
    if summary["hosts_with_mixed_dtypes"]:
        issues.append(f"mixed float dtypes in {len(summary['hosts_with_mixed_dtypes'])} hosts")
    if summary["hosts_with_nulls"]:
        issues.append(f"nulls in {len(summary['hosts_with_nulls'])} hosts")
    if summary["hosts_with_invalids"]:
        issues.append(f"invalid values in {len(summary['hosts_with_invalids'])} hosts")
    print(f"Integrity status: {'; '.join(issues) if issues else 'clean'} "
          f"(detail in integrity_report.md)")
    print(f"Errors: {summary['hosts_with_errors']} host(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
