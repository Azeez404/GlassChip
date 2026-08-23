<!-- Abstract skeleton (Phase 3D / STEP 2). NO prose yet — bullet objectives only.
Target ~200 words when drafted in STEP 3. Numbers must trace to the manifest. -->

# Abstract — [DRAFT PENDING]

Bullet plan (problem → method → findings → limitation → contribution):
- Problem: thermal models are identified from a machine's own temperature and power measurements, which vary in precision, sampling rate, and spatial detail.
- Method: on Summit, degrade ONLY measurement quality on the same hardware/workload (F0–F4); frozen first-order ARX; effective τ; analytic + moving-block bootstrap uncertainty; 116-unit fleet; causal online rolling-τ test.
- Finding 1: measurement quality substantially changes identified effective τ (0.29× under 1 °C quantization; 2.31× under 20 s downsampling).
- Finding 2: block-bootstrap confirms the shift; a precise-looking interval can surround a biased estimate.
- Finding 3: the quantization-induced estimate (~116 s) falls below the entire observed full-fidelity fleet range (min ~205 s).
- Finding 4: higher measurement quality does not materially improve out-of-sample residual prediction (best ≤0.066, near permutation null).
- Finding 5: τ is online-computable (~0.041 ms/window) but the evaluated standalone rule does not separate out-of-sample behavior from baseline variability.
- Limitation + contribution: a controlled empirical limits study on real HPC measurements — a caution for thermal-model calibration; not a new method, monitor, or physical claim.
