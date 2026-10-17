"""Frozen H18 representations constructed from an exact research prefix.

Boundaries are draw counts: a boundary at ``b`` starts the next segment
at draw ``b + 1``. Block costs omit the incomplete tail, while a predictive
current segment always extends from the final boundary through the full prefix.
"""
import numpy as np

from src.analysis.recurrence import research_matrix


MINIMUMS = (26, 52, 104)
MULTIPLIERS = (1, 2)
BLOCKS = (13, 26, 52)
SHAPE_FEATURES = ('sum', 'range', 'std', 'spacing_mean', 'spacing_std',
                  'consecutive_pairs', 'odd_count')


def shape_vector(x):
    """Return exactly the frozen seven recurrence shape coordinates per draw."""
    x = research_matrix(x)
    numbers = (np.nonzero(x)[1] + 1).reshape(-1, 6)
    spacing = np.diff(numbers, axis=1)
    return np.column_stack((numbers.sum(axis=1), np.ptp(numbers, axis=1),
                            numbers.std(axis=1, ddof=0), spacing.mean(axis=1),
                            spacing.std(axis=1, ddof=0), (spacing == 1).sum(axis=1),
                            (numbers % 2 == 1).sum(axis=1))).astype(float)


def block_frequency(x, block):
    """Count nonoverlapping complete blocks aligned to draw one.

    ``ends`` contains the one-based final draw of each complete block. The
    incomplete final block contributes neither counts nor observations.
    """
    x = research_matrix(x)
    if type(block) is not int or block not in BLOCKS:
        raise ValueError('Block size must be one of 13, 26, 52')
    complete = len(x) // block
    used = complete * block
    counts = x[:used].reshape(complete, block, 45).sum(axis=1)
    return dict(counts=counts, rates=counts / block,
                ends=np.arange(1, complete + 1, dtype=int) * block,
                block_size=block, used_draws=used, discarded_tail=len(x)-used)


def grid_endpoints(n, step=13):
    """Integer candidate boundaries, including zero and the exact final draw."""
    if type(n) is not int or n < 0 or type(step) is not int or step < 1:
        raise ValueError('Nonnegative integer length and positive integer step required')
    endpoints = np.arange(0, n + 1, step, dtype=int)
    if endpoints[-1] != n:
        endpoints = np.append(endpoints, n)
    return endpoints


def build_contexts(x, *, cutoff=None):
    """Build number/A/B13/B26/B52/C costs using only the supplied prefix.

    ``cutoff`` documents an already sliced prefix; passing future rows and an
    earlier cutoff is rejected instead of silently truncating. The dimension
    is the number of fitted parameters per segment (one for each number fit).
    A is a Bernoulli composite likelihood, not a row-six generative likelihood.
    B Gaussian costs use block observations, with public endpoints in draws.
    """
    x = research_matrix(x)
    n = len(x)
    if cutoff is not None and (type(cutoff) is not int or cutoff != n):
        raise ValueError('Exact causal prefix required: cutoff must equal input length')
    if n < 104:
        raise ValueError('At least 104 draws required for two complete 52-draw blocks')

    from src.analysis.change_point import bernoulli_cost_matrix, gaussian_cost_matrix

    endpoint = grid_endpoints(n)
    common = dict(cutoff=n, boundary_units='draws',
                  boundary_convention='boundary b starts the next segment at draw b+1',
                  prediction_segment='last boundary+1 through full prefix, including incomplete block tail',
                  prediction_end_draw=n)

    def context(costs, endpoints, dimension, observations, kind, used_draws,
                discarded_tail=0, **extra):
        return dict(costs=costs, endpoints=endpoints, dimension=dimension,
                    observations=observations, kind=kind, used_draws=used_draws,
                    discarded_tail=discarded_tail, **extra)

    number_costs = bernoulli_cost_matrix(x, endpoint, per_dimension=True)
    contexts = {
        'number': context(number_costs, endpoint, 1, n, 'bernoulli', n,
                          metadata=dict(common, features=45,
                                        likelihood='45 separate Bernoulli fits'), values=x),
        'A': context(number_costs.sum(axis=2), endpoint, 45, n, 'bernoulli', n,
                     metadata=dict(common, likelihood='Bernoulli composite likelihood'), values=x),
    }
    p = 6 / 45
    for block in BLOCKS:
        frequency = block_frequency(x, block)
        q = len(frequency['ends'])
        iid_std = float(np.sqrt(p * (1 - p) / block))
        standardized = (frequency['rates'] - p) / iid_std
        # The cost engine indexes q observations. Only its external coordinate
        # system is converted to draw counts; no partial block is ever fitted.
        costs = gaussian_cost_matrix(standardized, np.arange(q + 1, dtype=int))
        contexts[f'B{block}'] = context(
            costs, np.arange(q + 1, dtype=int) * block, 45, q, 'gaussian',
            frequency['used_draws'], frequency['discarded_tail'],
            metadata=dict(common, block_size=block, alignment='draw 1',
                          tail_policy='drop incomplete tail from segmentation only',
                          used_draws=frequency['used_draws'],
                          discarded_tail=frequency['discarded_tail'],
                          normalization='fixed IID marginal mean and binomial rate standard deviation',
                          mean=p, std=iid_std, cost_observation_units='complete blocks'),
            counts=frequency['counts'], rates=frequency['rates'],
            standardized=standardized, values=standardized, block_size=block)

    shapes = shape_vector(x)
    mean = shapes.mean(axis=0)
    raw_std = shapes.std(axis=0, ddof=0)
    constant = np.ptp(shapes, axis=0) == 0
    std = np.where(constant, 1., raw_std)
    standardized = (shapes - mean) / std
    # Repeated irrational shape values can acquire nonzero np.std through
    # roundoff in the mean; exact constant columns carry no Gaussian variation.
    standardized[:, constant] = 0.
    contexts['C'] = context(
        gaussian_cost_matrix(standardized, endpoint), endpoint, 7, n, 'gaussian', n,
        metadata=dict(common, feature_names=list(SHAPE_FEATURES), mean=mean.tolist(),
                      std=std.tolist(), raw_std=raw_std.tolist(), scaler_cutoff=n,
                      normalization='supplied prefix population mean/std; constant std replaced by one'),
        shapes=shapes, standardized=standardized, values=standardized)
    return contexts
