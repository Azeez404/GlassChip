# GLASSCHIP-V1 — Project Handover

**Status: FROZEN. Scientifically complete.** This document is sufficient to
continue the project without reading the whole repository. For the full
scientific story see `docs/RESEARCH_SUMMARY.md`; for usage see `README.md`.

---

## 1. What GLASSCHIP-V1 is

A test of one question on real HPC processor telemetry:

> Can a physics-informed neural network (PINN) learn thermal behaviour that
> classical first-order physics cannot already explain, from the same 
> observable inputs?

**Answer (demonstrated, not assumed): NO.** The classical first-order model
is the appropriate description; what it leaves unexplained is not learnable
from the available inputs. This is a rigorous negative result.

- **Dataset:** M100 ExaData (CINECA Marconi100), record `21-03`, CC-BY-4.0.
  Public, downloaded separately, never committed.
- **Inputs (locked):** temperature (`p0_core0_temp`), power (`p0_power`),
  fan speed (`fan0_0`) — the IPMI triple that shares an exact 20 s timestamp
  grid.

---

## 2. Completed phases (all locked)

| # | Phase | Outcome |
|---|---|---|
| 1 | Dataset exploration / schema / EDA | 3 inputs on a 20 s grid; 61.978 h usable window |
| 2 | Loader + Validator | read + compatibility gating |
| 3 | Preprocessing | exact-timestamp join; model-ready per-node frames |
| 4 | Visualization | descriptive only |
| 5 | Physics understanding | first-order lumped ODE is the only defensible model |
| 6 | PINN design | smallest defensible PINN specified |
| 7 | Thermal-intelligence design | one PINN yields behaviour/anomaly/monitoring as readings of one residual |
| 8 | Node screening | **372 PASS / 22 FAIL** of 394 |
| 9 | Classical baseline | median `τ_eff` ≈ 230 s; increment R² ≈ 0.04 |
| 10 | PINN implementation | **PINN beats baseline on 0/12 nodes** |
| 11 | Adversarial audit | conclusion upheld; residual is input-orthogonal, not quantization |
| 12 | Freeze + cleanup | repository release-ready |

---

## 3. Locked modules (`src/`, 7 layers)

`loader` → `validator` → `preprocessing` → `visualization` → `screening` →
`baseline` → `pinn`. Each has comprehensive in-code docstrings (the API
reference lives in the source). The dependency order is the pipeline order;
each layer refuses to proceed on upstream failure.

**Do not modify these implementations.** Reproducibility is pinned to them
(see §6).

---

## 4. Scientific conclusions (the load-bearing facts)

1. **Classical first-order physics captures the thermal envelope** — a
   consistent, physically sensible `τ_eff ≈ 230 s` across 372 independent
   nodes — but explains **~4 %** of the step-to-step dynamics (increment R²).
2. **The PINN does not beat the baseline** — marginally worse on all 12
   tested nodes, on both one-step RMSE and increment R². Its `τ` is ~9×
   inflated by MLP spectral bias; its `R_eff`/`T_ref` agree with the baseline
   (independent confirmation of the steady-state physics).
3. **The unexplained residual is real but unlearnable here.** It is
   1.9–4.4× the quantization floor (so *not* mostly quantization), yet a
   linear model of all observables (P, ΔP, fan, T) explains only
   **R² ≤ 0.04** of it. It is orthogonal to every available input.
4. **Therefore no PINN within scope can beat the baseline** — this is a
   data-observability limit, independent of implementation.

---

## 5. Repository structure

```
README.md              overview, install, usage, layout
requirements.txt       pinned dependencies
docs/
  RESEARCH_SUMMARY.md  complete scientific story (methodology, results)
  handovers/HANDOVER.md  this file
reports/validation/    the compatibility (PASS/FAIL) report
src/                   7 locked layers (docstrings = API reference)
examples/              run_pipeline.py, run_baseline.py, run_pinn.py
data/                  raw/ (Zenodo, gitignored) + exports/ (generated, gitignored)
```

---

## 6. Reproducibility

