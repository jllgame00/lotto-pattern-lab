"""Offline Phase6 commands, independent of old historical seals and freezes."""
from dataclasses import asdict
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd

from src.analysis.spatiotemporal import SearchConfig,lotto_matrix,search,compare_nulls,shift_scores,P
from src.prospective_experiment import strict_source,ROOT
from src.models.translation import TranslationModel,ChainModel


def add_commands(commands):
    for name,description in [('analyze-2d','Complete bounded2D searches and surrogate maxima'),
                              ('compare-2d','Causal translation/chain walk-forward research'),
                              ('freeze-2d','NEW Phase6 prospective experiment; never replaces Phase5')]:
        command=commands.add_parser(name,help=description)
        command.add_argument('--reports-dir',type=Path)
        if name=='analyze-2d': command.add_argument('--surrogates',type=int,default=199)
        if name=='compare-2d':
            command.add_argument('--start',type=int,default=401)
            command.add_argument('--cadence',type=int,default=26)
            command.add_argument('--primary-only',action='store_true')


def plot_matrix(x,path,*,start=1,end=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    end=len(x) if end is None else end
    if not 1<=start<=end<=len(x): raise ValueError('Invalid plot draw bounds')
    times,numbers=np.where(x[start-1:end])
    fig,ax=plt.subplots(figsize=(15,5))
    ax.scatter(times+start,numbers+1,s=4,alpha=.6,color='#245a81')
    ax.set(xlabel='Draw',ylabel='Main number',ylim=(0,46),title=f'Observed main-number points, draws{start}–{end} (descriptive only)')
    fig.tight_layout(); fig.savefig(path,dpi=160); plt.close(fig)


def descriptive(data,directory,*,surrogates=199,progress=print):
    began=perf_counter(); directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    plots=directory/'plots'; plots.mkdir(exist_ok=True)
    x=lotto_matrix(data,cutoff=len(data)); config=SearchConfig()
    result=search(x,config)
    filenames=dict(shifts='shift_scores',direction='directional_asymmetry',chain_counts='chain_counts',
                   chains='maximal_chains',lines='hough_lines',spectrum='spectral_peaks')
    for key,name in filenames.items(): result[key].to_csv(directory/f'{name}.csv',index=False)
    comparison,null=compare_nulls(x,config,replicates=surrogates,seed=60042,progress=progress)
    comparison.to_csv(directory/'global_null_comparison.csv',index=False)
    null.to_csv(directory/'surrogate_maxima.csv',index=False)
    # Select descriptive candidates on all allowed history. NEVER supplied to models.
    candidates=result['shifts'].query('delta_number!=0').nlargest(10,'raw_z')
    rolling=[]
    for end in range(260,len(x)+1,13):
        table=shift_scores(x[end-260:end])
        for c in candidates.itertuples():
            row=table[(table.delta_draw==c.delta_draw)&(table.delta_number==c.delta_number)].iloc[0].to_dict()
            row.update(start_draw=end-259,end_draw=end,window=260); rolling.append(row)
    rolling=pd.DataFrame(rolling); rolling.to_csv(directory/'rolling_translation_strength.csv',index=False)
    eras=[]
    for name,indices in zip(('early','middle','recent'),np.array_split(np.arange(len(x)),3)):
        table=shift_scores(x[indices])
        table['era']=name; table['start_draw']=int(indices[0]+1); table['end_draw']=int(indices[-1]+1)
        eras.append(table.merge(candidates[['delta_draw','delta_number']],on=['delta_draw','delta_number']))
    pd.concat(eras).to_csv(directory/'translation_era_stability.csv',index=False)
    plot_matrix(x,plots/'matrix_full.png')
    plot_matrix(x,plots/'matrix_recent.png',start=max(1,len(x)-155))
    metadata=dict(cutoff=len(data),matrix_shape=list(x.shape),configuration=asdict(config),
        null_replicates_per_family=surrogates,seed=60042,fixed_margin_trades_per_row=20,
        runtime_seconds=perf_counter()-began,runtime_scope='searches, exports and matrix plots; before summary plots',raw_maxima=result['maxima'],
        warnings=['Raw z statistics use simplified variance, not valid local significance tests.',
            'Global p=(1+surrogate maxima >= observed maximum)/(B+1); six-family Bonferroni within each null.',
            'Evidence must survive both nulls; constrained trades preserve margins exactly but finite mixing is approximate.',
            'Maximal chains reported; shorter overlapping subchains contribute to count statistics but are not independent discoveries.',
            'Descriptive top shifts use all history and must never be injected into earlier forecasts.',
            'FFT assumes an ordered finite label axis; fixed six-per-row, boundaries, taper and discrete axes affect peaks.',
            'No target1246 result has been retrieved, inspected or evaluated.'])
    (directory/'analysis_metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    _plots(result,rolling,comparison,null,plots)
    return metadata


def _plots(result,rolling,comparison,null,directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(10,6)); grid=result['shifts'].pivot(index='delta_number',columns='delta_draw',values='raw_z')
    im=ax.imshow(grid,origin='lower',aspect='auto',extent=(grid.columns.min()-.5,grid.columns.max()+.5,grid.index.min()-.5,grid.index.max()+.5),cmap='coolwarm')
    ax.set(xlabel='Draw displacement',ylabel='Number displacement',title='Overlap-normalized shift statistic (raw, not significance)')
    fig.colorbar(im,ax=ax,label='Raw z'); fig.tight_layout(); fig.savefig(directory/'shift_overlap.png',dpi=150); plt.close(fig)
    fig,axes=plt.subplots(3,2,figsize=(12,10))
    for ax,stat in zip(axes.ravel(),result['maxima']):
        for name,group in null.groupby('null_model'): ax.hist(group[stat],bins=18,alpha=.5,label=name)
        ax.axvline(result['maxima'][stat],color='black',label='real maximum')
        ax.set_title(stat); ax.legend(fontsize=7)
    fig.suptitle('The complete search is repeated on EVERY surrogate'); fig.tight_layout()
    fig.savefig(directory/'global_null_maxima.png',dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(13,5))
    if len(rolling):
        for (dt,dn),group in rolling.groupby(['delta_draw','delta_number']):
            ax.plot(group.end_draw,group.match_rate,label=f'({int(dt)}, {int(dn):+d})',alpha=.75)
    ax.axhline(P,color='black',linestyle='--',label='IID6/45'); ax.legend(ncol=4,fontsize=8)
    ax.set(xlabel='Rolling260-draw endpoint',ylabel='Conditional overlap rate',title='Full-history selected shifts: exploratory stability, not causal rule selection')
    fig.tight_layout(); fig.savefig(directory/'rolling_translation_strength.png',dpi=150); plt.close(fig)


def model_factories(primary_only=False):
    factories={'TranslationModel':TranslationModel,'ChainModel':ChainModel}
    if not primary_only:
        factories.update({
            'TranslationPositive':lambda:TranslationModel(direction='positive'),
            'TranslationNegative':lambda:TranslationModel(direction='negative'),
            'TranslationShort':lambda:TranslationModel(max_dt=13),
            'TranslationLong':lambda:TranslationModel(min_dt=14),
            'ChainPositive':lambda:ChainModel(direction='positive'),
            'ChainNegative':lambda:ChainModel(direction='negative'),
            'ChainShort':lambda:ChainModel(max_dt=13),
            'ChainLong':lambda:ChainModel(min_dt=14)})
    return factories


def comparison(data,directory,*,start=401,cadence=26,primary_only=False,progress=print):
    from src.analysis.features import build_prospective_features,GAP
    from src.prediction_scope import ProspectiveScope
    from src.backtest.translation import walk_forward,summaries,pool_report
    from src.backtest.ranking import summarize_rankings
    began=perf_counter(); directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    features=build_prospective_features(data,scope=ProspectiveScope(len(data)),progress=progress)
    features=features[features.target_draw<=len(data)][['target_draw','feature_cutoff','number','appeared_next',*GAP]]
    results=walk_forward(data,model_factories(primary_only),start=start,cadence=cadence,gap_features=features,progress=progress)
    results.to_csv(directory/'prediction_audit.csv',index=False)
    tables=summaries(results,starts=tuple(s for s in (401,501,601,701,801,901) if s>=start))
    for name,frame in tables.items(): frame.to_csv(directory/f'{name}.csv',index=False)
    development=results[results.target_draw<=900]
    if len(development):
        development_tables=summarize_rankings(development)
        development_tables['comparison'].to_csv(directory/'development_comparison.csv',index=False)
        pool_report(development).to_csv(directory/'development_pools.csv',index=False)
    events=results[(results.pool_8>=5)|(results.pool_10>=5)|(results.pool_12>=5)|(results.pool_15>=5)]
    events.to_csv(directory/'five_plus_pool_events.csv',index=False)
    meta=dict(start=start,end=len(data),cadence=cadence,seed=42,development_end=900,
        later_evaluation_start=901,combined_selection='predeclared equal rank; no outcome-selected weights',
        configurations={name:factory().configuration() for name,factory in model_factories(primary_only).items()},
        runtime_seconds=perf_counter()-began,bootstrap_replicates=2000,bootstrap_block=26,
        window_note='Start-point comparisons are nested slices of one chronological run; cadence sensitivity is a separate refit run.',
        pool_uncertainty='Paired26-draw circular block bootstrap vs seededRandom. Binomial marginal intervals assume independent indicators; diagnostic only. Degenerate all-zero bootstrap intervals do not establish absence of rare events. All intervals are unadjusted for model/pool comparisons.',
        caveat='Later evaluation is later than Phase6 development, not untouched by previous phases; no validated predictive claim.')
    (directory/'protocol.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return tables,meta


def run(args):
    if args.command=='freeze-2d':
        from src.phase6_freeze import freeze_2d
        from src.freeze_artifacts import digest
        paths=freeze_2d(args.data,args.reports_dir or ROOT/'reports/prospective/phase6')
        for name,path in paths.items(): print(f'{name}: {path}\nSHA-256: {digest(path)}')
        print('Separate Phase6 experiment FROZEN_UNEVALUATED. No target1246 result accessed.')
        return
    data,dataset_hash=strict_source(args.data)
    directory=args.reports_dir or ROOT/'reports/spatiotemporal'
    # Research exports must never write into data or any prospective directory.
    resolved=directory.resolve()
    if any(resolved.is_relative_to(p.resolve()) for p in (ROOT/'data',ROOT/'reports/prospective')):
        raise ValueError('Research reports cannot write to data or prospective artifacts')
    if args.command=='analyze-2d':
        meta=descriptive(data,directory,surrogates=args.surrogates,progress=lambda s:print(s,flush=True))
    else:
        tables,meta=comparison(data,directory/f'walk_forward_{args.cadence}',start=args.start,cadence=args.cadence,
            primary_only=args.primary_only,progress=lambda s:print(s,flush=True))
        print(tables['comparison'].query('evaluation_start==901')[['model','avg_hits','delta_vs_random','paired_ci_low','paired_ci_high']].to_string(index=False))
    print(f'Dataset SHA-256: {dataset_hash}; runtime{meta["runtime_seconds"]:.1f}s. Target1246 remains unevaluated.')
