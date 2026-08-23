# GLASSCHIP-V2 — Phase V2-α Report

**Outcome: GATE V2-α could not be executed — the primary richer-observation
dataset (Frontier) is verified but unsuitable, and no accessible alternative
qualifies. The observability barrier is not crossable with available public
data. This is a STOP on the primary V2 direction (D1), reported honestly.**

---

## 1. What GATE V2-α required

GATE V2-α is the decisive observability experiment: on a dataset with **richer
node-level observations** (a measured coolant boundary and/or finer temporal
resolution), reconstruct the frozen first-order residual and test — with strict
time-series cross-validation, out-of-sample — whether the new observations
predict the residual (target: test R² > ~0.20).

Running it requires a dataset that actually provides those richer node-level
observations.

## 2. Why it could not be run

Phase V2-1 (see `data_audit/dataset_inventory.md`) established, from primary
sources:

- **Frontier Energy dataset** (the audit's primary candidate) is
  **facility/cooling-loop level** — total power, PUE, waste heat from three
  subloops, loop coolant profiles. It has **no per-node processor
  temperature, power, utilisation, or node-co-located coolant boundary.** It is
  the same class of *facility* coolant that M100 already had and V1 could not
  attribute to nodes.
- **NLR Eagle** (6 nodes, Ganglia + iLO) is the same coarse class M100 already
  provides; no node coolant boundary.
- **UCR IR maps** and the **25 Hz consumer-CPU** dataset address different gaps
  (spatial field; single-device temporal resolution), are gated, and provide
  no fleet-scale HPC coolant boundary.

**No accessible public dataset supplies node-level co-located processor
temperature + power + measured coolant boundary at sub-20 s resolution.**
There is therefore no dataset on which GATE V2-α can be meaningfully executed.

Per master-prompt §20 (stop if the dataset cannot provide what is needed) and
§21 (honesty over a positive result), the disciplined action is to STOP the
primary direction here rather than force an experiment on unsuitable data.

## 3. What remains established (V1 + V2-audit, read-only)

- V1: the 20 s residual is unlearnable from V1's three inputs (out-of-sample
  R² ≈ 0).
- V2-audit Phase 2: adding **all** node-level M100 observables (23 per-core
  temps, ambient, VDD, utilisation, frequency, load) does **not** help —
  out-of-sample test R² stayed **negative** (−0.29 to −0.50) while in-sample
  train R² ≈ 0.4 (overfitting). High mutual information was a non-stationarity
  artefact.

The V2-audit's two hypothesised fixes were (i) a measured node-level boundary
and (ii) finer temporal resolution. Phase V2-1 finds **neither is available in
an accessible public dataset.** The barrier is not model complexity and not
metric selection — it is the absence of the required *observations* in any
reachable dataset.

## 4. Consequence

The question "can richer observations make the V1 residual learnable?" **cannot
be answered affirmatively with available public data**, because the required
observations do not exist in an accessible dataset. This does not falsify the
hypothesis; it means the experiment is currently **unrunnable**.

The scientifically honest response is to pivot to the direction that *is*
answerable with obtainable data — see `V2_DECISION.md`.

## 5. What was NOT done (and why that is correct)

- No PINN, recurrent, multi-node, or graph model was built. (No observability
  evidence justifies one; V1 proved complexity cannot recover missing
  information.)
- No structural audit of Frontier was performed. (Acquisition already showed it
  cannot answer the node-level question.)
- No tolerance join, interpolation, or workaround was used to force Frontier's
  facility data onto nodes. (That would fabricate the node-level boundary.)
