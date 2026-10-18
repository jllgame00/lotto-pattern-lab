"""Predeclared H23 search. Every surrogate rebuilds every representation/cell."""
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import numpy as np
from .recurrence import research_matrix
from .spatiotemporal import iid_surrogate, constrained_surrogate
from .optimal_transport import (LAGS, ROLLING_WINDOWS, STEPS, BARYCENTER_WINDOWS,
    draw_positions, lag_distances, direction, acceleration, correlation,
    successor_diagnostic, rolling_distribution, rolling_drift, discrete_w1,
    barycenter_diagnostic, geodesic_residual)

FAMILIES = ('lag_magnitude', 'direction', 'successor', 'rolling_drift', 'barycenter', 'geodesic')


def metric_vector(x, *, details=False):
    x = research_matrix(x)
    if len(x) < 132:
        raise ValueError('H23 complete search requires132..1245 draws')
    a = draw_positions(x); d = np.diff(a, axis=0)
    keys, families, metadata, values = [], [], [], []
    def add(family, name, value, **meta):
        keys.append(f'{family}|{name}'); families.append(family)
        metadata.append(dict(family=family, statistic=name, **meta)); values.append(float(value))
    for lag in LAGS:
        for p in (1, 2):
            distances = lag_distances(a, lag, p)
            for name, v in [('mean', distances.mean()), ('std', distances.std())]:
                add('lag_magnitude', f'W{p}_lag{lag}_{name}', v, lag=lag, p=p)
    magnitude = abs(d).mean(1)
    for lag in LAGS:
        add('lag_magnitude', f'magnitude_rank_lag{lag}', correlation(magnitude[:-lag], magnitude[lag:]), lag=lag)
    # Quartile thresholds describe the completed scope; not a forecasting rule.
    q25, q75 = np.quantile(magnitude[:-1], [.25, .75])
    nxt = magnitude[1:]; prev = magnitude[:-1]
    add('lag_magnitude', 'large_minus_small_next', nxt[prev >= q75].mean()-nxt[prev <= q25].mean())
    for lag in (1, 2, 3, 4):
        for name, v in direction(d[:-lag], d[lag:]).items():
            add('direction', f'{name}_lag{lag}', v.mean(), lag=lag)
    acc = acceleration(d)
    add('direction', 'acceleration_absolute', abs(acc).mean())
    add('direction', 'acceleration_rms', np.sqrt(np.mean(acc**2, axis=1)).mean())
    add('direction', 'acceleration_repeat_cosine', direction(acc[:-1], acc[1:])['cosine'].mean())
    successor = {}
    for metric in ('euclidean', 'cosine'):
        r = successor_diagnostic(d, metric); successor[metric] = r
        for name in ('cosine_relation', 'distance_relation'):
            add('successor', f'{metric}_{name}', r[name], metric=metric)
        for name in ('nearest_distance', 'cosine_gain', 'distance_gain'):
            add('successor', f'{metric}_{name}', r[name].mean(), metric=metric)
    drift = {}
    for w in ROLLING_WINDOWS:
        for step in STEPS:
            r = rolling_drift(a, w, step); drift[w, step] = r
            for name, v in [('mean', r['distance'].mean()), ('max', r['distance'].max())]:
                add('rolling_drift', f'W{w}_step{step}_{name}', v, window=w, step=step)
            movement = r['cdf_movement']
            add('rolling_drift', f'W{w}_step{step}_reversal',
                direction(movement[:-1], movement[1:])['cosine'].mean(), window=w, step=step)
        p, ends = rolling_distribution(a, w)
        # Historical return at endpoints13 apart, at least26 draws distant.
        returns = [discrete_w1(p[:i-25], p[i]).min() for i in range(26, len(p), 13)]
        add('rolling_drift', f'W{w}_return', np.mean(returns), window=w)
    barycenters = {}
    for w in BARYCENTER_WINDOWS:
        for p in (1, 2):
            r = barycenter_diagnostic(a, w, p); barycenters[w, p] = r
            for name in ('next_distance', 'recent_distance', 'gain', 'movement'):
                add('barycenter', f'W{w}_W{p}_{name}', r[name].mean(), window=w, p=p)
    for p in (1, 2):
        r = geodesic_residual(a, p)
        add('geodesic', f'W{p}_mean', r.mean(), p=p)
        add('geodesic', f'W{p}_std', r.std(), p=p)
    space = dict(cells=len(keys), family_cells={f:families.count(f) for f in FAMILIES},
                 lags=list(LAGS), rolling_windows=list(ROLLING_WINDOWS), steps=list(STEPS),
                 barycenter_windows=list(BARYCENTER_WINDOWS), pair_stride=3,
                 nearest_exclusion=3, direction_lags=[1,2,3,4], primary_metric='W1',
                 vector_metrics=['euclidean','cosine'], score='two-sided absolute pilot z')
    out = dict(draws=len(x), keys=keys, families=families, metadata=metadata,
               values=np.asarray(values), space=space, representation_hash=sha256(x.tobytes()).hexdigest())
    if details: out.update(positions=a, transports=d, successors=successor, drift=drift, barycenters=barycenters)
    return out


