"""Development selection, causal descriptive regimes, and the model gate."""
import numpy as np
import pandas as pd
import pytest

from src.analysis.spatiotemporal import iid_surrogate


def test_real_entropy_regime_integration_keeps_cutoffs():
    from src.analysis.complexity_regimes import regime_diagnostic
    x=iid_surrogate(155,seed=88)
    spec=dict(window=104,representation='number01',kind='block_entropy',L=3)
    a=regime_diagnostic(x[:140],spec,min_past=10)
    b=regime_diagnostic(x,spec,min_past=10)
    pd.testing.assert_frame_equal(a,b[b.target_draw<=140].reset_index(drop=True))
    assert a.target_draw.max()==140 and a.endpoint.max()==139


def test_complexity_cli_rejects_future_suffix_and_has_no_publication_action(tmp_path):
    from pathlib import Path
    from src.complexity_cli import guard,load_research_source
    from src.cli import _parser
    p=tmp_path/'future.csv';p.write_bytes(Path('data/raw/lotto_history.csv').read_bytes()+b'1246,FUTURE_UNPARSED\xff\n')
    with pytest.raises(ValueError,match='unknown suffix'):load_research_source(p)
    with pytest.raises(ValueError):guard('reports/prospective')
    with pytest.raises(SystemExit):_parser().parse_args(['complexity','prepare-freeze'])


def raw_metrics(draws=900):
    metadata = [dict(scope=scope, representation='number_01', kind='block_entropy',
                     L=3, window=104, endpoint=endpoint, family='entropy')
                for scope, endpoint in [('whole', None), ('rolling', 104),
                                         ('rolling', 208), ('rolling', 312)]]
    return dict(draws=draws, keys=['whole', 'first', 'second', 'sparse'],
                families=['entropy'] * 4, values=np.array([0., 1., 2., np.nan]),
                metadata=metadata)


def comparisons():
    return pd.DataFrame([dict(scope='development', cutoff=900, family=family,
                              null_model=null, adjusted_p=1.)
                         for family in ('entropy', 'conditional', 'ordinal', 'lz',
                                        'compression', 'chronological')
                         for null in ('iid', 'fixed_margins', 'draw_shuffle')])


def supported_comparisons():
    frame = comparisons()
    frame.loc[(frame.family == 'conditional') &
              frame.null_model.isin(['iid', 'fixed_margins']), 'adjusted_p'] = .05
    return frame


def low_rows():
    return pd.DataFrame(dict(target_draw=np.arange(501, 901), state='LOW', excess=.1))


def test_selection_uses_finite_development_rolling_max_and_freezes_parameters():
    from src.analysis.complexity_regimes import choose_development
    raw = raw_metrics()
    selected = choose_development(raw, np.array([100., 3., 4., np.nan]))
    assert selected['selected_key'] == 'second' and selected['z'] == 4.
    assert selected['spec']['window'] == 104 and selected['spec']['L'] == 3
    assert 'endpoint' not in selected['spec']
    raw['metadata'][2]['L'] = 5
    assert selected['spec']['L'] == 3
    with pytest.raises(TypeError):
        selected['spec']['L'] = 4
    assert choose_development(raw, [100., 4., 4., np.nan])['selected_key'] == 'first'


@pytest.mark.parametrize('draws', [899, 901, 1245])
def test_selection_rejects_any_scope_other_than_exact_development(draws):
    from src.analysis.complexity_regimes import choose_development
    with pytest.raises(ValueError, match='900'):
        choose_development(raw_metrics(draws), [1., 2., 3., np.nan])


def test_selection_refuses_missing_support_or_vector_mismatch():
    from src.analysis.complexity_regimes import choose_development
    with pytest.raises(ValueError):
        choose_development(raw_metrics(), [1., np.nan, np.nan, np.nan])
    with pytest.raises(ValueError):
        choose_development(raw_metrics(), [1., 2.])


def test_regime_threshold_excludes_current_and_metric_receives_only_past(monkeypatch):
    from src.analysis import complexity_regimes as module
    x = iid_surrogate(110, seed=19)
    received = []
    def metric(prefix, spec):
        received.append(len(prefix))
        np.testing.assert_array_equal(prefix, x[:len(prefix)])
        return float(len(prefix))
    monkeypatch.setattr(module, 'oriented_cell', metric)
    rows = module.regime_diagnostic(x, dict(window=3), min_past=104)
    assert received == list(range(3, 110))
    assert rows.iloc[103].state == 'UNKNOWN'
    row = rows.iloc[104]
    assert row.endpoint == 107 and row.target_draw == 108 and row.state == 'LOW'
    assert row.q_low == pytest.approx(37 + 1/3)
    assert row.q_high == pytest.approx(71 + 2/3)
    current, following = x[106], x[107]
    assert row.overlap == int(np.logical_and(current, following).sum())
    assert row.own_expected_overlap == pytest.approx(x[:107].mean(axis=0)[current].sum())
    assert row.excess == pytest.approx(row.overlap - row.own_expected_overlap)
    numbers = np.flatnonzero(following) + 1
    assert row.next_sum == numbers.sum() and row.next_range == numbers[-1] - numbers[0]


