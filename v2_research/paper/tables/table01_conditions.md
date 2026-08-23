# Table 1. Measurement-quality conditions

| Cond | Temperature | Sampling | Spatial | Note |
|---|---|---|---|---|
| F0 | socket-mean, float | 10 s | socket-mean | full (reference) |
| F1 | socket-mean, 1 C | 10 s | socket-mean | quantization |
| F2 | socket-mean, float | 20 s | socket-mean | downsample (decimate x2) |
| F3 | Tjmax, float | 10 s | hottest-core proxy | spatial; NOT a fixed-core stream (no per-core streams in archive) |
| F4 | Tjmax, 1 C | 20 s | hottest-core proxy | combined degradation |
