# Measurement Quality, Thermal Identification, and Residual Predictability in Supercomputer Temperature Measurements

## 1. Abstract

Thermal models of computing systems are routinely identified from a machine's own
temperature and power measurements, yet those measurements differ in how precisely, how
frequently, and with how much spatial detail they are recorded. We study, on the Summit
supercomputer, how such measurement quality affects a first-order thermal model identified
from the measurements, and whether higher measurement quality also makes the unexplained
residual behaviour more predictable. Holding the hardware and workload fixed, we degrade
only the measurements along three axes — temperature quantization to 1 degC, temporal
downsampling from 10 s to 20 s, and spatial aggregation to a single hottest-core proxy —
and re-identify the model in each condition. The identified effective thermal response
time, tau (an identification parameter, not a directly measured physical R.C constant),
shifts substantially: quantization moves the subset median from about 394 s to about 116 s
(0.29x), and downsampling to about 910 s (2.31x). Because an ideal first-order process
would leave tau unchanged under decimation, we read the downsampling result as evidence of
dynamics faster than the model represents, and treat F0 as a reference measurement regime
rather than as physical ground truth. A moving-block bootstrap confirms these shifts are
not an artifact of the uncertainty calculation, and shows that a precise-looking
confidence interval can surround a substantially biased estimate. Across all 116
host-socket units (median tau about 439 s, range 205-2596 s), the quantization-induced
estimate falls below the entire full-quality range observed across those units — whether
that estimate is the 20-unit subset median (about 116 s) or the all-116-unit median (about
142 s). In contrast, higher measurement quality does not materially improve out-of-sample
prediction of the residual (strongest model R^2 <= 0.066, near a permutation null).
Finally, tau is cheaply and causally computable online (about 0.041 ms per window), but a
short-window tau statistic does not separate out-of-sample behaviour from baseline
variability. Applying all five conditions to all 116 units, paired per unit, shows the
shift is not a constant factor, and that spatial aggregation disturbs unit ordering
(Spearman rho about 0.49) far more than quantization or downsampling does (about 0.80).
These are controlled empirical findings — a caution for thermal-model calibration on real
systems — rather than a new model, a monitor, or a physical claim.

## 2. Introduction

### 2.1 Problem

Large computing systems expose continuous measurements of their own temperature and power,
and a common way to reason about their thermal behaviour is to fit a compact thermal model
to those measurements. A first-order model of this kind summarises how temperature
responds to power with a small number of parameters, the most interpretable of which is an
effective thermal response time — informally, how quickly temperature follows a change in
power. Such identified models underpin thermal-aware scheduling, cooling studies, and
digital-twin calibration.

The measurements these models are fit to, however, are not uniform. Temperature is often
reported at coarse resolution (for example, rounded to 1 degC), sampled at a fixed and
sometimes slow rate, and aggregated over many on-chip sensors into one number per socket.
These are properties of the *measurement*, not of the hardware. It is therefore natural to
ask whether the model we identify is a property of the machine, or partly an artifact of
how the machine was measured. This question is rarely examined directly: prior work on
supercomputer thermal identification typically treats coarse measurements as an obstacle to
*overcome* on the way to an accurate model, rather than as a variable whose effect on the
identified parameter is measured.

### 2.2 Why measurement quality matters

If the identified parameter depends on measurement quality, then a calibration performed
under one measurement regime may not transfer to another, and a value that looks precise
may nonetheless be inaccurate. Two failure modes are of practical concern. First, a
calibration pipeline could assign a thermal response time that no comparable sampled unit
actually exhibits, simply because its measurements were coarser. Second, the apparent
tightness of a conventional confidence interval could give false confidence in such a
value. Both concern the *identification* of the model, and neither requires any change in
the underlying hardware. A separate but related question is whether spending effort on
better measurements pays off for *prediction*: if higher-quality measurements sharpen the
identified parameters, do they also make the part of the behaviour the model does not
explain — the residual — more predictable?

### 2.3 Research question

We study one focused question:

> On real supercomputer temperature and power measurements, how does measurement quality —
> temperature quantization, sampling rate, and spatial aggregation — affect identification
> of a first-order thermal model, and does higher measurement quality that sharpens
> parameter identification also make the unexplained residual dynamics more predictable
> out-of-sample?

We answer it with a controlled study on the Summit supercomputer. Because we degrade only
the measurements while holding the hardware and workload fixed, differences we observe are
attributable to measurement quality within this dataset rather than to differing machines
or workloads. We do not use a comparison across different machines to make this claim.

### 2.4 Contributions

We report the following empirical findings. Each is a controlled demonstration on real
measurements; the underlying statistical phenomena (quantization affecting identification,
uncertainty under temporal dependence, and the gap between identifiability and prediction)
are established in prior work, and we position our contribution accordingly.

1. A controlled, same-hardware measurement-quality ablation on real Summit temperature and
   power measurements (five conditions, F0-F4).
2. A quantification of how quantization, sampling, and spatial aggregation shift the
   identified effective tau. On the 20-unit ablation subset the ratios relative to full
   quality are 1.00, 0.29, 2.31, 0.72 and 0.89; across all 116 sampled units (Section 7.8)
   the corresponding per-unit median ratios are 1.00, 0.33, 2.26, 0.69 and 0.82.
3. A demonstration that conventional analytic uncertainty can remain tight around a
   substantially shifted estimate, corroborated by a moving-block bootstrap.
4. A population-scale comparison across 116 sampled host-sockets — our strongest result —
   showing that one measurement artifact can produce an identified tau below the entire
   full-quality range observed across every one of those units.
5. An out-of-sample residual evaluation (five baselines and a permutation null) showing
   that higher measurement quality does not materially improve residual prediction.
6. An operational boundary: tau is causally and cheaply computable online, but the
   evaluated standalone rule does not separate out-of-sample behaviour from baseline
   variability.
