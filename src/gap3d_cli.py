"""Offline Phase7 descriptive research and isolated command entry points."""
from dataclasses import asdict
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.analysis.gap3d import causal_states,GapEncoder,state_table
from src.analysis.gap3d_search import Search3DConfig,search3d,compare_nulls3d,conditional_scores
from src.analysis.spatiotemporal import lotto_matrix
from src.prospective_experiment import ROOT,strict_source


def add_commands(commands):
    p=commands.add_parser('analyze-gap3d',help='Gap-conditioned descriptive searches and complete null comparisons')
    p.add_argument('--surrogates',type=int,default=199)
    p.add_argument('--reports-dir',type=Path)
    p=commands.add_parser('compare-gap3d',help='Identical-target2D/3D walk-forward ablations')
    p.add_argument('--cadence',type=int,default=26)
    p.add_argument('--start',type=int,default=401)
    p.add_argument('--primary-only',action='store_true')
    p.add_argument('--reports-dir',type=Path)
    p=commands.add_parser('freeze-gap3d',help='One independent immutable Phase7 prediction; no result retrieval')
    p.add_argument('--reports-dir',type=Path)


def guard_reports(directory):
    path=Path(directory).resolve(); reports=(ROOT/'reports').resolve()
    if (path==ROOT.resolve() or path.is_relative_to((ROOT/'data').resolve()) or
        (path.is_relative_to(reports) and not path.is_relative_to(reports/'spatiotemporal3d'))):
        raise ValueError('Phase7 must not overwrite earlier research, canonical data, or prospective artifacts')


