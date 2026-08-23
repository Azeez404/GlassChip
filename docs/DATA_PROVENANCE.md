# Dataset Provenance and Integrity

Provenance for the Summit per-component power and thermal archive
(OSTI/OLCF DOI 10.13139/OLCF/1861393, CC-BY-4.0). The raw archive is never committed; these
reports record what was received, how it was checked, and how it was derived.

Machine-readable counterparts live in `artifacts/manifests/`.


---

## Inventory summary

*(source: `v2_research/summit/inventory/summary.md`)*

## Summit dataset - inventory summary

Generated 2026-08-19T18:52:45+00:00 | scan 56.4 s | source `v2_research\summit\raw\a_fullperiod_10sec_58hosts_decomp`

1. **Hosts discovered:** 58
2. **Hosts processed OK:** 58
3. **Hosts with errors:** 0
4. **Total Parquet files:** 8,223
5. **Total rows:** 73,904,353
6. **Total size:** 4.51 GB
7. **Global timestamp range:** 2020-01-01T00:00:00.000000000 -> 2022-01-31T23:59:50.000000000
8. **Sampling interval distribution (s):** {10: 58}
9. **Distinct fleet schemas:** 1 (consistent)
10. **Hosts with duplicates:** 58
11. **Hosts with nulls:** 58
12. **Hosts with invalid values:** 0
13. **Hosts with mixed float dtypes:** 38

### Suspicious anomalies (items 15-16)

- **Conflicting duplicate timestamps**: 58 hosts have duplicate timestamps, and (verified per host) the large majority are same-timestamp rows with *different* sensor payloads, not exact copies. Downstream preprocessing must apply a documented de-duplication/resolution rule; do NOT blind-drop. See `integrity_report.md`.
- **Mixed float dtypes**: 38 hosts store some temperature columns as Float64 in some files and Float32 in others (column names are otherwise identical fleet-wide). Unify dtype on load.
- **Partial/overlapping day files**: many day files hold fewer than 8640 rows (partial days) and some ranges overlap at day boundaries; missing calendar days are expected (5 collection months, not continuous).

See `schema_report.md`, `sampling_report.md`, `integrity_report.md`, and `dataset_inventory.{json,csv}` for detail. Per-host timestamp ranges are in the CSV/JSON.

---

## Integrity report

*(source: `v2_research/summit/inventory/integrity_report.md`)*

## Summit dataset - integrity report

- Hosts with duplicate timestamps: 58
- Hosts with nulls: 58
- Hosts with invalid values: 0
- Hosts with errors: 0

### Duplicate timestamps: exact-identical vs conflicting payload

Downstream MUST NOT blind-drop duplicates: most are same-timestamp rows with DIFFERENT sensor values (conflicting), needing a documented resolution rule. Inspection only records them.

