"""New causal replays of documented configurations, never historical bytes.

The old configurations were selected before draw901; these already examined
historical outcomes do not become an independent or prospective holdout here.
The H17 component set excludes MI, which remains available for audit only.
"""
from functools import partial
import json
import numbers

import numpy as np
import pandas as pd

from src.backtest.ranking import rank_metrics
from src.models.predictive import rank_numbers

START = 901
END = 1245
ELIGIBLE = ('GapLogistic', 'GraphStructureModel', 'GapShapeModel', 'MirrorModel')
AUDIT_ONLY = ('MutualInformationModel',)
BASELINES = ('RandomModel', 'Frequency26')


def canonical_configs():
    """Return fresh, JSON-compatible descriptions of existing fixed models."""
    from src.analysis.features import GAP
    return {
        'GapLogistic': dict(constructor='src.models.predictive.LogisticModel',
                            parameters=dict(columns=list(GAP), C=1., seed=42),
                            fit='expanding labels105..fit_cutoff; cadence anchored901',
                            role='eligible'),
        'GraphStructureModel': dict(constructor='src.models.graph_hypergraph.GraphStructureModel',
                                   parameters=dict(window=52, feature='neighbor_community', communities=3),
                                   fixed=dict(graph_threshold=2), fit='every target prefix', role='eligible'),
        'GapShapeModel': dict(constructor='src.models.transformed_space.GapShapeModel',
                             parameters=dict(K=25, sigma=1), fixed=dict(exclusion=26),
                             fit='every target prefix', role='eligible'),
        'MirrorModel': dict(constructor='src.models.symmetry.MirrorModel',
                           parameters=dict(window=10, lag=1, shrinkage=200, support=20),
                           fit='every target prefix', role='eligible'),
        'MutualInformationModel': dict(constructor='src.models.information_flow.MutualInformationModel',
                                      parameters=dict(lag=1, incoming=3),
                                      fixed=dict(training_window=624, context_support=20, shrinkage=20),
                                      fit='every target prefix', role='audit_only'),
        'Frequency26': dict(constructor='src.models.graph_hypergraph.RollingFrequencyControl',
                            parameters=dict(window=26), fit='every target prefix', role='baseline'),
        'RandomModel': dict(constructor='src.models.random_model.RandomModel', parameters={},
                           seed=42, seed_stream=10, ties='seeded uniform random ranking', role='baseline'),
    }


def replay(history, *, cadence=26, progress=None):
    """Replay fixed901..1245 with a901 Gap fit anchor and no1246 features.

    Uses existing primitives without recreating historical selection files or
    invoking old archive-dependent evaluators. Writes no artifacts itself.
    """
    if (not isinstance(history, pd.DataFrame) or 'draw_no' not in history
            or history.draw_no.tolist() != list(range(1, END+1))
            or type(cadence) is not int or cadence not in (13, 26)):
        raise ValueError('Replay requires exact draws1..1245 and cadence13/26')
    from src.analysis.features import _build_features, GAP
    from src.backtest.translation import walk_forward
    from src.models.graph_hypergraph import GraphStructureModel, RollingFrequencyControl
    from src.models.transformed_space import GapShapeModel
    from src.models.symmetry import MirrorModel
    from src.models.information_flow import MutualInformationModel

    features = _build_features(history, min_history=104, include_current=False, progress=progress)
    features = features[['target_draw', 'feature_cutoff', 'number', 'appeared_next', *GAP]]
    configs = canonical_configs()
    constructors = dict(GraphStructureModel=GraphStructureModel, GapShapeModel=GapShapeModel,
                        MirrorModel=MirrorModel, MutualInformationModel=MutualInformationModel,
                        Frequency26=RollingFrequencyControl)
    factories = {name: partial(constructor, **configs[name]['parameters'])
                 for name, constructor in constructors.items()}
    rows = walk_forward(history, factories, start=START, end=END, cadence=cadence,
                        seed=42, gap_features=features, combined=False, progress=progress)
    rows = rows.copy()
    rows['outer_fit_cutoff'] = rows.training_cutoff
    fresh = rows.model != 'GapLogistic'
    rows.loc[fresh, 'training_cutoff'] = rows.loc[fresh, 'feature_cutoff']
    rows['provenance'] = 'new_replay_from_documented_configuration'
    checked = validate_rows(rows)
    if set(checked.model) != set(configs) or len(checked) != len(configs)*(END-START+1):
        raise ValueError('Replay did not produce every model and target901..1245')
    return checked


def _integer(value, label):
    if (isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Real)
            or not np.isfinite(value) or value != int(value)):
        raise ValueError(f'{label} must be an integer')
    return int(value)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON score key')
        result[key] = value
    return result


def _decode(value):
    try:
        return json.loads(value, object_pairs_hook=_unique_object) if isinstance(value, str) else value
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError('Invalid prediction JSON') from exc


def _number_list(value, *, complete):
    values = _decode(value)
    if not isinstance(values, list):
        raise ValueError('Ranking and actual must be JSON number lists')
    if any(isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, np.integer)) for v in values):
        raise ValueError('Ranking and actual require integer numbers')
    if complete:
        if sorted(values) != list(range(1, 46)):
            raise ValueError('Complete ranking permutation1..45 required')
    elif len(values) != 6 or len(set(values)) != 6 or not set(values) <= set(range(1, 46)):
        raise ValueError('Actual requires six distinct numbers1..45')
    return values


