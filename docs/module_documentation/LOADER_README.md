# `loader.py` — M100 ExaData Dataset Loader

**Scope:** `RAW DATASET → ACCESSIBLE DATA`. Nothing else.

Reads Parquet, returns DataFrames. Does **not** clean, resample, decode, impute,
normalise, or engineer features. Anything that changes a number belongs in
preprocessing, not here.

---

## Install / requirements

```
pandas
pyarrow
```

No other dependencies. Pure `pathlib`, platform independent.

---

## Quick start

```python
from loader import DatasetLoader

loader = DatasetLoader("datasets/21-03")

loader.get_available_metrics()                          # 338 metric names
loader.get_available_nodes(plugin="ipmi_pub")           # node inventory
loader.load_metric("p0_power", nodes=["15"])            # filtered read
loader.load_metric_for_node("p0_power", "15")           # timestamp, value, node
loader.load_node("15", metrics=["p0_power", "ambient"]) # long format
loader.dataset_summary()                                # metadata only
```

Run `python example_usage.py` for a working walkthrough.

---

## ⚠️ Two dataset properties you must know before using this

### 1. Node ID namespaces are plugin-specific and do NOT match

Verified on record `21-03`:

| Plugin | Node ID range | Count |
|---|---|---|
| `ipmi_pub` (power, temps, fans) | 0 – 979 | 980 |
| `ganglia_pub` (cpu_user, load, mem) | **3 – 987** | 982 |
| `nagios_pub` (state) | 0 – 1162 | 1026 |

- `ipmi ∩ ganglia` = **974** nodes, not 980.
- `ganglia` has 980–987, which `ipmi` does not have at all.
- `ipmi` has 0, 1, 2, which `ganglia` does not have.

Coverage also varies **between metrics inside one plugin**: `p0_power` has 980
nodes, `ambient` has 979.

**Consequence:** node `"15"` in `ipmi_pub` is not proven to be the same physical
machine as node `"15"` in `ganglia_pub`. Joining CPU power (ipmi) to CPU
utilisation (ganglia) on the raw `node` column is **not yet justified**.

`get_available_nodes()` emits a `UserWarning` when namespaces disagree and
returns `common_node_ids` (the intersection) alongside the union. Use
`get_available_nodes(plugin=...)` for a single unambiguous namespace, and
`nodes_for_metric(metric)` for an exact per-metric set.

Establishing (or refuting) a cross-plugin node mapping is a preprocessing/
validation task, not a loader task. The loader's job is to make the discrepancy
visible rather than paper over it.

### 2. Two plugins have no `node` column at all

`schneider_pub` (cooling plant PLC) and `logics_pub` (electrical panels) are
**facility-scoped**. They carry `panel` / `device` instead. Node-based
accessors raise `DatasetLoaderError` for these rather than returning empty.

---

## Layout expected

```
<dataset_path>/
    year_month=21-03/
        plugin=ipmi_pub/
            metric=p0_power/
                a_0.parquet
        plugin=ganglia_pub/
            metric=cpu_user/
                a_0.parquet
        ...
```

Either the record root (`datasets/21-03`) or the `year_month=*` directory is
accepted; the loader resolves it.

Metric names are unique across plugins in this record, so the bare metric name
is a sufficient lookup key. A duplicate would warn and keep the first.

---

## Schemas (record `21-03`)

| Plugin | Columns | `value` dtype | Node-scoped |
|---|---|---|---|
| `ipmi_pub` | `timestamp`, `value`, `node` | `int32` | ✅ |
| `ganglia_pub` | `timestamp`, `value`, `node` | `float32` | ✅ |
| `nagios_pub` | `timestamp`, `value`, `description`, `host_group`, `nagiosdrained`, `node`, `state_type` | `int32` | ✅ |
| `schneider_pub` | `timestamp`, `value`, `panel` | `int32` | ❌ |
| `logics_pub` | `timestamp`, `value`, `panel`, `device` | `float32` | ❌ |

`timestamp` is `timestamp[ms, tz=UTC]` throughout.

---

## API