7. An extended, paired application of all five conditions to all 116 sampled units, showing
   that the degradation is not a constant per-unit factor, and that spatial aggregation
   disturbs the rank ordering of units far more than quantization or downsampling does.

To the best of our reviewed literature, the specific controlled combination — same
hardware, deliberate measurement-quality degradation, quantified effective-tau shift,
comparison against natural variation across the sampled units, an out-of-sample residual
evaluation, and an online-computation boundary — has not been reported together on real
supercomputer measurements, even though each ingredient is individually known.

## 3. Background and Related Work

Our study builds on four well-established lines of work. We summarise each, note what it
already establishes, and identify the narrow question that, to the best of our reviewed
literature, they do not jointly answer on real supercomputer measurements.

### 3.1 HPC thermal modeling

Thermal behaviour of large computing systems has been modelled from operational
measurements for both design and management. Compact thermal models of supercomputer nodes
have been identified directly from in-production systems, including settings where
temperature is reported at coarse (1 degC) resolution and ambient conditions vary
[P1; P2; P3]. Statistical models of node
temperatures across a supercomputer have also been developed [P4], and recent work
calibrates facility-level thermal-dynamic models on Marconi100
[P5]. Public per-node datasets, including the Summit
per-component power and thermal dataset we use [P13] and the M100 dataset [P12], have
enabled this
work. This establishes that identifying compact thermal models of real HPC nodes — including
under coarse temperature resolution — is prior art; it does not establish how the identified
parameter *changes* when measurement quality is varied in a controlled way.

### 3.2 Thermal system identification

First-order resistor-capacitor and autoregressive-with-exogenous-input (ARX) formulations
are standard for identifying thermal dynamics, and the associated theory distinguishes
structural identifiability (uniqueness under ideal data) from practical identifiability
(recovery under finite, noisy data) [P10; P11]. The estimator we use is standard; what is
not established is its behaviour under
deliberate, controlled measurement degradation across a sampled population of real units.
We keep the model frozen
and unmodified, using it only as a probe of measurement quality.

### 3.3 Measurement quantization and sampling

The effect of quantized observations on system identification is a mature topic: uniform
quantization can be viewed within an errors-in-variables framework and is known to bias
conventional least-squares estimates unless the quantization process is accounted for
[P6; P7; P8]. That
quantization biases identified parameters is therefore an established mechanism, not a new
discovery. What is not established is the size of this effect, and of temporal downsampling
and spatial aggregation, on identified thermal parameters of a real supercomputer, or how
that size compares with natural unit-to-unit variation.

### 3.4 Uncertainty under temporal dependence

For temporally dependent data, independent resampling and analytic interval estimates that
assume independence can understate variability; the moving-block bootstrap resamples
consecutive blocks to preserve dependence and is the standard remedy [P9; and the
independently proposed block bootstrap of Liu and Singh, P17]. That analytic intervals can
be too narrow under dependence is expected,
and we use the block bootstrap as the accepted correction. What that literature does not
address is the specific observation that, for identified thermal parameters under
quantization, a narrow interval can surround a substantially *biased* estimate — a matter
of accuracy, not only interval width.

### 3.5 Physics-informed and residual learning

A recurring theme across dynamical-systems modelling is that identifiability and predictive
accuracy can diverge: parameters that fit calibration data can still yield poor predictions
under new conditions [P10; P11]. Physics-informed and residual-correction
approaches have been applied to thermal and other dynamical systems. This establishes the
general principle that better identification need not imply better prediction; it does not
establish whether, for real supercomputer measurements, improving measurement quality
sharpens identification without materially improving out-of-sample prediction of the
residual. We include a physics-constrained neural residual model only as one of several
baselines; it is not the contribution of this paper.

### 3.6 Online thermal monitoring

Online monitoring, anomaly detection, and change detection for HPC systems is an active
area, including thermal-anomaly detection on Tier-0 systems [P14] and unsupervised anomaly
detection in HPC systems [P15]. This establishes
interest in deriving operational signals from thermal measurements; it does not establish
whether an online effective-tau statistic, computed causally from short windows, functions
as a useful standalone monitor. We report a negative operational boundary for this
statistic.

### 3.7 Research gap

Each ingredient above is individually established: HPC thermal identification (3.1),
standard identification estimators (3.2), quantization-induced bias (3.3),
dependence-aware uncertainty (3.4), the identifiability-prediction gap (3.5), and interest
in online monitoring (3.6). To the best of our reviewed literature, no prior work reports
the specific controlled combination we study on real supercomputer measurements: a
same-hardware measurement-quality ablation, a quantification of the resulting effective-tau
shift, a comparison of that shift against natural variation across sampled units, an
out-of-sample
residual evaluation, and an online-computation boundary. We frame our contribution as this
controlled empirical combination and its quantitative population-level comparison, not as
a new principle.

## 4. Dataset and Experimental Setup

### 4.1 Summit dataset

We use the public per-component power and thermal dataset of the Summit supercomputer
[P13], distributed under CC-BY-4.0. Summit nodes pair IBM POWER9 CPUs with NVIDIA V100
GPUs; we use the archive that records per-node measurements at a nominal 10 s interval
across a set of hosts. The measurement campaign behind this release, and a system-level
characterisation of Summit's power and thermal behaviour, are described by Shin et al.
[P16]; that work characterises the machine's observed behaviour, whereas we use the same
measurements to study how their quality affects an identified model.

One property of the release bears directly on our design. **The published package provides
10 s and 1 min aggregated means; the original 1 Hz measurements from which they were
derived are not part of the public distribution** [P13]. The finest temporal resolution
available to this study is therefore 10 s, and our downsampling condition (F2) necessarily
degrades from 10 s rather than from 1 Hz. Our records are also interval means rather than
instantaneous samples, which bounds the fast dynamics any analysis of this archive can
resolve (Sections 7.1 and 9). We state this explicitly because it is a property of the
public data rather than a choice: a 1 Hz analysis was not available to us.

