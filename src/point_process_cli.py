"""H19 offline research: sealed history, complete searches, causal evaluation."""
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.analysis.recurrence import research_matrix
from src.analysis.point_process_search import (FAMILIES,metric_vector,fit_calibration,standardize,
    complete_search,null_search,compare_maxima)
from src.analysis.spatiotemporal import lotto_matrix
from src.recurrence_cli import load_research_source,dump,summarize

ROOT=Path(__file__).resolve().parents[1]


def guard(directory):
    directory=Path(directory).resolve();allowed=(ROOT/'reports/point_process').resolve()
    if not directory.is_relative_to(allowed):raise ValueError('H19 output must stay under reports/point_process')
    directory.mkdir(parents=True,exist_ok=True);return directory


def load_calibration(directory,n):
    path=directory/f'calibration_{n}.npz';meta=json.loads((directory/f'calibration_{n}.json').read_text())
    if sha256(path.read_bytes()).hexdigest()!=meta.pop('npz_sha256'):raise ValueError('Frozen calibration integrity mismatch')
    with np.load(path) as data:meta.update({k:data[k] for k in data.files})
    if meta['draws']!=n:raise ValueError('Calibration cutoff mismatch')
    return meta


def calibrate(directory,pilots):
    for n in (1245,900):
        if (directory/f'calibration_{n}.json').exists():
            existing=load_calibration(directory,n)
            if existing['replicates']!=pilots or existing['seed']!=201001:raise ValueError('Existing calibration protocol differs')
            continue
        if (directory/f'calibration_{n}.npz').exists():raise ValueError('Calibration evidence already exists')
        began=perf_counter();c=fit_calibration(n,replicates=pilots,progress=lambda m:print(m,flush=True))
        arrays={k:c.pop(k) for k in ('mean','std','eligible','finite_count','pilot_values')}
        path=directory/f'calibration_{n}.npz';np.savez_compressed(path,**arrays)
        dump(directory/f'calibration_{n}.json',dict(c,npz_sha256=sha256(path.read_bytes()).hexdigest(),runtime_seconds=perf_counter()-began))


def benchmark(x,directory):
    c={n:load_calibration(directory,n) for n in (1245,900)};times=[]
    def progress(row):
        now=perf_counter();times.append(now-progress.last);progress.last=now
        print(f"Benchmark {row['null_model']} {row['replicate']+1}/2: {times[-1]:.3f}s",flush=True)
    progress.last=perf_counter();null_search(x,c,replicates=2,seed=200000,progress=progress)
    dump(directory/'benchmark.json',dict(seconds=times,estimated_serial_199_each_seconds=float(np.mean(times)*398),
        chosen_replicates=199,scopes=[1245,900],complete_search=True))