def distribution(x,directory):
    g,m,r=causal_states(x); g,r=g[:-1],r[:-1]
    encoder=GapEncoder().fit(g,r,cutoff=len(x)); finite=g[np.isfinite(g)]
    counts=pd.Series(finite.astype(int)).value_counts().sort_index().rename_axis('gap').reset_index(name='observations')
    counts['sparse_lt100']=counts.observations<100
    counts.to_csv(directory/'gap_counts.csv',index=False)
    summary=dict(observations=int(len(finite)),missing_never_seen=int(np.isnan(g).sum()),
        min=float(finite.min()),max=float(finite.max()),median=float(np.median(finite)),
        quantiles={str(q):float(np.quantile(finite,q)) for q in (.1,.25,1/3,.5,2/3,.75,.9,.95,.99)},
        encoder=encoder.configuration())
    (directory/'gap_distribution.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    rows=[]
    for representation in ('quantile','clipped','relative'):
        states=encoder.transform(g,r,representation)
        for state in range(-1,encoder.count(representation)):
            rows.append(dict(representation=representation,state=state,observations=int((states==state).sum()),
                winning_source_points=int((x&(states==state)).sum())))
    pd.DataFrame(rows).to_csv(directory/'state_support.csv',index=False)
    return summary


def stability(x,result,directory,config):
    g,m,r=causal_states(x); g,r=g[:-1],r[:-1]; encoder=GapEncoder().fit(g,r,cutoff=len(x))
    candidates=result['conditional'].query('search_eligible').nlargest(5,'raw_z')
    primary=result['conditional'].query('search_eligible and representation=="quantile"').nlargest(5,'raw_z')
    candidates=pd.concat([candidates,primary]).drop_duplicates(['representation','gap_state','delta_draw','delta_number'])
    outputs=[]
    windows=[('rolling',end-260,end) for end in range(260,len(x)+1,26)]
    windows += [(label,int(ix[0]),int(ix[-1]+1)) for label,ix in zip(('early','middle','recent'),np.array_split(np.arange(len(x)),3))]
    for representation,selected in candidates.groupby('representation'):
        states=encoder.transform(g,r,representation)
        for era,start,end in windows:
            if end-start<=config.max_dt: continue
            table=conditional_scores(x[start:end],states[start:end],state_count=encoder.count(representation),
                max_dt=config.max_dt,max_dn=config.max_dn,min_support=config.min_support)
            table=table.merge(selected[['gap_state','delta_draw','delta_number']],on=['gap_state','delta_draw','delta_number'])
            table['representation']=representation; table['era']=era; table['start_draw']=start+1; table['end_draw']=end
            outputs.append(table)
    frame=pd.concat(outputs,ignore_index=True) if outputs else pd.DataFrame()
    frame.to_csv(directory/'rule_stability.csv',index=False)
    return frame


def render_plots(x,result,rolling,comparison,null,directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory.mkdir(parents=True,exist_ok=True)
    g,m,r=causal_states(x); enc=GapEncoder().fit(g[:-1],r[:-1],cutoff=len(x)); state=enc.transform(g[:-1],r[:-1])
    fig,ax=plt.subplots(figsize=(15,5))
    for s,label,color in [(-1,'never seen (excluded from search)','#777777'),(0,'low','#1565c0'),(1,'medium','#e69f00'),(2,'high','#8e44ad')]:
        t,n=np.where(x&(state==s)); ax.scatter(t+1,n+1,s=3,color=color,label=label,alpha=.55)
    ax.set(xlabel='Draw',ylabel='Number',title='Winning points colored by causal PRE-draw gap state (descriptive full-history bins)')
    ax.legend(); fig.tight_layout(); fig.savefig(directory/'gap_state_raster.png',dpi=160); plt.close(fig)
    for s,label in enumerate(('low','medium','high')):
        table=result['conditional'].query('representation=="quantile" and gap_state==@s').copy()
        table.loc[~table.search_eligible,'raw_z']=np.nan
        grid=table.pivot(index='delta_number',columns='delta_draw',values='raw_z')
        # Keep the excluded zero displacement visibly blank, with honest integer coordinates.
        grid=grid.reindex(range(int(grid.index.min()),int(grid.index.max())+1))
        fig,ax=plt.subplots(figsize=(10,5)); im=ax.imshow(grid,origin='lower',aspect='auto',cmap='coolwarm',
            extent=(grid.columns.min()-.5,grid.columns.max()+.5,grid.index.min()-.5,grid.index.max()+.5))
        ax.set(xlabel='Draw displacement',ylabel='Number displacement',title=f'{label} gap: raw conditional score, not significance')
        fig.colorbar(im,ax=ax); fig.tight_layout(); fig.savefig(directory/f'{label}_gap_shifts.png',dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(12,5))
    if len(rolling):
        selected=result['conditional'].query('search_eligible').nlargest(1,'raw_z').iloc[0]
        series=rolling[(rolling.era=='rolling')&(rolling.representation==selected.representation)&
            (rolling.delta_draw==selected.delta_draw)&(rolling.delta_number==selected.delta_number)&(rolling.gap_state==selected.gap_state)]
        ax.plot(series.end_draw,series.match_rate,marker='.')
        ax.axhline(6/45,color='black',linestyle='--'); ax.set_title(f'Descriptive selected rule: ({int(selected.delta_draw)}, {int(selected.delta_number)}) {selected.representation} state{int(selected.gap_state)}')
    ax.set(xlabel='260-draw window endpoint',ylabel='Conditional match rate'); fig.tight_layout()
    fig.savefig(directory/'strongest_rule_rolling.png',dpi=150); plt.close(fig)
    paths=result['maximal_trajectories']
    if len(paths):
        path=paths.sort_values(['chain_length','start_draw'],ascending=[False,True]).iloc[0]
        ts=int(path.start_draw)-1+np.arange(int(path.chain_length))*int(path.delta_draw)
        ns=int(path.start_number)-1+np.arange(int(path.chain_length))*int(path.delta_number)
        fig=plt.figure(figsize=(9,7)); ax=fig.add_subplot(111,projection='3d')
        ax.plot(ts+1,ns+1,g[ts,ns],marker='o',color='#1565c0')
        ax.set(xlabel='Draw',ylabel='Number',zlabel='Raw pre-draw gap',title='Selected maximal trajectory: inspection only')
        fig.tight_layout(); fig.savefig(directory/'selected_trajectory_3d.png',dpi=150); plt.close(fig)
    fig,axes=plt.subplots(3,2,figsize=(12,10))
    for ax,stat in zip(axes.ravel(),result['maxima']):
        for kind,group in null.groupby('null_model'): ax.hist(group[stat],bins=18,alpha=.5,label=kind)
        ax.axvline(result['maxima'][stat],color='black',label='real maximum'); ax.set_title(stat); ax.legend(fontsize=7)
    axes.ravel()[-1].axis('off'); fig.suptitle('Complete-search maxima: gaps and bins recomputed in every surrogate')
    fig.tight_layout(); fig.savefig(directory/'global_null_maxima.png',dpi=150); plt.close(fig)


def analyze(data,directory,*,replicates=199,progress=print,dataset_hash=None):
    started=perf_counter(); directory=Path(directory); guard_reports(directory); directory.mkdir(parents=True,exist_ok=True)
    x=lotto_matrix(data,cutoff=len(data)); config=Search3DConfig()
    summary=distribution(x,directory)
    if progress: progress('Gap distribution BEFORE search: '+json.dumps(summary))
    state_table(data,cutoff=len(data)).to_csv(directory/'historical_states.csv',index=False)
    result=search3d(x,config)
    for key,value in result.items():
        if isinstance(value,pd.DataFrame): value.to_csv(directory/f'{key}.csv',index=False)
    (directory/'search_space.json').write_text(json.dumps(result['search_space'],indent=2),encoding='utf-8')
    if progress: progress('Search configurations: '+json.dumps(result['search_space']))
    comparison,null,follow=compare_nulls3d(x,config,replicates=replicates,progress=progress)
    comparison.to_csv(directory/'global_null_comparison.csv',index=False); null.to_csv(directory/'surrogate_maxima.csv',index=False)
    follow.to_csv(directory/'followup_42_minus5_null.csv',index=False)
    observed=result['conditional'].query('delta_draw==42 and delta_number==-5 and representation=="quantile"').copy()
    followup=[]
    for kind,group in follow.groupby('null_model'):
        for row in observed.to_dict('records'):
            values=group[group.gap_state==row['gap_state']].raw_z
            followup.append(dict(**row,null_model=kind,local_followup_p=float((1+(values>=row['raw_z']).sum())/(len(values)+1)),
                caveat='Phase6-selected follow-up; NOT independent preregistered evidence'))
    pd.DataFrame(followup).to_csv(directory/'followup_42_minus5.csv',index=False)
    rolling=stability(x,result,directory,config)
    metadata=dict(cutoff=len(data),dataset_hash=dataset_hash,configuration=asdict(config),encoder=result['encoder'],
        search_space=result['search_space'],maxima=result['maxima'],replicates=replicates,seed=70042,
        null_search_runtime_seconds=perf_counter()-started,hough='Not implemented: added intercept family would be sparse and hard to interpret.',
        destination_usage='DESCRIPTIVE_ONLY; never used by predictive rules',future_result_accessed=False)
    (directory/'analysis_metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    render_plots(x,result,rolling,comparison,null,directory/'plots')
    if progress: progress(comparison.to_string(index=False))
    return metadata


def model_factories(primary_only=False):
    from functools import partial
    from src.models.translation import TranslationModel,ChainModel
    from src.models.gap3d import GapConditionedTranslationModel,GapConditionedChainModel
    factories=dict(TranslationModel=TranslationModel,ChainModel=ChainModel,
        GapConditionedTranslationModel=GapConditionedTranslationModel,GapConditionedChainModel=GapConditionedChainModel)
    if not primary_only:
        for cls in (GapConditionedTranslationModel,GapConditionedChainModel):
            for representation in ('clipped','relative'):
                factories[cls.__name__+'_'+representation]=partial(cls,representation=representation)
    return factories


def comparison(data,directory,*,start=401,cadence=26,primary_only=False,progress=print):
    from src.analysis.features import build_prospective_features,GAP
    from src.prediction_scope import ProspectiveScope
    from src.backtest.translation import walk_forward,summaries,pool_report
    from src.backtest.ranking import summarize_rankings
    from src.backtest.gap3d import paired_comparisons
    began=perf_counter(); directory=Path(directory); guard_reports(directory); directory.mkdir(parents=True,exist_ok=True)
    features=build_prospective_features(data,scope=ProspectiveScope(len(data)),progress=progress)
    features=features[features.target_draw<=len(data)][['target_draw','feature_cutoff','number','appeared_next',*GAP]]
    factories=model_factories(primary_only)
    results=walk_forward(data,factories,start=start,cadence=cadence,gap_features=features,combined=False,progress=progress)
    results.to_csv(directory/'prediction_audit.csv',index=False)
    starts=tuple(s for s in (401,501,601,701,801,901) if s>=start)
    if start not in starts: starts=(start,)+starts
    tables=summaries(results,starts=starts)
    tables['paired_2d_3d']=paired_comparisons(results,starts=starts)
    for name,frame in tables.items(): frame.to_csv(directory/f'{name}.csv',index=False)
    development=results[results.target_draw<=900]
    if len(development):
        summarize_rankings(development)['comparison'].to_csv(directory/'development_comparison.csv',index=False)
        pool_report(development).to_csv(directory/'development_pools.csv',index=False)
    results[(results.pool_8>=5)|(results.pool_10>=5)|(results.pool_12>=5)|(results.pool_15>=5)].to_csv(directory/'five_plus_pool_events.csv',index=False)
    meta=dict(start=start,end=len(data),cadence=cadence,seed=42,development_end=900,later_evaluation_start=901,
        configurations={name:factory().configuration() for name,factory in factories.items()},
        runtime_seconds=perf_counter()-began,bootstrap_replicates=2000,bootstrap_block=26,
        selection='No outcome-selected settings, thresholds or combination; primary quantile models fixed before evaluation',
        window_note='Multiple starts are nested prediction slices; cadence sensitivity uses a separate refit run.',
        uncertainty='Unadjusted paired26-draw block bootstrap; degenerate rare-event intervals do not prove zero risk.',
        caveat='Historical later period is not a pristine holdout after earlier phases. No predictive claim.',
        future_result_accessed=False)
    (directory/'protocol.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return tables,meta


def run(args):
    if args.command=='freeze-gap3d':
        from src.phase7_freeze import freeze_gap3d
        from src.freeze_artifacts import digest
        paths=freeze_gap3d(args.data,args.reports_dir or ROOT/'reports/prospective/phase7')
        for name,path in paths.items(): print(f'{name}: {path}\nSHA-256: {digest(path)}')
        print('Independent Phase7 experiment FROZEN_UNEVALUATED; no target result accessed.')
        return
    data,dataset_hash=strict_source(args.data)
    directory=args.reports_dir or ROOT/'reports/spatiotemporal3d'
    guard_reports(directory)
    if args.command=='compare-gap3d':
        tables,meta=comparison(data,directory/f'walk_forward_{args.cadence}',start=args.start,cadence=args.cadence,
            primary_only=args.primary_only,progress=lambda s:print(s,flush=True))
        print(tables['comparison'][['model','evaluation_start','avg_hits','delta_vs_random','paired_ci_low','paired_ci_high']].to_string(index=False))
        print(f'Runtime {meta["runtime_seconds"]:.1f}s; source hash {dataset_hash}; no future result accessed.')
        return
    meta=analyze(data,directory,replicates=args.surrogates,progress=lambda s:print(s,flush=True),dataset_hash=dataset_hash)
    print(f'Completed Phase7 descriptive analysis in{meta["null_search_runtime_seconds"]:.1f}s; target1246 not accessed.')