Working with a single machine lets us degrade measurement quality on fixed hardware; the
resulting limits on external validity are discussed in Section 9. The M100 dataset [P12]
is used only as contextual background and is not used for any causal claim (its
measurement configuration and hardware differ, so a Summit-vs-M100 comparison would be
confounded).

### 4.2 Temperature and power measurements

Each measurement record provides, per CPU socket, a temperature and a power value in the
same row, so temperature and power are co-located in time without a separate join. For each
socket we use the socket-mean core temperature as the temperature signal and the socket
power as the power signal. We analyse CPU sockets only; GPU measurements are outside the
scope of this study.

### 4.3 Unit definition

The unit of analysis is a single CPU socket of a single host. The archive we use covers 58
hosts with 2 sockets each, giving **116 sampled host-sockets**. We emphasise that this is
a sample, not the whole machine: Summit comprises 4,626 compute nodes, so the 116 units
are a small subset of the installed system, and every population statistic reported below
describes this sample rather than Summit as a whole. Wherever we compare a
measurement-induced shift against "natural variation", the comparison is against the
variation observed across these 116 sampled units.

The controlled ablation and the bootstrap analyses (Sections 5, 7.1-7.4) use a fixed,
deterministic subset of 10 coverage-ranked hosts (20 units); the population analyses
(Sections 7.5-7.6) use all 116 units; and the extended ablation of Section 7.8 applies all
five measurement-quality conditions to all 116 units. Units are never mixed across the
train/test boundary in any evaluation.

### 4.4 Preprocessing

We derive a cleaned representation from the raw archive without modifying the raw files.
Numeric measurement columns are unified to a common floating-point type. A small fraction of
records carry duplicate timestamps whose payloads differ; rather than dropping them, we
resolve each duplicated (unit, timestamp) group by mean aggregation of its numeric values,
which is order-independent and consistent with the dataset's own per-interval mean
semantics. We do not interpolate missing values. Long interruptions in the measurement
stream (collection gaps) segment each unit's series into contiguous segments; no model pair
or evaluation window is ever formed across a gap. From the raw archive of about 73.9 million
rows this yields about 67.3 million cleaned rows across the sampled hosts [source:
artifacts/manifests/derived_manifest.json]. The raw data hash is recorded and
unchanged (Section 10).

### 4.5 Measurement-quality conditions (F0-F4)

We define five measurement-quality conditions, applied identically across units. F0 is the
full-quality reference: socket-mean temperature at floating-point resolution, 10 s sampling.
F1 (quantization) rounds temperature to the nearest 1 degC, keeping 10 s sampling. F2
(downsampling) decimates the series from 10 s to 20 s by keeping every second sample within
a segment, with no interpolation. F3 (spatial aggregation) replaces the socket-mean
temperature with a per-timestamp hottest-core value (a Tjmax proxy); the archive does not
provide fixed per-physical-core streams, so this is a precisely defined single-sensor proxy
rather than a fixed-core measurement, and we describe it as such throughout. F4 combines the
three degradations. Only the measurements change between conditions; the hardware, the
workload, the model, and the estimation procedure are held fixed. The overall design is
illustrated in Figure 1, and the conditions are summarised in Table 1.

## 5. Thermal Model and Identification

### 5.1 First-order ARX model

We use a first-order autoregressive-with-exogenous-input model relating the next temperature
sample to the current temperature and power:

    T[n+1] = alpha * T[n] + beta * P[n] + gamma,

where T is temperature, P is power, and (alpha, beta, gamma) are the model coefficients.
The model is fit on contiguous segments only; a consecutive pair (T[n], T[n+1]) is never
formed across a collection gap. The model and its estimation are frozen across all
conditions and units, so any difference in the identified parameters is attributable to the
measurement quality, not to a change in the model.

### 5.2 Effective thermal response time tau

From the autoregressive coefficient we report an effective thermal response time,

    tau = -dt / ln(alpha),

where dt is the sampling interval of the condition (10 s for F0/F1/F3, 20 s for F2/F4). We
emphasise that tau is an *identified model parameter* summarising how quickly temperature
follows a change in power under the fitted first-order model; it is not a directly measured
physical resistor-capacitor time constant, and we do not interpret it as one. Because the
sampling interval enters only through this conversion, reporting tau (rather than alpha)
places the F0/F1/F3 and F2/F4 conditions on a comparable time scale.

### 5.3 OLS estimation

The coefficients are estimated by ordinary least squares over all consecutive within-segment
pairs of a unit, regressing T[n+1] on the design [T[n], P[n], 1]. We retain a fit as a valid
effective time constant only when the autoregressive coefficient corresponds to a stable
first-order response (0 < alpha < 1).

### 5.4 Analytic uncertainty

We summarise analytic parameter uncertainty using the ordinary-least-squares covariance and
the delta method: the standard error of alpha is obtained from the OLS covariance, and the
standard error of tau follows by propagating alpha through tau = -dt/ln(alpha). From these
we report an analytic coefficient of variation and an analytic confidence interval for tau.
As is well known for temporally dependent data (Section 3.4), this analytic interval assumes
independence and can understate variability; we therefore also compute a bootstrap interval.

### 5.5 Moving-block bootstrap

To quantify uncertainty in a way that respects temporal dependence, we use a moving-block
bootstrap over consecutive model pairs. Blocks of consecutive pairs are resampled within
contiguous segments only, so no block crosses a collection gap. The block length is fixed at
approximately one full-quality effective response time (about 640 s), which corresponds to
64 pairs at 10 s and 32 pairs at 20 s; fixing the block length in time avoids any
circular dependence on the per-unit estimate. We draw B = 500 resamples with a fixed random
seed, refit the model on each resample, and retain resamples with a stable coefficient
(0 < alpha < 1). From the resulting distribution we report the bootstrap median tau, a
bootstrap coefficient of variation, and a bootstrap confidence interval. We report the
analytic and bootstrap estimates and intervals separately and do not treat the bootstrap as
correcting any bias in the point estimate; it quantifies uncertainty around it.

