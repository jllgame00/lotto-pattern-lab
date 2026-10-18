"""H25 inspection aids. No new statistics, tuning, or earlier-p aggregation."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .randomness_battery import TRACKS,SCOPES,FAMILIES
from .randomness_omnibus import SCORES,higher_criticism


def evidence_map(ledger,h25_status):
    ids=[h['id'] for h in ledger['hypotheses']];values=np.zeros((len(ids),3),int)
    for i,h in enumerate(ledger['hypotheses']):
        if h['status'] in ('DEFERRED','BACKLOG'):values[i]=-1
        elif h['id']=='H10':values[i,0]=2  # SSA corrected structure, no established predictive benefit.
        elif h['id']=='H12':values[i,0]=1  # One-null boundary, not robust rejection under both.
        elif h['id']=='H25' and h25_status!='TESTED / INCONCLUSIVE':values[i,0]=2
        if h['id'] in ('H12','H13','H16'):values[i,2]=2
        elif h['id']=='H2':values[i,2]=1  # Comparison baseline, not proven winner.
    return ids,values


def diagnostics(x,directory):
    from src.random_matrix_cli import dump
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap,BoundaryNorm
    directory=Path(directory);plots=directory/'plots';plots.mkdir(exist_ok=True)
    summary=json.loads((directory/'real_summary.json').read_text(encoding='utf-8'))
    metadata=json.loads((directory/'analysis_metadata.json').read_text(encoding='utf-8'))
    comparison=pd.read_csv(directory/'omnibus_comparison.csv');family=pd.read_csv(directory/'family_comparison.csv')
    pools={};units={}
    for track in TRACKS:
        with np.load(directory/f'battery_{track}_full.npz') as f:
            pools[track]={k:f[k] for k in ('z','p','scores','family_max','weights')}
        units[track]=pd.read_csv(directory/f'units_{track}_full.csv')
    def save(fig,name):
        fig.tight_layout();fig.savefig(plots/name,dpi=145);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,6))
    for track,color in [('iid','#2475a8'),('fixed_margins','#da9146')]:
        selected=family[(family.track==track)&(family.scope=='full')].set_index('family').reindex(FAMILIES)
        offset=-.18 if track=='iid' else .18;pos=np.arange(9)+offset
        axes[0].barh(pos,selected.real_max,height=.35,label=track,color=color)
        axes[1].barh(pos,selected.mean_bounded_anomaly,height=.35,label=track,color=color)
    for ax in axes:ax.set(yticks=range(9),yticklabels=FAMILIES);ax.legend()
    axes[0].set(title='Family maxima (oriented robust z)',xlabel='Maximum z')
    axes[1].set(title='Bounded anomaly mean within each family',xlabel='Mean clip(z-1,0,4)')
    save(fig,'01_family_overview.png')
    for number,track in [(2,'iid'),(3,'fixed_margins')]:
        fig,axes=plt.subplots(3,3,figsize=(12,10));names=summary[f'{track}_full']['family_names'];pool=pools[track]
        for j,ax in enumerate(axes.flat):
            if j>=len(names):ax.axis('off');continue
            ax.hist(pool['family_max'][1:,j],bins=24);ax.axvline(pool['family_max'][0,j],color='red',label='Real')
            ax.set(title=names[j],xlabel='Own family maximum z');ax.legend(fontsize=7)
        fig.suptitle(f'Real vs {track}:199 histories, peer-only normalization')
        save(fig,f'{number:02d}_{track}_family_maxima.png')
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for row,track in enumerate(TRACKS):
        pool=pools[track]
        axes[row,0].hist(pool['p'][0],bins=[0,.01,.025,.05,.1,.25,.5,1.00001],weights=pool['weights'])
        axes[row,0].set(title=f'{track}: empirical unit p',xlabel='p',ylabel='Equal-family probability mass')
        axes[row,1].hist(pool['z'][0],bins=45,weights=pool['weights'])
        axes[row,1].axvline(1,color='black',ls='--');axes[row,1].set(title=f'{track}: oriented unit anomalies',xlabel='z',ylabel='Equal-family probability mass')
    save(fig,'04_unit_anomalies.png')
    fig,axes=plt.subplots(2,2,figsize=(12,8));hc_rows=[]
    for row,track in enumerate(TRACKS):
        pool=pools[track];hc=higher_criticism(pool['p'][0],pool['weights'])
        axes[row,0].plot(hc['p_grid'],hc['curve']);axes[row,0].axhline(0,color='gray');axes[row,0].set(title=f'{track}: weighted HC curve',xlabel='Empirical unit p threshold',ylabel='HC-style score')
        axes[row,1].hist(pool['scores'][1:,2],bins=25);axes[row,1].axvline(pool['scores'][0,2],color='red',label='Real')
        axes[row,1].set(title=f'{track}: HC null calibration',xlabel='HC-style maximum');axes[row,1].legend()
        hc_rows.extend(dict(track=track,p=float(p),curve=float(c),weighted_cdf=float(v)) for p,c,v in zip(hc['p_grid'],hc['curve'],hc['cdf']))
    pd.DataFrame(hc_rows).to_csv(directory/'hc_curve.csv',index=False);save(fig,'05_higher_criticism.png')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for ax,track in zip(axes,TRACKS):
        pool=pools[track];ax.hist(pool['scores'][1:,1],bins=25);ax.axvline(pool['scores'][0,1],color='red',label='Real')
        ax.set(title=track,xlabel='Equal-family sum of bounded anomalies');ax.legend()
    save(fig,'06_sum_anomalies.png')
    fig,axes=plt.subplots(2,3,figsize=(12,7))
    for row,track in enumerate(TRACKS):
        for j,name in enumerate(SCORES):
            a=pools[track]['scores'];ax=axes[row,j];ax.hist(a[1:,j],bins=25);ax.axvline(a[0,j],color='red',label='Real')
            r=comparison[(comparison.track==track)&(comparison.scope=='full')&(comparison.score==name)].iloc[0]
            ax.set(title=f'{track} / {name}',xlabel=f'global p={r.global_p:.3f}; corrected6={r.overall_adjusted_p:.3f}');ax.legend(fontsize=7)
    save(fig,'07_omnibus_comparison.png')
    fig,axes=plt.subplots(1,3,figsize=(13,4));era_rows=[]
    for j,name in enumerate(SCORES):
        for track,color,offset in [('iid','#2475a8',-.08),('fixed_margins','#da9146',.08)]:
            real_values=[];low=[];high=[]
            for scope in ('early','middle','recent'):
                with np.load(directory/f'battery_{track}_{scope}.npz') as f:values=f['scores'][:,j]
                q=np.quantile(values[1:],[.05,.95]);real_values.append(values[0]);low.append(q[0]);high.append(q[1])
                r=comparison[(comparison.track==track)&(comparison.scope==scope)&(comparison.score==name)].iloc[0]
                era_rows.append(dict(track=track,scope=scope,score=name,real=values[0],null05=q[0],null95=q[1],global_p=r.global_p,corrected18=r.era_scan_adjusted_p))
            pos=np.arange(3)+offset;axes[j].plot(pos,real_values,'o-',color=color,label=track)
            axes[j].vlines(pos,low,high,color=color,alpha=.45,lw=5)
        axes[j].set(title=name,xticks=range(3),xticklabels=['early','middle','recent'],ylabel='Score (bands: null5-95%)');axes[j].legend(fontsize=7)
    pd.DataFrame(era_rows).to_csv(directory/'era_robustness.csv',index=False);save(fig,'08_era_robustness.png')
    fig,axes=plt.subplots(2,1,figsize=(13,8))
    for ax,track in zip(axes,TRACKS):
        leave=pd.read_csv(directory/f'leave_family_out_{track}.csv');names=list(dict.fromkeys(leave.removed_family))
        for name in SCORES:
            selected=leave[leave.score==name].set_index('removed_family').loc[names]
            ax.plot(range(len(names)),selected.global_p,'o-',label=name)
        ax.set(title=f'{track}: leave-one-family-out, descriptive only',xticks=range(len(names)),xticklabels=names,ylim=(0,1.05),ylabel='Empirical p (uncorrected)')
        ax.tick_params(axis='x',rotation=25);ax.legend(fontsize=7)
    save(fig,'09_leave_family_out.png')
    ledger=json.loads((Path(__file__).resolve().parents[2]/'docs/weak-signal-candidates.json').read_text(encoding='utf-8'))
    ids,matrix=evidence_map(ledger,metadata['status'])
    cmap=ListedColormap(['#dddddd','#edf0f5','#e4bd70','#6fa4b9']);norm=BoundaryNorm([-1.5,-.5,.5,1.5,2.5],4)
    fig,ax=plt.subplots(figsize=(11,12));ax.imshow(matrix,cmap=cmap,norm=norm,aspect='auto')
    ax.set(yticks=range(len(ids)),yticklabels=ids,xticks=range(3),xticklabels=['Scientific corrected structure','Established predictive superiority','Ensemble bookkeeping'])
    for i,h in enumerate(ids):
        for j in range(3):
            value=matrix[i,j];label='deferred' if value==-1 else 'none established' if value==0 else ('one-null boundary' if j==0 else 'baseline') if value==1 else ('SSA / corrected' if h=='H10' and j==0 else 'corrected battery' if h=='H25' and j==0 else 'exploratory candidate')
            ax.text(j,i,label,ha='center',va='center',fontsize=8)
    ax.set_title('Descriptive evidence map: separate claims, no p-value combination')
    save(fig,'10_evidence_map.png')
    dump(directory/'diagnostics_summary.json',dict(plots=10,score_names=list(SCORES),tracks=list(TRACKS),
        evidence_map_descriptive_only=True,era_triple_expected_below_support=True,publication_executed=False))
    print('H25 diagnostics:10plots and robustness tables saved',flush=True)
