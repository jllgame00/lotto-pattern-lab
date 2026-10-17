"""Causal Phase 17 tensors with fixed IID normalization.

Each time slice is anchored on an already completed, one-based draw.  Inputs
must be the complete research prefix: ``cutoff`` verifies its length and never
slices away future rows.  Scaling uses theoretical moments, never fitted data.
"""
from numbers import Integral

import numpy as np

from .recurrence import research_matrix


LAGS = (0, 1, 2, 4, 8, 13, 26)
WINDOWS = (10, 26, 52)
GAP_CLIP = 52
IID_P = 6 / 45


def build_tensors(x, *, cutoff=None, normalize=True):
    """Build A/B/C dictionaries of values, draws, features, and metadata.

    Values have axes ``time × number (1..45) × feature``. Tensor A starts at
    draw 27; B/C start at draw 52. At least 52 and at most 1245 valid binary
    six-number draws are required. If supplied, ``cutoff`` must be an integer
    equal to the input length. ``normalize=False`` exposes unscaled features.

    C's gap is zero on appearance, otherwise the number of completed draws
    since the most recent appearance, clipped to 52 and divided by 52. For
    a never-seen number the most recent appearance is initialized at draw 0.
    Its IID reference is the stationary nonnegative geometric distribution;
    the deterministic initial boundary is preserved in real and null tensors.
    """
    x = research_matrix(x)
    n = len(x)
    if cutoff is not None and (
        isinstance(cutoff, (bool, np.bool_))
        or not isinstance(cutoff, Integral)
        or cutoff != n
    ):
        raise ValueError('cutoff must equal the supplied complete prefix length')
    if n < 52:
        raise ValueError('At least 52 completed draws are required')

    variance = IID_P * (1 - IID_P)
    appearance_sd = float(np.sqrt(variance))
    anchors = np.arange(1, n + 1)
    lag_values = np.stack([x[26 - lag:n - lag] for lag in LAGS], axis=2).astype(float)

    # Prefix sums include the anchor row: draw t, window W -> rows [t-W:t].
    cumulative = np.vstack((np.zeros((1, 45)), np.cumsum(x, axis=0)))
    rolling = {
        window: (cumulative[52:] - cumulative[52 - window:n + 1 - window]) / window
        for window in WINDOWS
    }
    rate_values = np.stack([rolling[window] for window in WINDOWS], axis=2)

    last_appearance = np.maximum.accumulate(np.where(x, anchors[:, None], 0), axis=0)
    gap = np.minimum(anchors[:, None] - last_appearance, GAP_CLIP) / GAP_CLIP
    state_values = np.stack((x[51:], gap[51:], rolling[26], rolling[52]), axis=2)

    # Tail-sum moments for min(G,52), P(G=g)=p*(1-p)**g, g >= 0.
    k = np.arange(1, GAP_CLIP + 1)
    tail = (1 - IID_P) ** k
    gap_mean_unscaled = float(tail.sum())
    gap_second_unscaled = float(((2 * k - 1) * tail).sum())
    gap_mean = gap_mean_unscaled / GAP_CLIP
    gap_sd = float(np.sqrt(gap_second_unscaled - gap_mean_unscaled**2) / GAP_CLIP)

    def package(values, first_draw, features, mean, sd, **details):
        mean, sd = np.asarray(mean, dtype=float), np.asarray(sd, dtype=float)
        if normalize:
            values = (values - mean) / sd
        return {
            'values': values,
            'draws': anchors[first_draw - 1:].copy(),
            'features': features,
            'metadata': {
                'cutoff': n,
                'first_draw': first_draw,
                'last_draw': n,
                'normalized': bool(normalize),
                'normalization': 'fixed_iid' if normalize else 'none',
                'iid_probability': IID_P,
                'iid_mean': mean.tolist(),
                'iid_std': sd.tolist(),
                'anchor': 'completed_draw_inclusive',
                'number_labels': list(range(1, 46)),
                **details,
            },
        }

    return {
        'A': package(
            lag_values, 27, [f'lag_{lag}' for lag in LAGS],
            [IID_P] * len(LAGS), [appearance_sd] * len(LAGS), lags=list(LAGS),
        ),
        'B': package(
            rate_values, 52, [f'rate_{window}' for window in WINDOWS],
            [IID_P] * len(WINDOWS), np.sqrt(variance / np.array(WINDOWS)),
            windows=list(WINDOWS),
        ),
        'C': package(
            state_values, 52, ['appearance', 'gap_52', 'rate_26', 'rate_52'],
            [IID_P, gap_mean, IID_P, IID_P],
            [appearance_sd, gap_sd, np.sqrt(variance / 26), np.sqrt(variance / 52)],
            windows=[26, 52], gap_clip=GAP_CLIP, gap_divisor=GAP_CLIP,
            gap_initialization='last_appearance_draw_0',
            gap_iid_reference='nonnegative_geometric_stationary',
        ),
    }