def analyze(x,directory,replicates,workers):
    x=research_matrix(x)
    if len(x)!=1245:raise ValueError('Canonical H19 requires exact1..1245')
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive counts required')
    outputs=('real_summary.json','null_progress.jsonl','full_metrics.csv','development_metrics.csv','full_raw.npz',
        'development_raw.npz','binary_series.npy','null_metrics_full.npz','null_metrics_development.npz','null_maxima.csv',
        'global_null_comparison.csv','analysis_metadata.json')
    if any((directory/p).exists() for p in outputs):raise ValueError('Evidence exists; choose a new report subdirectory')
    c={n:load_calibration(directory,n) for n in (1245,900)};real={};began=perf_counter()
    for scope,n in [('full',1245),('development',900)]:
        raw=metric_vector(x[:n]);real[scope]=complete_search(raw,c[n])
        table=pd.DataFrame(raw['rows']);table['z']=standardize(raw,c[n]);table.to_csv(directory/f'{scope}_metrics.csv',index=False)
        np.savez_compressed(directory/f'{scope}_raw.npz',values=raw['values'])
    dump(directory/'real_summary.json',real);np.save(directory/'binary_series.npy',x)
    with (directory/'null_progress.jsonl').open('x',encoding='utf-8') as stream:
        def progress(row):
            for scope in real:
                if row[scope]['space']!=real[scope]['space']:raise RuntimeError('Complete-search parity mismatch')
            record={k:({a:b for a,b in v.items() if a!='raw_values'} if k in real else v) for k,v in row.items()}
            stream.write(json.dumps(record)+'\n');stream.flush()
            if (row['replicate']+1)%10==0:print(f"{row['null_model']} {row['replicate']+1}/{replicates}: {perf_counter()-began:.1f}s",flush=True)
        rows=null_search(x,c,replicates=replicates,workers=workers,progress=progress)
    flat=[];comparison=[]
    for scope in real:
        np.savez_compressed(directory/f'null_metrics_{scope}.npz',values=np.array([r[scope]['raw_values'] for r in rows]))
        flat.extend(dict(scope=scope,null_model=r['null_model'],replicate=r['replicate'],**r[scope]['maxima']) for r in rows)
        comparison.extend(compare_maxima(real[scope],rows,scope=scope))
    pd.DataFrame(flat).to_csv(directory/'null_maxima.csv',index=False);pd.DataFrame(comparison).to_csv(directory/'global_null_comparison.csv',index=False)
    dump(directory/'analysis_metadata.json',dict(research_cutoff=1245,development_cutoff=900,seed=200042,
        pilots_per_scope=c[1245]['replicates'],replicates_per_null=replicates,workers=workers,
        runtime_seconds=perf_counter()-began,draw1246_used=False,publication_executed=False))


def validate_development(x,directory):
    meta=json.loads((directory/'analysis_metadata.json').read_text())
    if any(meta.get(k)!=v for k,v in dict(replicates_per_null=199,pilots_per_scope=32,research_cutoff=1245,development_cutoff=900).items()):
        raise ValueError('Canonical32 pilots and199 complete nulls per family required')
    for n in (1245,900):
        calibration=load_calibration(directory,n)
        if calibration['replicates']!=32 or calibration['seed']!=201001:raise ValueError('Both calibration scopes require32 independent declared pilots')
    c=load_calibration(directory,900);real=json.loads((directory/'real_summary.json').read_text())['development']
    if real['representation_hash']!=sha256(x[:900].tobytes()).hexdigest():raise ValueError('Development source mismatch')
    observed=np.load(directory/'development_raw.npz')['values'];null=np.load(directory/'null_metrics_development.npz')['values']
    if observed.shape!=(len(c['keys']),) or null.shape!=(398,len(c['keys'])):raise ValueError('Incomplete development search')
    z=standardize(dict(draws=900,keys=c['keys'],values=observed),c)
    nz=np.divide(null-c['mean'],c['std'],out=np.full_like(null,np.nan),where=c['eligible'][None,:])
    comparison=pd.read_csv(directory/'global_null_comparison.csv');comparison=comparison[comparison.scope=='development']
    if len(comparison)!=12:raise ValueError('Six families and both nulls required')
    for kind,start in [('iid',0),('fixed_margins',199)]:
        for family in FAMILIES:
            mask=np.array(c['families'])==family;maximum=float(np.nanmax(z[mask]));generated=np.nanmax(nz[start:start+199,mask],axis=1)
            p=(1+int((generated>=maximum).sum()))/200;row=comparison[(comparison.null_model==kind)&(comparison.family==family)]
            if len(row)!=1 or not np.isclose(row.iloc[0].global_p,p) or not np.isclose(row.iloc[0].adjusted_p,min(1,6*p)):
                raise ValueError('Development own-global-max calibration mismatch')
    return comparison


