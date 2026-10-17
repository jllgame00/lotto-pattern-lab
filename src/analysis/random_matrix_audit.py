"""Arithmetic/seed/provenance audit independently of the search-max reducer."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import numpy as np
import pandas as pd
from .recurrence import research_matrix
from .spatiotemporal import iid_surrogate,constrained_surrogate
from .random_matrix_search import FAMILIES,metric_vector,fit_calibration


def verify_maxima(values,c,expected):
    values=np.asarray(values,float)
    z=np.full_like(values,np.nan);eligible=np.asarray(c['eligible'])
    z[:,eligible]=(values[:,eligible]-np.asarray(c['mean'])[eligible])/np.asarray(c['std'])[eligible]
    for family in FAMILIES:
        indices=np.flatnonzero((np.array(c['families'])==family)&eligible)
        np.testing.assert_allclose(np.nanmax(z[:,indices],axis=1),expected[family],rtol=1e-12,atol=1e-12)
    return z


def audit(x,directory):
    from src.random_matrix_cli import load_calibration,dump
    directory=Path(directory);target=directory/'audit_result.json'
    if target.exists():raise FileExistsError('Audit result exists')
    x=research_matrix(x)
    if len(x)!=1245:raise ValueError('Canonical historical audit requires1..1245')
    baseline=json.loads((directory/'starting_state.json').read_text(encoding='utf-8'))
    root=Path(baseline['root'])
    rows=[json.loads(line) for line in (directory/'null_progress.jsonl').read_text(encoding='utf-8').splitlines()]
    assert [(r['null_model'],r['replicate']) for r in rows]==[(k,i) for k in ('iid','fixed_margins') for i in range(199)]
    real=json.loads((directory/'real_summary.json').read_text(encoding='utf-8'))
    table=pd.read_csv(directory/'global_null_comparison.csv');maxima_table=pd.read_csv(directory/'null_maxima.csv')
    assert len(table)==24 and len(maxima_table)==796
    checks={};replayed=[]
    for scope,n,cells,rolling in [('full',1245,2443,39),('development',900,1699,27)]:
        c=load_calibration(directory,n);fresh=fit_calibration(n,replicates=32,seed=221001)
        for key in ('pilot_values','mean','std','eligible','finite_count'):
            np.testing.assert_allclose(c[key],fresh[key],rtol=0,atol=0,equal_nan=True)
        raw=metric_vector(x[:n]);assert raw['space']==real[scope]['space']
        assert len(raw['keys'])==cells and raw['space']['rolling_fits']==rolling
        assert raw['representation_hash']==real[scope]['representation_hash']
        with np.load(directory/f'{scope}_raw.npz') as f:
            np.testing.assert_allclose(raw['values'],f['values'],rtol=0,atol=0,equal_nan=True)
            np.testing.assert_allclose(raw['spectra'],f['spectra'],rtol=0,atol=0,equal_nan=True)
        with np.load(directory/f'null_metrics_{scope}.npz') as f:null=f['values'];spectra=f['spectra']
        assert null.shape==(398,cells) and spectra.shape==(398,*raw['spectra'].shape)
        expected={f:np.array([real[scope]['maxima'][f]]+[row[scope]['maxima'][f] for row in rows]) for f in FAMILIES}
        z=verify_maxima(np.vstack((raw['values'],null)),c,expected)
        stored=pd.read_csv(directory/f'{scope}_metrics.csv')
        assert stored.key.tolist()==raw['keys']
        np.testing.assert_allclose(stored.value,raw['values'],rtol=1e-12,equal_nan=True)
        np.testing.assert_allclose(stored.z,z[0],rtol=1e-12,atol=1e-12,equal_nan=True)
        for family in FAMILIES:
            np.testing.assert_allclose(maxima_table[maxima_table.scope==scope][family],expected[family][1:],rtol=1e-12)
            for kind,start in [('iid',0),('fixed_margins',199)]:
                a=expected[family][start+1:start+200];p=(1+np.sum(a>=expected[family][0]))/200
                saved=table[(table.scope==scope)&(table.null_model==kind)&(table.family==family)]
                assert len(saved)==1
                np.testing.assert_allclose([saved.iloc[0].global_p,saved.iloc[0].adjusted_p],[p,min(1,6*p)],rtol=1e-12)
        # Direct full 45-coordinate eigvalsh, independently of projected helper.
        for row in raw['intervals']:
            values=x[row['start']-1:row['end']].astype(float)
            cov=np.cov(values,rowvar=False);std=np.sqrt(np.diag(cov));scale=np.outer(std,std)
            corr=np.divide(cov,scale,out=np.zeros_like(cov),where=scale>0)
            for kind,matrix in [('correlation',corr),('covariance',cov)]:
                fit=row[kind];d=fit['nontrivial_dimension']
                direct=np.maximum(np.linalg.eigvalsh(matrix)[::-1][:d],0.)
                np.testing.assert_allclose(direct,fit['eigenvalues'],rtol=1e-10,atol=1e-12)
        for lagged in raw['lagged']:
            lag=lagged['lag'];a=x[:n-lag].astype(float);b=x[lag:n].astype(float)
            a=(a-a.mean(0))/a.std(0,ddof=1);b=(b-b.mean(0))/b.std(0,ddof=1)
            singular=np.linalg.svd(a.T@b/(len(a)-1),compute_uv=False)[:44]
            np.testing.assert_allclose(singular,lagged['singular_values'],rtol=1e-10,atol=1e-12)
        for kind,code,offset in [('iid',0,0),('fixed_margins',1,199)]:
            for i in (0,198):
                seed=int(np.random.SeedSequence([220042,code,i,n]).generate_state(1)[0]);entry=rows[offset+i][scope]
                assert seed==entry['seed']
                surrogate=iid_surrogate(n,seed=seed) if kind=='iid' else constrained_surrogate(x[:n],seed=seed)
                assert (surrogate.sum(1)==6).all()
                if kind=='fixed_margins':np.testing.assert_array_equal(surrogate.sum(0),x[:n].sum(0))
                replay=metric_vector(surrogate,details=False)
                np.testing.assert_allclose(replay['values'],null[offset+i],rtol=0,atol=0,equal_nan=True)
                np.testing.assert_allclose(replay['spectra'],spectra[offset+i],rtol=0,atol=0,equal_nan=True)
                assert replay['representation_hash']==entry['representation_hash']
                replayed.append(dict(scope=scope,null_model=kind,replicate=i,seed=seed))
        for row in rows:
            entry=row[scope];assert entry['space']==raw['space'] and entry['row_six'] and entry['rebuilt']
            if row['null_model']=='fixed_margins':assert entry['fixed_margins_preserved']
        checks[scope]=dict(cells=cells,rolling_fits=rolling,eligible=int(c['eligible'].sum()),pilots_replayed=32,
                           raw_to_own_max_to_p=True,independent_all_interval_eigenspectra=True,independent_all_lag_singular_values=True)
    selection=json.loads((directory/'selected_configuration.json').read_text(encoding='utf-8'))
    assert sha256(json.dumps(selection['selection'],sort_keys=True,allow_nan=False).encode()).hexdigest()==selection['sha256']
    for relative,expected_hash in baseline['artifacts'].items():
        assert sha256((root/relative).read_bytes()).hexdigest()==expected_hash,relative
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==baseline['head']
    assert not (root/'reports/prospective').exists()
    checks.update(protected_artifacts_unchanged=len(baseline['artifacts']),head_unchanged=True,replayed_main_cases=replayed,
        draw1246_used=False,archive_present=False,prospective_status='PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION',
        limitation='All64 pilots/eight representative main histories replayed; all796 saved null vectors audited. Not all398 histories regenerated.')
    dump(target,checks);print('RMT audit passed',flush=True)
    return checks
