"""Diagnostics must retain source identity and never rebuild forecasts."""
from hashlib import sha256
import importlib
import json

import numpy as np
import pandas as pd
import pytest


def module():
    return importlib.import_module('src.analysis.point_process_diagnostics')


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    d = module()
    monkeypatch.setattr(d, 'ROOT', tmp_path)
    rng = np.random.default_rng(20)
    x = np.zeros((208, 45), dtype=bool)
    for row in x:
        row[rng.choice(45, 6, replace=False)] = True
    out = tmp_path/'reports/point_process/example'
    out.mkdir(parents=True)
    leaders = {}
    for family, source, target in [('self_positive', 1, 1), ('self_negative', 2, 2),
                                    ('cross_positive', 3, 4), ('cross_negative', 5, 6)]:
        leaders[family] = dict(key=family, source=source, target=target, lag=1, z=2)
    full = dict(draws=len(x), representation_hash=sha256(x.tobytes()).hexdigest(),
                leaders=leaders, maxima={f:2 for f in (*leaders, 'renewal', 'kernel')})
    (out/'real_summary.json').write_text(json.dumps(dict(full=full)), encoding='utf-8')
    pd.DataFrame([dict(scope='full', null_model=kind, replicate=r,
                      **{f:float(r)/4 for f in full['maxima']})
                  for kind in ('iid', 'fixed_margins') for r in range(4)]).to_csv(out/'null_maxima.csv', index=False)
    selection = dict(development_matrix_hash=sha256(x.tobytes()).hexdigest())
    digest = sha256(json.dumps(selection, sort_keys=True, allow_nan=False).encode()).hexdigest()
    (out/'selected_configuration.json').write_text(json.dumps(dict(selection=selection, sha256=digest)), encoding='utf-8')
    forecast = {str(i):.05 + i/1000 for i in range(1, 46)}
    diag = [dict(number=i, probability=forecast[str(i)], baseline=.1,
                 self_contribution=.01, cross_contribution=-.01, incoming=[],
                 training_cutoff=180, source_cutoff=207) for i in range(1, 46)]
    walk = out/'walk_forward_26'
    walk.mkdir()
    pd.DataFrame([dict(model='HawkesInfluenceModel', target_draw=208,
                      outer_fit_cutoff=180, edge_training_cutoff=180, source_cutoff=207,
                      ranking=json.dumps(list(range(45, 0, -1))), scores=json.dumps(forecast),
                      actual=json.dumps((np.flatnonzero(x[-1])+1).tolist()),
                      last_diagnostic=json.dumps(diag), selected_edges=json.dumps([[]]*45),
                      coefficients=json.dumps([.2, .3]))]).to_csv(walk/'predictions.csv', index=False)
    return d, x, out


def test_exports_exact_event_history_all_hazards_and_direction_labels(evidence):
    d, x, out = evidence
    source = (out/'walk_forward_26/predictions.csv').read_bytes()
    paths = d.diagnostics(x, out)
    assert paths and all(p.exists() for p in paths)
    with np.load(out/'event_history.npz', allow_pickle=False) as cache:
        np.testing.assert_array_equal(cache['binary'], x)
        events = cache['event_draws'][cache['event_numbers']==1]
        np.testing.assert_array_equal(events, np.flatnonzero(x[:, 0])+1)
        np.testing.assert_array_equal(cache['interarrival_values'][cache['interarrival_numbers']==1], np.diff(events))
        last = np.flatnonzero(x[:, 0])[-1]
        assert cache['current_gap'][0] == len(x)-1-last
        np.testing.assert_array_equal(cache['recent_counts_10'][-1], x[-10:].sum(0))
    hazards = pd.read_csv(out/'renewal_hazards.csv')
    assert len(hazards) == 45*(27+6+5)
    assert {'raw_rate', 'conditional', 'expected_p', 'support', 'marginal_jeffreys_low',
            'marginal_jeffreys_high', 'own_baseline'} <= set(hazards)
    assert ((hazards.marginal_jeffreys_low<=hazards.marginal_jeffreys_high) | (hazards.support==0)).all()
    pooled = pd.read_csv(out/'pooled_renewal.csv')
    assert len(pooled) == 38 and 'frequency_weighted_expected_hits' in pooled
    matrix = pd.read_csv(out/'influence_matrix.csv')
    assert len(matrix) == 2025 and not matrix.full_history_descriptive.any()
    assert matrix.development_frozen.all()
    assert not matrix.forecast.any()
    assert len(pd.read_csv(out/'lag_effects.csv')) == 7*45*45
    assert len(pd.read_csv(out/'kernel_profiles.csv')) == 3*45*45
    assert (out/'walk_forward_26/predictions.csv').read_bytes() == source
    meta = json.loads((out/'diagnostic_metadata.json').read_text())
    assert meta['graph_comparison']['available'] is False
    assert meta['draw1246_used'] is False
    assert 'NaN' not in (out/'diagnostic_metadata.json').read_text()


