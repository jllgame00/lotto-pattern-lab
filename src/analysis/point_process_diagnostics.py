"""H19 descriptive exports and figures from stored, causally audited forecasts.

Full-history matrices and era-specific strongest lags are descriptive searches.
They never enter a forecast. Ranking figures use only archived walk-forward
probabilities. Graph comparisons read hash-verified Phase14 artifacts and do
not refit, reselect, or change the Graph model.
"""
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta, spearmanr

from src.analysis.recurrence import research_matrix
from src.analysis.point_process import (LAGS, SCHEMES, STATE_COUNTS, KERNELS, P,
    event_history, renewal_states, renewal_table, all_effects, kernel_effects)

ROOT = Path(__file__).resolve().parents[2]
DIRECTIONAL = ('self_positive', 'self_negative', 'cross_positive', 'cross_negative')
FAMILIES = ('renewal', *DIRECTIONAL, 'kernel')


def _directory(directory):
    directory = Path(directory).resolve()
    if not directory.is_relative_to((ROOT/'reports/point_process').resolve()):
        raise ValueError('H19 output must stay under reports/point_process')
    return directory


def _clean(value):
    if isinstance(value, dict):return {str(k):_clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):return [_clean(v) for v in value]
    if isinstance(value, np.generic):return _clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):return None
    return value


def _json(value):
    return json.dumps(_clean(value), sort_keys=True, allow_nan=False)


def _input(x, directory):
    x = research_matrix(x)
    if len(x)<208:raise ValueError('H19 diagnostics require 208..1245 draws')
    directory = _directory(directory)
    summary = json.loads((directory/'real_summary.json').read_text(encoding='utf-8'))
    full = summary['full']
    if (full.get('draws')!=len(x) or
            full.get('representation_hash')!=sha256(x.tobytes()).hexdigest()):
        raise ValueError('Stored full-search source hash/prefix mismatch')
    return x, directory, summary


def _decode(value):
    return json.loads(value) if isinstance(value, str) else value


def _prediction_archive(x, directory, required=False):
    path = directory/'walk_forward_26/predictions.csv'
    if not path.exists():
        if required:raise ValueError('Stored walk-forward forecast predictions required')
        return pd.DataFrame()
    selection_path = directory/'selected_configuration.json'
    payload = json.loads(selection_path.read_text(encoding='utf-8'))
    if (set(payload)!={'selection', 'sha256'} or
            sha256(json.dumps(payload['selection'], sort_keys=True, allow_nan=False).encode()).hexdigest()!=payload['sha256']):
        raise ValueError('Stored selection hash mismatch')
    development_hash = payload['selection'].get('development_matrix_hash')
    if development_hash!=sha256(x[:min(900, len(x))].tobytes()).hexdigest():
        raise ValueError('Stored selection development source hash mismatch')
    frame = pd.read_csv(path)
    own = frame[frame.model.isin(['RenewalModel', 'HawkesInfluenceModel', 'SignedInfluenceModel'])].copy()
    if own.duplicated(['model', 'target_draw']).any():raise ValueError('Duplicate stored forecast targets')
    for row in own.to_dict('records'):
        target = int(row['target_draw'])
        if not 2<=target<=len(x):raise ValueError('Stored forecast target outside source prefix')
        if (row.get('source_cutoff')!=target-1 or
                not 1<=row.get('outer_fit_cutoff', 0)<=target-1 or
                row.get('edge_training_cutoff')!=row['outer_fit_cutoff']):
            raise ValueError('Stored forecast source/edge cutoff is not causal')
        actual = sorted(_decode(row['actual']))
        if actual!=(np.flatnonzero(x[target-1])+1).tolist():
            raise ValueError('Stored actual outcome differs from source')
        ranking = _decode(row['ranking'])
        if sorted(ranking)!=list(range(1, 46)):raise ValueError('Stored ranking must cover 45 numbers')
        field = 'probabilities' if isinstance(row.get('probabilities'), str) else 'scores'
        probabilities = _decode(row[field])
        try:values = np.array([probabilities[str(i)] if str(i) in probabilities else probabilities[i] for i in range(1, 46)], float)
        except (TypeError, KeyError) as exc:raise ValueError('Stored 45-number probabilities required') from exc
        if len(probabilities)!=45 or not np.isfinite(values).all() or not ((0<=values)&(values<=1)).all():
            raise ValueError('Stored finite marginal probabilities required')
        detail = _decode(row['last_diagnostic'])
        if not isinstance(detail, list) or sorted(d['number'] for d in detail)!=list(range(1, 46)):
            raise ValueError('Stored 45-number diagnostic required')
        for d in detail:
            if d.get('source_cutoff')!=target-1 or d.get('training_cutoff')!=row['outer_fit_cutoff']:
                raise ValueError('Stored number diagnostic source cutoff mismatch')
            probability = d.get('probability', d.get('score'))
            if probability is not None and not np.isclose(probability, values[d['number']-1], atol=1e-12, rtol=0):
                raise ValueError('Stored diagnostic probability mismatch')
        edges = _decode(row['selected_edges'])
        if isinstance(edges, list):
            for incoming in edges:
                for edge in incoming:
                    if edge.get('training_cutoff')!=row['outer_fit_cutoff']:
                        raise ValueError('Stored selected edge source cutoff mismatch')
    return own


