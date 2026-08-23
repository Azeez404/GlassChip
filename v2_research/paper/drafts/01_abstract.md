# Abstract (draft v1)

Thermal models of computing systems are routinely identified from a machine's own
temperature and power measurements, yet those measurements differ in how precisely,
how frequently, and with how much spatial detail they are recorded. We study, on the
Summit supercomputer, how such measurement quality affects a first-order thermal model
identified from the measurements, and whether higher measurement quality also makes the
unexplained residual behaviour more predictable. Holding the hardware and workload
fixed, we degrade only the measurements along three axes — temperature quantization to
1 °C, temporal downsampling from 10 s to 20 s, and spatial aggregation to a single
hottest-core proxy — and re-identify the model in each condition. We find that the
identified effective thermal response time, τ (an identification parameter, not a
directly measured physical R·C constant), shifts substantially: quantization moves the
fleet-subset median from about 394 s to about 116 s (0.29×), and downsampling to about
910 s (2.31×). A moving-block bootstrap confirms these shifts are not an artifact of the
uncertainty calculation, and shows that a precise-looking confidence interval can
surround a substantially biased estimate. Across all 116 host–socket units (median τ
about 439 s, range 205–2596 s), the quantization-induced estimate falls below the
entire observed full-quality fleet range. In contrast, higher measurement quality does
not materially improve out-of-sample prediction of the residual (strongest model
R² ≤ 0.066, near a permutation null). Finally, τ is cheaply and causally computable
online (about 0.041 ms per window), but a short-window τ statistic does not separate
out-of-sample behaviour from baseline variability. These are controlled empirical
findings — a caution for thermal-model calibration on real systems — rather than a new
model, a monitor, or a physical claim.

<!-- ~215 words. Numbers trace to paper_results_manifest.json. Forbidden-claim clean:
effective τ defined; "not materially" (not "unlearnable"); no monitor/failure/physical
claim; mentor-facing terminology. Trim to ~200 in copy-edit. -->