| host | dup_ts | exact_identical_rows | conflicting_ts |
|---|---|---|---|
| a07n04 | 120779 | 2484 | 118295 |
| a09n18 | 120250 | 2286 | 117964 |
| a11n12 | 120221 | 2215 | 118006 |
| a13n06 | 120785 | 2197 | 118588 |
| a14n08 | 120291 | 2122 | 118169 |
| a16n12 | 120246 | 2129 | 118117 |
| a17n15 | 58222 | 609 | 57613 |
| a26n06 | 117781 | 2296 | 115485 |
| a26n16 | 117244 | 2186 | 115058 |
| a31n17 | 117250 | 2268 | 114982 |
| a32n09 | 117292 | 2328 | 114964 |
| a33n14 | 117732 | 2383 | 115349 |
| a34n06 | 117889 | 2375 | 115514 |
| b03n06 | 117893 | 11962 | 105931 |
| b03n16 | 117364 | 5225 | 112139 |
| b08n16 | 58465 | 566 | 57899 |
| b17n09 | 116530 | 2114 | 114416 |
| b18n01 | 116555 | 2160 | 114395 |
| b28n11 | 116496 | 2325 | 114171 |
| b29n03 | 116552 | 2459 | 114093 |
| c03n13 | 116355 | 4848 | 111507 |
| c04n05 | 116941 | 5026 | 111915 |
| c25n15 | 54782 | 641 | 54141 |
| d01n08 | 119110 | 4472 | 114638 |
| d01n18 | 119006 | 4717 | 114289 |
| d06n18 | 119063 | 4455 | 114608 |
| d07n10 | 119061 | 4680 | 114381 |
| d12n10 | 119066 | 4809 | 114257 |
| d13n02 | 119129 | 4287 | 114842 |
| d16n17 | 118665 | 4286 | 114379 |
| d17n09 | 118743 | 4866 | 113877 |
| d24n11 | 118639 | 5129 | 113510 |
| e05n03 | 117692 | 4547 | 113145 |
| e05n13 | 117065 | 5648 | 111417 |
| e27n05 | 119563 | 5770 | 113793 |
| e27n15 | 119409 | 5086 | 114323 |
| e30n11 | 119042 | 4852 | 114190 |
| f07n02 | 121510 | 5485 | 116025 |
| f07n12 | 121433 | 5769 | 115664 |
| f12n12 | 58533 | 529 | 58004 |
| f23n17 | 118279 | 4680 | 113599 |
| f24n09 | 118332 | 4864 | 113468 |
| g03n14 | 117471 | 4484 | 112987 |
| g04n06 | 118024 | 4887 | 113137 |
| g09n06 | 114296 | 5781 | 108515 |
| g09n16 | 117523 | 6302 | 111221 |
| g14n16 | 117533 | 5735 | 111798 |
| g15n08 | 117970 | 5452 | 112518 |
| g20n08 | 122056 | 4923 | 117133 |
| g20n18 | 122035 | 6948 | 115087 |
| g25n18 | 122359 | 6763 | 115596 |
| g26n10 | 122454 | 6309 | 116145 |
| h25n02 | 116644 | 8762 | 107882 |
| h25n12 | 116525 | 7375 | 109150 |
| h30n12 | 116074 | 5743 | 110331 |
| h31n04 | 116634 | 5492 | 111142 |
| h36n04 | 57834 | 604 | 57230 |
| h36n14 | 116456 | 2316 | 114140 |

### Nulls / invalids per host (non-zero only)

| host | total_nulls | null_pct | invalid columns |
|---|---|---|---|
| a07n04 | 5245 | 0.0133 | - |
| a09n18 | 6231 | 0.0158 | - |
| a11n12 | 5715 | 0.0145 | - |
| a13n06 | 5395 | 0.0137 | - |
| a14n08 | 5044 | 0.0128 | - |
| a16n12 | 5220 | 0.0133 | - |
| a17n15 | 5115 | 0.0145 | - |
| a26n06 | 5120 | 0.0136 | - |
| a26n16 | 6128 | 0.0163 | - |
| a31n17 | 6016 | 0.016 | - |
| a32n09 | 4725 | 0.0126 | - |
| a33n14 | 19763 | 0.0513 | - |
| a34n06 | 5220 | 0.0136 | - |
| b03n06 | 619304 | 1.6083 | - |
| b03n16 | 620324 | 1.6118 | - |
| b08n16 | 127281 | 0.3516 | - |
| b17n09 | 5510 | 0.0147 | - |
| b18n01 | 8422 | 0.0225 | - |
| b28n11 | 7418 | 0.0198 | - |
| b29n03 | 7452 | 0.0199 | - |
| c03n13 | 633151 | 1.6897 | - |
| c04n05 | 634023 | 1.691 | - |
| c25n15 | 128535 | 0.3688 | - |
| d01n08 | 636833 | 1.6525 | - |
| d01n18 | 643864 | 1.6709 | - |
| d06n18 | 644577 | 1.6726 | - |
| d07n10 | 636685 | 1.6522 | - |
| d12n10 | 637232 | 1.6536 | - |
| d13n02 | 637102 | 1.6532 | - |
| d16n17 | 645062 | 1.7182 | - |
| d17n09 | 639029 | 1.702 | - |
| d24n11 | 643055 | 1.7129 | - |
| e05n03 | 638469 | 1.7018 | - |
| e05n13 | 631451 | 1.6842 | - |
| e27n05 | 638697 | 1.6998 | - |
| e27n15 | 638783 | 1.7003 | - |
| e30n11 | 638730 | 1.7009 | - |
| f07n02 | 642643 | 1.6392 | - |
| f07n12 | 641488 | 1.6364 | - |
| f12n12 | 125321 | 0.343 | - |
| f23n17 | 638479 | 1.7015 | - |
| f24n09 | 640339 | 1.7064 | - |
| g03n14 | 636882 | 1.6217 | - |
| g04n06 | 636755 | 1.6204 | - |
| g09n06 | 636524 | 1.7076 | - |
| g09n16 | 638006 | 1.6244 | - |
| g14n16 | 637332 | 1.6227 | - |
| g15n08 | 652900 | 1.6616 | - |
| g20n08 | 630718 | 1.6003 | - |
| g20n18 | 632200 | 1.6041 | - |
| g25n18 | 633593 | 1.6071 | - |
| g26n10 | 630011 | 1.5979 | - |
| h25n02 | 623511 | 1.5884 | - |
| h25n12 | 616997 | 1.572 | - |
| h30n12 | 617611 | 1.5743 | - |
| h31n04 | 616927 | 1.5717 | - |
| h36n04 | 125875 | 0.3428 | - |
| h36n14 | 7419 | 0.0189 | - |