def test_fixed_relation_identities_and_era_reselection_are_explicit(evidence):
    d, x, out = evidence
    d.diagnostics(x, out)
    table = pd.read_csv(out/'relation_time.csv')
    era = table[table.window_kind=='era']
    assert len(era) == 4*3*7
    assert set(era.source) == {1, 2, 3, 5}
    assert era.candidate_frozen.all() and not era.relation_reselected.any()
    assert era.strongest_lag_descriptive.all()
    assert set(era.groupby('family').source.nunique()) == {1}
    assert era.minimum_source_support.eq(30).all()


def test_event_shuffle_rebuilds_export_and_rejects_stale_identity(evidence):
    d, x, out = evidence
    d.diagnostics(x, out)
    shuffled = x[np.random.default_rng(4).permutation(len(x))]
    with pytest.raises(ValueError, match='source|hash|prefix'):
        d.diagnostics(shuffled, out)
    summary = json.loads((out/'real_summary.json').read_text())
    summary['full']['representation_hash'] = sha256(shuffled.tobytes()).hexdigest()
    (out/'real_summary.json').write_text(json.dumps(summary))
    (out/'walk_forward_26/predictions.csv').unlink()
    d.diagnostics(shuffled, out)
    with np.load(out/'event_history.npz', allow_pickle=False) as cache:
        np.testing.assert_array_equal(cache['binary'], shuffled)
        assert not np.array_equal(cache['gaps'], d.event_history(x)['gaps'])


def test_output_scope_and_1246_are_rejected_before_writes(evidence, tmp_path):
    d, x, out = evidence
    for function in (d.diagnostics, d.plots):
        with pytest.raises(ValueError):
            function(x, tmp_path/'outside')
        with pytest.raises(ValueError):
            function(np.tile(x, (6, 1))[:1246], out)
    assert not (tmp_path/'outside').exists()


def test_graph_artifact_is_verified_before_loading_and_correlations_are_descriptive(evidence):
    d, x, out = evidence
    graph = d.ROOT/'reports/graph_hypergraph'
    graph.mkdir(parents=True)
    a = np.ones((45, 45)); np.fill_diagonal(a, 0)
    np.savez(graph/'structural_cache.npz', adjacency_W26=a[None])
    manifest = dict(research_cutoff=1245, draw1246_used=False,
                    artifacts={'structural_cache.npz':dict(sha256='wrong')})
    (graph/'run_manifest.json').write_text(json.dumps(manifest))
    d.diagnostics(x, out)
    meta = json.loads((out/'diagnostic_metadata.json').read_text())
    assert not meta['graph_comparison']['available']
    assert 'hash' in meta['graph_comparison']['reason'].lower()
    manifest['artifacts']['structural_cache.npz']['sha256'] = sha256((graph/'structural_cache.npz').read_bytes()).hexdigest()
    (graph/'run_manifest.json').write_text(json.dumps(manifest))
    d.diagnostics(x, out)
    meta = json.loads((out/'diagnostic_metadata.json').read_text())
    comparison = meta['graph_comparison']
    assert comparison['available'] and comparison['top_pairs'] == 45
    assert comparison['graph_refitted'] is False
    assert comparison['pair_aggregation'] == 'mean_of_directed_absolute_influence'
    assert set(comparison['correlations']) == {'absolute', 'positive', 'negative'}


