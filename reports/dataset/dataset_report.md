# M100 ExaData — Dataset Report
**GLASSCHIP-V1 | Dataset Exploration | 2026-07-21**

---

## 1. Dataset Overview

| Property | Value |
|---|---|
| Dataset Name | M100 ExaData (CINECA Marconi100) |
| Reference | Borghesi et al., *Scientific Data* (2023), DOI 10.1038/s41597-023-02174-3 |
| Zenodo | 10.5281/zenodo.7588815 → 7590583 |
| License | CC-BY-4.0 |
| Coverage | 2020-03-09 → 2022-09-28 (934 days) |
| Nodes | 980+ |
| Total raw size | ~49.9 TB |
| Compressed | ~372 GB (Parquet + zstd) |
| Records (Zenodo) | 12–13 (one per time period) |
| Locally available | 1 record: 21-03 (March 2021) |
| Archive size | 574.0 MB (21-03.tar) |
| Extracted size | 573.5 MB |
| File format | Apache Parquet (.parquet) with zstd compression |
| Hardware | IBM POWER9 AC922, 2×POWER9 sockets, 4×NVIDIA V100, liquid-cooled |
| Monitoring | IPMI/BMC, Ganglia, Nagios, Schneider Electric PLC, Logics SCADA |

---

## 2. Folder Structure (record: 21-03)

```
datasets/21-03/
└── year_month=21-03/
    ├── plugin=ganglia_pub/     (33 metrics)   OS+CPU telemetry
    ├── plugin=ipmi_pub/        (104 metrics)  Hardware IPMI/BMC
    ├── plugin=logics_pub/      (36 metrics)   Datacenter SCADA
    ├── plugin=nagios_pub/      (1 metrics)    Service monitoring
    └── plugin=schneider_pub/   (164 metrics)  Cooling PLC
```

Partitioning: year_month / plugin / metric / a_0.parquet
- Total plugins  : 5
- Total metrics  : 338
- Total files    : 338
- Total size     : 573.5 MB (record 21-03)
- Compression    : zstd embedded in Parquet
- Schema files   : None explicit

---

## 3. Plugin Breakdown

| Plugin | Metrics | Size (MB) | Domain |
|---|---|---|---|
| ipmi_pub | 104 | 331.0 | CPU/GPU temps, power, fans, PSU |
| ganglia_pub | 33 | 221.5 | CPU utilization, memory, network, load |
| schneider_pub | 164 | 4.2 | Cooling PLC: coolant temps/flow/valves/pumps |
| logics_pub | 36 | 16.7 | Datacenter SCADA: PUE, energy, power |
| nagios_pub | 1 | 0.1 | Service state (heavily anonymised) |

---

## 4. Available Parameters

### Temperature Sensors (IPMI)
| Metric | Unit | Description |
|---|---|---|
| p0_core0_temp … p0_core23_temp | °C | POWER9 Socket 0 per-core die temperatures (24 sensors) |
| p1_core0_temp … p1_core23_temp | °C | POWER9 Socket 1 per-core die temperatures (24 sensors) |
| p0_vdd_temp / p1_vdd_temp | °C | VDD voltage regulator temperature per socket |
| dimm0_temp … dimm15_temp | °C | DIMM module temperatures (16 slots) |
| gpu0/1/3/4_core_temp | °C | NVIDIA V100 GPU die temperatures |
| gpu0/1/3/4_mem_temp | °C | V100 HBM2 memory temperatures |
| ambient | °C | Node inlet/ambient temperature |

### Power Metrics (IPMI)
| Metric | Unit | Description |
|---|---|---|
| p0_power / p1_power | W | Socket 0/1 CPU power |
| total_power | W | Total node power (all components) |
| p0_mem_power / p1_mem_power | W | Memory subsystem power per socket |
| p0_io_power / p1_io_power | W | I/O subsystem power per socket |
| fan_disk_power | W | Fan+disk combined |
| ps0_input_power / ps1_input_power | W | PSU AC input power |
| gv100card0/1/3/4 | W | GPU card power |

### Fan Speed Metrics (IPMI)
| Metric | Unit | Description |
|---|---|---|
| fan0_0, fan0_1, fan1_0, fan1_1, fan2_0, fan2_1, fan3_0, fan3_1 | RPM | Fan tachometers (8 per node) |

### CPU & OS (Ganglia)
| Metric | Unit | Description |
|---|---|---|
| cpu_user/idle/system/nice/wio/steal | % | CPU utilization breakdown |
| cpu_speed | MHz | CPU clock frequency |
| load_one/five/fifteen | dimensionless | System load averages |
| mem_free/total/buffers/cached | kB | Memory usage |
| bytes_in/out, pkts_in/out | rates | Network throughput |

### Cooling Loop (Schneider PLC)
| Metric | Unit | Description |
|---|---|---|
| Temp_mandata | °C | Coolant supply temperature |
| Temp_ritorno | °C | Coolant return temperature |
| Delta_temp | °C | Supply–return differential |
| Portata_1, Portata_2 | L/min | Coolant flow rate |
| Pos_valvola1/2 | % | Valve positions |
| Out_pid_pompe | % | Pump PID output |
| Set_temperatura | °C | Coolant setpoint |

