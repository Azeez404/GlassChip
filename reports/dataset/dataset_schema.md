# M100 ExaData — Dataset Schema
**GLASSCHIP-V1 | Task 3: Complete Schema | 2026-07-21**

## Universal Schema (every .parquet file)

```
timestamp : Int64   (Unix epoch, seconds)
node      : Int64   (anonymised node ID)
<metric>  : Float64 (value; column name = metric name)
```

## Raw Schema — p0_power (sample)

```
Schema: Schema({'timestamp': Datetime(time_unit='ms', time_zone='UTC'), 'value': Int32, 'node': String})

First 5 rows:
shape: (5, 3)
┌─────────────────────────┬───────┬──────┐
│ timestamp               ┆ value ┆ node │
│ ---                     ┆ ---   ┆ ---  │
│ datetime[ms, UTC]       ┆ i32   ┆ str  │
╞═════════════════════════╪═══════╪══════╡
│ 2021-03-01 02:28:00 UTC ┆ 60    ┆ 105  │
│ 2021-03-01 02:28:20 UTC ┆ 60    ┆ 105  │
│ 2021-03-01 02:28:40 UTC ┆ 66    ┆ 105  │
│ 2021-03-01 02:29:00 UTC ┆ 60    ┆ 105  │
│ 2021-03-01 02:29:20 UTC ┆ 60    ┆ 105  │
└─────────────────────────┴───────┴──────┘
```

## Complete Metric Inventory (record: 21-03)

### plugin=ipmi_pub (104 metrics)
- `ambient` — 4.87 MB
- `dimm0_temp` — 1.76 MB
- `dimm10_temp` — 1.47 MB
- `dimm11_temp` — 1.58 MB
- `dimm12_temp` — 1.49 MB
- `dimm13_temp` — 1.55 MB
- `dimm14_temp` — 1.55 MB
- `dimm15_temp` — 1.39 MB
- `dimm1_temp` — 1.74 MB
- `dimm2_temp` — 1.69 MB
- `dimm3_temp` — 1.44 MB
- `dimm4_temp` — 1.81 MB
- `dimm5_temp` — 1.47 MB
- `dimm6_temp` — 1.55 MB
- `dimm7_temp` — 1.44 MB
- `dimm8_temp` — 1.76 MB
- `dimm9_temp` — 1.51 MB
- `fan0_0` — 2.78 MB
- `fan0_1` — 2.10 MB
- `fan1_0` — 3.13 MB
- `fan1_1` — 2.17 MB
- `fan2_0` — 3.31 MB
- `fan2_1` — 2.34 MB
- `fan3_0` — 3.20 MB
- `fan3_1` — 2.44 MB
- `fan_disk_power` — 6.06 MB
- `gpu0_core_temp` — 3.28 MB
- `gpu0_mem_temp` — 3.91 MB
- `gpu1_core_temp` — 3.47 MB
- `gpu1_mem_temp` — 4.09 MB
- `gpu3_core_temp` — 3.08 MB
- `gpu3_mem_temp` — 3.68 MB
- `gpu4_core_temp` — 3.27 MB
- `gpu4_mem_temp` — 4.06 MB
- `gv100card0` — 0.75 MB
- `gv100card1` — 1.00 MB
- `gv100card3` — 0.67 MB
- `gv100card4` — 0.71 MB
- `p0_core0_temp` — 2.23 MB
- `p0_core10_temp` — 3.43 MB
- `p0_core11_temp` — 3.63 MB
- `p0_core12_temp` — 3.67 MB
- `p0_core13_temp` — 3.49 MB
- `p0_core14_temp` — 3.45 MB
- `p0_core15_temp` — 3.59 MB
- `p0_core16_temp` — 3.49 MB
- `p0_core17_temp` — 3.39 MB
- `p0_core18_temp` — 3.52 MB
- `p0_core19_temp` — 3.32 MB
- `p0_core1_temp` — 2.28 MB
- `p0_core20_temp` — 3.65 MB
- `p0_core21_temp` — 3.58 MB
- `p0_core22_temp` — 3.56 MB
- `p0_core23_temp` — 3.31 MB
- `p0_core2_temp` — 2.83 MB
- `p0_core3_temp` — 2.80 MB
- `p0_core4_temp` — 3.15 MB
- `p0_core5_temp` — 3.25 MB
- `p0_core6_temp` — 3.38 MB
- `p0_core7_temp` — 3.49 MB
- `p0_core8_temp` — 3.52 MB
- `p0_core9_temp` — 3.64 MB
- `p0_io_power` — 5.81 MB
- `p0_mem_power` — 4.51 MB
- `p0_power` — 7.59 MB
- `p0_vdd_temp` — 3.10 MB
- `p1_core0_temp` — 2.04 MB
- `p1_core10_temp` — 3.58 MB
- `p1_core11_temp` — 3.54 MB
- `p1_core12_temp` — 3.63 MB
- `p1_core13_temp` — 3.68 MB
- `p1_core14_temp` — 3.79 MB
- `p1_core15_temp` — 3.69 MB
- `p1_core16_temp` — 3.40 MB
- `p1_core17_temp` — 3.21 MB
- `p1_core18_temp` — 3.24 MB
- `p1_core19_temp` — 3.39 MB
- `p1_core1_temp` — 2.03 MB
- `p1_core20_temp` — 3.70 MB
- `p1_core21_temp` — 3.51 MB
- `p1_core22_temp` — 3.75 MB
- `p1_core23_temp` — 3.63 MB
- `p1_core2_temp` — 2.61 MB
- `p1_core3_temp` — 2.60 MB
- `p1_core4_temp` — 3.08 MB
- `p1_core5_temp` — 3.09 MB
- `p1_core6_temp` — 3.41 MB
- `p1_core7_temp` — 3.66 MB
- `p1_core8_temp` — 3.59 MB
- `p1_core9_temp` — 3.31 MB
- `p1_io_power` — 5.71 MB
- `p1_mem_power` — 3.93 MB
- `p1_power` — 7.30 MB
- `p1_vdd_temp` — 3.17 MB
- `pcie` — 2.15 MB
- `ps0_input_power` — 5.46 MB
- `ps0_input_voltag` — 2.30 MB
- `ps0_output_curre` — 6.87 MB
- `ps0_output_volta` — 1.52 MB
- `ps1_input_power` — 5.30 MB
- `ps1_input_voltag` — 2.52 MB
- `ps1_output_curre` — 7.02 MB
- `ps1_output_volta` — 1.42 MB
- `total_power` — 6.93 MB

