"""Offline Phase12 H10 orchestration. No data collection or publication paths."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.analysis.multiscale import complete_search,null_search,compare_maxima
from src.analysis.spatiotemporal import lotto_matrix
from src.backtest.multiscale import (development_search,configuration_hash,load_selection,
    evaluate,paired_report,correlation_report)
from src.recurrence_cli import load_research_source,dump,summarize

ROOT=Path(__file__).resolve().parents[1]


def guard(directory):
    directory=Path(directory).resolve();allowed=(ROOT/'reports/multiscale').resolve()
    if not directory.is_relative_to(allowed):raise ValueError('Phase12 output must stay under reports/multiscale')
    directory.mkdir(parents=True,exist_ok=True)
    return directory


def benchmark(x,directory):
    times=[]
    def progress(row):
        now=perf_counter();times.append(now-progress.last);progress.last=now
        print(f"Benchmark {row['null_model']} {row['replicate']+1}/2: {times[-1]:.3f}s",flush=True)
    progress.last=perf_counter();null_search(x,replicates=2,seed=120000,progress=progress)
    report=dict(seconds=times,estimated_199_each_seconds=float(np.mean(times)*398),
        chosen_replicates_per_null=199,staging='Full1245 CWT; five fixed416 SSA windows, all53 series, all3 L, top8 components; identical to every surrogate')
    dump(directory/'benchmark.json',report);print(json.dumps(report),flush=True)


def analyze(x,directory,replicates,workers):
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:
        raise ValueError('Positive replicate and worker counts required before analysis')
    if any((directory/p).exists() for p in ('real_maxima.json','null_progress.jsonl')):
        raise ValueError('Existing analysis evidence; choose new reports subdirectory')
    began=perf_counter();real=complete_search(x)
    pd.DataFrame(real.pop('wavelet_rows')).to_csv(directory/'wavelet_search.csv',index=False)
    dump(directory/'ssa_search.json',real.pop('ssa_rows'))
    pd.DataFrame(real.pop('regions'),columns=['series','name','start','end','period','score',
        'duration','scale_stability','max_power','cell_count']).to_csv(directory/'localized_regions.csv',index=False)
    dump(directory/'real_maxima.json',real)
    from src.analysis.multiscale import representations
    from src.analysis.wavelet import morlet_transform
    names,y=representations(x,cutoff=len(x));np.save(directory/'representations.npy',y)
    t=morlet_transform(y)
    np.savez_compressed(directory/'wavelet_transform.npz',power=t['power'],coefficients=t['coefficients'],
        valid=t['valid'],periods=t['periods'],dominant_period_by_time=t['dominant_period_by_time'],global_power=t['global_power'])
    with (directory/'null_progress.jsonl').open('x',encoding='utf-8') as stream:
        def progress(row):
            if row['space']!=real['space']:raise RuntimeError('Complete search parity failure')
            stream.write(json.dumps(row)+'\n');stream.flush()
            if (row['replicate']+1)%10==0:print(f"{row['null_model']} {row['replicate']+1}/{replicates}: {perf_counter()-began:.1f}s",flush=True)
        rows=null_search(x,replicates=replicates,workers=workers,progress=progress)
    pd.DataFrame(rows).to_csv(directory/'null_maxima.csv',index=False)
    pd.DataFrame(compare_maxima(real,rows)).to_csv(directory/'global_null_comparison.csv',index=False)
    dump(directory/'analysis_metadata.json',dict(research_cutoff=1245,replicates_per_null=replicates,workers=workers,
        seed=120042,search_space=real['space'],matrix_hash=sha256(x.tobytes()).hexdigest(),
        runtime_seconds=perf_counter()-began,draw1246_used=False))


def select(x,directory):
    path=directory/'selected_configuration.json'
    if path.exists():raise ValueError('Development selection already frozen')
    began=perf_counter();s,table=development_search(x[:900],progress=lambda m:print(m,flush=True))
    with path.open('x',encoding='utf-8') as stream:json.dump(dict(selection=s,sha256=configuration_hash(s)),stream,indent=2)
    table.to_csv(directory/'development_predictions.csv',index=False)
    table.groupby(['candidate','model'],sort=False).hits.agg(['mean','count']).to_csv(directory/'development_summary.csv')
    dump(directory/'selection_runtime.json',dict(seconds=perf_counter()-began))


def compare(data,directory,cadence,sensitivity):
    path=directory/'selected_configuration.json';before=path.read_bytes();s=load_selection(path);began=perf_counter()
    rows=evaluate(data,s,cadence=cadence,sensitivity=sensitivity,progress=lambda m:print(m,flush=True))
    out=directory/f'walk_forward_{cadence}';out.mkdir(exist_ok=True)
    rows.to_csv(out/'predictions.csv',index=False);summarize(rows).to_csv(out/'summary.csv',index=False)
    paired_report(rows,block=cadence).to_csv(out/'paired.csv',index=False)
    correlation_report(rows,recurrence_path=ROOT/f'reports/recurrence/walk_forward_{cadence}/predictions.csv').to_csv(out/'rank_diversity.csv',index=False)
    if before!=path.read_bytes():raise RuntimeError('Selection changed during later evaluation')
    dump(out/'protocol.json',dict(start=901,end=1245,cadence=cadence,multiscale_refit='every target; exact training prefix',
        bootstrap_replicates=2000,bootstrap_block=cadence,selection_hash=configuration_hash(s),
        sensitivity=sensitivity,runtime_seconds=perf_counter()-began,draw1246_used=False))


def add_commands(commands):
    p=commands.add_parser('multiscale',help='Phase12 H10 local research <=1245')
    p.add_argument('action',choices=['benchmark','analyze','select','compare','plots','prepare-freeze'])
    p.add_argument('--reports-dir',type=Path,default=ROOT/'reports/multiscale')
    p.add_argument('--surrogates',type=int,default=199);p.add_argument('--workers',type=int,default=4)
    p.add_argument('--cadence',type=int,choices=[13,26],default=26);p.add_argument('--sensitivity',action='store_true')
    p.add_argument('--archive',type=Path,default=ROOT/'reports/prospective')
    p.add_argument('--protected-inventory',type=Path)


def run(args):
    directory=guard(args.reports_dir)
    if args.action=='prepare-freeze':
        from src.phase12_freeze import prepare_freeze
        protected=json.loads(args.protected_inventory.read_text()) if args.protected_inventory else None
        print(json.dumps(prepare_freeze(directory/'selected_configuration.json',args.archive,protected=protected),indent=2));return
    data=load_research_source(args.data);x=lotto_matrix(data,cutoff=len(data))
    if len(x)!=1245:raise ValueError('Canonical Phase12 requires exact draws1..1245')
    if args.action=='benchmark':benchmark(x,directory)
    elif args.action=='analyze':analyze(x,directory,args.surrogates,args.workers)
    elif args.action=='select':select(x,directory)
    elif args.action=='compare':compare(data,directory,args.cadence,args.sensitivity)
    elif args.action=='plots':
        from src.analysis.multiscale_plots import plots
        plots(x,directory)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,default=ROOT/'data/raw/lotto_history.csv')
    add_commands(p.add_subparsers(dest='command',required=True));run(p.parse_args())
