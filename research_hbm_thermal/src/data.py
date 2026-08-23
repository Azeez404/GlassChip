"""Data access and auditing for the GPU/HBM thermal coupling study.

Read-only access to the public Summit derived tables through a configurable path.
No dataset is copied or modified.
"""
from __future__ import annotations

import glob
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd
import yaml

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_config(path: str | None = None) -> dict:
    path = path or os.path.join(REPO, "research_hbm_thermal", "configs", "default.yaml")
    with open(path) as fh:
        cfg = yaml.safe_load(fh)
    root = os.environ.get("GLASSCHIP_SUMMIT_DERIVED", cfg["dataset"]["root"])
    cfg["dataset"]["root_abs"] = root if os.path.isabs(root) else os.path.join(REPO, root)
    cfg["dataset"]["gpu_power_map"] = {int(k): v for k, v in
                                       cfg["dataset"]["gpu_power_map"].items()}
    return cfg


def host_files(root: str) -> list[str]:
    files = sorted(glob.glob(os.path.join(root, "**", "*.parquet"), recursive=True))
    if not files:
        raise FileNotFoundError(f"No Summit parquet under {root!r}")
    return files


def host_name(path: str) -> str:
    return os.path.basename(os.path.dirname(path)).replace("host=", "")


@dataclass
class Trace:
    """One GPU: power, die temperature, HBM temperature, on a regular grid."""
    host: str
    gpu: int
    df: pd.DataFrame
    audit: dict


def verify_channel_map(cfg: dict, n_hosts: int = 3) -> dict:
    """Confirm each GPU core temperature's own power channel is its argmax correlate.

    Naming is not trusted; the mapping is established empirically.
    """
    pm = cfg["dataset"]["gpu_power_map"]
    tcols = [f"gpu{i}_core_temp" for i in range(6)]
    pcols = [pm[i] for i in range(6)]
    agree, checked, detail = 0, 0, {}
    for f in host_files(cfg["dataset"]["root_abs"])[:n_hosts]:
        d = pd.read_parquet(f, columns=tcols + pcols).dropna()
        if len(d) < 1000:
            continue
        for g in range(6):
            corrs = {p: float(d[tcols[g]].corr(d[p])) for p in pcols}
            best = max(corrs, key=corrs.get)
            checked += 1
            agree += int(best == pm[g])
            detail[f"{host_name(f)}|gpu{g}"] = {"expected": pm[g], "argmax": best,
                                                "r_expected": round(corrs[pm[g]], 4)}
    return {"checked": checked, "agree": agree,
            "agreement_rate": round(agree / max(checked, 1), 4), "detail": detail}


def load_trace(cfg: dict, host: str, gpu: int) -> Trace:
    """Load one GPU trace with the three required signals on the regular grid.

    Rows are kept only where the sampling step equals the nominal interval, so no
    model pair ever spans a collection gap or an irregular interval.
    """
    root = cfg["dataset"]["root_abs"]
    dt_s = float(cfg["dataset"]["dt_s"])
    pcol = cfg["dataset"]["gpu_power_map"][gpu]
    cands = [f for f in host_files(root) if f"host={host}" in f]
    if not cands:
        raise FileNotFoundError(f"host {host!r} not found")
    d = pd.read_parquet(cands[0], columns=["timestamp", "segment_id", "dt_s", pcol,
                                           f"gpu{gpu}_core_temp", f"gpu{gpu}_mem_temp"])
    d = d.rename(columns={pcol: "P", f"gpu{gpu}_core_temp": "Tg",
                          f"gpu{gpu}_mem_temp": "Tm"})
    n_raw = len(d)
    n_dup = int(d["timestamp"].duplicated().sum())
    monotonic = bool(d["timestamp"].is_monotonic_increasing)
    nulls = {c: int(d[c].isna().sum()) for c in ("P", "Tg", "Tm")}

    d = d.dropna(subset=["P", "Tg", "Tm"]).sort_values("timestamp").reset_index(drop=True)
    g = d.groupby("segment_id", sort=False)
    d["Tg_next"], d["Tm_next"] = g["Tg"].shift(-1), g["Tm"].shift(-1)
    d["dt_next"] = g["dt_s"].shift(-1)
    keep = (np.isclose(d["dt_s"].to_numpy(float), dt_s)
            & np.isclose(d["dt_next"].to_numpy(float), dt_s)
            & d[["Tg_next", "Tm_next"]].notna().all(axis=1).to_numpy())
    d = d[keep].reset_index(drop=True)
    d["dTg"] = d["Tg_next"] - d["Tg"]
    d["dTm"] = d["Tm_next"] - d["Tm"]

    audit = dict(
        host=host, gpu=gpu, n_raw=n_raw, n_usable=int(len(d)),
        n_duplicate_timestamps=n_dup, timestamps_monotonic=monotonic, nulls=nulls,
        n_segments=int(d["segment_id"].nunique()),
        Tg=dict(min=float(d.Tg.min()), median=float(d.Tg.median()), max=float(d.Tg.max()),
                n_unique=int(d.Tg.nunique())),
        Tm=dict(min=float(d.Tm.min()), median=float(d.Tm.median()), max=float(d.Tm.max()),
                n_unique=int(d.Tm.nunique())),
        P=dict(min=float(d.P.min()), median=float(d.P.median()), max=float(d.P.max()),
               n_unique=int(d.P.nunique())),
        median_Tg_minus_Tm=float((d.Tg - d.Tm).median()),
        corr_Tg_Tm=float(d.Tg.corr(d.Tm)), corr_P_Tg=float(d.P.corr(d.Tg)),
        corr_P_Tm=float(d.P.corr(d.Tm)),
    )
    return Trace(host=host, gpu=gpu, df=d, audit=audit)


def chronological_split(df: pd.DataFrame, cfg: dict) -> dict:
    """Split by time, never shuffled. Uses the longest usable segment."""
    seg = df["segment_id"].value_counts().idxmax()
    s = df[df["segment_id"] == seg].sort_values("timestamp").reset_index(drop=True)
    n = len(s)
    ftr, fva = cfg["split"]["train_frac"], cfg["split"]["val_frac"]
    i1, i2 = int(n * ftr), int(n * (ftr + fva))
    return {"segment_id": int(seg), "n": n,
            "train": s.iloc[:i1].reset_index(drop=True),
            "val": s.iloc[i1:i2].reset_index(drop=True),
            "test": s.iloc[i2:].reset_index(drop=True)}