## 6. Residual Prediction Evaluation

### 6.1 Residual definition

The residual is the part of the next-step temperature that the fitted first-order model does
not explain,

    r[n] = T[n+1] - ( alpha * T[n] + beta * P[n] + gamma ),

computed within segments. We ask whether this residual carries information that a predictor
can recover out-of-sample, and whether higher measurement quality changes the answer.

### 6.2 Prediction baselines

We evaluate five predictors of the residual, from simple to flexible: (i) a persistence
reference, (ii) a linear model, (iii) a gradient-boosted tree ensemble, (iv) a small
recurrent (LSTM) model, and (v) a small physics-constrained neural model. Predictors use
only quantities available from the measurements (for example power, change in power,
temperature, and short lags). The gradient-boosted ensemble is implemented with a
histogram-based gradient-boosting regressor, as an equivalent tree-ensemble stand-in where a
separate boosting library was unavailable; this substitution is documented for
reproducibility. The physics-constrained neural model is included only as one baseline to
test whether a physics-anchored network recovers residual structure the simpler models miss;
it is not a contribution of this paper.

### 6.3 Chronological out-of-sample protocol

All residual evaluation is strictly out-of-sample and chronological. Models are trained on
earlier data and evaluated on later, unseen data, with the split respecting the natural
collection blocks; observations are never shuffled across time, and no data crosses a
collection gap. Where predictors are pooled across units, the train/test division is applied
so that evaluation reflects generalisation rather than memorisation. We report out-of-sample
coefficient of determination (R^2) as the primary predictive metric.

### 6.4 Permutation null

Because small positive R^2 values can arise by chance, we accompany the residual evaluation
with a permutation null: the residual targets are permuted to break their temporal relation
to the predictors, and the evaluation is repeated to obtain a null reference (we report its
upper tail). A predictive result is only treated as meaningful if it exceeds this null
reference; we use this to avoid over-interpreting small positive values.

## 7. Results

### 7.1 Measurement quality changes the identified effective thermal response time

We first compare the identified effective thermal response time across the five
measurement-quality conditions on the same hardware and workload (Table 2, Figure 2). At
full quality (F0) the median over the 20-unit ablation subset is about 394 s. Quantizing
temperature to 1 degC (F1)
lowers it to about 116 s, a factor of about 0.29 relative to F0; downsampling from 10 s to
20 s (F2) raises it to about 910 s, a factor of about 2.31; the hottest-core proxy (F3)
gives about 283 s (about 0.72x); and the combined degradation (F4) gives about 352 s
(about 0.89x). Because only the measurement quality differs between conditions, these are
changes in the identified effective parameter, not changes in the physical thermal
behaviour of the hardware. The magnitude of the change is substantial: the identified
effective response time varies by roughly a factor of eight across the conditions applied
to the same units.

The downsampled condition deserves specific comment, because it is more informative than a
simple loss of resolution. For an ideal first-order process the effective response time is
*invariant* to the sampling interval: tau = -dt/ln(alpha) is exactly the
reparameterisation that removes dt, so halving the sampling rate should leave tau
unchanged and only coarsen its uncertainty. Observing tau move from about 394 s to about
910 s under 10 s to 20 s decimation is therefore not what a first-order description
predicts. The most economical reading is that the temperature signal contains dynamics
faster than the model represents — at minimum a second, shorter thermal mode, together
with high-frequency measurement noise — so that the single fitted coefficient at 10 s is
pulled toward the fast component, while decimation suppresses that component and shifts
the same coefficient toward the slower one. Both estimates then describe the same hardware
summarised over different effective bandwidths. We do not attempt to separate these
contributions here, and we do not claim to have identified the fast mode. The consequence
for the rest of the paper is one of interpretation rather than arithmetic: **F0 is best
read as a reference measurement regime, not as unquestionable physical ground truth.**
Comparisons throughout are made relative to F0 under a fixed identification convention,
which is what the artifact-versus-heterogeneity comparison of Section 7.6 requires; they
are not claims about a true underlying time constant.

### 7.2 A moving-block bootstrap confirms the shifts are not uncertainty artifacts

To check that these shifts are properties of the identified model rather than of the
analytic uncertainty calculation, we repeat the identification under a moving-block
bootstrap (500 resamples, a fixed block horizon of about 640 s, blocks never crossing a
collection gap; Section 5.5). The bootstrap median effective response times are about 394 s
(F0), 116 s (F1), 909 s (F2), 283 s (F3), and 352 s (F4), and no resample produced an
unstable fit (0% invalid). The bootstrap medians match the corresponding point estimates
essentially exactly (Table 2), so the measurement-quality-induced shifts persist under
dependence-aware resampling. We do not interpret the bootstrap as correcting the estimates
or as establishing any physical mechanism; it quantifies uncertainty around the same
estimates.

### 7.3 Precise uncertainty can coexist with a shifted estimate

Comparing the two uncertainty summaries (Table 2, Figure 2), the analytic delta-method
confidence intervals are systematically narrower than the block-bootstrap intervals: about
38.7 s versus 79.0 s at F0, 4.1 s versus 8.3 s at F1, 178.7 s versus 254.2 s at F2, 10.7 s
versus 19.0 s at F3, and 15.4 s versus 23.3 s at F4. This ordering is consistent with
temporal dependence inflating uncertainty beyond what the independence-based analytic
formula reports. Beyond interval width, we note that the quantized condition F1 has the
tightest uncertainty of any condition while also producing the most strongly shifted
effective response time (about 0.29x F0). In this setting, precision does not imply
accuracy: a narrow interval accompanies a substantially shifted estimate. We present this
as an empirical demonstration on these measurements, not as a new statistical principle.

### 7.4 Higher measurement quality does not materially improve residual prediction

