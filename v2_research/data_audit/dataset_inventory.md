# GLASSCHIP-V2 — Phase V2-1: Dataset Acquisition & Verification Record

**Task:** independently verify the primary V2 candidate (Frontier Energy
dataset) and any alternatives, against the V2 requirement.

**V2 requirement (from the audit):** to make the V1 20 s residual learnable,
a dataset must supply, *at the node/processor level*, at least one of:
1. a **measured coolant/thermal boundary temperature** co-located with the
   processor it cools, and/or
2. **temporal resolution finer than 20 s** with 1 °C-or-better temperature,
co-located with per-processor **temperature and power**.

**Method:** primary sources only (Nature, PubMed, OSTI, figshare). Full text
was paywalled/JS-gated; findings rest on three independent abstract sources
that agree. Nothing below is inferred from column names or the prior audit's
metadata (which was explicitly not trusted).

---

## Candidate 1 — Frontier Energy Dataset (the audit's PRIMARY candidate)

| Field | Value |
|---|---|
| Paper | Sun, J., Gao, Z., Grant, D. *et al.* "Energy dataset of Frontier supercomputer for waste heat recovery" |
| Venue | *Scientific Data* 11, 1077 (2024) |
| Paper DOI | `10.1038/s41597-024-03913-w` |
| Dataset | "Frontier HPC & Facility Data", figshare `10.6084/m9.figshare.24391240.v4` |
| Mirrors | OSTI `2483448`; PubMed `39362911` |
| Access | **Open** (figshare) — *accessible* |
| Hardware | Frontier (ORNL), AMD EPYC + 4× MI250X per node, 100 % direct liquid cooling, 3 cascaded fluid loops |

### What the dataset actually contains (verified from 3 abstracts)

- Supercomputer **total power** demand
- Accessory **cooling-system power** demand
- **PUE** (power usage effectiveness)
- **Waste heat** — overall and from the **three cooling subloops**
- **Coolant flow and temperature profiles** at **cooling-loop (facility) level**

### What it does NOT contain

- ❌ per-node / per-blade CPU or GPU temperature
- ❌ per-node power
- ❌ per-node utilisation or frequency
- ❌ a coolant temperature co-located with an individual processor

### Verdict: ✗ UNSUITABLE

**The dataset is facility/cooling-loop level, not per-node processor
telemetry.** Its purpose is waste-heat recovery — inherently a facility
concern. This is the **same granularity of coolant boundary that M100 already
had** (M100's `schneider_pub`/`logics_pub` facility loops), which V1 could not
attribute to nodes. It therefore does **not** fix either V2 root cause at the
node level.

**Note on the prior audit's error:** the V2 audit described Frontier as having
"per-blade coolant inlet/outlet measurements in each blade." That describes
Frontier's **physical architecture** (what the machine has), taken from a
generic search snippet — **not the contents of this dataset**. The instruction
to independently verify caught this. Corrected here.

---

## Candidate 2 — NLR HPC Eagle GPU Node Metrics

| Field | Value |
|---|---|
| Source | OSTI `3015213` |
| Contents | Ganglia node metrics + iLO power, **6** Eagle GPU nodes (2 CPU + 2 GPU each), 2019–2024, compressed CSV |
| Coolant boundary | ❌ not confirmed |
| Fine-res per-core temperature | ❌ Ganglia-level (coarse), like M100's ganglia plugin |
| Fleet size | 6 nodes |

**Verdict: ✗ UNSUITABLE.** Ganglia + iLO is the *same class* of coarse
utilisation/power telemetry M100 already provides (and which V1 excluded /
V2-audit tested as unhelpful). No node-level coolant boundary; no evidence of
sub-20 s per-core temperature. Six nodes is not a fleet.

---

## Candidate 3 — UCR Commercial Thermal-Map Dataset

| Field | Value |
|---|---|
| Source | github.com/sheldonucr/commercial_thermal_map_dataset; MLCAD 2024 |
| Contents | IR **thermal maps** of commercial CPUs/GPUs/TPU |
| Access | samples on GitHub; full data **"upon request"**; pickle format; no license |

**Verdict: ✗ UNSUITABLE.** Provides spatial temperature but **no measured
coolant boundary** and no co-located node power at HPC scale; access is gated
and the format is a security/reproducibility liability. Addresses a different
gap (spatial field) than the V2 root causes.

---

## Candidate 4 — Consumer CPU Stress Dataset (25 Hz)

| Field | Value |
|---|---|
| Source | IEEE DataPort `10.21227/95m0-wj49` (2025) |
| Contents | 1 mobile i7, thermocouples + 25 Hz IR + DTS |
| Access | **IEEE DataPort subscription** (paywalled) |

**Verdict: ✗ UNSUITABLE for V2's HPC question.** It *does* fix temporal
resolution (25 Hz) and gives a measured surface boundary — but it is **one
consumer device**, **paywalled**, no fleet, no HPC liquid-cooling boundary. It
could serve a *different* micro-study, not the fleet-scale V2 question.

---

## Phase V2-1 Conclusion

**No accessible public dataset provides node-level, co-located per-processor
temperature + power + a measured coolant boundary at finer-than-20 s
resolution.** The audit's primary candidate (Frontier) is verified accessible
but **facility-level**, and does not address either root cause at the node
level. All alternatives fail on granularity, access, or fleet scale.

**Structural audit (schema/sampling/quality) was intentionally NOT performed**:
acquisition already determined the primary candidate cannot answer the V2
question, so auditing its internal structure would not change the verdict.
This is a legitimate early stop (master prompt §20), not an omission.

**Consequence:** GATE V2-α (the observability experiment on richer data)
**cannot be executed** — there is no suitable richer dataset to run it on. See
`reports/PHASE_V2_ALPHA_REPORT.md` and `reports/V2_DECISION.md`.
