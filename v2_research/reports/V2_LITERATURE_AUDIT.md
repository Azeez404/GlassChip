# GLASSCHIP-V2 — Literature Audit (2024–2026)

Focused audit run alongside dataset acquisition. **Direct evidence** (from
retrieved abstracts) is separated from **my inference**.

---

## Retrieved works

| Paper / source | Year | Idea | Data / boundary | Relevance to V2 |
|---|---|---|---|---|
| PG-RSSNN — Physics-Guided Recurrent State-Space NN (arXiv 2606.02278) | 2026 | recurrent latent state, multi-step rollout without divergence | generic dynamical systems | recurrence method — *only if* a multi-step signal is shown to exist |
| Graph Neural ODE Digital Twins for reactor thermal-hydraulics under partial observability (arXiv 2604.07292) | 2026 | message-passing GNN + Neural ODE, directed sensor graph | reactor loops | multi-node/graph method for coupled thermal loops |
| Physics-constrained graph thermal networks for spacecraft digital twins (arXiv 2605.28452) | 2026 | interpretable graph Neural ODE, physical nodes | spacecraft | node = physical thermal element (core/spreader/coolant) |
| AI & digital twins for DC cooling failure prediction — review (EPJ ST, `10.1140/epjs/s11734-026-02411-x`) | 2026 | survey: classical→RNN→GNN→transformer→PINN→hybrid DT | data-center cooling | confirms field direction: hybrid physics-informed |
| Adaptive physically-consistent NN for DC thermal dynamics; monotonicity constraints (coolant flow/heat-load) | 2025 | monotone physical constraints prevent spurious correlations | liquid-cooled DC | constraint design; safety/interpretability |
| Frontier Energy dataset (Nature SciData, `10.1038/s41597-024-03913-w`) | 2024 | facility energy + cooling-loop telemetry | **facility-level** | **not node-level** (see dataset inventory) |
| Machine-learning cooling optimisation, IEEE ITherm best paper (arXiv 2601.02275) | 2026 | ML DC cooling optimisation | DC facility | control-oriented, facility scope |
| DeepOHeat / DeepOHeat-v1 (DAC'23 / arXiv 2504.03955) | 2023–25 | operator learning for 3D-IC thermal | simulated, known power map | needs a power map M100/Frontier lack |
| BPINN-EM (ICCAD'24) | 2024 | Bayesian PINN, electromigration UQ | simulated | UQ, not the V2 bottleneck |

---

## Direct evidence (what the abstracts state)

1. The field is consolidating on **hybrid physics-informed** architectures
   (PINN / graph / recurrent / digital-twin), moving away from pure
   data-driven models (EPJ ST review).
2. **Coolant/boundary-aware** modelling and **monotonicity constraints** are
   emphasised for liquid-cooled data centers (2025 adaptive-PCNN work).
3. **Graph Neural ODE** is the current method of choice for *coupled
   multi-node thermal loops under partial observability* (2026 reactor and
   spacecraft papers).
4. Recurrent **state-space** PINNs address multi-step prediction (PG-RSSNN).

## My inference (clearly labelled)

- The recurring prerequisite across all these methods is **richer observation**
  — a measured boundary and/or spatial sensor graph. The architectures assume
  the observability V1/V2-audit showed M100 lacks. **None of them would
  overcome the V1 residual on M100**, because they need inputs M100 does not
  provide at the node level.
- No retrieved 2024–2026 work reports a *fleet-scale HPC dataset with
  node-level co-located processor temperature + power + coolant boundary at
  sub-20 s resolution.* This absence is consistent with the Phase V2-1 finding
  that no such accessible public dataset exists.

## Novelty position (verified, not assumed)

GLASSCHIP-V1's **honest negative result** — a rigorous demonstration that the
residual is *unlearnable from the available observations*, with an
out-of-sample observability test rather than a benchmark chase — is **not**
the standard framing in this literature, which predominantly reports positive
model results on richer or simulated data. This methodological stance (test
observability before modelling) remains GLASSCHIP's distinctive contribution.