def select(x,directory):
    validate_development(x,directory)
    from src.backtest.point_process import development_search,configuration_hash
    path=directory/'selected_configuration.json'
    if path.exists() or (directory/'development_predictions.csv').exists():raise ValueError('Frozen development evidence exists')
    began=perf_counter();selection,table=development_search(x[:900],progress=lambda m:print(m,flush=True))
    with path.open('x',encoding='utf-8') as stream:json.dump(dict(selection=selection,sha256=configuration_hash(selection)),stream,indent=2,allow_nan=False)
    table.to_csv(directory/'development_predictions.csv',index=False)
    table.groupby(['candidate','model'],sort=False).agg(mean_hits=('hits','mean'),mean_logloss=('logloss','mean'),
        targets=('hits','size')).to_csv(directory/'development_summary.csv')
    dump(directory/'selection_runtime.json',dict(seconds=perf_counter()-began,publication_executed=False))


def compare(data,directory,cadence):
    from src.backtest.point_process import load_selection,configuration_hash,evaluate,paired_report,correlation_report,conditional_report
    path=directory/'selected_configuration.json';before=path.read_bytes();selection=load_selection(path);out=directory/f'walk_forward_{cadence}'
    if out.exists():raise ValueError('Walk-forward evidence exists')
    began=perf_counter();rows=evaluate(data,selection,cadence=cadence,progress=lambda m:print(m,flush=True));out.mkdir()
    rows.to_csv(out/'predictions.csv',index=False);summarize(rows).to_csv(out/'summary.csv',index=False)
    paired_report(rows,selection,block=cadence).to_csv(out/'paired.csv',index=False)
    paired_report(rows,selection,block=52).to_csv(out/'paired_block52.csv',index=False)
    correlation_report(rows,selection,graph_path=ROOT/f'reports/graph_hypergraph/walk_forward_{cadence}/predictions.csv',
        shape_path=ROOT/f'reports/transformed_space/walk_forward_{cadence}/predictions.csv',
        mirror_path=ROOT/f'reports/symmetry/walk_forward_{cadence}/predictions.csv').to_csv(out/'rank_diversity.csv',index=False)
    losses,conditional=conditional_report(rows,selection,block=cadence)
    losses.to_csv(out/'conditional_losses.csv',index=False);conditional.to_csv(out/'conditional_comparison.csv',index=False)
    _,conditional52=conditional_report(rows,selection,block=52);conditional52.to_csv(out/'conditional_block52.csv',index=False)
    if path.read_bytes()!=before:raise RuntimeError('Frozen selection changed')
    dump(out/'protocol.json',dict(start=901,end=1245,cadence=cadence,point_process_refit='outer_cadence_frozen_edges_coefficients',
        bootstrap_replicates=2000,bootstrap_block=cadence,sensitivity_block=52,old_models_refitted=False,
        selection_hash=configuration_hash(selection),runtime_seconds=perf_counter()-began,draw1246_used=False))


def add_commands(commands):
    p=commands.add_parser('point-process',help='Phase20 H19 offline<=1245; no publication')
    p.add_argument('action',choices=['calibrate','benchmark','analyze','select','compare','diagnostics','plots'])
    p.add_argument('--reports-dir',type=Path,default=ROOT/'reports/point_process');p.add_argument('--pilots',type=int,default=32)
    p.add_argument('--surrogates',type=int,default=199);p.add_argument('--workers',type=int,default=4)
    p.add_argument('--cadence',type=int,choices=[13,26],default=26)


def run(args):
    directory=guard(args.reports_dir)
    if args.action=='calibrate':calibrate(directory,args.pilots);return
    data=load_research_source(args.data);x=lotto_matrix(data,cutoff=len(data))
    if len(x)!=1245:raise ValueError('Canonical H19 requires exact1..1245')
    if args.action=='benchmark':benchmark(x,directory)
    elif args.action=='analyze':analyze(x,directory,args.surrogates,args.workers)
    elif args.action=='select':select(x,directory)
    elif args.action=='compare':compare(data,directory,args.cadence)
    elif args.action in ('diagnostics','plots'):
        from src.analysis.point_process_diagnostics import diagnostics,plots
        (diagnostics if args.action=='diagnostics' else plots)(x,directory)




