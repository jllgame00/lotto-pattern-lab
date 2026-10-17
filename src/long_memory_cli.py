"""H20 sealed, offline research; no predictive or publication command."""
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.analysis.recurrence import research_matrix
from src.analysis.spatiotemporal import lotto_matrix
from src.analysis.long_memory_search import (FAMILIES,PRIMARY,metric_vector,fit_calibration,
    standardize,complete_search,null_search,compare_maxima,development_selection)
from src.recurrence_cli import load_research_source,dump

ROOT=Path(__file__).resolve().parents[1]


def guard(directory):
    directory=Path(directory).resolve();allowed=(ROOT/'reports/long_memory').resolve()
    if not directory.is_relative_to(allowed):raise ValueError('H20 output must stay under reports/long_memory')
    directory.mkdir(parents=True,exist_ok=True);return directory


def canonical_matrix(x):
    x=research_matrix(x)
    if len(x)!=1245:raise ValueError('Canonical H20 requires exact1..1245')
    return x


def prospective_guard(target,archive):
    """Negative guard only; does not implement a prospective capability."""
    if target!=1247:raise ValueError('Target1246 is known; only1247 may ever be considered')
    archive=Path(archive)
    if not archive.is_dir() or not any(archive.rglob('*')):raise ValueError('PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION')
    raise ValueError('PREDICTIVE_MODEL_NOT_JUSTIFIED: no Phase21 publication capability')


def load_calibration(directory,n):
    path=directory/f'calibration_{n}.npz';meta=json.loads((directory/f'calibration_{n}.json').read_text(encoding='utf-8'))
    if sha256(path.read_bytes()).hexdigest()!=meta.pop('npz_sha256'):raise ValueError('Calibration integrity mismatch')
    with np.load(path) as data:meta.update({k:data[k] for k in data.files})
    if meta['draws']!=n:raise ValueError('Calibration cutoff mismatch')
    return meta


def calibrate(directory,pilots):
    for n in (1245,900):
        if (directory/f'calibration_{n}.json').exists():
            c=load_calibration(directory,n)
            if c['replicates']!=pilots or c['seed']!=211001:raise ValueError('Existing calibration differs')
            continue
        if (directory/f'calibration_{n}.npz').exists():raise ValueError('Calibration already exists')
        began=perf_counter();c=fit_calibration(n,replicates=pilots,progress=lambda m:print(m,flush=True))
        arrays={k:c.pop(k) for k in ('mean','std','eligible','finite_count','pilot_values')}
        path=directory/f'calibration_{n}.npz';np.savez_compressed(path,**arrays)
        dump(directory/f'calibration_{n}.json',dict(c,npz_sha256=sha256(path.read_bytes()).hexdigest(),runtime_seconds=perf_counter()-began))


def benchmark(x,directory):
    c={n:load_calibration(directory,n) for n in (1245,900)};times=[]
    def progress(row):
        now=perf_counter();times.append(now-progress.last);progress.last=now
        print(f"Benchmark {row['null_model']} {row['replicate']+1}/2: {times[-1]:.3f}s",flush=True)
    progress.last=perf_counter();null_search(x,c,replicates=2,seed=210000,progress=progress)
    dump(directory/'benchmark.json',dict(seconds=times,estimated_serial_199_each_seconds=float(np.mean(times)*398),
        chosen_replicates=199,full_and_development=True,complete_search=True))