### plugin=ganglia_pub (33 metrics)
- `boottime` — 5.89 MB
- `bytes_in` — 7.42 MB
- `bytes_out` — 7.45 MB
- `cpu_aidle` — 4.95 MB
- `cpu_idle` — 6.05 MB
- `cpu_nice` — 4.34 MB
- `cpu_num` — 5.62 MB
- `cpu_speed` — 5.77 MB
- `cpu_steal` — 5.01 MB
- `cpu_system` — 5.78 MB
- `cpu_user` — 6.40 MB
- `cpu_wio` — 4.76 MB
- `disk_free` — 2.40 MB
- `disk_total` — 0.08 MB
- `gexec` — 1.03 MB
- `load_fifteen` — 12.61 MB
- `load_five` — 13.04 MB
- `load_one` — 13.77 MB
- `machine_type` — 5.65 MB
- `mem_buffers` — 8.82 MB
- `mem_cached` — 9.63 MB
- `mem_free` — 17.42 MB
- `mem_shared` — 8.90 MB
- `mem_total` — 5.98 MB
- `os_name` — 5.36 MB
- `os_release` — 5.92 MB
- `part_max_used` — 1.67 MB
- `pkts_in` — 6.21 MB
- `pkts_out` — 6.17 MB
- `proc_run` — 6.05 MB
- `proc_total` — 6.91 MB
- `swap_free` — 9.05 MB
- `swap_total` — 5.36 MB

