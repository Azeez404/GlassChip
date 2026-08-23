"""GLASSCHIP-V2 Phase 1 - Summit acquisition / feasibility audit.

ACQUIRE -> VERIFY -> PILOT -> FEASIBILITY. No modelling. No PINN. No residual.
GLASSCHIP-V1 is read-only; this script never imports or modifies V1 code.

Distribution note: the Summit dataset ships via Globus only (see
metadata/dataset_metadata.json). This script does NOT download it. Place the
sample tar in  v2_research/summit/raw/  and run:

    python v2_research/summit/scripts/summit_phase1_audit.py

Behaviour:
  * raw/ empty  -> writes a BLOCKED report + exact human download instructions,
                   exits 0 (nothing fabricated).
  * tar present -> lists the archive, selects 5 reproducible pilot nodes,
                   extracts ONLY those (column-projected reads), runs the
                   temporal / quality / physical audits, and writes
                   feasibility/{pilot_manifest,pilot_quality}.json + figures.

Design for scale: per-node streaming, pyarrow column projection (only the ~8
columns needed), never loads the whole archive into RAM.
"""
from __future__ import annotations

import io
import json
import sys
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]          # v2_research/summit/
RAW = ROOT / "raw"
EXTRACTED = ROOT / "extracted"
FEAS = ROOT / "feasibility"
FIGS = FEAS / "figures"
LOGS = ROOT / "logs"
TARGET_TAR = "a_fullperiod_10sec_58hosts_decomp.tar"

# only these columns are read from parquet (projection keeps RAM/O(1) small)
PILOT_COLS = [
    "timestamp", "hostname",
    "p0_core_temp_mean", "p0_power",
    "p1_core_temp_mean", "p1_power",
    "gpu0_core_temp", "p0_gpu0_power",
]
ASSUMED_COOLANT_C = 21.0        # documented facility inlet; NOT measured (see schema.json)
N_PILOT = 5
GAPMULT = 3.0

for d in (RAW, EXTRACTED, FEAS, FIGS, LOGS):
    d.mkdir(parents=True, exist_ok=True)

_log_lines: list[str] = []


def log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {msg}"
    print(line)
    _log_lines.append(line)