def _score_map(value):
    scores = _decode(value)
    if not isinstance(scores, dict):
        raise ValueError('Scores must be a45-number map')
    if set(scores) == {str(n) for n in range(1, 46)}:
        scores = {int(k): v for k, v in scores.items()}
    elif (set(scores) != set(range(1, 46))
          or any(isinstance(k, bool) or not isinstance(k, (int, np.integer)) for k in scores)):
        raise ValueError('Scores must contain exactly numbers1..45')
    if any(isinstance(v, (bool, np.bool_)) or not isinstance(v, numbers.Real)
           or not np.isfinite(v) for v in scores.values()):
        raise ValueError('All45 scores must be finite real values')
    return scores


def validate_rows(rows):
    """Validate complete rows and per-model contiguous ranges within901..1245.

    Partial leading/trailing ranges are allowed. Missing internal targets,
    conflicting actual outcomes, future cutoffs, and altered score rankings
    fail closed. Available metrics are checked; absent metrics are recomputed.
    """
    required = {'model', 'target_draw', 'feature_cutoff', 'training_cutoff', 'scores', 'ranking', 'actual'}
    if not isinstance(rows, pd.DataFrame) or rows.empty or not required <= set(rows):
        raise ValueError('Nonempty prediction rows with complete scores/ranking/cutoffs required')
    if rows.duplicated(['model', 'target_draw']).any():
        raise ValueError('Duplicate model-target rows')
    valid_names = set(canonical_configs())
    actuals = {}
    result = rows.copy(deep=True).reset_index(drop=True)
    for index, row in enumerate(rows.to_dict('records')):
        if not isinstance(row['model'], str) or row['model'] not in valid_names:
            raise ValueError('Unknown input model')
        target = _integer(row['target_draw'], 'target_draw')
        feature = _integer(row['feature_cutoff'], 'feature_cutoff')
        training = _integer(row['training_cutoff'], 'training_cutoff')
        if not START <= target <= END or feature != target-1 or not 0 <= training < target:
            raise ValueError('Target/cutoff outside causal901..1245 scope')
        if 'outer_fit_cutoff' in row:
            outer = _integer(row['outer_fit_cutoff'], 'outer_fit_cutoff')
            if not 0 <= outer <= training:
                raise ValueError('Outer fit cutoff exceeds effective training cutoff')
        ranking = _number_list(row['ranking'], complete=True)
        actual = _number_list(row['actual'], complete=False)
        scores = _score_map(row['scores'])
        if row['model'] != 'RandomModel' and ranking != rank_numbers(scores):
            raise ValueError('Ranking disagrees with descending score/smaller-number tie rule')
        outcome = frozenset(actual)
        if target in actuals and actuals[target] != outcome:
            raise ValueError('Conflicting actual outcomes at the same target')
        actuals[target] = outcome
        metrics = rank_metrics(ranking, outcome)
        metrics.update({f'pool_{k}': len(set(ranking[:k]) & outcome) for k in (6, 8, 10, 12, 15)})
        for key, value in metrics.items():
            if key in row:
                supplied = row[key]
                if (isinstance(supplied, (bool, np.bool_)) or not isinstance(supplied, numbers.Real)
                        or not np.isfinite(supplied) or not np.isclose(supplied, value, rtol=0, atol=1e-12)):
                    raise ValueError(f'Ranking metric integrity mismatch: {key}')
            result.at[index, key] = value
    for _, group in result.groupby('model', sort=False):
        targets = sorted(int(t) for t in group.target_draw)
        if targets != list(range(targets[0], targets[-1]+1)):
            raise ValueError('Missing internal target in model range')
    return result.sort_values(['target_draw', 'model']).reset_index(drop=True)


def load_panel(rows, names):
    """Return matched targets, number-coordinate ranks(N,C,45), and actuals.

    Intersection metadata explicitly reports discarded leading/trailing rows;
    no internal holes are silently removed. All supplied rows are validated,
    including audit-only models outside the requested component list.
    """
    if (not isinstance(names, (list, tuple)) or not names
            or any(not isinstance(n, str) for n in names) or len(set(names)) != len(names)):
        raise ValueError('Distinct nonempty model names required')
    checked = validate_rows(rows)
    if not set(names) <= set(checked.model):
        raise ValueError('Requested model predictions are unavailable')
    groups = {name: checked[checked.model == name].set_index('target_draw') for name in names}
    common = sorted(set.intersection(*(set(group.index) for group in groups.values())))
    if not common or common != list(range(int(common[0]), int(common[-1])+1)):
        raise ValueError('Nonempty contiguous common target intersection required')
    targets = np.asarray(common, dtype=int)
    ranks = np.empty((len(targets), len(names), 45), dtype=int)
    actual = np.zeros((len(targets), 45), dtype=bool)
    for i, target in enumerate(targets):
        for j, name in enumerate(names):
            row = groups[name].loc[target]
            order = np.asarray(_number_list(row.ranking, complete=True), dtype=int)
            ranks[i, j, order-1] = np.arange(1, 46)
            if j == 0:
                actual[i, np.asarray(_number_list(row.actual, complete=False))-1] = True
    intersection = dict(expected_start=START, expected_end=END, expected_targets=END-START+1,
                        start=int(targets[0]), end=int(targets[-1]), targets=len(targets),
                        available_ranges={name: [int(group.index.min()), int(group.index.max())]
                                          for name, group in groups.items()},
                        excluded_targets={name: sorted(int(t) for t in set(group.index)-set(common))
                                          for name, group in groups.items()})
    return dict(targets=targets, ranks=ranks, actual=actual, names=list(names), intersection=intersection)
