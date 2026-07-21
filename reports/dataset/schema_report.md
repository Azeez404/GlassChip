# M100 ExaData — Schema Report
**GLASSCHIP-V1 | Task 3: Schema Analysis | 2026-07-21**

---

## 1. File Format

- Format: Apache Parquet (.parquet)
- Compression: zstd per-column, embedded in Parquet
- Partitioning: year_month / plugin / metric / a_0.parquet
- Total files (21-03): 338 across 5 plugins, 338 metrics

---

## 2. Universal 3-Column Schema

| Column | Type | Description |
|---|---|---|
| timestamp | Int64 (Unix epoch, seconds) | Observation timestamp, 1-second precision |
| node | Int64 | Anonymised node ID (random integer; stability unverified across records) |
| [metric_name] | Float64 / Int64 | Observed value; column name = metric name |

---

## 3. Sample Schema — ipmi_pub/p0_power/a_0.parquet

| Column | Type | Nulls | Sample Values |
|---|---|---|---|
| `timestamp` | `Datetime(time_unit='ms', time_zone='UTC')` | 0 (0.0%) | [datetime.datetime(2021, 3, 1, 2, 28, tzinfo=zoneinfo.ZoneInfo(key='UTC')), datetime.datetime(2021, 3, 1, 2, 28, 20, tzinfo=zoneinfo.ZoneInfo(key='UTC')), datetime.datetime(2021, 3, 1, 2, 28, 40, tzinfo=zoneinfo.ZoneInfo(key='UTC'))] |
| `value` | `Int32` | 0 (0.0%) | [60, 60, 66] |
| `node` | `String` | 0 (0.0%) | ['105', '105', '105'] |

- Rows: 10,699,612 if df_s is not None else 'N/A'
- Unique nodes: 980

---

## 4. Timestamp Analysis

| Property | Value |
|---|---|
| Column | timestamp |
| Type | Int64 (Unix epoch) |
| Unit | ms |
| Start | 2021-03-01 00:00:00 |
| End | 2021-03-30 14:53:40 |
| Range (days) | 29.620601851851852 |
| **Median sampling interval** | **0.0 s** |
| Precision (paper) | 1 second |

GATE A: interval = 0.0 s → PASS (Cth feasible from transients)

---

## 5. Node Identifier

| Property | Value |
|---|---|
| Column | node |
| Type | Int64 |
| Anonymised | Yes |
| Unique nodes (21-03) | 980 |
| Sample IDs | ['0', '1', '10', '100', '101'] |
| Cross-record stability | UNVERIFIED — GATE B open |

---

## 6. Feature Classification

**ipmi_pub Numerical (Float64)**:
Temperature: p0_core[0-23]_temp, p1_core[0-23]_temp, dimm[0-15]_temp,
             gpu[0,1,3,4]_core_temp, gpu[0,1,3,4]_mem_temp, ambient, p0_vdd_temp, p1_vdd_temp
Power: p0_power, p1_power, total_power, p0_mem_power, p1_mem_power, p0_io_power, p1_io_power,
       fan_disk_power, ps0_input_power, ps1_input_power, gv100card[0,1,3,4]
Fan: fan0_0, fan0_1, fan1_0, fan1_1, fan2_0, fan2_1, fan3_0, fan3_1
PSU: ps0_input_voltag, ps1_input_voltag, ps0_output_volta, ps1_output_volta,
     ps0_output_curre, ps1_output_curre

**ganglia_pub Numerical**: cpu_user/idle/system/nice/wio/steal/aidle (%), cpu_speed (MHz),
load_one/five/fifteen, mem_free/total/buffers/cached/shared (kB), bytes_in/out, pkts_in/out

**ganglia_pub Categorical**: machine_type, os_name, os_release, gexec

**nagios_pub**: state (Int: 0=OK,1=WARN,2=CRIT,3=UNKNOWN)

