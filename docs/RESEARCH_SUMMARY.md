# GLASSCHIP-V1 — Complete Scientific Summary

*Self-contained. Understandable without reading the code.*

Physics-constrained thermal modelling of fleet-scale processor telemetry, and
an honest test of whether a physics-informed neural network (PINN) can improve
on classical thermal physics for this problem.

---

## Research Problem

Modern processors convert electrical power almost entirely into heat. Their
temperature is governed, to first order, by the lumped thermal relation

```
C dT/dt = P - (T - T_ref)/R
```

(an RC circuit: power in, heat out, temperature as the state). The question
GLASSCHIP-V1 sets out to answer:

> Using only real HPC processor telemetry, can a physics-informed neural
> network learn thermal behaviour that classical first-order physics cannot
> already explain, while respecting the same observable physics?

## Objectives

1. Learn effective processor thermal behaviour from real HPC telemetry.
2. Build one scientifically defensible PINN — not the fanciest, the smallest.
3. Preserve scientific correctness over favourable metrics.
4. Establish a classical baseline and test the PINN honestly against it.

## Dataset

**M100 ExaData** (CINECA Marconi100 supercomputer), record `21-03`, CC-BY-4.0,
Borghesi et al., *Nature Scientific Data* (2023). Public, permanently
archived on Zenodo, never redistributed through this repository.

Three input signals per node, on a rigid 20 s IPMI grid:

| Role | Metric | Unit |
|---|---|---|
| Temperature | `p0_core0_temp` | °C, **1 °C quantized** |
| Power | `p0_power` | W (per socket) |
| Fan speed | `fan0_0` | RPM |

**Key data facts (measured, not assumed):**
- The record contains **one contiguous 61.978 h window** (11,157 samples) plus
  a 9-sample fragment, separated by a **648.9 h gap** — not a month.
- **394 nodes** carry all three metrics (temperature limits this; power/fan
  have 980).
- Node ID namespaces are **plugin-specific and do not match** across plugins.
- The data is **observational and closed-loop** (power is DVFS-governed), so
  no causal claim is supported.

## Physics

Only the lumped first-order ODE above is used — no spatial operators, no PDEs,
no Fourier heat conduction (the data has no spatial coordinates). Recovered
quantities are **effective**, not physical:

- `τ_eff = RC` — the trustworthy quantity; independent of the unobservable
  fraction of socket power reaching the core sensor.
- `R_eff`, `C_eff` — effective, contaminated by that unknown fraction; never
  reported as physical SI values without caveat.
- `T_ref` — effective reference temperature.

## Pipeline (7 layers, each gates the next)

```
loader        raw Parquet -> dataframes
validator     what can safely coexist?  PASS / FAIL   (single source of truth)
preprocessing gate -> clean -> exact-timestamp join -> export
visualization what does the data look like?           (describe, never explain)
screening     which nodes deserve to teach a model?   PASS / FAIL
baseline      how much does simple first-order physics explain?
pinn          can a PINN explain what the baseline cannot?
```

`preprocessing` refuses to run whenever `validator` returns `FAIL`; there is
no override. This is why the locked prototype uses only the IPMI triple
(temperature, power, fan) — they share a 100 % exact timestamp match, whereas
CPU utilisation / frequency (from a different plugin, 90 s / 60 s jittered)
match at 5.7 % and would require value fabrication to join.

## Experiments

**Node screening (Phase 8).** Four physics-motivated gates: temperature
excitation above the 1 °C quantization floor; genuine power variation;
coherent power↔temperature coupling (the guard against nodes where power
varies but temperature does not); a usable contiguous segment.

- Result: **372 PASS / 22 FAIL** of 394 nodes. FAIL reasons: power varies with
  no thermal response (12), quantization-dominated temperature (6),
  insufficient excitation (4), segment too short (4), weak coupling (3).

**Classical baseline (Phase 9).** The exact discrete-time solution of the
first-order ODE — `T[n+1] = α·T[n] + β·P[n] + γ` — fit by ordinary least
squares on the values directly. It never finite-differences (the 1 °C / 20 s
derivative is quantization noise). Fit on all 372 PASS nodes.

