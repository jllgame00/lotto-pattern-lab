"""Phase25 H24 offline orchestration; no collection or publication command."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from time import perf_counter
import numpy as np
import pandas as pd
from .optimal_transport_cli import archive_inventory,load_source
from .random_matrix_cli import dump
from .analysis.recurrence import research_matrix
from .analysis.spatiotemporal import iid_surrogate,constrained_surrogate
from .analysis.symbolic_search import (FAMILIES,metric_vector,fit_calibration,standardize,
    complete_search,null_search,compare_maxima,development_selection)

ROOT=Path(__file__).resolve().parents[1]


def guard(directory):
    directory=Path(directory).resolve()
    if not directory.is_relative_to((ROOT/'reports/symbolic').resolve()):raise ValueError('H24 outputs must stay under reports/symbolic')
    directory.mkdir(parents=True,exist_ok=True);return directory


def prospective_guard(target,archive_status):
    if type(target) is not int or target!=1247:raise ValueError('Target1246 is forbidden; only1247 may be considered')
    if archive_status=='PROSPECTIVE_ARCHIVE_INTEGRITY_FAILURE':raise ValueError(archive_status)
    if archive_status!='VERIFIED':raise ValueError('PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION')
    raise ValueError('PREDICTIVE_MODEL_NOT_JUSTIFIED: no Phase25 publication capability')


def prepare(directory):
    if (directory/'starting_state.json').exists():raise FileExistsError('Starting state already recorded')
    root=subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=ROOT,text=True).strip()
    if root!='D:/univ/personal/lotto-pattern-lab':raise ValueError('Unexpected Git root; STOP')
    allowed={'.gitignore','README.md','docs/README.md','docs/research-ideas.md','src/cli.py'}
    tracked=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
    artifacts={name:sha256((ROOT/name).read_bytes()).hexdigest() for name in tracked if name not in allowed and (ROOT/name).is_file()}
    archive=archive_inventory(ROOT/'reports/prospective')
    dump(directory/'starting_state.json',dict(root=root,branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),artifacts=artifacts,archive=archive,
        initial_worktree='clean (verified before implementation)',research_cutoff=1245,draw1246_used=False))
    print(f"Archive {archive['status']}: {len(archive['files'])}files/{len(archive['checks'])}checks",flush=True)


def load_calibration(directory,n):
    c=json.loads((directory/f'calibration_{n}.json').read_text(encoding='utf-8'));path=directory/f'calibration_{n}.npz'
    if c['npz_sha256']!=sha256(path.read_bytes()).hexdigest():raise ValueError('Calibration hash mismatch')
    with np.load(path) as f:c.update({k:f[k] for k in f.files})
    return c


def calibrate(directory):
    for n in (900,1245):
        target=directory/f'calibration_{n}.json'
        if target.exists() or target.with_suffix('.npz').exists():raise FileExistsError('Calibration exists')
        c=fit_calibration(n,progress=lambda m:print(m,flush=True));arrays={k:c.pop(k) for k in ('mean','std','raw_std','eligible','pilot_values')}
        path=target.with_suffix('.npz');np.savez_compressed(path,**arrays)
        dump(target,dict(c,npz_sha256=sha256(path.read_bytes()).hexdigest()))


def save_metrics(directory,scope,raw,c):
    z=standardize(raw,c)
    pd.DataFrame([dict(key=key,value=raw['values'][i],z=z[i],eligible=bool(c['eligible'][i]),**raw['metadata'][i])
        for i,key in enumerate(raw['keys'])]).to_csv(Path(directory)/f'{scope}_metrics.csv',index=False)
    np.savez_compressed(Path(directory)/f'{scope}_raw.npz',values=raw['values'])


def analyze(x,directory):
    x=research_matrix(x)
    if len(x)!=1245:raise ValueError('Canonical H24 requires1..1245')
    if any((directory/f).exists() for f in ('real_summary.json','null_progress.jsonl')):raise FileExistsError('Analysis evidence exists')
    c={n:load_calibration(directory,n) for n in (900,1245)}
    if any(v['seed']!=251001 or v['replicates']!=32 or not v['eligible'].all() for v in c.values()):raise ValueError('Canonical32pilot/all304cell calibration required')
    began=perf_counter();real={}
    for scope,n in [('development',900),('full',1245)]:
        raw=metric_vector(x[:n]);real[scope]=complete_search(raw,c[n]);save_metrics(directory,scope,raw,c[n])
    dump(directory/'real_summary.json',real);np.save(directory/'binary_series.npy',x)
    with (directory/'null_progress.jsonl').open('x',encoding='utf-8') as stream:
        def progress(row):
            for scope in real:
                if row[scope]['space']!=real[scope]['space']:raise ValueError('Complete search parity failed')
            record={key:({k:v for k,v in value.items() if k!='raw_values'} if key in real else value) for key,value in row.items()}
            stream.write(json.dumps(record,allow_nan=False)+'\n');stream.flush()
            if (row['replicate']+1)%10==0:print(f"{row['null_model']} {row['replicate']+1}/199, {perf_counter()-began:.1f}s",flush=True)
        rows=null_search(x,c,progress=progress)
    comparison=[];maxima=[]
    for scope in real:
        np.savez_compressed(directory/f'null_metrics_{scope}.npz',values=np.array([r[scope]['raw_values'] for r in rows]))
        comparison.extend(compare_maxima(real[scope],rows,scope=scope))
        maxima.extend(dict(scope=scope,null_model=row['null_model'],replicate=row['replicate'],**row[scope]['maxima']) for row in rows)
    pd.DataFrame(comparison).to_csv(directory/'global_null_comparison.csv',index=False)
    pd.DataFrame(maxima).to_csv(directory/'null_maxima.csv',index=False)
    selection=development_selection(x[:900],c[900],rows)
    digest=sha256(json.dumps(selection,sort_keys=True,allow_nan=False).encode()).hexdigest()
    dump(directory/'selected_configuration.json',dict(selection=selection,sha256=digest))
    dump(directory/'analysis_metadata.json',dict(research_cutoff=1245,bin_fit_end=200,symbol_start=201,
        development_validation=[601,900],later_validation=[901,1245],main_seed=250042,pilot_seed=251001,
        pilots_per_scope=32,replicates_per_null=199,fixed_margin_trades_per_row=20,workers=1,
        runtime_seconds=perf_counter()-began,input_hash=sha256(x.tobytes()).hexdigest(),
        draw1246_used=False,publication_executed=False,gate=selection['decision']))
    print(selection['decision'],flush=True)


def verify_maxima(values,c,expected):
    values=np.asarray(values,float);eligible=np.asarray(c['eligible']);z=np.full_like(values,np.nan)
    z[:,eligible]=(values[:,eligible]-np.asarray(c['mean'])[eligible])/np.asarray(c['std'])[eligible]
    for family in FAMILIES:
        mask=(np.array(c['families'])==family)&eligible
        np.testing.assert_allclose(np.max(z[:,mask],axis=1),expected[family],rtol=1e-12,atol=1e-12)
    return z


def audit(x,directory):
    x=research_matrix(x)
    if len(x)!=1245:raise ValueError('Canonical H24 audit requires1..1245')
    baseline=json.loads((directory/'starting_state.json').read_text(encoding='utf-8'))
    real=json.loads((directory/'real_summary.json').read_text(encoding='utf-8'))
    rows=[json.loads(line) for line in (directory/'null_progress.jsonl').read_text(encoding='utf-8').splitlines()]
    assert [(r['null_model'],r['replicate']) for r in rows]==[(k,i) for k in ('iid','fixed_margins') for i in range(199)]
    comparison=pd.read_csv(directory/'global_null_comparison.csv');maxima=pd.read_csv(directory/'null_maxima.csv')
    assert len(comparison)==24 and len(maxima)==796
    checks={};replayed=[]
    for scope,n in [('full',1245),('development',900)]:
        c=load_calibration(directory,n);fresh=fit_calibration(n,progress=lambda m:print('Audit '+m,flush=True))
        for k in ('mean','std','raw_std','eligible','pilot_values'):np.testing.assert_array_equal(c[k],fresh[k])
        raw=metric_vector(x[:n])
        with np.load(directory/f'{scope}_raw.npz') as f:np.testing.assert_array_equal(raw['values'],f['values'])
        with np.load(directory/f'null_metrics_{scope}.npz') as f:values=f['values']
        assert values.shape==(398,304)
        expected={family:np.array([real[scope]['maxima'][family]]+[r[scope]['maxima'][family] for r in rows]) for family in FAMILIES}
        z=verify_maxima(np.vstack((raw['values'],values)),c,expected)
        saved=pd.read_csv(directory/f'{scope}_metrics.csv')
        np.testing.assert_allclose(saved.value,raw['values'],rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(saved.z,z[0],rtol=1e-12,atol=1e-12,equal_nan=True)
        for family in FAMILIES:
            np.testing.assert_allclose(maxima[maxima.scope==scope][family],expected[family][1:],rtol=1e-12)
            for kind,offset in [('iid',0),('fixed_margins',199)]:
                p=(1+np.sum(expected[family][offset+1:offset+200]>=expected[family][0]))/200
                r=comparison[(comparison.scope==scope)&(comparison.family==family)&(comparison.null_model==kind)].iloc[0]
                np.testing.assert_allclose([r.global_p,r.adjusted_p],[p,min(1.,6*p)],rtol=1e-12)
        for kind,code,offset in [('iid',0,0),('fixed_margins',1,199)]:
            for i in (0,198):
                seed=int(np.random.SeedSequence([250042,code,i,n]).generate_state(1)[0])
                null=iid_surrogate(n,seed=seed) if kind=='iid' else constrained_surrogate(x[:n],seed=seed)
                replay=metric_vector(null);np.testing.assert_array_equal(replay['values'],values[offset+i])
                assert replay['encoding_hash']==rows[offset+i][scope]['encoding_hash']
                assert replay['representation_hash']==rows[offset+i][scope]['representation_hash']
                replayed.append(dict(scope=scope,null_model=kind,replicate=i,seed=seed))
        for row in rows:
            assert row[scope]['rebuilt'] and row[scope]['row_six'] and row[scope]['space']==raw['space']
            if row['null_model']=='fixed_margins':assert row[scope]['fixed_margins_preserved']
        checks[scope]=dict(cells=304,eligible=int(c['eligible'].sum()),pilots_replayed=32,all_raw_vectors_to_max_to_p=True)
    selection=json.loads((directory/'selected_configuration.json').read_text(encoding='utf-8'))
    assert selection['sha256']==sha256(json.dumps(selection['selection'],sort_keys=True,allow_nan=False).encode()).hexdigest()
    assert selection['selection']==development_selection(x[:900],load_calibration(directory,900),rows)
    for name,digest in baseline['artifacts'].items():assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    assert baseline['archive']==archive_inventory(ROOT/'reports/prospective')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==baseline['head']
    # Independent count/context arithmetic instead of the vectorized occurrence ranks.
    from .analysis.symbolic import encode_all,word_codes,prequential_losses,ALPHAS
    encoded=encode_all(x)
    for name,r in encoded.items():
        s=r['symbols'];A=r['alphabet'];loss=prequential_losses(s,A);contexts=[{} for _ in range(4)]
        for t,target in enumerate(s):
            predictions=[]
            for k in range(4):
                context=tuple(s[t-k:t]) if k<=t else None
                counts=contexts[k].get(context,np.zeros(A,int)) if context is not None else np.zeros(A,int)
                prob=np.array([(counts[target]+alpha)/(counts.sum()+alpha*A) for alpha in ALPHAS])
                if k and (context is None or counts.sum()<20):prob=predictions[-1]
                predictions.append(prob)
                if context is not None:
                    if context not in contexts[k]:contexts[k][context]=np.zeros(A,int)
                    contexts[k][context][target]+=1
            np.testing.assert_allclose(np.exp(-loss[t]),np.array(predictions),rtol=1e-12,atol=1e-12)
        for L in (2,3,4):
            literal=np.array([sum(int(s[i+j])*A**(L-j-1) for j in range(L)) for i in range(len(s)-L+1)])
            np.testing.assert_array_equal(word_codes(s,A,L),literal)
    checks.update(protected_artifacts_unchanged=len(baseline['artifacts']),archive_status=baseline['archive']['status'],
        archive_unchanged=True,head_unchanged=True,replayed_main_cases=replayed,independent_prequential_context_counts=True,
        independent_word_encoding=True,draw1246_used=False,publication_executed=False,
        limitation='64pilots and8representative main histories replayed; all796saved raw vectors audited, not all398histories regenerated')
    dump(directory/'audit_result.json',checks);print('H24 audit passed',flush=True)


def add_commands(commands):
    p=commands.add_parser('symbolic',help='Phase25 H24 offline1..1245, calibration1..200')
    p.add_argument('action',choices=['prepare','calibrate','analyze','diagnostics','audit'])
    p.add_argument('--reports-dir',type=Path,default=ROOT/'reports/symbolic')


def run(args):
    directory=guard(args.reports_dir)
    if args.action=='prepare':prepare(directory);return
    if not (directory/'starting_state.json').exists():raise ValueError('Run prepare first')
    if args.action=='calibrate':calibrate(directory);return
    _,x=load_source(args.data)
    if args.action=='analyze':analyze(x,directory)
    elif args.action=='audit':audit(x,directory)
    elif args.action=='diagnostics':
        from .analysis.symbolic_diagnostics import diagnostics
        diagnostics(x,directory)
