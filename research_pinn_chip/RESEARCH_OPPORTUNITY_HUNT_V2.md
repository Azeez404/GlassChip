# RESEARCH OPPORTUNITY HUNT V2
## Second PINN / scientific-ML hunt after the failed Summit GPU thermal prototype

Audit only. No code, no experiments, no plots, nothing committed. Datasets verified by direct
inspection or by fetching the publisher/repository page — not assumed from paper abstracts.

---

## 1. Executive conclusion

**NO VIABLE PINN PROBLEM FOUND** — at the level of a serious paper, under the stated
constraints (public data, student-tractable physics, limited time, a genuine structural role
for physics, and a sub-area that is not already saturated).

This is not a failure of searching. Twelve directions were evaluated and every one dies for a
reason belonging to the same small set, which together form a **structural squeeze** on
physics-informed ML in the computer-chip domain:

1. **Where the physics is known and linear** (thermal RC networks, IR drop on a power grid),
   the governing operator is available in closed form, and classical numerical linear algebra
   beats a neural surrogate on the accuracy-per-second frontier. Our own failed prototype is
   direct experimental evidence: the three-parameter classical RC model (4.88 °C RMSE) beat
   every neural variant we trained.
2. **Where the physics needs geometry** (thermal fields, hotspots, 3D-IC/chiplet stacks), the
   floorplan is proprietary for exactly those chips that have public telemetry, and public for
   simulators that have no real measurements. You can have the equation or the data, not both.
3. **Where the physics is genuinely unknown and nonlinear** (leakage–temperature feedback,
   aging), either the signal is not measurable in public data — **verified below, not assumed**
   — or the sub-area already has published PIML work.
4. **Where data is abundant**, gradient-boosted trees win, which we measured rather than
   supposed.

The least-dead PIML candidate is a **structurally-embedded UDE for long-horizon thermal
stability** (Candidate 3 below). It is honest, cheap, and would probably work — but its novelty
is low and its ceiling is a workshop paper. It is graded INVESTIGATE, not GO.

**The strongest actual research available in this domain requires no neural network at all**
and is documented in `RESEARCH_OPPORTUNITY_HUNT.md`: measurement-based identification of GPU
die↔HBM thermal coupling across production GPUs. Recommending a weak PIML project over a
stronger non-PIML one purely to keep a neural network in the story would be the wrong call.

---

## 2. What the failed Summit PINN taught us

The prototype is not merely a negative datapoint; it diagnosed a mechanism that constrains this
entire search.

| Model | Multi-step RMSE (H=30) |
|---|---|
| GBT | **4.44 °C** |
| Classical RC | 4.88 °C |
| PINN-strict (ablation) | 6.24 °C |
| MLP, λ=0 (ablation) | 6.60 °C |
| GBT tail-weighted | 6.91 °C |
| **PINN (soft physics + collocation)** | **27.81 °C** |

Three transferable lessons:

- **A soft physics penalty is not a physics guarantee.** The PINN diverged monotonically to
  117 °C where truth was 60 °C. Two competing loss terms with out-of-distribution collocation
  points produced a physics-*induced* runaway. Structural embedding of the mechanistic term in
  the forward map cannot fail this way — the distinction is architectural, not a tuning knob.
- **Simple linear physics is a liability, not an asset, for a neural formulation.** If a
  three-parameter least-squares fit beats your network, the physics was never the bottleneck.
- **Accuracy on an abundant-data forecasting task is the wrong target.** Trees own that regime.
  Any surviving candidate must offer something a tree structurally *cannot* provide.

This last lesson is applied below as a hard filter, and it eliminates most of the field.

---

## 3. Research landscape

Searched arXiv, IEEE Xplore, ACM DL, ScienceDirect, Springer, Nature, MDPI, plus dataset hosts
(Hugging Face, GitHub, Zenodo, OSTI, data.gov), weighted to 2024–2026.

**Saturated — do not enter:**
- *Chip thermal surrogates / operator learning*: DeepOHeat (DAC 2023, arXiv:2302.12949) →
  Enhanced Operator Learning (ASP-DAC 2025) → DeepOHeat-v1 (arXiv:2504.03955, KAN trunk nets).
- *PINN sparse-sensor thermal field reconstruction*: extensively covered, **including
  semiconductors** — silicon-wafer thermoelastic reconstruction with PINN+FNO in photolithography
  (Eng. App. AI 2025), 3D heat conduction in bulk FinFET structures, physics-driven sensor
  placement optimisation (Applied Thermal Eng. 2024), FOSSA sensor selection for PINN inverse
  problems (arXiv:2604.06534).
