"""Phase9 offline joint-state research commands and isolated report paths."""
from dataclasses import asdict
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.prospective_experiment import ROOT,strict_source
from src.analysis.spatiotemporal import lotto_matrix
from src.analysis.joint_state import JointEncoder,state_table,support_audit,LABELS
from src.analysis.joint_search import JointSearchConfig,search_joint,compare_joint_nulls,parent_controls
from src.analysis.frequency_search import conditional_frequency

def guard_reports(directory):
    path=Path(directory).resolve();reports=ROOT/'reports'
    if path==ROOT or path.is_relative_to(ROOT/'data') or (path.is_relative_to(reports) and not path.is_relative_to(reports/'spatiotemporal_joint')):
        raise ValueError('Phase9 cannot overwrite data, earlier research or prospective artifacts')

def add_commands(commands):
    p=commands.add_parser('analyze-joint',help='Nine-state translation/interaction search and complete nulls')
    p.add_argument('--surrogates',type=int,default=199);p.add_argument('--reports-dir',type=Path)
    p=commands.add_parser('compare-joint',help='Identical-target joint/single-state/2D ablation')
    p.add_argument('--cadence',type=int,default=26);p.add_argument('--reports-dir',type=Path)
    p=commands.add_parser('freeze-joint',help='New independent Phase9 prospective snapshot; no result retrieval')
    p.add_argument('--reports-dir',type=Path)

def stability(x,result,directory,config):
    table=result['translations'];eligible=table[table.search_eligible & table.delta_number.ne(0)]
    leaders=pd.concat([eligible.nlargest(3,'interaction_lift'),eligible.nlargest(3,'raw_z')]).drop_duplicates(['state','delta_draw','delta_number'])
    enc=JointEncoder().fit(x,cutoff=len(x));states=enc.transform(x)['joint_state'][:-1];frames=[]
    intervals=[('rolling',end-260,end) for end in range(260,len(x)+1,26)]
    intervals +=[(era,int(ix[0]),int(ix[-1]+1)) for era,ix in zip(('early','middle','recent'),np.array_split(np.arange(len(x)),3)) if len(ix)>config.max_dt]
    for era,start,end in intervals:
        scores=parent_controls(conditional_frequency(x[start:end],states[start:end],state_count=9,max_dt=config.max_dt,
            max_dn=config.max_dn,min_support=config.min_support),prior=config.prior,min_support=config.min_support)
        scores=scores.merge(leaders[['state','delta_draw','delta_number']],on=['state','delta_draw','delta_number'])
        scores['era']=era;scores['start_draw']=start+1;scores['end_draw']=end;frames.append(scores)
    output=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame(columns=['era','end_draw','match_rate','interaction_lift','search_eligible'])
    output.to_csv(directory/'rule_stability.csv',index=False);return output

