"""Phase 3B paper-analysis config: source artifact paths + LOCKED expected
values for validation. Read-only w.r.t. all Phase 2 artifacts. No experiments."""
from pathlib import Path

ROOT = Path("v2_research/summit")
SRC = {
    "2A": ROOT / "counterfactual" / "phase2a_results.json",
    "2B": ROOT / "observability_ablation" / "observability_ablation_results.json",
    "2C": ROOT / "phase2c_bootstrap" / "phase2c_bootstrap_results.json",
    "2D": ROOT / "phase2d_fleet" / "phase2d_results.json",
    "2E": ROOT / "phase2e_streaming" / "phase2e_results.json",
}
OUT = Path("v2_research/paper_analysis")
FIG_DIR = OUT / "figures"
TAB_DIR = OUT / "tables"
REP_DIR = OUT / "reports"

RAW_SHA256 = "9898170bed7f41b2205a98e206ca0a12a7d429795fb0b16efb8773f74b00996e"

# condition key map (Phase 2B/2C internal -> paper label)
COND_ORDER = ["F0", "F1", "F2", "F3", "F4"]
COND_KEY = {"F0": "F0_full", "F1": "F1_quantized", "F2": "F2_downsampled",
            "F3": "F3_spatial", "F4": "F4_combined"}
COND_DESC = {
    "F0": dict(temp="socket-mean, float", samp="10 s", spatial="socket-mean", note="full (reference)"),
    "F1": dict(temp="socket-mean, 1 C", samp="10 s", spatial="socket-mean", note="quantization"),
    "F2": dict(temp="socket-mean, float", samp="20 s", spatial="socket-mean", note="downsample (decimate x2)"),
    "F3": dict(temp="Tjmax, float", samp="10 s", spatial="hottest-core proxy",
               note="spatial; NOT a fixed-core stream (no per-core streams in archive)"),
    "F4": dict(temp="Tjmax, 1 C", samp="20 s", spatial="hottest-core proxy", note="combined degradation"),
}

# LOCKED expected values (rounded) for the validator. Loaded (unrounded) values
# must match within tolerances below.
EXPECT = {
    "tau_point": {"F0": 394, "F1": 116, "F2": 910, "F3": 283, "F4": 352},      # 2B
    "tau_boot":  {"F0": 394, "F1": 116, "F2": 909, "F3": 283, "F4": 352},      # 2C
    "tau_ratio": {"F0": 1.00, "F1": 0.29, "F2": 2.31, "F3": 0.72, "F4": 0.89},  # 2C
    "fleet": dict(n_valid=116, median=439, mean=552, std=365, iqr=[376, 588],
                  p05=275, p95=1200, min=205, max=2596, socket_corr=0.789,
                  socket_rel_diff=0.242),
    "residual_hgb_max": 0.066,     # 2B (F4)
    "streaming": dict(rel_spread=0.62, power_confound=0.0, runtime_ms=0.041),
}
TOL = {"tau_s": 2.0, "tau_pct": 0.01, "ratio": 0.02, "fleet_pct": 0.02,
       "small": 0.01, "runtime_ms": 0.03}

TERMS = {  # mentor-facing terminology (narrative)
    "telemetry": "temperature and power measurements",
    "fidelity": "measurement quality",
    "tau": "how quickly temperature responds to changes in power (effective time constant)",
}
