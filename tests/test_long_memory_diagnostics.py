"""Independent checks of H20 descriptive calibration and bootstrap outputs."""
import numpy as np
import pytest


def test_finite_sample_calibration_uses_matching_raw_persistent_cells():
    from src.analysis.long_memory_diagnostics import finite_sample_table
    observed = np.full(55, .7)
    null = np.tile(np.array([.4, .6, .5, .9])[:, None], (1, 55))
    # A later, unrelated cell must never contaminate alpha calibration.
    null = np.column_stack((null, np.full(4, 100.)))
    metadata = [dict(family='persistent', column=j) for j in range(55)]
    metadata.append(dict(family='rolling', column=0))
    rows = finite_sample_table(observed, [f's{j}' for j in range(55)],
                               null, metadata, ['iid']*2+['fixed_margins']*2)
    assert len(rows) == 55
    assert rows[0]['observed_alpha'] == .7
    assert rows[0]['iid_median'] == pytest.approx(.5)
    assert rows[0]['fixed_margins_median'] == pytest.approx(.7)
    assert rows[0]['iid_centered_alpha'] == pytest.approx(.2)
    assert rows[0]['fixed_margins_centered_alpha'] == pytest.approx(0.)
    assert rows[0]['iid_percentile'] == 1.
    assert rows[0]['fixed_margins_percentile'] == .5


def test_moving_block_bootstrap_reports_finite_reproducible_alpha_intervals():
    from src.analysis.long_memory_diagnostics import moving_block_bootstrap
    values = np.random.default_rng(31).normal(size=(416, 2))
    a = moving_block_bootstrap(values, ['a', 'b'], block_lengths=(26,),
                               replicates=9, seed=211999)
    b = moving_block_bootstrap(values, ['a', 'b'], block_lengths=(26,),
                               replicates=9, seed=211999)
    assert a == b
    assert len(a) == 2
    for row in a:
        assert np.isfinite([row['alpha'], row['ci_low'], row['ci_high']]).all()
        assert row['ci_low'] <= row['ci_high']
        assert row['replicates'] == row['finite_replicates'] == 9
        assert row['block_length'] == 26
        assert 'asymptotic' in row['limitation']


def test_diagnostics_rejects_future_and_noncanonical_cutoffs_before_writes(tmp_path):
    from src.analysis.long_memory_diagnostics import diagnostics
    x = np.zeros((1246, 45), dtype=bool)
    x[:, :6] = True
    with pytest.raises(ValueError):
        diagnostics(x, tmp_path)
    with pytest.raises(ValueError):
        diagnostics(x[:416], tmp_path)
    assert not list(tmp_path.iterdir())


def test_plot_bundle_contains_ten_nonempty_standalone_figures(tmp_path):
    import pandas as pd
    from src.analysis.long_memory_diagnostics import _plots
    from src.analysis.long_memory import dfa, crossover
    from src.analysis.long_memory_series import build_series, aggregation
    from src.analysis.spatiotemporal import iid_surrogate
    representation = build_series(iid_surrogate(416, seed=71))
    curve = dfa(representation['values'])
    raw = dict(representations=representation, curve=curve, cross=crossover(curve),
               aggregation=aggregation(representation['values']),
               rolling=[dict(window=416, end=416, alpha=curve['alpha'])])
    comparison = pd.DataFrame([
        dict(scope='full', null_model=model, family='persistent', real_max=2., null_median=1.)
        for model in ('iid', 'fixed_margins')])
    calibration = [dict(iid_median=.5, fixed_margins_median=.51) for _ in range(55)]
    files = _plots(raw, [0, 1, 45], {'iid': raw['curve'], 'fixed_margins': raw['curve']},
                   comparison, calibration, tmp_path)
    assert len(files) == len(set(files)) == 10
    for filename in files:
        path = tmp_path/filename
        assert path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
        assert path.stat().st_size > 1000


def test_canonical_diagnostics_rejects_outside_directory_without_creating_files(tmp_path):
    from src.analysis.long_memory_diagnostics import diagnostics
    from src.analysis.spatiotemporal import iid_surrogate
    with pytest.raises(ValueError, match='output'):
        diagnostics(iid_surrogate(1245, seed=3), tmp_path)
    assert not list(tmp_path.iterdir())


def test_diagnostics_preserves_existing_outputs_before_reading_inputs(tmp_path, monkeypatch):
    import src.analysis.long_memory_diagnostics as module
    from src.analysis.spatiotemporal import iid_surrogate
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    directory = tmp_path/'reports'/'long_memory'
    directory.mkdir(parents=True)
    output = directory/'diagnostics.json'
    output.write_text('existing research output', encoding='utf-8')
    with pytest.raises(FileExistsError):
        module.diagnostics(iid_surrogate(1245, seed=3), directory)
    assert output.read_text(encoding='utf-8') == 'existing research output'
    assert sorted(p.name for p in directory.iterdir()) == ['diagnostics.json']