### Mixed dtypes across files (anomaly, handled on read)

| host | columns (dtypes seen) |
|---|---|
| a17n15 | hostname: null/string; p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| a26n06 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| a26n16 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| a31n17 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| a32n09 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| a33n14 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| a34n06 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| b03n06 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| b03n16 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| b08n16 | timestamp: timestamp[ns, tz=UTC]/timestamp[us, tz=UTC]; hostname: null/string; p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| b17n09 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| b18n01 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| b28n11 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| b29n03 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| c03n13 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| c04n05 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| c25n15 | hostname: null/string; p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| d01n08 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| d01n18 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| d06n18 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| d07n10 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| d12n10 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| d13n02 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| d16n17 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| d17n09 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| d24n11 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| e05n03 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| e05n13 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| e27n05 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| e27n15 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| e30n11 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| f07n02 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| f07n12 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| f12n12 | hostname: null/string; p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| f23n17 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| f24n09 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| g09n06 | p0_core_temp_mean: double/float; p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_mean: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |
| h36n04 | p0_core_temp_min: double/float; p0_core_temp_max: double/float; p1_core_temp_min: double/float; p1_core_temp_max: double/float |

---

## Schema report

*(source: `v2_research/summit/inventory/schema_report.md`)*

## Summit dataset - schema report

Distinct fleet-wide schemas: **1**

- 58 host(s), 30 columns

### Column inventory (column -> hosts, role)

| column | role | hosts |
|---|---|---|
| `gpu0_core_temp` | temperature | 58/58 |
| `gpu0_mem_temp` | temperature | 58/58 |
| `gpu1_core_temp` | temperature | 58/58 |
| `gpu1_mem_temp` | temperature | 58/58 |
| `gpu2_core_temp` | temperature | 58/58 |
| `gpu2_mem_temp` | temperature | 58/58 |
| `gpu3_core_temp` | temperature | 58/58 |
| `gpu3_mem_temp` | temperature | 58/58 |
| `gpu4_core_temp` | temperature | 58/58 |
| `gpu4_mem_temp` | temperature | 58/58 |
| `gpu5_core_temp` | temperature | 58/58 |
| `gpu5_mem_temp` | temperature | 58/58 |
| `hostname` | host_id | 58/58 |
| `p0_core_temp_max` | temperature | 58/58 |
| `p0_core_temp_mean` | temperature | 58/58 |
| `p0_core_temp_min` | temperature | 58/58 |
| `p0_gpu0_power` | power | 58/58 |
| `p0_gpu1_power` | power | 58/58 |
| `p0_gpu2_power` | power | 58/58 |
| `p0_power` | power | 58/58 |
| `p1_core_temp_max` | temperature | 58/58 |
| `p1_core_temp_mean` | temperature | 58/58 |
| `p1_core_temp_min` | temperature | 58/58 |
| `p1_gpu0_power` | power | 58/58 |
| `p1_gpu1_power` | power | 58/58 |
| `p1_gpu2_power` | power | 58/58 |
| `p1_power` | power | 58/58 |
| `ps0_input_power` | power | 58/58 |
| `ps1_input_power` | power | 58/58 |
| `timestamp` | timestamp | 58/58 |

