"""Offline Phase10 reports. Prior experiment directories are never outputs."""
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.prospective_experiment import ROOT,strict_source
from src.analysis.spatiotemporal import lotto_matrix,P
from src.analysis.number_space import WINDOWS,METRICS,rolling_counts,smooth
from src.analysis.number_space_search import complete_search,compare_nulls,spacing_reference


def guard_reports(directory):
    path=Path(directory).resolve()
    if path==ROOT or path.is_relative_to(ROOT/'data') or (path.is_relative_to(ROOT/'reports') and not path.is_relative_to(ROOT/'reports/number_space')):
        raise ValueError('Phase10 research outputs require their own reports/number_space directory')


def add_commands(commands):
    p=commands.add_parser('analyze-number-space',help='Bounded range/kernel/spacing search and complete nulls')
    p.add_argument('--surrogates',type=int,default=199);p.add_argument('--reports-dir',type=Path)
    p=commands.add_parser('compare-number-space',help='Development-selected range/neighborhood walk-forward')
    p.add_argument('--cadence',type=int,default=26);p.add_argument('--reports-dir',type=Path)
    p=commands.add_parser('freeze-number-space',help='Independent Phase10 prospective snapshot; no result access')
    p.add_argument('--reports-dir',type=Path)


def plot_reports(x,result,directory,selected=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    def save(name):plt.tight_layout();plt.savefig(directory/(name+'.png'),dpi=140);plt.close()
    numbers=np.arange(1,46)
    plt.figure(figsize=(11,4));plt.bar(numbers,x.mean(axis=0));plt.axhline(P,color='black',ls='--');plt.xlabel('Number');plt.ylabel('Main appearance rate');plt.title('Long-term density; descriptive only');save('long_term_density')
    for w in WINDOWS:
        a=rolling_counts(x,w)[-1]/w
        plt.figure(figsize=(11,4));plt.bar(numbers,a);plt.axhline(P,color='black',ls='--');plt.xlabel('Number');plt.ylabel('Appearance rate');plt.title(f'Previous {w} draws only; no target outcome');save(f'recent_w{w}')
    plt.figure(figsize=(11,4));a=rolling_counts(x,26)[-1]/26
    plt.plot(numbers,a,label='Own W26');plt.plot(numbers,smooth(a,'triangular2'),label='Smoothed triangular2');plt.plot(numbers,smooth(a,'triangular2',neighbor_only=True),label='Neighbor-only');plt.legend();plt.xlabel('Number');plt.title('Finite-axis signals; no wrap');save('raw_vs_smoothed')
    r=result['density'];data=r[(r.window==26)&(r.width==5)].pivot(index='start_number',columns='end_draw',values='raw_z')
    plt.figure(figsize=(12,5));plt.imshow(data,aspect='auto',origin='lower',extent=[26,len(x),1,41],cmap='coolwarm');plt.colorbar(label='Raw range z (not significance)');plt.xlabel('Last included draw');plt.ylabel('Width5 range start');plt.title('W26 overlapping range activity');save('range_density_history')
    z=result['zones'];z=z[(z.window==26)&(z.width==5)]
    plt.figure(figsize=(12,4));plt.plot(z.end_draw,z.center);plt.xlabel('Last included draw');plt.ylabel('Strongest width5 center');plt.title('Overlapping windows mechanically create persistence; W26');save('hot_zone_centers')
    reference=spacing_reference()['sample'];fig,axes=plt.subplots(1,2,figsize=(11,4))
    for ax,col in zip(axes,['draw_range','minimum_spacing']):
        ax.hist(reference[col],bins=25,density=True,alpha=.5,label='Independent IID reference50k')
        ax.hist(result['spacing'][col],bins=25,density=True,histtype='step',lw=2,label='Historical');ax.set_xlabel(col);ax.legend(fontsize=8)
    fig.suptitle('Raw distributions; complete-search calibration reported separately');save('spacing_vs_null')
    from src.models.number_space import RangeDensityModel
    kw={} if selected is None else selected['range']
    model=RangeDensityModel(**kw).fit(x,cutoff=len(x));scores=model.score_matrix(x,target=len(x)+1)
    plt.figure(figsize=(11,4));plt.bar(numbers,[scores[n] for n in numbers]);plt.xlabel('Number');plt.ylabel('Ranking support');plt.title('Development-selected range ranking' if selected else 'Predeclared W26/width5 reference ranking');save('range_model_ranking')


def analyze(data,directory,*,replicates=199,dataset_hash=None,progress=print):
    directory=Path(directory);guard_reports(directory);directory.mkdir(parents=True,exist_ok=True)
    began=perf_counter();x=lotto_matrix(data,cutoff=len(data));result=complete_search(x,details=True)
    for name in ('density','range_leaders','zones','movement','peaks','activity','spacing','spacing_peaks','motifs'):
        result[name].to_csv(directory/(name+'.csv'),index=False)
    reference=spacing_reference()
    pd.DataFrame(dict(metric=METRICS,reference_mean=reference['mean'],reference_std=reference['std'],
        historical_mean=result['spacing'][list(METRICS)].mean().to_numpy())).to_csv(directory/'spacing_summary.csv',index=False)
    comparison,null=compare_nulls(x,replicates=replicates,progress=progress)
    comparison.to_csv(directory/'global_null_comparison.csv',index=False);null.to_csv(directory/'surrogate_maxima.csv',index=False)
    plot_reports(x,result,directory/'plots')
    meta=dict(cutoff=len(x),dataset_hash=dataset_hash,search_space=result['space'],maxima=result['maxima'],
        replicates=replicates,seed=100042,reference_draws=50000,reference_seed=1010,future_result_accessed=False,runtime_seconds=perf_counter()-began)
    (directory/'analysis_metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    if progress:progress(comparison.to_string(index=False));progress(f'Analysis runtime {meta["runtime_seconds"]:.1f}s')
    return meta


def run(args):
    if args.command=='freeze-number-space':
        from src.phase10_freeze import freeze_number_space
        from src.freeze_artifacts import digest
        paths=freeze_number_space(args.data,args.reports_dir or ROOT/'reports/prospective/phase10')
        for name,path in paths.items():print(f'{name}: {path}\nSHA256: {digest(path)}')
        return
    data,h=strict_source(args.data);directory=args.reports_dir or ROOT/'reports/number_space';guard_reports(directory)
    if args.command=='analyze-number-space':analyze(data,directory,replicates=args.surrogates,dataset_hash=h)
    else:
        from src.backtest.number_space import comparison
        comparison(data,directory,cadence=args.cadence)
