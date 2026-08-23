"""One-node and two-node lumped thermal models for a GPU die and its HBM.

Physical picture, in plain terms
--------------------------------
The GPU die turns electrical power into heat. Some of that heat leaves to the
coolant. Some flows sideways into the HBM memory stacks sitting on the same
package. The HBM also loses heat to the coolant. Two connected buckets of heat,
one of them filled by the die's power.

Continuous equations
--------------------
    C_g dTg/dt = P - (Tg - Ta)/R_g - (Tg - Tm)/R_gm      die
    C_m dTm/dt =     (Tg - Tm)/R_gm - (Tm - Ta)/R_m      HBM

Discretised at dt with forward Euler and reparameterised so every coefficient is
a positive rate:

    dTg = dt * ( a_g*P - b_g*(Tg - Ta_g) - c_g*(Tg - Tm) )
    dTm = dt * ( c_m*(Tg - Tm) - b_m*(Tm - Ta_m) )

    a_g = 1/C_g          heating per watt
    b_g = 1/(R_g C_g)    die-to-coolant rate      1/b_g = die time constant
    c_g = 1/(R_gm C_g)   die-to-HBM rate seen by the die
    c_m = 1/(R_gm C_m)   die-to-HBM rate seen by the HBM  <-- THE COUPLING TERM
    b_m = 1/(R_m C_m)    HBM-to-coolant rate
    Ta   = effective coolant temperature

MODEL A (one-node, no coupling) drops c_g and c_m; the HBM is then driven by
power alone, exactly as the die is. Both models therefore see the SAME
measurements; Model B differs only by allowing the HBM to exchange heat with the
die.

MODEL C (unconstrained control) lets Tg enter the HBM equation with a free
coefficient rather than as the physical difference (Tg - Tm). It separates "Tg
carries information" from "the physical coupling form is the right description".

All models are linear in their parameters, so ordinary least squares is exact and
no iterative optimisation is involved.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def _ols(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float]:
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coef, float(np.linalg.cond(X))


@dataclass
class FitReport:
    params: dict
    cond: dict
    admissible: bool
    violations: list = field(default_factory=list)


class OneNodeModel:
    """MODEL A. Die and HBM each driven by power only; no coupling."""

    name = "one-node"

    def __init__(self, dt: float = 10.0) -> None:
        self.dt = dt
        self.report_: FitReport | None = None

    def fit(self, d) -> "OneNodeModel":
        P, Tg, Tm = d.P.to_numpy(float), d.Tg.to_numpy(float), d.Tm.to_numpy(float)
        one = np.ones_like(P)
        Xg = np.column_stack([P, Tg, one])
        Xm = np.column_stack([P, Tm, one])
        cg, kg = _ols(Xg, d.dTg.to_numpy(float))
        cm, km = _ols(Xm, d.dTm.to_numpy(float))
        a_g, b_g = cg[0] / self.dt, -cg[1] / self.dt
        a_m, b_m = cm[0] / self.dt, -cm[1] / self.dt
        p = dict(a_g=a_g, b_g=b_g, Ta_g=(cg[2] / self.dt / b_g) if b_g else np.nan,
                 a_m=a_m, b_m=b_m, Ta_m=(cm[2] / self.dt / b_m) if b_m else np.nan,
                 tau_g=(1 / b_g) if b_g > 0 else np.nan,
                 tau_m=(1 / b_m) if b_m > 0 else np.nan)
        v = [k for k, ok in {"a_g>0": a_g > 0, "b_g>0": b_g > 0,
                             "a_m>0": a_m > 0, "b_m>0": b_m > 0}.items() if not ok]
        self.report_ = FitReport(p, {"die": kg, "hbm": km}, not v, v)
        self._cg, self._cm = cg, cm
        return self

    def step(self, Tg: float, Tm: float, P: float) -> tuple[float, float]:
        dTg = self._cg[0] * P + self._cg[1] * Tg + self._cg[2]
        dTm = self._cm[0] * P + self._cm[1] * Tm + self._cm[2]
        return Tg + dTg, Tm + dTm


class TwoNodeModel:
    """MODEL B. Die and HBM exchange heat through a shared thermal pathway."""

    name = "two-node"

    def __init__(self, dt: float = 10.0) -> None:
        self.dt = dt
        self.report_: FitReport | None = None

    def fit(self, d) -> "TwoNodeModel":
        P, Tg, Tm = d.P.to_numpy(float), d.Tg.to_numpy(float), d.Tm.to_numpy(float)
        one = np.ones_like(P)
        # die:  dTg = dt*(a_g*P - b_g*(Tg-Ta) - c_g*(Tg-Tm))
        Xg = np.column_stack([P, Tg, Tm, one])
        # HBM:  dTm = dt*(c_m*(Tg-Tm) - b_m*(Tm-Ta))
        Xm = np.column_stack([Tg, Tm, one])
        cg, kg = _ols(Xg, d.dTg.to_numpy(float))
        cm, km = _ols(Xm, d.dTm.to_numpy(float))
        a_g = cg[0] / self.dt
        c_g = cg[2] / self.dt                 # coefficient on +Tm in the die equation
        b_g = -cg[1] / self.dt - c_g
        c_m = cm[0] / self.dt                 # coefficient on +Tg in the HBM equation
        b_m = -cm[1] / self.dt - c_m
        p = dict(a_g=a_g, b_g=b_g, c_g=c_g, c_m=c_m, b_m=b_m,
                 tau_g=(1 / b_g) if b_g > 0 else np.nan,
                 tau_m=(1 / b_m) if b_m > 0 else np.nan,
                 tau_couple=(1 / c_m) if c_m > 0 else np.nan,
                 R_gm_over_Cm=(1 / c_m) if c_m > 0 else np.nan)
        v = [k for k, ok in {"a_g>0": a_g > 0, "b_g>0": b_g > 0, "c_g>0": c_g > 0,
                             "c_m>0": c_m > 0, "b_m>0": b_m > 0}.items() if not ok]
        # discrete stability of the coupled 2x2 system
        A = np.array([[1 + cg[1], cg[2]], [cm[0], 1 + cm[1]]])
        rho = float(np.max(np.abs(np.linalg.eigvals(A))))
        p["spectral_radius"] = rho
        if rho >= 1.0:
            v.append("spectral_radius<1")
        self.report_ = FitReport(p, {"die": kg, "hbm": km}, not v, v)
        self._cg, self._cm = cg, cm
        return self

    def step(self, Tg: float, Tm: float, P: float) -> tuple[float, float]:
        dTg = self._cg[0] * P + self._cg[1] * Tg + self._cg[2] * Tm + self._cg[3]
        dTm = self._cm[0] * Tg + self._cm[1] * Tm + self._cm[2]
        return Tg + dTg, Tm + dTm


class UnconstrainedModel:
    """MODEL C (control). HBM sees P, Tg, Tm with free coefficients.

    Not a physical model. It answers: is any benefit due to the physical coupling
    structure, or merely to the die temperature being an informative regressor?
    """

    name = "unconstrained"

    def __init__(self, dt: float = 10.0) -> None:
        self.dt = dt
        self.report_: FitReport | None = None

    def fit(self, d) -> "UnconstrainedModel":
        P, Tg, Tm = d.P.to_numpy(float), d.Tg.to_numpy(float), d.Tm.to_numpy(float)
        one = np.ones_like(P)
        X = np.column_stack([P, Tg, Tm, one])
        cg, kg = _ols(X, d.dTg.to_numpy(float))
        cm, km = _ols(X, d.dTm.to_numpy(float))
        self.report_ = FitReport({"note": "no physical interpretation"},
                                 {"die": kg, "hbm": km}, True, [])
        self._cg, self._cm = cg, cm
        return self

    def step(self, Tg: float, Tm: float, P: float) -> tuple[float, float]:
        x = np.array([P, Tg, Tm, 1.0])
        return Tg + float(self._cg @ x), Tm + float(self._cm @ x)


def rollout(model, seg, horizon: int, clip: float = 60.0):
    """Free-running multi-step prediction over contiguous blocks.

    Seeded with observed temperatures at block start, then fed its own predictions.
    Only the observed future POWER is consumed. This is the fair comparison: every
    model gets the same initial condition and the same power, and must predict both
    temperatures jointly.
    """
    P = seg.P.to_numpy(float)
    Tg_o, Tm_o = seg.Tg.to_numpy(float), seg.Tm.to_numpy(float)
    n = len(seg)
    starts = range(0, n - horizon - 1, horizon)
    pg, pm, tg, tm = [], [], [], []
    for s in starts:
        Tg, Tm = Tg_o[s], Tm_o[s]
        for k in range(horizon):
            Tg, Tm = model.step(Tg, Tm, P[s + k])
            Tg = float(np.clip(Tg, -clip, 150.0))
            Tm = float(np.clip(Tm, -clip, 150.0))
            pg.append(Tg); pm.append(Tm)
            tg.append(Tg_o[s + k + 1]); tm.append(Tm_o[s + k + 1])
    return (np.array(pg), np.array(pm), np.array(tg), np.array(tm))


def one_step(model, seg):
    P = seg.P.to_numpy(float)
    Tg, Tm = seg.Tg.to_numpy(float), seg.Tm.to_numpy(float)
    pg = np.empty(len(seg)); pm = np.empty(len(seg))
    for i in range(len(seg)):
        pg[i], pm[i] = model.step(Tg[i], Tm[i], P[i])
    return pg, pm, seg.Tg_next.to_numpy(float), seg.Tm_next.to_numpy(float)
