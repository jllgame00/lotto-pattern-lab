"""Independent H17 artifact audit; no selection changes or publication.

Metric and rank arithmetic below is independent of the research evaluator.
Development/validation and four placebo runs are deterministic verification of
already frozen decisions, not further model-selection attempts.
"""
from hashlib import sha256
import ast
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from .final_ensemble_inputs import canonical_configs, load_panel
from .final_ensemble import (PROMOTED, SPLITS, split_panel, select_development,
                             validate_selection, random_weight_templates, placebo_panel)

ROOT = Path(__file__).resolve().parents[2]


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _json(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def _hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def verify_stage_chain(directory):
    directory = Path(directory)
    stages = {}
    for name in ('protocol', 'development_selection', 'validation_gate', 'final_started', 'configuration_freeze'):
        record = _json(directory/f'{name}.json')
        if set(record) != {'payload', 'sha256'} or _digest(record['payload']) != record['sha256']:
            raise ValueError(f'Stage seal hash mismatch: {name}')
        stages[name] = record['payload']
    p, s, g, f, c = (stages[n] for n in stages)
    links = [(s, 'protocol_hash', p), (g, 'protocol_hash', p), (g, 'development_hash', s),
             (f, 'validation_hash', g), (c, 'protocol_hash', p), (c, 'development_hash', s),
             (c, 'validation_hash', g)]
    if any(record.get(key) != _digest(parent) for record, key, parent in links):
        raise ValueError('Stage hash chain parent link mismatch')
    if (f.get('model_selection_evaluations') != 1 or f.get('final_start') != 1131 or f.get('final_end') != 1245
            or c.get('selected') != g.get('selected') or c.get('kind') != 'CONFIGURATION_ONLY'
            or any(c.get(k) is not False for k in ('draw1246_used', 'draw1247_prediction_generated', 'publication_executed'))):
        raise ValueError('Frozen final scope/count or configuration-only restriction violated')
    return stages


def independent_combine(ranks, weights):
    values = np.asarray(ranks)
    weights = np.asarray(weights, dtype=float)
    if (values.ndim != 3 or values.shape[2] != 45 or weights.shape != (values.shape[1],)
            or not np.all(np.sort(values, axis=2) == np.arange(1, 46))
            or not np.isfinite(weights).all() or (weights < 0).any() or not np.isclose(weights.sum(), 1)):
        raise ValueError('Invalid component ranks or weights')
    costs = np.round(np.sum((values-1)/44 * weights[None, :, None], axis=1), 12)
    result = np.empty(costs.shape, dtype=int)
    for i, cost in enumerate(costs):
        order = sorted(range(45), key=lambda number: (cost[number], number))
        result[i, order] = np.arange(1, 46)
    return result


def _series(ranks, actual):
    ranks, actual = np.asarray(ranks), np.asarray(actual)
    if ranks.shape != actual.shape or ranks.ndim != 2 or ranks.shape[1] != 45 or not np.all(actual.sum(1) == 6):
        raise ValueError('Matched rank/actual rows required')
    winning = np.array([row[np.flatnonzero(winners)] for row, winners in zip(ranks, actual)])
    return dict(mean_winning_rank=winning.mean(1), hits=(winning <= 6).sum(1),
                **{f'pool{k}': (winning <= k).sum(1) for k in (6, 8, 10, 12, 15)})


def independent_metrics(ranks, actual):
    values = _series(ranks, actual)
    result = dict(targets=len(ranks), avg_top6=float(values['hits'].mean()),
                  mean_winning_rank=float(values['mean_winning_rank'].mean()))
    result.update({f'hits{i}': int((values['hits'] == i).sum()) for i in range(7)})
    result.update({f'recall{k}': float(values[f'pool{k}'].mean()/6) for k in (6, 10, 15)})
    for k in (6, 8, 10, 12, 15):
        result[f'ge5_pool{k}'] = int((values[f'pool{k}'] >= 5).sum())
        result[f'all6_pool{k}'] = int((values[f'pool{k}'] == 6).sum())
    return result


def verify_frozen_rankings(path, targets, actual, rankings):
    with np.load(path, allow_pickle=False) as stored:
        expected = dict(targets=targets, actual=actual, **rankings)
        if set(stored.files) != set(expected):
            raise ValueError('Frozen rank artifact array inventory mismatch')
        for name, values in expected.items():
            if not np.array_equal(stored[name], values):
                raise ValueError(f'Frozen rank artifact mismatch: {name}')


def _compare(actual, expected, label):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or not set(expected) <= set(actual):
            raise ValueError(f'Missing audit fields: {label}')
        for key, value in expected.items():
            _compare(actual[key], value, f'{label}.{key}')
    elif isinstance(expected, (list, tuple, np.ndarray)):
        if isinstance(actual, str):
            actual = ast.literal_eval(actual)
        if not isinstance(actual, (list, tuple, np.ndarray)) or len(actual) != len(expected):
            raise ValueError(f'Array mismatch: {label}')
        for i, value in enumerate(expected):
            _compare(actual[i], value, f'{label}[{i}]')
    elif expected is None:
        if actual is not None and not pd.isna(actual):
            raise ValueError(f'Null mismatch: {label}')
    elif isinstance(expected, (bool, np.bool_)):
        if not isinstance(actual, (bool, np.bool_)) or actual != expected:
            raise ValueError(f'Boolean mismatch: {label}')
    elif isinstance(expected, (int, float, np.integer, np.floating)):
        if not isinstance(actual, (int, float, np.integer, np.floating)) or not np.isclose(actual, expected, atol=2e-11, rtol=1e-12):
            raise ValueError(f'Numeric mismatch: {label}: {actual} != {expected}')
    elif actual != expected:
        raise ValueError(f'Value mismatch: {label}')


def _table(path, expected, keys):
    saved = pd.read_csv(path, float_precision='round_trip')
    if len(saved) != len(expected) or saved.duplicated(keys).any():
        raise ValueError(f'Incomplete/duplicate table: {Path(path).name}')
    index = {tuple(row[k] for k in keys): row for row in saved.to_dict('records')}
    if set(index) != {tuple(row[k] for k in keys) for row in expected}:
        raise ValueError(f'Table key mismatch: {Path(path).name}')
    for row in expected:
        key = tuple(row[k] for k in keys)
        _compare(index[key], row, f'{Path(path).name}:{key}')
    return saved


def _rankings(panel, allpanel, selection, gate):
    result = {name: allpanel['ranks'][:, i] for i, name in enumerate(allpanel['names'])}
    weights = dict(EqualAll=[.25]*4, OrdinarySubset=selection['ordinary']['weights'],
                   DiversitySubset=selection['diversity']['weights'], WeightedWinner=selection['winner']['weights'],
                   SelectedEnsemble=gate['selected']['weights'])
    result.update({name: independent_combine(panel['ranks'], weight) for name, weight in weights.items()})
    return result


def _interval(a, b, block):
    delta = np.asarray(a)-np.asarray(b); n = len(delta); length = min(block, n)
    rng = np.random.default_rng(270042)
    starts = rng.integers(0, n, size=(2000, int(np.ceil(n/length))))
    indices = (starts[:, :, None]+np.arange(length)) % n
    means = delta[indices.reshape(2000, -1)[:, :n]].mean(1)
    q = np.quantile(means, [.025, .975, .05/6, 1-.05/6])
    return dict(difference=float(delta.mean()), ci_low=q[0], ci_high=q[1],
                simultaneous_low=q[2], simultaneous_high=q[3], block=block, replicates=2000)


def _correlation(a, b):
    if np.std(a) == 0 or np.std(b) == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def _diversity(ranks, actual, names, scope):
    rows = []
    for i, left in enumerate(names):
        for j, right in enumerate(names):
            a, b = ranks[:, i], ranks[:, j]
            aa, bb = _series(a, actual), _series(b, actual)
            rows.append(dict(scope=scope, left=left, right=right,
                spearman=float(np.mean(1-6*np.square(a-b).sum(1)/(45*(45**2-1)))),
                winner_rank_error_correlation=_correlation(aa['mean_winning_rank'], bb['mean_winning_rank']),
                top6_hit_correlation=_correlation(aa['hits'], bb['hits']),
                **{f'top{k}_overlap': float(((a <= k) & (b <= k)).sum(1).mean()) for k in (6, 10, 15)}))
    return rows


def _tables(directory, panel, allpanel, selection, gate, ranks):
    performance, paired, loo, diversity = [], [], [], []
    weights = np.asarray(gate['selected']['weights'])
    refs = list(dict.fromkeys(['RandomModel', 'GapLogistic', selection['best_single']]))
    for scope, (start, end) in SPLITS.items():
        mask = (panel['targets'] >= start) & (panel['targets'] <= end)
        actual = panel['actual'][mask]
        performance.extend(dict(scope=scope, model=name, **independent_metrics(value[mask], actual)) for name, value in ranks.items())
        base = independent_metrics(ranks['SelectedEnsemble'][mask], actual)
        for i, name in enumerate(PROMOTED):
            if weights[i] <= 0 or weights.sum()-weights[i] <= 0:
                continue
            w = weights.copy(); w[i] = 0; w /= w.sum()
            r = independent_combine(panel['ranks'][mask], w)
            m = independent_metrics(r, actual)
            loo.append(dict(scope=scope, removed=name, weights=w.tolist(), **m,
                top6_change=m['avg_top6']-base['avg_top6'], winner_rank_change=m['mean_winning_rank']-base['mean_winning_rank'],
                spearman_with_full=float(np.mean(1-6*np.square(r-ranks['SelectedEnsemble'][mask]).sum(1)/(45*(45**2-1))))))
        diversity.extend(_diversity(allpanel['ranks'][mask, :5], actual, allpanel['names'][:5], scope))
        if scope != 'development':
            a = _series(ranks['SelectedEnsemble'][mask], actual)
            for ref in refs:
                b = _series(ranks[ref][mask], actual)
                for block in (26, 13, 52):
                    paired.extend([dict(scope=scope, reference=ref, metric='mean_winning_rank_improvement', **_interval(b['mean_winning_rank'], a['mean_winning_rank'], block)),
                                   dict(scope=scope, reference=ref, metric='top6_improvement', **_interval(a['hits'], b['hits'], block))])
    diversity.extend(_diversity(allpanel['ranks'][:, :5], panel['actual'], allpanel['names'][:5], 'common'))
    _table(directory/'performance.csv', performance, ['scope', 'model'])
    _table(directory/'paired.csv', paired, ['scope', 'reference', 'metric', 'block'])
    _table(directory/'leave_one_out.csv', loo, ['scope', 'removed'])
    _table(directory/'diversity.csv', diversity, ['scope', 'left', 'right'])
    robust = []
    for start in (1131, 1170, 1208):
        mask = panel['targets'] >= start
        for name in dict.fromkeys(['SelectedEnsemble', 'GapLogistic', selection['best_single']]):
            robust.append(dict(start=start, end=1245, cadence=26, model=name, **independent_metrics(ranks[name][mask], panel['actual'][mask])))
    _table(directory/'robustness.csv', robust, ['start', 'model'])
    final = _json(directory/'final_evaluation.json')
    _compare(final, dict(final=[r for r in performance if r['scope'] == 'final'], validation_gate=gate['passed'],
                        configuration=gate['selected'], best_single=selection['best_single'], selection_reruns=0, draw1246_used=False), 'final_evaluation')
    return dict(performance=len(performance), paired=len(paired), leave_one_out=len(loo), diversity=len(diversity))


def _placebos(directory, panel):
    rows = pd.read_csv(directory/'placebos.csv', float_precision='round_trip')
    expected = {(kind, i) for kind in ('random_weight', 'random_candidate') for i in range(199)}
    if len(rows) != 398 or set(zip(rows.kind, rows.replicate)) != expected:
        raise ValueError('Exactly199 placebo rows per kind required')
    checked = []
    for kind, seed in [('random_weight', 270101), ('random_candidate', 270202)]:
        for i in range(199):
            child = int(np.random.SeedSequence([seed, i]).generate_state(1)[0])
            row = rows[(rows.kind == kind) & (rows.replicate == i)].iloc[0].to_dict()
            if row['seed'] != child:
                raise ValueError('Placebo seed stream mismatch')
            for scope in SPLITS:
                _compare(row[f'{scope}_promoted_gain'], row[f'{scope}_rank_gain'] if row['gate_passed'] else 0., 'placebo promoted gain')
            if i not in (0, 198):
                continue
            p = placebo_panel(panel, seed=child) if kind == 'random_candidate' else panel
            grid = random_weight_templates(PROMOTED, seed=child) if kind == 'random_weight' else None
            selected = select_development(split_panel(p, 'development'), grid)
            gate = validate_selection(split_panel(p, 'validation'), selected)
            check = dict(kind=kind, replicate=i, seed=child, winner=selected['winner']['id'],
                         selected_weights=gate['selected']['weights'], best_single=selected['best_single'], gate_passed=gate['passed'])
            for scope in SPLITS:
                part = split_panel(p, scope)
                r = independent_combine(part['ranks'], gate['selected']['weights'])
                w = independent_combine(part['ranks'], selected['winner']['weights'])
                best = part['ranks'][:, list(PROMOTED).index(selected['best_single'])]
                m, b, wm = [independent_metrics(a, part['actual']) for a in (r, best, w)]
                gain = b['mean_winning_rank']-m['mean_winning_rank']
                check.update({f'{scope}_rank_gain': gain, f'{scope}_top6_gain': m['avg_top6']-b['avg_top6'],
                              f'{scope}_winner_rank_gain': b['mean_winning_rank']-wm['mean_winning_rank'],
                              f'{scope}_promoted_gain': gain if gate['passed'] else 0.})
            _compare(row, check, f'placebo:{kind}:{i}')
            checked.append(dict(kind=kind, replicate=i, seed=child))
    return checked


def _portfolios(history, directory, panel, ranks, selection):
    from .final_ensemble_portfolio import evaluate_portfolios
    frame = pd.read_csv(directory/'portfolio_draws.csv', float_precision='round_trip')
    methods = ['SelectedEnsembleWeighted', 'SelectedEnsembleCoverage', 'GapLogisticWeighted', 'BestSingleWeighted', 'UniformRandom']
    budgets = [1, 5, 10, 20]
    keys = ['target_draw', 'replicate', 'method', 'budget']
    wanted = {(t, r, m, b) for t in range(1131, 1246) for r in range(10) for m in methods for b in budgets}
    if len(frame) != 23000 or set(map(tuple, frame[keys].to_numpy())) != wanted:
        raise ValueError('Incomplete23000-row equal-budget portfolio audit')
    indexed_history = history.set_index('draw_no')
    outcomes = {t: set(np.flatnonzero(panel['actual'][t-901])+1) for t in range(1131, 1246)}
    labels = dict(SelectedEnsembleWeighted='SelectedEnsemble', SelectedEnsembleCoverage='SelectedEnsemble',
                  GapLogisticWeighted='GapLogistic', BestSingleWeighted=selection['best_single'])
    tickets_by_group = {}
    for row in frame.to_dict('records'):
        target, replicate, method, budget = (row[k] for k in keys)
        tickets = json.loads(row['tickets'])
        if (len(tickets) != budget or row['ticket_count'] != budget or len({tuple(t) for t in tickets}) != budget
                or any(len(t) != 6 or len(set(t)) != 6 or any(type(n) is not int or not 1 <= n <= 45 for n in t) for t in tickets)):
            raise ValueError('Invalid/duplicate portfolio ticket')
        if _hash_text(row['tickets']) != row['tickets_hash'] or row['seed'] != 270500 or json.loads(row['seed_entropy']) != [270500, replicate, target]:
            raise ValueError('Portfolio ticket hash or seed mismatch')
        if method in labels:
            pool = set(np.flatnonzero(ranks[labels[method]][target-901] <= 12)+1)
            if any(not set(ticket) <= pool for ticket in tickets):
                raise ValueError('Portfolio ticket escapes frozenTop12 pool')
        actual = outcomes[target]; bonus = int(indexed_history.loc[target, 'bonus'])
        hit = [len(set(t) & actual) for t in tickets]
        p2 = sum(h == 5 and bonus in t for h, t in zip(hit, tickets))
        p3 = sum(h == 5 and bonus not in t for h, t in zip(hit, tickets))
        _compare(row, dict(best_main=max(hit), ge4=int(max(hit) >= 4), ge5=int(max(hit) >= 5), ge6=int(max(hit) >= 6),
                           prize2=int(p2 > 0), prize3=int(p3 > 0), prize2_tickets=p2, prize3_tickets=p3), 'portfolio outcomes')
        tickets_by_group.setdefault((target, replicate, method), {})[budget] = tickets
    for group in tickets_by_group.values():
        if any(group[b] != group[20][:b] for b in budgets):
            raise ValueError('Portfolio budgets are not nested prefixes')
    summary = []
    for (method, budget), g in frame.groupby(['method', 'budget'], sort=False):
        by_seed = g.groupby('replicate')
        row = dict(method=method, budget=budget, n_targets=115, replicates=10, mean_best_main=float(by_seed.best_main.mean().mean()))
        for event in ('ge4', 'ge5', 'ge6', 'prize2', 'prize3'):
            counts = by_seed[event].sum()
            row.update({f'{event}_mean_count': float(counts.mean()), f'{event}_min_count': int(counts.min()), f'{event}_max_count': int(counts.max())})
        row.update({f'prize{prize}_mean_ticket_count': float(by_seed[f'prize{prize}_tickets'].sum().mean()) for prize in (2, 3)})
        summary.append(row)
    _table(directory/'portfolio_summary.csv', summary, ['method', 'budget'])
    orders = {label: np.argsort(ranks[name][230:231], axis=1)+1 for label, name in
              [('SelectedEnsemble', 'SelectedEnsemble'), ('GapLogistic', 'GapLogistic'), ('BestSingle', selection['best_single'])]}
    replayed = evaluate_portfolios(orders, np.array([1131]), panel['actual'][230:231],
                                  np.array([indexed_history.loc[1131, 'bonus']]), replicates=1)['draws']
    saved = frame[(frame.target_draw == 1131) & (frame.replicate == 0)]
    lookup = {(r['method'], r['budget']): r for r in saved.to_dict('records')}
    for row in replayed.to_dict('records'):
        _compare(lookup[row['method'], row['budget']], row, 'portfolio regeneration1131/0')
    _compare(_json(directory/'portfolio_configuration.json'), dict(seed=270500, replicates=10, budgets=budgets,
        pool_size=12, n_targets=115, target_start=1131, target_end=1245), 'portfolio configuration')
    return dict(rows=len(frame), unique_twenty_ticket_portfolios=len(tickets_by_group), summaries=len(summary), regenerated_target=1131, regenerated_replicate=0)


def _hash_text(text):
    return sha256(text.encode('utf8')).hexdigest()


def independent_decision(performance, paired, placebos, robustness, cadence, best_single, gate_passed):
    """Verify the declared classification, with inclusive numerical tail ties."""
    final = performance[performance.scope == 'final'].set_index('model')
    selected = final.loc['SelectedEnsemble']
    refs = list(dict.fromkeys(['RandomModel', 'GapLogistic', best_single]))
    gains = {ref: float(final.loc[ref].mean_winning_rank-selected.mean_winning_rank) for ref in refs}
    point = all(gains[ref] > 0 and selected.avg_top6 >= final.loc[ref].avg_top6 for ref in ('GapLogistic', best_single))
    robust = True
    for _, part in robustness.groupby('start'):
        means = part.set_index('model').mean_winning_rank
        robust = robust and all(means['SelectedEnsemble'] <= means[ref] for ref in ('GapLogistic', best_single))
    c = cadence[cadence.scope == 'final'].set_index('model').mean_winning_rank
    robust = robust and all(c['SelectedEnsemble'] <= c[ref] for ref in ('GapLogistic', best_single))
    primary = paired[(paired.scope == 'final') & (paired.block == 26) & (paired.metric == 'mean_winning_rank_improvement')]
    supported = bool((primary.simultaneous_low > 0).all())
    raw, promotion, rates = {}, {}, {}
    observed = gains[best_single]
    for kind, group in placebos.groupby('kind'):
        raw[kind] = (1+int((group.final_rank_gain >= observed-1e-12).sum()))/(len(group)+1)
        promotion[kind] = ((1+int((group.final_promoted_gain >= observed-1e-12).sum()))/(len(group)+1)) if gate_passed else None
        rates[kind] = float(group.gate_passed.mean())
    status = 'NO_ENSEMBLE_ADVANTAGE_ESTABLISHED'
    if gate_passed and point:
        status = 'EXPLORATORY_ENSEMBLE_CANDIDATE'
        if supported and robust and all(v <= .025 for v in promotion.values()):
            status = 'HISTORICAL_ENSEMBLE_ADVANTAGE'
    return dict(status=status, selected_final_rank_gain=observed, rank_gains=gains,
        placebo_comparison=dict(observed_promoted_gain=observed if gate_passed else 0., raw_tail_fractions=raw, promotion_tail_fractions=promotion),
        placebo_gate_rates=rates, final_point_gate=bool(point), simultaneous_primary_supported=supported, robustness_supported=bool(robust))


def _underlying_samples(history, rows):
    from .spatiotemporal import lotto_matrix
    from src.models.graph_hypergraph import GraphStructureModel, RollingFrequencyControl
    from src.models.transformed_space import GapShapeModel
    from src.models.symmetry import MirrorModel
    from src.models.information_flow import MutualInformationModel
    x = lotto_matrix(history, cutoff=1245)
    constructors = dict(GraphStructureModel=GraphStructureModel, GapShapeModel=GapShapeModel,
                        MirrorModel=MirrorModel, MutualInformationModel=MutualInformationModel, Frequency26=RollingFrequencyControl)
    configs = canonical_configs(); checked = []
    for target in (901, 1131, 1245):
        for name, constructor in constructors.items():
            model = constructor(**configs[name]['parameters'])
            scores = model.fit(x[:target-1], cutoff=target-1).score_matrix(x[:target-1], target=target)
            saved = json.loads(rows[(rows.target_draw == target) & (rows.model == name)].iloc[0].scores)
            _compare([saved[str(n)] for n in range(1, 46)], [scores[n] for n in range(1, 46)], f'base replay:{name}:{target}')
            checked.append(dict(model=name, target=target))
    return checked


def verify_fit_calendar(rows, cadence):
    """Causal cutoffs must also identify the declared historical fit calendar."""
    for row in rows.itertuples():
        anchor = 900+cadence*((row.target_draw-901)//cadence)
        effective = anchor if row.model == 'GapLogistic' else row.target_draw-1
        outer = row.target_draw-1 if row.model == 'RandomModel' else anchor
        if row.training_cutoff != effective or row.outer_fit_cutoff != outer:
            raise ValueError('Replay fit calendar/effective cutoff mismatch')


def audit(history, directory):
    """Verify completed H17 artifacts and write only audit_result.json."""
    directory = Path(directory).resolve()
    if not directory.is_relative_to((ROOT/'reports/final_ensemble').resolve()):
        raise ValueError('Audit output must stay under reports/final_ensemble')
    if history.draw_no.tolist() != list(range(1, 1246)):
        raise ValueError('Audit requires exact historical draws1..1245')
    stages = verify_stage_chain(directory)
    p, s, gate, config = (stages[k] for k in ('protocol', 'development_selection', 'validation_gate', 'configuration_freeze'))
    _compare(p, dict(historical_cutoff=1245, common=[901, 1245], splits=SPLITS,
                     candidates=list(PROMOTED), audit_only=['MutualInformationModel'], configs=canonical_configs(),
                     placebos=199, bootstrap=2000, blocks=[26, 13, 52]), 'protocol boundaries')
    start = _json(directory/'starting_state.json')
    if (_digest(start['protected']) != p['protected_inventory_hash'] or len(start['protected']) != 435
            or start['head'] != p['start_sha'] or start['data_sha256'] != p['data_sha256']):
        raise ValueError('Starting protected inventory/identity mismatch')
    for name, digest in {**start['protected'], **p['source_hashes']}.items():
        path = (ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or _hash(path) != digest:
            raise ValueError(f'Protected source/artifact changed: {name}')
    for args, expected in [(['rev-parse', 'HEAD'], start['head']), (['branch', '--show-current'], start['branch'])]:
        if subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip() != expected:
            raise ValueError('Git starting HEAD/branch changed')
    if _hash(ROOT/'data/raw/lotto_history.csv') != p['data_sha256'] or _hash(directory/'predeclared_plan.md') != p['plan_sha256']:
        raise ValueError('Data or frozen plan bytes changed')
    from src.randomness_cli import verified_archive
    archive = verified_archive(ROOT/'reports/prospective')
    if archive != start['archive']:
        raise ValueError('Prospective archive changed or new publication appeared')
    _compare(config, dict(git_sha=start['head'], data_sha256=p['data_sha256'], scientific_source_hashes=p['source_hashes']), 'configuration provenance')
    names = [*PROMOTED, 'MutualInformationModel', 'RandomModel', 'Frequency26']
    panels = {}; raw = {}
    for cadence in (26, 13):
        path = directory/f'predictions_{cadence}.csv'; record = _json(directory/f'replay_audit_{cadence}.json')
        if _hash(path) != record['csv_sha256'] or record.get('original_bytes_verified') is not False:
            raise ValueError('Replay artifact hash or original-byte disclaimer mismatch')
        raw[cadence] = pd.read_csv(path, float_precision='round_trip')
        verify_fit_calendar(raw[cadence], cadence)
        allpanel = load_panel(raw[cadence], names)
        if allpanel['targets'].tolist() != list(range(901, 1246)) or len(raw[cadence]) != 7*345:
            raise ValueError('All seven complete replay series required')
        if cadence == 26 and (len(record['checks']) != 7 or not all(c['matches'] for c in record['checks'])):
            raise ValueError('Documented point-metric replay check failed')
        for check in record['checks']:
            counts = np.bincount(raw[cadence][raw[cadence].model == check['model']].hits, minlength=7).tolist()
            _compare(check, dict(observed=counts, matches=counts == check['documented']), 'replay hit-distribution')
        panels[cadence] = (dict(allpanel, names=list(PROMOTED), ranks=allpanel['ranks'][:, :4]), allpanel)
    panel, allpanel = panels[26]
    from .spatiotemporal import lotto_matrix
    source_actual = lotto_matrix(history, cutoff=1245)[900:]
    if not np.array_equal(allpanel['actual'], source_actual) or not np.array_equal(panels[13][1]['actual'], source_actual):
        raise ValueError('Prediction actual outcomes do not match source')
    for i, name in enumerate(names):
        if name != 'GapLogistic' and not np.array_equal(allpanel['ranks'][:, i], panels[13][1]['ranks'][:, i]):
            raise ValueError('Fresh-prefix model changed with outer cadence')
    if s['prediction_sha256'] != _hash(directory/'predictions_26.csv'):
        raise ValueError('Development prediction parent hash mismatch')
    recomputed = select_development(split_panel(panel, 'development'))
    _compare(s, recomputed, 'frozen development verification')
    _table(directory/'development_grid.csv', recomputed['development_rows'], ['id'])
    recomputed_gate = validate_selection(split_panel(panel, 'validation'), recomputed)
    _compare(gate, recomputed_gate, 'frozen validation verification')
    ranks = _rankings(panel, allpanel, s, gate)
    verify_frozen_rankings(directory/'frozen_rankings.npz', panel['targets'], panel['actual'], ranks)
    table_counts = _tables(directory, panel, allpanel, s, gate, ranks)
    r13 = _rankings(*panels[13], s, gate); cadence_rows = []
    for scope, (a, b) in SPLITS.items():
        mask = (panel['targets'] >= a) & (panel['targets'] <= b)
        for name in dict.fromkeys(['SelectedEnsemble', 'GapLogistic', s['best_single']]):
            cadence_rows.append(dict(scope=scope, model=name, cadence=13, **independent_metrics(r13[name][mask], panel['actual'][mask])))
    _table(directory/'cadence_robustness.csv', cadence_rows, ['scope', 'model'])
    samples = _underlying_samples(history, raw[26])
    placebo_checks = _placebos(directory, panel)
    portfolio_checks = _portfolios(history, directory, panel, ranks, s)
    ledger = _json(directory/'provenance_before.json'); unavailable = []
    for candidate in ledger['candidates']:
        for artifact in candidate['artifacts']:
            if artifact['availability'] == 'HISTORICAL_UNAVAILABLE':
                unavailable.append(artifact['path'])
                if (ROOT/artifact['path']).exists():
                    raise ValueError('Historical missing artifact was recreated in original location')
    summary = _json(directory/'main_summary.json')
    _compare(summary, dict(selected=gate['selected'], best_single=s['best_single'], validation_passed=gate['passed'],
                           historical_cutoff=1245, draw1246_used=False, draw1247_prediction_generated=False), 'summary frozen identity')
    if summary['status'] != config['historical_status']:
        raise ValueError('Summary/configuration status mismatch')
    tables = {name: pd.read_csv(directory/f'{name}.csv', float_precision='round_trip')
              for name in ('performance', 'paired', 'placebos', 'robustness', 'cadence_robustness')}
    decision = independent_decision(tables['performance'], tables['paired'], tables['placebos'],
                                    tables['robustness'], tables['cadence_robustness'], s['best_single'], gate['passed'])
    # The original strict-comparison report remains byte-preserved. Check its
    # unchanged scientific decision and the separately recorded tie correction.
    original_comparison = decision.pop('placebo_comparison')
    _compare(summary, decision, 'independent final decision')
    _compare(summary['placebo_comparison'], {k: v for k, v in original_comparison.items() if k != 'raw_tail_fractions'}, 'promotion diagnostics')
    correction = _json(directory/'reporting_correction.json')
    _compare(correction, dict(original_summary_sha256=_hash(directory/'main_summary.json'),
        placebo_sha256=_hash(directory/'placebos.csv'), original_raw_tail_fractions=summary['placebo_comparison']['raw_tail_fractions'],
        corrected_raw_tail_fractions=original_comparison['raw_tail_fractions'], tolerance=1e-12,
        promotion_tail_fractions=original_comparison['promotion_tail_fractions'], status=decision['status'],
        validation_passed=gate['passed'], selection_changed=False, final_evaluation_rerun=False), 'reporting correction')
    ready = gate['passed'] and decision['status'] in ('EXPLORATORY_ENSEMBLE_CANDIDATE', 'HISTORICAL_ENSEMBLE_ADVANTAGE')
    _compare(config, dict(ready_for_1247=bool(ready), readiness='H17_CONFIGURATION_FROZEN_READY_FOR_1247' if ready else 'H17_CONFIGURATION_FROZEN_NOT_CURRENTLY_JUSTIFIED',
                         candidates=list(PROMOTED), underlying_configurations={n: canonical_configs()[n] for n in PROMOTED}), 'configuration readiness')
    result = dict(status='PASS', verification_only=True, historical_cutoff=1245,
        starting_head=start['head'], protected_files_verified=len(start['protected']),
        scientific_sources_verified=len(p['source_hashes']), archive_status=archive['status'], archive_files_verified=len(archive['files']),
        stage_hashes={k: _digest(v) for k, v in stages.items()}, prediction_rows_each=7*345,
        table_rows=table_counts, frozen_rank_arrays=len(ranks), underlying_score_samples=samples,
        underlying_gap_retrained=False, all_base_predictions_retrained=False,
        placebo_rows=398, placebo_seed_checks=398, placebo_full_recomputations=placebo_checks,
        portfolio=portfolio_checks, original_artifacts_verified=False, original_artifacts_still_unavailable=sorted(set(unavailable)),
        historical_final_model_selection_evaluations=1, audit_selection_changes=0,
        reporting_correction_verified=True, corrected_raw_tail_fractions=original_comparison['raw_tail_fractions'],
        original_main_summary_raw_tails_superseded=True, historical_status=decision['status'], configuration_readiness=config['readiness'],
        draw1246_used=False, draw1247_prediction_generated=False, publication_executed=False,
        limitations=['Hash links verify present consistency, not a trusted external timestamp.',
                     'Historical data were previously inspected; this audit establishes no prospective evidence.',
                     'Gap scores were not all refitted; saved rows, hit distributions, source outcomes and downstream arithmetic were checked.'],
        audited_artifact_sha256={f.name: _hash(f) for f in sorted(directory.iterdir()) if f.is_file() and f.name != 'audit_result.json'})
    (directory/'audit_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf8')
    return result
