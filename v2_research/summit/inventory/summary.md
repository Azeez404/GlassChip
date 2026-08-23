# Summit dataset - inventory summary

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

## Suspicious anomalies (items 15-16)

- **Conflicting duplicate timestamps**: 58 hosts have duplicate timestamps, and (verified per host) the large majority are same-timestamp rows with *different* sensor payloads, not exact copies. Downstream preprocessing must apply a documented de-duplication/resolution rule; do NOT blind-drop. See `integrity_report.md`.
- **Mixed float dtypes**: 38 hosts store some temperature columns as Float64 in some files and Float32 in others (column names are otherwise identical fleet-wide). Unify dtype on load.
- **Partial/overlapping day files**: many day files hold fewer than 8640 rows (partial days) and some ranges overlap at day boundaries; missing calendar days are expected (5 collection months, not continuous).

See `schema_report.md`, `sampling_report.md`, `integrity_report.md`, and `dataset_inventory.{json,csv}` for detail. Per-host timestamp ranges are in the CSV/JSON.