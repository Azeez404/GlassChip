"""Tests for src/alignment/aligner.py (AsofAligner).

Self-contained: uses assertions, no pytest dependency. Run:

    python tests/test_aligner.py

Exercises heterogeneous native rates (temp 20 s, freq 60 s, util 90 s), a gap
that must be flagged missing, causality (no future leakage), and the guarantee
that no value is interpolated/fabricated.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from alignment import AsofAligner, AlignmentError  # noqa: E402

T0 = pd.Timestamp("2021-03-01 00:00:00", tz="UTC")


def _frame(role: str, step_s: int, n: int, drop_secs: set[int] | None = None):
    drop = drop_secs or set()
    secs = [i * step_s for i in range(n) if i * step_s not in drop]
    return pd.DataFrame({
        "timestamp": [T0 + pd.Timedelta(seconds=s) for s in secs],
        role: [float(s) for s in secs],   # value == its own second, so identifiable
    })


def test_reference_grid_and_intervals():
    temp = _frame("temperature", 20, 31)      # 0..600 s
    freq = _frame("cpu_speed", 60, 11)         # 0..600 s
    util = _frame("cpu_user", 90, 7, drop_secs={270})  # 0,90,180,360,450,540 (270 dropped)
    out, rep = AsofAligner().align({"temperature": temp, "cpu_speed": freq, "cpu_user": util})

    assert rep["reference"] == "temperature", rep["reference"]      # finest grid chosen
    assert len(out) == 31 and list(out["timestamp"]) == list(temp["timestamp"])
    assert abs(rep["metrics"]["temperature"]["native_interval_s"] - 20) < 1e-6
    assert abs(rep["metrics"]["cpu_speed"]["native_interval_s"] - 60) < 1e-6
    assert abs(rep["metrics"]["cpu_user"]["native_interval_s"] - 90) < 1e-6
    return out, rep


def test_no_fabrication_and_causality():
    out, _ = test_reference_grid_and_intervals()
    # every present slow value must be an ACTUAL source sample (no interpolation)
    freq_src = {float(i * 60) for i in range(11)}
    util_src = {0.0, 90.0, 180.0, 360.0, 450.0, 540.0}
    fv = out["cpu_speed"].to_numpy()
    uv = out["cpu_user"].to_numpy()
    assert set(fv[~np.isnan(fv)]).issubset(freq_src)
    assert set(uv[~np.isnan(uv)]).issubset(util_src)
    # causality: ages are non-negative wherever present
    for col in ("cpu_speed_age_s", "cpu_user_age_s"):
        a = out[col].to_numpy()
        assert np.all(a[np.isfinite(a)] >= 0.0)


def test_staleness_bound_and_missingness():
    out, rep = test_reference_grid_and_intervals()
    secs = ((out["timestamp"] - T0).dt.total_seconds()).to_numpy()

    # freq bound = 1.5 * 60 = 90 s; max gap between ref and last freq is 40 s -> never missing
    assert not out["cpu_speed_missing"].any()
    assert rep["metrics"]["cpu_speed"]["n_missing"] == 0

    # util bound = 1.5 * 90 = 135 s. With 270 dropped, last sample before the gap
    # is at 180 s; ages exceed 135 s once ref time > 315 s -> t=320,340 missing.
    miss = out.set_index(np.round(secs).astype(int))["cpu_user_missing"]
    assert bool(miss.loc[300]) is False and out.set_index(np.round(secs).astype(int))["cpu_user"].loc[300] == 180.0
    assert bool(miss.loc[320]) is True and bool(miss.loc[340]) is True
    assert np.isnan(out.set_index(np.round(secs).astype(int))["cpu_user"].loc[320])
    assert bool(miss.loc[360]) is False  # fresh sample at 360 s restores presence
    # ages of present values never exceed the bound
    ages = out["cpu_user_age_s"].to_numpy()
    assert np.all(ages[np.isfinite(ages)] <= rep["metrics"]["cpu_user"]["max_staleness_s"] + 1e-9)


def test_explicit_max_staleness_override():
    temp = _frame("temperature", 20, 10)       # 0..180 s
    util = _frame("cpu_user", 90, 3)            # 0,90,180 s
    # tight bound of 30 s: util only valid within 30 s of a sample
    out, rep = AsofAligner().align({"temperature": temp, "cpu_user": util},
                                   max_staleness={"cpu_user": 30.0})
    assert rep["metrics"]["cpu_user"]["max_staleness_s"] == 30.0
    secs = np.round(((out["timestamp"] - T0).dt.total_seconds()).to_numpy()).astype(int)
    m = out.set_index(secs)["cpu_user_missing"]  # reference grid is temp's 20 s instants
    # util samples at 0/90/180 s; bound 30 s. Present where age(ref, last sample) <= 30.
    for present_s in (0, 20, 100, 120, 180):   # ages 0,20,10,30,0
        assert not bool(m.loc[present_s]), present_s
    for missing_s in (40, 60, 80, 140, 160):   # ages 40,60,80,50,70 > 30
        assert bool(m.loc[missing_s]), missing_s


def test_empty_and_bad_input():
    try:
        AsofAligner().align({})
        raise AssertionError("expected AlignmentError on empty input")
    except AlignmentError:
        pass


def main() -> int:
    tests = [test_reference_grid_and_intervals, test_no_fabrication_and_causality,
             test_staleness_bound_and_missingness, test_explicit_max_staleness_override,
             test_empty_and_bad_input]
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
