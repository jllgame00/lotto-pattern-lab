"""Offline Phase16 H14; no collection, prediction or publication command."""
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.analysis.complexity_search import (metric_vector,fit_calibration,complete_search,null_search,compare_maxima,standardize)
from src.analysis.complexity_encoding import representations
from src.analysis.spatiotemporal import lotto_matrix
from src.recurrence_cli import load_research_source,dump

ROOT=Path(__file__).resolve().parents[1]


def guard(directory):
    directory=Path(directory).resolve();allowed=(ROOT/'reports/complexity').resolve()
    if not directory.is_relative_to(allowed):raise ValueError('H14 output must stay under reports/complexity')
    directory.mkdir(parents=True,exist_ok=True);return directory


def load_calibration(directory,n):
    p=directory/f'calibration_{n}.npz';j=json.loads((directory/f'calibration_{n}.json').read_text())
    if sha256(p.read_bytes()).hexdigest()!=j.pop('npz_sha256'):raise ValueError('Frozen calibration integrity mismatch')
    with np.load(p) as arrays:j.update({k:arrays[k] for k in arrays.files})
    return j


def calibrate(directory,pilots):
    for n in (1245,900):
        if (directory/f'calibration_{n}.json').exists():load_calibration(directory,n);continue
        began=perf_counter();c=fit_calibration(n,replicates=pilots,progress=lambda m:print(m,flush=True))
        arrays={k:c.pop(k) for k in ('mean','std','eligible','finite_count','pilot_values')}
        p=directory/f'calibration_{n}.npz';np.savez_compressed(p,**arrays)
        dump(directory/f'calibration_{n}.json',dict(c,npz_sha256=sha256(p.read_bytes()).hexdigest(),runtime_seconds=perf_counter()-began))


def benchmark(x,directory):
    calibrations={n:load_calibration(directory,n) for n in (1245,900)};times=[]
    def progress(row):
        now=perf_counter();times.append(now-progress.last);progress.last=now
        print(f"Benchmark {row['null_model']} {row['replicate']+1}/2: {times[-1]:.3f}s",flush=True)
    progress.last=perf_counter();null_search(x,calibrations,replicates=2,seed=160000,progress=progress)
    dump(directory/'benchmark.json',dict(seconds=times,estimated_199_each_three_nulls_seconds=float(np.mean(times)*597),
        chosen_replicates=199,scopes=[1245,900],inner_permutations=3,full_search=True))


def _progress_record(row):
    return {k:({kk:vv for kk,vv in v.items() if kk!='raw_values'} if k in ('full','development') else v) for k,v in row.items()}


def analyze(x,directory,replicates,workers):
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive counts required')
    if any((directory/p).exists() for p in ('real_summary.json','null_progress.jsonl')):raise ValueError('Evidence exists; use a new reports subdirectory')
    calibrations={n:load_calibration(directory,n) for n in (1245,900)};real={};began=perf_counter()
    for scope,n in (('full',1245),('development',900)):
        raw=metric_vector(x[:n]);c=calibrations[n];real[scope]=complete_search(raw,c)
        rows=pd.DataFrame(raw['rows']);rows['z']=standardize(raw,c);rows.to_csv(directory/f'{scope}_metrics.csv',index=False)
        np.savez_compressed(directory/f'{scope}_raw.npz',values=raw['values'])
    dump(directory/'real_summary.json',real);np.save(directory/'binary_series.npy',x)
    reps=representations(x);np.savez_compressed(directory/'representations.npz',**{name:r['symbols'] for name,r in reps.items()})
    dump(directory/'encoding_inventory.json',{name:{k:v for k,v in r.items() if k not in ('symbols','data')}|dict(
        raw_bytes=len(r['data']),sha256=sha256(r['data']).hexdigest()) for name,r in reps.items()})
    with (directory/'null_progress.jsonl').open('x',encoding='utf-8') as stream:
        def progress(row):
            for scope in real:
                if row[scope]['space']!=real[scope]['space']:raise RuntimeError('Complete-search parity failure')
            stream.write(json.dumps(_progress_record(row))+'\n');stream.flush()
            if (row['replicate']+1)%10==0:print(f"{row['null_model']} {row['replicate']+1}/{replicates}: {perf_counter()-began:.1f}s",flush=True)
        rows=null_search(x,calibrations,replicates=replicates,workers=workers,progress=progress)
    flat=[];comparisons=[]
    for scope in real:
        np.savez_compressed(directory/f'null_metrics_{scope}.npz',values=np.array([r[scope]['raw_values'] for r in rows]))
        flat.extend(dict(scope=scope,cutoff=real[scope]['draws'],null_model=r['null_model'],replicate=r['replicate'],**r[scope]['maxima']) for r in rows)
        comparisons.extend(compare_maxima(real[scope],rows,scope=scope))
    pd.DataFrame(flat).to_csv(directory/'null_maxima.csv',index=False)
    pd.DataFrame(comparisons).to_csv(directory/'global_null_comparison.csv',index=False)
    dump(directory/'analysis_metadata.json',dict(research_cutoff=1245,development_cutoff=900,seed=160042,
        pilots_per_scope=calibrations[1245]['replicates'],replicates_per_null=replicates,workers=workers,
        runtime_seconds=perf_counter()-began,draw1246_used=False,publication_executed=False))


