"""GATE B — node-identity fingerprint METHOD VALIDATION (local, within-record).

Cross-record identity needs a second M100 record, which cannot be downloaded
here (Zenodo 403s direct HTTP; other months are 6.4-14.6 GB). So we validate
the *method* and test a NECESSARY precondition on the record we have (21-03):

    Can node fingerprints re-identify the same physical node across two
    disjoint time windows, above a shuffled-label chance baseline?

Within-record re-identification is EASIER than cross-record (same period,
similar workload). Therefore:
  - high within-record accuracy  -> necessary, not sufficient; method viable
  - low  within-record accuracy  -> cross-record identity is hopeless -> GATE B
                                    fails regardless of the download.

Two signature families (per node, per half):
  RAW         : level statistics (median/std/quantiles of T, P, fan).
                Optimistic - will NOT transfer across records with different
                workloads; reported only as an upper bound.
  CONDITIONAL : workload-robust hardware signatures - effective thermal
                response (tau_eff, R_eff, corr(P,T)) and fan-vs-power slope.
                This is the honest proxy for cross-record transfer.

Negative control: permute node labels; accuracy should fall to ~1/N.

Reads V1's frozen ClassicalBaselineModel read-only. No V1 file modified.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from baseline import ClassicalBaselineModel  # noqa: E402  (V1 frozen, read-only)
from preprocessing import TimeSeriesBuilder  # noqa: E402  (V1 frozen, read-only)

DATASET = "data/raw/21-03"
GAPMULT = 3.0
RNG = np.random.default_rng(0)


def longest_segment(frame):
    dt = frame["timestamp"].diff().dt.total_seconds().to_numpy()
    med = np.nanmedian(dt)
    brk = list(np.where(dt > med * GAPMULT)[0])
    b = [0] + brk + [len(frame)]
    lo, hi = max([(b[i], b[i + 1]) for i in range(len(b) - 1)],
                 key=lambda x: x[1] - x[0])
    return frame.iloc[lo:hi].reset_index(drop=True)


def signatures(T, P, fan):
    """Return (raw_vector, conditional_vector) for one node-half."""
    raw = [np.median(T), np.std(T), np.percentile(T, 10), np.percentile(T, 90),
           np.median(P), np.std(P), np.percentile(P, 90),
           np.median(fan), np.std(fan)]
    # conditional / workload-robust hardware signatures
    bf = ClassicalBaselineModel().fit([(T, P)])
    tau = bf.tau_eff_s if bf.is_stable else 0.0
    r_eff = bf.r_eff if np.isfinite(bf.r_eff) else 0.0
    corr = float(np.corrcoef(P, T)[0, 1]) if np.std(P) > 0 and np.std(T) > 0 else 0.0
    # fan response to power (slope), robust to level
    if np.std(P) > 0 and np.std(fan) > 0:
        fan_slope = float(np.polyfit(P, fan, 1)[0])
    else:
        fan_slope = 0.0
    cond = [np.clip(tau, 0, 5000), np.clip(r_eff, 0, 5), corr, fan_slope]
    return np.array(raw, float), np.array(cond, float)


def reid_accuracy(A, B):
    """Top-1 nearest-neighbour re-identification of A[i] -> B[i]."""
    # standardise columns across nodes (z-score) for fair distance
    def z(M):
        s = M.std(0); s[s == 0] = 1
        return (M - M.mean(0)) / s
    Az, Bz = z(A), z(B)
    d = np.linalg.norm(Az[:, None, :] - Bz[None, :, :], axis=2)  # (N,N)
    nn = d.argmin(1)
    return float(np.mean(nn == np.arange(len(A))))


def main():
    builder = TimeSeriesBuilder(DATASET)
    pass_nodes = json.load(open("data/exports/screening_results.json"))["pass_nodes"]
    nodes = pass_nodes[:120]                      # enough for a meaningful N

    raw_A, raw_B, con_A, con_B, used = [], [], [], [], []
    for node in nodes:
        seg = longest_segment(builder.build_timeseries(node))
        if len(seg) < 2000:
            continue
        h = len(seg) // 2
        Ta, Pa, Fa = (seg["temperature"].to_numpy()[:h],
                      seg["power"].to_numpy()[:h], seg["fan_speed"].to_numpy()[:h])
        Tb, Pb, Fb = (seg["temperature"].to_numpy()[h:],
                      seg["power"].to_numpy()[h:], seg["fan_speed"].to_numpy()[h:])
        ra, ca = signatures(Ta, Pa, Fa)
        rb, cb = signatures(Tb, Pb, Fb)
        if not (np.all(np.isfinite(ra)) and np.all(np.isfinite(cb))):
            continue
        raw_A.append(ra); raw_B.append(rb); con_A.append(ca); con_B.append(cb)
        used.append(node)

    raw_A, raw_B = np.array(raw_A), np.array(raw_B)
    con_A, con_B = np.array(con_A), np.array(con_B)
    N = len(used)
    chance = 1.0 / N

    acc_raw = reid_accuracy(raw_A, raw_B)
    acc_con = reid_accuracy(con_A, con_B)

    # negative control: shuffle B labels, repeat
    def shuffled(A, B, k=200):
        accs = []
        for _ in range(k):
            perm = RNG.permutation(len(B))
            accs.append(reid_accuracy(A, B[perm]))
        return float(np.mean(accs)), float(np.std(accs))
    sh_raw_m, sh_raw_s = shuffled(raw_A, raw_B)
    sh_con_m, sh_con_s = shuffled(con_A, con_B)

    print(f"N = {N} PASS nodes, split into two time halves of the 62 h window")
    print(f"chance (1/N) = {chance:.4f}\n")
    print(f"{'signature':<12}{'reid acc':>10}{'shuffled':>12}{'z vs shuffle':>14}")
    for name, acc, shm, shs in [("RAW", acc_raw, sh_raw_m, sh_raw_s),
                                 ("CONDITIONAL", acc_con, sh_con_m, sh_con_s)]:
        z = (acc - shm) / shs if shs > 0 else float("inf")
        print(f"{name:<12}{acc:>10.3f}{shm:>12.4f}{z:>14.1f}")

    out = {"n_nodes": N, "chance": chance,
           "raw": {"reid_acc": acc_raw, "shuffled_mean": sh_raw_m},
           "conditional": {"reid_acc": acc_con, "shuffled_mean": sh_con_m},
           "note": "within-record; easier than cross-record. High != sufficient; low = fatal."}
    Path("v2_research/d2_longitudinal/results").mkdir(parents=True, exist_ok=True)
    Path("v2_research/d2_longitudinal/results/gateB_fingerprint_validation.json").write_text(
        json.dumps(out, indent=2))
    print("\nsaved results/gateB_fingerprint_validation.json")


if __name__ == "__main__":
    main()