- *PINN inverse heat conduction*: E-PINN, PIHNO, heat-source field inversion, compressive-sensing
  variants.
- *PINN datacenter/GPU thermal control*: knowledge-embedded PINN for GPU-datacenter HVAC (Feb
  2026), physics-aware GPU power forecasting (arXiv:2605.04074), 2025 review of PINNs for
  electronics/battery thermal management.
- *Physics-informed RUL for power semiconductors*: online PINN for electronic-equipment RUL
  (Scientific Reports 2025), Coffin-Manson physics-guided losses for IGBT.

**Active but CV-dominated:** static/dynamic IR drop — PDNNet (arXiv:2403.18569), CFIRSTNET
(arXiv:2502.12168), Attention U-Net (arXiv:2408.03292), WACA-UNet (arXiv:2507.19197). The
ConvNeXtV2 attention U-Net reports a 61.1% MAE reduction over the ICCAD-2023 contest winner. An
accuracy race a student will not win.

**Proven template in an adjacent domain:** *Residual-Corrected Equivalent-Circuit Model with
Universal Differential Equations for Robust Battery Voltage Prediction under Operating-Condition
Shift* (arXiv:2605.06419) — compact physical model + learned structured residual, beating LSTM
baselines under temperature and drive-cycle transfer. This is the strongest existing evidence
that a structural hybrid works under distribution shift, and it is also why the chip analogue
would read as a domain transfer rather than a method contribution.

---

## 4. Candidate matrix

| # | Candidate | Structural role for physics | Public data verified | Saturation | Verdict |
|---|---|---|---|---|---|
| 1 | GPU hot-regime thermal forecasting | None (tested) | Yes | — | **KILLED experimentally** |
| 2 | Sparse sensor → die thermal field | Strong in principle | Sim only; no floorplan for chips with public telemetry | **High** | REJECT |
| 3 | **Structural UDE for long-horizon thermal stability** | **Moderate — provable boundedness** | **Yes** | Moderate | **INVESTIGATE (best PIML)** |
| 4 | IR drop / PDN with KCL constraint | Weak — linear solve, operator known | Yes (ICCAD-2023, CircuitNet) | High (CV) | REJECT |
| 5 | Leakage–temperature feedback (UDE) | Strong in principle | **Signal verified too weak + confounded** | Low | **REJECT — data-verified kill** |
| 6 | Semiconductor aging / RUL (IGBT) | Strong | Yes (NASA 7wwx-fk77) | High | REJECT (crowded; not a processor) |
| 7 | GPU die↔HBM coupling | **None — fully observed** | Yes | Low | Reject *as PIML*; strong as classical ID |
| 8 | Thermal parameter identification | None — closed form | Yes | — | REJECT |
| 9 | Missing per-core sensor reconstruction | Moderate | No logical→physical core map | Moderate | REJECT — unfalsifiable |
| 10 | Cross-device / cross-facility transfer | Moderate | Yes | Low | REJECT — confounded |
| 11 | Physics-constrained anomaly detection | Moderate | Yes + Nagios labels | Owned by dataset authors | REJECT |
| 12 | 3D-IC / chiplet thermal (CoMeT, HotSpot) | Strong | Simulator public, no real data | High | REJECT — simulation-only |

---

## 5. Detailed analysis of the decisive candidates

### Candidate 5 — Leakage–temperature feedback *(the one I most wanted to work)*

**Problem.** Leakage current rises with temperature, which raises temperature further. The
functional form is empirical and device-specific — a genuinely *unknown function*, which is the
textbook case where a UDE earns its place over parameter fitting.

**Why it should have worked.** No geometry needed (lumped scalar relation); physics known in
form but not in parameters; not saturated for processors on production telemetry; falsifiable
(does the learned leakage curve come out monotone increasing?).

**Why it is dead — verified, not assumed.** I tested whether the signal is observable. Taking
the lowest power decile per GPU as an idle proxy (dynamic power ≈ constant, so residual power
variation ≈ leakage), across 6 hosts:

| Host | n idle | corr(P, T) | median P across T bins |
|---|---|---|---|
| a07n04 | 119,185 | +0.139 | 35.20 → 35.22 W |
| a09n18 | 158,618 | +0.193 | 34.0 → 34.0 W |
| a11n12 | 197,529 | +0.255 | 33.0 → 33.0 W |
| a13n06 | 125,934 | +0.140 | 35.20 → 35.33 W |
| a14n08 | 126,284 | +0.203 | 30.67 → 30.78 W |
| a16n12 | 215,179 | +0.514 | 34.88 → 35.00 W |