def flush_log(name: str) -> None:
    (LOGS / name).write_text("\n".join(_log_lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# BLOCKED path: no data present                                               #
# --------------------------------------------------------------------------- #
DOWNLOAD_INSTRUCTIONS = f"""\
Summit sample not found in {RAW}.

The dataset is distributed via GLOBUS ONLY (no direct HTTP). To obtain it:

  1. Create/sign in to a free Globus account (https://app.globus.org) using
     any institutional / Google / ORCID identity.
  2. Install Globus Connect Personal on this machine and create a local
     endpoint (or use an existing institutional endpoint) as the destination.
  3. Open the source collection (File Manager link):
       https://app.globus.org/file-manager?origin_id=57618e0a-2c99-45ff-9694-24141b92fa17&origin_path=%2Fgen101%2Fworld-shared%2Fdoi-data%2FOLCF%2F202204%2F10.13139_OLCF_1861393%2F
  4. Transfer ONLY this file (4.6 GB) into {RAW}:
       {TARGET_TAR}
     (58 nodes, full period, 10 s means, 73,904,353 rows - best for the pilot.)
  5. Re-run this script. It will verify size, compute SHA-256, list the
     archive, build the 5-node pilot, and emit the feasibility report.

Do NOT commit the tar (already gitignored). Do NOT download the 612 GB full
set - the sample is sufficient for Phase 1.
"""


def report_blocked() -> None:
    log("ACQUISITION STATUS: BLOCKED - sample tar not present.")
    (FEAS / "pilot_manifest.json").write_text(json.dumps({
        "phase1_status": "BLOCKED_HUMAN_ACTION_REQUIRED",
        "reason": "Summit dataset is Globus-only; automated download not possible in this environment.",
        "expected_file": TARGET_TAR,
        "place_in": str(RAW),
        "download_instructions": DOWNLOAD_INSTRUCTIONS,
    }, indent=2), encoding="utf-8")
    print("\n" + DOWNLOAD_INSTRUCTIONS)
    flush_log("phase1_audit.log")


# --------------------------------------------------------------------------- #
# DATA path helpers                                                           #
# --------------------------------------------------------------------------- #
def sha256_of(path: Path, chunk=1 << 20) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def hostname_of(member_name: str) -> str | None:
    # layout: hostname/month/yyyymmdd.parquet
    parts = Path(member_name).parts
    return parts[0] if member_name.endswith(".parquet") and len(parts) >= 3 else None


def read_parquet_bytes(raw: bytes, columns: list[str]):
    import pyarrow.parquet as pq
    table = pq.read_table(io.BytesIO(raw), columns=columns)
    return table.to_pandas()


def temporal_audit(ts) -> dict:
    import pandas as pd
    ts = pd.to_datetime(ts).sort_values().reset_index(drop=True)
    dt = ts.diff().dt.total_seconds().to_numpy()[1:]
    dt = dt[np.isfinite(dt)]
    med = float(np.median(dt)) if dt.size else float("nan")
    gaps = int(np.sum(dt > med * GAPMULT)) if dt.size else 0
    return {
        "n_timestamps": int(ts.size),
        "median_interval_s": med,
        "p05_interval_s": float(np.percentile(dt, 5)) if dt.size else None,
        "p95_interval_s": float(np.percentile(dt, 95)) if dt.size else None,
        "n_gaps_gt_3x_median": gaps,
        "n_duplicate_timestamps": int(ts.duplicated().sum()),
        "monotonic_after_sort": True,
        "span_hours": float((ts.iloc[-1] - ts.iloc[0]).total_seconds() / 3600) if ts.size > 1 else 0.0,
    }


def pair_quality(T, P) -> dict:
    T = np.asarray(T, float)
    P = np.asarray(P, float)
    ok = np.isfinite(T) & np.isfinite(P)
    corr = None
    if ok.sum() > 10 and np.std(T[ok]) > 0 and np.std(P[ok]) > 0:
        corr = float(np.corrcoef(T[ok], P[ok])[0, 1])
    return {
        "n_valid_pairs": int(ok.sum()),
        "frac_missing": float(1 - ok.mean()) if T.size else 1.0,
        "temp_min_C": float(np.nanmin(T)) if np.isfinite(T).any() else None,
        "temp_max_C": float(np.nanmax(T)) if np.isfinite(T).any() else None,
        "power_min_W": float(np.nanmin(P)) if np.isfinite(P).any() else None,
        "power_max_W": float(np.nanmax(P)) if np.isfinite(P).any() else None,
        "corr_power_temp": corr,
    }


def make_figures(node: str, df) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:  # noqa: BLE001
        log(f"  (figures skipped: {e})")
        return
    import pandas as pd
    t = pd.to_datetime(df["timestamp"])
    panels = [("p0_core_temp_mean", "CPU0 temp (C)"), ("p0_power", "CPU0 power (W)"),
              ("gpu0_core_temp", "GPU0 temp (C)"), ("p0_gpu0_power", "GPU0 power (W)")]
    fig, ax = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
    for a, (col, lab) in zip(ax, panels):
        if col in df:
            a.plot(t, df[col], lw=0.4)
        a.set_ylabel(lab, fontsize=8)
    ax[-1].set_xlabel("time")
    fig.suptitle(f"Summit pilot node {node}")
    fig.tight_layout()
    fig.savefig(FIGS / f"pilot_{node}.png", dpi=90)
    plt.close(fig)


def to_v1_baseline_segments(df, socket: int = 0):
    """V2 adapter: reshape a node frame into V1 ClassicalBaselineModel segments.

    Returns list of (T, P) numpy arrays split on timestamp gaps. Does NOT import
    or run V1 - Phase 1 only proves the shape is compatible; fitting happens in
    Phase 2. V1 stays frozen.
    """
    import pandas as pd
    tcol, pcol = f"p{socket}_core_temp_mean", f"p{socket}_power"
    d = df[["timestamp", tcol, pcol]].dropna().sort_values("timestamp").reset_index(drop=True)
    if len(d) < 2:
        return []
    dt = pd.to_datetime(d["timestamp"]).diff().dt.total_seconds().to_numpy()
    med = np.nanmedian(dt[1:])
    brk = list(np.where(dt > med * GAPMULT)[0])
    bounds = [0] + brk + [len(d)]
    segs = []
    for i in range(len(bounds) - 1):
        lo, hi = bounds[i], bounds[i + 1]
        if hi - lo >= 100:
            segs.append((d[tcol].to_numpy()[lo:hi], d[pcol].to_numpy()[lo:hi]))
    return segs


# --------------------------------------------------------------------------- #
def run_pilot(tar_path: Path) -> None:
    t0 = time.time()
    size = tar_path.stat().st_size
    log(f"tar found: {tar_path.name}  ({size/1e9:.2f} GB)")
    log("computing SHA-256 (streamed)...")
    digest = sha256_of(tar_path)
    log(f"  sha256 = {digest}")

    # update metadata with real values
    meta_path = ROOT / "metadata" / "dataset_metadata.json"
    meta = json.loads(meta_path.read_text())
    meta.update({"downloaded_file": tar_path.name, "file_size_bytes": size,
                 "sha256": digest, "download_timestamp": datetime.now(timezone.utc).isoformat(),
                 "acquisition_status": "OBTAINED"})
    meta_path.write_text(json.dumps(meta, indent=2))

    # 1) list archive, group parquet members by hostname (no extraction yet)
    log("listing archive members...")
    host_members: dict[str, list[str]] = {}
    with tarfile.open(tar_path, "r") as tar:
        for m in tar:
            if not m.isfile():
                continue
            h = hostname_of(m.name)
            if h:
                host_members.setdefault(h, []).append(m.name)
    hosts = sorted(host_members)
    log(f"  {len(hosts)} hostnames, {sum(len(v) for v in host_members.values())} parquet files")

    # 2) reproducible pilot selection: sorted hostnames, evenly spaced, must have
    #    the most day-files (best coverage). Deterministic => reproducible.
    ranked = sorted(hosts, key=lambda h: (-len(host_members[h]), h))
    pilot = sorted(ranked[:N_PILOT])
    log(f"pilot nodes (top coverage, sorted): {pilot}")

    # 3) per-node streaming read (only pilot members, only projected columns)
    import pandas as pd
    manifest = {"phase1_status": None, "tar": tar_path.name, "sha256": digest,
                "n_hosts_in_archive": len(hosts), "pilot_nodes": pilot,
                "selection_rule": "sorted hostnames, ranked by (most day-files, name); top 5; reproducible",
                "columns_read": PILOT_COLS, "assumed_coolant_C": ASSUMED_COOLANT_C,
                "coolant_is_measured": False}
    quality = {}
    with tarfile.open(tar_path, "r") as tar:
        for node in pilot:
            frames = []
            for name in sorted(host_members[node]):
                f = tar.extractfile(name)
                if f is None:
                    continue
                raw = f.read()
                try:
                    frames.append(read_parquet_bytes(raw, PILOT_COLS))
                except Exception as e:  # noqa: BLE001
                    log(f"  {node}:{name} read failed: {e}")
            if not frames:
                quality[node] = {"error": "no readable parquet"}
                continue
            df = pd.concat(frames, ignore_index=True)
            df["coolant_C_assumed"] = ASSUMED_COOLANT_C
            # persist a compact per-node model-ready table (gitignored dir)
            out = EXTRACTED / f"pilot_{node}.parquet"
            df.to_parquet(out, index=False)

            ta = temporal_audit(df["timestamp"])
            cpu0 = pair_quality(df.get("p0_core_temp_mean"), df.get("p0_power"))
            cpu1 = pair_quality(df.get("p1_core_temp_mean"), df.get("p1_power"))
            gpu0 = pair_quality(df.get("gpu0_core_temp"), df.get("p0_gpu0_power"))
            seg0 = to_v1_baseline_segments(df, 0)
            quality[node] = {
                "n_rows": int(len(df)), "temporal": ta,
                "cpu_socket0": cpu0, "cpu_socket1": cpu1, "gpu0": gpu0,
                "v1_adapter_segments_cpu0": len(seg0),
                "v1_adapter_total_samples_cpu0": int(sum(len(s[0]) for s in seg0)),
                "physical_sanity": {
                    "cpu_temp_in_10_110C": (cpu0["temp_min_C"] is not None
                                            and cpu0["temp_min_C"] > 10 and cpu0["temp_max_C"] < 110),
                    "cpu_power_nonneg": (cpu0["power_min_W"] is not None and cpu0["power_min_W"] >= 0),
                    "corr_power_temp_positive": (cpu0["corr_power_temp"] is not None
                                                 and cpu0["corr_power_temp"] > 0),
                },
            }
            make_figures(node, df)
            log(f"  {node}: rows={len(df)} span={ta['span_hours']:.1f}h "
                f"dt~{ta['median_interval_s']:.0f}s cpu0_pairs={cpu0['n_valid_pairs']} "
                f"corr(P,T)={cpu0['corr_power_temp']}")

    # 4) feasibility summary
    elapsed = time.time() - t0
    total_pilot_bytes = sum(p.stat().st_size for p in EXTRACTED.glob("pilot_*.parquet"))
    feas = {
        "tar_size_GB": round(size / 1e9, 2),
        "pilot_extracted_MB": round(total_pilot_bytes / 1e6, 1),
        "pilot_nodes": len(pilot),
        "pilot_wall_time_s": round(elapsed, 1),
        "est_per_node_s": round(elapsed / max(len(pilot), 1), 2),
        "est_30_node_min": round(elapsed / max(len(pilot), 1) * 30 / 60, 1),
        "ram_strategy": "per-node streaming + column projection; peak RAM ~ one node's frame (<1 GB)",
        "notes": "10s means (not raw 1Hz); coolant assumed constant 21C (not measured).",
    }
    # pass condition (CPU temp+power clean and aligned; GPU optional)
    def clean(node_q):
        c = node_q.get("cpu_socket0", {})
        ps = node_q.get("physical_sanity", {})
        return (c.get("n_valid_pairs", 0) > 1000 and ps.get("cpu_temp_in_10_110C")
                and ps.get("cpu_power_nonneg"))
    n_clean = sum(1 for q in quality.values() if isinstance(q, dict) and clean(q))
    manifest["phase1_status"] = "PASS" if n_clean >= 3 else "REVIEW"
    manifest["n_clean_pilot_nodes"] = n_clean

    (FEAS / "pilot_manifest.json").write_text(json.dumps(manifest, indent=2))
    (FEAS / "pilot_quality.json").write_text(json.dumps({"feasibility": feas, "nodes": quality}, indent=2))
    log(f"PHASE 1 pilot status: {manifest['phase1_status']} ({n_clean}/{len(pilot)} clean CPU nodes)")
    flush_log("phase1_audit.log")


def main() -> int:
    log("=== GLASSCHIP-V2 Summit Phase 1 audit ===")
    tar_path = RAW / TARGET_TAR
    # accept any *.tar in raw/ if the exact name differs
    if not tar_path.exists():
        alt = sorted(RAW.glob("*.tar"))
        if alt:
            tar_path = alt[0]
            log(f"using archive found in raw/: {tar_path.name}")
    if not tar_path.exists():
        report_blocked()
        return 0
    try:
        import pyarrow  # noqa: F401
    except Exception:
        log("ERROR: pyarrow required to read parquet. pip install pyarrow.")
        flush_log("phase1_audit.log")
        return 2
    run_pilot(tar_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
