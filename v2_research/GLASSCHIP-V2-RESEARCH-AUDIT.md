# GLASSCHIP-V2 — Research Audit

**Status: investigation only. No V2 model built. GLASSCHIP-V1 untouched.**

Order enforced throughout: **observations → observability → physics → model
→ validation.** No architecture was chosen before the evidence.

All V2 work lives under `v2_research/` and reads V1 read-only. The frozen V1
repository, its inputs, joins, gates, baseline, PINN, thresholds, conclusions,
and the `8473342129fb19f0` anchor are unchanged.

---

## 1. Executive Summary

V1 concluded that its residual was **unlearnable from its three inputs** — an
observability limit, not a model limit. V2's first job was to test whether the
M100 telemetry V1 *excluded* removes that limit. It was tested empirically, not
assumed.

**Central result (Phase 2, decisive):** adding **every available node-level
M100 observable** — the 23 other per-core temperatures, ambient, VDD
temperature, total/second-socket power (all on V1's exact 20 s grid), plus
utilisation, frequency, and load — provides **no out-of-sample information**
about the V1 residual. Under proper time-series cross-validation the residual's
test R² is **negative** for every predictor set (control −0.43, +same-grid
temps −0.49, +workload −0.29, combined −0.50), while in-sample fit is high
(train R² ≈ 0.4). The high mutual information (0.6–0.96) is an in-sample
non-stationarity artefact with zero predictive value.

**Interpretation:** the V1 20 s temperature increment is dominated by
irreducible fast noise (quantization plus sub-20 s workload transients that a
20 s grid cannot resolve). **More node-level observability does not help;
therefore a richer, recurrent, or multi-node model of the same target cannot
help either.** V2 must change *what is observed* or *what is predicted* — not
the model.

**Recommendation:** do **not** build a more complex model of the V1 residual.
Pursue one of two evidence-supported directions: **(A)** a new dataset with
genuinely richer observability — measured coolant boundary temperature and/or
higher temporal resolution (the **Frontier** energy dataset is the prime
candidate); or **(B)** a different, learnable *target* on M100 — longitudinal
`τ`-drift across records. Multi-node and recurrent PINNs are **not** justified
by the evidence for the 20 s-increment target.

---

## 2. V1 Constraints That Must Remain Frozen

Locked inputs (temperature/power/fan); exact-timestamp join; screening gates
(372/22); the discrete first-order baseline; the scientific conclusions; the
`8473342129fb19f0` anchor. V2 is a separate project label. None of the above
may be modified, and this audit modifies none of them.

---

## 3. Excluded M100 Metrics Audit

Two classes, established empirically (Phase 1):

| Class | Metrics | Plugin | Grid | Nodes | Alignment |
|---|---|---|---|---|---|
| **Same-grid IPMI** | `p0_core1..23_temp`, `p1_core*`, `ambient`, `p0_vdd_temp`, `total_power`, `p1_power` | `ipmi_pub` | **20 s (exact)** | 394 (per-core) / 979–980 (rest) | **Exact join, same node namespace — clean** |
| **Ganglia workload** | `cpu_user/system/idle/steal/wio`, `cpu_speed` (freq), `load_one/five/fifteen`, `proc_run`, mem/net | `ganglia_pub` | **60–90 s, jittered** | 982 | Causal ASOF fill; **cross-plugin node identity UNVERIFIED** |
| Facility cooling | coolant, CRAC (`logics_pub`, `schneider_pub`) | facility | varies | **no node column** | cannot be node-attributed |

The same-grid IPMI temperatures are the scientifically cleanest addition: same
sensor family, same 20 s instants, same node identity — no resampling, no
leakage. This made them the strongest test of the observability hypothesis.

---

## 4. Sampling-Rate / Alignment Analysis

- **Same-grid IPMI (20 s):** no alignment needed — exact inner join, identical
  to V1's policy. Zero information lost.
- **Ganglia (60–90 s):** aligned by **causal ASOF join** (last value at or
  before each 20 s instant) — leakage-free, but each value is held constant
  across ~3–5 residual samples, so it can only carry ~90 s-scale information
  and **cannot resolve the 20 s residual structure by construction.**
- **Two independent penalties on ganglia:** (i) the 60–90 s grid cannot see
  sub-90 s dynamics; (ii) V1 proved cross-plugin node IDs are not the same
  physical machine (392/394 ID overlap ≠ identity). Any ganglia result is
  therefore *conditional on an unverified identity assumption* — and, as it
  turned out, negative even under that generous assumption.

Interpolation/tolerance joins were deliberately avoided (they fabricate the
very sub-grid structure being tested for).

---

## 5. V1 Residual Observability Analysis (the decisive experiment)

Target: V1's **frozen** residual `r[n] = T0[n+1] − (α·T0[n] + β·P[n] + γ)`,
recovered per PASS node with V1's own locked `ClassicalBaselineModel`.
Predictors taken at time `n` (causal). Evaluation: `TimeSeriesSplit` 5-fold,
mean **test** R² (linear + random forest), with train R² reported to diagnose
overfitting. 10 representative PASS nodes.

| Predictor set | linear test R² | RF test R² | RF train R² | Verdict |
|---|---:|---:|---:|---|
| **control** (P, ΔP, fan, T0) | −0.24 | −0.43 | 0.39 | reproduces V1's null ✓ |
| **+ same-grid temps** | −0.75 | −0.49 | 0.46 | no gain (worse) |
| **+ workload** (util/freq/load) | −0.67 | −0.29 | 0.42 | no gain |
| **combined** | −1.00 | −0.50 | 0.46 | **worst** (over-fitting) |

Mutual information was high (`p0_core1_temp` 0.96, `cpu_user` 0.87, …) **but is
spurious** — it reflects in-sample correlation on non-stationary series; the
matching train-R²≈0.4 / negative-test-R² gap proves there is **no
generalizable predictive signal.**

**Ranked observability table:**

| Variable | Alignment | Coverage | Lag info | Residual relationship | Predictive value | Recommendation |
|---|---|---|---|---|---|---|
| per-core temps (`p0_coreN`) | exact 20 s | 394 nodes | none robust | high MI, **negative test R²** | **none** | do not use for this target |
| `ambient` | exact 20 s | 979 | none | low MI, no test gain | none | (boundary interest only) |
| `p0_vdd_temp`, `total_power` | exact 20 s | 980 | none | high MI, no test gain | none | do not use |
| `cpu_user`/`system`/`idle` | ASOF 90 s | 982* | none | high MI, negative test R² | none | do not use (also ID-unverified) |
| `cpu_speed` (freq) | ASOF 60 s | 982* | none | no test gain | none | do not use |
| `load_one`, `proc_run` | ASOF 80–90 s | 982* | none | no test gain | none | do not use |

\*conditional on unverified cross-plugin node identity.

**Answer to the central question: NO.** The excluded M100 observations do not
contain out-of-sample information about the V1 residual. The observability
limit is not in *which* node-level metrics V1 chose — it is in the **20 s / 1 °C
resolution** of the M100 IPMI telemetry itself.

---

## 6. External Dataset Survey

| Dataset | Source | Hardware | Coolant / boundary | Per-core T | Util/Freq | Sampling | Nodes | License | V2 relevance |
|---|---|---|---|---|---|---|---|---|---|
| **Frontier Energy** (2024) | Nature Sci Data `s41597-024-03913-w` | AMD CPU+4 GPU blades, direct liquid | **coolant inlet & outlet per blade** | blade-level | partial | **[VERIFY]** | 74 cabinets × 64 blades | open | ★ **measured coolant boundary — fixes V1's biggest gap** |
| SMC Data Challenge — HPC Power/Thermal | ORNL (Summit) | POWER9+V100 | facility | node | yes | coarse | Summit-scale | open | comparable to M100; boundary at facility level |
| Consumer CPU stress dataset (2025) | IEEE DataPort `10.21227/95m0-wj49` | mobile i7 | thermocouples + IR | die-region (IR) | yes | **25 Hz** | 1 | subscription | ★ **sub-second resolution** — resolves fast dynamics M100 cannot |
| M100 ExaData (V1) | Zenodo | POWER9+V100 | facility only | 20 s | 60–90 s | 20 s | 980 | CC-BY-4.0 | control / longitudinal target |

Two external candidates address the **two** root causes identified in Phase 5:
Frontier supplies **measured node-level coolant boundary** (turning `T_ref`
from a fitted extrapolation into an observation); the consumer/IR dataset
supplies **25 Hz resolution** (resolving the sub-20 s transients M100 aliases
into noise). Both are single-issue fixes; neither is M100.

---

## 7. Recent Literature Audit (2024–2026)

| Work | Idea | What V1 lacked | Transferable to V2 |
|---|---|---|---|
| **PG-RSSNN** — Physics-Guided Recurrent State-Space NN (arXiv 2606.02278) | recurrent latent thermal state, multi-step rollout, no divergence | V1 was single-step, stateless | recurrence *if* a multi-step signal exists (Phase 2 says not at 20 s) |
| **GNN-ODE digital twins** (arXiv 2604.07292) | message-passing GNN + Neural ODE under **partial observability** | V1 single-node, no spatial graph | multi-node graph *if* spatial coupling is observable |
| **Physics-constrained graph thermal networks** (arXiv 2605.28452) | interpretable graph Neural ODE, physical nodes | V1 one lumped node | node = core/socket/spreader/coolant, physically justified |
| **Frontier waste-heat dataset** (Nature 2024) | coolant loop instrumentation | V1 had no coolant boundary | direct: measured `T_ref` |
| DeepOHeat / DeepOHeat-v1 (DAC'23 / 2504.03955) | operator learning, spatial thermal | V1 no spatial field | needs a power map V1/M100 lack |
| BPINN-EM (ICCAD'24) | Bayesian PINN, uncertainty | V1 point estimates | UQ, not the bottleneck here |
| DC cooling failure-prediction review 2018–2026 (EPJ ST) | field survey | — | context |

**Consistent themes in recent HPC thermal ML:** measured **coolant/boundary**
temperature, **recurrent/state-space** temporal models, and **graph/multi-node**
spatial structure. V1 had none of the three — but Phase 2 shows the last two
only help if the *observations* support them, which at 20 s they do not.

---

## 8. Missing Variables Identified

Ranked by how directly they attack the V1 limit:

1. **Measured coolant/boundary temperature** — V1's `T_ref` is a fitted
   extrapolation to an unobserved `P≈0`; a measured boundary would make the
   steady-state physics identifiable and is the single most-cited missing
   variable in the literature. *M100 has it only at facility scope; Frontier
   has it per blade.*
2. **Higher temporal resolution (sub-20 s)** — the residual is sub-grid noise;
   only finer sampling can resolve it. *Not obtainable from M100.*
3. **Spatial power map / per-core power** — V1 has socket power vs single-core
   temperature. *Not in M100.*
4. Per-core temperatures, utilisation, frequency — **present in M100 but
   empirically unhelpful for the 20 s residual (Phase 2).**

---

## 9. Candidate V2 Research Directions

| # | Direction | Attacks | Evidence support |
|---|---|---|---|
| D1 | **New dataset with coolant boundary + finer sampling** (Frontier / IR) | root cause (boundary + resolution) | **Strong** — directly supplies the two missing variables |
| D2 | **Longitudinal target on M100** (`τ`-drift across records) | different, slow, learnable signal | **Moderate** — untested but plausibly learnable; needs cross-record identity (GATE B) |
| D3 | Multi-node thermal graph on M100 | spatial coupling | **Weak** — Phase 2: per-core temps give no out-of-sample residual gain |
| D4 | Recurrent/stateful PINN on M100 | temporal memory | **Weak** — Phase 2: no out-of-sample structure at 20 s to remember |
| D5 | More complex single-node PINN on V1 target | model capacity | **Refuted** — V1 + Phase 2 both null |

---

## 10. Recursive PINN Assessment

A recurrent/state-space PINN (à la PG-RSSNN) is attractive *in general* but is
**not supported for the M100 20 s-increment target**: Phase 2 shows the residual
has no out-of-sample predictive structure from any features, lagged or
contemporaneous — there is no temporal memory to exploit. Recurrence would fit
in-sample (as the RF did, train R²≈0.4) and fail out-of-sample. **Recommended
only if V2 first moves to a dataset/target where a multi-step signal is shown
to exist** (mandatory pre-test: does lagged history predict the target
out-of-sample before adding recurrence). Avoid teacher-forcing leakage; compare
one-step vs multi-step rollout.

---

## 11. Multi-Record / Longitudinal Assessment

V1 used one 62 h window. M100 ships 12–13 records over 934 days. A longitudinal
target — does `τ_eff` drift with workload/time; is there slow thermal
degradation — is a **different, slower, plausibly learnable signal** than the
20 s increment, and is the cheapest genuinely new direction (stays in M100,
CC-BY-4.0). **Prerequisite (V1 GATE B, still open):** establish cross-record
node identity before mixing records; do not pool blindly. This is D2.

---

## 12. Multi-Node Physics Assessment

Replacing the single lumped node with a physical multi-node network
(core → package → spreader → heatsink → coolant) is well-motivated by the
graph-thermal literature, **but only introduces states that observations can
constrain.** Phase 2 tested the observable proxy for inter-core coupling
(neighbouring per-core temperatures) and found **no out-of-sample residual
gain.** Adding unobserved hidden nodes to fit the 20 s residual would be
complexity without observability — precisely V1's warned failure mode. Multi-
node is justified **only** on a dataset with a measured boundary (coolant) and,
ideally, per-core power — i.e. it rides on D1, not on M100 alone.

---

## 13. Decision Matrix

| Question | Answer | Evidence |
|---|---|---|
| A. Can excluded M100 metrics inform the residual? | **No** | Phase 2: test R² ≤ 0 for all sets |
| B. Defensible alignment for their grids? | Yes (causal ASOF) — but it doesn't help | Phase 4/5 |
| C. Does an external dataset give better observability? | **Yes** | Frontier (coolant), IR (25 Hz) |
| D. Key missing M100 variables? | coolant boundary; sub-20 s resolution; per-core power | Phase 8 |
| E. Variables used in recent research? | coolant/boundary, recurrent state, graph structure | Phase 7 |
| F. Approaches V1 didn't try? | recurrent state-space, graph Neural ODE, measured boundary | Phase 7 |
| G. Is the problem…? | **insufficient observations (resolution + boundary)** — not model complexity, not spatial-model absence | Phases 2, 5 |

---

## 14. Recommended V2 Direction

> **Primary (D1): change the observation.** Move to a dataset that supplies the
> two variables Phase 2 identified as the actual bottleneck — a **measured
> coolant/boundary temperature** and **higher temporal resolution**. The
> **Frontier Energy dataset** (per-blade coolant inlet/outlet, open, 2024) is
> the strongest single candidate; the 25 Hz consumer/IR dataset is a
> complementary fast-dynamics probe. Only *after* an observability test on the
> new data (does the boundary/finer sampling actually reduce the residual
> out-of-sample?) should any model — and only then possibly a multi-node or
> recurrent one — be considered.
>
> **Secondary (D2): change the target.** If staying in M100, pursue
> **longitudinal `τ`-drift** across records (a slow, learnable signal), after
> resolving cross-record node identity (GATE B).

**Do not** build a richer single-node/recurrent/multi-node PINN of the V1 20 s
residual on M100. Phase 2 shows there is nothing there to learn.

---

## 15. Why This Direction Is Scientifically Justified

The order was respected. **Observability was tested before any model.** The
result is unambiguous and reproduces V1 on the control: the M100 20 s residual
carries no out-of-sample information recoverable from any available node-level
observation. That is a property of the *observations* (resolution + missing
boundary), so the scientifically valid response is to improve the observations
(D1) or change the target to one the observations can support (D2) — not to add
model capacity, which Phase 2 shows overfits and fails out-of-sample.

---

## 16. What Should NOT Be Done

- Do not build a bigger/recurrent/multi-node PINN of the V1 residual on M100.
- Do not trust mutual information or in-sample fit — Phase 2 shows both are high
  while out-of-sample value is zero. Every V2 claim must pass time-series CV.
- Do not join ganglia to IPMI by node ID without first proving cross-plugin
  identity.
- Do not pool M100 records without proving cross-record node identity (GATE B).
- Do not interpolate/tolerance-join to manufacture sub-grid structure.
- Do not modify, fork, or "improve" GLASSCHIP-V1.

---

## 17. Exact Next Experimental Gate

**GATE V2-α (observability on new data), before any model:**

1. Acquire the Frontier Energy dataset (and/or the 25 Hz IR dataset).
2. Reproduce the Phase 2 protocol on it: fit the frozen first-order baseline,
   form the residual, and test — **with time-series CV, out-of-sample** —
   whether the **measured coolant boundary** and/or **finer sampling** reduce
   the residual.
3. **Pass condition:** out-of-sample test R² of the residual rises materially
   above zero (say > 0.2) when the new observations are added.
4. Only if V2-α passes: proceed to physics (multi-node with a measured
   boundary) → model → validation. If it fails, the thermal residual is
   irreducible at achievable resolution and V2 should pivot to the longitudinal
   target (D2) or stop.

**No V2 architecture is committed until GATE V2-α passes.**

---

*Artifacts: `v2_research/phase2_residual_observability.py`,
`v2_research/phase2_results.json`. V1 repository unmodified.*
