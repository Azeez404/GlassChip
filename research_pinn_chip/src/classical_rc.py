"""Model A - first-order lumped thermal model.

Plain English: the GPU turns electrical power into heat, which raises its
temperature; at the same time it loses heat to its coolant, faster the hotter it is
relative to that coolant. Temperature changes according to the balance of the two.

    C dT/dt = P - (T - T_amb)/R

Discretised at dt:

    dT[n] = dt * ( a*P[n] - b*(T[n] - T_amb) ),   a = 1/C,  b = 1/(R C)

Expanded for least squares:  dT = (dt*a) P - (dt*b) T + (dt*b*T_amb)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

DT_S = 10.0


@dataclass
class RCFit:
    a: float          # 1/C   [degC / (W s)]
    b: float          # 1/(RC) [1/s]
    T_amb: float      # fitted effective sink temperature [degC]
    tau_s: float      # 1/b, effective thermal time constant [s]
    admissible: bool  # a>0, b>0
    cond: float       # design-matrix condition number


class ClassicalRC:
    """Ordinary least squares in the physical parameterisation. Train regime only."""

    def __init__(self, dt: float = DT_S) -> None:
        self.dt = dt
        self.fit_: RCFit | None = None

    def fit(self, T: np.ndarray, P: np.ndarray, dT: np.ndarray) -> "ClassicalRC":
        X = np.column_stack([P, T, np.ones_like(T)])
        coef, *_ = np.linalg.lstsq(X, dT, rcond=None)
        c_p, c_t, c_1 = coef
        a = c_p / self.dt
        b = -c_t / self.dt
        T_amb = (c_1 / self.dt / b) if b != 0 else np.nan
        self.fit_ = RCFit(
            a=float(a), b=float(b), T_amb=float(T_amb),
            tau_s=float(1.0 / b) if b > 0 else float("nan"),
            admissible=bool(a > 0 and b > 0),
            cond=float(np.linalg.cond(X)),
        )
        return self

    def predict_dT(self, T: np.ndarray, P: np.ndarray) -> np.ndarray:
        f = self.fit_
        if f is None:
            raise RuntimeError("ClassicalRC not fitted")
        return self.dt * (f.a * P - f.b * (T - f.T_amb))
