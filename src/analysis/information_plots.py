"""H11 inspection plots; no graph inference or community analysis."""
import json
import numpy as np
import pandas as pd
from src.analysis.information import LAGS,HISTORIES,mi_matrix,te_matrix
from src.backtest.information_flow import load_selection,construct
from src.recurrence_cli import dump


def temporal_diagnostics(x,leaders):
    rows=[];ends=list(range(416,1246,104))
    if ends[-1]!=1245:ends.append(1245)
    spans=[('early',1,415),('middle',416,830),('recent',831,1245)]+[('rolling',e-415,e) for e in ends]
    for family,leader in leaders.items():
        i,j=leader['source']-1,leader['target']-1
        for era,start,end in spans:
            small=x[start-1:end][:,[i,j]];lag=leader['lag'];k,l=leader['k'],leader['l']
            result=mi_matrix(small,lag) if family=='mi' else te_matrix(small,lag,k,l)
            rows.append(dict(family=family,source=i+1,target=j+1,lag=lag,k=k,l=l,era=era,start=start,end=end,
                samples=result['samples'],forward=float(result['raw'][0,1]),reverse=float(result['raw'][1,0]),
                corrected=float(result['corrected'][0,1]),eligible=bool(result['eligible'][0,1]),
                reverse_eligible=bool(result['eligible'][1,0]),occupied=int(result['occupied'][0,1]),
                sparse=bool(result['sparse'][0,1])))
    return pd.DataFrame(rows)


def conditional_diagnostics(x,leaders):
    """MLE uncertainty reduction for selected descriptive pairs, not future skill."""
    result=[]
    def conditional_entropy(counts):
        total=counts.sum();support=counts.sum(-1)
        p=np.divide(counts,support[...,None],out=np.zeros_like(counts,dtype=float),where=support[...,None]>0)
        log=np.zeros_like(p);np.log2(p,out=log,where=p>0)
        return float(-np.sum(counts*log)/total)
    for family in ('cmi','te','asymmetry','stable_te'):
        c=leaders[family];small=x[:,[c['source']-1,c['target']-1]]
        table=te_matrix(small,c['lag'],c['k'],c['l']);counts=table['counts'][0,1]
        baseline=conditional_entropy(counts.sum(0));with_source=conditional_entropy(counts)
        result.append(dict(family=family,source=c['source'],target=c['target'],lag=c['lag'],k=c['k'],l=c['l'],
            samples=table['samples'],target_history_entropy=baseline,source_added_entropy=with_source,
            in_sample_gain_bits=baseline-with_source,raw_te=float(table['raw'][0,1]),
            corrected_te=float(table['corrected'][0,1]),sparse=bool(table['sparse'][0,1]),
            occupied=int(table['occupied'][0,1]),prediction_evidence=False))
    return pd.DataFrame(result)


