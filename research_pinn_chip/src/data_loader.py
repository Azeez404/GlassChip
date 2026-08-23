"""Data loading, trace selection, causal features and regime split.

Clean-room: reads the public Summit derived tables READ-ONLY through a configurable
path. Nothing from the GLASSCHIP source tree is imported.
"""
from __future__ import annotations

import glob
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

#: Default location of the read-only Summit derived tables. Override with the
#: GLASSCHIP_SUMMIT_DERIVED environment variable.
DEFAULT_SUMMIT_DERIVED = os.environ.get(
    "GLASSCHIP_SUMMIT_DERIVED",
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "v2_research", "summit", "derived", "cleaned",
    ),
)

#: Verified by correlation: each GPU core temperature's own power channel.
GPU_POWER = {
    0: "p0_gpu0_power", 1: "p0_gpu1_power", 2: "p0_gpu2_power",
    3: "p1_gpu0_power", 4: "p1_gpu1_power", 5: "p1_gpu2_power",
}

DT_S = 10.0          # nominal sampling interval
COLD_MAX_C = 45.0    # training regime upper bound
HOT_MIN_C = 55.0     # test regime lower bound
N_LAGS = 2           # T[n], T[n-1], T[n-2] and P likewise

FEATURES = ["T", "T_l1", "T_l2", "P", "P_l1", "P_l2", "dP", "dT"]


@dataclass
class Trace:
    host: str
    gpu: int
    df: pd.DataFrame          # feature frame with target
    n_raw: int


def _host_files(root: str) -> list[str]:
    files = sorted(glob.glob(os.path.join(root, "**", "*.parquet"), recursive=True))
    if not files:
        raise FileNotFoundError(f"No Summit parquet found under {root!r}")
    return files


def scan_traces(root: str = DEFAULT_SUMMIT_DERIVED) -> pd.DataFrame:
    """Regime coverage for every (host, gpu) trace. Used for deterministic selection."""
    rows = []
    for f in _host_files(root):
        host = os.path.basename(os.path.dirname(f)).replace("host=", "")
        cols = list(GPU_POWER.values()) + [f"gpu{i}_core_temp" for i in range(6)]
        d = pd.read_parquet(f, columns=cols)
        for g in range(6):
            t, p = d[f"gpu{g}_core_temp"], d[GPU_POWER[g]]
            ok = t.notna() & p.notna()
            if not ok.any():
                continue
            tt = t[ok]
            rows.append(dict(
                host=host, gpu=g, n=int(ok.sum()),
                n_cold=int((tt < COLD_MAX_C).sum()),
                n_hot=int((tt > HOT_MIN_C).sum()),
                n_mid=int(((tt >= COLD_MAX_C) & (tt <= HOT_MIN_C)).sum()),
                tmax=float(tt.max()), tmed=float(tt.median()),
                pmax=float(p[ok].max()),
            ))
    return pd.DataFrame(rows)


def select_trace(scan: pd.DataFrame, min_cold: int = 100_000) -> tuple[str, int]:
    """Deterministic: most hot-regime samples, subject to enough cold samples.

    Tie-break on (host, gpu) ascending. Selection never depends on model performance.
    """
    ok = scan[scan.n_cold >= min_cold]
    if ok.empty:
        raise RuntimeError("No trace satisfies the cold-regime minimum.")
    ok = ok.sort_values(["n_hot", "host", "gpu"], ascending=[False, True, True])
    top = ok.iloc[0]
    return str(top.host), int(top.gpu)


def load_trace(host: str, gpu: int, root: str = DEFAULT_SUMMIT_DERIVED) -> Trace:
    """Load one GPU trace and build strictly causal lag features.

    Lags are formed only across exact DT_S steps inside a single segment, so no
    feature ever spans a collection gap or an irregular interval.
    """
    path = os.path.join(root, f"host={host}", "data.parquet")
    if not os.path.exists(path):
        cands = [f for f in _host_files(root) if f"host={host}" in f]
        if not cands:
            raise FileNotFoundError(f"host {host!r} not found under {root!r}")
        path = cands[0]

    pcol = GPU_POWER[gpu]
    d = pd.read_parquet(path, columns=["timestamp", "segment_id", "dt_s", pcol,
                                       f"gpu{gpu}_core_temp"])
    d = d.rename(columns={pcol: "P", f"gpu{gpu}_core_temp": "T"})
    n_raw = len(d)
    d = d.dropna(subset=["T", "P"]).sort_values("timestamp").reset_index(drop=True)

    # Causal lags within segment; require the regular 10 s grid for every step used.
    g = d.groupby("segment_id", sort=False)
    d["T_l1"], d["T_l2"] = g["T"].shift(1), g["T"].shift(2)
    d["P_l1"], d["P_l2"] = g["P"].shift(1), g["P"].shift(2)
    d["T_next"] = g["T"].shift(-1)
    d["dt_next"] = g["dt_s"].shift(-1)
    for k in (0, 1, 2):
        d[f"_dt{k}"] = g["dt_s"].shift(k)

    regular = np.ones(len(d), dtype=bool)
    for k in (0, 1, 2):
        regular &= np.isclose(d[f"_dt{k}"].to_numpy(dtype=float), DT_S)
    regular &= np.isclose(d["dt_next"].to_numpy(dtype=float), DT_S)

    d["dP"] = d["P"] - d["P_l1"]
    d["dT"] = d["T"] - d["T_l1"]

    need = FEATURES + ["T_next"]
    d = d[regular & d[need].notna().all(axis=1)].reset_index(drop=True)
    d["target_dT"] = d["T_next"] - d["T"]
    return Trace(host=host, gpu=gpu, df=d, n_raw=n_raw)


def regime_split(df: pd.DataFrame) -> dict:
    """Train = everything below COLD_MAX_C; test = everything above HOT_MIN_C.

    A sample qualifies only if its target AND every lagged temperature it uses fall
    on the same side. The 10 degC gap makes the sets disjoint by construction.
    """
    temps = df[["T", "T_l1", "T_l2", "T_next"]].to_numpy(dtype=float)
    cold = (temps < COLD_MAX_C).all(axis=1)
    hot = (temps > HOT_MIN_C).all(axis=1)
    mid = ~(cold | hot)
    return {
        "train": df[cold].reset_index(drop=True),
        "test": df[hot].reset_index(drop=True),
        "n_total": int(len(df)),
        "n_train": int(cold.sum()),
        "n_test": int(hot.sum()),
        "n_excluded": int(mid.sum()),
        "hot_pct": float(100.0 * hot.sum() / max(len(df), 1)),
    }


def hot_blocks(df: pd.DataFrame, horizon: int) -> list[np.ndarray]:
    """Contiguous hot-regime runs long enough for a free-running rollout.

    A block is a maximal run of consecutive rows (original index step of 1, same
    segment) whose temperatures are all above HOT_MIN_C.
    """
    temps = df[["T", "T_l1", "T_l2", "T_next"]].to_numpy(dtype=float)
    hot = (temps > HOT_MIN_C).all(axis=1)
    idx = np.flatnonzero(hot)
    if idx.size == 0:
        return []
    seg = df["segment_id"].to_numpy()
    blocks, start = [], idx[0]
    for a, b in zip(idx[:-1], idx[1:]):
        if b != a + 1 or seg[b] != seg[a]:
            if a - start + 1 >= horizon + 1:
                blocks.append(np.arange(start, a + 1))
            start = b
    if idx[-1] - start + 1 >= horizon + 1:
        blocks.append(np.arange(start, idx[-1] + 1))
    return blocks