def _configuration_hash(c):return sha256(json.dumps(c,sort_keys=True,allow_nan=False).encode()).hexdigest()


def regimes(x,directory):
    from src.analysis.complexity_regimes import choose_development,regime_diagnostic,development_gate
    path=directory/'selected_configuration.json'
    if path.exists():raise ValueError('Development decision already frozen')
    c=load_calibration(directory,900)
    with np.load(directory/'development_raw.npz') as data:values=data['values']
    raw=dict(draws=900,keys=c['keys'],families=c['families'],metadata=c['metadata'],values=values)
    choice=choose_development(raw,standardize(raw,c));spec=dict(choice['spec'])
    dev=regime_diagnostic(x[:900],spec);comparison=pd.read_csv(directory/'global_null_comparison.csv')
    gate=development_gate(comparison[comparison.scope=='development'],dev,research_cutoff=900)
    gate['halves_means']={k:(v if np.isfinite(v) else None) for k,v in gate['halves_means'].items()}
    selection=dict(version='phase16-descriptive-v1',research_cutoff=1245,development_end=900,later_start=901,
        spec=spec,selected_key=choice['selected_key'],z=choice['z'],decision=gate,
        development_matrix_hash=sha256(x[:900].tobytes()).hexdigest(),draw1246_used=False,
        predictive_model_created=False,prospective_capability_created=False,
        prospective_status='PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION')
    with path.open('x',encoding='utf-8') as stream:json.dump(dict(selection=selection,sha256=_configuration_hash(selection)),stream,indent=2)
    dev.to_csv(directory/'development_regimes.csv',index=False)
    # The frozen specification precedes all later regime/outcome diagnostics.
    full=regime_diagnostic(x,spec);full.to_csv(directory/'regimes.csv',index=False)
    full.assign(era=np.where(full.target_draw<=900,'development','later')).groupby(['era','state']).agg(
        samples=('overlap','size'),mean_overlap=('overlap','mean'),own_expected=('own_expected_overlap','mean'),
        excess=('excess','mean'),next_sum=('next_sum','mean'),next_range=('next_range','mean')).to_csv(directory/'regime_summary.csv')
    print(json.dumps(gate,indent=2),flush=True)
    if gate['model_justified']:print('DEVELOPMENT_GATE_PASSED: predictive implementation still required',flush=True)


def add_commands(commands):
    p=commands.add_parser('complexity',help='Phase16 H14 offline research<=1245; no publication')
    p.add_argument('action',choices=['calibrate','benchmark','analyze','regimes','plots'])
    p.add_argument('--reports-dir',type=Path,default=ROOT/'reports/complexity')
    p.add_argument('--pilots',type=int,default=32);p.add_argument('--surrogates',type=int,default=199);p.add_argument('--workers',type=int,default=4)


def run(args):
    directory=guard(args.reports_dir)
    if args.action=='calibrate':calibrate(directory,args.pilots);return
    data=load_research_source(args.data);x=lotto_matrix(data,cutoff=len(data))
    if len(x)!=1245:raise ValueError('Canonical H14 requires exact1..1245')
    if args.action=='benchmark':benchmark(x,directory)
    elif args.action=='analyze':analyze(x,directory,args.surrogates,args.workers)
    elif args.action=='regimes':regimes(x,directory)
    elif args.action=='plots':
        from src.analysis.complexity_plots import plots
        plots(x,directory)