We next ask whether the part of the next-step temperature that the first-order model does
not explain — the residual — can be predicted out-of-sample, and whether measurement
quality changes the answer (Table 3, Figure 3). Across all conditions the residual is only
weakly predictable. The linear baseline is near zero at full quality (about 0.001), and the
strongest predictor, the gradient-boosted tree ensemble, reaches an out-of-sample R^2 of at
most about 0.066 (at F4), with values of about 0.034 (F0), 0.055 (F1), 0.006 (F2), and
0.046 (F3); the permutation-null upper tails are at or below zero in every condition. The
values do not increase with measurement quality — indeed several degraded conditions match
or exceed the full-quality value. We therefore find that higher measurement quality did not
materially improve out-of-sample residual prediction. The physics-constrained neural model
is one of the five baselines evaluated here and did not materially improve prediction over
the simpler models; it is not a contribution of this paper.

### 7.5 Variation across the sampled units establishes the natural range of effective tau

We estimate the effective response time at full quality for every one of the 116 sampled
host-sockets (Table 4, Figure 4). All 116 of 116 units yield valid estimates. The
sampled-population median is about 439 s (bootstrap median also about 439 s), the mean
about 552 s, and the standard
deviation about 365 s; the interquartile range is about 376-588 s, the 5th and 95th
percentiles about 275 s and 1200 s, and the minimum and maximum about 205 s and 2596 s.
Considering the two sockets of a host (58 paired hosts), their effective response times are
correlated (about 0.789), with a median absolute difference of about 102.5 s and a median
relative difference of about 24.2%; we report this similarity descriptively and do not
attribute it to any cause. The 20-unit subset used in the ablation has a median of about
394 s, close to the median of about 440 s over the remaining 96 units and within the sampled
interquartile range, so the subset is representative of the sampled population.

### 7.6 Measurement artifact versus natural heterogeneity across sampled units

Placing the measurement-quality effect against this natural variation is our strongest
observation (Table 4, Figure 5). The quantized estimate of about 116 s lies below the
entire full-quality range observed across the sampled units: it is below the sampled
minimum of about 205 s and well below the 5th percentile of about 275 s. In other words,
quantizing the temperature measurements produces an identified effective response time
that no full-quality sampled unit exhibits.

By contrast, the downsampled estimate of about 910 s falls within the sampled units'
natural upper range (below the 95th percentile of about 1200 s). The overall swing induced
by measurement quality, from the quantized 0.29x to the downsampled 2.31x, spans about a
factor of eight, compared with a natural spread across sampled units (95th over 5th
percentile) of about 4.4x. A measurement artifact can thus produce an identified effective
thermal parameter outside the range observed across any full-quality sampled unit. This is
an empirical comparison on these measurements and does not establish that every quantized
deployment will behave this way.

This comparison does not depend on the choice of ablation subset. The 116 s figure is the
median over the 20-unit subset; applying the same quantization to all 116 units
(Section 7.8) gives a median of about 142 s, which also lies below the full-quality
minimum of about 205 s. The margin is narrower at the larger sample, and we report both
values rather than only the more favourable one.

### 7.7 Online computation is feasible, but tau is not a useful standalone monitor here

Finally, we evaluate the effective response time as a causal, online statistic computed from
short rolling windows (Table 4, Figure 6). The computation is inexpensive: about 0.041 ms
per window, comfortably faster than the 10 s measurement interval, and it uses no future
data. Treating the first half of each unit's series as a baseline and monitoring the second
half, the out-of-sample alert rate (about 0.102) is essentially equal to the baseline
alert rate obtained under the same rule on the baseline period (about 0.103), a difference
of about +0.0004; about 51% of units have an out-of-sample rate above their baseline, close
to chance. The short-window estimate is itself highly variable (median relative spread about
0.62), and its deviations show essentially no correlation with power-regime change
(about 0.004). The alert rates remain at approximately baseline level under F0, F1, and F2.
We conclude that the effective response time is computable causally and cheaply enough for
real-time processing, but the evaluated short-window statistic does not provide evidence of
useful standalone monitoring: it is computable, but not, on this evidence, useful as a
monitor. Summit contains no labeled anomaly or failure events, so this is an unsupervised
stability and change-detection evaluation rather than a failure-detection benchmark.

### 7.8 Extending the ablation to all 116 sampled units: paired per-unit effects

The ablation of Sections 7.1-7.4 reports condition-level medians over a 20-unit subset. To
check that those medians are not an artifact of the subset, and to examine what the
degradations do to *individual* units rather than to a summary statistic, we applied all
five conditions to all 116 sampled host-sockets, reusing the same condition definitions,
segmentation, and estimator without modification. All 116 units yield a valid estimate in
every condition, so every comparison below is exactly paired. The full-quality median over
all 116 units is about 439 s, reproducing the independently computed value of Section 7.5.

Two sets of condition medians therefore appear in this paper and should not be conflated.
Sections 7.1-7.4 report the 20-unit ablation subset (F0 about 394 s, F1 about 116 s); this
section reports all 116 units (F0 about 439 s, F1 about 142 s). Both are correct for their
respective samples, and the subset is representative of the wider population (Section 7.5).
A condition median quoted without qualification elsewhere in the text refers to the 20-unit
subset, which is the canonical ablation. Two things become visible that the medians conceal
(Table 5).

**The degradation is not a constant factor.** Under quantization the per-unit ratio to
full quality has a median of about 0.33 but a 5th-95th percentile range of about
0.22-0.47; under the hottest-core proxy the range is wider still, about 0.22-1.00 around a
median of about 0.69. The same measurement change therefore moves different units by
materially different amounts, so the effect cannot be removed by applying a single global
correction factor to a coarsely measured population.

**Spatial aggregation disturbs the ordering of units; quantization and downsampling
largely preserve it.** Ranking units by identified tau and comparing each condition
against full quality, Spearman's rho is about 0.80 (95% CI 0.71-0.86) for quantization and
about 0.82 (0.73-0.88) for downsampling, but falls to about 0.49 (0.32-0.63) for the
hottest-core proxy and about 0.50 (0.33-0.64) for the combined condition. Under the two
temporally defined degradations a coarsely measured population still ranks its units
roughly as the reference regime does; under spatial aggregation that correspondence is
substantially weaker. We report this as an observed property of these measurements and do
not attribute it to a mechanism.