def plots(x,directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch
    out=directory/'plots';out.mkdir(exist_ok=True)
    real=json.loads((directory/'real_maxima.json').read_text());leaders=real['leaders']
    conditional_diagnostics(x,leaders).to_csv(directory/'conditional_information_diagnostic.csv',index=False)
    def save(name):
        plt.tight_layout();plt.savefig(out/name,dpi=150);plt.close()
    def heatmap(matrix,mask,title,name,symmetric=False):
        plt.figure(figsize=(8,7));m=np.where(mask,matrix,np.nan)
        bound=max(float(np.nanmax(np.abs(m))) if np.isfinite(m).any() else 0.,1e-9)
        plt.imshow(m,cmap='coolwarm' if symmetric else 'magma',vmin=-bound if symmetric else 0,vmax=bound,origin='lower')
        ticks=np.arange(0,45,4);plt.xticks(ticks,ticks+1);plt.yticks(ticks,ticks+1)
        plt.xlabel('Target number');plt.ylabel('Source number');plt.title(title);plt.colorbar(label='bits')
        save(name)
    cross=~np.eye(45,dtype=bool)
    c=leaders['mi'];r=mi_matrix(x,c['lag'])
    heatmap(r['raw'],r['eligible']&cross,f"Lagged MI, lag{c['lag']}; descriptive global winner",'mi_matrix.png')
    c=leaders['te'];r=te_matrix(x,c['lag'],c['k'],c['l'])
    heatmap(r['raw'],r['eligible']&cross,f"TE lag{c['lag']} k{c['k']} l{c['l']}; descriptive",'te_directed_matrix.png')
    c=leaders['asymmetry'];r=te_matrix(x,c['lag'],c['k'],c['l'])
    heatmap(r['raw']-r['raw'].T,r['eligible']&r['eligible'].T&cross,
        f"TE forward-minus-reverse lag{c['lag']} k{c['k']} l{c['l']}",'te_asymmetry.png',symmetric=True)
    profile=[];c=leaders['te'];small=x[:,[c['source']-1,c['target']-1]]
    for lag in LAGS:
        for k,l in HISTORIES:
            r=te_matrix(small,lag,k,l)
            profile.append(dict(lag=lag,k=k,l=l,forward=float(r['raw'][0,1]),reverse=float(r['raw'][1,0]),
                eligible=bool(r['eligible'][0,1]),samples=r['samples']))
    frame=pd.DataFrame(profile);frame.to_csv(directory/'strongest_pair_lag_profile.csv',index=False)
    plt.figure(figsize=(10,4))
    for (k,l),g in frame.groupby(['k','l']):plt.plot(g.lag,g.forward,'o-',label=f'k{k} l{l}')
    plt.xlabel('Source lag');plt.ylabel('TE bits');plt.title(f"Descriptive pair {c['source']} -> {c['target']}");plt.legend()
    save('strongest_pair_lag_profile.png')
    temporal=temporal_diagnostics(x,leaders);temporal.to_csv(directory/'candidate_temporal_stability.csv',index=False)
    fig,axes=plt.subplots(2,1,figsize=(11,6))
    for family in ('te','stable_te'):
        g=temporal[(temporal.family==family)&(temporal.era=='rolling')]
        axes[0].plot(g.end,np.where(g.eligible,g.forward,np.nan),'o-',label=f'{family} leader forward')
        axes[0].plot(g.end,np.where(g.reverse_eligible,g.reverse,np.nan),'--',label=f'{family} leader reverse')
        axes[1].plot(g.end,np.where(g.eligible,g.corrected,np.nan),'o-',label=family)
    axes[0].set_ylabel('Raw TE bits');axes[0].legend();axes[1].set_ylabel('MM corrected TE');axes[1].set_xlabel('416-draw window endpoint');axes[1].legend()
    save('strongest_pair_temporal_stability.png')
    null=pd.read_csv(directory/'null_maxima.csv')
    for kind in ('iid','fixed_margins'):
        fig,axes=plt.subplots(1,5,figsize=(16,3))
        for ax,family in zip(axes,real['maxima']):
            ax.hist(null[null.null_model==kind][family],bins=20,color='steelblue');ax.axvline(real['maxima'][family],color='red')
            ax.set_title(family);ax.set_xlabel('Global maximum')
        fig.suptitle(f'Real (red) versus {kind}: complete-search maxima');save(f'real_vs_{kind}.png')
    # Inspection-only frozen TE configuration, trained before target901.
    selection=load_selection(directory/'selected_configuration.json');cfg=selection['models']['TransferEntropyModel']
    past=x[:900][-624:];table=te_matrix(past,cfg['lag'],cfg['k'],cfg['l'])
    mask=table['eligible']&cross&(table['corrected']>0);order=np.argsort(-np.where(mask,table['corrected'],-np.inf).ravel(),kind='stable')
    edges=[]
    for flat in order[:10]:
        i,j=np.unravel_index(flat,(45,45))
        if mask[i,j]:edges.append(dict(source=int(i+1),target=int(j+1),corrected=float(table['corrected'][i,j]),training_cutoff=900))
    pd.DataFrame(edges,columns=['source','target','corrected','training_cutoff']).to_csv(directory/'inspection_edges.csv',index=False)
    fig,ax=plt.subplots(figsize=(9,9));theta=2*np.pi*np.arange(45)/45;pos=np.column_stack((np.cos(theta),np.sin(theta)))
    ax.scatter(pos[:,0],pos[:,1],s=160,color='lightgrey',zorder=3)
    for n,p in enumerate(pos,1):ax.text(*p,str(n),ha='center',va='center',fontsize=8,zorder=4)
    maximum=max([e['corrected'] for e in edges],default=1.)
    for edge in edges:
        a,b=pos[edge['source']-1],pos[edge['target']-1]
        ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=12,shrinkA=9,shrinkB=9,
            connectionstyle='arc3,rad=0.10',linewidth=.8+2*edge['corrected']/maximum,color='teal',alpha=.65))
    ax.set_aspect('equal');ax.axis('off');ax.set_title('Exploratory information edges; training <=900\nMM weights; global significance is tested separately')
    save('information_flow_inspection.png')
    rows=pd.read_csv(directory/'walk_forward_26/predictions.csv');fig,axes=plt.subplots(2,1,figsize=(12,6));examples={}
    for ax,name in zip(axes,['MutualInformationModel','TransferEntropyModel']):
        row=rows[(rows.model==name)&(rows.target_draw==1245)].iloc[0];scores=json.loads(row.scores);ranking=json.loads(row.ranking)
        model=construct(selection['models'][name]).fit(x[:1244],cutoff=1244)
        reproduced=model.score_matrix(x[:1244],target=1245)
        if any(reproduced[n]!=scores[str(n)] for n in range(1,46)):raise ValueError('Historical score reproduction mismatch')
        examples[name]=dict(target=1245,information_training_cutoff=1244,ranking=ranking,diagnostic=model.last_diagnostic)
        ax.bar(np.arange(45),[scores[str(n)] for n in ranking]);ax.set_xticks(np.arange(45),ranking,fontsize=7)
        ax.set_title(f'{name}; historical target1245, only <=1244');ax.set_ylabel('Smoothed score')
    save('model_ranking_example.png');dump(directory/'historical_ranking_example.json',examples)
    loss=pd.read_csv(directory/'walk_forward_26/conditional_logloss.csv')
    plt.figure(figsize=(11,4));plt.plot(loss.target_draw,loss.difference.rolling(26,min_periods=26).mean())
    plt.axhline(0,color='grey');plt.xlabel('Target draw');plt.ylabel('26-draw mean logloss difference\nTE - target-history baseline');save('source_added_logloss.png')
