"""Development-frozen descriptive complexity states and a model admission gate.

Higher oriented metrics denote lower proxy complexity. State thresholds use
only previously completed metrics; next-draw outcomes are attached afterwards.
This module creates neither a predictor nor any prospective artifact.
"""
from copy import deepcopy
from types import MappingProxyType

import numpy as np
import pandas as pd

from src.analysis.spatiotemporal import binary_matrix


def choose_development(raw_result, z_values):
    """Freeze the strongest finite rolling cell from exactly draws 1..900.

    ``z_values`` must come from the independent development pilot calibration.
    Equal maxima retain the complete search's first cell ordering. The selected
    endpoint identifies the discovery cell, but is removed from the reusable
    rolling specification.
    """
    if raw_result.get('draws') != 900:
        raise ValueError('Metric selection requires exactly development draws 1..900')
    z = np.asarray(z_values, dtype=float)
    keys = raw_result['keys']
    values = np.asarray(raw_result['values'], dtype=float)
    metadata = raw_result['metadata']
    if (z.ndim != 1 or values.shape != z.shape or len(keys) != len(z)
            or len(metadata) != len(z) or len(raw_result['families']) != len(z)):
        raise ValueError('Metric keys, metadata, values, families and calibration must align')
    eligible = np.isfinite(z) & np.isfinite(values)
    eligible &= np.array([cell.get('scope') == 'rolling' for cell in metadata])
    if not eligible.any():
        raise ValueError('No finite calibrated development rolling metric is available')
    index = int(np.argmax(np.where(eligible, z, -np.inf)))
    spec = deepcopy(metadata[index])
    spec.pop('endpoint', None)
    return dict(spec=MappingProxyType(spec), selected_key=keys[index], z=float(z[index]))


def oriented_cell(prefix, spec):
    """Evaluate the search's fixed estimator lazily, without importing a CLI."""
    from src.analysis.complexity_search import oriented_cell as evaluate
    return evaluate(prefix, spec)


def regime_diagnostic(x, spec, development_end=900, min_past=104):
    """Return causal state/outcome rows through the sealed research endpoint.

    Endpoint ``end`` consumes draws 1..end and labels only draw end+1. The own
    frequency baseline is the prefix appearance rate summed over the current
    six winners. Sparse metrics remain UNKNOWN and never enter threshold fits.
    """
    if development_end != 900:
        raise ValueError('The frozen development endpoint must be 900')
    if type(min_past) is not int or min_past < 1:
        raise ValueError('min_past must be a positive integer')
    x = binary_matrix(x)
    if len(x) > 1245 or not np.all(x.sum(axis=1) == 6):
        raise ValueError('Expected six main winners in each research draw, through 1245 only')
    window = spec.get('window')
    if not isinstance(window, (int, np.integer)) or window < 1:
        raise ValueError('The frozen metric requires a positive draw window')
    records = []
    past = []
    for end in range(int(window), len(x)):
        value = float(oriented_cell(x[:end], spec))
        q_low = q_high = np.nan
        state = 'UNKNOWN'
        if len(past) >= min_past:
            q_low, q_high = np.quantile(past, [1/3, 2/3])
            if np.isfinite(value):
                state = 'NORMAL'
                if q_low < q_high:
                    if value <= q_low:
                        state = 'HIGH'
                    elif value >= q_high:
                        state = 'LOW'
        records.append(dict(endpoint=end, target_draw=end+1, metric=value,
                            q_low=float(q_low), q_high=float(q_high), state=state))
        if np.isfinite(value):
            past.append(value)

    # Complete every metric/threshold calculation before accessing outcomes.
    counts = x.astype(np.int64).cumsum(axis=0)
    for row in records:
        end = row['endpoint']
        current, following = x[end-1], x[end]
        overlap = int(np.logical_and(current, following).sum())
        expected = float(counts[end-1, current].sum() / end)
        numbers = np.flatnonzero(following) + 1
        row.update(overlap=overlap, own_expected_overlap=expected,
                   excess=overlap-expected, next_sum=int(numbers.sum()),
                   next_range=int(numbers[-1]-numbers[0]))
    columns = ['endpoint', 'target_draw', 'metric', 'q_low', 'q_high', 'state',
               'overlap', 'own_expected_overlap', 'excess', 'next_sum', 'next_range']
    return pd.DataFrame(records, columns=columns)


def development_gate(comparisons, rows, *, research_cutoff):
    """Admit a later model only from the predeclared development conditions.

    Comparisons are the complete six-family by three-null development table.
    Descriptive rows after target 900 are ignored. Both LOW-state development
    halves need strictly positive mean excess above .05 and total support >=30.
    """
    if research_cutoff != 900:
        raise ValueError('The model gate requires research_cutoff=900')
    comparisons = pd.DataFrame(comparisons).copy()
    if 'null_model' not in comparisons and 'null' in comparisons:
        comparisons = comparisons.rename(columns={'null': 'null_model'})
    required = {'scope', 'cutoff', 'family', 'null_model', 'adjusted_p'}
    if not required.issubset(comparisons.columns):
        raise ValueError('Complete development comparison metadata is required')
    if not (comparisons.scope.eq('development').all() and comparisons.cutoff.eq(900).all()):
        raise ValueError('Only development comparisons through draw 900 may enter the gate')
    families = ('entropy', 'conditional', 'ordinal', 'lz', 'compression', 'chronological')
    nulls = ('iid', 'fixed_margins', 'draw_shuffle')
    expected = {(family, null) for family in families for null in nulls}
    pairs = list(zip(comparisons.family, comparisons.null_model))
    if len(pairs) != len(expected) or set(pairs) != expected:
        raise ValueError('Exactly six families by three null comparisons are required')
    p = pd.to_numeric(comparisons.adjusted_p, errors='raise')
    if ((p.dropna() < 0) | (p.dropna() > 1)).any():
        raise ValueError('Adjusted p values must be probabilities')
    significant = {(family, null): bool(np.isfinite(value) and value <= .05)
                   for family, null, value in zip(comparisons.family, comparisons.null_model, p)}
    temporal_families = ('conditional', 'ordinal', 'lz', 'compression', 'chronological')
    structure = any(significant[(family, 'iid')] and significant[(family, 'fixed_margins')]
                    for family in temporal_families)
    structure |= significant[('chronological', 'draw_shuffle')]

    rows = pd.DataFrame(rows)
    if not {'target_draw', 'state', 'excess'}.issubset(rows.columns):
        raise ValueError('Diagnostic target, state and excess columns are required')
    selected = rows.loc[rows.target_draw.between(501, 900) & rows.state.eq('LOW')].copy()
    if selected.target_draw.duplicated().any():
        raise ValueError('Each development outcome may be counted only once')
    selected = selected.loc[np.isfinite(selected.excess)]
    means = {label: float(selected.loc[selected.target_draw.between(start, end), 'excess'].mean())
             for label, start, end in [('501..700', 501, 700), ('701..900', 701, 900)]}
    enough = len(selected) >= 30
    positive = all(np.isfinite(value) and value > .05 for value in means.values())
    justified = bool(structure and enough and positive)
    reasons = []
    if not structure:
        reasons.append('No corrected development temporal structure comparison passed')
    if not enough:
        reasons.append('Fewer than 30 finite LOW-state development outcomes')
    if not positive:
        reasons.append('Both development halves must have LOW-state mean excess > .05')
    return dict(model_justified=justified, structure_supported=bool(structure),
                low_support=len(selected), halves_means=means,
                reason='; '.join(reasons) if reasons else 'All development model conditions passed')