### plugin=schneider_pub (164 metrics)
- `Alm_TY141` — 0.02 MB
- `PLC_PLC_Q101.Abilita_inverter` — 0.02 MB
- `PLC_PLC_Q101.Abilita_valvola1` — 0.02 MB
- `PLC_PLC_Q101.Abilita_valvola2` — 0.02 MB
- `PLC_PLC_Q101.Allarme_on` — 0.02 MB
- `PLC_PLC_Q101.Allarme_presente` — 0.02 MB
- `PLC_PLC_Q101.Alm_inverter_p101` — 0.02 MB
- `PLC_PLC_Q101.Alm_inverter_p102` — 0.02 MB
- `PLC_PLC_Q101.Alm_inverter_p103` — 0.02 MB
- `PLC_PLC_Q101.Alm_inverter_p104` — 0.02 MB
- `PLC_PLC_Q101.Alm_max_portata` — 0.02 MB
- `PLC_PLC_Q101.Alm_max_t_mandata` — 0.02 MB
- `PLC_PLC_Q101.Alm_max_t_ritorno` — 0.02 MB
- `PLC_PLC_Q101.Alm_min_portata` — 0.02 MB
- `PLC_PLC_Q101.Alm_min_t_mandata` — 0.02 MB
- `PLC_PLC_Q101.Alm_nostart_p101` — 0.02 MB
- `PLC_PLC_Q101.Alm_nostart_p102` — 0.02 MB
- `PLC_PLC_Q101.Alm_nostart_p103` — 0.02 MB
- `PLC_PLC_Q101.Alm_nostart_p104` — 0.02 MB
- `PLC_PLC_Q101.Alm_w1` — 0.02 MB
- `PLC_PLC_Q101.Cmd_valvola_1` — 0.05 MB
- `PLC_PLC_Q101.Cmd_valvola_2` — 0.05 MB
- `PLC_PLC_Q101.Delta_temp` — 0.02 MB
- `PLC_PLC_Q101.Diff_minuti_cavedio` — 0.03 MB
- `PLC_PLC_Q101.Diff_minuti_quadro` — 0.03 MB
- `PLC_PLC_Q101.Diff_minuti_sala` — 0.03 MB
- `PLC_PLC_Q101.In_marcia_p101` — 0.02 MB
- `PLC_PLC_Q101.In_marcia_p102` — 0.02 MB
- `PLC_PLC_Q101.In_marcia_p103` — 0.02 MB
- `PLC_PLC_Q101.In_marcia_p104` — 0.02 MB
- `PLC_PLC_Q101.Kp_pid_pompe` — 0.02 MB
- `PLC_PLC_Q101.Kp_pid_valvole` — 0.02 MB
- `PLC_PLC_Q101.Manuale_p101` — 0.02 MB
- `PLC_PLC_Q101.Manuale_p102` — 0.02 MB
- `PLC_PLC_Q101.Manuale_p103` — 0.02 MB
- `PLC_PLC_Q101.Manuale_p104` — 0.02 MB
- `PLC_PLC_Q101.Manuale_ty141` — 0.02 MB
- `PLC_PLC_Q101.Manuale_ty142` — 0.02 MB
- `PLC_PLC_Q101.Max_ana_out_ty141` — 0.02 MB
- `PLC_PLC_Q101.Max_ana_out_ty142` — 0.02 MB
- `PLC_PLC_Q101.Max_ana_portata1` — 0.02 MB
- `PLC_PLC_Q101.Max_ana_portata2` — 0.02 MB
- `PLC_PLC_Q101.Max_ana_pos_ty141` — 0.02 MB
- `PLC_PLC_Q101.Max_ana_pos_ty142` — 0.02 MB
- `PLC_PLC_Q101.Max_portata` — 0.02 MB
- `PLC_PLC_Q101.Max_t_mandata` — 0.02 MB
- `PLC_PLC_Q101.Max_t_ritorno` — 0.02 MB
- `PLC_PLC_Q101.Max_visi_portata2` — 0.02 MB
- `PLC_PLC_Q101.Max_visu_portata1` — 0.02 MB
- `PLC_PLC_Q101.Min_ana_out_ty141` — 0.02 MB
- `PLC_PLC_Q101.Min_ana_out_ty142` — 0.02 MB
- `PLC_PLC_Q101.Min_ana_portata1` — 0.02 MB
- `PLC_PLC_Q101.Min_ana_portata2` — 0.02 MB
- `PLC_PLC_Q101.Min_ana_pos_ty141` — 0.02 MB
- `PLC_PLC_Q101.Min_ana_pos_ty142` — 0.02 MB
- `PLC_PLC_Q101.Min_lavoro_p101` — 0.03 MB
- `PLC_PLC_Q101.Min_lavoro_p102` — 0.03 MB
- `PLC_PLC_Q101.Min_lavoro_p103` — 0.03 MB
- `PLC_PLC_Q101.Min_lavoro_p104` — 0.03 MB
- `PLC_PLC_Q101.Min_lavoro_quadro` — 0.03 MB
- `PLC_PLC_Q101.Min_out_pid_pompe` — 0.02 MB
- `PLC_PLC_Q101.Min_out_pid_valv` — 0.02 MB
- `PLC_PLC_Q101.Min_parz_p101` — 0.02 MB
- `PLC_PLC_Q101.Min_parz_p102` — 0.02 MB
- `PLC_PLC_Q101.Min_parz_p103` — 0.02 MB
- `PLC_PLC_Q101.Min_parz_p104` — 0.02 MB
- `PLC_PLC_Q101.Min_parziali_p101` — 0.03 MB
- `PLC_PLC_Q101.Min_parziali_p102` — 0.03 MB
- `PLC_PLC_Q101.Min_parziali_p103` — 0.03 MB
- `PLC_PLC_Q101.Min_parziali_p104` — 0.03 MB
- `PLC_PLC_Q101.Min_parziali_quadro` — 0.03 MB
- `PLC_PLC_Q101.Min_portata` — 0.02 MB
- `PLC_PLC_Q101.Min_t_mandata` — 0.02 MB
- `PLC_PLC_Q101.Min_vel_pompe` — 0.02 MB
- `PLC_PLC_Q101.Min_visu_portata1` — 0.02 MB
- `PLC_PLC_Q101.Min_visu_portata2` — 0.02 MB
- `PLC_PLC_Q101.Ore_lavoro_p101` — 0.03 MB
- `PLC_PLC_Q101.Ore_lavoro_p102` — 0.03 MB
- `PLC_PLC_Q101.Ore_lavoro_p103` — 0.03 MB
- `PLC_PLC_Q101.Ore_lavoro_p104` — 0.03 MB
- `PLC_PLC_Q101.Ore_parziali_p101` — 0.03 MB
- `PLC_PLC_Q101.Ore_parziali_p102` — 0.03 MB
- `PLC_PLC_Q101.Ore_parziali_p103` — 0.03 MB
- `PLC_PLC_Q101.Ore_parziali_p104` — 0.03 MB
- `PLC_PLC_Q101.Out_pid_pompe` — 0.04 MB
- `PLC_PLC_Q101.Out_pid_val` — 0.05 MB
- `PLC_PLC_Q101.P101_fault` — 0.02 MB
- `PLC_PLC_Q101.P101_in_marcia` — 0.02 MB
- `PLC_PLC_Q101.P102_fault` — 0.02 MB
- `PLC_PLC_Q101.P102_in_marcia` — 0.02 MB
- `PLC_PLC_Q101.P103_fault` — 0.02 MB
- `PLC_PLC_Q101.P103_in_marcia` — 0.02 MB
- `PLC_PLC_Q101.P104_fault` — 0.02 MB
- `PLC_PLC_Q101.P104_in_marcia` — 0.02 MB
- `PLC_PLC_Q101.Pb_arresto_p101` — 0.02 MB
- `PLC_PLC_Q101.Pb_arresto_p102` — 0.02 MB
- `PLC_PLC_Q101.Pb_arresto_p103` — 0.02 MB
- `PLC_PLC_Q101.Pb_arresto_p104` — 0.02 MB
- `PLC_PLC_Q101.Pb_marcia_p101` — 0.02 MB
- `PLC_PLC_Q101.Pb_marcia_p102` — 0.02 MB
- `PLC_PLC_Q101.Pb_marcia_p103` — 0.02 MB
- `PLC_PLC_Q101.Pb_marcia_p104` — 0.02 MB
- `PLC_PLC_Q101.Portata_1` — 0.05 MB
- `PLC_PLC_Q101.Portata_1_hmi` — 0.04 MB
- `PLC_PLC_Q101.Portata_2` — 0.05 MB
- `PLC_PLC_Q101.Portata_2_hmi` — 0.04 MB
- `PLC_PLC_Q101.Portata_attiva` — 0.04 MB
- `PLC_PLC_Q101.Pos_valvola1` — 0.04 MB
- `PLC_PLC_Q101.Pos_valvola_2` — 0.05 MB
- `PLC_PLC_Q101.Posizione_ty141` — 0.03 MB
- `PLC_PLC_Q101.Posizione_ty142` — 0.03 MB
- `PLC_PLC_Q101.Rif_auto_attivo` — 0.03 MB
- `PLC_PLC_Q101.Rif_auto_p101` — 0.02 MB
- `PLC_PLC_Q101.Rif_auto_p102` — 0.02 MB
- `PLC_PLC_Q101.Rif_auto_ty141` — 0.03 MB
- `PLC_PLC_Q101.Rif_auto_ty142` — 0.03 MB
- `PLC_PLC_Q101.Rif_inverter` — 0.03 MB
- `PLC_PLC_Q101.Rif_man_p101` — 0.02 MB
- `PLC_PLC_Q101.Rif_man_p102` — 0.02 MB
- `PLC_PLC_Q101.Rif_man_ty141` — 0.02 MB
- `PLC_PLC_Q101.Rif_man_ty142` — 0.02 MB
- `PLC_PLC_Q101.Sel_misuratore` — 0.02 MB
- `PLC_PLC_Q101.Set_man_pid_pompe` — 0.04 MB
- `PLC_PLC_Q101.Set_man_pid_valv` — 0.04 MB
- `PLC_PLC_Q101.Set_temperatura` — 0.02 MB
- `PLC_PLC_Q101.Start_impianto` — 0.02 MB
- `PLC_PLC_Q101.Start_p101` — 0.02 MB
- `PLC_PLC_Q101.Start_p102` — 0.02 MB
- `PLC_PLC_Q101.Start_p103` — 0.02 MB
- `PLC_PLC_Q101.Start_p104` — 0.02 MB
- `PLC_PLC_Q101.Stato_p101` — 0.02 MB
- `PLC_PLC_Q101.Stato_p102` — 0.02 MB
- `PLC_PLC_Q101.Stato_p103` — 0.02 MB
- `PLC_PLC_Q101.Stato_p104` — 0.02 MB
- `PLC_PLC_Q101.Stato_quadro` — 0.02 MB
- `PLC_PLC_Q101.Status_w1` — 0.02 MB
- `PLC_PLC_Q101.Status_w2` — 0.02 MB
- `PLC_PLC_Q101.T_mandata_hmi` — 0.03 MB
- `PLC_PLC_Q101.T_ritorno_hmi` — 0.03 MB
- `PLC_PLC_Q101.T_scambio_cavedio` — 0.02 MB
- `PLC_PLC_Q101.T_scambio_quadri` — 0.02 MB
- `PLC_PLC_Q101.T_scambio_sala` — 0.02 MB
- `PLC_PLC_Q101.Td_pid_pompe` — 0.02 MB
- `PLC_PLC_Q101.Td_pid_valvole` — 0.02 MB
- `PLC_PLC_Q101.Temp_mandata` — 0.03 MB
- `PLC_PLC_Q101.Temp_ritorno` — 0.03 MB
- `PLC_PLC_Q101.Ti_pid_pompe` — 0.02 MB
- `PLC_PLC_Q101.Ti_pid_valvole` — 0.02 MB
- `PLC_PLC_Q101.V_min_rem_cavedio` — 0.02 MB
- `PLC_PLC_Q101.V_min_rem_quadro` — 0.02 MB
- `PLC_PLC_Q101.V_min_rem_sala` — 0.02 MB
- `PLC_PLC_Q101.V_ore_parz_p101` — 0.02 MB
- `PLC_PLC_Q101.V_ore_parz_p102` — 0.02 MB
- `PLC_PLC_Q101.V_ore_parz_p103` — 0.02 MB
- `PLC_PLC_Q101.V_ore_parz_p104` — 0.02 MB
- `PLC_PLC_Q101.V_ore_parz_quadro` — 0.02 MB
- `PLC_PLC_Q101.V_ore_rem_cavedio` — 0.02 MB
- `PLC_PLC_Q101.V_ore_rem_quadro` — 0.02 MB
- `PLC_PLC_Q101.V_ore_rem_sala` — 0.02 MB
- `PLC_PLC_Q101.V_ore_tot_p101` — 0.02 MB
- `PLC_PLC_Q101.V_ore_tot_p102` — 0.02 MB
- `PLC_PLC_Q101.V_ore_tot_p103` — 0.02 MB
- `PLC_PLC_Q101.V_ore_tot_p104` — 0.02 MB
- `PLC_PLC_Q101.V_ore_tot_quadro` — 0.02 MB