### `DatasetLoader(dataset_path)`

Indexes the tree on construction — a path scan only, no file reads (~0.06 s for
338 metrics). Raises `DatasetLoaderError` if the path is missing or contains no
`plugin=*` directories.

Supports `len(loader)`, `"p0_power" in loader`, and `repr()`.

### `load_parquet(path, columns=None, filters=None)`

Read a Parquet file or directory. `filters` are PyArrow predicate pushdown,
e.g. `[("node", "in", ["15"])]`.

### `load_metric(metric, nodes=None, columns=None)`

Load one metric. When `nodes` is given the filter is **pushed into the Parquet
reader**, so memory is proportional to the result, not the file.

> `p0_power` is 10.7 M rows for one month. Always prefer `nodes=` / `columns=`
> over loading in full and slicing afterwards.

Raises `DatasetLoaderError` if `nodes` is passed for a facility-scoped metric.

### `load_metric_for_node(metric, node, columns=None)`

One metric, one node. Returns `timestamp`, `value`, `node`. Raises
`NodeNotFoundError` if the node has no rows in that metric.

### `load_node(node, metrics=None, plugins=None)`

All records for one node, long format:
`timestamp`, `value`, `node`, `metric`, `plugin` — sorted by metric then time.

- `metrics=None` reads every node-scoped metric (~580 MB for one month) and
  emits a `UserWarning`. Pass `metrics=` or `plugins=` to scope it.
- Long format keeps only the columns common to all node-scoped plugins.
  `nagios_pub`'s extra columns are dropped here — use `load_metric` for those.
- Stacking `int32` (ipmi) with `float32` (ganglia) widens `value` to `float64`.
  Container change only; no value is altered.

### `get_available_metrics(plugin=None)` → `list[str]`

### `get_available_plugins()` → `list[str]`

### `nodes_for_metric(metric)` → `list[str]`

Exact node set for one metric. Use when per-metric precision matters.

### `get_available_nodes(plugin=None, refresh=False)` → `dict`

```
total_nodes, node_ids                # union across node-scoped plugins
total_common_nodes, common_node_ids  # intersection
namespaces_agree                     # False on record 21-03
min_id, max_id, is_contiguous, dtype
by_plugin: {plugin: {total_nodes, min_id, max_id, source_metric}}
```

Each plugin's set is sampled from its **largest** metric file (widest coverage)
and cached. Warns when namespaces disagree.

### `dataset_summary(sample_timestamps=True)` → `dict`

Metadata only; reads Parquet footers, never row data.

```
dataset_path, root
total_files, total_bytes, total_size_mb
total_metrics, total_nodes
nodes_by_plugin, total_common_nodes, node_namespaces_agree
plugins: {plugin: {metrics, files, bytes, size_mb, node_scoped, columns, dtypes}}
metrics_by_plugin
timestamp_range: {min, max, source_metric, dtype}
```

---

## Exceptions

```
DatasetLoaderError                    # base
├── MetricNotFoundError  (KeyError)   # unknown metric
└── NodeNotFoundError    (KeyError)   # node absent from that metric
```

---

## Measured on record `21-03`

| Operation | Time |
|---|---|
| `DatasetLoader(...)` | 0.06 s |
| `get_available_nodes()` | 0.43 s (cached after) |
| `dataset_summary()` | 0.55 s |
| `load_metric_for_node("p0_power", "15")` | 0.15 s → 11,166 rows |
| `load_metric("p0_power", nodes=[0,1,2])` | 0.08 s → 33,499 rows |
| `load_node("15", metrics=[5 metrics])` | 0.40 s → 47,136 rows |

Record totals: 338 metrics · 338 files · 601.32 MB · 5 plugins ·
`2021-03-01 00:00:00Z` → `2021-03-31 12:03:15Z` · 20 s sampling interval.

---

## Deliberately not implemented

Missing-value handling · resampling / alignment · unit decoding (e.g. Schneider
values are integer tenths of °C — **not** decoded here) · normalisation ·
feature engineering · validation · visualisation · caching to disk · models.

All of the above belong to later modules.