**A caution on measuring dispersion in tau.** It is tempting to read the narrowing of the
tau distribution under quantization (interquartile range about 0.37 times the full-quality
value) as measurement-induced homogenisation of the population. That reading does not
survive checking. Because tau = -dt/ln(alpha) is strongly nonlinear as alpha approaches
one, dispersion in tau can move for purely algebraic reasons. Recomputing the same
statistic on the underlying coefficient alpha reverses the direction for quantization
(interquartile ratio about 3.3, i.e. wider rather than narrower), and the scale-free
coefficient of variation of (1 - alpha) is essentially unchanged (about 0.33 versus 0.37).
Only the hottest-core proxy narrows in both parameterisations. **We therefore make no
claim of measurement-induced homogenisation**, and we note the more general point that
population spread reported in tau should be verified in alpha, or restricted to rank
statistics, which are invariant to any monotone reparameterisation.

This extended ablation is reported separately from the canonical 20-unit analysis; it adds
unit coverage and paired per-unit statistics, and it does not alter any previously
reported value.

## 8. Discussion

### 8.1 Main finding

The central result of this study is that measurement quality changes the identified
effective thermal response time substantially, even when the hardware and the workload are
held fixed. Applying three measurement degradations to the same units moves the identified
effective response time from about 394 s at full quality to about 116 s under 1 degC
temperature quantization (a factor of about 0.29), to about 910 s under 20 s downsampling
(a factor of about 2.31), to about 283 s under the hottest-core spatial proxy, and to about
352 s under the combined degradation. We stress that this is a change in an identified model
parameter, not a change in the physical thermal behaviour of the hardware: the same
hardware, running the same work, is simply measured differently, and the fitted first-order
model reports a different effective response time. The effective response time is therefore
best read as a joint property of the machine and of how the machine was measured.

### 8.2 Why the result matters

That quantization can bias an estimated parameter is not itself new (Section 3.3); the
practically important observation here is about the *size* of that effect relative to real
variation. Across the 116 sampled host-sockets at full quality, the identified effective
response time ranges from
about 205 s to about 2596 s, with a 5th percentile of about 275 s. The quantized estimate of
about 116 s lies below this entire observed range. A measurement choice can thus produce an
identified parameter that no full-quality sampled unit exhibits — that is, an artifact
of measurement can be larger than the natural variation between units. We report this as an
empirical result on this dataset and do not extrapolate it to every high-performance
computing system or every measurement pipeline.

### 8.3 Precision versus accuracy

The uncertainty analysis makes a related point. The analytic delta-method intervals are
consistently narrower than the dependence-aware block-bootstrap intervals, which is expected
when temporal correlation is present (Section 3.4). More notably, the quantized condition —
whose estimate is the most strongly shifted relative to full quality — also has the tightest
uncertainty of any condition. A narrow interval describes statistical precision around the
fitted estimate under the assumed model; it does not establish that the estimate is accurate
relative to the full-quality reference. This distinction between precision and accuracy is a
standard one; our contribution is to demonstrate it concretely in a real high-performance
computing setting, where a confident-looking interval accompanies a substantially shifted
estimate. The bootstrap does not remove the measurement-induced shift — the bootstrap
medians reproduce the point estimates — it only confirms that the shift persists under
dependence-aware resampling.

### 8.4 Identification versus prediction

The residual evaluation separates two questions that are often treated together: whether a
model parameter can be identified, and whether the remaining dynamics are predictably
structured out of sample. Better measurement quality changes and, by the tightness of its
intervals, sharpens identification; it does not materially improve out-of-sample prediction
of the residual. The linear baseline is near zero at full quality, and the strongest
predictor reaches an out-of-sample R^2 of at most about 0.066, close to the permutation
null, with several degraded conditions matching or exceeding the full-quality value. We do
not conclude that the residual contains no structure, nor that it is exactly zero; the
strongest model does extract a small, mostly null-level signal. The conservative reading is
that, under the evaluated models and conditions, the residual was not materially predictable
out of sample, and improving measurement quality did not change that.

### 8.5 Why the sampled-population result strengthens the study

The sampled-population analysis provides the context needed to interpret the controlled
ablation. All
116 of 116 units yield valid full-quality estimates, with a median of about 439 s and a
natural range of about 205-2596 s (5th and 95th percentiles about 275 s and 1200 s). Against
this backdrop the ablation's 20-unit subset is representative: its median of about 394 s is
close to the about 440 s of the remaining 96 units and sits within the sampled
interquartile range. The sampled population also lets us judge the artifact against real
heterogeneity, which is the
basis for the observation in Section 8.2. We further note that the two sockets of a host tend
to have similar identified response times (correlation about 0.789, median relative
difference about 24.2%); we report this as a descriptive property only and do not attribute
it to cooling, position, workload, or any other cause.

### 8.6 Operational boundary

The effective response time can be computed causally from short rolling windows at negligible
cost (about 0.041 ms per window), which makes online computation straightforward. However,
computational feasibility does not by itself make the quantity a useful monitoring signal. In
our evaluation the out-of-sample alert rate (about 0.102) is essentially equal to the
baseline alert rate produced by the same rule on the baseline period (about 0.103), the
short-window estimate is highly variable (median relative spread about 0.62), and its
fluctuations are essentially uncorrelated with power-regime change. We therefore distinguish
computable from useful: the evaluated short-window statistic is computable online but does
not, on this evidence, provide a useful standalone monitoring signal. Summit contains no
labeled anomaly or failure events, so this is an unsupervised stability and change-detection
evaluation rather than a validated monitoring result.

### 8.7 What the study contributes

