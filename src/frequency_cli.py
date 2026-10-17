"""Isolated offline Phase8 research commands; never write earlier report trees."""
from dataclasses import asdict
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.prospective_experiment import ROOT,strict_source
from src.analysis.spatiotemporal import lotto_matrix
from src.analysis.frequency3d import WINDOWS,frequency_states,FrequencyEncoder,frequency_table
from src.analysis.frequency_search import FrequencySearchConfig,search_frequency,compare_frequency_nulls,conditional_frequency

def guard_reports(directory):
    path=Path(directory).resolve();reports=ROOT/'reports'
    if path==ROOT or path.is_relative_to(ROOT/'data') or (path.is_relative_to(reports) and not path.is_relative_to(reports/'spatiotemporal_frequency')):
        raise ValueError('Phase8 cannot overwrite earlier research, data or prospective artifacts')

def add_commands(commands):
    p=commands.add_parser('analyze-frequency3d',help='Complete all-window recent-frequency searches and nulls')
    p.add_argument('--surrogates',type=int,default=199);p.add_argument('--reports-dir',type=Path)
    p=commands.add_parser('compare-frequency3d',help='Identical-target frequency/2D/gap3D comparisons')
    p.add_argument('--cadence',type=int,default=26);p.add_argument('--reports-dir',type=Path)
    p=commands.add_parser('freeze-frequency3d',help='Independent Phase8 prospective snapshot, no result retrieval')
    p.add_argument('--reports-dir',type=Path)

def distribution(x,directory):
    summaries=[];supports=[];raw_counts=[]
    for window in WINDOWS:
        f={k:v[:-1] for k,v in frequency_states(x,window).items()};enc=FrequencyEncoder(window).fit(f,cutoff=len(x))
        finite=f['count'][np.isfinite(f['count'])]
        summaries.append(dict(window=window,observations=len(finite),missing=int(np.isnan(f['count']).sum()),
            min=float(finite.min()),max=float(finite.max()),median=float(np.median(finite)),
            quantiles={str(q):float(np.quantile(finite,q)) for q in (.1,1/3,.5,2/3,.9,.95,.99)},encoder=enc.configuration()))
        for count in range(window+1):
            raw_counts.append(dict(window=window,count=count,rate=count/window,observations=int((f['count']==count).sum()),
                winning_sources=int((x&(f['count']==count)).sum()),sparse_lt100=bool((x&(f['count']==count)).sum()<100)))
        for representation in ('count','quantile','relative'):
            states=enc.transform(f,representation)
            for state in range(-1,enc.count(representation)):
                supports.append(dict(window=window,representation=representation,state=state,
                    observations=int((states==state).sum()),winning_sources=int((x&(states==state)).sum())))
    (directory/'state_distribution.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8')
    pd.DataFrame(supports).to_csv(directory/'state_support.csv',index=False)
    pd.DataFrame(raw_counts).to_csv(directory/'count_distribution.csv',index=False)
    return summaries

def stability(x,result,directory,config):
    leaders=pd.concat([g[g.search_eligible & (g.delta_number!=0)].nlargest(1,'raw_z') for _,g in result['conditional'].groupby('window')])
    output=[]
    intervals=[('rolling',end-260,end) for end in range(260,len(x)+1,26)]
    intervals +=[(era,int(ix[0]),int(ix[-1]+1)) for era,ix in zip(('early','middle','recent'),np.array_split(np.arange(len(x)),3)) if len(ix)>config.max_dt]
    for rule in leaders.itertuples():
        f={k:v[:-1] for k,v in frequency_states(x,rule.window).items()};enc=FrequencyEncoder(rule.window).fit(f,cutoff=len(x))
        states=enc.transform(f,rule.representation)
        for era,start,end in intervals:
            table=conditional_frequency(x[start:end],states[start:end],state_count=enc.count(rule.representation),
                max_dt=config.max_dt,max_dn=config.max_dn,min_support=config.min_support)
            selected=table[(table.delta_draw==rule.delta_draw)&(table.delta_number==rule.delta_number)&(table.state==rule.state)].copy()
            selected['window']=rule.window;selected['representation']=rule.representation;selected['era']=era
            selected['start_draw']=start+1;selected['end_draw']=end;output.append(selected)
    frame=pd.concat(output,ignore_index=True) if output else pd.DataFrame(columns=['window','era','end_draw','match_rate','search_eligible'])
    frame.to_csv(directory/'rule_stability.csv',index=False)
    return frame

