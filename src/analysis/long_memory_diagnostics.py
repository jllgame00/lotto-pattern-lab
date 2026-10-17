"""Descriptive H20 plots, finite-sample baselines, and sensitivity checks.

These outputs describe the historical sample. Selection of a visually unusual
curve and block-bootstrap intervals do not establish an asymptotic Hurst
exponent or predictive skill; inference uses the complete-search null tests.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .long_memory import dfa
from .long_memory_search import metric_vector
from .long_memory_series import build_series
from .recurrence import research_matrix
from .spatiotemporal import constrained_surrogate, iid_surrogate


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_LIMITATION = (
    'Circular moving-block bootstrap intervals are descriptive, conditional on '
    'selected series and finite block length; they do not prove asymptotic H '
    'or account for selection across all search cells.'
)


def finite_sample_table(observed, names, null_values, metadata, models):
    """Calibrate each whole-curve alpha against its matching raw null cell.

    Percentiles are empirical fractions <= observed, without a p-value claim.
    Centered alpha is observed minus the model-specific finite-sample median.
    """
    observed = np.asarray(observed, float)
    null_values = np.asarray(null_values, float)
    models = np.asarray(models)
    if (observed.shape != (55,) or len(names) != 55 or null_values.ndim != 2
            or null_values.shape != (len(models), len(metadata))):
        raise ValueError('Aligned 55-series alpha and raw null inventory required')
    indices = {}
    for i, meta in enumerate(metadata):
        if meta['family'] == 'persistent':
            column = int(meta['column'])
            if column in indices:
                raise ValueError('Duplicate persistent calibration cell')
            indices[column] = i
    if set(indices) != set(range(55)):
        raise ValueError('Exactly one raw persistent alpha cell per series required')
    rows = []
    for j, name in enumerate(names):
        row = dict(series=name, column=j, observed_alpha=float(observed[j]))
        for model in ('iid', 'fixed_margins'):
            a = null_values[models == model, indices[j]]
            a = a[np.isfinite(a)]
            if not len(a):
                raise ValueError(f'No finite {model} alpha calibration for {name}')
            median = float(np.median(a))
            row.update({f'{model}_median': median,
                        f'{model}_centered_alpha': float(observed[j]-median),
                        f'{model}_percentile': float(np.mean(a <= observed[j])),
                        f'{model}_replicates': len(a)})
        rows.append(row)
    return rows


def moving_block_bootstrap(values, names, *, block_lengths=(26, 52),
                           replicates=199, seed=211999):
    """Circular blocks of jointly sampled observations, with each DFA refitted."""
    values = np.asarray(values, float)
    if values.ndim == 1:
        values = values[:, None]
    if (values.ndim != 2 or values.shape[1] != len(names)
            or not np.isfinite(values).all() or len(values) < 208
            or type(replicates) is not int or replicates < 2):
        raise ValueError('Finite aligned series and at least two replicates required')
    n = len(values)
    observed = dfa(values)['alpha']
    rows = []
    for block in block_lengths:
        if type(block) is not int or not 1 <= block <= n:
            raise ValueError('Block lengths must be positive integers no longer than the sample')
        rng = np.random.default_rng(np.random.SeedSequence([seed, n, block]))
        samples = []
        for _ in range(replicates):
            starts = rng.integers(0, n, size=int(np.ceil(n/block)))
            indices = ((starts[:, None]+np.arange(block)) % n).ravel()[:n]
            samples.append(dfa(values[indices])['alpha'])
        samples = np.asarray(samples)
        for j, name in enumerate(names):
            a = samples[:, j]
            a = a[np.isfinite(a)]
            low, high = np.quantile(a, [.025, .975]) if len(a) else (np.nan, np.nan)
            rows.append(dict(series=name, alpha=float(observed[j]), block_length=block,
                             replicates=replicates, finite_replicates=len(a),
                             ci_low=float(low), ci_high=float(high), seed=seed,
                             limitation=BOOTSTRAP_LIMITATION))
    return rows


def _series_record(raw, j):
    curve = raw['curve']
    return dict(series=raw['representations']['names'][j], column=int(j),
                group=raw['representations']['groups'][j], alpha=float(curve['alpha'][j]),
                r2=float(curve['r2'][j]), curvature=float(curve['curvature'][j]),
                scales=curve['scales'].tolist(),
                fluctuation=curve['fluctuation'][:, j].tolist())


def _json_safe(value):
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, np.integer):
        return int(value)
    return value


def _plots(raw, selected, matched, comparison, calibration, directory):
    """Ten standalone figures, all based on the declared historical sample."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    paths = []
    names = raw['representations']['names']
    alpha = raw['curve']['alpha']

    def save(fig, filename):
        fig.tight_layout()
        path = directory/filename
        if path.exists():
            raise FileExistsError(path)
        fig.savefig(path, dpi=150)
        plt.close(fig)
        paths.append(path.name)

    def curve_plot(curve, j, title, filename):
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.loglog(curve['scales'], curve['fluctuation'][:, j], 'o-')
        ax.set(xlabel='Scale (draws)', ylabel='DFA fluctuation F(s)',
               title=f"{title}: {names[j]}, alpha={curve['alpha'][j]:.3f}, R²={curve['r2'][j]:.3f}")
        save(fig, filename)

    j = selected[0]
    curve_plot(raw['curve'], j, 'Real selected raw persistent curve', 'selected_real_dfa.png')
    for model, curve in matched.items():
        curve_plot(curve, j, f'{model} matched series (seed 211234)', f'selected_{model}_dfa.png')

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(alpha[:45], bins=12, edgecolor='white')
    ax.axvline(.5, color='gray', linestyle='--', label='0.5 reference (not a decision threshold)')
    ax.set(xlabel='Whole-curve DFA1 alpha', ylabel='Number series', title='45 number alpha distribution')
    ax.legend(fontsize=8)
    save(fig, 'number_alpha_distribution.png')

    fig, ax = plt.subplots(figsize=(10, 5))
    frame = comparison[comparison.scope == 'full'] if 'scope' in comparison else comparison
    for model, group in frame.groupby('null_model', sort=False):
        ax.plot(group.family, group.real_max, 'o-', label=f'{model}: real maximum')
        ax.plot(group.family, group.null_median, 'x--', label=f'{model}: null median maximum')
    ax.tick_params(axis='x', rotation=35)
    ax.set(ylabel='Pilot-standardized search statistic', title='Complete-search global extremes')
    ax.legend(fontsize=8)
    save(fig, 'global_extremes.png')

    fig, ax = plt.subplots(figsize=(10, 5))
    image = ax.imshow(raw['cross']['improvement'], aspect='auto', vmin=0, vmax=1)
    ax.set(yticks=np.arange(len(raw['cross']['boundaries'])),
           yticklabels=raw['cross']['boundaries'], xlabel='Series column (0..54)',
           ylabel='Crossover boundary', title='Continuous-hinge SSE improvement')
    fig.colorbar(image, ax=ax, label='Fractional SSE reduction')
    save(fig, 'crossovers.png')

    fig, ax = plt.subplots(figsize=(8, 5))
    for j in selected:
        ax.loglog(raw['aggregation']['blocks'], raw['aggregation']['variance'][:, j],
                  'o-', label=f"{names[j]} ({raw['aggregation']['slope'][j]:.3f})")
    ax.set(xlabel='Aggregation block length', ylabel='Variance of block means',
           title='Selected series aggregation (legend: slope)')
    ax.legend(fontsize=8)
    save(fig, 'aggregation.png')

    fig, ax = plt.subplots(figsize=(10, 5))
    for window in (312, 416, 624):
        rows = [r for r in raw['rolling'] if r['window'] == window]
        ax.plot([r['end'] for r in rows], [r['alpha'][selected[0]] for r in rows],
                'o-', markersize=3, label=f'W={window}')
    ax.set(xlabel='Last historical draw in window', ylabel='Locally refitted DFA1 alpha',
           title=f'Rolling curves: {names[selected[0]]}')
    ax.legend()
    save(fig, 'rolling_alpha.png')

    fig, ax = plt.subplots(figsize=(8, 5))
    for j in range(45, 55):
        ax.loglog(raw['curve']['scales'], raw['curve']['fluctuation'][:, j], label=names[j])
    ax.set(xlabel='Scale (draws)', ylabel='DFA fluctuation F(s)', title='Whole-system shape and band curves')
    ax.legend(fontsize=7)
    save(fig, 'whole_system_dfa.png')

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(np.arange(55), alpha, '.', label='Observed alpha')
    ax.plot(np.arange(55), [r['iid_median'] for r in calibration], '.', label='IID median alpha')
    ax.plot(np.arange(55), [r['fixed_margins_median'] for r in calibration], '.', label='Fixed-margin median alpha')
    ax.set(xlabel='Series column (0..54)', ylabel='DFA1 alpha', title='Finite-sample calibration (55 series)')
    ax.legend(fontsize=8)
    save(fig, 'finite_sample_alpha.png')
    return paths