We position this work conservatively as a controlled empirical limits study: it shows how
measurement quality can alter identified thermal parameters on real high-performance
computing measurements, how the resulting artifact compares with natural variation across
sampled units,
and how parameter identification can remain disconnected from residual predictability. We
explicitly concede that the underlying ideas are established: identifying thermal models of
high-performance computing nodes, the biasing effect of quantization on system
identification, dependence-aware bootstrap uncertainty, and the divergence between
identifiability and prediction are all prior art (Section 3). We do not present any of these
as newly invented. The contribution is the controlled combination on real measurements and,
in particular, the comparison of the measurement-induced shift against natural variation
across the sampled units.

## 9. Threats to Validity and Limitations

1. **Effective parameter.** The reported tau is an identified parameter of the fitted
   first-order model, not a direct physical resistor-capacitor measurement, and we do not
   interpret it as a hardware constant.
2. **Single-system external validity.** The controlled ablation is performed on Summit
   (POWER9 + V100). We do not claim the specific magnitudes generalise to other
   high-performance computing systems or architectures.
3. **M100 comparison.** M100 is used only as background context; a Summit-vs-M100 comparison
   would be confounded by machine and architecture differences, and we make no causal
   cross-machine claim.
4. **Tjmax proxy.** Condition F3 uses a per-timestamp hottest-core value as an approximation
   of a single-core temperature stream, because the archive does not provide fixed
   per-physical-core streams; results for F3/F4 should be read with this proxy in mind.
5. **Residual is not exactly zero.** The strongest model reaches an out-of-sample R^2 of up
   to about 0.066; we therefore describe the residual as not materially predictable in this
   evaluation, and avoid any claim that it is unlearnable or exactly zero.
6. **No labeled anomaly events.** The online evaluation (Section 7.7) is a
   stability/change-detection assessment; it is not a validated failure- or
   anomaly-prediction benchmark.
7. **No deployed digital twin.** The calibration implication is argued from the observed
   parameter shift; it was not demonstrated within a deployed digital-twin system.
8. **Socket and host differences.** The socket correlation and relative differences are
   descriptive; we did not identify their physical causes.
9. **Measurement mechanism.** Errors-in-variables attenuation and temporal aliasing are
   plausible explanations for the observed shifts, but we did not causally isolate them; they
   are not established findings of this study.
10. **Temporal resolution.** The underlying measurements are 10 s means rather than raw
    1 Hz measurements, which bounds the temporal detail available to the analysis.
11. **Spatial aggregation.** The meaning of spatial aggregation depends on the streams
    available in this archive and should not be generalised beyond the evaluated conditions.
12. **Bootstrap scope.** The moving-block bootstrap addresses temporal dependence in
    uncertainty estimation; it does not correct measurement-induced parameter bias.

13. **F0 is a reference regime, not ground truth.** The downsampling result (Section
    7.1) indicates dynamics faster than the first-order model represents. All
    comparisons are therefore relative to a fixed identification convention at F0; we
    do not claim to recover a true underlying time constant, and we did not isolate the
    fast mode.
14. **Temporal resolution is bounded by the public release.** The distributed archive
    provides 10 s and 1 min means only; the original 1 Hz measurements are not public
    (Section 4.1). Our records are interval means, so dynamics faster than 10 s cannot
    be resolved by any analysis of this archive.
15. **116 units are a sample, not the machine.** All population statistics describe the
    116 sampled host-sockets, not Summit's 4,626 nodes. A larger sample could widen the
    observed range and reduce the margin by which the quantized estimate falls below
    it.
16. **Rank and dispersion results are descriptive.** The reduced rank agreement under
    spatial aggregation (Section 7.8) is an observed property of these measurements; we
    did not identify its mechanism. We make no claim of measurement-induced
    homogenisation, because the apparent narrowing in tau does not survive re-checking
    in alpha.

**Reproducibility and artifacts.** The analysis is deterministic and traceable. The raw
measurements are used read-only, with a recorded content hash (SHA-256 prefix
9898170b...996e); the identification model and its estimation are frozen and unchanged across
all conditions; random procedures use fixed seeds; and the tables and figures are
regenerated from the locked result artifacts by a single analysis pipeline. Where a standard
gradient-boosting library was unavailable, a histogram-based gradient-boosting regressor was
used as an equivalent stand-in, and this substitution is documented.

## 10. Practical Implications

The findings suggest a small number of concrete practices for building thermal models from a
machine's own temperature and power measurements.

- **Measurement provisioning.** Temperature resolution and sampling rate should be treated
  as modelling choices, not merely data-engineering details, because they can change the
  identified parameter.
- **Calibration.** A fitted thermal parameter should be interpreted together with the
  measurement conditions under which it was identified, rather than as a
  measurement-independent property of the hardware.
- **Cross-unit comparisons.** Comparing fitted thermal parameters across units requires
  consistent measurement quality, because a measurement artifact can be larger than the
  natural variation between units.
- **Uncertainty reporting.** A narrow conventional confidence interval should not be read as
  evidence that an estimate is accurate; precision and accuracy are distinct here.
- **Real-time use.** Online computation of the effective response time is inexpensive, but
  computational feasibility alone does not validate it as an operational health indicator.

These are cautions for practice; they are not a proposed framework, and we make no claim of
deployment readiness, improved cooling, energy optimisation, or failure prediction.

## 11. Conclusion

We studied how measurement quality affects a first-order thermal model identified from a
supercomputer's own temperature and power measurements. Four findings summarise the work.
First, on the same hardware and workload, measurement quality materially changes the
identified effective thermal response time, from about 394 s at full quality to about 116 s
under temperature quantization and about 910 s under temporal downsampling. Second, a
moving-block bootstrap confirms these shifts are not artifacts of the uncertainty
calculation, while the analytic intervals can be too narrow and, in the quantized case,
tight around a strongly shifted estimate. Third, the quantization artifact can fall outside
the natural variation observed across the 116 sampled host-sockets, yet higher measurement
quality
does not materially improve out-of-sample prediction of the unexplained residual. Fourth,
the effective response time is cheap to compute online but is not, in this evaluation, a
validated standalone monitoring signal. Taken together, these are an empirical limits and
caution study about identifying thermal models from imperfect measurements — not a new
identification algorithm, a monitoring system, a physics-informed learning method, or a
physical thermal model.

