# 2. Introduction (draft v1)

## 2.1 Problem

Large computing systems expose continuous measurements of their own temperature and
power, and a common way to reason about their thermal behaviour is to fit a compact
thermal model to those measurements. A first-order model of this kind summarises how
temperature responds to power with a small number of parameters, the most interpretable
of which is an effective thermal response time — informally, how quickly temperature
follows a change in power. Such identified models underpin thermal-aware scheduling,
cooling studies, and digital-twin calibration.

The measurements these models are fit to, however, are not uniform. Temperature is often
reported at coarse resolution (for example, rounded to 1 °C), sampled at a fixed and
sometimes slow rate, and aggregated over many on-chip sensors into one number per socket.
These are properties of the *measurement*, not of the hardware. It is therefore natural
to ask whether the model we identify is a property of the machine, or partly an artifact
of how the machine was measured. This question is rarely examined directly: prior work on
supercomputer thermal identification typically treats coarse measurements as an obstacle
to *overcome* on the way to an accurate model, rather than as a variable whose effect on
the identified parameter is measured.

## 2.2 Why measurement quality matters

If the identified parameter depends on measurement quality, then a calibration performed
under one measurement regime may not transfer to another, and a value that looks precise
may nonetheless be inaccurate. Two failure modes are of practical concern. First, a
calibration pipeline could assign a thermal response time that no comparable unit in the
fleet actually exhibits, simply because its measurements were coarser. Second, the
apparent tightness of a conventional confidence interval could give false confidence in
such a value. Both concern the *identification* of the model, and neither requires any
change in the underlying hardware. A separate but related question is whether spending
effort on better measurements pays off for *prediction*: if higher-quality measurements
sharpen the identified parameters, do they also make the part of the behaviour the model
does not explain — the residual — more predictable?

## 2.3 Research question

We study one focused question:

> On real supercomputer temperature and power measurements, how does measurement quality
> — temperature quantization, sampling rate, and spatial aggregation — affect
> identification of a first-order thermal model, and does higher measurement quality that
> sharpens parameter identification also make the unexplained residual dynamics more
> predictable out-of-sample?

We answer it with a controlled study on the Summit supercomputer. Because we degrade only
the measurements while holding the hardware and workload fixed, differences we observe are
attributable to measurement quality within this dataset rather than to differing machines
or workloads. We do not use a comparison across different machines to make this claim.

## 2.4 Contributions

We report the following empirical findings. Each is a controlled demonstration on real
measurements; the underlying statistical phenomena (quantization affecting identification,
uncertainty under temporal dependence, and the gap between identifiability and prediction)
are established in prior work, and we position our contribution accordingly.

1. A controlled, same-hardware measurement-quality ablation on real Summit temperature and
   power measurements (five conditions, F0–F4).
2. A quantification of how quantization, sampling, and spatial aggregation shift the
   identified effective τ (ratios 1.00, 0.29, 2.31, 0.72, 0.89 relative to full quality).
3. A demonstration that conventional analytic uncertainty can remain tight around a
   substantially shifted estimate, corroborated by a moving-block bootstrap.
4. A fleet-scale comparison — our strongest result — showing that one measurement artifact
   can produce an identified τ below the entire observed full-quality range across 116
   host–socket units.
5. An out-of-sample residual evaluation (five baselines and a permutation null) showing
   that higher measurement quality does not materially improve residual prediction.
6. An operational boundary: τ is causally and cheaply computable online, but the evaluated
   standalone rule does not separate out-of-sample behaviour from baseline variability.

To the best of our reviewed literature, the specific controlled combination — same
hardware, deliberate measurement-quality degradation, quantified effective-τ shift,
comparison against natural fleet variation, out-of-sample residual evaluation, and an
online-computation boundary — has not been reported together on real supercomputer
measurements, even though each ingredient is individually known.

<!-- Guardrails: effective τ defined as identification parameter; no physical R·C; no
causal cross-machine claim (within-Summit only); "not materially" not "unlearnable";
conservative novelty ("to the best of our reviewed literature"); Related-Work citations
[VERIFY] deferred to Section 3. Numbers trace to paper_results_manifest.json. -->
