"""Classical first-order lumped thermal baseline for GLASSCHIP-V1.

ONE model, ONE question:

    How much of the observed processor thermal behaviour can simple
    first-order thermal physics explain?

The governing physics is the lumped RC thermal equation

    C dT/dt = P - (T - T_ref)/R

Naively fitting this needs dT/dt, which at 20 s sampling and 1 degC
quantization is mostly 0 or +-0.05 degC/s -- quantization noise, not a
derivative. So this baseline does NOT differentiate. It uses the **exact
discrete-time solution** of the same equation, with power held constant
across each 20 s step:

    T[n+1] = alpha * T[n] + beta * P[n] + gamma

This is a linear ARX model fit by ordinary least squares on the recorded
values directly -- no derivative, no quantization amplification. The
continuous parameters are recovered analytically:

    tau_eff = -dt / ln(alpha)          effective time constant  [s]
    R_eff   = beta / (1 - alpha)        effective thermal gain   [degC/W]
    T_ref   = gamma / (1 - alpha)       effective reference temp [degC]
    C_eff   = tau_eff / R_eff           effective capacitance    [J/K per W?]

R_eff and C_eff are EFFECTIVE, not physical: the heat fraction reaching the
sensor (alpha_heat) is unobservable, so both absorb it. Their product
tau_eff = R_eff * C_eff is alpha_heat-independent and is the trustworthy
quantity.

This module fits and evaluates. It does not screen nodes, does not read
files, and does not learn anything beyond three linear coefficients.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

__all__ = ["ClassicalBaselineModel", "BaselineFit", "BaselineMetrics"]

#: Nominal sampling interval of the IPMI telemetry, in seconds.
DEFAULT_DT_S: float = 20.0


@dataclass
class BaselineFit:
    """Fitted parameters of the discrete first-order model."""

    alpha: float
    beta: float
    gamma: float
    dt_s: float
    n_pairs: int

    # --- recovered effective physical quantities -------------------------

    @property
    def is_stable(self) -> bool:
        """A physically valid first-order system decays: 0 < alpha < 1."""
        return 0.0 < self.alpha < 1.0

    @property
    def tau_eff_s(self) -> float:
        """Effective time constant (s). alpha_heat-independent."""
        if not self.is_stable:
            return float("nan")
        return -self.dt_s / np.log(self.alpha)

    @property
    def r_eff(self) -> float:
        """Effective thermal gain dT_ss/dP (degC/W). alpha_heat-contaminated."""
        denom = 1.0 - self.alpha
        return self.beta / denom if denom != 0 else float("nan")

    @property
    def t_ref(self) -> float:
        """Effective reference temperature (degC) = steady-state T at P=0."""
        denom = 1.0 - self.alpha
        return self.gamma / denom if denom != 0 else float("nan")

    @property
    def c_eff(self) -> float:
        """Effective capacitance proxy = tau/R. alpha_heat-contaminated."""
        r = self.r_eff
        return self.tau_eff_s / r if r not in (0.0, float("nan")) else float("nan")


@dataclass
class BaselineMetrics:
    """Evaluation of the fitted model, with honest reference baselines."""

    rmse: float
    mae: float
    r2: float
    # persistence reference: predict T[n+1] = T[n]
    persistence_rmse: float
    # honest dynamic score: R^2 on the increment T[n+1]-T[n]
    increment_r2: float
    # physics residual statistics
    residual_std: float
    residual_mean: float
    residual_lag1_autocorr: float
    n_pairs: int


class ClassicalBaselineModel:
    """Discrete-time first-order lumped thermal model, fit by OLS.

    Parameters
    ----------
    dt_s:
        Sampling interval used to convert alpha to a time constant.

    Notes
    -----
    Fitting and evaluation operate on **contiguous segments only**. A
    consecutive pair ``(T[n], T[n+1])`` that would span the 648.9 h data
    gap is never formed -- the caller passes each gap-free segment
    separately.
    """

    def __init__(self, dt_s: float = DEFAULT_DT_S) -> None:
        self.dt_s = dt_s
        self.fit_: BaselineFit | None = None

    # ------------------------------------------------------------------
    # Fitting
    # ------------------------------------------------------------------

    @staticmethod
    def _pairs(
        segments: Sequence[tuple[np.ndarray, np.ndarray]]
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Build (T[n], P[n]) -> T[n+1] pairs within each segment.

        Pairs never cross a segment boundary.
        """
        t_now, p_now, t_next = [], [], []
        for temp, power in segments:
            temp = np.asarray(temp, dtype="float64")
            power = np.asarray(power, dtype="float64")
            if len(temp) < 2:
                continue
            t_now.append(temp[:-1])
            p_now.append(power[:-1])
            t_next.append(temp[1:])
        if not t_now:
            raise ValueError("No usable consecutive pairs in any segment.")
        return (
            np.concatenate(t_now),
            np.concatenate(p_now),
            np.concatenate(t_next),
        )

    def fit(
        self, segments: Sequence[tuple[np.ndarray, np.ndarray]]
    ) -> BaselineFit:
        """Fit alpha, beta, gamma by ordinary least squares.

        Parameters
        ----------
        segments:
            One ``(temperature, power)`` array pair per contiguous segment
            of a single node.

        Returns
        -------
        BaselineFit
        """
        t_now, p_now, t_next = self._pairs(segments)
        # Design matrix [T[n], P[n], 1]; target T[n+1].
        x = np.column_stack([t_now, p_now, np.ones_like(t_now)])
        coef, *_ = np.linalg.lstsq(x, t_next, rcond=None)
        self.fit_ = BaselineFit(
            alpha=float(coef[0]),
            beta=float(coef[1]),
            gamma=float(coef[2]),
            dt_s=self.dt_s,
            n_pairs=len(t_next),
        )
        return self.fit_

    # ------------------------------------------------------------------
    # Prediction and evaluation
    # ------------------------------------------------------------------

    def predict_onestep(
        self, temp_now: np.ndarray, power_now: np.ndarray
    ) -> np.ndarray:
        """One-step-ahead prediction T_hat[n+1] = alpha T[n] + beta P[n] + gamma."""
        if self.fit_ is None:
            raise RuntimeError("Model is not fitted.")
        f = self.fit_
        return f.alpha * np.asarray(temp_now) + f.beta * np.asarray(power_now) + f.gamma

    def evaluate(
        self, segments: Sequence[tuple[np.ndarray, np.ndarray]]
    ) -> BaselineMetrics:
        """Evaluate the fitted model, with persistence and increment references.

        Returns
        -------
        BaselineMetrics

        Notes
        -----
        One-step ``R^2`` is inflated by persistence -- temperature barely
        changes in 20 s, so even ``T_hat = T[n]`` scores well. Therefore
        this also reports:

        - ``persistence_rmse`` (the ``T[n+1]=T[n]`` reference), so the
          reader sees how much physics adds over doing nothing, and
        - ``increment_r2`` -- ``R^2`` on the change ``T[n+1]-T[n]``, which
          is the honest measure of how much of the *dynamics* the model
          explains.
        """
        if self.fit_ is None:
            raise RuntimeError("Model is not fitted.")
        t_now, p_now, t_next = self._pairs(segments)
        pred = self.predict_onestep(t_now, p_now)
        resid = t_next - pred

        rmse = float(np.sqrt(np.mean(resid**2)))
        mae = float(np.mean(np.abs(resid)))
        ss_res = float(np.sum(resid**2))
        ss_tot = float(np.sum((t_next - t_next.mean()) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

        # persistence reference
        pers_resid = t_next - t_now
        persistence_rmse = float(np.sqrt(np.mean(pers_resid**2)))

        # increment R^2: explain the actual change, not the level
        actual_inc = t_next - t_now
        pred_inc = pred - t_now
        ss_res_i = float(np.sum((actual_inc - pred_inc) ** 2))
        ss_tot_i = float(np.sum((actual_inc - actual_inc.mean()) ** 2))
        increment_r2 = 1.0 - ss_res_i / ss_tot_i if ss_tot_i > 0 else float("nan")

        # residual structure
        if len(resid) > 2 and resid.std() > 0:
            lag1 = float(np.corrcoef(resid[:-1], resid[1:])[0, 1])
        else:
            lag1 = float("nan")

        return BaselineMetrics(
            rmse=rmse,
            mae=mae,
            r2=r2,
            persistence_rmse=persistence_rmse,
            increment_r2=increment_r2,
            residual_std=float(resid.std()),
            residual_mean=float(resid.mean()),
            residual_lag1_autocorr=lag1,
            n_pairs=len(t_next),
        )

    def residuals(
        self, segments: Sequence[tuple[np.ndarray, np.ndarray]]
    ) -> np.ndarray:
        """Return the physics residual r[n] = T[n+1] - T_hat[n+1]."""
        if self.fit_ is None:
            raise RuntimeError("Model is not fitted.")
        t_now, p_now, t_next = self._pairs(segments)
        return t_next - self.predict_onestep(t_now, p_now)