---

## Sampling report

*(source: `v2_research/summit/inventory/sampling_report.md`)*

## Summit dataset - sampling report

Intervals are computed from actual timestamp differences, not the directory name.

### Fleet dominant-interval distribution

| dominant interval (s) | hosts |
|---|---|
| 10 | 58 |

### Per-host sampling

| host | dominant | min | max | median | %dev | gaps>3x | irregular |
|---|---|---|---|---|---|---|---|
| a07n04 | 10 | 10 | 15724810 | 10 | 0.019 | 88 | 142 |
| a09n18 | 10 | 10 | 15724810 | 10 | 0.019 | 89 | 141 |
| a11n12 | 10 | 10 | 15724810 | 10 | 0.019 | 89 | 141 |
| a13n06 | 10 | 10 | 15724810 | 10 | 0.019 | 88 | 142 |
| a14n08 | 10 | 10 | 15724810 | 10 | 0.019 | 89 | 140 |
| a16n12 | 10 | 10 | 15724810 | 10 | 0.019 | 89 | 141 |
| a17n15 | 10 | 10 | 15724810 | 10 | 0.021 | 85 | 150 |
| a26n06 | 10 | 10 | 15724810 | 10 | 0.019 | 84 | 126 |
| a26n16 | 10 | 10 | 15724810 | 10 | 0.019 | 85 | 126 |
| a31n17 | 10 | 10 | 15724810 | 10 | 0.019 | 85 | 126 |
| a32n09 | 10 | 10 | 15724810 | 10 | 0.018 | 85 | 124 |
| a33n14 | 10 | 10 | 15724810 | 10 | 0.02 | 81 | 152 |
| a34n06 | 10 | 10 | 15724810 | 10 | 0.02 | 81 | 153 |
| b03n06 | 10 | 10 | 15724810 | 10 | 0.02 | 81 | 153 |
| b03n16 | 10 | 10 | 15724810 | 10 | 0.02 | 82 | 155 |
| b08n16 | 10 | 10 | 15724810 | 10 | 0.022 | 84 | 165 |
| b17n09 | 10 | 10 | 15724810 | 10 | 0.019 | 78 | 139 |
| b18n01 | 10 | 10 | 15724810 | 10 | 0.019 | 79 | 140 |
| b28n11 | 10 | 10 | 15724810 | 10 | 0.02 | 80 | 141 |
| b29n03 | 10 | 10 | 15724810 | 10 | 0.02 | 87 | 142 |
| c03n13 | 10 | 10 | 15724810 | 10 | 0.02 | 87 | 142 |
| c04n05 | 10 | 10 | 15724810 | 10 | 0.02 | 86 | 143 |
| c25n15 | 10 | 10 | 15724810 | 10 | 0.022 | 92 | 151 |
| d01n08 | 10 | 10 | 15724810 | 10 | 0.019 | 79 | 141 |
| d01n18 | 10 | 10 | 15724810 | 10 | 0.019 | 82 | 145 |
| d06n18 | 10 | 10 | 15724810 | 10 | 0.019 | 80 | 145 |
| d07n10 | 10 | 10 | 15724810 | 10 | 0.019 | 79 | 141 |
| d12n10 | 10 | 10 | 15724810 | 10 | 0.019 | 79 | 143 |
| d13n02 | 10 | 10 | 15724810 | 10 | 0.019 | 79 | 140 |
| d16n17 | 10 | 10 | 15724810 | 10 | 0.02 | 81 | 145 |
| d17n09 | 10 | 10 | 15724810 | 10 | 0.019 | 79 | 140 |
| d24n11 | 10 | 10 | 15724810 | 10 | 0.02 | 81 | 143 |
| e05n03 | 10 | 10 | 15724810 | 10 | 0.02 | 77 | 148 |
| e05n13 | 10 | 10 | 15724810 | 10 | 0.02 | 78 | 146 |
| e27n05 | 10 | 10 | 15724810 | 10 | 0.019 | 82 | 138 |
| e27n15 | 10 | 10 | 15724810 | 10 | 0.019 | 82 | 138 |
| e30n11 | 10 | 10 | 15724810 | 10 | 0.02 | 83 | 138 |
| f07n02 | 10 | 10 | 15724810 | 10 | 0.018 | 89 | 122 |
| f07n12 | 10 | 10 | 15724810 | 10 | 0.018 | 89 | 123 |
| f12n12 | 10 | 10 | 15724810 | 10 | 0.02 | 92 | 137 |
| f23n17 | 10 | 10 | 15724810 | 10 | 0.02 | 79 | 150 |
| f24n09 | 10 | 10 | 15724810 | 10 | 0.02 | 79 | 149 |
| g03n14 | 10 | 10 | 15724810 | 10 | 0.018 | 88 | 129 |
| g04n06 | 10 | 10 | 15724810 | 10 | 0.018 | 87 | 128 |
| g09n06 | 10 | 10 | 15724810 | 10 | 0.019 | 85 | 127 |
| g09n16 | 10 | 10 | 15724810 | 10 | 0.018 | 87 | 127 |
| g14n16 | 10 | 10 | 15724810 | 10 | 0.018 | 87 | 128 |
| g15n08 | 10 | 10 | 15724810 | 10 | 0.018 | 88 | 128 |
| g20n08 | 10 | 10 | 15724810 | 10 | 0.019 | 80 | 141 |
| g20n18 | 10 | 10 | 15724810 | 10 | 0.019 | 81 | 142 |
| g25n18 | 10 | 10 | 15724810 | 10 | 0.019 | 79 | 142 |
| g26n10 | 10 | 10 | 15724810 | 10 | 0.019 | 79 | 142 |
| h25n02 | 10 | 10 | 15724810 | 10 | 0.018 | 93 | 126 |
| h25n12 | 10 | 10 | 15724810 | 10 | 0.018 | 93 | 127 |
| h30n12 | 10 | 10 | 15724810 | 10 | 0.018 | 93 | 126 |
| h31n04 | 10 | 10 | 15724810 | 10 | 0.018 | 93 | 127 |
| h36n04 | 10 | 10 | 15724810 | 10 | 0.021 | 94 | 151 |
| h36n14 | 10 | 10 | 15724810 | 10 | 0.019 | 93 | 129 |

