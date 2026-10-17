"""Phase 11 local-only research orchestration. Never fetches any draw."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.analysis.recurrence import (EmbeddingConfig,observations,embed,fit_scaler,
    distances,eligible,recurrence_matrix,rqa,successor_diagnostic)
from src.analysis.recurrence_search import complete_search,null_search,compare_maxima,SEARCH_SPACE
from src.analysis.spatiotemporal import lotto_matrix,iid_surrogate,constrained_surrogate
from src.backtest.recurrence import (development_search,configuration_hash,load_selection,
    evaluate,paired_report,correlation_report,factories)

ROOT=Path(__file__).resolve().parents[1]


def load_research_source(path):
    # Refuse an unknown suffix by byte length BEFORE CSV parses a future row.
    from src.prospective_experiment import strict_source
    return strict_source(path)[0]


def dump(path,payload):
    Path(path).write_text(json.dumps(payload,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')


def guard(directory):
    directory=Path(directory).resolve()
    allowed=(ROOT/'reports/recurrence').resolve()
    if not directory.is_relative_to(allowed): raise ValueError('Phase 11 output must stay under reports/recurrence')
    directory.mkdir(parents=True,exist_ok=True)
    return directory


def benchmark(x,directory):
    times=[]
    def progress(row):
        now=perf_counter(); times.append(now-progress.last);progress.last=now
        print(f"Benchmark {row['null_model']} {row['replicate']+1}/2: {times[-1]:.2f}s",flush=True)
    progress.last=perf_counter()
    null_search(x[:900],replicates=2,seed=110000,progress=progress)
    report=dict(benchmark_replicates_per_null=2,seconds=times,
        estimated_199_each_seconds=float(np.mean(times)*398),
        chosen_replicates_per_null=199,structural_endpoints=[661,899],
        staging='Fixed contiguous development interval, all 180 embeddings, both constructions; no result-dependent reduction')
    dump(directory/'benchmark.json',report);print(json.dumps(report),flush=True)


def analyze(x,directory,replicates,workers=4):
    if any((directory/name).exists() for name in ('null_progress.jsonl','real_search.csv','real_maxima.json')):
        raise ValueError('Existing null run; use a new report subdirectory to preserve evidence')
    began=perf_counter();dev=x[:900]
    real=complete_search(dev)
    pd.DataFrame(real.pop('rows')).to_csv(directory/'real_search.csv',index=False)
    dump(directory/'real_maxima.json',real)
    log=directory/'null_progress.jsonl'
    if log.exists(): raise ValueError('Existing null run; use a new report subdirectory to avoid overwriting evidence')
    with log.open('x',encoding='utf-8') as stream:
        def progress(row):
            stream.write(json.dumps(row)+'\n');stream.flush()
            print(f"{row['null_model']} {row['replicate']+1}/{replicates}, elapsed {perf_counter()-began:.1f}s",flush=True)
        rows=null_search(dev,replicates=replicates,progress=progress,workers=workers)
    pd.DataFrame(rows).to_csv(directory/'null_maxima.csv',index=False)
    pd.DataFrame(compare_maxima(real,rows)).to_csv(directory/'global_null_comparison.csv',index=False)
    dump(directory/'analysis_metadata.json',dict(research_cutoff=1245,structure_history_cutoff=900,
        structural_endpoints=[661,899],scale_end=400,replicates_per_null=replicates,seed=110042,
        input_matrix_hash=sha256(x.tobytes()).hexdigest(),development_matrix_hash=sha256(dev.tobytes()).hexdigest(),
        search_space=SEARCH_SPACE,workers=workers,runtime_seconds=perf_counter()-began,draw1246_used=False))


def select(x,directory):
    path=directory/'selected_configuration.json'
    if path.exists(): raise ValueError('Development configuration already frozen')
    began=perf_counter()
    s,table,stability=development_search(x[:900],progress=lambda k:print('Development '+k,flush=True))
    # Structural construction selection uses development data only and is frozen before evaluation.
    real=complete_search(x[:900]);s['structural_selection']=real['leaders']['det']
    with path.open('x',encoding='utf-8') as stream:
        json.dump(dict(selection=s,sha256=configuration_hash(s)),stream,indent=2)
    table.to_csv(directory/'development_candidates.csv',index=False)
    stability.to_csv(directory/'development_stability.csv',index=False)
    dump(directory/'selection_runtime.json',dict(seconds=perf_counter()-began))


def summarize(rows):
    output=[]
    ranges=[('all',901,1245),('start1001',1001,1245),('start1101',1101,1245),
            ('early',901,1015),('middle',1016,1130),('recent',1131,1245)]
    for era,start,end in ranges:
        for model,g in rows[rows.target_draw.between(start,end)].groupby('model'):
            output.append(dict(model=model,era=era,targets=len(g),avg_hits=float(g.hits.mean()),
                **{k:float(g[k].mean()) for k in ('recall_6','recall_10','recall_15','mean_winning_rank')},
                **{f'hits_{k}':int((g.hits==k).sum()) for k in range(7)},
                **{f'top{k}_{threshold}plus':int((g[f'pool_{k}']>=threshold).sum())
                    for k in (6,8,10,12,15) for threshold in (5,6)}))
    return pd.DataFrame(output)


def compare(data,directory,cadence):
    s=load_selection(directory/'selected_configuration.json')
    before=(directory/'selected_configuration.json').read_bytes();began=perf_counter()
    rows=evaluate(data,s,cadence=cadence,progress=lambda text:print(text,flush=True))
    out=directory/f'walk_forward_{cadence}';out.mkdir(exist_ok=True)
    rows.to_csv(out/'predictions.csv',index=False)
    summarize(rows).to_csv(out/'summary.csv',index=False)
    paired_report(rows,block=26 if cadence==26 else 13).to_csv(out/'paired.csv',index=False)
    correlation_report(rows).to_csv(out/'gap_correlations.csv',index=False)
    if before!=(directory/'selected_configuration.json').read_bytes(): raise RuntimeError('Selection changed during evaluation')
    dump(out/'protocol.json',dict(start=901,end=1245,cadence=cadence,bootstrap_replicates=2000,
        bootstrap_block=26 if cadence==26 else 13,selection_hash=configuration_hash(s),
        runtime_seconds=perf_counter()-began,draw1246_used=False))


def historical_example(x,selection,row):
    target=int(row.target_draw);cutoff=int(row.training_cutoff)
    model=factories(selection)['RecurrenceAnalogModel']().fit(x[:cutoff],cutoff=cutoff)
    scores=model.score_matrix(x[:target-1],target=target)
    recorded=json.loads(row.scores)
    if not np.allclose(list(scores.values()),[recorded[str(n)] for n in range(1,46)],rtol=1e-12,atol=1e-12):
        raise ValueError('Historical example does not match saved evaluation scores')
    from src.models.predictive import rank_numbers
    ranking=rank_numbers(scores)
    if ranking!=json.loads(row.ranking): raise ValueError('Historical ranking mismatch')
    return dict(target=target,training_cutoff=cutoff,ranking=ranking,
        analogs=model.analogs(x[:target-1],target=target))


def plots(x,directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=directory/'plots';out.mkdir(exist_ok=True)
    s=load_selection(directory/'selected_configuration.json')
    choice=s['structural_selection'];c=EmbeddingConfig(**choice['config']);construction=choice['construction']
    def geometry(history,start,end):
        o=observations(history,c);scaler=fit_scaler(o,400) if c.metric=='euclidean' else None
        e,ends=embed(o,c,scaler);keep=(ends>=start)&(ends<=end);e,ends=e[keep],ends[keep]
        d=distances(e,e,c.metric);v=eligible(ends,c);r=recurrence_matrix(d,v,construction)
        return ends,d,v,r
    def save(name):
        plt.tight_layout();plt.savefig(out/name,dpi=150);plt.close()
    for label,history in [('real',x[:900]),('iid',iid_surrogate(900,seed=110043)),
            ('fixed_margin',constrained_surrogate(x[:900],seed=110044))]:
        ends,d,v,r=geometry(history,661,899)
        plt.figure(figsize=(6,5));plt.imshow(r,origin='lower',extent=[661,899,661,899],cmap='binary',interpolation='nearest')
        plt.title(f'{label}: {c.key}, {construction}');plt.xlabel('State endpoint');plt.ylabel('State endpoint')
        save(f'{label}_recurrence.png')
    ends,d,v,r=geometry(x[:900],661,899)
    diag=successor_diagnostic(x[:900],ends,d,v,details=True)
    dump(directory/'selected_successor_diagnostic.json',diag)
    dec=pd.DataFrame(diag['deciles']);dec.to_csv(directory/'successor_deciles.csv',index=False)
    plt.figure();plt.plot(dec.decile,dec.overlap,'o-');plt.axhline(diag['ordinary_overlap'],color='grey',linestyle='--',label='Ordinary pairs')
    plt.axhline(.8,color='black',linestyle=':',label='IID expectation');plt.xlabel('Distance decile (near to far)');plt.ylabel('Successor overlap');plt.legend();save('state_distance_successor.png')
    null=pd.read_csv(directory/'null_maxima.csv');real=json.loads((directory/'real_maxima.json').read_text())
    fig,axes=plt.subplots(1,5,figsize=(16,3))
    for ax,family in zip(axes,real['maxima']):
        ax.hist([null[null.null_model==k][family] for k in ('iid','fixed_margins')],label=['IID','Fixed'],alpha=.7)
        ax.axvline(real['maxima'][family],color='red');ax.set_title(family)
    axes[0].legend();save('rqa_real_null.png')
    rolling=[]
    for end in range(639,1245,26):
        for label,history in [('real',x),('iid',iid_surrogate(len(x),seed=110045)),
                ('fixed_margin',None)]:
            # One comparable fixed surrogate across all windows, initialized below.
            if label=='fixed_margin':
                if 'fixed' not in locals(): fixed=constrained_surrogate(x,seed=110046)
                history=fixed
            ends,d,v,r=geometry(history,end-238,end)
            rolling.append(dict(end=end,history=label,**rqa(r,v)))
    roll=pd.DataFrame(rolling);roll.to_csv(directory/'rolling_rqa.csv',index=False)
    fig,axes=plt.subplots(2,2,figsize=(11,7))
    for ax,metric in zip(axes.flat,['det','lmax','laminarity','recurrence_time_mean']):
        for label,g in roll.groupby('history'): ax.plot(g.end,g[metric],label=label)
        ax.set_title(metric);ax.set_xlabel('Window endpoint')
    axes[0,0].legend();save('rolling_recurrence.png')
    rows=pd.read_csv(directory/'walk_forward_26/predictions.csv');row=rows[(rows.target_draw==1245)&(rows.model=='RecurrenceAnalogModel')].iloc[0]
    example=historical_example(x,s,row);analog=example['analogs']
    dump(directory/'nearest_analog_example.json',example)
    model=factories(s)['RecurrenceAnalogModel']().fit(x[:900],cutoff=900)
    plt.figure(figsize=(9,4));plt.bar([str(a['endpoint']) for a in analog],[a['distance'] for a in analog])
    plt.xlabel('Historical endpoint (successor = endpoint + 1)');plt.ylabel('Distance');plt.title('Historical target 1245');save('nearest_analog_example.png')
    distances_history=[]
    for target in range(901,1246):
        if (target-901)%26==0:model.fit(x[:target-1],cutoff=target-1)
        a=model.analogs(x[:target-1],target=target)[0]
        distances_history.append(dict(target=target,endpoint=a['endpoint'],distance=a['distance']))
    frame=pd.DataFrame(distances_history);frame.to_csv(directory/'nearest_distance_history.csv',index=False)
    plt.figure(figsize=(10,3));plt.plot(frame.target,frame.distance);plt.xlabel('Target draw');plt.ylabel('Nearest distance');save('nearest_distance_history.png')
    rows=pd.read_csv(directory/'walk_forward_26/predictions.csv');row=rows[(rows.target_draw==1245)&(rows.model=='RecurrenceAnalogModel')].iloc[0]
    scores=json.loads(row.scores);ranking=json.loads(row.ranking)
    plt.figure(figsize=(11,4));plt.bar(range(45),[scores[str(n)] for n in ranking]);plt.xticks(range(45),ranking,fontsize=7)
    plt.xlabel('Numbers in predicted rank order');plt.ylabel('Successor score');plt.title('Historical target 1245');save('ranking_example.png')


def add_commands(commands):
    p=commands.add_parser('recurrence',help='Phase 11 H9: local research through draw 1245 only')
    p.add_argument('action',choices=['benchmark','analyze','select','compare','plots','prepare-freeze'])
    p.add_argument('--reports-dir',type=Path,default=ROOT/'reports/recurrence')
    p.add_argument('--surrogates',type=int,default=199)
    p.add_argument('--cadence',type=int,choices=[13,26],default=26)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--archive',type=Path,default=ROOT/'reports/prospective')
    p.add_argument('--protected-inventory',type=Path)


def run(args):
    directory=guard(args.reports_dir)
    if args.action=='prepare-freeze':
        from src.phase11_freeze import prepare_freeze
        protected=json.loads(args.protected_inventory.read_text()) if args.protected_inventory else None
        print(json.dumps(prepare_freeze(directory/'selected_configuration.json',args.archive,protected=protected),indent=2))
        return
    data=load_research_source(args.data)
    x=lotto_matrix(data,cutoff=len(data))
    if len(x)!=1245: raise ValueError('Canonical Phase 11 run requires exact draws 1..1245')
    if args.action=='benchmark': benchmark(x,directory)
    elif args.action=='analyze': analyze(x,directory,args.surrogates,args.workers)
    elif args.action=='select': select(x,directory)
    elif args.action=='compare': compare(data,directory,args.cadence)
    elif args.action=='plots': plots(x,directory)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,default=ROOT/'data/raw/lotto_history.csv')
    commands=p.add_subparsers(dest='command',required=True);add_commands(commands)
    run(p.parse_args())