**logics_pub Numerical**: Pue, Dcie, Mw, Mwh, Corrente*, Tensione, Frequenza, Potenza*, Tot*

**schneider_pub Numerical**: Temp_mandata, Temp_ritorno, Delta_temp (°C),
Portata_1/2 (L/min), Pos_valvola*/Posizione_ty* (%), Out_pid_pompe/val (%), Set_temperatura

**schneider_pub Boolean/Status**: All Alm_*, P10*_fault, P10*_in_marcia, Status_*, Stato_*

---

## 7. Null Value Analysis (IPMI Key Metrics — 21-03)

| Metric | Rows | Null % | Status |
|---|---|---|---|
| `p0_core0_temp` | 4,348,914 | 0.0% | Good |
| `p0_core1_temp` | 4,348,914 | 0.0% | Good |
| `p0_core2_temp` | 5,499,185 | 0.0% | Good |
| `p0_core3_temp` | 5,499,184 | 0.0% | Good |
| `p0_core4_temp` | 6,644,079 | 0.0% | Good |
| `p0_core5_temp` | 6,644,079 | 0.0% | Good |
| `p0_core6_temp` | 7,174,556 | 0.0% | Good |
| `p0_core7_temp` | 7,174,555 | 0.0% | Good |
| `p0_core8_temp` | 7,841,629 | 0.0% | Good |
| `p0_core9_temp` | 7,841,630 | 0.0% | Good |
| `p0_core10_temp` | 7,875,100 | 0.0% | Good |
| `p0_core11_temp` | 7,875,101 | 0.0% | Good |
| `p0_core12_temp` | 7,752,453 | 0.0% | Good |
| `p0_core13_temp` | 7,752,450 | 0.0% | Good |
| `p0_core14_temp` | 7,641,178 | 0.0% | Good |
| `p0_core15_temp` | 7,641,180 | 0.0% | Good |
| `p0_core16_temp` | 7,444,982 | 0.0% | Good |
| `p0_core17_temp` | 7,444,981 | 0.0% | Good |
| `p0_core18_temp` | 7,623,665 | 0.0% | Good |
| `p0_core19_temp` | 7,623,665 | 0.0% | Good |
| `p0_core20_temp` | 7,925,515 | 0.0% | Good |
| `p0_core21_temp` | 7,925,515 | 0.0% | Good |
| `p0_core22_temp` | 7,830,519 | 0.0% | Good |
| `p0_core23_temp` | 7,830,517 | 0.0% | Good |
| `p1_core0_temp` | 4,019,844 | 0.0% | Good |
| `p1_core1_temp` | 4,019,844 | 0.0% | Good |
| `p1_core2_temp` | 5,435,647 | 0.0% | Good |
| `p1_core3_temp` | 5,435,648 | 0.0% | Good |
| `p1_core4_temp` | 6,234,240 | 0.0% | Good |
| `p1_core5_temp` | 6,234,241 | 0.0% | Good |
| `p1_core6_temp` | 7,473,241 | 0.0% | Good |
| `p1_core7_temp` | 7,473,242 | 0.0% | Good |
| `p1_core8_temp` | 7,456,131 | 0.0% | Good |
| `p1_core9_temp` | 7,456,132 | 0.0% | Good |
| `p1_core10_temp` | 8,047,981 | 0.0% | Good |
| `p1_core11_temp` | 8,047,981 | 0.0% | Good |
| `p1_core12_temp` | 7,875,080 | 0.0% | Good |
| `p1_core13_temp` | 7,875,080 | 0.0% | Good |
| `p1_core14_temp` | 8,042,698 | 0.0% | Good |
| `p1_core15_temp` | 8,042,696 | 0.0% | Good |
| `p1_core16_temp` | 7,564,772 | 0.0% | Good |
| `p1_core17_temp` | 7,564,772 | 0.0% | Good |
| `p1_core18_temp` | 7,648,815 | 0.0% | Good |
| `p1_core19_temp` | 7,648,813 | 0.0% | Good |
| `p1_core20_temp` | 7,925,762 | 0.0% | Good |
| `p1_core21_temp` | 7,925,762 | 0.0% | Good |
| `p1_core22_temp` | 7,877,519 | 0.0% | Good |
| `p1_core23_temp` | 7,877,521 | 0.0% | Good |
| `p0_power` | 10,699,612 | 0.0% | Good |
| `p1_power` | 10,699,605 | 0.0% | Good |
| `total_power` | 10,699,572 | 0.0% | Good |
| `p0_mem_power` | 10,699,639 | 0.0% | Good |
| `p1_mem_power` | 10,699,630 | 0.0% | Good |
| `p0_io_power` | 10,699,658 | 0.0% | Good |
| `p1_io_power` | 10,699,649 | 0.0% | Good |
| `ambient` | 10,710,830 | 0.0% | Good |
| `p0_vdd_temp` | 10,722,227 | 0.0% | Good |
| `p1_vdd_temp` | 10,722,214 | 0.0% | Good |
| `fan0_0` | 10,722,272 | 0.0% | Good |
| `fan0_1` | 10,722,254 | 0.0% | Good |
| `fan1_0` | 10,711,082 | 0.0% | Good |
| `fan1_1` | 10,711,039 | 0.0% | Good |
| `fan2_0` | 10,722,196 | 0.0% | Good |
| `fan2_1` | 10,722,185 | 0.0% | Good |
| `fan3_0` | 10,722,176 | 0.0% | Good |
| `fan3_1` | 10,710,997 | 0.0% | Good |
| `ps0_input_power` | 10,722,068 | 0.0% | Good |
| `ps1_input_power` | 10,710,889 | 0.0% | Good |
| `ps0_input_voltag` | 10,722,039 | 0.0% | Good |
| `ps1_input_voltag` | 10,710,868 | 0.0% | Good |
| `fan_disk_power` | 10,699,677 | 0.0% | Good |
| `gpu0_core_temp` | 10,700,097 | 0.0% | Good |
| `gpu0_mem_temp` | 10,700,056 | 0.0% | Good |
| `gpu1_core_temp` | 10,700,060 | 0.0% | Good |
| `gpu1_mem_temp` | 10,700,028 | 0.0% | Good |
| `gpu3_core_temp` | 10,699,996 | 0.0% | Good |
| `gpu3_mem_temp` | 10,699,953 | 0.0% | Good |
| `gpu4_core_temp` | 10,699,945 | 0.0% | Good |
| `gpu4_mem_temp` | 10,699,906 | 0.0% | Good |

---

## 8. Known Issues

1. GPU index gap: indices 0,1,3,4 — index 2 absent
2. PSU column truncation: ps0_input_voltag, ps0_output_volta, ps0_output_curre (20-char EXAMON limit)
3. Schema drift: 934-day campaign — metrics added/removed across records
4. Italian Schneider names: mandata=supply, ritorno=return, portata=flow
5. Nagios largely stripped by anonymisation — only state metric remains


---

## ADDENDUM — Confirmed Real Schema (post-execution)

| Column | Confirmed Type | Notes |
|---|---|---|
| timestamp | Datetime(time_unit='ms', time_zone='UTC') | Polars Datetime, NOT Int64 |
| value | Int32 | Integer-encoded sensor value |
| node | String | String representation of integer ('0'..'979') |

Special cases:
- **Schneider PLC files**: use `panel` (String: 'Q101','Q102') instead of `node` — datacenter-level sensor
- **Schneider Temp_mandata, Temp_ritorno, Delta_temp**: value / 10 = actual degC
- **IPMI, Ganglia, Logics**: value is direct physical unit (W, degC, %, RPM, etc.)

Confirmed sampling interval:
- GATE A (per-node, p0_power): 20.0 s — PASS
