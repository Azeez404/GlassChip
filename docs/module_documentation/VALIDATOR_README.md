# `validator.py` — Scientific Inspector

**Scope:** answers one question — **what can safely exist together?**

Reports. Never repairs. No interpolation, resampling, alignment, imputation,
dropping, or normalisation. Where two metrics cannot be joined it says so and
stops. Constructing a joined series is preprocessing's job.

Requires `loader.py` (locked, unmodified), `pandas`, `numpy`, `pyarrow`.

---

## Headline verdict on record `21-03`

```python
DatasetValidator("datasets/21-03").validate_glasschip_inputs()["verdict"]
# 'FAIL'
```

**The five locked mandatory inputs cannot form a model-ready series from the
raw record.** Two blocking issues:

1. **Three different sampling intervals** — 20 s / 60 s / 90 s.
2. **Exact timestamp joins are not viable** — 5.7–5.8 % match across plugins.

`FAIL` does **not** mean the project is infeasible. It means an explicit,
documented preprocessing decision is required before modelling, and that
decision is out of this module's remit.

**The IPMI-only subset PASSES:**

```python
validate_glasschip_inputs(inputs={
    "temperature": "p0_core0_temp",
    "power":       "p0_power",
    "fan_speed":   "fan0_0",
})["verdict"]
# 'PASS'  — 394 shared nodes, all 20 s, 100 % exact match
```

---

## Measured facts (record `21-03`, node 15)

### Sampling intervals differ by plugin, and within plugin

| Metric | Plugin | Interval | Jitter | Regular grid |
|---|---|---|---|---|
| `p0_power`, `p0_core0_temp`, `fan0_0`, `ambient` | `ipmi_pub` | **20.0 s** | 0.00 s | ✅ |
| `cpu_speed` (frequency) | `ganglia_pub` | **60.0 s** | ±1 s | ❌ |
| `cpu_user` (utilisation) | `ganglia_pub` | **90.0 s** | 2.61 s | ❌ |

IPMI is a rigid grid. Ganglia is a jittered stream — its timestamps can
never land reliably on IPMI's grid.

### Exact-match matrix

| Pair | Intervals | Exact match | Joinable |
|---|---|---|---|
| `p0_core0_temp` + `p0_power` | 20/20 | **100.00 %** | ✅ |
| `p0_power` + `fan0_0` | 20/20 | **100.00 %** | ✅ |
| `p0_core0_temp` + `fan0_0` | 20/20 | **100.00 %** | ✅ |
| `cpu_speed` + `cpu_user` | 60/90 | 49.96 % | ❌ |
| `p0_power` + `cpu_speed` | 20/60 | 5.74 % | ❌ |
| `p0_power` + `cpu_user` | 20/90 | 5.83 % | ❌ |

**Ganglia cannot even join itself** (60 s vs 90 s, 49.96 %).

### Contiguity — the record is not a month

| | |
|---|---|
| IPMI span | 29.62 days |
| IPMI samples | 11,167 @ 20 s |
| **Coverage vs 20 s grid** | **8.7 %** |
| Gaps > 3 × median | 1 |
| **Largest gap** | **648.85 h (27 days)** |
| **Longest contiguous run** | **61.98 h** |
| Ganglia span | 2.58 days (ends; no tail fragment) |

IPMI holds one contiguous block `03-01 00:00` → `03-03 13:58` (61.98 h,
11,157 rows) then a 27-day gap then a **9-row, 3-minute fragment** on 03-30.
That fragment is what inflates the span to 29.6 days and drags coverage to
8.7 %.

**All five mandatory inputs share the same 61.98 h window.** That is the
usable data in this record. At 20 s it is ~11,150 samples per node — ample
for `R_th` / `C_th`, and **not** enough for longitudinal analysis.

### Node coverage is not uniform — including within one plugin

| Metric | Nodes |
|---|---|
| `p0_power`, `fan0_0`, `p0_vdd_temp`, `gpu*_temp`, `dimm*_temp` | 980 |
| `ambient` | 979 |
| `cpu_user`, `cpu_speed` | 982 (IDs 3–987) |
| **`p0_core0_temp`, `p0_core1_temp`** | **394** |
| Other `p0_coreN_temp` | 366 – 738 |

**Intersection of the five mandatory inputs: 392 nodes**, not 980.

Of the 74 IPMI temperature metrics, only 26 have full 980-node coverage.
Per-core sensors range 366–738.

---

## ⚠️ The temperature-metric choice is yours, not the validator's

`GLASSCHIP_MANDATORY_INPUTS` defaults `temperature` to **`p0_core0_temp`**.

| Candidate | Nodes | Physical meaning |
|---|---|---|
| `p0_core0_temp` *(default)* | **394** | Core-proximate — correct quantity for CPU `R_th` |
| `p0_vdd_temp` | **980** | VDD **regulator**, not the die |
| `ambient` | 979 | Node inlet air |
| `gpu0_core_temp` | 980 | GPU die, different thermal domain |

