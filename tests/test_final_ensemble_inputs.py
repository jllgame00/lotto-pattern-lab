"""Bounded replay and artifact integrity tests; synthetic outcomes only."""
import importlib.util
import json

import numpy as np
import pandas as pd
import pytest


def artifact_row(model='GraphStructureModel', target=901, reverse=False):
    ranking = list(range(45, 0, -1)) if reverse else list(range(1, 46))
    actual = [1, 2, 3, 4, 5, 6]
    winning = [ranking.index(n) + 1 for n in actual]
    return dict(model=model, target_draw=target, feature_cutoff=target-1,
                training_cutoff=target-1, outer_fit_cutoff=900, seed=42,
                scores=json.dumps({n: float(n if reverse else 46-n) for n in range(1, 46)}),
                ranking=json.dumps(ranking), actual=json.dumps(actual),
                hits=sum(r <= 6 for r in winning), mean_winning_rank=np.mean(winning),
                **{f'recall_{k}': sum(r <= k for r in winning)/6 for k in (6, 10, 15)},
                **{f'pool_{k}': sum(r <= k for r in winning) for k in (6, 8, 10, 12, 15)})


def test_inputs_module_exists():
    assert importlib.util.find_spec('src.analysis.final_ensemble_inputs') is not None


def test_panel_inverts_permutations_and_reports_contiguous_intersection():
    from src.analysis.final_ensemble_inputs import load_panel
    rows = pd.DataFrame([artifact_row('GraphStructureModel', t) for t in (901, 902, 903)] +
                        [artifact_row('MirrorModel', t, True) for t in (902, 903, 904)])
    panel = load_panel(rows.sample(frac=1, random_state=1), ['MirrorModel', 'GraphStructureModel'])
    assert panel['targets'].tolist() == [902, 903]
    assert panel['names'] == ['MirrorModel', 'GraphStructureModel']
    assert panel['ranks'].shape == (2, 2, 45)
    assert panel['ranks'][0, 0].tolist() == list(range(45, 0, -1))
    assert panel['ranks'][0, 1].tolist() == list(range(1, 46))
    assert panel['actual'].dtype == np.bool_
    assert panel['actual'][0].tolist() == [True]*6 + [False]*39
    assert panel['intersection']['excluded_targets'] == {'MirrorModel': [904], 'GraphStructureModel': [901]}


def test_panel_uses_number_coordinates_for_non_self_inverse_ranking():
    from src.analysis.final_ensemble_inputs import load_panel
    row = artifact_row()
    order = [2, 3, 1] + list(range(4, 46))
    row['ranking'] = json.dumps(order)
    row['scores'] = json.dumps({n: 46-order.index(n) for n in order})
    panel = load_panel(pd.DataFrame([row]), ['GraphStructureModel'])
    assert panel['ranks'][0, 0, :4].tolist() == [3, 1, 2, 4]


@pytest.mark.parametrize('field,value', [
    ('target_draw', 1246), ('target_draw', 900), ('target_draw', 901.5),
    ('target_draw', True), ('feature_cutoff', 901), ('training_cutoff', 901),
    ('training_cutoff', -1), ('training_cutoff', 899.5), ('outer_fit_cutoff', 901),
    ('ranking', json.dumps([1]*45)), ('ranking', json.dumps([True]+list(range(2, 46)))),
    ('actual', json.dumps([1, 2, 3, 4, 5, 5])), ('hits', 5), ('recall_10', 0),
    ('scores', json.dumps({n: float('nan') for n in range(1, 46)})),
    ('scores', json.dumps({n: 1 for n in range(1, 45)})),
])
def test_invalid_artifacts_fail_closed(field, value):
    from src.analysis.final_ensemble_inputs import validate_rows
    row = artifact_row(); row[field] = value
    with pytest.raises(ValueError):
        validate_rows(pd.DataFrame([row]))


def test_nonrandom_tie_rule_and_random_exception():
    from src.analysis.final_ensemble_inputs import validate_rows
    row = artifact_row('MirrorModel', reverse=True)
    row['scores'] = json.dumps({n: 6/45 for n in range(1, 46)})
    with pytest.raises(ValueError, match='rank|tie'):
        validate_rows(pd.DataFrame([row]))
    row['model'] = 'RandomModel'
    assert len(validate_rows(pd.DataFrame([row]))) == 1