def _hazards(x):
    rows, pooled = [], []
    for scheme in SCHEMES:
        table = renewal_table(x, scheme)
        for j in range(45):
            for state in range(STATE_COUNTS[scheme]):
                support, hits = int(table['support'][j, state]), int(table['hits'][j, state])
                ci = beta.ppf([.025, .975], hits+.5, support-hits+.5) if support else [np.nan]*2
                rows.append(dict(scheme=scheme, number=j+1, state=state, support=support, hits=hits,
                    raw_rate=table['rate'][j, state], conditional=table['conditional'][j, state],
                    expected_p=P, own_baseline=table['baseline'][j], effect=table['effect'][j, state],
                    score=table['score'][j, state], eligible=table['eligible'][j, state],
                    marginal_jeffreys_low=ci[0], marginal_jeffreys_high=ci[1],
                    uncertainty='marginal_descriptive_not_joint_process_inference'))
        for state in range(STATE_COUNTS[scheme]):
            support = int(table['support'][:, state].sum())
            hits = int(table['hits'][:, state].sum())
            expected = float(np.dot(table['support'][:, state], table['baseline']))
            base = expected/support if support else P
            pooled.append(dict(scheme=scheme, state=state, support=support, hits=hits,
                raw_rate=hits/support if support else np.nan, expected_p=P,
                frequency_weighted_expected_hits=expected, own_frequency_baseline=base,
                conditional=(hits+26*base)/(support+26),
                descriptive_only=True, independent_number_processes_assumed=False))
    return pd.DataFrame(rows), pd.DataFrame(pooled)


def _lag_rows(effects):
    rows = []
    for l, lag in enumerate(LAGS):
        for i in range(45):
            for j in range(45):
                row = dict(lag=lag, source=i+1, target=j+1, kind='self' if i==j else 'cross')
                row.update({key:effects[key][l, i, j] for key in
                    ('support', 'hits', 'baseline', 'rate', 'conditional', 'lift', 'log_odds', 'effect', 'score', 'eligible')})
                rows.append(row)
    return pd.DataFrame(rows)


def _influence(effects):
    active = np.asarray(effects['eligible']) & np.isfinite(effects['effect'])
    chosen = np.argmax(np.where(active, abs(effects['effect']), -np.inf), axis=0)
    valid = active.any(axis=0)
    matrix = np.take_along_axis(effects['effect'], chosen[None], axis=0)[0]
    matrix = np.where(valid, matrix, np.nan)
    rows = [dict(source=i+1, target=j+1, effect=matrix[i, j],
                 lag=int(LAGS[chosen[i, j]]) if valid[i, j] else None,
                 supported=bool(valid[i, j]), full_history_descriptive=True, forecast=False,
                 selection='maximum_absolute_supported_effect_across_declared_lags')
            for i in range(45) for j in range(45)]
    return matrix, pd.DataFrame(rows)