The correlation has the right sign consistently (mean +0.241). But the effect is **~0.1–0.3 W
on a 35 W baseline**, the idle temperature range is narrow (mostly 28–32 °C, giving almost no
leverage), and — fatally — **the correlation is fully explained by the confound**: power causes
temperature, so any residual workload variation produces exactly this positive corr(P, T) with
zero leakage present. There is no instrument in this dataset to break that confound.

**KILL.** This check took two minutes and saved weeks.

### Candidate 4 — IR drop / power delivery network

**Problem.** Solve **G·v = i** on the chip's power grid: current through resistance causes
voltage droop, which slows or breaks timing. Ground truth needs a large sparse solve.

**Physics in plain language.** The power grid is a huge mesh of resistors. Ohm's law says
voltage lost = current × resistance; Kirchhoff says current in equals current out at every
node. That is the whole model — genuinely simpler than any thermal PDE.

**Data — verified.** ICCAD 2023 CAD Contest Problem C: 20 real circuits (10 released, 10
hidden) plus hundreds of synthetic benchmarks. CircuitNet (github.com/circuitnet/CircuitNet,
also on Hugging Face): >10K samples from 6 open-source RISC-V designs, 28 nm (N28) and 14 nm
(N14), LEF/DEF and graph features, IR drop / congestion / DRC / timing. Both genuinely public
and downloadable.

**Why it fails the filter.** The problem is a **linear system with a fully known operator**. If
you have G and i — and the contest inputs give you exactly that — the physics residual is
computable, but so is the exact answer, by a sparse direct solve or multigrid. A physics-informed
network is then a slow approximate linear solver competing against decades of optimised
numerical linear algebra. Meanwhile the accuracy race is dominated by CV architectures posting
61% MAE reductions. **REJECT.**

### Candidate 3 — Structural UDE for long-horizon thermal stability *(best surviving PIML)*

**Research question.** Does embedding the thermal energy balance *structurally* in the forward
model — rather than as a soft loss penalty — guarantee bounded long-horizon GPU temperature
predictions where both black-box models and soft-constrained PINNs drift or diverge?

**Structural argument, and it is a real one.** Write

    dT/dt = [ a·P − b·(T − T_amb) ]  +  NN(features)
             └── mechanistic term ──┘    └ learned residual ┘

with a, b > 0 enforced. The mechanistic term is a restoring force present in every forward step,
so the model has a provably bounded steady state T → T_amb + a·P/b. A black-box model has no
such guarantee, and our measured results show both failure modes concretely: the soft-penalty
PINN diverged to 117 °C, and the GBT drifted monotonically downward. **Boundedness is a provable
property, not an accuracy hope** — which is the only thing on the "valid structural advantage"
list that this domain actually offers.

**Feasibility.** Data local and verified; physics is one line; the evaluation harness from the
failed prototype can be re-derived quickly. Prototype in hours.

**Why it is still only INVESTIGATE.** The novelty is low. The battery UDE paper
(arXiv:2605.06419) already demonstrates precisely this advantage under distribution shift, in a
different device class. The chip version is a domain transfer of an established method — exactly
the "we applied method X to dataset Y" framing to avoid. Best realistic outcome: a workshop
paper.

---

## 6. Dataset verification

| Dataset | Source | Verified content | Sufficient? |
|---|---|---|---|
| **Summit power/thermal** | OSTI/OLCF DOI 10.13139/OLCF/1861393, CC-BY-4.0; local | Per-GPU power 17–400 W float; GPU core temp float; HBM temp float; 10 s; 6 GPUs × 4,626 nodes. Timestamps monotonic, 0 duplicates. Channel map verified by correlation | Yes for thermal dynamics; **no floorplan, no coolant inlet temperature** |
| **M100 ExaData** | Sci. Data 10:288, CC-BY; local | 24 per-core temps × 2 sockets, ambient, fans, 934 days. **`gv100card*` per-GPU power is identically zero across 10.7 M rows** | No — cannot drive a physical GPU model |
| **ICCAD 2023 Contest C** | IEEE Xplore 10323767 | 20 real (10 hidden) + hundreds of synthetic IR-drop benchmarks | Yes, but candidate rejected on method grounds |
| **CircuitNet / N14 / N28** | github.com/circuitnet/CircuitNet, Hugging Face | >10K samples, 6 RISC-V designs, LEF/DEF, IR drop + congestion + timing | Yes, but candidate rejected |
| **NASA IGBT aging** | data.gov `7wwx-fk77` | IRG4BC30KD thermal cycling; V_ge, V_ce, I_c | Yes, but power device ≠ processor, and PIML RUL is crowded |
| **HotSpot 6/7** | github.com/uvahotspot/HotSpot | Grid + block models, 3D-IC, **leakage mode**, example configs, BU 3D test suite | Simulator only — no real chip to validate against |
| **CoMeT** | github.com/marg-tools/CoMeT | 2D/2.5D/3D core-memory interval thermal simulation | Simulation only |

