"""Model D - a new, minimal physics-informed neural model.

Written from scratch for this branch. No GLASSCHIP PINN architecture or loss is
reused or consulted.

The network predicts the temperature increment dT[n] = T[n+1] - T[n] from strictly
causal features. Its loss combines

    L = L_data + lambda * L_physics

    L_data    = mean ( dT_hat - dT_obs )^2                    over TRAINING samples
    L_physics = mean ( dT_hat/dt - (a*P - b*(T - T_amb)) )^2  over COLLOCATION points

where a > 0 and b > 0 (softplus-parameterised) and T_amb are learned jointly with the
network weights. The physics residual is the first-order energy balance

    C dT/dt = P - (T - T_amb)/R,   a = 1/C,  b = 1/(R C)

and needs no labels, which is what lets it constrain behaviour in a regime where no
training data exists.

Two variants:
  * strict       - physics residual evaluated only at training points.
  * collocation  - physics additionally enforced on a SYNTHETIC (T, P) grid covering
                   the hot regime. The grid is generated numerically; no measured
                   hot-regime row is used, so this remains leakage-free.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch
import torch.nn as nn

DT_S = 10.0
SEED = 0


def set_seed(seed: int = SEED) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)


@dataclass
class PINNResult:
    data_loss: float
    physics_loss: float
    total_loss: float
    a: float
    b: float
    T_amb: float
    tau_s: float
    epochs: int
    history: list = field(default_factory=list)


class _Net(nn.Module):
    def __init__(self, n_in: int, hidden: int = 64) -> None:
        super().__init__()
        self.body = nn.Sequential(
            nn.Linear(n_in, hidden), nn.Tanh(),
            nn.Linear(hidden, hidden), nn.Tanh(),
            nn.Linear(hidden, 1),
        )
        # Learned physical parameters. softplus keeps a, b strictly positive.
        self.raw_a = nn.Parameter(torch.tensor(-6.0))
        self.raw_b = nn.Parameter(torch.tensor(-6.0))
        self.T_amb = nn.Parameter(torch.tensor(21.0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.body(x).squeeze(-1)

    @property
    def a(self) -> torch.Tensor:
        return torch.nn.functional.softplus(self.raw_a)

    @property
    def b(self) -> torch.Tensor:
        return torch.nn.functional.softplus(self.raw_b)


class ThermalPINN:
    """Physics-informed increment predictor.

    Parameters
    ----------
    lam:
        Weight on the physics residual. lam = 0 reduces the model to a plain MLP,
        which is used as the ablation that tests whether physics contributes anything.
    collocation:
        If True, add synthetic collocation points spanning the hot regime.
    """

    def __init__(self, n_features: int, lam: float = 1.0, collocation: bool = True,
                 epochs: int = 300, lr: float = 1e-3, hidden: int = 64,
                 dt: float = DT_S, seed: int = SEED) -> None:
        set_seed(seed)
        self.net = _Net(n_features, hidden)
        self.lam = lam
        self.collocation = collocation
        self.epochs = epochs
        self.lr = lr
        self.dt = dt
        self.result_: PINNResult | None = None
        # index of T and P inside the standardised feature vector
        self.i_T, self.i_P = 0, 3

    def _make_collocation(self, mu: np.ndarray, sd: np.ndarray, n: int = 4096
                          ) -> torch.Tensor:
        """Synthetic (T, P) grid over the full operating envelope.

        Physically plausible ranges taken from hardware limits, not from test data:
        T in [20, 80] degC, P in [17, 400] W. Lags are set equal to the current value
        and the differences to zero, i.e. a locally steady operating point.
        """
        rng = np.random.default_rng(SEED)
        T = rng.uniform(20.0, 80.0, n)
        P = rng.uniform(17.0, 400.0, n)
        raw = np.zeros((n, len(mu)))
        raw[:, 0], raw[:, 1], raw[:, 2] = T, T, T          # T, T_l1, T_l2
        raw[:, 3], raw[:, 4], raw[:, 5] = P, P, P          # P, P_l1, P_l2
        raw[:, 6], raw[:, 7] = 0.0, 0.0                    # dP, dT
        return torch.tensor((raw - mu) / sd, dtype=torch.float32)

    def fit(self, Xs: np.ndarray, y: np.ndarray, mu: np.ndarray, sd: np.ndarray
            ) -> "ThermalPINN":
        Xt = torch.tensor(Xs, dtype=torch.float32)
        yt = torch.tensor(y, dtype=torch.float32)
        mu_t = torch.tensor(mu, dtype=torch.float32)
        sd_t = torch.tensor(sd, dtype=torch.float32)

        colloc = self._make_collocation(mu, sd) if self.collocation else None
        opt = torch.optim.Adam(self.net.parameters(), lr=self.lr)
        n = Xt.shape[0]
        batch = min(8192, n)
        g = torch.Generator().manual_seed(SEED)
        history = []

        for ep in range(self.epochs):
            perm = torch.randperm(n, generator=g)[:batch]
            xb, yb = Xt[perm], yt[perm]

            dT_hat = self.net(xb)
            l_data = torch.mean((dT_hat - yb) ** 2)

            # physics residual at training points (always) + synthetic grid (optional)
            xp = xb if colloc is None else torch.cat([xb, colloc], dim=0)
            dT_p = self.net(xp)
            T_p = xp[:, self.i_T] * sd_t[self.i_T] + mu_t[self.i_T]
            P_p = xp[:, self.i_P] * sd_t[self.i_P] + mu_t[self.i_P]
            resid = dT_p / self.dt - (self.net.a * P_p
                                      - self.net.b * (T_p - self.net.T_amb))
            l_phys = torch.mean(resid ** 2)

            loss = l_data + self.lam * l_phys
            opt.zero_grad()
            loss.backward()
            opt.step()
            if ep % 25 == 0 or ep == self.epochs - 1:
                history.append((ep, float(l_data), float(l_phys), float(loss)))

        b = float(self.net.b.detach())
        self.result_ = PINNResult(
            data_loss=float(l_data.detach()), physics_loss=float(l_phys.detach()),
            total_loss=float(loss.detach()), a=float(self.net.a.detach()), b=b,
            T_amb=float(self.net.T_amb.detach()),
            tau_s=(1.0 / b) if b > 0 else float("nan"),
            epochs=self.epochs, history=history,
        )
        return self

    def predict_dT(self, Xs: np.ndarray) -> np.ndarray:
        self.net.eval()
        with torch.no_grad():
            out = self.net(torch.tensor(Xs, dtype=torch.float32)).numpy()
        self.net.train()
        return out