def test_append_cannot_change_earlier_metrics_thresholds_or_outcomes(monkeypatch):
    from src.analysis import complexity_regimes as module
    x = iid_surrogate(120, seed=29)
    monkeypatch.setattr(module, 'oriented_cell', lambda prefix, spec: float(len(prefix) % 7))
    before = module.regime_diagnostic(x[:110], dict(window=3), min_past=4)
    after = module.regime_diagnostic(x, dict(window=3), min_past=4)
    pd.testing.assert_frame_equal(before, after.iloc[:len(before)].reset_index(drop=True))


def test_tied_thresholds_are_normal_and_sparse_metrics_are_unknown(monkeypatch):
    from src.analysis import complexity_regimes as module
    x = iid_surrogate(12, seed=39)
    monkeypatch.setattr(module, 'oriented_cell', lambda prefix, spec: np.nan if len(prefix) == 9 else 1.)
    rows = module.regime_diagnostic(x, dict(window=3), min_past=4)
    assert rows.state.tolist() == ['UNKNOWN'] * 4 + ['NORMAL', 'NORMAL', 'UNKNOWN', 'NORMAL', 'NORMAL']


def test_diagnostic_never_creates_a_1246_target_and_rejects_future_matrix(monkeypatch):
    from src.analysis import complexity_regimes as module
    monkeypatch.setattr(module, 'oriented_cell', lambda prefix, spec: 1.)
    rows = module.regime_diagnostic(iid_surrogate(1245, seed=49), dict(window=104))
    assert rows.target_draw.max() == 1245 and rows.endpoint.max() == 1244
    with pytest.raises(ValueError):
        module.regime_diagnostic(iid_surrogate(1246, seed=49), dict(window=104))
    with pytest.raises(ValueError):
        module.regime_diagnostic(iid_surrogate(110, seed=49), dict(window=104), development_end=901)


def test_gate_requires_temporal_structure_and_positive_both_development_halves():
    from src.analysis.complexity_regimes import development_gate
    passed = development_gate(supported_comparisons(), low_rows(), research_cutoff=900)
    assert passed['model_justified'] and passed['structure_supported']
    assert passed['low_support'] == 400
    assert passed['halves_means'] == pytest.approx({'501..700': .1, '701..900': .1})
    failed = low_rows()
    failed.loc[failed.target_draw > 700, 'excess'] = .05
    assert not development_gate(supported_comparisons(), failed, research_cutoff=900)['model_justified']
    assert not development_gate(comparisons(), low_rows(), research_cutoff=900)['model_justified']
    only_entropy = comparisons()
    only_entropy.loc[only_entropy.family == 'entropy', 'adjusted_p'] = .001
    assert not development_gate(only_entropy, low_rows(), research_cutoff=900)['structure_supported']


def test_gate_allows_shuffle_chronological_and_counts_only_development_low_rows():
    from src.analysis.complexity_regimes import development_gate
    frame = comparisons()
    frame.loc[(frame.family == 'chronological') &
              (frame.null_model == 'draw_shuffle'), 'adjusted_p'] = .01
    rows = pd.concat([low_rows().iloc[[0, -1]],
                      pd.DataFrame(dict(target_draw=np.arange(901, 1246), state='LOW', excess=10.))])
    result = development_gate(frame, rows, research_cutoff=900)
    assert result['structure_supported'] and result['low_support'] == 2
    assert not result['model_justified']
    assert result['halves_means'] == pytest.approx({'501..700': .1, '701..900': .1})


def test_gate_rejects_full_scope_and_non_development_cutoff():
    from src.analysis.complexity_regimes import development_gate
    for invalid in (supported_comparisons().assign(scope='full'),
                    supported_comparisons().assign(cutoff=1245),
                    supported_comparisons().iloc[:-1]):
        with pytest.raises(ValueError):
            development_gate(invalid, low_rows(), research_cutoff=900)
    with pytest.raises(ValueError):
        development_gate(supported_comparisons(), low_rows(), research_cutoff=1245)
    with pytest.raises(TypeError):
        development_gate(supported_comparisons(), low_rows())


def test_existing_publication_guard_leaves_absent_archive_pending(tmp_path):
    from src.phase15_freeze import prepare_freeze, PENDING
    with pytest.raises(ValueError, match=PENDING):
        prepare_freeze(tmp_path/'no-selection', tmp_path/'no-archive')
    with pytest.raises(ValueError):
        prepare_freeze(tmp_path/'no-selection', tmp_path/'no-archive', target=1246)
    assert list(tmp_path.iterdir()) == []