def fit_calibration(n, *, replicates=32, seed=241001, progress=None):
    if type(n) is not int or not 132 <= n <= 1245 or type(replicates) is not int or replicates < 4:
        raise ValueError('Historical cutoff and at least four pilots required')
    rows = []
    for i in range(replicates):
        child = int(np.random.SeedSequence([seed, n, i]).generate_state(1)[0])
        raw = metric_vector(iid_surrogate(n, seed=child)); rows.append(raw['values'])
        if progress: progress(f'Pilot {n}: {i+1}/{replicates}')
    a = np.asarray(rows); mean = a.mean(0); std = a.std(0, ddof=1)
    return dict(draws=n, replicates=replicates, seed=seed, keys=raw['keys'], families=raw['families'],
                metadata=raw['metadata'], space=raw['space'], mean=mean, std=std,
                eligible=np.isfinite(std)&(std>1e-12), pilot_values=a)


def standardize(raw, c):
    if raw['draws'] != c['draws'] or raw['keys'] != c['keys']:
        raise ValueError('Calibration scope/search mismatch')
    z = np.full(len(raw['keys']), np.nan); active = np.asarray(c['eligible']) & np.isfinite(raw['values'])
    z[active] = abs((raw['values'][active]-np.asarray(c['mean'])[active])/np.asarray(c['std'])[active])
    return z


def complete_search(raw, c):
    z = standardize(raw, c); maxima, leaders = {}, {}; families = np.array(raw['families'])
    for family in FAMILIES:
        indices = np.flatnonzero((families == family)&np.isfinite(z))
        if not len(indices): raise ValueError(f'No eligible cells: {family}')
        i = int(indices[np.argmax(z[indices])]); maxima[family] = float(z[i])
        leaders[family] = dict(index=i, key=raw['keys'][i], value=float(raw['values'][i]), z=float(z[i]), **raw['metadata'][i])
    return dict(draws=raw['draws'], maxima=maxima, leaders=leaders, space=raw['space'],
                eligible_cells=int(np.isfinite(z).sum()), representation_hash=raw['representation_hash'])


def _null_job(x, c, kind, code, i, seed, dev):
    row = dict(null_model=kind, replicate=i)
    for scope, actual in [('full', x)]+([('development', x[:900])] if dev else []):
        n = len(actual); child = int(np.random.SeedSequence([seed, code, i, n]).generate_state(1)[0])
        null = iid_surrogate(n, seed=child) if kind=='iid' else constrained_surrogate(actual, seed=child)
        raw = metric_vector(null)
        row[scope] = dict(complete_search(raw, c[n]), seed=child, rebuilt=True, raw_values=raw['values'],
                          row_six=bool((null.sum(1)==6).all()), changed_fraction=float((actual!=null).mean()),
                          fixed_margins_preserved=bool(np.array_equal(actual.sum(0), null.sum(0))) if kind!='iid' else None)
    return row


def _initialize(x, c, dev):
    global _WORKER
    _WORKER = x, c, dev


def _job(job):
    x, c, dev = _WORKER
    return _null_job(x, c, *job, dev)


