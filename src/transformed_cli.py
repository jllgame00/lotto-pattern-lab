"""Offline H13 transformed-space orchestration, histories<=1245 only."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.analysis.transformed_search import complete_search,null_search,compare_maxima
from src.analysis.spatiotemporal import lotto_matrix
from src.recurrence_cli import load_research_source,dump,summarize

ROOT=Path(__file__).resolve().parents[1]


def guard(directory):
    p=Path(directory).resolve();allowed=(ROOT/'reports/transformed_space').resolve()
    if not p.is_relative_to(allowed):raise ValueError('H13 outputs must stay under reports/transformed_space')
    p.mkdir(parents=True,exist_ok=True);return p


def benchmark(x,directory):
    times=[]
    def progress(row):
        now=perf_counter();times.append(now-progress.last);progress.last=now
        print(f"Benchmark {row['null_model']} {row['replicate']+1}/2: {times[-1]:.3f}s",flush=True)
    progress.last=perf_counter();null_search(x,replicates=2,progress=progress)
    d=dict(seconds=times,estimated_199_each_seconds=float(np.mean(times)*398),replicates_per_null=199,
        staging='all6moduli,all7lags,all44distances,samecausalshapegrid')
    dump(directory/'benchmark.json',d);print(json.dumps(d),flush=True)


def analyze(x,directory,replicates,workers):
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive counts required')
    if any((directory/p).exists() for p in ('real_maxima.json','null_progress.jsonl')):raise ValueError('Evidence exists; use new reports subdirectory')
    began=perf_counter();real=complete_search(x)
    for field in ('modular_rows','temporal_rows','successor_rows','distance_rows','shape_rows'):
        pd.DataFrame(real.pop(field)).to_csv(directory/(field+'.csv'),index=False)
    np.savez_compressed(directory/'transformed_cache.npz',**real.pop('arrays'));np.save(directory/'binary_series.npy',x)
    dump(directory/'real_maxima.json',real)
    with (directory/'null_progress.jsonl').open('x',encoding='utf-8') as stream:
        def progress(row):
            if row['space']!=real['space']:raise RuntimeError('Complete-search parity failure')
            stream.write(json.dumps(row)+'\n');stream.flush()
            if (row['replicate']+1)%10==0:print(f"{row['null_model']} {row['replicate']+1}/{replicates}: {perf_counter()-began:.1f}s",flush=True)
        rows=null_search(x,replicates=replicates,workers=workers,progress=progress)
    flat=[dict(null_model=r['null_model'],replicate=r['replicate'],seed=r['seed'],**r['maxima']) for r in rows]
    pd.DataFrame(flat).to_csv(directory/'null_maxima.csv',index=False)
    pd.DataFrame(compare_maxima(real,rows)).to_csv(directory/'global_null_comparison.csv',index=False)
    dump(directory/'analysis_metadata.json',dict(research_cutoff=1245,seed=150042,replicates_per_null=replicates,
        workers=workers,search_space=real['space'],matrix_hash=sha256(x.tobytes()).hexdigest(),
        runtime_seconds=perf_counter()-began,draw1246_used=False))


def select(x,directory):
    from src.backtest.transformed_space import development_search,configuration_hash
    p=directory/'selected_configuration.json'
    if p.exists():raise ValueError('Selection already frozen')
    began=perf_counter();s,table=development_search(x[:900],progress=lambda m:print(m,flush=True))
    with p.open('x',encoding='utf-8') as stream:json.dump(dict(selection=s,sha256=configuration_hash(s)),stream,indent=2)
    table.to_csv(directory/'development_predictions.csv',index=False)
    table.groupby(['candidate','model'],sort=False).hits.agg(['mean','count']).to_csv(directory/'development_summary.csv')
    dump(directory/'selection_runtime.json',dict(seconds=perf_counter()-began))


def compare(data,directory,cadence):
    from src.backtest.transformed_space import load_selection,configuration_hash,evaluate,paired_report,correlation_report
    path=directory/'selected_configuration.json';before=path.read_bytes();s=load_selection(path);began=perf_counter()
    rows=evaluate(data,s,cadence=cadence,progress=lambda m:print(m,flush=True));out=directory/f'walk_forward_{cadence}';out.mkdir(exist_ok=True)
    rows.to_csv(out/'predictions.csv',index=False);summarize(rows).to_csv(out/'summary.csv',index=False)
    paired_report(rows,block=cadence).to_csv(out/'paired.csv',index=False)
    paired_report(rows,block=52).to_csv(out/'paired_block52.csv',index=False)
    correlation_report(rows,graph_path=ROOT/f'reports/graph_hypergraph/walk_forward_{cadence}/predictions.csv').to_csv(out/'rank_diversity.csv',index=False)
    if path.read_bytes()!=before:raise RuntimeError('Frozen selection changed')
    dump(out/'protocol.json',dict(start=901,end=1245,cadence=cadence,transformed_refit='everytargettrainingprefix',
        bootstrap_replicates=2000,bootstrap_block=cadence,sensitivity_block=52,references=['RandomModel','GapLogistic'],
        selection_hash=configuration_hash(s),runtime_seconds=perf_counter()-began,draw1246_used=False))


def add_commands(commands):
    p=commands.add_parser('transformed-space',help='Phase15 H13 local research<=1245')
    p.add_argument('action',choices=['benchmark','analyze','select','compare','sensitivity','plots','prepare-freeze'])
    p.add_argument('--reports-dir',type=Path,default=ROOT/'reports/transformed_space')
    p.add_argument('--surrogates',type=int,default=199);p.add_argument('--workers',type=int,default=4)
    p.add_argument('--cadence',type=int,choices=[13,26],default=26)
    p.add_argument('--archive',type=Path,default=ROOT/'reports/prospective');p.add_argument('--protected-inventory',type=Path)


def run(args):
    directory=guard(args.reports_dir)
    if args.action=='prepare-freeze':
        from src.phase15_freeze import prepare_freeze
        protected=json.loads(args.protected_inventory.read_text()) if args.protected_inventory else None
        print(json.dumps(prepare_freeze(directory/'selected_configuration.json',args.archive,protected=protected),indent=2));return
    data=load_research_source(args.data);x=lotto_matrix(data,cutoff=len(data))
    if len(x)!=1245:raise ValueError('Canonical H13 requires exact1..1245')
    if args.action=='benchmark':benchmark(x,directory)
    elif args.action=='analyze':analyze(x,directory,args.surrogates,args.workers)
    elif args.action=='select':select(x,directory)
    elif args.action=='compare':compare(data,directory,args.cadence)
    elif args.action=='sensitivity':
        from src.backtest.transformed_space import load_selection,sensitivity
        p=directory/'selected_configuration.json';before=p.read_bytes()
        sensitivity(x,load_selection(p),progress=lambda m:print(m,flush=True)).to_csv(directory/'later_sensitivity.csv',index=False)
        if p.read_bytes()!=before:raise RuntimeError('Selection changed')
    elif args.action=='plots':
        from src.analysis.transformed_plots import plots
        plots(x,directory)
