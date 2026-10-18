"""Offline H23 runner. No collection, import, publication or target command."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from time import perf_counter
import numpy as np
import pandas as pd
from .analysis.recurrence import research_matrix
from .analysis.spatiotemporal import lotto_matrix, iid_surrogate, constrained_surrogate
from .analysis.optimal_transport_search import (FAMILIES, metric_vector, fit_calibration,
    standardize, complete_search, null_search, compare_maxima, development_selection)
from .recurrence_cli import load_research_source
from .random_matrix_cli import dump

ROOT = Path(__file__).resolve().parents[1]


def guard(directory):
    directory = Path(directory).resolve()
    if not directory.is_relative_to((ROOT/'reports/optimal_transport').resolve()):
        raise ValueError('H23 output must stay under reports/optimal_transport')
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def canonical_matrix(x):
    x = research_matrix(x)
    if len(x)!=1245: raise ValueError('Canonical H23 requires exact1..1245')
    return x


def load_source(path):
    data = load_research_source(path)
    return data, canonical_matrix(lotto_matrix(data, cutoff=len(data)))


def archive_inventory(archive):
    archive = Path(archive)
    if not archive.exists(): return dict(status='ABSENT', files={}, checks=[])
    files = {p.relative_to(archive).as_posix():sha256(p.read_bytes()).hexdigest()
             for p in sorted(archive.rglob('*')) if p.is_file()}
    checks = []
    for record in sorted(archive.rglob('*_integrity.json')):
        try:
            payload = json.loads(record.read_text(encoding='utf-8'))
            mapping = payload.get('files', payload)
            if not isinstance(mapping, dict) or not mapping: raise ValueError('Empty integrity record')
            for name, digest in mapping.items():
                target = (record.parent/name).resolve()
                valid = target.is_relative_to(archive.resolve()) and target.is_file()
                valid = valid and sha256(target.read_bytes()).hexdigest()==digest
                checks.append(dict(record=record.relative_to(archive).as_posix(),file=name,verified=bool(valid)))
        except (ValueError, TypeError, OSError) as exc:
            checks.append(dict(record=record.relative_to(archive).as_posix(),verified=False,error=str(exc)))
    verified = bool(checks) and all(c['verified'] for c in checks)
    return dict(status='VERIFIED' if verified else 'PROSPECTIVE_ARCHIVE_INTEGRITY_FAILURE',files=files,checks=checks)


def prospective_guard(target, archive_status):
    if type(target) is not int or target!=1247:
        raise ValueError('Target1246 is forbidden; only1247 may be considered')
    if archive_status=='PROSPECTIVE_ARCHIVE_INTEGRITY_FAILURE': raise ValueError(archive_status)
    if archive_status!='VERIFIED': raise ValueError('PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION')
    raise ValueError('PREDICTIVE_MODEL_NOT_JUSTIFIED: no Phase24 publication capability')


def prepare(directory):
    path = directory/'starting_state.json'
    if path.exists(): raise FileExistsError('Starting evidence exists')
    root = subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=ROOT,text=True).strip()
    if root!='D:/univ/personal/lotto-pattern-lab': raise ValueError('Unexpected Git root; STOP')
    allowed = {'.gitignore','README.md','docs/README.md','docs/research-ideas.md','src/cli.py'}
    tracked = subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
    artifacts = {p:sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked if p not in allowed and (ROOT/p).is_file()}
    archive = archive_inventory(ROOT/'reports/prospective')
    dump(path,dict(root=root,branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        initial_worktree='clean (verified before implementation)',artifacts=artifacts,archive=archive,
        research_cutoff=1245,draw1246_used=False))
    print(f"Archive {archive['status']}: {len(archive['files'])} files, {len(archive['checks'])} checks",flush=True)


def load_calibration(directory, n):
    c = json.loads((directory/f'calibration_{n}.json').read_text(encoding='utf-8'))
    path = directory/f'calibration_{n}.npz'
    if sha256(path.read_bytes()).hexdigest()!=c['npz_sha256']: raise ValueError('Calibration hash mismatch')
    with np.load(path) as f: c.update({k:f[k] for k in f.files})
    return c


def calibrate(directory, pilots=32):
    for n in (900,1245):
        target = directory/f'calibration_{n}.json'
        if target.exists() or target.with_suffix('.npz').exists(): raise FileExistsError('Calibration exists')
        c = fit_calibration(n,replicates=pilots,progress=lambda m:print(m,flush=True))
        arrays = {k:c.pop(k) for k in ('mean','std','eligible','pilot_values')}
        path = directory/f'calibration_{n}.npz'; np.savez_compressed(path,**arrays)
        dump(target,dict(c,npz_sha256=sha256(path.read_bytes()).hexdigest()))


def analyze(x, directory, *, replicates=199, workers=1):
    x = canonical_matrix(x)
    if (directory/'real_summary.json').exists() or (directory/'null_progress.jsonl').exists():
        raise FileExistsError('Analysis evidence exists')
    c = {n:load_calibration(directory,n) for n in (900,1245)}
    if any(v['replicates']!=32 or v['seed']!=241001 for v in c.values()) or replicates!=199:
        raise ValueError('Canonical H23 requires32 pilots and199+199 nulls')
    began = perf_counter(); real = {}
    for scope,n in [('development',900),('full',1245)]:
        raw = metric_vector(x[:n]); real[scope] = complete_search(raw,c[n]); z = standardize(raw,c[n])
        pd.DataFrame([dict(key=key,value=raw['values'][i],z=z[i],**raw['metadata'][i]) for i,key in enumerate(raw['keys'])]).to_csv(directory/f'{scope}_metrics.csv',index=False)
        np.savez_compressed(directory/f'{scope}_raw.npz',values=raw['values'])
    dump(directory/'real_summary.json',real); np.save(directory/'binary_series.npy',x)
    with (directory/'null_progress.jsonl').open('x',encoding='utf-8') as stream:
        def progress(row):
            record = {}
            for key,value in row.items():
                record[key] = {k:v for k,v in value.items() if k!='raw_values'} if key in real else value
            for scope in real:
                if row[scope]['space']!=real[scope]['space']: raise ValueError('Null search parity mismatch')
            stream.write(json.dumps(record,allow_nan=False)+'\n'); stream.flush()
            if (row['replicate']+1)%10==0: print(f"{row['null_model']} {row['replicate']+1}/{replicates}, {perf_counter()-began:.1f}s",flush=True)
        rows = null_search(x,c,replicates=replicates,workers=workers,progress=progress)
    maxima,comparison = [],[]
    for scope in real:
        np.savez_compressed(directory/f'null_metrics_{scope}.npz',values=np.array([r[scope]['raw_values'] for r in rows]))
        maxima.extend(dict(scope=scope,null_model=r['null_model'],replicate=r['replicate'],**r[scope]['maxima']) for r in rows)
        comparison.extend(compare_maxima(real[scope],rows,scope=scope))
    pd.DataFrame(maxima).to_csv(directory/'null_maxima.csv',index=False)
    pd.DataFrame(comparison).to_csv(directory/'global_null_comparison.csv',index=False)
    selection = development_selection(x[:900],c[900],rows)
    digest = sha256(json.dumps(selection,sort_keys=True,allow_nan=False).encode()).hexdigest()
    dump(directory/'selected_configuration.json',dict(selection=selection,sha256=digest))
    dump(directory/'analysis_metadata.json',dict(research_cutoff=1245,development_cutoff=900,later_start=901,
        main_seed=240042,pilot_seed=241001,pilots_per_scope=32,replicates_per_null=replicates,workers=workers,
        runtime_seconds=perf_counter()-began,draw1246_used=False,publication_executed=False,
        input_matrix_hash=sha256(x.tobytes()).hexdigest(),fixed_margin_trades_per_row=20,
        gate=selection['decision']))
    print(selection['decision'],flush=True)


def verify_maxima(values,c,expected):
    values = np.asarray(values,float); eligible = np.asarray(c['eligible'])
    z = np.full_like(values,np.nan)
    z[:,eligible] = abs((values[:,eligible]-np.asarray(c['mean'])[eligible])/np.asarray(c['std'])[eligible])
    for family in FAMILIES:
        mask = (np.array(c['families'])==family)&eligible
        np.testing.assert_allclose(np.max(z[:,mask],axis=1),expected[family],rtol=1e-12,atol=1e-12)
    return z


def audit(x,directory):
    x = canonical_matrix(x); baseline = json.loads((directory/'starting_state.json').read_text(encoding='utf-8'))
    real = json.loads((directory/'real_summary.json').read_text(encoding='utf-8'))
    rows = [json.loads(line) for line in (directory/'null_progress.jsonl').read_text(encoding='utf-8').splitlines()]
    assert [(r['null_model'],r['replicate']) for r in rows]==[(k,i) for k in ('iid','fixed_margins') for i in range(199)]
    comparison = pd.read_csv(directory/'global_null_comparison.csv')
    maxima_table = pd.read_csv(directory/'null_maxima.csv')
    assert len(comparison)==24 and len(maxima_table)==796
    replayed = []; checks = {}
    for scope,n in [('full',1245),('development',900)]:
        c = load_calibration(directory,n); raw = metric_vector(x[:n])
        fresh = fit_calibration(n,replicates=32,progress=lambda m:print('Audit '+m,flush=True))
        for key in ('mean','std','eligible','pilot_values'): np.testing.assert_array_equal(c[key],fresh[key])
        with np.load(directory/f'null_metrics_{scope}.npz') as f: values = f['values']
        assert values.shape==(398,len(raw['keys']))
        with np.load(directory/f'{scope}_raw.npz') as f: np.testing.assert_array_equal(raw['values'],f['values'])
        expected = {f:np.array([real[scope]['maxima'][f]]+[r[scope]['maxima'][f] for r in rows]) for f in FAMILIES}
        z = verify_maxima(np.vstack((raw['values'],values)),c,expected)
        for family in FAMILIES:
            np.testing.assert_allclose(maxima_table[maxima_table.scope==scope][family],expected[family][1:],rtol=1e-12)
        saved = pd.read_csv(directory/f'{scope}_metrics.csv')
        np.testing.assert_allclose(saved.value,raw['values'],rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(saved.z,z[0],rtol=1e-12,atol=1e-12)
        for family in FAMILIES:
            for kind,offset in [('iid',0),('fixed_margins',199)]:
                p = (1+np.sum(expected[family][offset+1:offset+200]>=expected[family][0]))/200
                r = comparison[(comparison.scope==scope)&(comparison.family==family)&(comparison.null_model==kind)].iloc[0]
                np.testing.assert_allclose([r.global_p,r.adjusted_p],[p,min(1,6*p)],rtol=1e-12)
        for kind,code,offset in [('iid',0,0),('fixed_margins',1,199)]:
            for i in (0,198):
                seed = int(np.random.SeedSequence([240042,code,i,n]).generate_state(1)[0])
                null = iid_surrogate(n,seed=seed) if kind=='iid' else constrained_surrogate(x[:n],seed=seed)
                replay = metric_vector(null)
                np.testing.assert_array_equal(replay['values'],values[offset+i])
                assert replay['representation_hash']==rows[offset+i][scope]['representation_hash']
                assert rows[offset+i][scope]['seed']==seed
                replayed.append(dict(scope=scope,null_model=kind,replicate=i,seed=seed))
        for row in rows:
            assert row[scope]['space']==raw['space'] and row[scope]['rebuilt'] and row[scope]['row_six']
            if row['null_model']=='fixed_margins': assert row[scope]['fixed_margins_preserved']
        checks[scope] = dict(cells=len(raw['keys']),pilots_replayed=32,all_raw_vectors_to_own_max_to_p=True)
    selected = json.loads((directory/'selected_configuration.json').read_text(encoding='utf-8'))
    assert selected['sha256']==sha256(json.dumps(selected['selection'],sort_keys=True,allow_nan=False).encode()).hexdigest()
    assert selected['selection']==development_selection(x[:900],load_calibration(directory,900),rows)
    for name,digest in baseline['artifacts'].items(): assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    assert baseline['archive']==archive_inventory(ROOT/'reports/prospective')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==baseline['head']
    # Independent arithmetic checks, without calling the OT helper functions.
    from scipy.stats import wasserstein_distance
    from .analysis.optimal_transport import draw_positions, lag_distances, rolling_distribution, discrete_w1, barycenter_diagnostic, geodesic_residual
    positions = draw_positions(x)
    for lag in (1,2,3,4,8,13,26):
        for p in (1,2):
            expected_distance = np.array([(sum(abs(v-u)**p for u,v in zip(a,b))/6)**(1/p)
                for a,b in zip(positions[:-lag],positions[lag:])])
            np.testing.assert_allclose(lag_distances(positions,lag,p),expected_distance,rtol=1e-12)
    for w in (26,52,104):
        probs,ends = rolling_distribution(positions,w)
        for i in (0,len(probs)//2,len(probs)-1):
            counts = np.bincount(positions[ends[i]-w:ends[i]].astype(int).ravel(),minlength=46)[1:]/(6*w)
            np.testing.assert_allclose(probs[i],counts,rtol=1e-12)
        for step in (1,4,13,26):
            for i in (step,len(probs)-1):
                expected_distance = wasserstein_distance(np.arange(1,46),np.arange(1,46),probs[i-step],probs[i])
                np.testing.assert_allclose(discrete_w1(probs[i-step],probs[i]),expected_distance,rtol=1e-12,atol=1e-12)
    for w in (10,26,52):
        b = barycenter_diagnostic(positions,w)
        for i in range(len(b['barycenters'])):
            np.testing.assert_allclose(b['barycenters'][i],positions[i:i+w].mean(0),rtol=1e-12)
    second = np.diff(positions,n=2,axis=0)
    np.testing.assert_allclose(geodesic_residual(positions),abs(second).mean(1)/2,rtol=1e-12)
    checks.update(archive_status=baseline['archive']['status'],archive_unchanged=True,head_unchanged=True,
        protected_artifacts_unchanged=len(baseline['artifacts']),replayed_main_cases=replayed,
        independent_lag_arithmetic=True,independent_discrete_w1_scipy=True,independent_rolling_counts=True,
        independent_mean_barycenters=True,geodesic_acceleration_identity=True,
        draw1246_used=False,publication_executed=False,
        limitation='All64 pilots and8 representative main histories replayed; all796 saved raw vectors audited. Not all398 histories regenerated.')
    dump(directory/'audit_result.json',checks); print('H23 audit passed',flush=True)


def add_commands(commands):
    p = commands.add_parser('optimal-transport',help='Phase24 H23 offline exact OT1..1245')
    p.add_argument('action',choices=['prepare','calibrate','analyze','diagnostics','audit'])
    p.add_argument('--reports-dir',type=Path,default=ROOT/'reports/optimal_transport')
    p.add_argument('--workers',type=int,default=1)


def run(args):
    directory = guard(args.reports_dir)
    if args.action=='prepare': prepare(directory); return
    if not (directory/'starting_state.json').exists(): raise ValueError('Run prepare/archive inventory first')
    if args.action=='calibrate': calibrate(directory); return
    _,x = load_source(args.data)
    if args.action=='analyze': analyze(x,directory,workers=args.workers)
    elif args.action=='diagnostics':
        from .analysis.optimal_transport_diagnostics import diagnostics
        diagnostics(x,directory)
    elif args.action=='audit': audit(x,directory)
