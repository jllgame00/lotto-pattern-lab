"""H23 inspection aids. Era/rolling summaries are descriptive, not extra tests."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .optimal_transport import (LAGS, draw_positions, displacement_summary, lag_distances,
    direction, acceleration, correlation, geodesic_residual, quantile_distance)
from .optimal_transport_search import FAMILIES, metric_vector


def distribution(v):
    a = np.asarray(v,float)
    return dict(count=len(a),mean=float(a.mean()),std=float(a.std()),minimum=float(a.min()),
                q05=float(np.quantile(a,.05)),median=float(np.median(a)),q95=float(np.quantile(a,.95)),maximum=float(a.max()))


def descriptive_summary(x, raw=None):
    raw = metric_vector(x,details=True) if raw is None else raw
    a = raw['positions']; d = raw['transports']; w1 = abs(d).mean(1)
    direct = direction(d[:-1],d[1:]); movement = displacement_summary(d)
    quartiles = np.quantile(w1[:-1],[.25,.5,.75]); bins = np.digitize(w1[:-1],quartiles)
    bary = {}
    for (w,p),r in raw['barycenters'].items():
        bary[f'{w}_W{p}'] = dict(first_target=int(r['target_draws'][0]),
            next_mean=float(r['next_distance'].mean()),recent_mean=float(r['recent_distance'].mean()),
            unconditional_mean=float(r['unconditional_distance'].mean()),gain=float(r['gain'].mean()),
            movement_mean=float(r['movement'].mean()),
            sorted_mean_max_difference=float(abs(r['barycenters']-r['sorted_mean_baseline']).max()))
    successor = {}
    for metric,r in raw['successors'].items():
        successor[metric] = {name:float(np.mean(r[name])) for name in ('cosine_relation','distance_relation',
            'nearest_distance','cosine_gain','distance_gain','nearest_next_cosine','nearest_next_distance')}
        successor[metric]['pairs'] = len(r['pair_distance'])
        successor[metric]['nearest_queries'] = len(r['query_indices'])
    return dict(draws=len(a),consecutive_W1=distribution(w1),consecutive_W2=distribution(lag_distances(a,1,2)),
        lags={str(l):distribution(lag_distances(a,l,1)) for l in LAGS},
        displacement={k:float(np.mean(v)) for k,v in movement.items()},
        magnitude_memory={str(l):correlation(w1[:-l],w1[l:]) for l in LAGS},
        conditional_bins=[dict(bin=i,count=int((bins==i).sum()),next_W1=float(w1[1:][bins==i].mean())) for i in range(4)],
        direction={k:float(v.mean()) for k,v in direct.items()},successor=successor,
        drift={f'{w}_{s}':distribution(r['distance']) for (w,s),r in raw['drift'].items()},barycenter=bary,
        geodesic=dict(W1=distribution(geodesic_residual(a,1)),W2=distribution(geodesic_residual(a,2)),descriptive_only=True),
        acceleration=dict(absolute=float(abs(acceleration(d)).mean()),rms=float(np.sqrt(np.mean(acceleration(d)**2,axis=1)).mean())))


def diagnostics(x,directory):
    from src.random_matrix_cli import dump
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory = Path(directory); plots = directory/'plots'; plots.mkdir(exist_ok=True)
    raw = metric_vector(x,details=True); summary = descriptive_summary(x,raw)
    dump(directory/'descriptive_summary.json',summary)
    a = raw['positions']; d = raw['transports']; w1 = abs(d).mean(1)
    movement = displacement_summary(d)
    pd.DataFrame(dict(from_draw=np.arange(1,len(a)),to_draw=np.arange(2,len(a)+1),
        W1=w1,W2=lag_distances(a,1,2),**movement,**{f'd{i+1}':d[:,i] for i in range(6)})).to_csv(directory/'consecutive_transport.csv',index=False)
    drift_rows = []
    for (w,s),r in raw['drift'].items():
        drift_rows.extend(dict(window=w,step=s,endpoint=int(e),W1=float(v)) for e,v in zip(r['endpoints'],r['distance']))
    pd.DataFrame(drift_rows).to_csv(directory/'rolling_drift.csv',index=False)
    bary_rows, recent_rows = [], []
    for (w,p),r in raw['barycenters'].items():
        for i,t in enumerate(r['target_draws']):
            bary_rows.append(dict(window=w,p=p,target_draw=int(t),next_distance=r['next_distance'][i],
                unconditional_distance=r['unconditional_distance'][i],recent_distance=r['recent_distance'][i],
                **{f'q{j+1}':r['barycenters'][i,j] for j in range(6)}))
            distances = quantile_distance(a[t-w-1:t-1], r['barycenters'][i], p)
            recent_rows.extend(dict(window=w,p=p,training_endpoint=int(t-1),recent_draw=int(draw),distance=float(v))
                               for draw,v in zip(range(t-w,t),distances))
    pd.DataFrame(bary_rows).to_csv(directory/'barycenters.csv',index=False)
    pd.DataFrame(recent_rows).to_csv(directory/'barycenter_recent_distances.csv',index=False)
    for metric,r in raw['successors'].items():
        pd.DataFrame(dict(query_transport=r['query_indices'],neighbor_transport=r['neighbor_indices'],
            query_from_draw=r['query_indices']+1,query_to_draw=r['query_indices']+2,
            next_target_draw=r['query_indices']+3,neighbor_next_draw=r['neighbor_indices']+3,
            nearest_distance=r['nearest_distance'],next_cosine=r['nearest_next_cosine'],
            next_distance=r['nearest_next_distance'],cosine_gain=r['cosine_gain'],distance_gain=r['distance_gain'])).to_csv(directory/f'successor_{metric}.csv',index=False)
    era_rows,rolling_rows = [],[]
    for name,lo,hi in [('early',0,415),('middle',415,830),('recent',830,1245)]:
        part = metric_vector(x[lo:hi])
        era_rows.extend(dict(era=name,start=lo+1,end=hi,key=k,value=float(v)) for k,v in zip(part['keys'],part['values']))
    endpoints = sorted(set(range(208,len(x)+1,52))|{len(x)})
    for end in endpoints:
        part = metric_vector(x[end-208:end])
        rolling_rows.extend(dict(start=end-207,end=end,key=k,value=float(v)) for k,v in zip(part['keys'],part['values']))
    pd.DataFrame(era_rows).to_csv(directory/'era_metrics.csv',index=False)
    pd.DataFrame(rolling_rows).to_csv(directory/'rolling_metrics.csv',index=False)
    def save(fig,name):
        fig.tight_layout(); fig.savefig(plots/name,dpi=145); plt.close(fig)
    fig,ax = plt.subplots(figsize=(9,4))
    for i in range(6):
        ax.plot([a[0,i],a[1,i]],[0,1],marker='o',label=f'quantile {i+1}')
    ax.set(xlim=(0,46),yticks=[0,1],yticklabels=['Draw1','Draw2'],xlabel='Number axis1..45',title='Exact monotone transport, mass1/6 per position')
    ax.legend(ncol=3,fontsize=8); save(fig,'01_monotone_transport.png')
    fig,ax = plt.subplots(figsize=(8,4)); ax.hist(w1,bins=35,color='#287b9b')
    ax.axvline(w1.mean(),color='black',label=f'mean {w1.mean():.3f}'); ax.legend()
    ax.set(xlabel='Consecutive W1',ylabel='Count',title='Draw-to-draw transport magnitude'); save(fig,'02_consecutive_w1.png')
    fig,ax = plt.subplots(figsize=(8,4))
    ax.boxplot([lag_distances(a,l,1) for l in LAGS],tick_labels=[str(l) for l in LAGS],showfliers=False)
    ax.set(xlabel='Temporal lag',ylabel='W1',title='Predeclared temporal lags'); save(fig,'03_w1_lags.png')
    fig,axes = plt.subplots(1,2,figsize=(11,4)); direct = direction(d[:-1],d[1:])
    axes[0].hist(direct['cosine'],bins=30); axes[0].axvline(direct['cosine'].mean(),color='red')
    axes[0].set(title='Consecutive transport cosine',xlabel='Cosine: reversal <0 < persistence')
    with np.load(directory/'null_metrics_full.npz') as f: null_raw = f['values']
    index = raw['keys'].index('direction|cosine_lag1')
    axes[1].hist(null_raw[:199,index],bins=22,alpha=.6,label='IID')
    axes[1].hist(null_raw[199:,index],bins=22,alpha=.6,label='Fixed margins')
    axes[1].axvline(raw['values'][index],color='black',label='Real'); axes[1].legend()
    axes[1].set(title='Mean cosine: null comparison',xlabel='Uncorrected descriptive cell')
    save(fig,'04_direction_persistence.png')
    fig,axes = plt.subplots(1,2,figsize=(11,4))
    for ax,metric in zip(axes,('euclidean','cosine')):
        r = raw['successors'][metric]
        ax.hexbin(r['pair_distance'],r['pair_next_cosine'],gridsize=35,mincnt=1,cmap='viridis')
        ax.set(title=f"{metric}: rho={-r['cosine_relation']:.3f}",xlabel='Transport vector distance',ylabel='Next transport cosine')
    save(fig,'05_successor.png')
    fig,axes = plt.subplots(3,1,figsize=(11,8))
    for ax,w in zip(axes,(26,52,104)):
        for step in (1,4,13,26):
            r = raw['drift'][w,step]; ax.plot(r['endpoints'],r['distance'],label=f'step{step}',lw=.8)
        ax.set(title=f'Rolling distribution W{w}',ylabel='W1'); ax.legend(ncol=4,fontsize=8)
    axes[-1].set_xlabel('Completed endpoint'); save(fig,'06_rolling_drift.png')
    fig,axes = plt.subplots(3,1,figsize=(11,8))
    for ax,w in zip(axes,(10,26,52)):
        r = raw['barycenters'][w,1]
        ax.plot(r['target_draws']-1,r['barycenters'],lw=.8); ax.set(title=f'W2 barycenter / mean quantiles, W{w}',ylabel='Position')
    axes[-1].set_xlabel('Training endpoint'); save(fig,'07_barycenter_trajectory.png')
    fig,axes = plt.subplots(1,3,figsize=(12,4))
    for ax,w in zip(axes,(10,26,52)):
        r = raw['barycenters'][w,1]
        ax.hist(r['next_distance'],bins=25,alpha=.6,label='Next to rolling center')
        ax.hist(r['unconditional_distance'],bins=25,alpha=.5,label='Next to prior global mean')
        ax.set(title=f'Window{w}',xlabel='W1'); ax.legend(fontsize=7)
    save(fig,'08_next_barycenter_distance.png')
    maxima = pd.read_csv(directory/'null_maxima.csv')
    real = json.loads((directory/'real_summary.json').read_text(encoding='utf-8'))['full']
    for number,kind in [(9,'iid'),(10,'fixed_margins')]:
        fig,axes = plt.subplots(2,3,figsize=(12,7)); subset=maxima[(maxima.scope=='full')&(maxima.null_model==kind)]
        for ax,family in zip(axes.flat,FAMILIES):
            ax.hist(subset[family],bins=24,alpha=.8); ax.axvline(real['maxima'][family],color='red',label='Real')
            ax.set(title=family,xlabel='Own complete-search maximum |z|'); ax.legend(fontsize=8)
        fig.suptitle(f'Real vs {kind},199 rebuilt histories'); save(fig,f'{number:02d}_{kind}_global_max.png')
    # Additional descriptive geodesic/acceleration inspection, never a predictor.
    fig,axes = plt.subplots(1,2,figsize=(10,4))
    axes[0].hist(geodesic_residual(a),bins=30); axes[0].set(title='Geodesic midpoint residual (future used)',xlabel='W1 residual')
    axes[1].plot(np.arange(3,len(a)+1),abs(acceleration(d)).mean(1),lw=.6)
    axes[1].set(title='Transport acceleration',xlabel='Draw',ylabel='Mean absolute acceleration')
    save(fig,'11_geodesic_acceleration.png')
    print('H23 diagnostics:11 plots and descriptive tables saved',flush=True)
