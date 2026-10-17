"""H13 inspection plots and fixed-candidate historical diagnostics."""
import json
import numpy as np
import pandas as pd
from src.analysis.modular_space import MODULI,LAGS,representation as modular,transition
from src.analysis.difference_space import representation as difference,absolute_relation,shape_successor
from src.analysis.transformed_search import correlation
from src.recurrence_cli import dump


def plots(x,directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from src.backtest.transformed_space import load_selection,factories,PRIMARY_MODELS,OPTIONAL_MODELS
    out=directory/'plots';out.mkdir(exist_ok=True)
    real=json.loads((directory/'real_maxima.json').read_text());s=load_selection(directory/'selected_configuration.json')
    null=pd.read_csv(directory/'null_maxima.csv')
    def save(name):plt.tight_layout();plt.savefig(out/name,dpi=150);plt.close()
    fig,axes=plt.subplots(2,3,figsize=(12,7))
    for k,ax in zip(MODULI,axes.ravel()):
        r=modular(x,k);ax.bar(np.arange(k)-.15,r['histogram'].mean(0),width=.3,label='Real/draw')
        ax.bar(np.arange(k)+.15,r['expected'],width=.3,label='IID exact');ax.set_title(f'mod{k}');ax.set_xlabel('Residue');ax.legend()
    save('residue_distribution_overview.png')
    c=real['leaders']['modular_temporal'];r=modular(x,c['modulus']);series=r[c['feature']];lag=c['lag']
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    axes[0].plot(np.arange(1,len(x)+1),series,alpha=.7);axes[0].set_xlabel('Draw');axes[0].set_title(f"mod{c['modulus']} {c['feature']}")
    axes[1].scatter(series[:-lag].ravel(),series[lag:].ravel(),alpha=.1,s=10);axes[1].set_xlabel(f'Source t-{lag}');axes[1].set_ylabel('Future t')
    axes[1].set_title(f"Selected |r|={c['value']:.3f}; full search corrected separately")
    save('strongest_residue_temporal.png')
    def null_plot(families,name):
        fig,axes=plt.subplots(2,len(families),figsize=(5*len(families),6),squeeze=False)
        for row,kind in enumerate(('iid','fixed_margins')):
            for ax,family in zip(axes[row],families):
                ax.hist(null[null.null_model==kind][family],bins=18);ax.axvline(real['maxima'][family],color='red')
                ax.set_title(f'{kind}: {family}');ax.set_xlabel('Complete-search global maximum')
        save(name)
    null_plot(['modular_structure','modular_temporal','modular_successor'],'modular_real_vs_null.png')
    d=difference(x)
    pair_observed=d['pair_histogram'].sum(0);pair_expected=len(x)*d['pair_expected']
    pd.DataFrame(dict(distance=np.arange(1,45),opportunities=d['opportunities'],pair_observed=pair_observed,
        pair_expected=pair_expected,pair_lift=pair_observed/pair_expected,
        pair_per_opportunity=pair_observed/d['opportunities'],iid_per_opportunity=len(x)/66,
        adjacent_observed=d['adjacent_histogram'].sum(0),adjacent_expected=len(x)*d['adjacent_expected'])).to_csv(directory/'within_draw_distribution.csv',index=False)
    fig,axes=plt.subplots(2,1,figsize=(11,7))
    for ax,key,expected in zip(axes,['pair_histogram','adjacent_histogram'],['pair_expected','adjacent_expected']):
        ax.plot(np.arange(1,45),d[key].sum(0),label='Real');ax.plot(np.arange(1,45),len(x)*d[expected],label='IID exact')
        ax.set_xlabel('Absolute difference / adjacent gap');ax.set_title(key);ax.legend()
    save('absolute_difference_expectation.png')
    values=np.array([absolute_relation(x,lag)['z'][1:] for lag in LAGS]);limit=np.abs(values).max()
    plt.figure(figsize=(12,4));plt.imshow(values,aspect='auto',cmap='coolwarm',vmin=-limit,vmax=limit,extent=(.5,44.5,6.5,-.5))
    plt.yticks(range(7),LAGS);plt.xlabel('Absolute distance (d0 reference excluded)');plt.ylabel('Lag');plt.colorbar(label='Conditional normalized count z')
    save('lag_distance_heatmap.png')
    temporal=[];c=real['leaders']['distance'];mod=real['leaders']['modular_temporal'];successor=real['leaders']['modular_successor']
    intervals=[('early',1,415),('middle',416,830),('recent',831,1245)]+[('rolling',end-207,end) for end in range(208,1246,52)]
    for era,start,end in intervals:
        prefix=x[start-1:end];a=absolute_relation(prefix,c['lag']);distance=c['distance']
        r=modular(prefix,mod['modulus']);series=r[mod['feature']];lag=mod['lag']
        t=transition(prefix,successor['modulus'],successor['lag']);rr=successor['residue'];state=successor['source_count']
        temporal.append(dict(era=era,start=start,end=end,distance=distance,lag=c['lag'],
            distance_z=float(a['z'][distance]),observed=int(a['observed'][distance]),expected=float(a['expected'][distance]),
            modular_modulus=mod['modulus'],modular_lag=lag,modular_feature=mod['feature'],
            modular_correlation=correlation(series[:-lag],series[lag:],columns=mod['feature']=='histogram'),
            successor_support=int(t['counts'][rr,state]),successor_eligible=bool(t['eligible'][rr,state]),
            successor_z=float(t['z'][rr,state]) if t['eligible'][rr,state] else None))
    dump(directory/'temporal_diagnostics.json',temporal);rolling=pd.DataFrame([r for r in temporal if r['era']=='rolling'])
    fig,axes=plt.subplots(2,1,figsize=(11,6));axes[0].plot(rolling.end,rolling.distance_z);axes[0].axhline(0,color='grey')
    axes[0].set_title(f"Selected lag{c['lag']} /distance{c['distance']}; W208 descriptive trace");axes[0].set_ylabel('Normalized count z')
    axes[1].plot(rolling.end,rolling.modular_correlation);axes[1].set_ylabel('Selected residue correlation');axes[1].set_xlabel('Window endpoint')
    save('strongest_distance_through_time.png')
    plt.figure(figsize=(7,5));plt.scatter(d['normalized_gaps'][:,0],d['normalized_gaps'][:,1],c=np.arange(1,len(x)+1),cmap='viridis',s=12,alpha=.6)
    plt.colorbar(label='Draw');plt.xlabel('Gap1/range');plt.ylabel('Gap2/range');plt.title('First two of five normalized gap coordinates (descriptive)')
    save('adjacent_gap_projection.png');null_plot(['distance','shape'],'difference_real_vs_null.png')
    rows=pd.read_csv(directory/'walk_forward_26/predictions.csv');models=factories(s)
    names=[name for name in (*PRIMARY_MODELS,*OPTIONAL_MODELS) if name in models];examples={}
    fig,axes=plt.subplots(len(names),1,figsize=(12,3*len(names)),squeeze=False)
    for name,ax in zip(names,axes.ravel()):
        row=rows[(rows.model==name)&(rows.target_draw==1245)].iloc[0];scores=json.loads(row.scores);ranking=json.loads(row.ranking)
        m=models[name]().fit(x[:1244],cutoff=1244);rep=m.score_matrix(x[:1244],target=1245)
        if any(rep[n]!=scores[str(n)] for n in range(1,46)):raise ValueError('Historical score reproduction mismatch')
        examples[name]=dict(target=1245,training_cutoff=1244,ranking=ranking,diagnostic=m.last_diagnostic)
        ax.bar(np.arange(45),[rep[n] for n in ranking]);ax.set_xticks(np.arange(45),ranking,fontsize=7);ax.set_title(f'{name}: historical1245 using<=1244')
    save('model_ranking_example.png');dump(directory/'historical_ranking_example.json',examples)
    diversity=pd.read_csv(directory/'walk_forward_26/rank_diversity.csv');table=diversity.groupby(['model','reference']).spearman.mean().unstack()
    table.plot.bar(figsize=(11,5));plt.axhline(0,color='grey');plt.ylabel('Mean number-coordinate Spearman');plt.xticks(rotation=10)
    save('rank_correlation_comparison.png');shape=[]
    for K in (10,25):
        t=shape_successor(x,K);shape.append(dict(K=K,score=t['score'],queries=len(t['rows']),
            mean_gain=float(t['gains'].mean()),mean_nearest_distance=float(np.mean([r['nearest_distance'] for r in t['rows']])),
            mean_baseline_distance=float(np.mean([r['baseline_distance'] for r in t['rows']]))))
    dump(directory/'shape_diagnostic.json',shape)