The default is the physically correct quantity, accepting a 394-node limit.
`p0_vdd_temp` buys full coverage but measures a different point in the
thermal circuit — on node 15 it spans only **34–36 °C** against a **32→72 W**
power swing, which is a well-cooled regulator, not a die proxy.

The validator reports coverage and lets you decide. Override via `inputs=`.

---

## Verdict thresholds

Every judgement traces to a module constant. All are auditable and
adjustable.

| Constant | Value | Meaning |
|---|---|---|
| `EXACT_MATCH_TOLERANCE_S` | `0.0` | Timestamps must be bit-identical. Anything looser is interpolation. |
| `JITTER_TOLERANCE_S` | `0.5` | Above this a series is a jittered stream, not a grid. |
| `MIN_EXACT_MATCH_RATIO` | `0.95` | Exact-join viability threshold. |
| `MIN_NODE_OVERLAP_RATIO` | `0.95` | Node-compatibility threshold. |
| `MIN_COVERAGE_RATIO` | `0.90` | Below this a series is reported sparse. |
| `MIN_CONTIGUOUS_SEGMENT_S` | `43200` (12 h) | Shortest run that can carry a transient fit. |
| `GAP_THRESHOLD_MULTIPLIER` | `3.0` | Interval > 3 × median counts as a gap. |

---

## API

### `DatasetValidator(loader)`

Accepts a `DatasetLoader` or a path. Caches node sets and timing profiles.

### `validate_metric(metric, sample_node=None)`

Existence, schema, dtypes, row count, file count, size, timestamp/node
availability, node range, and a full timing profile.

Returns `valid`, `issues`, and `timing` with: `median_interval_s`,
`interval_jitter_s`, `is_regular_grid`, `coverage_ratio`, `is_sparse`,
`n_gaps`, `largest_gap_h`, `n_segments`, `longest_segment_h`, `segments`.

> `longest_segment_h` is the honest usability number. `coverage_ratio` is
> distorted by isolated tail fragments — see the 8.7 % case above.

### `validate_node(node, metrics=None, plugins=None)`

Which metrics and plugins carry a node; which do not. Flags plugin absence
because node ID namespaces are plugin-local.

`metrics=None` reads one `node` column per node-scoped metric (~138).

### `validate_timestamp_alignment(metrics, node=None)`

Per-metric timing plus a pairwise matrix: nominal intervals, exact-match
ratio, `exact_join_viable`, and temporal overlap window.

Match ratio counts timestamps of the **sparser** series appearing
bit-identically in the denser one. A tolerance join is preprocessing and is
deliberately not offered.

Raises `ValidationError` on fewer than two node-scoped metrics or no shared
node.

### `find_common_nodes(metrics)`

Intersection, union, per-metric counts and ranges, `overlap_ratio` against
the smallest set. Facility-scoped metrics reported separately and excluded.

### `validate_metric_compatibility(metrics, node=None)`

Three independent axes, reported separately:

- **`schema`** — `timestamp` + `value` present; scope not mixed
- **`identifier`** — node namespaces intersect sufficiently
- **`timestamp`** — shared time base at `EXACT_MATCH_TOLERANCE_S`

Returns `verdict` (`PASS`/`FAIL`), `blocking`, `limitations`.

### `validate_glasschip_inputs(inputs=None, node=None)`

Feasibility of the locked mandatory inputs. Checks existence, plugin spread,
node intersection, sampling compatibility, exact-join viability, and
contiguous-segment sufficiency.

Returns `verdict` (`PASS`/`FAIL`), `justification`, `blocking_issues`,
`scientific_limitations`, `sampling`, `common_nodes`.

### `generate_validation_report(metrics=None, node=None)`

Everything above plus a `joinability` matrix and flat `observations`.
JSON-serialisable with `default=str`. ~8 s on record `21-03`.

`observations` states what was measured. It contains no repair instructions.

---

## Standing scientific limitations (reported on every run)

1. Only 392 of 394 nodes carry every mandatory input.
2. Inputs span two plugins; **cross-plugin node identity is unproven**.
3. Coverage 8.7 % over 29.62 days; usable contiguous run **61.98 h**.
4. **Observational production telemetry** — power is closed-loop under DVFS
   and governor control, so inputs are not independent and **no causal claim
   is supported**.
5. **No instrument characterisation is possible** — sensor accuracy,
   calibration, and drift are unknown and unknowable from this record.

---

## Exceptions

```
ValidationError   # a validation could not be carried out at all
```

Raised for: fewer than two metrics, no node-scoped metric, no shared node,
unopenable dataset. A metric that merely *fails* validation returns a report
with `valid=False`; it does not raise.

---

## Deliberately not implemented

Tolerance/as-of joins · resampling · gap filling · interpolation ·
outlier handling · unit decoding · value-range or physical-plausibility
checks · any repair or recommendation of a repair.

If something is wrong it is reported, not fixed. If something is
incompatible, compatibility is not forced.
