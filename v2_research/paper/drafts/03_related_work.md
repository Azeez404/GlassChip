# 3. Background and Related Work (draft v1)

<!-- Citations use short descriptive keys mapping to literature_matrix.md (P1–P13).
Every bibliographic detail (authors, venue, year, DOI) remains [VERIFY] until confirmed
on the publisher/source page in STEP 8. No details are fabricated here. -->

Our study builds on four well-established lines of work. We summarise each, note what it
already establishes, and identify the narrow question that, to the best of our reviewed
literature, they do not jointly answer on real supercomputer measurements.

## 3.1 HPC thermal modeling

Thermal behaviour of large computing systems has been modelled from operational
measurements for both design and management. Compact, distributed thermal models of
supercomputer nodes have been identified directly from in-production systems, including
settings where temperature is reported at coarse (1 °C) resolution and ambient conditions
vary [P1: "Thermal Model Identification of Computing Nodes in HPC Systems", VERIFY;
P2: "Thermal model identification of supercomputing nodes in production environment",
VERIFY; P3: arXiv:1810.01865, VERIFY]. Statistical models of node temperatures across a
supercomputer have also been developed [P4: arXiv:1505.06275, VERIFY], and recent work
calibrates facility-level thermal-dynamic models on the Marconi100 system [P5:
arXiv:2607.28962, VERIFY]. Public per-node measurement datasets, including the Summit
per-component power and thermal dataset we use [P13: DOI 10.13139/OLCF/1861393, VERIFY]
and the M100 dataset [P12: DOI 10.1038/s41597-023-02174-3, VERIFY], have enabled this
line of work. **What this establishes:** identifying compact thermal models of real HPC
nodes — including under coarse temperature resolution — is prior art. **What it does not
establish:** how the identified parameter *changes* when measurement quality is varied in
a controlled way; prior work generally treats coarse measurements as an obstacle to
overcome toward an accurate model, not as an independent variable whose effect is measured.

## 3.2 Thermal system identification

First-order resistor–capacitor and autoregressive-with-exogenous-input (ARX) formulations
are standard for identifying thermal dynamics, and the associated theory distinguishes
structural identifiability (uniqueness under ideal data) from practical identifiability
(recovery under finite, noisy data) [P10: arXiv:2508.18853, VERIFY; P11: PMC10914513,
VERIFY]. **What this establishes:** the estimator we use is standard and well understood.
**What it does not establish:** its behaviour under deliberate, controlled measurement
degradation on a real fleet. We deliberately keep the model frozen and unmodified, using
it only as a probe of measurement quality.

## 3.3 Measurement quantization and sampling

The effect of quantized observations on system identification is a mature topic: uniform
quantization can be viewed within an errors-in-variables framework and is known to bias
conventional least-squares estimates unless the quantization process is accounted for
[P6: "System Identification with Quantized Observations", VERIFY; P7: Automatica 2008,
S0005109807000970, VERIFY; P8: arXiv:1804.10015, VERIFY]. **What this establishes:** that
quantization biases identified parameters is an established mechanism, not a new
discovery. **What it does not establish:** the size of this effect, and of temporal
downsampling and spatial aggregation, on identified thermal parameters of a real
supercomputer, or how that size compares with natural unit-to-unit variation.

## 3.4 Uncertainty under temporal dependence

For temporally dependent data, independent resampling and analytic interval estimates
that assume independence can understate variability; the moving-block bootstrap resamples
consecutive blocks to preserve dependence and is the standard remedy [P9: Künsch 1989,
Annals of Statistics, VERIFY; and the independently proposed block bootstrap of Liu and
Singh 1992, VERIFY]. **What this establishes:** that analytic intervals can be too narrow
under dependence is expected, and the block bootstrap is the accepted correction, which we
use. **What it does not establish:** the specific observation that, for identified thermal
parameters under quantization, a narrow interval can surround a substantially *biased*
estimate — a matter of accuracy, not only interval width.

## 3.5 Physics-informed and residual learning

A recurring theme across dynamical-systems modelling is that identifiability and
predictive accuracy can diverge: parameters that fit calibration data can still yield poor
predictions under new conditions [P10: arXiv:2508.18853, VERIFY; P11: PMC10914513,
VERIFY]. Physics-informed and residual-correction approaches have been applied to thermal
and other dynamical systems. **What this establishes:** the general principle that better
identification need not imply better prediction. **What it does not establish:** whether,
for real supercomputer measurements, improving measurement quality sharpens identification
without materially improving out-of-sample prediction of the residual. We include a
physics-constrained neural residual model only as one of several baselines; it is not the
contribution of this paper.

## 3.6 Online thermal monitoring

Online monitoring and change detection for HPC systems is an active area
[VERIFY: add one or two representative HPC thermal-monitoring references]. **What this
establishes:** interest in deriving operational signals from thermal measurements. **What
it does not establish:** whether an online effective-τ statistic, computed causally from
short windows, functions as a useful standalone monitor. We report a negative operational
boundary for this specific statistic.

## 3.7 Research gap

Each ingredient above is individually established: HPC thermal identification (§3.1),
standard identification estimators (§3.2), quantization-induced bias (§3.3),
dependence-aware uncertainty (§3.4), the identifiability–prediction gap (§3.5), and
interest in online monitoring (§3.6). To the best of our reviewed literature, no prior
work reports the specific controlled combination we study on real supercomputer
measurements: a same-hardware measurement-quality ablation, a quantification of the
resulting effective-τ shift, a comparison of that shift against natural fleet variation,
an out-of-sample residual evaluation, and an online-computation boundary. We frame our
contribution as this controlled empirical combination and its quantitative
fleet-level comparison, not as a new principle.
