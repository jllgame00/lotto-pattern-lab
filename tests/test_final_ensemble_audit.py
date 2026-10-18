"""Independent verifier must reject resealed links and changed rank artifacts."""
from hashlib import sha256
import importlib.util
import json

import numpy as np
import pytest


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def seal(path, value):
    path.write_text(json.dumps(dict(payload=value, sha256=digest(value))), encoding='utf8')


def chain(path):
    protocol = dict(version='test')
    development = dict(protocol_hash=digest(protocol))
    spec = dict(id='equal_all', weights=[.25]*4)
    validation = dict(protocol_hash=digest(protocol), development_hash=digest(development), selected=spec)
    started = dict(validation_hash=digest(validation), final_start=1131, final_end=1245, model_selection_evaluations=1)
    configuration = dict(protocol_hash=digest(protocol), development_hash=digest(development),
                         validation_hash=digest(validation), selected=spec, kind='CONFIGURATION_ONLY',
                         draw1246_used=False, draw1247_prediction_generated=False, publication_executed=False)
    values = dict(protocol=protocol, development_selection=development, validation_gate=validation,
                  final_started=started, configuration_freeze=configuration)
    for name, value in values.items():
        seal(path/f'{name}.json', value)
    return values


def test_audit_module_exists():
    assert importlib.util.find_spec('src.analysis.final_ensemble_audit') is not None


def test_complete_hash_chain_is_verified(tmp_path):
    from src.analysis.final_ensemble_audit import verify_stage_chain
    expected = chain(tmp_path)
    assert verify_stage_chain(tmp_path) == expected


def test_payload_change_without_resealing_fails(tmp_path):
    from src.analysis.final_ensemble_audit import verify_stage_chain
    chain(tmp_path)
    path = tmp_path/'protocol.json'
    record = json.loads(path.read_text()); record['payload']['version'] = 'changed'
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match='hash|seal'):
        verify_stage_chain(tmp_path)


def test_validly_resealed_broken_parent_link_fails(tmp_path):
    from src.analysis.final_ensemble_audit import verify_stage_chain
    values = chain(tmp_path)
    values['validation_gate']['development_hash'] = '0'*64
    seal(tmp_path/'validation_gate.json', values['validation_gate'])
    with pytest.raises(ValueError, match='chain|link'):
        verify_stage_chain(tmp_path)


@pytest.mark.parametrize('field,value', [('model_selection_evaluations', 2), ('final_start', 1130)])
def test_final_stage_cannot_claim_multiple_evaluations_or_shift_scope(tmp_path, field, value):
    from src.analysis.final_ensemble_audit import verify_stage_chain
    values = chain(tmp_path); values['final_started'][field] = value
    seal(tmp_path/'final_started.json', values['final_started'])
    with pytest.raises(ValueError):
        verify_stage_chain(tmp_path)


def test_frozen_rank_artifact_must_match_independent_number_ranks(tmp_path):
    from src.analysis.final_ensemble_audit import verify_frozen_rankings, independent_combine
    ranks = np.stack([np.arange(1, 46), np.arange(45, 0, -1)], axis=0)[None]
    expected = independent_combine(ranks, [.5, .5])
    assert expected.tolist() == [list(range(1, 46))]
    actual = np.array([[True]*6+[False]*39])
    path = tmp_path/'rankings.npz'
    np.savez(path, targets=np.array([1131]), actual=actual, SelectedEnsemble=expected)
    verify_frozen_rankings(path, np.array([1131]), actual, dict(SelectedEnsemble=expected))
    changed = expected.copy(); changed[0, :2] = [2, 1]
    np.savez(path, targets=np.array([1131]), actual=actual, SelectedEnsemble=changed)
    with pytest.raises(ValueError, match='rank'):
        verify_frozen_rankings(path, np.array([1131]), actual, dict(SelectedEnsemble=expected))


def test_independent_metric_oracle_counts_actual_winners():
    from src.analysis.final_ensemble_audit import independent_metrics
    actual = np.zeros((2, 45), dtype=bool)
    actual[0, :6] = True; actual[1, 6:12] = True
    values = independent_metrics(np.tile(np.arange(1, 46), (2, 1)), actual)
    assert values['avg_top6'] == 3
    assert values['mean_winning_rank'] == 6.5
    assert values['hits0'] == 1 and values['hits6'] == 1
    assert values['recall10'] == pytest.approx(5/6)
    assert values['all6_pool12'] == 2


def test_final_decision_cannot_promote_after_failed_validation():
    import pandas as pd
    from src.analysis.final_ensemble_audit import independent_decision
    perf = pd.DataFrame([dict(scope='final', model=n, mean_winning_rank=m, avg_top6=.8)
                         for n, m in [('SelectedEnsemble', 22), ('GapLogistic', 23), ('RandomModel', 24)]])
    paired = pd.DataFrame([dict(scope='final', block=26, metric='mean_winning_rank_improvement', simultaneous_low=.5)])
    placebos = pd.DataFrame([dict(kind=k, gate_passed=True, final_rank_gain=.2, final_promoted_gain=.2)
                            for k in ('random_weight', 'random_candidate')])
    robustness = pd.DataFrame([dict(start=1131, model=n, mean_winning_rank=m)
                               for n, m in [('SelectedEnsemble', 22), ('GapLogistic', 23)]])
    result = independent_decision(perf, paired, placebos, robustness, perf, 'GapLogistic', False)
    assert result['status'] == 'NO_ENSEMBLE_ADVANTAGE_ESTABLISHED'
    assert result['final_point_gate'] is True
    assert result['placebo_comparison']['observed_promoted_gain'] == 0
    assert result['placebo_comparison']['promotion_tail_fractions'] == {'random_candidate': None, 'random_weight': None}


def test_causal_but_wrong_gap_calendar_is_rejected():
    import pandas as pd
    from src.analysis.final_ensemble_audit import verify_fit_calendar
    row = dict(model='GapLogistic', target_draw=928, feature_cutoff=927,
               training_cutoff=926, outer_fit_cutoff=926)
    verify_fit_calendar(pd.DataFrame([row]), 26)
    row['training_cutoff'] = 925
    with pytest.raises(ValueError, match='calendar|cutoff'):
        verify_fit_calendar(pd.DataFrame([row]), 26)