def diagnostics(x, directory):
    """Write new H20 diagnostics beneath ROOT/reports/long_memory only.

    Requires the canonical full-sample search and its 398 null vectors first.
    Existing diagnostic outputs are never silently replaced.
    """
    x = research_matrix(x)
    if len(x) != 1245:
        raise ValueError('Canonical diagnostics require exactly historical draws 1..1245')
    directory = Path(directory).resolve()
    if directory != (ROOT/'reports'/'long_memory').resolve():
        raise ValueError('Diagnostics output must be ROOT/reports/long_memory')
    filenames = ('diagnostics.json', 'finite_sample_alpha_calibration.csv',
                 'moving_block_bootstrap.csv', 'temporal_robustness.csv',
                 'rolling_alpha.csv', 'dfa2_sensitivity.csv', 'rs_spectral_secondary.csv',
                 'whole_system_alpha.csv')
    plot_names = ('selected_real_dfa.png', 'selected_iid_dfa.png', 'selected_fixed_margins_dfa.png',
                  'number_alpha_distribution.png', 'global_extremes.png', 'crossovers.png',
                  'aggregation.png', 'rolling_alpha.png', 'whole_system_dfa.png', 'finite_sample_alpha.png')
    targets = [directory/f for f in filenames]+[directory/'plots'/f for f in plot_names]
    existing = [str(p) for p in targets if p.exists()]
    if existing:
        raise FileExistsError('Refusing to replace diagnostics: '+', '.join(existing))
    calibration_meta = json.loads((directory/'calibration_1245.json').read_text(encoding='utf-8'))
    real_summary = json.loads((directory/'real_summary.json').read_text(encoding='utf-8'))
    metrics = pd.read_csv(directory/'full_metrics.csv')
    comparison = pd.read_csv(directory/'global_null_comparison.csv')
    with np.load(directory/'null_metrics_full.npz', allow_pickle=False) as archive:
        null_values = archive['values']
    raw = metric_vector(x, details=True)
    if (calibration_meta['keys'] != raw['keys'] or null_values.shape != (398, len(raw['keys']))
            or len(metrics) != len(raw['keys'])):
        raise ValueError('Canonical raw-null inventory does not match diagnostics search')
    if not np.allclose(metrics['value'], raw['values'], equal_nan=True):
        raise ValueError('Stored real metrics do not match supplied historical sample')
    rep = raw['representations']
    alpha = raw['curve']['alpha']
    persistent = int(np.nanargmax(alpha[:45]))
    anti = int(np.nanargmin(alpha[:45]))
    system = 45+int(np.nanargmax(abs(alpha[45:]-.5)))
    selected = list(dict.fromkeys((persistent, anti, system)))
    calibrated = finite_sample_table(alpha, rep['names'], null_values,
                                    calibration_meta['metadata'], ['iid']*199+['fixed_margins']*199)
    bootstrap = moving_block_bootstrap(rep['values'][:, selected], [rep['names'][j] for j in selected])
    temporal = []
    for label, start, end in (('early', 0, 415), ('middle', 415, 830), ('recent', 830, 1245)):
        curve = dfa(rep['values'][start:end])
        for j, name in enumerate(rep['names']):
            temporal.append(dict(era=label, start=start+1, end=end, series=name, column=j,
                                 alpha=curve['alpha'][j], r2=curve['r2'][j],
                                 curvature=curve['curvature'][j], usable_scales=curve['usable_scales']))
    rolling = [dict(window=row['window'], start=row['end']-row['window']+1, end=row['end'],
                    series=rep['names'][j], column=j, alpha=value,
                    absolute_deviation=abs(value-.5))
               for row in raw['rolling'] for j, value in enumerate(row['alpha'])]
    sensitivity = [dict(series=name, column=j, dfa1_alpha=alpha[j],
                        dfa2_alpha=raw['sensitivity']['alpha'][j],
                        dfa2_r2=raw['sensitivity']['r2'][j],
                        difference=raw['sensitivity']['alpha'][j]-alpha[j], secondary=True)
                   for j, name in enumerate(rep['names'])]
    secondary = [dict(series=name, column=j, rs_exponent=raw['rs']['exponent'][j],
                      spectral_beta=raw['spectral']['beta'][j], spectral_r2=raw['spectral']['r2'][j],
                      spectral_bins=raw['spectral']['bins'], secondary=True)
                 for j, name in enumerate(rep['names'])]
    whole = [_series_record(raw, j) for j in range(45, 55)]
    b, j = np.unravel_index(np.nanargmax(raw['cross']['improvement']), raw['cross']['improvement'].shape)
    cross = dict(_series_record(raw, j), boundary=int(raw['cross']['boundaries'][b]),
                 improvement=float(raw['cross']['improvement'][b, j]),
                 short_alpha=float(raw['cross']['short_alpha'][b, j]),
                 long_alpha=float(raw['cross']['long_alpha'][b, j]))
    rolling_strongest = max(rolling, key=lambda r: r['absolute_deviation'] if np.isfinite(r['alpha']) else -np.inf)
    matched = {
        'iid': dfa(build_series(iid_surrogate(1245, seed=211234))['values']),
        'fixed_margins': dfa(build_series(constrained_surrogate(x, seed=211234))['values']),
    }
    summary = dict(draws=1245, descriptive_only=True, representation_hash=raw['representation_hash'],
                   strongest_persistent=_series_record(raw, persistent),
                   strongest_anti_persistent=_series_record(raw, anti),
                   strongest_crossover=cross, strongest_whole_system=_series_record(raw, system),
                   whole_system=whole, rolling_strongest=rolling_strongest,
                   bootstrap=bootstrap, bootstrap_limitation=BOOTSTRAP_LIMITATION,
                   selected_columns=selected, matched_seed=211234,
                   matched_curves={model: dict(series=rep['names'][persistent], column=persistent,
                                               alpha=curve['alpha'][persistent], r2=curve['r2'][persistent],
                                               scales=curve['scales'], fluctuation=curve['fluctuation'][:, persistent])
                                   for model, curve in matched.items()},
                   saved_search_scopes=list(real_summary),
                   inferential_reference='global_null_comparison.csv: complete-search null maxima with family correction')
    (directory/'plots').mkdir(parents=True, exist_ok=True)
    summary['plots'] = _plots(raw, selected, matched, comparison, calibrated, directory/'plots')
    for filename, rows in zip(filenames[1:], (calibrated, bootstrap, temporal, rolling, sensitivity, secondary, whole)):
        pd.DataFrame(rows).to_csv(directory/filename, index=False)
    (directory/'diagnostics.json').write_text(json.dumps(_json_safe(summary), ensure_ascii=False,
                                                       indent=2, allow_nan=False)+'\n', encoding='utf-8')
    return summary