def _development_influence(x, full_effects):
    cutoff = min(900, len(x))
    development = all_effects(x[:cutoff])
    matrix, table = _influence(development)
    table['full_history_descriptive'] = False
    table['development_frozen'] = True
    table['training_cutoff'] = cutoff
    table['development_matrix_hash'] = sha256(x[:cutoff].tobytes()).hexdigest()
    table['selection'] = 'development_maximum_absolute_supported_effect;ties_declared_lag_order'
    table['effect_scope'] = 'development_only'
    full_values, full_support = [], []
    for row in table.itertuples():
        if pd.isna(row.lag):
            full_values.append(np.nan); full_support.append(0)
            continue
        index = (LAGS.index(int(row.lag)), row.source-1, row.target-1)
        full_values.append(full_effects['effect'][index])
        full_support.append(full_effects['support'][index])
    table['full_effect_at_frozen_lag'] = full_values
    table['full_support_at_frozen_lag'] = full_support
    table['full_effect_descriptive_only'] = True
    return matrix, table


def _temporal(x, leaders):
    n = len(x)
    cuts = (0, 415, 830, 1245) if n==1245 else (0, n//3, 2*n//3, n)
    windows = [('era', name, left, right) for name, left, right in
               zip(('early', 'middle', 'recent'), cuts[:-1], cuts[1:])]
    ends = sorted(set(range(416, n+1, 52)) | ({n} if n>=416 else set()))
    windows += [('rolling', f'ending{end}', end-416, end) for end in ends]
    rows = []
    for kind, name, left, right in windows:
        effects = all_effects(x[left:right])
        for family in DIRECTIONAL:
            leader = leaders[family]
            i, j = int(leader['source'])-1, int(leader['target'])-1
            sign = -1 if family.endswith('negative') else 1
            scores = effects['score'][:, i, j]*sign
            active = effects['eligible'][:, i, j] & np.isfinite(scores)
            selected = int(np.argmax(np.where(active, scores, -np.inf))) if active.any() else None
            for l, lag in enumerate(LAGS):
                rows.append(dict(family=family, candidate_key=leader.get('key', family), source=i+1, target=j+1,
                    full_selected_lag=leader['lag'], lag=lag, window_kind=kind, window=name,
                    start=left+1, end=right, support=effects['support'][l, i, j], hits=effects['hits'][l, i, j],
                    baseline=effects['baseline'][l, i, j], conditional=effects['conditional'][l, i, j],
                    effect=effects['effect'][l, i, j], score=effects['score'][l, i, j], eligible=active[l],
                    strongest_lag=LAGS[selected] if selected is not None else None,
                    strongest_lag_descriptive=True, minimum_source_support=30,
                    candidate_frozen=True, relation_reselected=False, independent_test=False))
    return pd.DataFrame(rows)


def _correlation(a, b):
    a, b = np.asarray(a), np.asarray(b)
    valid = np.isfinite(a)&np.isfinite(b)
    if valid.sum()<3 or np.ptp(a[valid])==0 or np.ptp(b[valid])==0:return None
    return float(spearmanr(a[valid], b[valid]).statistic)


def _graph_comparison(matrix):
    graph_dir = ROOT/'reports/graph_hypergraph'
    unavailable = dict(available=False, graph_refitted=False)
    manifest_path = graph_dir/'run_manifest.json'
    if not manifest_path.exists():return dict(unavailable, reason='Frozen graph manifest unavailable')
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest['research_cutoff']!=1245 or manifest['draw1246_used'] is not False:
            return dict(unavailable, reason='Frozen graph source boundary mismatch')
        path = next((graph_dir/name for name in ('structural_cache.npz', 'adjacency.csv', 'cooccurrence.csv')
                     if (graph_dir/name).exists()), None)
        if path is None:return dict(unavailable, reason='Frozen usable adjacency artifact unavailable')
        # Verify the exact bytes BEFORE numpy/pandas interprets the artifact.
        raw = path.read_bytes()
        if manifest['artifacts'][path.name]['sha256']!=sha256(raw).hexdigest():
            return dict(unavailable, reason='Frozen graph artifact hash mismatch')
        if path.suffix=='.npz':
            with np.load(BytesIO(raw), allow_pickle=False) as stored:
                key = 'adjacency_W26' if 'adjacency_W26' in stored else 'adjacency'
                if key not in stored:return dict(unavailable, reason='Frozen usable adjacency key unavailable')
                adjacent = stored[key]
                if adjacent.ndim==3:adjacent = adjacent[-1]
        else:
            adjacent = pd.read_csv(BytesIO(raw), header=None).to_numpy(float)
        if (adjacent.shape!=(45, 45) or not np.isfinite(adjacent).all() or
                not np.allclose(adjacent, adjacent.T) or (adjacent<0).any()):
            return dict(unavailable, reason='Frozen adjacency is not a usable symmetric 45x45 matrix')
        influence = np.nan_to_num(matrix, nan=0.)
        np.fill_diagonal(influence, 0.)
        upper = np.triu_indices(45, 1)
        graph_values = adjacent[upper]
        graph_top = set(np.argsort(-graph_values, kind='stable')[:45])
        comparisons = {}
        for name, directed in [('absolute', abs(influence)), ('positive', np.maximum(influence, 0)),
                               ('negative', np.maximum(-influence, 0))]:
            values = ((directed+directed.T)/2)[upper]
            top = set(np.argsort(-values, kind='stable')[:45])
            comparisons[name] = dict(spearman=_correlation(graph_values, values),
                top45_overlap=len(graph_top&top), top45_overlap_fraction=len(graph_top&top)/45,
                incoming_strength_spearman=_correlation(adjacent.sum(axis=0), directed.sum(axis=0)))
        return dict(available=True, graph_refitted=False, artifact=str(path.relative_to(ROOT)),
            artifact_sha256=sha256(raw).hexdigest(), graph_reference='predeclared_W26_final_stored_endpoint',
            top_pairs=45, pair_aggregation='mean_of_directed_absolute_influence',
            directed_unsupported_cells='zero_for_comparison', correlations=comparisons,
            descriptive_only=True, independent_test=False)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return dict(unavailable, reason=f'Frozen graph integrity/adjacency unavailable: {exc}')


def _frozen_matrix(archive):
    if archive.empty:return None
    hawkes = archive[archive.model=='HawkesInfluenceModel'].sort_values('target_draw')
    if hawkes.empty:return None
    first = hawkes.iloc[0]
    if first.outer_fit_cutoff>900:return None
    edges = _decode(first.selected_edges)
    rows = []
    for j, incoming in enumerate(edges):
        for edge in incoming:
            weights = np.asarray(edge['lag_weights'], float)
            rows.append(dict(source=edge['source'], target=j+1, amplitude=edge['amplitude'],
                lag_weights=_json(weights), primary_declared_lag=LAGS[int(np.argmax(abs(weights)))],
                training_cutoff=int(first.outer_fit_cutoff), development_frozen=True,
                full_history_descriptive=False, forecast_input=True))
    return pd.DataFrame(rows, columns=['source', 'target', 'amplitude', 'lag_weights', 'primary_declared_lag',
        'training_cutoff', 'development_frozen', 'full_history_descriptive', 'forecast_input'])


def diagnostics(x, directory):
    """Write descriptive tables, pickle-free event arrays, and provenance JSON."""
    x, directory, summary = _input(x, directory)
    archive = _prediction_archive(x, directory)
    history = event_history(x)
    effects = all_effects(x)
    kernel = kernel_effects(x, effects=effects)
    hazards, pooled = _hazards(x)
    lag = _lag_rows(effects)
    _, full_history_influence = _influence(effects)
    matrix, influence = _development_influence(x, effects)
    temporal = _temporal(x, summary['full']['leaders'])
    profiles = []
    for k, name in enumerate(KERNELS):
        for i in range(45):
            for j in range(45):
                profiles.append(dict(kernel=name, source=i+1, target=j+1, score=kernel['score'][k, i, j],
                    amplitude=kernel['amplitude'][k, i, j], eligible=kernel['eligible'][k, i, j],
                    lags=_json(LAGS), lag_effects=_json(effects['effect'][:, i, j]),
                    lag_supports=_json(effects['support'][:, i, j]), descriptive_only=True))
    tables = {'renewal_hazards.csv':hazards, 'pooled_renewal.csv':pooled, 'lag_effects.csv':lag,
              'self_lag_effects.csv':lag[lag.kind=='self'], 'cross_lag_effects.csv':lag[lag.kind=='cross'],
              'influence_matrix.csv':influence, 'development_frozen_influence.csv':influence,
              'full_history_descriptive_influence.csv':full_history_influence, 'relation_time.csv':temporal,
              'kernel_profiles.csv':pd.DataFrame(profiles)}
    frozen = _frozen_matrix(archive)
    if frozen is not None:tables['stored_model_edges.csv'] = frozen
    # Ragged arrays are flattened with number labels; loading never needs pickle.
    arrays = dict(binary=x, gaps=history['gaps'], relative=history['relative'],
        current_gap=history['current_gap'], current_relative=history['current_relative'],
        event_draws=np.concatenate(history['events']),
        event_numbers=np.concatenate([np.full(len(e), j+1, int) for j, e in enumerate(history['events'])]),
        interarrival_values=np.concatenate(history['interarrivals']),
        interarrival_numbers=np.concatenate([np.full(len(e), j+1, int) for j, e in enumerate(history['interarrivals'])]))
    arrays.update({f'recent_counts_{w}':values for w, values in history['recent_counts'].items()})
    arrays.update({f'states_{scheme}':renewal_states(x, scheme) for scheme in SCHEMES})
    directory.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(directory/'event_history.npz', **arrays)
    paths = [directory/'event_history.npz']
    for filename, frame in tables.items():
        path = directory/filename
        frame.to_csv(path, index=False)
        paths.append(path)
    metadata = dict(draws=len(x), research_cutoff=1245, draw1246_used=False,
        representation_hash=sha256(x.tobytes()).hexdigest(),
        full_history_matrix='descriptive maximum absolute supported effect across seven declared lags; never forecast input',
        primary_matrix_selection_cutoff=min(900, len(x)),
        primary_matrix_development_hash=sha256(x[:min(900, len(x))].tobytes()).hexdigest(),
        primary_matrix='development effects at development-selected lags; no evaluation-set lag choice',
        graph_comparison_matrix='development_effect_at_development_selected_lag',
        relative='gap divided by causal mean completed own interarrival',
        recent_counts='completed draws ending at row t, includes t; not predictor for target t',
        uncertainty='marginal Jeffreys intervals descriptive only; inferential evidence uses complete-search draw-level null',
        temporal='four full-search fixed identities; strongest lag per era is descriptive reselection, not independent testing',
        rolling_window=416, rolling_stride=52, minimum_source_support=30,
        frozen_development_matrix_available=True, stored_model_edges_available=frozen is not None,
        forecasts=dict(available=not archive.empty, source='stored_walk_forward_26', model_refitted=False),
        graph_comparison=_graph_comparison(matrix),
        artifacts={p.name:dict(sha256=sha256(p.read_bytes()).hexdigest()) for p in paths})
    path = directory/'diagnostic_metadata.json'
    path.write_text(_json(metadata), encoding='utf-8')
    return paths+[path]


def plots(x, directory):
    """Render ten figures; final forecast is archived target 1245 canonically."""
    x, directory, summary = _input(x, directory)
    archive = _prediction_archive(x, directory, required=True)
    chosen = archive[(archive.model=='HawkesInfluenceModel') & (archive.target_draw==len(x))]
    if len(chosen)!=1:raise ValueError('Stored final Hawkes forecast required for ranking plot')
    row = chosen.iloc[0]
    field = 'probabilities' if isinstance(row.get('probabilities'), str) else 'scores'
    probabilities = _decode(row[field])
    p = np.array([probabilities[str(i)] if str(i) in probabilities else probabilities[i] for i in range(1, 46)])
    actual = np.asarray(_decode(row.actual), int)
    null = pd.read_csv(directory/'null_maxima.csv')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out = _directory(directory/'plots')
    out.mkdir(exist_ok=True)
    paths = []
    def save(fig, name):
        path = out/name
        fig.tight_layout()
        fig.savefig(path, dpi=120)
        plt.close(fig)
        paths.append(path)
    hazards, pooled = _hazards(x)
    effects = all_effects(x)
    matrix, _ = _development_influence(x, effects)
    temporal = _temporal(x, summary['full']['leaders'])
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, scheme in zip(axes, SCHEMES):
        group = pooled[pooled.scheme==scheme]
        ax.plot(group.state, group.raw_rate, 'o-', label='Pooled raw hazard')
        ax.plot(group.state, group.own_frequency_baseline, '--', label='Own-frequency reference')
        ax.set(title=scheme, xlabel='Renewal state', ylabel='Empirical event rate')
    axes[0].legend(fontsize=8)
    fig.suptitle('Full-history empirical renewal hazards (descriptive)')
    save(fig, 'empirical_hazard.png')
    fig, ax = plt.subplots(figsize=(9, 5))
    for scheme in SCHEMES:
        group = pooled[pooled.scheme==scheme]
        ax.plot(group.state, group.raw_rate/P, 'o-', label=scheme)
    ax.axhline(1, color='black', linestyle='--', label='IID p=6/45')
    ax.set(xlabel='Renewal state', ylabel='Raw hazard / IID p', title='Renewal versus IID; descriptive only')
    ax.legend(); save(fig, 'hazard_vs_iid.png')
    fig, ax = plt.subplots(figsize=(9, 5))
    for family in ('self_positive', 'self_negative'):
        lead = summary['full']['leaders'][family]; j = int(lead['source'])-1
        ax.plot(LAGS, effects['effect'][:, j, j], 'o-', label=f"{family}: {j+1}")
    ax.axhline(0, color='black', linewidth=.7)
    ax.set(xlabel='Strictly earlier lag (draws)', ylabel='Smoothed conditional minus baseline', title='Fixed full-search self leaders; descriptive lag profiles')
    ax.legend(); save(fig, 'self_lag_profile.png')
    for sign, name in ((1, 'positive'), (-1, 'negative')):
        fig, ax = plt.subplots(figsize=(8, 7))
        image = ax.imshow(np.maximum(sign*matrix, 0), origin='lower', extent=(.5, 45.5, .5, 45.5), cmap='magma')
        fig.colorbar(image, ax=ax, label=f'{name} effect magnitude')
        ax.set(xlabel='Target number', ylabel='Source number', title=f'Development through {min(900, len(x))}: frozen-lag {name} effects')
        save(fig, f'{name}_influence_matrix.png')
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, family in zip(axes.ravel(), DIRECTIONAL):
        group = temporal[(temporal.family==family)&(temporal.window_kind=='era')]
        for era, era_rows in group.groupby('window', sort=False):ax.plot(era_rows.lag, era_rows.effect, 'o-', label=era)
        lead = summary['full']['leaders'][family]
        ax.set(title=f"{family}: {lead['source']} to {lead['target']}", xlabel='Lag', ylabel='Smoothed effect')
        ax.legend(fontsize=8)
    fig.suptitle('Fixed relations across eras; strongest lag reselection is descriptive')
    save(fig, 'strongest_pair_lag_profiles.png')
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, family in zip(axes.ravel(), DIRECTIONAL):
        lead = summary['full']['leaders'][family]
        group = temporal[(temporal.family==family)&(temporal.lag==int(lead['lag']))]
        rolling = group[group.window_kind=='rolling']
        if rolling.empty:rolling = group[group.window_kind=='era']
        ax.plot(rolling.end, rolling.effect, 'o-')
        ax.set(title=f"{family}: fixed lag {lead['lag']}", xlabel='Window end draw', ylabel='Smoothed effect')
    fig.suptitle('Fixed full-history candidates through time; 416 draws / stride 52 when available')
    save(fig, 'strongest_pair_time.png')
    for kind, filename in [('iid', 'iid_global_maxima.png'), ('fixed_margins', 'fixed_margin_global_maxima.png')]:
        fig, axes = plt.subplots(2, 3, figsize=(13, 7))
        group = null[(null.scope=='full')&(null.null_model==kind)]
        if group.empty:raise ValueError(f'Stored {kind} full-search null maxima required')
        for ax, family in zip(axes.ravel(), FAMILIES):
            values = pd.to_numeric(group[family], errors='raise').to_numpy()
            ax.hist(values[np.isfinite(values)], bins=min(20, max(2, len(values))), alpha=.7)
            ax.axvline(summary['full']['maxima'][family], color='red', label='Observed global max')
            ax.set(title=family, xlabel='Complete-search calibrated maximum')
        axes[0, 0].legend(fontsize=8)
        fig.suptitle(f'{kind}: every surrogate repeats the full candidate search')
        save(fig, filename)
    fig, ax = plt.subplots(figsize=(14, 5))
    labels = np.arange(1, 46)
    ax.bar(labels, p, color='steelblue', label='Stored causal marginal probability')
    ax.scatter(actual, p[actual-1]+.004, marker='*', s=100, color='goldenrod', edgecolors='black', label='Actual winning numbers', zorder=3)
    ax.set(xlabel='Number', ylabel='Archived marginal probability', xlim=(.2, 45.8),
        title=f'Hawkes stored ranking target {len(x)}; fit through {int(row.outer_fit_cutoff)}, source through {len(x)-1}')
    ax.legend(); save(fig, 'hawkes_ranking_45.png')
    return paths