def analyze(x,directory,replicates,workers):
    x=canonical_matrix(x);c={n:load_calibration(directory,n) for n in (1245,900)}
    if any((directory/f).exists() for f in ('real_summary.json','null_progress.jsonl','analysis_metadata.json')):raise ValueError('Research evidence already exists')
    real={};began=perf_counter()
    for scope,n in [('full',1245),('development',900)]:
        raw=metric_vector(x[:n]);real[scope]=complete_search(raw,c[n]);z=standardize(raw,c[n])
        pd.DataFrame([dict(key=k,value=float(raw['values'][i]),z=float(z[i]),**raw['metadata'][i]) for i,k in enumerate(raw['keys'])]).to_csv(directory/f'{scope}_metrics.csv',index=False)
        np.savez_compressed(directory/f'{scope}_raw.npz',values=raw['values'])
    dump(directory/'real_summary.json',real);np.save(directory/'binary_series.npy',x)
    with (directory/'null_progress.jsonl').open('x',encoding='utf-8') as stream:
        def progress(row):
            for scope in real:
                if row[scope]['space']!=real[scope]['space']:raise RuntimeError('Null search-space mismatch')
            record={k:({a:b for a,b in v.items() if a!='raw_values'} if k in real else v) for k,v in row.items()}
            stream.write(json.dumps(record)+'\n');stream.flush()
            if (row['replicate']+1)%10==0:print(f"{row['null_model']} {row['replicate']+1}/{replicates}: {perf_counter()-began:.1f}s",flush=True)
        rows=null_search(x,c,replicates=replicates,workers=workers,progress=progress)
    flat=[];comparison=[]
    for scope in real:
        np.savez_compressed(directory/f'null_metrics_{scope}.npz',values=np.array([r[scope]['raw_values'] for r in rows]))
        flat.extend(dict(scope=scope,null_model=r['null_model'],replicate=r['replicate'],**r[scope]['maxima']) for r in rows)
        comparison.extend(compare_maxima(real[scope],rows,scope=scope))
    pd.DataFrame(flat).to_csv(directory/'null_maxima.csv',index=False)
    pd.DataFrame(comparison).to_csv(directory/'global_null_comparison.csv',index=False)
    dump(directory/'analysis_metadata.json',dict(research_cutoff=1245,development_cutoff=900,seed=210042,
        pilot_seed=211001,pilots_per_scope=c[1245]['replicates'],replicates_per_null=replicates,
        workers=workers,runtime_seconds=perf_counter()-began,draw1246_used=False,publication_executed=False))


def select(x,directory):
    """Recompute saved own maxima before accepting development-only evidence."""
    x=canonical_matrix(x);meta=json.loads((directory/'analysis_metadata.json').read_text())
    if any(meta.get(k)!=v for k,v in dict(research_cutoff=1245,development_cutoff=900,seed=210042,pilot_seed=211001,pilots_per_scope=32,replicates_per_null=199).items()):raise ValueError('Canonical complete null protocol required')
    c=load_calibration(directory,900);raw=metric_vector(x[:900]);found=complete_search(raw,c)
    with np.load(directory/'development_raw.npz') as f:stored=f['values']
    with np.load(directory/'null_metrics_development.npz') as f:null=f['values']
    if not np.allclose(raw['values'],stored,equal_nan=True) or null.shape!=(398,len(c['keys'])):raise ValueError('Development source/search mismatch')
    nz=np.divide(null-c['mean'],c['std'],out=np.full_like(null,np.nan),where=c['eligible'][None,:])
    table=pd.read_csv(directory/'global_null_comparison.csv');table=table[table.scope=='development']
    if len(table)!=18:raise ValueError('All primary and secondary families required')
    for kind,start in [('iid',0),('fixed_margins',199)]:
        for family in FAMILIES:
            mask=np.array(c['families'])==family;a=np.nanmax(nz[start:start+199,mask],axis=1)
            p=(1+int((a>=found['maxima'][family]).sum()))/200;correction=6 if family in PRIMARY else 3
            row=table[(table.null_model==kind)&(table.family==family)]
            if len(row)!=1 or not np.isclose(row.iloc[0].global_p,p) or not np.isclose(row.iloc[0].adjusted_p,min(1,correction*p)):raise ValueError('Development global-max evidence mismatch')
    selection=development_selection(x[:900],table.to_dict('records'),leaders=found['leaders'])
    path=directory/'selected_configuration.json'
    if path.exists():raise ValueError('Frozen development decision exists')
    payload=dict(selection=selection,sha256=sha256(json.dumps(selection,sort_keys=True,allow_nan=False).encode()).hexdigest())
    dump(path,payload);print(selection['decision'],flush=True)


def add_commands(commands):
    p=commands.add_parser('long-memory',help='Phase21 H20 offline<=1245; no publication')
    p.add_argument('action',choices=['calibrate','benchmark','analyze','select','diagnostics'])
    p.add_argument('--reports-dir',type=Path,default=ROOT/'reports/long_memory')
    p.add_argument('--pilots',type=int,default=32);p.add_argument('--surrogates',type=int,default=199)
    p.add_argument('--workers',type=int,default=3)


def run(args):
    directory=guard(args.reports_dir)
    if args.action=='calibrate':calibrate(directory,args.pilots);return
    data=load_research_source(args.data);x=canonical_matrix(lotto_matrix(data,cutoff=len(data)))
    if args.action=='benchmark':benchmark(x,directory)
    elif args.action=='analyze':analyze(x,directory,args.surrogates,args.workers)
    elif args.action=='select':select(x,directory)
    elif args.action=='diagnostics':
        from src.analysis.long_memory_diagnostics import diagnostics
        diagnostics(x,directory)