- Python 3.10+ (verified 3.13). `pip install -r requirements.txt`
  (pandas, pyarrow, numpy, matplotlib, torch-cpu).
- Dataset: download M100 record `21-03` from Zenodo into `data/raw/21-03/`
  (see README). Never committed.
- **Determinism anchor:** node-15 model-ready frame SHA-256 (first 16) =
  `8473342129fb19f0`, via `TimeSeriesBuilder`. If this changes, something in
  the locked pipeline changed.
- Entry points: the three `examples/run_*.py` scripts (self-bootstrap `src/`
  onto the path).

---

## 7. Known limitations (all documented, none hidden)

- **Data:** 62 h usable window (not longitudinal); 20 s sampling and 1 °C
  quantization; socket power vs single-core temperature (spatial mismatch);
  observational closed-loop (no causal claims); coolant temperature out of
  scope, so `T_ref` is a learned extrapolation.
- **Physics:** effective parameters only; `R_eff`/`C_eff` absorb an
  unobservable heat fraction; `τ` not robustly identifiable.
- **PINN:** single-node; small MLP has spectral bias; its physics loss (the
  baseline's own model) structurally limits it to matching, not exceeding,
  the baseline; CPU-trained, Adam-only.
- **Scope:** 3 of ~338 metrics; 1 of 12–13 records; CPU socket 0 only.

---

## 8. Remaining work in GLASSCHIP-V1

**None required.** V1 is frozen and complete. The only optional, in-scope
housekeeping (do **not** treat as mandatory):

- Run `run_baseline.py` without the node cap to regenerate the full 372-node
  parameter table (a regenerable output; not committed).
- Add unit tests under a `tests/` folder if desired (none exist).

---

## 9. What must NEVER be changed in GLASSCHIP-V1

- The three locked inputs (temperature, power, fan) — utilisation/frequency
  are on a different grid and were excluded for a proven reason (5.7 % exact
  timestamp match).
- The exact-timestamp join (no tolerance joins, no interpolation across the
  648.9 h gap).
- The node-screening gates (372/22) and their thresholds.
- The classical baseline's discrete first-order formulation.
- The scientific conclusion (§4) and its honest framing.
- The `8473342129fb19f0` reproducibility anchor.

---

## 10. Exactly what to do next (if continuing)

The V1 result is that **the residual is unlearnable from the three available
inputs.** Any continuation must therefore change *what is observed*, not the
model. This is **discussion only — do not implement under the V1 label.**

**Suggested GLASSCHIP-V2 starting point (not a commitment):**

1. **Add observability, not complexity.** The V1 residual is input-orthogonal,
   so a better network cannot help. The scientifically motivated next step is
   richer inputs from the *same dataset* that V1 excluded — e.g. per-core
   temperatures, utilisation/frequency (accepting their coarser grid via an
   explicit, documented resampling decision), or the facility coolant
   temperature (which would turn `T_ref` from a learned extrapolation into a
   measured boundary condition).
2. **Or change the target.** Longitudinal analysis across multiple Zenodo
   records (V1 used one) could test slow degradation — a different, learnable
   signal.
3. **Keep the honesty bar.** V2 must first re-establish whether its new inputs
   carry mutual information with the residual (the Phase-11 test), before
   building any model. Do not repeat V1's near-miss of blaming the model for a
   data limit.

Whatever V2 does, it is a **new project label** — V1 stays frozen.

---

## 11. One-paragraph summary for a cold start

GLASSCHIP-V1 asks whether a PINN beats classical first-order thermal physics
on Marconi100 processor telemetry (temperature, power, fan; 20 s; one 62 h
window). After screening 394 nodes to 372, a discrete first-order model
recovers a sensible `τ ≈ 230 s` but explains ~4 % of the dynamics; the PINN,
compared fairly, beats it on 0/12 nodes. An adversarial audit shows the
leftover residual is real but orthogonal to every input (R² ≤ 0.04), so no
model can recover it here. The project is a clean negative result, frozen and
release-ready. Continuation requires new *observations*, not new *models* —
that is the V2 question.