---

## Dataset inventory (narrative)

*(source: `v2_research/data_audit/dataset_inventory.md`)*

## GLASSCHIP-V2 — Phase V2-1: Dataset Acquisition & Verification Record

**Task:** independently verify the primary V2 candidate (Frontier Energy
dataset) and any alternatives, against the V2 requirement.

**V2 requirement (from the audit):** to make the V1 20 s residual learnable,
a dataset must supply, *at the node/processor level*, at least one of:
1. a **measured coolant/thermal boundary temperature** co-located with the
   processor it cools, and/or
2. **temporal resolution finer than 20 s** with 1 °C-or-better temperature,
co-located with per-processor **temperature and power**.

**Method:** primary sources only (Nature, PubMed, OSTI, figshare). Full text
was paywalled/JS-gated; findings rest on three independent abstract sources
that agree. Nothing below is inferred from column names or the prior audit's
metadata (which was explicitly not trusted).

---

### Candidate 1 — Frontier Energy Dataset (the audit's PRIMARY candidate)

| Field | Value |
|---|---|
| Paper | Sun, J., Gao, Z., Grant, D. *et al.* "Energy dataset of Frontier supercomputer for waste heat recovery" |
| Venue | *Scientific Data* 11, 1077 (2024) |
| Paper DOI | `10.1038/s41597-024-03913-w` |
| Dataset | "Frontier HPC & Facility Data", figshare `10.6084/m9.figshare.24391240.v4` |
| Mirrors | OSTI `2483448`; PubMed `39362911` |
| Access | **Open** (figshare) — *accessible* |
| Hardware | Frontier (ORNL), AMD EPYC + 4× MI250X per node, 100 % direct liquid cooling, 3 cascaded fluid loops |