## References

All records below were resolved against Crossref, DataCite, or the publisher / preprint
record of the work itself. No entry carries an unverified field.

- **[P1]** Diversi, R., Bartolini, A., & Benini, L. (2020). Thermal Model Identification of
  Computing Nodes in High-Performance Computing Systems. *IEEE Transactions on Industrial
  Electronics*, 67(9), 7778-7788. DOI 10.1109/TIE.2019.2945277.
- **[P2]** Diversi, R., Bartolini, A., Beneventi, F., & Benini, L. (2016). Thermal model
  identification of supercomputing nodes in production environment. In *IECON 2016 - 42nd
  Annual Conference of the IEEE Industrial Electronics Society*, 4838-4844. IEEE Xplore
  document 7793664.
- **[P3]** Pittino, F., Diversi, R., Benini, L., & Bartolini, A. (2020). Robust
  Identification of Thermal Models for In-Production High-Performance-Computing Clusters
  With Machine-Learning-Based Data Selection. *IEEE Transactions on Computer-Aided Design of
  Integrated Circuits and Systems*, 39, 2042-2054. DOI 10.1109/TCAD.2019.2950378. Preprint:
  arXiv:1810.01865.
- **[P4]** Storlie, C. B., Reich, B. J., Rust, W. N., Ticknor, L. O., Bonnie, A. M.,
  Montoya, A. J., & Michalak, S. E. (2015). Spatiotemporal Modeling of Node Temperatures in
  Supercomputers. arXiv:1505.06275 [stat.AP].
- **[P5]** Ngwerume, C., Tong, L., Ten, C.-W., & Hu, Y. (2026). A Configurable
  Thermal-Dynamic Model for AI Data Center Cooling Load Simulation. arXiv:2607.28962.
- **[P6]** Wang, L. Y., Yin, G. G., Zhang, J.-F., & Zhao, Y. (2010). *System Identification
  with Quantized Observations*. Systems & Control: Foundations & Applications. Birkhauser
  Boston. ISBN 978-0-8176-4955-5.
- **[P7]** Wang, L. Y., & Yin, G. G. (2007). Asymptotically efficient parameter estimation
  using quantized output observations. *Automatica*, 43(7), 1178-1191.
  DOI 10.1016/j.automatica.2006.12.030.
- **[P8]** Moschitta, A., Schoukens, J., & Carbone, P. (2015). Parametric System
  Identification Using Quantized Data. *IEEE Transactions on Instrumentation and
  Measurement*, 64(8), 2312-2322. DOI 10.1109/TIM.2015.2390833. Preprint: arXiv:1804.10015.
- **[P9]** Kunsch, H. R. (1989). The Jackknife and the Bootstrap for General Stationary
  Observations. *The Annals of Statistics*, 17(3), 1217-1241. DOI 10.1214/aos/1176347265.
- **[P10]** Preston, S. P., Wilkinson, R. D., Clayton, R. H., Chappell, M. J., &
  Mirams, G. R. (2025). Think before you fit: parameter identifiability, sensitivity and
  uncertainty in systems biology models. arXiv:2508.18853 [stat.ME].
- **[P11]** Liu, Y., Suh, K., Maini, P. K., Cohen, D. J., & Baker, R. E. (2024). Parameter
  identifiability and model selection for partial differential equation models of cell
  invasion. *Journal of the Royal Society Interface*, 21(212). DOI 10.1098/rsif.2023.0607.
- **[P12]** Borghesi, A., Di Santi, C., Molan, M., Seyedkazemi Ardebili, M., Mauri, A.,
  Guarrasi, M., Galetti, D., Cestari, M., Barchi, F., Benini, L., Beneventi, F., &
  Bartolini, A. (2023). M100 ExaData: a data collection campaign on the CINECA's Marconi100
  Tier-0 supercomputer. *Scientific Data*, 10, 288. DOI 10.1038/s41597-023-02174-3. Used
  only as context.
- **[P13]** Shin, W., Ellis, J. A., Karimi, A. M., Oles, V., Dash, S., & Wang, F. (2022).
  *Long Term Per-Component Power and Thermal Measurements of the OLCF Summit System*
  [Data set]. Oak Ridge National Laboratory. DOI 10.13139/OLCF/1861393. CC-BY-4.0. Primary
  dataset.
- **[P14]** Seyedkazemi Ardebili, M., Bartolini, A., Acquaviva, A., & Benini, L. (2022).
  Rule-Based Thermal Anomaly Detection for Tier-0 HPC Systems. In *High Performance
  Computing. ISC High Performance 2022 International Workshops*, Lecture Notes in Computer
  Science, 262-276. Springer. DOI 10.1007/978-3-031-23220-6_18.
- **[P15]** Molan, M., Borghesi, A., Cesarini, D., Benini, L., & Bartolini, A. (2023).
  RUAD: Unsupervised anomaly detection in HPC systems. *Future Generation Computer Systems*,
  141, 542-554. DOI 10.1016/j.future.2022.12.001.
- **[P16]** Shin, W., Oles, V., Karimi, A. M., Ellis, J. A., & Wang, F. (2021). Revealing
  power, energy and thermal dynamics of a 200PF pre-exascale supercomputer. In *Proceedings
  of the International Conference for High Performance Computing, Networking, Storage and
  Analysis (SC '21)*, 1-14. DOI 10.1145/3458817.3476188.
- **[P17]** Liu, R. Y., & Singh, K. (1992). Moving blocks jackknife and bootstrap capture
  weak convergence. In R. LePage & L. Billard (Eds.), *Exploring the Limits of Bootstrap*,
  225-248. Wiley, New York.
