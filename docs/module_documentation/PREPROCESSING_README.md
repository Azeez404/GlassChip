# GLASSCHIP-V1 Preprocessing

**Scope:** `SCIENTIFICALLY VALIDATED DATA → MODEL READY DATA`.

Prototype only: **temperature, power, fan speed**. Nothing else.

---

## Architecture

```
loader.py            (LOCKED)   raw parquet -> dataframes
validator.py         (LOCKED)   what can safely coexist?  PASS / FAIL
        |
        v
metric_selector.py   THE GATE   refuses anything validator FAILs
        |
        v
preprocessor.py                 sort, dtype, drop impossible values
        |
        v
timeseries_builder.py           exact inner join on timestamp
        |
        v
exporter.py                     Node_15.parquet / Node_15.csv
```

Each stage does one thing and hands on. No stage reaches back.

---

## The gate

`metric_selector.py` calls `validator.py` and **raises
`IncompatibleSelectionError` on `FAIL`**. There is deliberately **no
override flag**. Invalid data stays invalid.

```python
selector.select_metrics()                       # PASS -> proceeds
selector.select_metrics({                       # FAIL -> raises
    "temperature": "cpu_user",   # 90 s, ganglia
    "power":       "p0_power",   # 20 s, ipmi
})
# IncompatibleSelectionError: Validator returned FAIL; preprocessing must stop.
#   - Metrics sample at different nominal intervals {'cpu_user': 90.0, 'p0_power': 20.0}.
#   - only 5.3% of cpu_user timestamps match exactly (threshold 95%).
```

Use `describe_selection()` to inspect a refusal without raising.

---

## Locked metric set

| Role | Metric | Plugin | Interval | Nodes |
|---|---|---|---|---|
| `temperature` | `p0_core0_temp` | `ipmi_pub` | 20 s | 394 |
| `power` | `p0_power` | `ipmi_pub` | 20 s | 980 |
| `fan_speed` | `fan0_0` | `ipmi_pub` | 20 s | 980 |

**Common nodes: 394.** All three sit on the same rigid 20 s IPMI grid with a
measured **100 % exact timestamp match** — which is the only reason an exact
join is possible.

`cpu_user` (90 s) and `cpu_speed` (60 s) are **out of scope**. They match at
5.7–5.8 %; joining them would require tolerance matching, which is value
fabrication.

---

## Quick start

```python
from metric_selector import MetricSelector
from timeseries_builder import TimeSeriesBuilder
from exporter import Exporter

selector = MetricSelector("datasets/21-03")
node = selector.select_node("15")                 # verified against validator

builder = TimeSeriesBuilder("datasets/21-03")     # gate runs on construction
frame, report = builder.construct_node_dataframe(node)

Exporter("data/processed").export_node(
    frame, node, formats=("parquet", "csv"), report=report
)
```

Run `python preprocessing_example_usage.py` for a full walkthrough.

---

## Output

```
                timestamp node  temperature  power  fan_speed
2021-03-01 00:00:00+00:00   15         44.0   34.0     4300.0
2021-03-01 00:00:20+00:00   15         45.0   34.0     4300.0
2021-03-01 00:00:40+00:00   15         44.0   34.0     4300.0
2021-03-01 00:01:00+00:00   15         45.0   34.0     4300.0
```

| Column | dtype | Unit |
|---|---|---|
| `timestamp` | `datetime64[ms, UTC]` | — |
| `node` | `string` | — |
| `temperature` | `float64` | °C |
| `power` | `float64` | W (per socket) |
| `fan_speed` | `float64` | RPM |

Files: `Node_<id>.parquet`, `Node_<id>.csv`, `Node_<id>_report.json`.

Parquet round-trips identically (`read_parquet(...).equals(frame) is True`).
Prefer it; CSV carries no dtype information.

---

## What each module does

### `metric_selector.py`

`select_metrics()` · `select_node()` · `select_nodes()` ·
`select_common_nodes()` · `describe_selection()`

Refuses unsupported roles, absent metrics, and any selection the validator
fails.

### `preprocessor.py`

`preprocess_metric()` · `preprocess_node()` · `prepare_model_input()`

Exactly four operations, all removal or shaping:

1. Sort ascending by timestamp
2. `int32 → float64` (exact for the integer ranges present), timestamps to
   UTC-aware