#### What the dataset actually contains (verified from 3 abstracts)

- Supercomputer **total power** demand
- Accessory **cooling-system power** demand
- **PUE** (power usage effectiveness)
- **Waste heat** — overall and from the **three cooling subloops**
- **Coolant flow and temperature profiles** at **cooling-loop (facility) level**

#### What it does NOT contain

- ❌ per-node / per-blade CPU or GPU temperature
- ❌ per-node power
- ❌ per-node utilisation or frequency
- ❌ a coolant temperature co-located with an individual processor

#### Verdict: ✗ UNSUITABLE

**The dataset is facility/cooling-loop level, not per-node processor
telemetry.** Its purpose is waste-heat recovery — inherently a facility
concern. This is the **same granularity of coolant boundary that M100 already
had** (M100's `schneider_pub`/`logics_pub` facility loops), which V1 could not
attribute to nodes. It therefore does **not** fix either V2 root cause at the
node level.

**Note on the prior audit's error:** the V2 audit described Frontier as having
"per-blade coolant inlet/outlet measurements in each blade." That describes
Frontier's **physical architecture** (what the machine has), taken from a
generic search snippet — **not the contents of this dataset**. The instruction
to independently verify caught this. Corrected here.

---

### Candidate 2 — NLR HPC Eagle GPU Node Metrics

| Field | Value |
|---|---|
| Source | OSTI `3015213` |
| Contents | Ganglia node metrics + iLO power, **6** Eagle GPU nodes (2 CPU + 2 GPU each), 2019–2024, compressed CSV |
| Coolant boundary | ❌ not confirmed |
| Fine-res per-core temperature | ❌ Ganglia-level (coarse), like M100's ganglia plugin |
| Fleet size | 6 nodes |

**Verdict: ✗ UNSUITABLE.** Ganglia + iLO is the *same class* of coarse
utilisation/power telemetry M100 already provides (and which V1 excluded /
V2-audit tested as unhelpful). No node-level coolant boundary; no evidence of
sub-20 s per-core temperature. Six nodes is not a fleet.

---

### Candidate 3 — UCR Commercial Thermal-Map Dataset

| Field | Value |
|---|---|
| Source | github.com/sheldonucr/commercial_thermal_map_dataset; MLCAD 2024 |
| Contents | IR **thermal maps** of commercial CPUs/GPUs/TPU |
| Access | samples on GitHub; full data **"upon request"**; pickle format; no license |

**Verdict: ✗ UNSUITABLE.** Provides spatial temperature but **no measured
coolant boundary** and no co-located node power at HPC scale; access is gated
and the format is a security/reproducibility liability. Addresses a different
gap (spatial field) than the V2 root causes.

---

### Candidate 4 — Consumer CPU Stress Dataset (25 Hz)

| Field | Value |
|---|---|
| Source | IEEE DataPort `10.21227/95m0-wj49` (2025) |
| Contents | 1 mobile i7, thermocouples + 25 Hz IR + DTS |
| Access | **IEEE DataPort subscription** (paywalled) |

**Verdict: ✗ UNSUITABLE for V2's HPC question.** It *does* fix temporal
resolution (25 Hz) and gives a measured surface boundary — but it is **one
consumer device**, **paywalled**, no fleet, no HPC liquid-cooling boundary. It
could serve a *different* micro-study, not the fleet-scale V2 question.

---

### Phase V2-1 Conclusion

**No accessible public dataset provides node-level, co-located per-processor
temperature + power + a measured coolant boundary at finer-than-20 s
resolution.** The audit's primary candidate (Frontier) is verified accessible
but **facility-level**, and does not address either root cause at the node
level. All alternatives fail on granularity, access, or fleet scale.

**Structural audit (schema/sampling/quality) was intentionally NOT performed**:
acquisition already determined the primary candidate cannot answer the V2
question, so auditing its internal structure would not change the verdict.
This is a legitimate early stop (master prompt §20), not an omission.

**Consequence:** GATE V2-α (the observability experiment on richer data)
**cannot be executed** — there is no suitable richer dataset to run it on. See
`reports/PHASE_V2_ALPHA_REPORT.md` and `reports/V2_DECISION.md`.
