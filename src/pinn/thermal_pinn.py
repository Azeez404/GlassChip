"""The single Physics-Informed Neural Network of GLASSCHIP-V1.

ONE model, ONE scientific question (set by Phase 9):

    Can a PINN explain the structured thermal behaviour left unexplained by
    the classical first-order baseline, while respecting the same observable
    physics -- or is that residual irreducible quantization noise?

Design (locked in Phase 6). The network maps continuous time to temperature

    T_hat(u) = MLP(u)            u = (t - t0) / span   in [0, 1]

(input normalised so tanh does not saturate) and its derivative dT_hat/dt is
obtained by AUTOMATIC DIFFERENTIATION, never by finite differencing (which
1 degC / 20 s quantization destroys -- the whole motivation for a PINN here).
The chain rule carries u back to physical time; the ODE is written in
per-TIME_UNIT_S units so the learnable scalars are O(1).

Governing physics is the SAME first-order lumped ODE the baseline used:

    dT/dt = a*P - b*T + c        (a,b,c learnable, per node)

recovering  tau = 1/b,  R_eff = a/b,  T_ref = c/b.  Stability (b>0) and
positive gain (a>0) are enforced by construction (softplus), so the learned
system always decays -- no unstable or non-physical fit is representable.

There are NO spatial operators, NO PDEs, NO Fourier heat conduction, NO
second network. One small MLP, three physics scalars. (An optional Fourier
FEATURE embedding of the time input exists but defaults OFF -- see PINNConfig
-- keeping the network minimal.)

Scope: single node at a time (locked). Fit per node on its gap-free
segment; never differentiate across the 648.9 h data gap.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn

__all__ = ["ThermalPINN", "PINNConfig", "PINNFit", "set_seed"]

#: Physical time unit (s) used to scale the network input. Chosen near the
#: median effective time constant (~230 s from Phase 9) so the normalized
#: dynamics are O(1) and well-conditioned, while keeping the MLP input in a
#: modest range that tanh does not saturate on.
TIME_UNIT_S: float = 300.0

#: Temperature quantization step of the sensor (degC). Drives the data loss.
QUANT_STEP_C: float = 1.0


def set_seed(seed: int = 0) -> None:
    """Make a fit reproducible."""
    np.random.seed(seed)
    torch.manual_seed(seed)


@dataclass
class PINNConfig:
    """Hyper-parameters. Deliberately minimal; each value is justified."""

    hidden: int = 64          # 2 hidden layers, 64 tanh units
    n_freq: int = 0           # Fourier features off: keeps the network minimal;
                              # the smooth MLP fits the physical envelope, which
                              # is the scientifically appropriate target
    lr: float = 1e-2
    epochs: int = 3000
    lam_physics: float = 0.1  # soft physics weight; see justification below
    quant_halfwidth: float = 0.5 * QUANT_STEP_C
    seed: int = 0


@dataclass
class PINNFit:
    """Recovered effective parameters and training diagnostics."""

    a: float
    b: float
    c: float
    tau_eff_s: float
    r_eff: float
    t_ref: float
    final_loss: float
    final_data_loss: float
    final_physics_loss: float
    converged: bool


class _MLP(nn.Module):
    """t -> T_hat with Fourier features to counter MLP spectral bias.

    A plain MLP of time is biased toward low frequencies and smooths the
    faster thermal fluctuations, which biases the autodiff derivative (and
    hence tau). A small Fourier feature embedding
    ``[s, sin(2*pi*k*s), cos(2*pi*k*s)]`` restores mid-frequency
    representation while keeping the network small. Tanh keeps all
    derivatives smooth for clean autodiff.
    """

    def __init__(
        self, hidden: int, n_freq: int, t_mean: float, t_scale: float
    ) -> None:
        super().__init__()
        self.n_freq = n_freq
        k = torch.arange(1, n_freq + 1, dtype=torch.float32)
        self.register_buffer("freqs", 2.0 * np.pi * k)
        in_dim = 1 + 2 * n_freq
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
            nn.Linear(hidden, 1),
        )
        self.register_buffer("t_mean", torch.tensor(float(t_mean)))
        self.register_buffer("t_scale", torch.tensor(float(t_scale)))

    def _features(self, s: torch.Tensor) -> torch.Tensor:
        ang = s * self.freqs  # (N, n_freq)
        return torch.cat([s, torch.sin(ang), torch.cos(ang)], dim=1)

    def forward(self, s: torch.Tensor) -> torch.Tensor:
        return self.t_mean + self.t_scale * self.net(self._features(s))


class ThermalPINN:
    """Physics-informed fit of the first-order thermal ODE for one node.

    Parameters
    ----------
    config:
        Hyper-parameters. The defaults are the intended configuration.

    Notes
    -----
    ``a`` and ``b`` are stored as raw parameters passed through ``softplus``
    so that ``a > 0`` (positive gain) and ``b > 0`` (stable decay) hold by
    construction. ``tau = 1/b`` is therefore always finite and positive.
    """

    def __init__(self, config: PINNConfig | None = None) -> None:
        self.cfg = config or PINNConfig()
        self.model: _MLP | None = None
        self.fit_: PINNFit | None = None

    # ------------------------------------------------------------------
    # Fitting
    # ------------------------------------------------------------------

    def fit(
        self,
        t_seconds: np.ndarray,
        temperature: np.ndarray,
        power: np.ndarray,
    ) -> PINNFit:
        """Fit T_hat(t) and the physics parameters on ONE gap-free segment.

        Parameters
        ----------
        t_seconds:
            Time in seconds from the segment start (strictly increasing).
        temperature:
            Observed temperature (degC), 1 degC quantized.
        power:
            Observed power (W), the physics forcing term.

        Returns
        -------
        PINNFit
        """
        set_seed(self.cfg.seed)
        cfg = self.cfg

        t = np.asarray(t_seconds, dtype="float64")
        y = np.asarray(temperature, dtype="float64")
        p = np.asarray(power, dtype="float64")

        # Network input is normalised to [0,1] so tanh does not saturate.
        # Physical time is recovered for the derivative via the span D.
        t0 = float(t.min())
        span = float(t.max() - t.min()) + 1e-9       # segment duration (s)
        u_np = ((t - t0) / span).reshape(-1, 1)       # in [0,1]
        # d/dt = (d/du) * (du/dt) = (d/du) / span. We express the ODE in
        # per-TIME_UNIT_S units so the learnable scalars are O(1):
        #   dT/dt_unit = (dT/du) * (TIME_UNIT_S / span)
        du_to_unit = TIME_UNIT_S / span

        t_mean, t_scale = float(y.mean()), float(y.std() + 1e-6)

        s = torch.tensor(u_np, dtype=torch.float32, requires_grad=True)
        y_t = torch.tensor(y.reshape(-1, 1), dtype=torch.float32)
        p_t = torch.tensor(p.reshape(-1, 1), dtype=torch.float32)

        self.model = _MLP(cfg.hidden, cfg.n_freq, t_mean, t_scale)
        # Physics scalars in per-TIME_UNIT_S units: A*P - B*T + C, with
        # A,B > 0. B ~ TIME_UNIT_S/tau ~ 300/230 ~ 1.3 -> init softplus~1.3.
        a_raw = nn.Parameter(torch.tensor(-3.0))   # softplus(-3)~0.049
        b_raw = nn.Parameter(torch.tensor(0.2))    # softplus(0.2)~0.80
        c_raw = nn.Parameter(torch.tensor(0.0))

        params = list(self.model.parameters()) + [a_raw, b_raw, c_raw]
        opt = torch.optim.Adam(params, lr=cfg.lr)

        sp = torch.nn.functional.softplus
        dz = cfg.quant_halfwidth
        loss_hist: list[float] = []

        for _ in range(cfg.epochs):
            opt.zero_grad()
            t_hat = self.model(s)

            # dT_hat/du via autodiff, converted to per-TIME_UNIT_S units.
            dTdu = torch.autograd.grad(
                t_hat, s, grad_outputs=torch.ones_like(t_hat),
                create_graph=True,
            )[0]
            dTdt_unit = dTdu * du_to_unit

            A = sp(a_raw)
            B = sp(b_raw) + 1e-6
            C = c_raw

            # Data loss: quantization-aware. The dead-zone term does not
            # penalise predictions within +-0.5 degC of the integer
            # observation (they round to the same value); a light quadratic
            # pull (weight 0.1) keeps the trajectory tracked so the autodiff
            # derivative is meaningful. Together: fit the data down to, but
            # not below, the quantization floor.
            e = t_hat - y_t
            deadzone = torch.mean(torch.clamp(torch.abs(e) - dz, min=0.0) ** 2)
            data_loss = deadzone + 0.1 * torch.mean(e ** 2)

            # Physics loss: ODE residual (per TIME_UNIT_S) at the sample
            # points (collocation).
            phys_res = dTdt_unit - (A * p_t - B * t_hat + C)
            phys_loss = torch.mean(phys_res ** 2)

            loss = data_loss + cfg.lam_physics * phys_loss
            loss.backward()
            opt.step()
            loss_hist.append(float(loss.item()))

        with torch.no_grad():
            A_v = float(sp(a_raw)); B_v = float(sp(b_raw) + 1e-6); C_v = float(c_raw)

        # Convert per-TIME_UNIT_S scalars back to physical units.
        b_v = B_v / TIME_UNIT_S           # 1/s
        a_v = A_v / TIME_UNIT_S           # 1/(s) * (degC/W)/degC ... see r_eff
        c_v = C_v / TIME_UNIT_S
        tau = TIME_UNIT_S / B_v           # s
        converged = (
            len(loss_hist) > 50
            and abs(loss_hist[-1] - loss_hist[-50]) < 1e-4 * (loss_hist[0] + 1e-9)
        )
        self.fit_ = PINNFit(
            a=a_v, b=b_v, c=c_v,
            tau_eff_s=tau, r_eff=A_v / B_v, t_ref=C_v / B_v,
            final_loss=loss_hist[-1],
            final_data_loss=float(data_loss.item()),
            final_physics_loss=float(phys_loss.item()),
            converged=bool(converged),
        )
        return self.fit_

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, t_seconds: np.ndarray) -> np.ndarray:
        """Continuous temperature estimate T_hat(t)."""
        if self.model is None:
            raise RuntimeError("Model is not fitted.")
        s = torch.tensor(
            (np.asarray(t_seconds, dtype="float64") / TIME_UNIT_S).reshape(-1, 1),
            dtype=torch.float32,
        )
        with torch.no_grad():
            return self.model(s).numpy().ravel()

    def save(self, path: str) -> None:
        """Persist the network weights."""
        if self.model is None:
            raise RuntimeError("Model is not fitted.")
        torch.save(self.model.state_dict(), path)