def test_stored_prediction_audit_rejects_future_sources_and_wrong_actual(evidence):
    d, x, out = evidence
    file = out/'walk_forward_26/predictions.csv'
    frame = pd.read_csv(file)
    frame.loc[0, 'source_cutoff'] = 208
    frame.to_csv(file, index=False)
    with pytest.raises(ValueError, match='source|cutoff|causal'):
        d.diagnostics(x, out)
    frame.loc[0, 'source_cutoff'] = 207
    frame.loc[0, 'actual'] = json.dumps([1, 2, 3, 4, 5, 6])
    frame.to_csv(file, index=False)
    with pytest.raises(ValueError, match='actual|outcome'):
        d.diagnostics(x, out)


def test_ten_plots_render_using_stored_final_forecast(evidence, monkeypatch):
    d, x, out = evidence
    d.diagnostics(x, out)
    import matplotlib.axes
    observed = []
    original = matplotlib.axes.Axes.bar
    def capture(self, positions, values, *args, **kwargs):
        if len(np.atleast_1d(values)) == 45:
            observed.append(np.asarray(values))
        return original(self, positions, values, *args, **kwargs)
    monkeypatch.setattr(matplotlib.axes.Axes, 'bar', capture)
    paths = d.plots(x, out)
    assert len(paths) == 10
    assert all(p.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') for p in paths)
    assert any(np.allclose(values, .05+np.arange(1, 46)/1000) for values in observed)
    import matplotlib.pyplot as plt
    assert not plt.get_fignums()


def test_plots_require_stored_forecast_instead_of_fitting_a_replacement(evidence):
    d, x, out = evidence
    (out/'walk_forward_26/predictions.csv').unlink()
    with pytest.raises(ValueError, match='stored|forecast|prediction'):
        d.plots(x, out)


def test_development_lag_matrix_is_independent_of_later_events_and_model_archive(evidence):
    d, x, out = evidence
    rng = np.random.default_rng(202)
    x = np.concatenate([x, np.zeros((792, 45), bool)])
    for row in x[208:]:row[rng.choice(45, 6, replace=False)] = True
    (out/'walk_forward_26/predictions.csv').unlink()
    summary = json.loads((out/'real_summary.json').read_text())
    def reset_summary():
        summary['full'].update(draws=len(x), representation_hash=sha256(x.tobytes()).hexdigest())
        (out/'real_summary.json').write_text(json.dumps(summary))
    reset_summary()
    d.diagnostics(x, out)
    first = pd.read_csv(out/'development_frozen_influence.csv')
    assert len(first) == 2025
    assert first.training_cutoff.eq(900).all()
    assert first.development_matrix_hash.eq(sha256(x[:900].tobytes()).hexdigest()).all()
    assert first.development_frozen.all() and not first.forecast.any()
    x[900:] = x[900:][::-1]
    reset_summary()
    d.diagnostics(x, out)
    second = pd.read_csv(out/'development_frozen_influence.csv')
    pd.testing.assert_frame_equal(first[['source', 'target', 'lag', 'effect']],
                                  second[['source', 'target', 'lag', 'effect']])
    meta = json.loads((out/'diagnostic_metadata.json').read_text())
    assert meta['primary_matrix_selection_cutoff'] == 900
    assert meta['graph_comparison_matrix'] == 'development_effect_at_development_selected_lag'