### plugin=logics_pub (36 metrics)
- `Bad_values` — 0.00 MB
- `Comlost` — 0.00 MB
- `Corrente` — 0.80 MB
- `Corrente_L1` — 1.64 MB
- `Corrente_L2` — 1.64 MB
- `Corrente_L3` — 1.63 MB
- `Dcie` — 0.08 MB
- `Energia` — 3.02 MB
- `Fattore_di_potenza` — 1.12 MB
- `Frequenza` — 0.48 MB
- `Gateway` — 0.00 MB
- `ID_Modbus` — 0.00 MB
- `Mvar` — 0.01 MB
- `Mvarh` — 0.09 MB
- `Mw` — 0.01 MB
- `Mwh` — 0.09 MB
- `Potenza` — 1.61 MB
- `Potenza_attiva` — 1.23 MB
- `Prototype` — 0.00 MB
- `Pue` — 0.08 MB
- `Stato` — 0.85 MB
- `Status` — 0.07 MB
- `Tensione` — 0.87 MB
- `Tot` — 0.09 MB
- `Tot_cdz` — 0.07 MB
- `Tot_chiller` — 0.07 MB
- `Tot_ict` — 0.08 MB
- `Tot_qpompe` — 0.05 MB
- `Tot_servizi` — 0.01 MB
- `Volt1` — 0.23 MB
- `Volt2` — 0.25 MB
- `Volt3` — 0.23 MB
- `address` — 0.00 MB
- `deviceid` — 0.00 MB
- `pit` — 0.13 MB
- `pt` — 0.14 MB