def test_duplicate_holes_and_inconsistent_actuals_are_rejected():
    from src.analysis.final_ensemble_inputs import validate_rows
    for rows in ([artifact_row(), artifact_row()],
                 [artifact_row(target=901), artifact_row(target=903)]):
        with pytest.raises(ValueError):
            validate_rows(pd.DataFrame(rows))
    other = artifact_row('MirrorModel')
    other['actual'] = json.dumps([1, 2, 3, 4, 5, 7])
    other.update(hits=5, recall_6=5/6, mean_winning_rank=22/6, pool_6=5)
    with pytest.raises(ValueError, match='actual|outcome'):
        validate_rows(pd.DataFrame([artifact_row(), other]))


@pytest.mark.parametrize('names', [[], ['unknown'], ['MirrorModel', 'MirrorModel']])
def test_panel_rejects_unavailable_or_duplicate_names(names):
    from src.analysis.final_ensemble_inputs import load_panel
    with pytest.raises(ValueError):
        load_panel(pd.DataFrame([artifact_row()]), names)


def test_panel_rejects_disjoint_ranges():
    from src.analysis.final_ensemble_inputs import load_panel
    with pytest.raises(ValueError, match='intersection|common'):
        load_panel(pd.DataFrame([artifact_row(), artifact_row('MirrorModel', 902)]),
                   ['GraphStructureModel', 'MirrorModel'])


def test_replay_rejects_short_history_and_unsupported_cadence_before_features():
    from src.analysis.final_ensemble_inputs import replay
    for history, cadence in [(pd.DataFrame({'draw_no': range(1, 1245)}), 26),
                             (pd.DataFrame({'draw_no': range(1, 1247)}), 26),
                             (pd.DataFrame({'draw_no': range(1, 1246)}), 7)]:
        with pytest.raises(ValueError):
            replay(history, cadence=cadence)


def test_replay_records_effective_cutoff_without_altering_gap_fit(monkeypatch):
    from src.analysis.final_ensemble_inputs import replay, canonical_configs
    from src.analysis import features
    from src.backtest import translation
    # Isolate the expensive existing feature/model engine. The wrapper must
    # still normalize provenance correctly and enforce the complete output.
    def build(history, **kwargs):
        assert kwargs['include_current'] is False and kwargs['min_history'] == 104
        assert history.draw_no.tolist() == list(range(1, 1246))
        return pd.DataFrame(columns=['target_draw', 'feature_cutoff', 'number', 'appeared_next', *features.GAP])
    def evaluate(history, factories, **kwargs):
        assert (kwargs['start'], kwargs['end'], kwargs['cadence'], kwargs['combined']) == (901, 1245, 26, False)
        assert factories['GraphStructureModel']().configuration() == dict(window=52, feature='neighbor_community', communities=3)
        assert factories['GapShapeModel']().configuration() == dict(K=25, sigma=1)
        assert factories['MirrorModel']().configuration() == dict(window=10, lag=1, shrinkage=200, support=20)
        assert factories['MutualInformationModel']().configuration() == dict(lag=1, incoming=3)
        rows = []
        for name in canonical_configs():
            for t in range(901, 1246):
                row = artifact_row(name, t)
                row.pop('outer_fit_cutoff')
                row['training_cutoff'] = t-1 if name == 'RandomModel' else 900+26*((t-901)//26)
                rows.append(row)
        return pd.DataFrame(rows)
    monkeypatch.setattr(features, '_build_features', build)
    monkeypatch.setattr(translation, 'walk_forward', evaluate)
    out = replay(pd.DataFrame({'draw_no': range(1, 1246)}))
    graph = out[(out.model == 'GraphStructureModel') & (out.target_draw == 902)].iloc[0]
    gap = out[(out.model == 'GapLogistic') & (out.target_draw == 902)].iloc[0]
    assert graph.training_cutoff == 901 and graph.outer_fit_cutoff == 900
    assert gap.training_cutoff == 900 and gap.outer_fit_cutoff == 900
    assert len(out) == 7*345