**PINN (Phase 10).** One small MLP mapping continuous time to temperature,
`dT̂/dt` obtained by automatic differentiation (the entire motivation — a
continuous representation bypasses the quantization that destroys the discrete
derivative). Learnable first-order physics parameters, stability and
positivity enforced by construction, quantization-aware data loss, physics
loss from the same ODE. Fit per node; compared to the baseline on 12
representative PASS nodes via a fair one-step metric.

**Adversarial audit (Phase 11).** An attempt to falsify the Phase 10
conclusion, including testing whether the baseline residual is quantization
and whether it is learnable from the inputs.

## Results

**Classical baseline (372 nodes):**

| Quantity | Median | Note |
|---|---|---|
| `τ_eff` | 230 s | physically sensible for a liquid-cooled CPU |
| `R_eff` | 0.14 °C/W | effective |
| `T_ref` | 37.5 °C | effective; implausible vs coolant → extrapolation artifact |
| one-step RMSE | 1.42 °C | |
| one-step R² | 0.96 | **persistence-inflated** |
| **increment R²** | **0.04** | honest measure — explains ~4 % of the dynamics |

**PINN vs baseline (12 representative nodes, fair one-step metric):**

| | PINN | Baseline |
|---|---|---|
| median one-step RMSE | 1.504 °C | **1.478 °C** |
| median increment R² | 0.009 | **0.045** |
| **PINN beats baseline — RMSE** | **0 / 12** | — |
| **PINN beats baseline — incR²** | **0 / 12** | — |

The PINN is marginally **worse** on every node. `R_eff` and `T_ref` agree with
the baseline (independent confirmation of the steady-state physics); `τ` is
~9× inflated by MLP spectral bias.

**Adversarial audit (framing-independent test):**

- The baseline residual (0.74–1.71 °C) is **1.9–4.4× the quantization floor**
  (0.39 °C) — so it is **not** mostly quantization (correcting a Phase 10
  claim).
- But a linear model of **all** observables (P, ΔP, fan, T) explains
  **R² = 0.001–0.042** of the residual; every individual correlation ≈ 0.
- **Conclusion:** the residual is real but **orthogonal to the available
  inputs** — unlearnable by any model within scope.

## Scientific Findings

1. **Classical first-order physics captures the thermal envelope** (a
   consistent, sensible `τ_eff` across 372 independent nodes) but explains
   almost none of the step-to-step dynamics (increment R² ≈ 0.04).
2. **The PINN does not beat the baseline** — marginally worse on every tested
   node, on both fair metrics.
3. **The unexplained residual is not quantization and not learnable** from the
   three inputs. It is process/workload noise driven by activity that 20 s
   socket power does not resolve.
4. **Two independent methods agree on the steady-state physics** (`R_eff`,
   `T_ref`) — the PINN's one genuine positive contribution: cross-validation
   of the baseline.

## Limitations

- **Data:** 62 h usable window (not longitudinal); 20 s sampling and 1 °C
  quantization; socket power vs single-core temperature (spatial mismatch);
  observational closed-loop (no causal claims); coolant temperature
  out of scope, so `T_ref` is a learned extrapolation.
- **Physics:** effective parameters only; `R_eff`/`C_eff` absorb an
  unobservable heat fraction; `τ` is not robustly identifiable (the two methods
  bracket it).
- **PINN:** single-node; small MLP has spectral bias (inflates `τ`); its
  physics loss, being the baseline's own model, structurally limits it to
  matching rather than exceeding the baseline; CPU-trained, Adam-only.
- **Scope:** three metrics of ~338; one record of 12–13; CPU socket 0 only.

## Conclusions

> **Within GLASSCHIP-V1, the classical first-order model is the appropriate
> description of the data. The residual it leaves is real but orthogonal to
> everything observed, so no PINN — however implemented — can beat it here.**

This is a **negative result, and a rigorous one.** The PINN was not required to
win; it was required to answer the scientific question honestly, and it did:
the physics that *can* be learned from these inputs is already captured by the
classical baseline, and what remains is not recoverable. The value of the PINN
in this project is an independent confirmation of the baseline's steady-state
physics and a clean demonstration — via the adversarial audit — of *why* the
remaining residual is irreducible: not noise-free, not quantization, but
input-orthogonal.
