# GLASSCHIP-V1 Thermal Behaviour Visualisation

**Scope:** answers *what does the data look like?* — never *why*.

No physical law, equation, mechanism, or parameter is named anywhere in this
module's code or output. Observations are descriptive statements about the
plotted series and nothing else.

Prototype scope: **temperature, power, fan speed**, on **one node at a
time**, defaulting to **node 15**.

---

## Architecture

```
timeseries_builder.py   (LOCKED)   model-ready per-node frame
        |
        v
visualizer.py                      ThermalVisualizer
        |
        +--> figures  ->  visualizations/*.png
        +--> observations (descriptive text + statistics)
```

Reads through the locked pipeline. Writes only PNGs and a report dict.

Libraries: `matplotlib`, `numpy`, `pandas`. Backend forced to `Agg` so
figures render headless on any platform.

---

## Quick start

```python
from visualizer import ThermalVisualizer

viz = ThermalVisualizer("datasets/21-03")

viz.plot_temperature()          # node 15 by default
viz.plot_power()
viz.plot_fan_speed()
viz.plot_temperature_vs_power()
viz.plot_temperature_vs_fan()
viz.plot_thermal_behaviour()
viz.plot_segment_boundaries()

report = viz.generate_visualization_report()
```

Every plot returns `(figure, path)`. `plot_all()` produces all seven.

Run `python visualization_example_usage.py` for a full walkthrough.

---

## Segments are never drawn as one line

Record `21-03` node 15 contains **two segments separated by 648.9 hours with
no data**:

| Segment | Duration | Samples |
|---|---|---|
| 1 | **61.978 h** | 11,157 |
| 2 | **0.044 h** | 9 |

Every time-axis figure splits into **one panel per segment**, each with its
own x-axis measured in hours *from that segment's start*. Panel widths scale
with `sqrt(duration)` so the 9-sample fragment stays visible beside the
61.978 h block. The spine facing each discontinuity is removed.

**There is one deliberate exception.** `plot_segment_boundaries()` draws a
single continuous wall-clock axis — precisely so the 27-day emptiness is
visible as emptiness.

Connecting the segments with a line would draw 27 days of data that does not
exist.

---

## Functions

| Function | Shows |
|---|---|
| `plot_temperature()` | Temperature vs time, per segment |
| `plot_power()` | Power vs time, per segment |
| `plot_fan_speed()` | Fan speed vs time, per segment |
| `plot_temperature_vs_power()` | Scatter (coloured by time) · shared timeline · cross-correlation vs lag |
| `plot_temperature_vs_fan()` | Same three panels |
| `plot_thermal_behaviour()` | All three metrics stacked on one aligned timeline |
| `plot_segment_boundaries()` | Sample occupancy on wall clock · interval distribution |
| `generate_visualization_report()` | Statistics, segments, relationships, observations |
| `plot_all()` | All seven figures |

All accept `node=`, `save=`, `filename=`.

Relationship plots use the **longest segment only**, since cross-correlation
across a 27-day gap is meaningless.

---

## Measured on node 15

```
segments      1: 61.978 h, 11157 samples   |   2: 0.044 h, 9 samples
temperature   41.0 - 53.0 degC   std 0.91    13 distinct values
power         32.0 - 72.0 W      std 1.73    12 distinct values
fan_speed     4300 - 4400 RPM    std 28.85    2 distinct values
```

| Pair | Pearson r | Peak &#124;r&#124; | Peak lag |
|---|---|---|---|
| power → temperature | 0.3806 | 0.3842 | **20 s** |
| temperature → fan_speed | −0.0198 | 0.0348 | not reported |
| power → fan_speed | 0.0088 | 0.0382 | not reported |

---

## ⚠️ Node 15 is among the quietest nodes available

The locked default is a near-idle node. For context, other common nodes:

| node | T_std | P_std | fan uniques | corr(P,T) |
|---|---|---|---|---|
| **15 (default)** | **0.91** | **1.73** | **2** | 0.381 |
| 1 | 1.86 | 1.49 | 3 | 0.579 |
| 55 | 4.66 | 28.04 | 18 | 0.747 |
| 59 | 8.32 | 45.69 | 13 | 0.926 |
| 99 | 10.65 | 55.93 | **27** | **0.955** |

On node 15 **fan speed takes only two values** (4300 / 4400 RPM), so its
plots are near-flat and its correlations are indistinguishable from scatter.
This is a property of the node, not of the plotting.

The report states this plainly rather than presenting flat lines as though
they were the phenomenon. `node=` accepts any of the 394 common nodes.

---

## Honesty rules enforced in code

**1. Lag claims are withheld below `MIN_REPORTABLE_CORRELATION = 0.2`.**

A cross-correlation peak on |r| = 0.03 is noise. Reporting *"changes in fan
speed appear later than changes in temperature"* on that basis would
manufacture a temporal claim the data does not support. Below the threshold
the report says so explicitly; the numeric lag is still returned.

**2. The interval histogram verifies its own bin coverage.**

`np.logspace(log10(min), ...)` produces a first edge fractionally *above*
`min` in floating point. On node 15 that silently dropped **11,164 of 11,165
intervals** — the plot showed only the 27-day gap and hid 99.99 % of the
data. Bin edges are now padded outwards and the sample count is asserted
before drawing; a mismatch raises `VisualizationError` rather than
rendering a misleading distribution.

**3. Near-constant and low-cardinality series are flagged**
(`NEAR_CONSTANT_STD = 1.0`, `LOW_CARDINALITY_THRESHOLD = 5`), because they
constrain what any later analysis can show.

---

## Observation vocabulary

Permitted — descriptive:

- *"2 temporal segments present: segment 1 spans 61.978 h with 11157 samples."*
- *"No samples exist for 648.9 h between segment 1 and segment 2."*
- *"fan_speed takes only 2 distinct values on this node."*
- *"Correlation between power and temperature is larger at a lag of 20 s than at zero lag; changes in temperature appear later than changes in power."*

Forbidden — explanatory:

- ~~"Thermal capacitance causes the delay."~~
- ~~"Fan behaviour follows Newton's law of cooling."~~
- ~~"R_th can now be estimated."~~

Those belong to later modules. This module reports the observation and
stops.

---

## Limitations

1. **Single node.** No fleet plots, no dashboards, no aggregation across
   nodes.
2. **Three metrics only.** CPU utilisation, frequency, and GPU metrics are
   out of prototype scope.
3. **Correlation is not association in any stronger sense.** The lag panels
   measure temporal co-movement in observational, closed-loop telemetry.
   Nothing here supports a causal reading.
4. **Quantisation is visible and real.** Temperature is recorded in 1 °C
   steps, power in ~2 W steps. The scatter grid is the sensor, not the
   plotting.
5. **62 hours, not a month.** Segment 1 is the only substantial run.
6. **The 9-sample fragment is retained** and given its own panel. It is real
   data.

---

## Not implemented, by rule

Dash · Streamlit · Plotly · web apps · interactive interfaces · publication
or conference figures · fleet-wide dashboards · model overlays · fitted
curves · physical annotations · trend lines · smoothing · any explanatory
text.
