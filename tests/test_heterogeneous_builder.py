"""Tests for src/alignment/heterogeneous_builder.py.

Self-contained (assertions, no pytest). Uses tiny in-memory fixtures only -
never writes files and never substitutes for the real M100 dataset. Run:

    python tests/test_heterogeneous_builder.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from alignment import (  # noqa: E402
    HeterogeneousTimeSeriesBuilder, BuilderError, DEFAULT_ROLE_METRICS,
    DEFAULT_STALENESS_S,
)

T0 = pd.Timestamp("2021-03-01 00:00:00", tz="UTC")


def _raw(step_s: int, n: int, node="15", drop_secs=None, dupes=None, bad=False):
    """A raw single-metric frame: columns timestamp, value, node."""
    drop = drop_secs or set()
    secs = [i * step_s for i in range(n) if i * step_s not in drop]
    ts = [T0 + pd.Timedelta(seconds=s) for s in secs]
    val = [float(s) for s in secs]
    if dupes:  # append duplicate timestamps with a different (later-ignored) value
        for s in dupes:
            ts.append(T0 + pd.Timedelta(seconds=s)); val.append(-999.0)
    df = pd.DataFrame({"timestamp": ts, "value": val, "node": node})
    if bad:  # inject a malformed row (null ts) and a non-finite value
        df = pd.concat([df, pd.DataFrame({"timestamp": [pd.NaT, ts[0]],
                                          "value": [1.0, np.inf], "node": node})],
                       ignore_index=True)
    return df


def _fixture(node="15"):
    return {
        "temperature": _raw(20, 31, node),                       # 0..600 s (ref)
        "power": _raw(20, 31, node),
        "fan": _raw(20, 31, node),
        "frequency": _raw(60, 11, node),                          # 0..600 s
        "utilization": _raw(90, 7, node, drop_secs={270}),        # gap at 270 s
    }


def test_role_mapping_and_reference_metadata():
    b = HeterogeneousTimeSeriesBuilder()
    assert b.role_metrics["temperature"] == "p0_core0_temp"
    assert b.role_metrics["frequency"] == "cpu_speed"
    out, rep = b.build_node("15", raw_frames=_fixture())
    assert rep["reference"]["role"] == "temperature"
    assert rep["reference"]["metric"] == "p0_core0_temp"
    assert rep["alignment_direction"] == "backward (causal)"
    assert rep["role_to_metric"] == DEFAULT_ROLE_METRICS
    assert rep["effective_staleness_s"]["utilization"] == DEFAULT_STALENESS_S["utilization"]
    return out, rep


def test_duplicate_cleaning_and_rejection():
    b = HeterogeneousTimeSeriesBuilder()
    raw = _raw(20, 10, dupes={40, 80}, bad=True)
    clean, rep = b.clean_metric("temperature", raw)
    assert rep["n_duplicate_timestamps_dropped"] == 2
    assert rep["n_rejected"] == 2                     # NaT ts + inf value
    assert clean["timestamp"].is_monotonic_increasing
    assert not clean["timestamp"].duplicated().any()
    # kept value at a duplicated instant is the first real one (40.0), not -999
    v40 = clean.loc[clean["timestamp"] == T0 + pd.Timedelta(seconds=40), "temperature"]
    assert float(v40.iloc[0]) == 40.0


def test_native_interval_estimation():
    _, rep = test_role_mapping_and_reference_metadata()
    m = rep["metrics"]
    assert abs(rep["cleaning"]["temperature"]["native_interval_s"] - 20) < 1e-6
    assert abs(rep["cleaning"]["frequency"]["native_interval_s"] - 60) < 1e-6
    assert abs(rep["cleaning"]["utilization"]["native_interval_s"] - 90) < 1e-6


def test_backward_causal_and_no_fabrication():
    out, _ = test_role_mapping_and_reference_metadata()
    # ages non-negative (backward); present slow values are actual source samples
    for col in ("frequency_age_s", "utilization_age_s"):
        a = out[col].to_numpy()
        assert np.all(a[np.isfinite(a)] >= 0.0)
    util_src = {0.0, 90.0, 180.0, 360.0, 450.0, 540.0}
    uv = out["utilization"].to_numpy()
    assert set(uv[~np.isnan(uv)]).issubset(util_src)


def test_staleness_missingness():
    out, rep = test_role_mapping_and_reference_metadata()
    secs = np.round(((out["timestamp"] - T0).dt.total_seconds()).to_numpy()).astype(int)
    miss = out.set_index(secs)["utilization_missing"]
    # util bound 135 s, sample at 180 then gap to 360 -> t=320,340 exceed 135 s
    assert bool(miss.loc[300]) is False and bool(miss.loc[320]) is True and bool(miss.loc[340]) is True
    assert bool(miss.loc[360]) is False
    ages = out["utilization_age_s"].to_numpy()
    assert np.all(ages[np.isfinite(ages)] <= rep["effective_staleness_s"]["utilization"] + 1e-9)
    # fast metrics never missing
    assert not out["power_missing"].any() and not out["fan_missing"].any()


def test_node_identity_preserved():
    out, rep = HeterogeneousTimeSeriesBuilder().build_node("42", raw_frames=_fixture("42"))
    assert (out["node"] == "42").all()
    assert rep["node"] == "42"
    assert out.columns[1] == "node"


def test_determinism():
    b = HeterogeneousTimeSeriesBuilder()
    o1, _ = b.build_node("15", raw_frames=_fixture())
    o2, _ = b.build_node("15", raw_frames=_fixture())
    assert o1.equals(o2)


def test_report_completeness():
    _, rep = test_role_mapping_and_reference_metadata()
    for key in ("node", "reference", "alignment_direction", "role_to_metric",
                "effective_staleness_s", "cleaning", "n_rows_aligned", "metrics",
                "missingness", "columns"):
        assert key in rep, key
    for role in ("temperature", "frequency", "utilization"):
        c = rep["cleaning"][role]
        for k in ("n_in", "n_rejected", "n_duplicate_timestamps_dropped", "n_out",
                  "native_interval_s"):
            assert k in c, (role, k)


def test_missing_dataset_path_actionable_error():
    # no source and no injected frames -> clear, actionable error (never fabricate)
    b = HeterogeneousTimeSeriesBuilder(source=None)
    try:
        b.build_node("15")
        raise AssertionError("expected BuilderError when no data available")
    except BuilderError as e:
        assert "No dataset loader configured" in str(e)


def main() -> int:
    tests = [test_role_mapping_and_reference_metadata, test_duplicate_cleaning_and_rejection,
             test_native_interval_estimation, test_backward_causal_and_no_fabrication,
             test_staleness_missingness, test_node_identity_preserved, test_determinism,
             test_report_completeness, test_missing_dataset_path_actionable_error]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