def plots(x,result,rolling,null,directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory.mkdir(parents=True,exist_ok=True)
    f={k:v[:-1] for k,v in frequency_states(x,26).items()};enc=FrequencyEncoder(26).fit(f,cutoff=len(x));states=enc.transform(f)
    fig,ax=plt.subplots(figsize=(15,5))
    for s,label,color in [(-1,'insufficient history','#777777'),(0,'COLD','#1565c0'),(1,'NEUTRAL','#e69f00'),(2,'HOT','#c62828')]:
        t,n=np.where(x&(states==s));ax.scatter(t+1,n+1,s=3,label=label,color=color,alpha=.6)
    ax.set(xlabel='Draw',ylabel='Number',title='W26 PRE-draw frequency states; descriptive full-history bins');ax.legend()
    fig.tight_layout();fig.savefig(directory/'W26_state_raster.png',dpi=150);plt.close(fig)
    for window in WINDOWS:
        fig,axes=plt.subplots(1,3,figsize=(15,5),sharey=True)
        table=result['conditional'].query('window==@window and representation=="quantile"')
        for s,ax in enumerate(axes):
            g=table[table.state==s].copy();g.loc[~g.search_eligible,'raw_z']=np.nan
            grid=g.pivot(index='delta_number',columns='delta_draw',values='raw_z')
            im=ax.imshow(grid,origin='lower',aspect='auto',cmap='coolwarm',vmin=-5,vmax=5,
                extent=(.5,grid.columns.max()+.5,grid.index.min()-.5,grid.index.max()+.5))
            ax.set(title=['COLD','NEUTRAL','HOT'][s],xlabel='Draw displacement',ylabel='Number displacement')
        fig.suptitle(f'W{window}: raw conditional z, not significance');fig.colorbar(im,ax=axes,shrink=.7)
        fig.savefig(directory/f'W{window}_conditional.png',dpi=150,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(15,4))
    for window,ax in zip(WINDOWS,axes):
        g=result['directional'].query('window==@window and kind=="hot_cold_direction_interaction"').copy()
        g.loc[~g.search_eligible,'raw_z']=np.nan
        grid=g.pivot(index='delta_number',columns='delta_draw',values='raw_z')
        im=ax.imshow(grid,origin='lower',aspect='auto',cmap='coolwarm',vmin=-4,vmax=4,
            extent=(.5,grid.columns.max()+.5,.5,grid.index.max()+.5))
        ax.set(title=f'W{window}',xlabel='Draw displacement',ylabel='Absolute number displacement')
    fig.suptitle('HOT minus COLD directional contrast: descriptive raw z');fig.colorbar(im,ax=axes,shrink=.7)
    fig.savefig(directory/'hot_cold_direction.png',dpi=150,bbox_inches='tight');plt.close(fig)
    fig,ax=plt.subplots(figsize=(12,5))
    for window,g in rolling[rolling.era=='rolling'].groupby('window'):
        ax.plot(g.end_draw,g.match_rate.where(g.search_eligible.astype(bool)),label=f'W{window}')
    if len(rolling[rolling.era=='rolling']): ax.legend()
    else: ax.text(.5,.5,'No complete 260-draw rolling windows',ha='center',transform=ax.transAxes)
    ax.axhline(6/45,color='black',linestyle='--');ax.set(xlabel='260-draw window endpoint',ylabel='Match rate',title='Selected strongest rules: descriptive; minimum100 opportunities')
    fig.tight_layout();fig.savefig(directory/'strongest_rules_rolling.png',dpi=150);plt.close(fig)
    paths=result['paths']
    if len(paths):
        path=paths.sort_values(['chain_length','window','start_draw'],ascending=[False,True,True]).iloc[0]
        t=int(path.start_draw)-1+np.arange(int(path.chain_length))*int(path.delta_draw)
        n=int(path.start_number)-1+np.arange(int(path.chain_length))*int(path.delta_number)
        f=frequency_states(x,int(path.window));fig=plt.figure(figsize=(9,7));ax=fig.add_subplot(111,projection='3d')
        ax.plot(t+1,n+1,f['rate'][t,n],marker='o');ax.set(xlabel='Draw',ylabel='Number',zlabel='Pre-draw frequency rate',title=f'W{int(path.window)} selected trajectory: inspection only')
        fig.tight_layout();fig.savefig(directory/'selected_trajectory.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(3,2,figsize=(12,10))
    for ax,stat in zip(axes.ravel(),result['maxima']):
        for kind,g in null.groupby('null_model'): ax.hist(g[stat],bins=18,alpha=.5,label=kind)
        ax.axvline(result['maxima'][stat],color='black');ax.set_title(stat);ax.legend(fontsize=7)
    axes.ravel()[-1].axis('off');fig.suptitle('All-window complete-search global maxima')
    fig.tight_layout();fig.savefig(directory/'null_global_maxima.png',dpi=150);plt.close(fig)

def analyze(data,directory,*,replicates=199,progress=print,dataset_hash=None):
    start=perf_counter();directory=Path(directory);guard_reports(directory);directory.mkdir(parents=True,exist_ok=True)
    x=lotto_matrix(data,cutoff=len(data));cfg=FrequencySearchConfig()
    dist=distribution(x,directory)
    if progress: progress('State distributions exported BEFORE pattern search: '+json.dumps(dist))
    frequency_table(data,cutoff=len(data)).to_csv(directory/'historical_states.csv',index=False)
    result=search_frequency(x,cfg)
    for key,value in result.items():
        if isinstance(value,pd.DataFrame): value.to_csv(directory/f'{key}.csv',index=False)
    if progress: progress('Complete search space: '+json.dumps(result['space']))
    comparison,null,follow=compare_frequency_nulls(x,cfg,replicates=replicates,progress=progress)
    comparison.to_csv(directory/'global_null_comparison.csv',index=False);null.to_csv(directory/'surrogate_maxima.csv',index=False)
    follow.to_csv(directory/'followup_null.csv',index=False)
    observed=result['conditional'].query('delta_draw==42 and delta_number==-5 and representation=="quantile"')
    rows=[]
    for kind,g in follow.groupby('null_model'):
        for row in observed.to_dict('records'):
            values=g[(g.window==row['window'])&(g.state==row['state'])].raw_z
            rows.append(dict(**row,null_model=kind,local_followup_p=float((1+(values>=row['raw_z']).sum())/(1+len(values))),caveat='Phase6 selected rule, NOT independent preregistration'))
    pd.DataFrame(rows).to_csv(directory/'followup_42_minus5.csv',index=False)
    rolling=stability(x,result,directory,cfg);plots(x,result,rolling,null,directory/'plots')
    meta=dict(cutoff=len(data),dataset_hash=dataset_hash,configuration=asdict(cfg),encoders=result['encoders'],
        search_space=result['space'],maxima=result['maxima'],window_maxima=result['window_maxima'],
        replicates=replicates,seed=80042,runtime_seconds=perf_counter()-start,future_result_accessed=False,
        hough='Deferred: sparse intercept search adds little interpretable information',
        count_rate_equivalence='count and rate are identical partitions within W, tested once')
    (directory/'analysis_metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    if progress: progress(comparison.to_string(index=False))
    return meta

def run(args):
    if args.command=='freeze-frequency3d':
        from src.phase8_freeze import freeze_frequency
        from src.freeze_artifacts import digest
        paths=freeze_frequency(args.data,args.reports_dir or ROOT/'reports/prospective/phase8')
        for name,path in paths.items(): print(f'{name}: {path}\nSHA-256: {digest(path)}')
        return
    data,h=strict_source(args.data);directory=args.reports_dir or ROOT/'reports/spatiotemporal_frequency';guard_reports(directory)
    if args.command=='analyze-frequency3d': meta=analyze(data,directory,replicates=args.surrogates,dataset_hash=h,progress=lambda s:print(s,flush=True))
    else:
        from src.backtest.frequency3d import comparison
        meta=comparison(data,directory/f'walk_forward_{args.cadence}',cadence=args.cadence,progress=lambda s:print(s,flush=True))
    print(f'Phase8 runtime {meta["runtime_seconds"]:.1f}s. Canonical hash {h}. No future result accessed.')
