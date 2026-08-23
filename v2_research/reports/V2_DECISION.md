# GLASSCHIP-V2 — Decision Report

**GATE V2-α: could not be executed → primary direction (D1, richer external
observations) STOPS. Single recommended next action: pivot to D2 (longitudinal
M100), beginning with GATE B (cross-record node identity).**

---

## Decision Table

| Question | Result | Evidence |
|---|---|---|
| Is the (Frontier) dataset actually richer than M100? | **No** — facility-level, same coolant *class* M100 already had | `data_audit/dataset_inventory.md`; 3 abstracts (Nature/PubMed/OSTI) |
| Is a coolant boundary measured? | Only at **facility/loop level**, not node-level (as in M100) | abstracts |
| Is temporal resolution improved? | **No** — facility energy telemetry, coarse | abstracts |
| Is power physically aligned with temperature? | **N/A** — no per-node temperature exists in the dataset | abstracts |
| Is the residual smaller on the new data? | **Cannot compute** — no per-node processor data | — |
| Does coolant information predict the residual? | **Cannot test** — facility loop, no node attribution | — |
| Does finer sampling predict the residual? | **Cannot test** — no finer sampling available | — |
| Does combined information predict the residual? | **Cannot test** | — |
| **Does GATE V2-α pass?** | **NO — unrunnable** (no suitable dataset) | Phase V2-α report |
| Is a PINN justified? | **No** | no observability evidence |
| Is recurrence justified? | **No** | V2-audit: no out-of-sample temporal structure at 20 s |
| Is multi-node physics justified? | **No** | V2-audit: per-core temps give no out-of-sample gain |

---

## Interpretation

The V2 hypothesis was that **richer node-level observations** (measured coolant
boundary and/or sub-20 s resolution) could make the V1 residual learnable.
Phase V2-1 verified, from primary sources, that **no accessible public dataset
provides those observations at the node level**:

- Frontier = facility/loop-level (the prior audit's "per-blade" claim was the
  machine's architecture, not the dataset's contents — corrected).
- Eagle = coarse Ganglia + iLO, 6 nodes, no node coolant.
- UCR IR / consumer-25 Hz = different gaps, gated, single-device / no HPC
  coolant.

The barrier is confirmed to be **observations that do not exist in reachable
data** — consistent with, and strengthening, V1's conclusion. It is neither a
model-complexity problem nor a metric-selection problem.

---

## Recommended Next Action (exactly one)

> **Pivot to D2 — the longitudinal M100 target — and execute GATE B first:
> test cross-record node identity by acquiring one additional M100 record and
> checking whether node IDs correspond to the same physical machines across
> records.**

Rationale: D2 is the *only* direction answerable with **obtainable** data (more
M100 records are public, CC-BY-4.0). It changes the *question* — from the
irreducible 20 s increment to slow `τ_eff` drift across records — to one the
available observations may support. GATE B is its clean, concrete, testable
prerequisite (V1 left it open; do not pool records until identity is proven).

**Concrete first step of D2:**
1. Download one further M100 record (e.g. a different `year_month`).
2. Test node-identity stability across records (statistical signature
   matching, ID-set overlap, sensor-fingerprint consistency).
3. **Only if GATE B passes:** test whether `τ_eff` is stably identifiable
   per record (V1 found `τ` poorly identified — this is a genuine risk for a
   drift target) *before* any drift modelling.

**Honesty caveat carried forward:** D2 abandons the original "make the residual
learnable" goal for a different question. If GATE B fails, or `τ_eff` proves
too poorly identified per record to track drift, then the scientifically
complete answer is that **GLASSCHIP's thermal-learnability question is closed
for available public data**, and V2 should stop rather than manufacture a
result.

---

## What must NOT happen next

- No PINN / recurrent / multi-node / graph model on M100's 20 s residual.
- No use of Frontier's facility coolant as a node boundary (fabrication).
- No pooling of M100 records before GATE B passes.
- No modification of frozen GLASSCHIP-V1.
