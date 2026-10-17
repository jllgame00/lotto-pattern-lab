"""Phase13 H11 local-only orchestration; never fetches or publishes a draw."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.analysis.information import LAGS,HISTORIES
from src.analysis.information_search import complete_search,null_search,compare_maxima,temporal_randomization
from src.analysis.spatiotemporal import lotto_matrix
from src.backtest.information_flow import (development_search,load_selection,configuration_hash,evaluate,
    paired_report,correlation_report,conditional_report,sensitivity)
from src.recurrence_cli import load_research_source,dump,summarize

ROOT=Path(__file__).resolve().parents[1]


def guard(directory):
    directory=Path(directory).resolve();allowed=(ROOT/'reports/information_flow').resolve()
    if not directory.is_relative_to(allowed):raise ValueError('Phase13 output must stay under reports/information_flow')
    directory.mkdir(parents=True,exist_ok=True)
    return directory


def benchmark(x,directory):
    times=[]
    def progress(row):
        now=perf_counter();times.append(now-progress.last);progress.last=now
        print(f"Benchmark {row['null_model']} {row['replicate']+1}/2: {times[-1]:.3f}s",flush=True)
    progress.last=perf_counter();null_search(x,replicates=2,seed=130000,progress=progress)
    report=dict(seconds=times,estimated_199_each_seconds=float(np.mean(times)*398),chosen_replicates_per_null=199,
        staging='All45 series/pairs, all7lags and4 histories, full1245 +3fixederas; same support/own maxima')
    dump(directory/'benchmark.json',report);print(json.dumps(report),flush=True)


def local_bias(directory,mi,te,x):
    began=perf_counter();result=temporal_randomization(x)
    np.savez_compressed(directory/'temporal_source_null.npz',mi_null=result['mi_null'],te_null=result['te_null'])
    configs=[(lag,k,l) for lag in LAGS for k,l in HISTORIES]
    for label,rows,arrays in [('mi',mi,result['mi_null']),('te',te,result['te_null'])]:
        output=[]
        for row in rows:
            c=LAGS.index(row['lag']) if label=='mi' else configs.index((row['lag'],row['k'],row['l']))
            values=arrays[:,c,row['source']-1,row['target']-1];values=values[np.isfinite(values)]
            output.append(dict(**row,temporal_null_replicates=len(values),
                temporal_null_mean=float(values.mean()) if len(values) else None,
                temporal_null_std=float(values.std()) if len(values) else None,
                temporal_null_q95=float(np.quantile(values,.95)) if len(values) else None,
                temporal_bias_subtracted=float(row['value']-values.mean()) if len(values) else None,
                local_unadjusted_p=float((1+(values>=row['value']).sum())/(1+len(values))) if len(values) else None))
        pd.DataFrame(output).to_csv(directory/f'{label}_temporal_bias.csv',index=False)
    dump(directory/'temporal_null_protocol.json',dict(replicates=19,seed=130043,offset_range=[53,len(x)-53],
        source_only_shift=True,target_history_unchanged=True,column_margins_preserved=True,
        valid_lotto_history=False,local_p_is_global_evidence=False,runtime_seconds=perf_counter()-began))


def analyze(x,directory,replicates,workers):
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive counts required before analysis')
    if any((directory/p).exists() for p in ('real_maxima.json','null_progress.jsonl')):raise ValueError('Existing analysis evidence; choose new reports subdirectory')
    began=perf_counter();real=complete_search(x)
    mi=real.pop('mi_rows');te=real.pop('te_rows');arrays=real.pop('arrays')
    pd.DataFrame(mi).to_csv(directory/'mi_search.csv',index=False)
    pd.DataFrame(te).to_csv(directory/'te_search.csv',index=False)
    np.save(directory/'binary_series.npy',x);np.savez_compressed(directory/'information_tables.npz',**arrays)
    dump(directory/'real_maxima.json',real)
    with (directory/'null_progress.jsonl').open('x',encoding='utf-8') as stream:
        def progress(row):
            if row['space']!=real['space']:raise RuntimeError('Complete-search parity failure')
            stream.write(json.dumps(row)+'\n');stream.flush()
            if (row['replicate']+1)%10==0:print(f"{row['null_model']} {row['replicate']+1}/{replicates}: {perf_counter()-began:.1f}s",flush=True)
        rows=null_search(x,replicates=replicates,workers=workers,progress=progress)
    pd.DataFrame(rows).to_csv(directory/'null_maxima.csv',index=False)
    pd.DataFrame(compare_maxima(real,rows)).to_csv(directory/'global_null_comparison.csv',index=False)
    global_seconds=perf_counter()-began
    local_bias(directory,mi,te,x)
    dump(directory/'analysis_metadata.json',dict(research_cutoff=1245,seed=130042,replicates_per_null=replicates,
        workers=workers,search_space=real['space'],eligible_counts=real['eligible_counts'],eras=real['eras'],
        matrix_hash=sha256(x.tobytes()).hexdigest(),global_runtime_seconds=global_seconds,
        total_runtime_seconds=perf_counter()-began,draw1246_used=False))


def select(x,directory):
    path=directory/'selected_configuration.json'
    if path.exists():raise ValueError('Development selection already frozen')
    began=perf_counter();s,table=development_search(x[:900],progress=lambda m:print(m,flush=True))
    with path.open('x',encoding='utf-8') as stream:json.dump(dict(selection=s,sha256=configuration_hash(s)),stream,indent=2)
    table.to_csv(directory/'development_predictions.csv',index=False)
    table.groupby(['candidate','model'],sort=False).hits.agg(['mean','count']).to_csv(directory/'development_summary.csv')
    dump(directory/'selection_runtime.json',dict(seconds=perf_counter()-began))


def compare(data,directory,cadence):
    path=directory/'selected_configuration.json';before=path.read_bytes();s=load_selection(path);began=perf_counter()
    rows=evaluate(data,s,cadence=cadence,progress=lambda m:print(m,flush=True))
    out=directory/f'walk_forward_{cadence}';out.mkdir(exist_ok=True)
    rows.to_csv(out/'predictions.csv',index=False);summarize(rows).to_csv(out/'summary.csv',index=False)
    paired_report(rows,block=cadence).to_csv(out/'paired.csv',index=False)
    correlation_report(rows).to_csv(out/'rank_diversity.csv',index=False)
    losses,uncertainty=conditional_report(rows,block=cadence)
    losses.to_csv(out/'conditional_logloss.csv',index=False);uncertainty.to_csv(out/'conditional_paired.csv',index=False)
    if before!=path.read_bytes():raise RuntimeError('Selection changed during later evaluation')
    dump(out/'protocol.json',dict(start=901,end=1245,cadence=cadence,information_refit='every target; trailing624 training only',
        bootstrap_replicates=2000,bootstrap_block=cadence,selection_hash=configuration_hash(s),
        runtime_seconds=perf_counter()-began,draw1246_used=False))


def add_commands(commands):
    p=commands.add_parser('information-flow',help='Phase13 H11 local research <=1245')
    p.add_argument('action',choices=['benchmark','analyze','select','compare','sensitivity','plots','prepare-freeze'])
    p.add_argument('--reports-dir',type=Path,default=ROOT/'reports/information_flow')
    p.add_argument('--surrogates',type=int,default=199);p.add_argument('--workers',type=int,default=4)
    p.add_argument('--cadence',type=int,choices=[13,26],default=26)
    p.add_argument('--archive',type=Path,default=ROOT/'reports/prospective')
    p.add_argument('--protected-inventory',type=Path)


def run(args):
    directory=guard(args.reports_dir)
    if args.action=='prepare-freeze':
        from src.phase13_freeze import prepare_freeze
        protected=json.loads(args.protected_inventory.read_text()) if args.protected_inventory else None
        print(json.dumps(prepare_freeze(directory/'selected_configuration.json',args.archive,protected=protected),indent=2));return
    data=load_research_source(args.data);x=lotto_matrix(data,cutoff=len(data))
    if len(x)!=1245:raise ValueError('Canonical Phase13 requires exact draws1..1245')
    if args.action=='benchmark':benchmark(x,directory)
    elif args.action=='analyze':analyze(x,directory,args.surrogates,args.workers)
    elif args.action=='select':select(x,directory)
    elif args.action=='compare':compare(data,directory,args.cadence)
    elif args.action=='sensitivity':
        s=load_selection(directory/'selected_configuration.json');before=configuration_hash(s)
        table=sensitivity(x,progress=lambda m:print(m,flush=True));table.to_csv(directory/'later_sensitivity.csv',index=False)
        assert before==configuration_hash(load_selection(directory/'selected_configuration.json'))
    elif args.action=='plots':
        from src.analysis.information_plots import plots
        plots(x,directory)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,default=ROOT/'data/raw/lotto_history.csv')
    add_commands(p.add_subparsers(dest='command',required=True));run(p.parse_args())
