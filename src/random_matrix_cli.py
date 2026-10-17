"""Offline H21 orchestration: no fetching, prediction or publication command."""
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from .analysis.recurrence import research_matrix
from .analysis.spatiotemporal import lotto_matrix
from .analysis.random_matrix_search import (FAMILIES,metric_vector,fit_calibration,standardize,
    complete_search,null_search,compare_maxima,development_selection)
from .recurrence_cli import load_research_source

ROOT=Path(__file__).resolve().parents[1]


def safe(value):
    if isinstance(value,dict):return {str(k):safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,np.ndarray)):return [safe(v) for v in value]
    if isinstance(value,(float,np.floating)):return float(value) if np.isfinite(value) else None
    if isinstance(value,np.generic):return value.item()
    return value


def dump(path,payload):
    Path(path).write_text(json.dumps(safe(payload),ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def guard(directory):
    directory=Path(directory).resolve();allowed=(ROOT/'reports/random_matrix').resolve()
    if not directory.is_relative_to(allowed):raise ValueError('H21 output must stay under reports/random_matrix')
    directory.mkdir(parents=True,exist_ok=True);return directory


def canonical_matrix(x):
    x=research_matrix(x)
    if len(x)!=1245:raise ValueError('Canonical H21 requires exact1..1245')
    return x


def prospective_guard(target,archive):
    if type(target) is not int or target!=1247:raise ValueError('Target1246 is forbidden; only1247 may be considered')
    archive=Path(archive)
    if not archive.is_dir() or not any(archive.rglob('*')):raise ValueError('PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION')
    raise ValueError('PREDICTIVE_MODEL_NOT_JUSTIFIED: no Phase22 publication capability')


def load_calibration(directory,n):
    path=directory/f'calibration_{n}.npz';meta=json.loads((directory/f'calibration_{n}.json').read_text(encoding='utf-8'))
    if sha256(path.read_bytes()).hexdigest()!=meta.pop('npz_sha256'):raise ValueError('Calibration integrity mismatch')
    with np.load(path,allow_pickle=False) as data:meta.update({k:data[k] for k in data.files})
    if meta['draws']!=n:raise ValueError('Calibration cutoff mismatch')
    return meta


def calibrate(directory,pilots):
    for n in (1245,900):
        if (directory/f'calibration_{n}.json').exists():
            c=load_calibration(directory,n)
            if c['replicates']!=pilots or c['seed']!=221001:raise ValueError('Existing calibration differs')
            continue
        if (directory/f'calibration_{n}.npz').exists():raise FileExistsError('Partial calibration exists')
        began=perf_counter();c=fit_calibration(n,replicates=pilots,progress=lambda m:print(m,flush=True))
        arrays={k:c.pop(k) for k in ('mean','std','eligible','finite_count','pilot_values')}
        path=directory/f'calibration_{n}.npz';np.savez_compressed(path,**arrays)
        dump(directory/f'calibration_{n}.json',dict(c,npz_sha256=sha256(path.read_bytes()).hexdigest(),runtime_seconds=perf_counter()-began))


def benchmark(x,directory):
    if (directory/'benchmark.json').exists():raise FileExistsError('Benchmark exists')
    c={n:load_calibration(directory,n) for n in (1245,900)};times=[]
    began=perf_counter()
    def progress(row):
        now=perf_counter();times.append(now-progress.last);progress.last=now
        print(f"Benchmark {row['null_model']} {row['replicate']}: {times[-1]:.3f}s",flush=True)
    progress.last=began;null_search(x,c,replicates=2,seed=220000,progress=progress)
    dump(directory/'benchmark.json',dict(seconds=times,estimated_serial_seconds=float(np.mean(times)*398),
        chosen_replicates=199,complete_search=True,full_and_development=True))


def analyze(x,directory,replicates,workers):
    x=canonical_matrix(x)
    owned=('real_summary.json','null_progress.jsonl','analysis_metadata.json','full_metrics.csv','full_raw.npz',
        'development_metrics.csv','development_raw.npz','binary_series.npy','null_metrics_full.npz',
        'null_metrics_development.npz','null_maxima.csv','global_null_comparison.csv')
    if any((directory/f).exists() for f in owned):
        raise FileExistsError('Research evidence already exists')
    c={n:load_calibration(directory,n) for n in (1245,900)};real={};began=perf_counter()
    for scope,n in [('full',1245),('development',900)]:
        raw=metric_vector(x[:n]);real[scope]=complete_search(raw,c[n]);z=standardize(raw,c[n])
        pd.DataFrame([dict(key=key,value=raw['values'][i],z=z[i],**raw['metadata'][i]) for i,key in enumerate(raw['keys'])]).to_csv(directory/f'{scope}_metrics.csv',index=False)
        np.savez_compressed(directory/f'{scope}_raw.npz',values=raw['values'],spectra=raw['spectra'])
    dump(directory/'real_summary.json',real);np.save(directory/'binary_series.npy',x)
    with (directory/'null_progress.jsonl').open('x',encoding='utf-8') as stream:
        def progress(row):
            for scope in real:
                if row[scope]['space']!=real[scope]['space']:raise RuntimeError('Null search inventory mismatch')
            record={k:({a:b for a,b in v.items() if a not in ('raw_values','spectra')} if k in real else v) for k,v in row.items()}
            stream.write(json.dumps(record,allow_nan=False)+'\n');stream.flush()
            if (row['replicate']+1)%10==0:print(f"{row['null_model']} {row['replicate']+1}/{replicates}: {perf_counter()-began:.1f}s",flush=True)
        rows=null_search(x,c,replicates=replicates,workers=workers,progress=progress)
    flat=[];comparison=[]
    for scope in real:
        np.savez_compressed(directory/f'null_metrics_{scope}.npz',values=np.array([r[scope]['raw_values'] for r in rows]),spectra=np.array([r[scope]['spectra'] for r in rows]))
        flat.extend(dict(scope=scope,null_model=r['null_model'],replicate=r['replicate'],**r[scope]['maxima']) for r in rows)
        comparison.extend(compare_maxima(real[scope],rows,scope=scope))
    pd.DataFrame(flat).to_csv(directory/'null_maxima.csv',index=False)
    pd.DataFrame(comparison).to_csv(directory/'global_null_comparison.csv',index=False)
    dump(directory/'analysis_metadata.json',dict(research_cutoff=1245,development_cutoff=900,seed=220042,pilot_seed=221001,
        pilots_per_scope=c[1245]['replicates'],replicates_per_null=replicates,workers=workers,runtime_seconds=perf_counter()-began,
        input_matrix_hash=sha256(x.tobytes()).hexdigest(),draw1246_used=False,publication_executed=False))


def select(x,directory):
    x=canonical_matrix(x);path=directory/'selected_configuration.json'
    if path.exists():raise FileExistsError('Development decision is frozen')
    meta=json.loads((directory/'analysis_metadata.json').read_text(encoding='utf-8'))
    if any(meta.get(k)!=v for k,v in dict(research_cutoff=1245,development_cutoff=900,seed=220042,pilot_seed=221001,pilots_per_scope=32,replicates_per_null=199).items()):
        raise ValueError('Canonical complete null protocol required')
    c=load_calibration(directory,900);raw=metric_vector(x[:900])
    with np.load(directory/'development_raw.npz') as f:np.testing.assert_allclose(f['values'],raw['values'],rtol=0,atol=0,equal_nan=True)
    with np.load(directory/'null_metrics_development.npz') as f:null=f['values']
    if null.shape!=(398,len(c['keys'])):raise ValueError('Incomplete development null vectors')
    rows=[json.loads(line) for line in (directory/'null_progress.jsonl').read_text(encoding='utf-8').splitlines()]
    if [(r['null_model'],r['replicate']) for r in rows]!=[(k,i) for k in ('iid','fixed_margins') for i in range(199)]:raise ValueError('Null inventory incomplete')
    z=np.divide(null-c['mean'],c['std'],out=np.full_like(null,np.nan),where=c['eligible'][None,:])
    for family in FAMILIES:
        mask=np.array(c['families'])==family;maxima=np.nanmax(z[:,mask],axis=1)
        np.testing.assert_allclose(maxima,[row['development']['maxima'][family] for row in rows],rtol=1e-12)
    selection=development_selection(x[:900],c,rows)
    digest=sha256(json.dumps(selection,sort_keys=True,allow_nan=False).encode()).hexdigest()
    dump(path,dict(selection=selection,sha256=digest));print(selection['decision'],flush=True)


def add_commands(commands):
    p=commands.add_parser('random-matrix',help='Phase22 H21 offline1..1245; no publication')
    p.add_argument('action',choices=['calibrate','benchmark','analyze','select','diagnostics','audit'])
    p.add_argument('--reports-dir',type=Path,default=ROOT/'reports/random_matrix')
    p.add_argument('--pilots',type=int,default=32);p.add_argument('--surrogates',type=int,default=199);p.add_argument('--workers',type=int,default=3)


def run(args):
    directory=guard(args.reports_dir)
    if args.action=='calibrate':calibrate(directory,args.pilots);return
    data=load_research_source(args.data);x=canonical_matrix(lotto_matrix(data,cutoff=len(data)))
    if args.action=='benchmark':benchmark(x,directory)
    elif args.action=='analyze':analyze(x,directory,args.surrogates,args.workers)
    elif args.action=='select':select(x,directory)
    elif args.action=='diagnostics':
        from .analysis.random_matrix_diagnostics import diagnostics
        diagnostics(x,directory)
    elif args.action=='audit':
        from .analysis.random_matrix_audit import audit
        audit(x,directory)