def plots(x,result,support,rolling,null,directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(1,2,figsize=(11,5))
    for ax,column,title in zip(axes,('observations','winning_sources'),('All number-state observations','Winning source points')):
        grid=support.pivot(index='gap_state',columns='frequency_state',values=column).reindex(index=range(3),columns=range(3))
        im=ax.imshow(grid,cmap='Blues');ax.set(xticks=range(3),xticklabels=['COLD','NEUTRAL','HOT'],yticks=range(3),yticklabels=['LOW','MID','HIGH'],title=title)
        for i in range(3):
            for j in range(3):
                color='white' if grid.iloc[i,j]>.6*grid.to_numpy().max() else 'black'
                ax.text(j,i,str(int(grid.iloc[i,j])),ha='center',va='center',color=color)
        fig.colorbar(im,ax=ax,shrink=.7)
    fig.tight_layout();fig.savefig(directory/'joint_support.png',dpi=150);plt.close(fig)
    table=result['translations']
    for state,label in [(0,'low_cold'),(8,'high_hot')]:
        scores=table[table.state==state].copy();scores.loc[~scores.search_eligible,'raw_z']=np.nan
        grid=scores.pivot(index='delta_number',columns='delta_draw',values='raw_z')
        fig,ax=plt.subplots(figsize=(10,5));im=ax.imshow(grid,origin='lower',aspect='auto',cmap='coolwarm',vmin=-5,vmax=5,
            extent=(.5,grid.columns.max()+.5,grid.index.min()-.5,grid.index.max()+.5))
        if scores.raw_z.isna().all():ax.text(.5,.5,'No rules meet minimum support',transform=ax.transAxes,ha='center')
        ax.set(xlabel='Draw displacement',ylabel='Number displacement',title=f'{LABELS[state]} raw joint z; not significance')
        fig.colorbar(im,ax=ax);fig.tight_layout();fig.savefig(directory/f'{label}_translations.png',dpi=150);plt.close(fig)
    eligible=table[table.search_eligible & table.delta_number.ne(0)]
    leader=eligible.nlargest(1,'interaction_lift').iloc[0] if len(eligible) else None
    fig,ax=plt.subplots(figsize=(9,5))
    if leader is not None:
        values=[leader.unconditional_shrunk_rate,leader.gap_shrunk_rate,leader.frequency_shrunk_rate,leader.joint_shrunk_rate]
        ax.bar(['Unconditional','Gap only','Frequency only','Joint'],values,color=['#777777','#1565c0','#e69f00','#8e44ad'])
        ax.set_title(f'Selected interaction ({int(leader.delta_draw)},{int(leader.delta_number)}), {leader.joint_label}')
        ax.set_ylim(0,max(values)*1.25)
    ax.set_ylabel('Shrunken historical match rate; not predictive evidence');fig.tight_layout();fig.savefig(directory/'parent_vs_joint.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5))
    g=table[table.search_eligible].groupby(['delta_number','delta_draw']).interaction_lift.max().unstack()
    if len(g):
        im=ax.imshow(g,origin='lower',aspect='auto',cmap='viridis',extent=(.5,g.columns.max()+.5,g.index.min()-.5,g.index.max()+.5));fig.colorbar(im,ax=ax)
    ax.set(xlabel='Draw displacement',ylabel='Number displacement',title='Best supported joint interaction lift per shift; selected raw values')
    fig.tight_layout();fig.savefig(directory/'interaction_lift.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(12,7),sharex=True)
    if leader is not None and len(rolling):
        g=rolling[(rolling.era=='rolling')&(rolling.state==leader.state)&(rolling.delta_draw==leader.delta_draw)&(rolling.delta_number==leader.delta_number)]
        for column,label,color in [('joint_shrunk_rate','Joint','#1565c0'),('gap_shrunk_rate','Gap','#e69f00'),('frequency_shrunk_rate','Frequency','#2e7d32')]:
            axes[0].plot(g.end_draw,g[column],label=label,color=color,linestyle=':',marker='.',alpha=.6)
            axes[0].plot(g.end_draw,g[column].where(g.search_eligible),color=color)
        axes[0].legend();axes[1].plot(g.end_draw,g.interaction_lift,linestyle=':',marker='.',alpha=.6)
        axes[1].plot(g.end_draw,g.interaction_lift.where(g.search_eligible))
        if len(g) and not g.search_eligible.any():
            axes[1].text(.5,.08,'All rolling windows below100 joint opportunities; descriptive dots only',ha='center',transform=axes[1].transAxes)
    axes[0].set_ylabel('Shrunken rate');axes[1].set(xlabel='260-draw window endpoint',ylabel='Interaction lift');axes[1].axhline(0,color='black',linestyle='--')
    fig.suptitle('Selected strongest interaction: dotted=subthreshold descriptive; solid=support100+')
    fig.tight_layout();fig.savefig(directory/'strongest_rule_rolling.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,5));paths=result['paths']
    if len(paths):
        path=paths.sort_values(['chain_length','start_draw'],ascending=[False,True]).iloc[0]
        t=int(path.start_draw)+np.arange(int(path.chain_length))*int(path.delta_draw);n=int(path.start_number)+np.arange(int(path.chain_length))*int(path.delta_number)
        ax.plot(t,n,marker='o');ax.set_title(f'Selected same-joint-state chain: {path.label}; inspection only')
    else:ax.text(.5,.5,'No supported three-point path',ha='center',transform=ax.transAxes)
    ax.set(xlabel='Draw',ylabel='Number');fig.tight_layout();fig.savefig(directory/'selected_chain.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for ax,stat in zip(axes.ravel(),result['maxima']):
        for kind,g in null.groupby('null_model'):ax.hist(g[stat],bins=18,alpha=.5,label=kind)
        ax.axvline(result['maxima'][stat],color='black');ax.set_title(stat);ax.legend(fontsize=7)
    fig.suptitle('Complete-search global maxima; both state histories recomputed')
    fig.tight_layout();fig.savefig(directory/'global_null_maxima.png',dpi=150);plt.close(fig)

def analyze(data,directory,*,replicates=199,progress=print,dataset_hash=None):
    began=perf_counter();directory=Path(directory);guard_reports(directory);directory.mkdir(parents=True,exist_ok=True)
    x=lotto_matrix(data,cutoff=len(data));config=JointSearchConfig()
    states=state_table(data,cutoff=len(data));support=support_audit(states)
    states.to_csv(directory/'historical_states.csv',index=False);support.to_csv(directory/'joint_support.csv',index=False)
    if progress:progress('Joint-state audit BEFORE search:\n'+support.to_string(index=False))
    result=search_joint(x,config)
    for key,value in result.items():
        if isinstance(value,pd.DataFrame):value.to_csv(directory/f'{key}.csv',index=False)
    opportunities=result['translations'].groupby('state').valid_opportunities.sum().rename('summed_shift_opportunities_overlapping')
    support.merge(opportunities,left_on='joint_state',right_index=True).to_csv(directory/'support_with_shift_opportunities.csv',index=False)
    if progress:progress('Complete search space: '+json.dumps(result['space']))
    comparison,null=compare_joint_nulls(x,config,replicates=replicates,progress=progress)
    comparison.to_csv(directory/'global_null_comparison.csv',index=False);null.to_csv(directory/'surrogate_maxima.csv',index=False)
    rolling=stability(x,result,directory,config);plots(x,result,support,rolling,null,directory/'plots')
    meta=dict(cutoff=len(data),dataset_hash=dataset_hash,configuration=asdict(config),encoder=result['encoder'],
        search_space=result['space'],maxima=result['maxima'],replicates=replicates,seed=90042,
        runtime_seconds=perf_counter()-began,future_result_accessed=False,
        deferred='No arbitrary state transitions or continuous4D displacement geometry')
    (directory/'analysis_metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    if progress:progress(comparison.to_string(index=False))
    return meta

def run(args):
    if args.command=='freeze-joint':
        from src.phase9_freeze import freeze_joint
        from src.freeze_artifacts import digest
        paths=freeze_joint(args.data,args.reports_dir or ROOT/'reports/prospective/phase9')
        for name,path in paths.items():print(f'{name}: {path}\nSHA-256: {digest(path)}')
        return
    data,h=strict_source(args.data);directory=args.reports_dir or ROOT/'reports/spatiotemporal_joint';guard_reports(directory)
    if args.command=='analyze-joint':meta=analyze(data,directory,replicates=args.surrogates,dataset_hash=h,progress=lambda s:print(s,flush=True))
    else:
        from src.backtest.joint import comparison
        meta=comparison(data,directory/f'walk_forward_{args.cadence}',cadence=args.cadence,progress=lambda s:print(s,flush=True))
    print(f'Phase9 runtime {meta["runtime_seconds"]:.1f}s; dataset SHA256 {h}; no future result accessed.')