### plugin=nagios_pub (1 metrics)
- `state` — 0.14 MB

## Null Value Assessment (IPMI Key Metrics)

| Metric | Available | Rows | Null % |
|---|---|---|---|
| `p0_core0_temp` | Yes | 4,348,914 | 0.00% |
| `p0_core1_temp` | Yes | 4,348,914 | 0.00% |
| `p0_core2_temp` | Yes | 5,499,185 | 0.00% |
| `p0_core3_temp` | Yes | 5,499,184 | 0.00% |
| `p0_core4_temp` | Yes | 6,644,079 | 0.00% |
| `p0_core5_temp` | Yes | 6,644,079 | 0.00% |
| `p0_core6_temp` | Yes | 7,174,556 | 0.00% |
| `p0_core7_temp` | Yes | 7,174,555 | 0.00% |
| `p0_core8_temp` | Yes | 7,841,629 | 0.00% |
| `p0_core9_temp` | Yes | 7,841,630 | 0.00% |
| `p0_core10_temp` | Yes | 7,875,100 | 0.00% |
| `p0_core11_temp` | Yes | 7,875,101 | 0.00% |
| `p0_core12_temp` | Yes | 7,752,453 | 0.00% |
| `p0_core13_temp` | Yes | 7,752,450 | 0.00% |
| `p0_core14_temp` | Yes | 7,641,178 | 0.00% |
| `p0_core15_temp` | Yes | 7,641,180 | 0.00% |
| `p0_core16_temp` | Yes | 7,444,982 | 0.00% |
| `p0_core17_temp` | Yes | 7,444,981 | 0.00% |
| `p0_core18_temp` | Yes | 7,623,665 | 0.00% |
| `p0_core19_temp` | Yes | 7,623,665 | 0.00% |
| `p0_core20_temp` | Yes | 7,925,515 | 0.00% |
| `p0_core21_temp` | Yes | 7,925,515 | 0.00% |
| `p0_core22_temp` | Yes | 7,830,519 | 0.00% |
| `p0_core23_temp` | Yes | 7,830,517 | 0.00% |
| `p1_core0_temp` | Yes | 4,019,844 | 0.00% |
| `p1_core1_temp` | Yes | 4,019,844 | 0.00% |
| `p1_core2_temp` | Yes | 5,435,647 | 0.00% |
| `p1_core3_temp` | Yes | 5,435,648 | 0.00% |
| `p1_core4_temp` | Yes | 6,234,240 | 0.00% |
| `p1_core5_temp` | Yes | 6,234,241 | 0.00% |
| `p1_core6_temp` | Yes | 7,473,241 | 0.00% |
| `p1_core7_temp` | Yes | 7,473,242 | 0.00% |
| `p1_core8_temp` | Yes | 7,456,131 | 0.00% |
| `p1_core9_temp` | Yes | 7,456,132 | 0.00% |
| `p1_core10_temp` | Yes | 8,047,981 | 0.00% |
| `p1_core11_temp` | Yes | 8,047,981 | 0.00% |
| `p1_core12_temp` | Yes | 7,875,080 | 0.00% |
| `p1_core13_temp` | Yes | 7,875,080 | 0.00% |
| `p1_core14_temp` | Yes | 8,042,698 | 0.00% |
| `p1_core15_temp` | Yes | 8,042,696 | 0.00% |
| `p1_core16_temp` | Yes | 7,564,772 | 0.00% |
| `p1_core17_temp` | Yes | 7,564,772 | 0.00% |
| `p1_core18_temp` | Yes | 7,648,815 | 0.00% |
| `p1_core19_temp` | Yes | 7,648,813 | 0.00% |
| `p1_core20_temp` | Yes | 7,925,762 | 0.00% |
| `p1_core21_temp` | Yes | 7,925,762 | 0.00% |
| `p1_core22_temp` | Yes | 7,877,519 | 0.00% |
| `p1_core23_temp` | Yes | 7,877,521 | 0.00% |
| `p0_power` | Yes | 10,699,612 | 0.00% |
| `p1_power` | Yes | 10,699,605 | 0.00% |
| `total_power` | Yes | 10,699,572 | 0.00% |
| `p0_mem_power` | Yes | 10,699,639 | 0.00% |
| `p1_mem_power` | Yes | 10,699,630 | 0.00% |
| `p0_io_power` | Yes | 10,699,658 | 0.00% |
| `p1_io_power` | Yes | 10,699,649 | 0.00% |
| `ambient` | Yes | 10,710,830 | 0.00% |
| `p0_vdd_temp` | Yes | 10,722,227 | 0.00% |
| `p1_vdd_temp` | Yes | 10,722,214 | 0.00% |
| `fan0_0` | Yes | 10,722,272 | 0.00% |
| `fan0_1` | Yes | 10,722,254 | 0.00% |
| `fan1_0` | Yes | 10,711,082 | 0.00% |
| `fan1_1` | Yes | 10,711,039 | 0.00% |
| `fan2_0` | Yes | 10,722,196 | 0.00% |
| `fan2_1` | Yes | 10,722,185 | 0.00% |
| `fan3_0` | Yes | 10,722,176 | 0.00% |
| `fan3_1` | Yes | 10,710,997 | 0.00% |
| `ps0_input_power` | Yes | 10,722,068 | 0.00% |
| `ps1_input_power` | Yes | 10,710,889 | 0.00% |
| `ps0_input_voltag` | Yes | 10,722,039 | 0.00% |
| `ps1_input_voltag` | Yes | 10,710,868 | 0.00% |
| `fan_disk_power` | Yes | 10,699,677 | 0.00% |
| `gpu0_core_temp` | Yes | 10,700,097 | 0.00% |
| `gpu0_mem_temp` | Yes | 10,700,056 | 0.00% |
| `gpu1_core_temp` | Yes | 10,700,060 | 0.00% |
| `gpu1_mem_temp` | Yes | 10,700,028 | 0.00% |
| `gpu3_core_temp` | Yes | 10,699,996 | 0.00% |
| `gpu3_mem_temp` | Yes | 10,699,953 | 0.00% |
| `gpu4_core_temp` | Yes | 10,699,945 | 0.00% |
| `gpu4_mem_temp` | Yes | 10,699,906 | 0.00% |