3. Drop nulls and **physically impossible** values
4. Drop exact duplicate timestamps (`keep="first"`, nothing merged or
   averaged)

Returns a removal report: `n_input`, `n_output`, `n_removed_null`,
`n_removed_out_of_bounds`, `n_removed_duplicate`, `removal_ratio`.

### `timeseries_builder.py`

`build_timeseries()` · `align_metrics()` · `construct_node_dataframe()` ·
`build_many()`

**Exact inner join on the timestamp instant** (`validate="one_to_one"`). No
tolerance, no `merge_asof`, no reindexing, no fill. A row survives only if
all three metrics recorded a value at that exact instant.

Reports contiguous segments — boundaries only, nothing inserted between
them.

### `exporter.py`

`export_parquet()` · `export_csv()` · `export_node()` · `export_many()`

Writes what it is given, unchanged. Refuses empty frames and, unless
`overwrite=True`, refuses to clobber.

---

## Physical bounds

`PHYSICAL_BOUNDS` in `preprocessor.py`. Inclusive; a record outside its
bound is removed.

| Role | Bound | Observed in `21-03` | Basis |
|---|---|---|---|
| `temperature` | 0 – 125 °C | 31 – 54 °C | POWER9 Tjmax ≈ 100 °C; IPMI sensor span |
| `power` | 0 – 500 W | 10 – 268 W | POWER9 AC922 socket TDP ≈ 250 W |
| `fan_speed` | 0 – 30000 RPM | 0 – 10100 RPM | Observed maximum |

**Deliberately permissive.** They reject the *impossible* (−50 W, 500 °C,
−400 RPM), not the *unusual*. Narrowing them is a scientific filtering
decision, not preprocessing — pass `bounds=` to `Preprocessor` and justify
it.

On record `21-03` these bounds remove **zero** records: no nulls, no
negatives, no duplicate timestamps.

**`fan_speed == 0` is retained.** A stopped fan is physically possible. It
occurs in 2.5 % of raw `fan0_0` rows, intermittently, and those rows carry
no matching power timestamp so the exact join drops them anyway.

---

## Measured on record `21-03`, node 15

| | |
|---|---|
| Rows after cleaning | temperature 11,167 · power 11,166 · fan 11,166 |
| Rows after exact join | **11,166** |
| Join retention | **1.0000** |
| Records removed by bounds | **0** |
| Nulls in output | **0** |
| Segments | **61.978 h** (11,157 samples) + 0.044 h (9 samples) |
| Build time | ~0.7 s/node |
| File size | 87.9 KB parquet · 501.6 KB csv |

The two segments reproduce the validator's finding exactly: one contiguous
61.98 h block, then a 27-day gap, then a 9-row fragment.

---

## Limitations

1. **62 hours, not a month.** Record `21-03` holds one contiguous 61.98 h
   block plus a 3-minute fragment. Enough for `R_th` / `C_th`; **not**
   longitudinal analysis.
2. **394 nodes, not 980.** `p0_core0_temp` limits the intersection. Per-core
   sensors span 366–738 nodes across the record.
3. **The 9-row fragment survives.** It is real data and is not dropped. Any
   model fit must respect the segment boundaries in the report.
4. **Temperature choice is a scientific decision.** `p0_core0_temp` is
   core-proximate and correct for CPU `R_th`, at the cost of coverage.
   `p0_vdd_temp` reaches 980 nodes but measures a voltage regulator — on
   node 15 it spans 34–36 °C against a 32→72 W power swing.
5. **Observational, closed-loop data.** Power is governed by DVFS; inputs
   are not independent and no causal claim is supported.
6. **No instrument characterisation.** Sensor accuracy, calibration, and
   drift are unknown and unknowable from this record.
7. **Single socket.** `p0_*` only. `p1_*` is not combined.

---

## Not implemented, by rule

Normalisation · standardisation · interpolation · resampling · reindexing ·
forward/backward fill · gap filling · `merge_asof` or any tolerance join ·
PCA · dimensionality reduction · feature engineering · derived columns ·
outlier statistics · smoothing · timestamp fabrication · missing-value
fabrication.

If the validator says `FAIL`, preprocessing stops. Compatibility is never
forced.