**The recurring dataset problem, stated once:** the chips with public *telemetry* (POWER9,
V100) have no public *floorplan*; the simulators with public geometry (HotSpot, CoMeT) have no
real measurements. Every geometry-dependent PIML formulation dies on this gap.

---

## 7. Prior-art and PIML justification summary

Applying the key filter — *what does the physics provide that the data does not?* — to every
candidate:

| Advantage claimed | Available here? |
|---|---|
| Hidden/unobservable state | **No** for the well-posed GPU problem (P, T_core, T_mem all measured) |
| Conservation laws | Yes, but linear and already exactly solvable |
| Physical bounds | **Yes — Candidate 3.** The one real advantage on offer |
| Sparse observations | Only with geometry we do not have |
| Expensive labels | Yes for IR drop — but then a direct solver is the competitor |
| Extrapolation | **Measured and refuted** in our prototype; literature also documents PINNs extrapolating poorly |
| Long-horizon stability | **Yes — Candidate 3** |
| Sim-to-real bridging | Blocked: no floorplan for chips with public data |

One advantage survives — bounded long-horizon behaviour — and it supports exactly one candidate.

---

## 8. Reviewer-from-hell test on the top 3

**Candidate 3 (Structural UDE).** *"Why not just use the classical RC, which already scored 4.88
and is provably bounded?"* — This is the killer, and it has no clean answer. The RC alone is
stable, interpretable, and nearly as accurate; the learned residual must earn its complexity.
*"Isn't this the battery paper with GPUs substituted?"* — Substantially, yes. **Survives, wounded.**

**Candidate 4 (IR drop).** *"Why is a neural network solving a linear system with a known
matrix?"* — No answer. *"Your baseline is a U-Net posting 61% MAE improvements; where do you
fit?"* — Nowhere. **Killed.**

**Candidate 7 (GPU die↔HBM).** *"Where is the neural network and why do you need one?"* — There
isn't one, and it doesn't. **Killed as PIML; strong as classical identification.**

---

## 9–11. Ranking

🥇 **BEST SCIENTIFIC OPPORTUNITY — and it is not a PIML project.** Measurement-based
identification of GPU die↔HBM thermal coupling across production GPUs (see
`RESEARCH_OPPORTUNITY_HUNT.md`). Physics-constrained state-space identification, no neural
network. Novelty 68 / Impact 76 / Feasibility 88.

🥈 **BEST BALANCE (PIML) — Candidate 3**, structural UDE for long-horizon thermal stability.
Honest, cheap, probably works, low novelty, workshop ceiling.

🥉 **SAFEST PUBLICATION PATH.** Submit the finished GLASSCHIP measurement-quality paper to
FGCS/JPDC. It exists, it is journal-ready, and it is the only asset with a near-certain outcome.

💀 **MOST TEMPTING BUT BAD IDEA — IR drop with a physics-informed network.** It has everything
that looks right on paper: verified public benchmarks (ICCAD-2023, CircuitNet), trivially
explainable physics (Ohm + Kirchhoff), expensive labels, real industrial relevance, and a
visible ML literature to compare against. It is a trap. The operator is known and the system is
linear, so a neural model is an inferior linear solver; and the accuracy race is already run by
CV specialists. It would consume the whole window and produce a paper that reviewers reject in
one sentence.

---

## 12–20. If Candidate 3 is pursued anyway

**Research question.** Does structurally embedding a thermal energy balance in the forward
model, rather than imposing it as a loss penalty, produce bounded and physically admissible
long-horizon GPU temperature predictions where black-box and soft-constrained models drift or
diverge?

**Hypothesis.** At long horizons (H ≥ 300 steps = 3000 s) the structural UDE remains bounded and
converges to a physically sensible steady state, while GBT drifts without bound and the
soft-penalty PINN diverges. At short horizons the UDE is merely competitive.