def null_search(x, calibrations, *, replicates=199, seed=240042, workers=1, include_development=True, progress=None):
    x = research_matrix(x)
    if include_development and len(x)!=1245: raise ValueError('Full/development requires exact1..1245')
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:
        raise ValueError('Positive counts required')
    c = {n:{k:v[k] for k in ('draws','keys','mean','std','eligible')} for n,v in calibrations.items()}
    jobs = [(kind,code,i,seed) for kind,code in [('iid',0),('fixed_margins',1)] for i in range(replicates)]
    rows = []
    def collect(iterator):
        for row in iterator:
            rows.append(row)
            if progress: progress(row)
    if workers==1: collect(_null_job(x,c,*job,include_development) for job in jobs)
    else:
        with ProcessPoolExecutor(max_workers=workers,initializer=_initialize,initargs=(x,c,include_development)) as pool:
            collect(pool.map(_job,jobs,chunksize=1))
    return rows


def compare_maxima(real, rows, *, scope='full'):
    out = []
    for kind in ('iid','fixed_margins'):
        selected = [r[scope] for r in rows if r['null_model']==kind]
        if not selected: raise ValueError('Both null families required')
        for family in FAMILIES:
            a = np.array([r['maxima'][family] for r in selected]); obs = real['maxima'][family]
            p = (1+int((a>=obs).sum()))/(len(a)+1)
            out.append(dict(scope=scope,null_model=kind,family=family,real_max=obs,
                null_median=float(np.median(a)),global_p=p,adjusted_p=min(1.,6*p),replicates=len(a)))
    return out


def development_selection(x, c, rows):
    x = research_matrix(x)
    if len(x)!=900 or c.get('draws')!=900: raise ValueError('Development requires exact1..900')
    raw = metric_vector(x, details=True); found = complete_search(raw,c)
    comparison = compare_maxima(found,rows,scope='development')
    passing = [f for f in FAMILIES if all(r['adjusted_p']<=.05 for r in comparison if r['family']==f)]
    metrics = {}
    for metric, r in raw['successors'].items():
        eras = [dict(cosine_gain=float(r['cosine_gain'][s].mean()),distance_gain=float(r['distance_gain'][s].mean()))
                for s in np.array_split(np.arange(len(r['query_indices'])),3)]
        stable = all(e['cosine_gain']>0 and e['distance_gain']>0 for e in eras)
        favorable = {}
        for name in ('cosine_gain','distance_gain'):
            i = raw['keys'].index(f'successor|{metric}_{name}')
            signed_z = float((raw['values'][i]-np.asarray(c['mean'])[i])/np.asarray(c['std'])[i]) if c['eligible'][i] else 0.
            evidence = []
            for kind in ('iid','fixed_margins'):
                null_max = np.array([row['development']['maxima']['successor'] for row in rows if row['null_model']==kind])
                p = (1+int((null_max>=signed_z).sum()))/(len(null_max)+1) if signed_z>0 else 1.
                evidence.append(dict(null_model=kind,signed_z=signed_z,global_p=p,adjusted_p=min(1.,6*p)))
            favorable[name] = evidence
        directionally_supported = all(e['adjusted_p']<=.05 for group in favorable.values() for e in group)
        metrics[metric] = dict(cosine_gain=float(r['cosine_gain'].mean()),distance_gain=float(r['distance_gain'].mean()),
            eras=eras,stable=stable,favorable_evidence=favorable,directionally_supported=directionally_supported)
    candidates = [m for m in metrics if 'successor' in passing and metrics[m]['stable'] and metrics[m]['directionally_supported']]
    selected = max(candidates,key=lambda m:metrics[m]['cosine_gain']) if candidates else None
    return dict(training_cutoff=900,training_hash=sha256(x.tobytes()).hexdigest(),later_start=901,
        passing_families=passing,successor_metrics=metrics,selected_metric=selected,
        continuation_gate_passed=bool(selected),barycenter_independent_model=False,
        barycenter_reason='Average quantiles equal the trivial sorted-position mean exactly',
        predictive_model_justified=bool(selected),
        decision='CONTINUATION_IMPLEMENTATION_REQUIRED' if selected else 'PREDICTIVE_MODEL_NOT_JUSTIFIED',
        ensemble_decision='PENDING_LATER_EVALUATION' if selected else 'NOT CURRENTLY JUSTIFIED',comparison=comparison)