### Infrastructure (Logics SCADA)
| Metric | Unit | Description |
|---|---|---|
| Pue | ratio | Power Usage Effectiveness |
| Dcie | ratio | Datacenter Infrastructure Efficiency |
| Mw/Mwh | MW/MWh | Power/energy consumption |
| Corrente, Corrente_L1/L2/L3 | A | 3-phase electrical current |

### PSU Voltage/Current (IPMI)
| Metric | Unit | Description |
|---|---|---|
| ps0/1_input_voltag | V | AC input voltage (~200V mains) |
| ps0/1_output_volta | V | DC output voltage |
| ps0/1_output_curre | A | DC output current |

---

## 5. Summary Statistics

### Temperature (°C)
| Metric | N | Min | P25 | Median | Mean | P75 | P95 | Max | Std |
|---|---|---|---|---|---|---|---|---|---|
| P0 Core (all 24) | 960000 | 22.0 | 41.0 | 47.0 | 49.75 | 60.0 | 67.0 | 78.0 | 11.11 |
| P1 Core (all 24) | 960000 | 21.0 | 40.0 | 45.0 | 48.77 | 60.0 | 68.0 | 85.0 | 11.61 |
| GPU (core+mem) | 320000 | 19.0 | 38.0 | 43.0 | 44.84 | 51.0 | 65.0 | 83.0 | 10.18 |
| Ambient | 10710830 | 5.0 | 19.2 | 23.6 | 22.28 | 25.6 | 28.0 | 40.8 | 4.67 |
| VDD (P0+P1) | 21422155 | 2.0 | 31.0 | 35.0 | 35.54 | 41.0 | 47.0 | 56.0 | 6.73 |
| Coolant Supply | 20486 | 172.0 | 180.0 | 182.0 | 181.48 | 183.0 | 184.0 | 203.0 | 2.0 |
| Coolant Return | 20486 | 233.0 | 240.0 | 242.0 | 242.56 | 245.0 | 246.0 | 256.0 | 2.75 |

### Power (W)
| Metric | N | Min | P25 | Median | Mean | P75 | P95 | Max | Std |
|---|---|---|---|---|---|---|---|---|---|
| P0 Socket | 10699612 | 4.0 | 44.0 | 60.0 | 86.63 | 140.0 | 170.0 | 314.0 | 51.86 |
| P1 Socket | 10699605 | 6.0 | 36.0 | 52.0 | 78.53 | 136.0 | 170.0 | 346.0 | 53.58 |
| Total Node | 10699572 | 260.0 | 540.0 | 680.0 | 707.71 | 820.0 | 1140.0 | 1980.0 | 235.27 |

### CPU Utilization
| Metric | N | Min | P25 | Median | Mean | P75 | P95 | Max | Std |
|---|---|---|---|---|---|---|---|---|---|
| CPU User % | 2622586 | 0.0 | 2.4 | 3.1 | 23.05 | 41.8 | 99.2 | 100.0 | 30.05 |
| CPU Idle % | 2622401 | 0.0 | 57.0 | 96.7 | 75.99 | 97.0 | 100.0 | 100.0 | 30.83 |
| PUE | 17111 | 1.26 | 1.38 | 1.41 | 1.41 | 1.44 | 1.49 | 1.59 | 0.04 |

---

## 6. Strengths

1. **Scale**: 980+ nodes (orders of magnitude larger than typical thermal papers)
2. **Duration**: 934 days continuous monitoring
3. **Cooling boundary conditions**: Coolant supply/return/flow rate fully measured (Schneider PLC)
4. **Socket-level power**: P0 and P1 separate — enables per-socket Rth
5. **Per-core granularity**: 48 temperature sensors per node (24 per socket)
6. **GPU telemetry**: Core + HBM temp + GPU power for all 4 cards
7. **Infrastructure context**: PUE, datacenter power, CRAC cooling SCADA
8. **PSU channels**: Voltage + current — enables energy balance cross-validation
9. **Open license**: CC-BY-4.0, permanent DOIs
10. **Efficient format**: Parquet + zstd, hive-partitioned — OOM-safe on 16 GB RAM

---

## 7. Limitations

1. Anonymised node IDs — cross-record stability unverified (GATE B)
2. No maintenance logs — Rth drift causally uninterpretable
3. Closed-loop production — no controlled excitation
4. No job scheduler data — workload type unknown
5. Schema drift expected across 934 days
6. No spatial coordinates — no PDE analysis possible
7. PSU voltage is AC input, not CPU VDD — CMOS model not directly applicable
8. GPU index 2 absent — one channel missing
9. No calibration data for IPMI sensors
10. Only 1 of 12–13 records downloaded locally

---

## 8. Observations

- The dataset's combination of thermal + power + complete cooling loop is scientifically exceptional
- Liquid cooling implies narrow temperature range — verify leakage nonlinearity detectability
- Schneider PLC enables direct Newton cooling formulation with measured boundary conditions
- PSU I×V cross-validates node power estimates
- Hive-partitioned Parquet is safe for streaming on 16 GB RAM
- Logics SCADA PUE provides datacenter-level efficiency context
