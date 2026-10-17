"""Stored-output H16 figures; plotting never fits or selects a predictor."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .recurrence import research_matrix
from .symmetry import LAGS, SHIFTS, mirror


def plots(x, directory):
    """Render ten required inspection plots and the secondary shift heatmap.

    ``directory`` is an existing report under reports/symmetry. All statistical
    values and historical predictions come from stored evidence. The supplied
    research matrix certifies the report's prefix, without fitting any model.
    Return the paths of generated PNG files.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    x = research_matrix(x)
    directory = Path(directory).resolve()
    allowed = (Path(__file__).resolve().parents[2] / 'reports' / 'symmetry').resolve()
    if not directory.is_relative_to(allowed):
        raise ValueError('H16 plot output must stay under reports/symmetry')

    def read_json(name):
        return json.loads((directory / name).read_text(encoding='utf-8'))

    same = read_json('same_draw_summary.json')
    real = read_json('real_summary.json')['full']
    if real['draws'] != len(x):
        raise ValueError('Stored full-search cutoff does not match supplied prefix')
    if real.get('representation_hash') != sha256(x.tobytes()).hexdigest():
        raise ValueError('Stored full-search source hash does not match supplied prefix')
    draw = pd.read_csv(directory / 'draw_metrics.csv')
    pooled = pd.read_csv(directory / 'pooled_relations.csv').sort_values('lag')
    pairs = pd.read_csv(directory / 'pair_relations.csv')
    rolling = pd.read_csv(directory / 'rolling_symmetry.csv')
    temporal = pd.read_csv(directory / 'temporal_stability.csv')
    null = pd.read_csv(directory / 'null_maxima.csv')
    null = null[null.scope == 'full']
    predictions = pd.read_csv(directory / 'walk_forward_26' / 'predictions.csv')
    if (draw.draw.tolist() != list(range(1, len(x)+1))
            or int(rolling.endpoint.max()) != len(x)
            or not pooled.target_end.eq(len(x)).all()
            or int(predictions.target_draw.max()) != len(x)
            or temporal.end.max() != len(x)):
        raise ValueError('Stored diagnostic endpoints do not match supplied prefix')
    if len(x) != 1245:
        raise ValueError('Canonical stored historical ranking plot requires cutoff1245')
    if set(pooled.lag) != set(LAGS) or pairs.duplicated(['source', 'lag']).any():
        raise ValueError('Incomplete or duplicate stored lag diagnostics')
    series_path = directory / 'binary_series.npy'
    if series_path.exists() and not np.array_equal(np.load(series_path, allow_pickle=False), x):
        raise ValueError('Stored binary series does not match supplied prefix')

    out = directory / 'plots'
    out.mkdir(parents=True, exist_ok=True)
    paths = []

    def save(fig, name):
        path = out / name
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        paths.append(path)

    def heatmap(values, labels, title, color_label, name, *, size=(10, 8)):
        values = np.asarray(values, dtype=float)
        finite = values[np.isfinite(values)]
        limit = max(float(np.max(np.abs(finite))) if len(finite) else 0., 1e-12)
        fig, ax = plt.subplots(figsize=size)
        cmap = plt.get_cmap('RdBu_r').copy()
        cmap.set_bad('#dddddd')
        im = ax.imshow(np.ma.masked_invalid(values), aspect='auto', interpolation='nearest',
                       cmap=cmap, vmin=-limit, vmax=limit)
        ax.set_xticks(np.arange(len(LAGS)), LAGS)
        ax.set_yticks(np.arange(len(labels)), labels, fontsize=7)
        ax.set_xlabel('Source-to-target lag (draws)')
        ax.set_title(title)
        fig.colorbar(im, ax=ax, label=color_label)
        save(fig, name)

    labels = np.arange(1, 46)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(labels, mirror(labels), 'o-', ms=3, label='mirror(n) = 46 - n')
    ax.scatter([23], [23], s=85, color='#c44e52', zorder=3, label='23: separate fixed point')
    ax.set(xlim=(.5, 45.5), ylim=(.5, 45.5), xlabel='Source number', ylabel='Mirror number',
           title='Fixed reflection around 23: 22 nontrivial pairs')
    ax.set_xticks([1, 5, 10, 15, 20, 23, 25, 30, 35, 40, 45])
    ax.set_yticks([1, 5, 10, 15, 20, 23, 25, 30, 35, 40, 45])
    ax.grid(alpha=.2)
    ax.legend()
    save(fig, 'mirror_mapping.png')

    observed = np.array([same['pair_count_distribution'][str(k)] for k in range(4)], dtype=float)
    if observed.sum() != len(x):
        raise ValueError('Stored same-draw distribution cutoff mismatch')
    iid = np.array([sum(r['probability'] for r in same['iid_joint_distribution'] if r['pairs'] == k)
                    for k in range(4)]) * len(x)
    fixed = same.get('fixed_margin_pair_count_distribution')
    fixed = same.get('fixed_margin_example', {}).get('pair_count_distribution') if fixed is None else fixed
    fig, ax = plt.subplots(figsize=(9, 5))
    width = .25 if fixed is not None else .36
    ax.bar(np.arange(4)-width/2, observed, width, label=f'Observed (N={len(x)})')
    ax.bar(np.arange(4)+width/2, iid, width, label='Exact IID expectation')
    if fixed is not None:
        counts = np.array([fixed[str(k)] for k in range(4)]) if isinstance(fixed, dict) else np.asarray(fixed)
        ax.bar(np.arange(4)+1.5*width, counts, width, label='Stored fixed-margin example')
    ax.set(xticks=np.arange(4), xlabel='Complete nontrivial mirror pairs in one draw', ylabel='Number of draws',
           title='Same-draw reflection: observed and exact IID distribution')
    ax.legend()
    save(fig, 'same_draw_symmetry.png')

    pooled = pooled.set_index('lag').loc[list(LAGS)].reset_index()
    positions = np.arange(len(LAGS))
    fig, ax = plt.subplots(figsize=(10, 5))
    errors = np.maximum(0, np.vstack((pooled.rate-pooled.ci_low, pooled.ci_high-pooled.rate)))
    ax.errorbar(positions, pooled.rate, yerr=errors, fmt='o-', capsize=4,
                label='Observed; 95% block-bootstrap interval')
    ax.scatter([0], [5/44], marker='D', color='#c44e52', label='Lag 0 IID conditional baseline: 5/44')
    ax.plot(positions[1:], np.full(len(LAGS)-1, 6/45), '--', color='grey',
            label='Positive-lag IID baseline: 6/45')
    ax.set(xticks=positions, xticklabels=LAGS, xlabel='Lag (draws)', ylabel='Mapped-target hit rate',
           title='Pooled reflection strength; dependent-event intervals are descriptive')
    ax.legend(fontsize=8)
    save(fig, 'pooled_lag_strength.png')

    order = np.column_stack((np.arange(1, 23), np.arange(45, 23, -1))).ravel()
    pairs = pairs.copy()
    eligible = pairs.eligible.astype(str).str.lower().eq('true')
    pairs['display_risk'] = pairs.risk_difference.where(eligible)
    pair_matrix = pairs.pivot(index='source', columns='lag', values='display_risk').reindex(index=order, columns=LAGS)
    heatmap(pair_matrix, [f'{n} -> {46-n}' for n in order],
            'Directional mirror risk difference (source support >=20)', 'Rate minus aligned baseline',
            'pair_lag_heatmap.png', size=(10, 12))
    rates = pairs.pivot(index='source', columns='lag', values='rate').reindex(index=order, columns=LAGS).to_numpy()
    valid = pairs.assign(valid=eligible).pivot(index='source', columns='lag', values='valid').reindex(index=order, columns=LAGS).to_numpy()
    directional = (rates[::2]-rates[1::2])
    directional[~(valid[::2].astype(bool) & valid[1::2].astype(bool))] = np.nan
    heatmap(directional, [f'{n} <-> {46-n}' for n in range(1, 23)],
            'Directional asymmetry: low-to-high minus high-to-low', 'Conditional-rate difference',
            'directional_asymmetry.png')

    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    for window, group in rolling.groupby('window', sort=True):
        group = group.sort_values('endpoint')
        for ax, column, label in zip(axes,
                ('mean_pairs', 'mean_symmetry', 'mean_imbalance', 'mean_correlation'),
                ('Mean pairs', 'Mean normalized symmetry', 'Mean side imbalance', 'Mean binary pair correlation')):
            ax.plot(group.endpoint, group[column], label=f'W{window}')
            ax.set_ylabel(label)
    for ax in axes:
        ax.legend(ncol=3, fontsize=8)
        ax.grid(alpha=.2)
    axes[0].set_title('Reflection through time; correlation requires >=12 variable pairs')
    axes[-1].set_xlabel('Completed historical window endpoint')
    save(fig, 'rolling_symmetry.png')

    strongest = temporal[temporal.family == 'pair'].copy()
    strongest['era_order'] = strongest.era.map({'early': 0, 'middle': 1, 'recent': 2})
    strongest = strongest.sort_values('era_order')
    if len(strongest) != 3:
        raise ValueError('Stored strongest-pair diagnostics require three eras')
    first = strongest.iloc[0]
    fig, axes = plt.subplots(3, 1, figsize=(11, 10))
    positions = np.arange(3)
    axes[0].plot(positions, strongest.rate, 'o-', label='Conditional hit rate')
    axes[0].plot(positions, strongest.baseline, 'D--', label='Aligned baseline')
    for p, row in zip(positions, strongest.itertuples()):
        axes[0].annotate(f'support={row.support}', (p, row.rate), xytext=(0, 8),
                         textcoords='offset points', ha='center', fontsize=8)
    axes[0].set_title(f'Strongest stored directional pair {int(first.source)} -> {int(first.target)}, '
                      f'lag {int(first.lag)}; descriptive temporal check')
    axes[0].set_ylabel('Conditional hit rate')
    axes[0].set_xticks(positions, strongest.era.tolist())
    axes[0].set_ylim(top=max(strongest.rate.max(), strongest.baseline.max()) + .04)
    axes[0].legend()
    axes[1].bar(positions, strongest.risk_difference, color='#4c72b0')
    axes[1].axhline(0, color='grey', lw=1)
    axes[1].set_ylabel('Rate minus aligned baseline')
    axes[1].set_xticks(positions, [f'{r.era}\n{r.start}-{r.end}' for r in strongest.itertuples()])
    axes[1].set_xlabel('Historical era (global leader retained throughout)')
    selected_rolling = pd.read_csv(directory / 'pair_rolling.csv')
    selected_rolling = selected_rolling[selected_rolling.family == 'pair']
    for window, group in selected_rolling.groupby('window'):
        if group.eligible.any():
            # Keep missing-support endpoints as NaN so lines cannot imply a
            # persistent regime across long unsupported intervals.
            axes[2].plot(group.endpoint, group.risk_difference.where(group.eligible), marker='.', label=f'W{window}; source support >=10')
    axes[2].axhline(0, color='grey', lw=1)
    axes[2].set(xlabel='Completed rolling endpoint (selected pair held fixed)', ylabel='Conditional minus baseline')
    if len(selected_rolling): axes[2].legend(fontsize=8)
    save(fig, 'strongest_pair_time.png')

    def null_panels(families, name, *, columns, title):
        rows = int(np.ceil(len(families)/columns))
        fig, axes = plt.subplots(rows, columns, figsize=(5*columns, 3.5*rows), squeeze=False)
        for ax, family in zip(axes.flat, families):
            for kind, color, label in [('iid', '#4c72b0', 'IID'), ('fixed_margins', '#dd8452', 'Fixed margins')]:
                values = null.loc[null.null_model == kind, family].dropna().to_numpy()
                ax.hist(values, bins=18, alpha=.5, color=color, label=label)
            ax.axvline(real['maxima'][family], color='#c44e52', lw=2, label='Real family maximum')
            ax.set(title=family, xlabel='Pilot-normalized complete-search maximum', ylabel='Null replicates')
            ax.legend(fontsize=7)
        for ax in list(axes.flat)[len(families):]:
            ax.set_visible(False)
        fig.suptitle(title)
        save(fig, name)

    null_panels(('pooled', 'pair', 'anti'), 'symmetry_anti.png', columns=3,
                title='Reflection and anti-reflection: own family-global null maxima (full scope)')
    null_panels(('same_draw', 'pooled', 'pair', 'asymmetry', 'regime', 'anti', 'shift'),
                'global_max_null.png', columns=3,
                title='All seven search families: full-scope IID and fixed-margin maxima')

    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    for ax, model in zip(axes, ('MirrorModel', 'GapLogistic')):
        selected = predictions[(predictions.model == model) & (predictions.target_draw == 1245)]
        if len(selected) != 1:
            raise ValueError(f'Exactly one stored {model} target1245 prediction required')
        row = selected.iloc[0]
        if row.feature_cutoff != 1244 or row.training_cutoff >= 1245:
            raise ValueError('Historical ranking uses an invalid stored cutoff')
        scores = json.loads(row.scores)
        ranking, actual = json.loads(row.ranking), json.loads(row.actual)
        if sorted(ranking) != list(range(1, 46)) or set(map(int, scores)) != set(range(1, 46)):
            raise ValueError('Complete stored number scores and ranking required')
        if sorted(actual) != (np.flatnonzero(x[1244])+1).tolist():
            raise ValueError('Stored historical actual numbers do not match supplied prefix')
        ax.bar(labels, [scores[str(n)] for n in labels],
               color=['#dd8452' if n in ranking[:6] else '#4c72b0' for n in labels])
        ax.scatter(actual, [scores[str(n)] for n in actual], marker='*', color='#c44e52', s=85,
                   zorder=3, label='Actual main numbers')
        ax.set_title(f'{model}: stored historical target1245 scores; top six in orange')
        ax.set_ylabel('Stored model score')
        ax.legend(fontsize=8)
    axes[-1].set_xticks(labels, labels, fontsize=7)
    axes[-1].set_xlabel('Number (all features completed through draw1244; no refitting for plots)')
    save(fig, 'model_ranking.png')

    metric_path = directory / 'full_metrics.csv'
    if metric_path.exists():
        metrics = pd.read_csv(metric_path)
        shifts = metrics[metrics.kind == 'shift_pooled_risk']
        values = shifts.pivot(index='shift', columns='lag', values='z').reindex(index=SHIFTS, columns=LAGS)
        heatmap(values, [f'shift {s:+d}' for s in SHIFTS],
                'Secondary reflection shifts; descriptive, no predictor selection',
                'Pilot-normalized oriented risk difference', 'secondary_shift_heatmap.png', size=(10, 4))
    return paths
