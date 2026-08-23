"""Models B and C - gradient-boosted trees, unweighted and tail-weighted.

XGBoost and LightGBM are NOT installed in this environment. scikit-learn's
HistGradientBoostingRegressor is the direct equivalent (histogram-based gradient
boosted trees, the same algorithm family, with sample_weight support). This
substitution is documented rather than made silently.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

SEED = 0


def make_model() -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        max_iter=400, learning_rate=0.05, max_depth=6,
        min_samples_leaf=50, l2_regularization=1.0,
        early_stopping=False, random_state=SEED,
    )


def tail_weights(T_train: np.ndarray, clip: tuple[float, float] = (1.0, 50.0)) -> np.ndarray:
    """Exponentially up-weight the warm tail of the TRAINING distribution.

    Uses training temperatures only - no test label or test statistic is involved.
    This is the control that determines whether any PINN advantage is merely the
    tree under-weighting rare warm samples.
    """
    med = float(np.median(T_train))
    s = float(np.std(T_train))
    if not np.isfinite(s) or s <= 0:
        return np.ones_like(T_train)
    w = np.exp((T_train - med) / s)
    return np.clip(w, clip[0], clip[1])