**Minimum prototype.** Reuse the verified trace (a11n12 GPU5) and the same regime split. Add one
arm: `dT/dt = a·P − b·(T − T_amb) + NN(x)` with a, b softplus-positive. Sweep the rollout horizon
H ∈ {30, 100, 300, 1000} and plot RMSE and max |T̂| against H for all arms. **The falsifiable
claim is about the shape of that curve, not about the value at H=30.**

**Kill condition.** The classical RC alone matches the UDE at every horizon (the network adds
nothing), or the UDE also diverges.

**Expected scores.** Novelty 34/100 · Impact 42/100 · Feasibility 90/100 · Publication 40/100.

**Risks.** Low novelty is the dominant one. Secondary: the classical RC is already bounded, so
the comparison may reduce to "the network adds noise to a model that was already fine."

---

## 21. Recommended next action

Do **not** start Candidate 3 first. In priority order:

1. **Submit the finished GLASSCHIP measurement-quality paper** to FGCS or JPDC. It is done and
   it is the only near-certain outcome in the portfolio.
2. **Start the non-PIML GPU die↔HBM identification project.** It scored highest on every axis and
   needs no neural network.
3. Treat Candidate 3 as an optional half-day experiment appended to (2) — the die↔HBM work
   produces the same harness, so the long-horizon stability test becomes nearly free.

Adding a neural network to this research programme is not currently justified by the evidence.

---

WINNER:
None. NO VIABLE PINN PROBLEM FOUND at serious-paper level under the stated constraints. The least-dead PIML candidate is a structurally-embedded UDE for long-horizon GPU thermal stability, graded INVESTIGATE and workshop-ceiling; the strongest actual research in this domain requires no neural network.

RESEARCH QUESTION:
(For the fallback PIML candidate only) Does structurally embedding a thermal energy balance in the forward model, rather than imposing it as a loss penalty, produce bounded long-horizon GPU temperature predictions where black-box and soft-constrained models drift or diverge?

METHOD:
Universal Differential Equation / structural hybrid — mechanistic RC term plus a learned residual inside the integrator. Explicitly not a PINN: the failed prototype showed that a soft physics penalty produces physics-induced runaway, which structural embedding avoids by construction.

WHY PHYSICS IS NECESSARY:
It is not necessary for accuracy — a three-parameter classical model already beat every neural variant we trained. The single defensible role left is guaranteeing that predictions stay bounded: a mechanistic restoring term in the forward map gives a provable steady state, which no black-box model can promise. That is the only structural advantage this domain offers, and it supports a workshop paper, not a strong one.

DATASET:
Summit per-component power and thermal (OSTI/OLCF DOI 10.13139/OLCF/1861393, CC-BY-4.0) — verified local, per-GPU power 17–400 W with GPU core and HBM temperatures at 10 s across 6 GPUs × 4,626 nodes.

TODAY'S PROTOTYPE:
Add one arm to the existing harness — dT/dt = a·P − b·(T − T_amb) + NN(x) with a, b constrained positive — and sweep the free-running horizon H ∈ {30, 100, 300, 1000}, plotting RMSE and max |T̂| against H for the classical RC, GBT, soft-penalty PINN and structural UDE. The claim under test is the shape of that curve, not the value at any single horizon.

NOVELTY:
34/100

IMPACT:
42/100

FEASIBILITY:
90/100

PUBLICATION POTENTIAL:
40/100

CONFIDENCE:
82/100

GO / INVESTIGATE / KILL:
INVESTIGATE — but deprioritised. The honest headline verdict is NO VIABLE PINN PROBLEM FOUND.

IF GO:
Do not start here. Submit the finished GLASSCHIP measurement-quality paper to FGCS/JPDC, then begin the non-PIML GPU die↔HBM thermal coupling identification project; the structural-UDE horizon sweep can be appended to that work as a half-day experiment once its harness exists.

IF NO VIABLE PINN PROBLEM:
Stated explicitly: under the constraints of public data, student-tractable physics, limited time, a genuine structural role for physics, and an unsaturated sub-area, no computer-chip research problem was found in which physics-informed neural learning provides a defensible advantage sufficient for a serious publication. The domain squeezes PIML from three sides — known linear operators favour classical solvers, geometry-dependent formulations lack public floorplans for the chips that have public telemetry, and the genuinely nonlinear phenomena are either unmeasurable in public data or already covered. Adding a neural network to this research programme is not currently justified by the evidence.
