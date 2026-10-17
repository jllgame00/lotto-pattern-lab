"""Independent Kruskal, cloud arithmetic, own-max and seeded H22 audits."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist,squareform
from .recurrence import research_matrix
from .spatiotemporal import iid_surrogate,constrained_surrogate
from .topology_search import FAMILIES,metric_vector,fit_calibration


def kruskal_deaths(distances):
    d=np.asarray(distances,float);n=len(d);a,b=np.triu_indices(n,1);weights=d[a,b]
    order=np.argsort(weights,kind='stable');parent=np.arange(n);size=np.ones(n,int);deaths=[]
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for index in order:
        u=find(int(a[index]));v=find(int(b[index]))
        if u==v:continue
        if size[u]<size[v]:u,v=v,u
        parent[v]=u;size[u]+=size[v];deaths.append(float(weights[index]))
        if len(deaths)==n-1:break
    return np.asarray(deaths)


def verify_maxima(values,c,expected):
    values=np.asarray(values,float);eligible=np.asarray(c['eligible']);z=np.full_like(values,np.nan)
    z[:,eligible]=(values[:,eligible]-np.asarray(c['mean'])[eligible])/np.asarray(c['std'])[eligible]
    entropy=np.array(c['families'])=='h0_entropy';z[:,entropy]=abs(z[:,entropy])
    for family in FAMILIES:
        mask=(np.array(c['families'])==family)&eligible
        np.testing.assert_allclose(np.nanmax(z[:,mask],axis=1),expected[family],rtol=1e-12,atol=1e-12)
    return z


def audit(x,directory):
    from src.topology_cli import load_calibration,dump
    directory=Path(directory);target=directory/'audit_result.json'
    if target.exists():raise FileExistsError('Audit result exists')
    x=research_matrix(x)
    if len(x)!=1245:raise ValueError('Canonical historical audit requires1..1245')
    baseline=json.loads((directory/'starting_state.json').read_text(encoding='utf-8'));root=Path(baseline['root'])
    rows=[json.loads(line) for line in (directory/'null_progress.jsonl').read_text(encoding='utf-8').splitlines()]
    assert [(r['null_model'],r['replicate']) for r in rows]==[(k,i) for k in ('iid','fixed_margins') for i in range(199)]
    real=json.loads((directory/'real_summary.json').read_text(encoding='utf-8'))
    table=pd.read_csv(directory/'global_null_comparison.csv');maxima_table=pd.read_csv(directory/'null_maxima.csv')
    assert len(table)==16 and len(maxima_table)==796
    checks={};replayed=[]
    for scope,n,cells,cloud_count in [('full',1245,560,140),('development',900,380,95)]:
        c=load_calibration(directory,n)
        fresh=fit_calibration(n,replicates=32,seed=231001,progress=lambda text:print('Audit '+text,flush=True))
        for key in ('pilot_values','mean','std','eligible','finite_count'):
            np.testing.assert_allclose(c[key],fresh[key],rtol=0,atol=0,equal_nan=True)
        raw=metric_vector(x[:n]);assert raw['space']==real[scope]['space'] and len(raw['clouds'])==cloud_count
        assert len(raw['keys'])==cells and raw['representation_hash']==real[scope]['representation_hash']
        with np.load(directory/f'{scope}_raw.npz') as f:np.testing.assert_allclose(raw['values'],f['values'],rtol=0,atol=0,equal_nan=True)
        with np.load(directory/f'null_metrics_{scope}.npz') as f:null=f['values']
        assert null.shape==(398,cells)
        expected={f:np.array([real[scope]['maxima'][f]]+[row[scope]['maxima'][f] for row in rows]) for f in FAMILIES}
        z=verify_maxima(np.vstack((raw['values'],null)),c,expected)
        stored=pd.read_csv(directory/f'{scope}_metrics.csv');assert stored.key.tolist()==raw['keys']
        np.testing.assert_allclose(stored.value,raw['values'],rtol=1e-12,equal_nan=True)
        np.testing.assert_allclose(stored.z,z[0],rtol=1e-12,atol=1e-12,equal_nan=True)
        for family in FAMILIES:
            np.testing.assert_allclose(maxima_table[maxima_table.scope==scope][family],expected[family][1:],rtol=1e-12)
            for kind,start in [('iid',0),('fixed_margins',199)]:
                a=expected[family][start+1:start+200];p=(1+np.sum(a>=expected[family][0]))/200
                saved=table[(table.scope==scope)&(table.null_model==kind)&(table.family==family)]
                assert len(saved)==1
                np.testing.assert_allclose([saved.iloc[0].global_p,saved.iloc[0].adjusted_p],[p,min(1,4*p)],rtol=1e-12)
        # Independent cloud construction/scaling, SciPy metric, and Kruskal.
        for cloud in raw['clouds']:
            local=x[cloud['start']-1:cloud['end']]
            if cloud['family']=='A':values=local.astype(float);metric=cloud['metric']
            elif cloud['family']=='B':
                numbers=(np.nonzero(local)[1]+1).reshape(-1,6);gaps=np.diff(numbers,axis=1)
                shape=np.column_stack((numbers.sum(1),np.ptp(numbers,axis=1),numbers.std(1),gaps.mean(1),gaps.std(1),(gaps==1).sum(1),(numbers%2==1).sum(1)))
                std=shape.std(0);constant=np.ptp(shape,axis=0)==0
                values=(shape-shape.mean(0))/np.where(constant,1.,std);values[:,constant]=0.;metric='euclidean'
            else:
                values=np.array([x[a-1:b].mean(0) for a,b in zip(cloud['block_starts'],cloud['point_draws'])]);metric='euclidean'
                assert np.all(cloud['block_starts'][1:]>cloud['point_draws'][:-1])
            np.testing.assert_allclose(values,cloud['values'],rtol=1e-12,atol=1e-12)
            d=squareform(pdist(values,metric));deaths=kruskal_deaths(d);p=cloud['persistence']
            np.testing.assert_allclose(deaths,p['finite_intervals'][:,1],rtol=1e-10,atol=1e-10)
            assert len(deaths)==cloud['points']-1 and p['infinite_components']==1
            total=float(deaths.sum());weights=deaths[deaths>0]/total if total else np.empty(0)
            expected_summary=[deaths[-1],total,-np.sum(weights*np.log(weights)),deaths[-max(1,int(np.ceil(.1*len(deaths)))):].sum()/total if total else 0.]
            np.testing.assert_allclose(expected_summary,[p[s] for s in ('longest','total','entropy','tail')],rtol=1e-10,atol=1e-10)
        print(f'Audit independent {scope}: {cloud_count} clouds',flush=True)
        for kind,code,offset in [('iid',0,0),('fixed_margins',1,199)]:
            for i in (0,198):
                seed=int(np.random.SeedSequence([230042,code,i,n]).generate_state(1)[0]);entry=rows[offset+i][scope]
                assert seed==entry['seed']
                surrogate=iid_surrogate(n,seed=seed) if kind=='iid' else constrained_surrogate(x[:n],seed=seed)
                assert (surrogate.sum(1)==6).all()
                if kind=='fixed_margins':np.testing.assert_array_equal(surrogate.sum(0),x[:n].sum(0))
                replay=metric_vector(surrogate,details=False)
                np.testing.assert_allclose(replay['values'],null[offset+i],rtol=0,atol=0,equal_nan=True)
                assert replay['representation_hash']==entry['representation_hash'] and replay['space']==raw['space']
                replayed.append(dict(scope=scope,null_model=kind,replicate=i,seed=seed))
        for row in rows:
            entry=row[scope];assert entry['space']==raw['space'] and entry['row_six'] and entry['rebuilt']
            if row['null_model']=='fixed_margins':assert entry['fixed_margins_preserved']
        checks[scope]=dict(cells=cells,clouds=cloud_count,eligible=int(c['eligible'].sum()),pilots_replayed=32,
            raw_to_own_max_to_p=True,independent_cloud_scaling_distances_and_kruskal=True,identical_null_point_counts=True)
    selection=json.loads((directory/'selected_configuration.json').read_text(encoding='utf-8'))
    assert sha256(json.dumps(selection['selection'],sort_keys=True,allow_nan=False).encode()).hexdigest()==selection['sha256']
    dev=table[table.scope=='development'];passing=[f for f in FAMILIES if (dev[dev.family==f].adjusted_p<=.05).all()]
    assert passing==selection['selection']['passing_families']
    for relative,digest in baseline['artifacts'].items():assert sha256((root/relative).read_bytes()).hexdigest()==digest,relative
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==baseline['head']
    assert not (root/'reports/prospective').exists()
    checks.update(protected_artifacts_unchanged=len(baseline['artifacts']),head_unchanged=True,replayed_main_cases=replayed,
        draw1246_used=False,archive_present=False,h1_status='H1_DEFERRED_DEPENDENCY_LIMITATION',
        limitation='All64 pilots/eight representative main histories replayed; all796 saved null vectors audited. Not all398 histories regenerated.')
    dump(target,checks);print('Topology audit passed',flush=True)
    return checks
