"""Tests for src/alignment/fleet_driver.py.

Self-contained (assertions, no pytest, no external dataset). Uses injected
in-memory frames and temp output dirs. Run:

    python tests/test_fleet_driver.py
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from alignment.fleet_driver import (  # noqa: E402
    FleetConfig, FleetDriver, FleetError, build_arg_parser, _parse_staleness, main,
)
from alignment.heterogeneous_builder import DEFAULT_STALENESS_S  # noqa: E402

T0 = pd.Timestamp("2021-03-01 00:00:00", tz="UTC")


def _raw(step_s: int, n: int, node, drop_secs=None):
    drop = drop_secs or set()
    secs = [i * step_s for i in range(n) if i * step_s not in drop]
    return pd.DataFrame({"timestamp": [T0 + pd.Timedelta(seconds=s) for s in secs],
                         "value": [float(s) for s in secs], "node": node})


def _good_frames(node):
    return {"temperature": _raw(20, 31, node), "power": _raw(20, 31, node),
            "fan": _raw(20, 31, node), "frequency": _raw(60, 11, node),
            "utilization": _raw(90, 7, node, drop_secs={270})}


def _provider(node):
    if str(node) == "bad":                       # no temperature -> build fails
        return {"power": _raw(20, 31, node)}
    return _good_frames(node)


def _driver(outdir, loader=None, staleness=None):
    cfg = FleetConfig(dataset_root=None, output_dir=str(outdir),
                      staleness_s=dict(staleness or DEFAULT_STALENESS_S))
    return FleetDriver(cfg, loader=loader, raw_frames_provider=_provider)


def _tmp():
    return Path(tempfile.mkdtemp(prefix="fleet_test_"))


def test_single_node_success():
    out = _tmp(); s = _driver(out).run(["15"])
    assert s["n_requested"] == 1 and s["n_succeeded"] == 1 and s["n_failed"] == 0
    assert (out / "node=15" / "aligned.parquet").is_file()
    assert (out / "node=15" / "report.json").is_file()
    assert (out / "fleet_summary.json").is_file()


def test_multiple_node_success():
    out = _tmp(); s = _driver(out).run(["15", "16"])
    assert s["n_succeeded"] == 2
    for n in ("15", "16"):
        assert (out / f"node={n}" / "aligned.parquet").is_file()


def test_explicit_selection_and_determinism():
    o1, o2 = _tmp(), _tmp()
    s1 = _driver(o1).run(["16", "15", "15"])   # unsorted + duplicate
    s2 = _driver(o2).run(["15", "16"])
    assert s1["requested_nodes"] == ["15", "16"] == s2["requested_nodes"]  # sorted, deduped
    f1 = pd.read_parquet(o1 / "node=15" / "aligned.parquet")
    f2 = pd.read_parquet(o2 / "node=15" / "aligned.parquet")
    assert f1.equals(f2)


def test_missing_invalid_node_handling():
    out = _tmp(); s = _driver(out).run(["bad"])
    assert s["n_succeeded"] == 0 and s["n_failed"] == 1
    assert s["failed"][0]["node"] == "bad" and "Error" in s["failed"][0]["error"]
    assert not (out / "node=bad" / "aligned.parquet").exists()  # no misleading artifact


def test_partial_fleet_failure_reported():
    out = _tmp(); s = _driver(out).run(["15", "bad", "16"])
    assert s["n_requested"] == 3 and s["n_succeeded"] == 2 and s["n_failed"] == 1
    failed_nodes = [f["node"] for f in s["failed"]]
    assert failed_nodes == ["bad"]                # recorded, not silently skipped
    assert {c["node"] for c in s["succeeded"]} == {"15", "16"}


def test_output_parquet_and_report_content():
    out = _tmp(); _driver(out).run(["15"])
    df = pd.read_parquet(out / "node=15" / "aligned.parquet")
    assert "node" in df.columns and (df["node"] == "15").all()
    assert {"temperature", "utilization", "utilization_age_s", "utilization_missing"} <= set(df.columns)
    rep = json.loads((out / "node=15" / "report.json").read_text())
    assert rep["reference"]["role"] == "temperature"
    assert rep["alignment_direction"] == "backward (causal)"


class _StubLoader:
    def __init__(self, nodes): self._nodes = nodes
    def nodes_for_metric(self, metric): return list(self._nodes)


def test_all_mode_enumeration():
    out = _tmp()
    d = _driver(out, loader=_StubLoader(["15", "16", "17"]))
    nodes = d.enumerate_all_nodes()
    assert nodes == ["15", "16", "17"]
    s = d.run(nodes)
    assert s["n_succeeded"] == 3
    # enumeration without a loader is an explicit, actionable error
    try:
        FleetDriver(FleetConfig(output_dir=str(out)), raw_frames_provider=_provider).enumerate_all_nodes()
        raise AssertionError("expected FleetError without a loader")
    except FleetError as e:
        assert "enumerate" in str(e)


def test_config_propagation():
    out = _tmp()
    d = _driver(out, staleness={**DEFAULT_STALENESS_S, "utilization": 200.0})
    s = d.run(["15"])
    assert s["effective_staleness_s"]["utilization"] == 200.0
    rep = json.loads((out / "node=15" / "report.json").read_text())
    assert rep["effective_staleness_s"]["utilization"] == 200.0   # reached the builder


def test_empty_fleet():
    out = _tmp(); s = _driver(out).run([])
    assert s["n_requested"] == 0 and s["n_succeeded"] == 0 and s["n_failed"] == 0
    assert (out / "fleet_summary.json").is_file()


def test_cli_parse_and_validation():
    p = build_arg_parser()
    ns = p.parse_args(["--dataset-root", "x", "--output-dir", "o", "--nodes", "1", "2",
                       "--staleness", "frequency=120", "utilization=200"])
    assert ns.nodes == ["1", "2"] and ns.staleness == ["frequency=120", "utilization=200"]
    assert _parse_staleness(ns.staleness) == {"frequency": 120.0, "utilization": 200.0}
    # --nodes and --all are mutually exclusive and one is required
    for bad in ([], ["--nodes", "1", "--all"]):
        try:
            p.parse_args(bad); raise AssertionError("expected SystemExit")
        except SystemExit:
            pass
    # bad staleness spec
    try:
        _parse_staleness(["frequency"]); raise AssertionError("expected error")
    except argparse.ArgumentTypeError:
        pass
    # --all without --dataset-root exits 2 (via main)
    assert main(["--output-dir", "o", "--all"]) == 2


def main_run() -> int:
    tests = [test_single_node_success, test_multiple_node_success,
             test_explicit_selection_and_determinism, test_missing_invalid_node_handling,
             test_partial_fleet_failure_reported, test_output_parquet_and_report_content,
             test_all_mode_enumeration, test_config_propagation, test_empty_fleet,
             test_cli_parse_and_validation]
    failed = 0
    for t in tests:
        try:
            t(); print(f"PASS {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1; print(f"FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main_run())
