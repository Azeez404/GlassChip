"""Minimal usage examples for :mod:`validator`.

Run from the project root::

    python examples/validator_example_usage.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from validator import GLASSCHIP_MANDATORY_INPUTS, DatasetValidator

DATASET_PATH = "data/raw/21-03"


def main() -> None:
    validator = DatasetValidator(DATASET_PATH)

    # --- 1. metric validation -----------------------------------------
    report = validator.validate_metric("p0_power")
    timing = report["timing"]
    print(f"p0_power: {report['n_rows']:,} rows, {report['n_nodes']} nodes, "
          f"dtype={report['value_dtype']}")
    print(f"  interval={timing['median_interval_s']}s "
          f"regular={timing['is_regular_grid']} "
          f"coverage={timing['coverage_ratio']:.1%}")
    print(f"  longest contiguous run={timing['longest_segment_h']:.2f} h "
          f"(largest gap {timing['largest_gap_h']:.1f} h)")

    # --- 2. node validation -------------------------------------------
    metrics = list(GLASSCHIP_MANDATORY_INPUTS.values())
    node = validator.validate_node("15", metrics=metrics)
    print(f"\nnode 15: {node['n_available']}/{node['n_metrics_checked']} "
          f"metrics, plugins={node['present_in_plugins']}")

    # --- 3. common nodes ----------------------------------------------
    common = validator.find_common_nodes(metrics)
    print(f"\ncommon nodes across mandatory inputs: {common['n_common']} "
          f"(overlap {common['overlap_ratio']:.1%})")
    for metric, info in common["per_metric"].items():
        print(f"  {metric:16s} {info['plugin']:12s} {info['n_nodes']:4d} nodes")

    # --- 4. timestamp alignment ---------------------------------------
    align = validator.validate_timestamp_alignment(metrics)
    print(f"\nalignment on node {align['node']}: "
          f"same_interval={align['all_same_interval']} "
          f"compatible={align['compatible']}")
    for pair in align["pairs"]:
        flag = "OK " if pair["exact_join_viable"] else "NO "
        print(f"  {flag}{pair['metric_a']:15s}+{pair['metric_b']:15s}"
              f"{pair['exact_match_ratio']:8.2%}")

    # --- 5. pairwise compatibility ------------------------------------
    for pair in (("p0_core0_temp", "p0_power"), ("p0_core0_temp", "cpu_user")):
        result = validator.validate_metric_compatibility(list(pair))
        print(f"\n{pair[0]} + {pair[1]} -> {result['verdict']}")
        for issue in result["blocking"]:
            print(f"  BLOCKING: {issue}")

    # --- 6. GLASSCHIP mandatory inputs --------------------------------
    verdict = validator.validate_glasschip_inputs()
    print(f"\nGLASSCHIP mandatory inputs: {verdict['verdict']}")
    print(f"  {verdict['justification']}")
    for issue in verdict["blocking_issues"]:
        print(f"  BLOCKING: {issue}")

    # IPMI-only subset, for contrast
    subset = validator.validate_glasschip_inputs(inputs={
        "temperature": "p0_core0_temp",
        "power": "p0_power",
        "fan_speed": "fan0_0",
    })
    print(f"\nIPMI-only subset: {subset['verdict']}: {subset['justification']}")

    # --- 7. full report -----------------------------------------------
    full = validator.generate_validation_report()
    print(f"\nfull report verdict={full['verdict']}, "
          f"{len(full['observations'])} observations, "
          f"{len(full['joinability'])} metric pairs assessed")


if __name__ == "__main__":
    main()
