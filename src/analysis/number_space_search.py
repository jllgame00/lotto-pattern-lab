"""Identical complete finite-axis searches for real and surrogate histories."""
from functools import lru_cache
from collections import Counter
import numpy as np
import pandas as pd
from src.analysis.spatiotemporal import iid_surrogate,constrained_surrogate
from src.analysis.number_space import (matrix,WINDOWS,WIDTHS,KERNELS,METRICS,
    rolling_counts,range_arrays,range_history,smooth,smooth_z,zone_history,movement,
    draw_statistics,search_space,strong_zones)

FAMILIES=('range_density','neighborhood','persistence','movement','spacing_clustering','spacing_motif')


@lru_cache(maxsize=1)
def spacing_reference():
    # Independent Monte Carlo reference, not estimated from the historical data.
    frames=[draw_statistics(iid_surrogate(1000,seed=1010+i),details=False) for i in range(50)]
    sample=pd.concat(frames,ignore_index=True)
    return dict(mean=sample[list(METRICS)].mean().to_numpy(),std=sample[list(METRICS)].std(ddof=0).to_numpy(),sample=sample)


def complete_search(x,reference=None,*,details=False):
    x=matrix(x);space=search_space(len(x));reference=spacing_reference() if reference is None else reference
    maxima={key:0. for key in FAMILIES};density=[];leaders=[];zones=[];motions=[];peaks=[];activity=[]
    for window in WINDOWS:
        counts=rolling_counts(x,window);rate=counts/window
        for width in WIDTHS:
            totals,z=range_arrays(x,window,width)
            maxima['range_density']=max(maxima['range_density'],float(z.max()))
            history=zone_history(x,window=window,width=width)
            metrics=movement(history.center.to_numpy(),width=width)
            maxima['persistence']=max(maxima['persistence'],metrics['identical_run'])
            maxima['movement']=max(maxima['movement'],metrics['direction_run'])
            if details:
                table=range_history(x,window=window,width=width);density.append(table);zones.append(history)
                top=table.sort_values(['raw_z','end_draw','start_number'],ascending=[False,True,True]).drop_duplicates(['start_number','end_number']).head(3)
                leaders.append(top);_,grouped=strong_zones(table[table.end_draw==len(x)])
                motions.append(dict(window=window,width=width,latest_grouped_zones=str(grouped),**metrics))
        for kernel in KERNELS:
            for neighbor in (False,True) if kernel!='none' else (False,):
                z=smooth_z(rate,kernel,window,neighbor_only=neighbor)
                maxima['neighborhood']=max(maxima['neighborhood'],float(z.max()))
                if details:
                    i,j=np.unravel_index(z.argmax(),z.shape);scores=smooth(rate,kernel,neighbor_only=neighbor)
                    peaks.append(dict(window=window,kernel=kernel,signal='neighbor_only' if neighbor else 'smoothed',
                        end_draw=int(i+window),number=int(j+1),score=float(scores[i,j]),raw_z=float(z[i,j])))
                    activity.append(pd.DataFrame(dict(window=window,kernel=kernel,signal='neighbor_only' if neighbor else 'smoothed',
                        number=np.arange(1,46),end_draw=len(x),target_draw=len(x)+1,own_rate=rate[-1],score=scores[-1],raw_z=z[-1])))
    statistics=draw_statistics(x);values=statistics[list(METRICS)].to_numpy()
    c=np.vstack((np.zeros((1,len(METRICS))),np.cumsum(values,axis=0)))
    cluster=[]
    for window in (1,*WINDOWS):
        means=(c[window:]-c[:-window])/window
        z=(means-reference['mean'])/(reference['std']/np.sqrt(window))
        maxima['spacing_clustering']=max(maxima['spacing_clustering'],float(np.abs(z).max()))
        if details:
            for j,name in enumerate(METRICS):
                i=int(np.abs(z[:,j]).argmax())
                cluster.append(dict(window=window,metric=name,end_draw=i+window,mean=float(means[i,j]),
                    reference_mean=float(reference['mean'][j]),reference_std=float(reference['std'][j]),raw_z=float(z[i,j])))
    motif=Counter(map(tuple,statistics.adjacent_spacings));maxima['spacing_motif']=int(max(motif.values()))
    result=dict(maxima=maxima,space=space)
    if details:
        result.update(density=pd.concat(density,ignore_index=True),range_leaders=pd.concat(leaders,ignore_index=True).sort_values('raw_z',ascending=False),
            zones=pd.concat(zones,ignore_index=True),movement=pd.DataFrame(motions),peaks=pd.DataFrame(peaks).sort_values('raw_z',ascending=False),
            activity=pd.concat(activity,ignore_index=True),spacing=statistics,spacing_peaks=pd.DataFrame(cluster),
            motifs=pd.DataFrame([dict(spacings=str(k),occurrences=v) for k,v in motif.most_common()]))
    return result


def compare_nulls(x,*,replicates=199,seed=100042,progress=None):
    x=matrix(x)
    if type(replicates) is not int or replicates<1:raise ValueError('Positive surrogate count required')
    reference=spacing_reference();real=complete_search(x,reference)['maxima'];rows=[]
    for kind,code in [('iid',0),('fixed_margins',1)]:
        for i in range(replicates):
            child=int(np.random.SeedSequence([seed,code,i]).generate_state(1)[0])
            null=iid_surrogate(len(x),seed=child) if kind=='iid' else constrained_surrogate(x,seed=child)
            outcome=complete_search(null,reference)
            if outcome['space']!=search_space(len(x)):raise RuntimeError('Null search differs from real search')
            rows.append(dict(null_model=kind,replicate=i,seed=child,recomputed_features=True,**outcome['maxima']))
            if progress and (i+1)%20==0:progress(f'{kind}: {i+1}/{replicates} complete searches')
    maxima=pd.DataFrame(rows);comparison=[]
    for kind,group in maxima.groupby('null_model'):
        for statistic in FAMILIES:
            exceed=int((group[statistic]>=real[statistic]).sum());p=(exceed+1)/(replicates+1)
            comparison.append(dict(null_model=kind,statistic=statistic,real_max=real[statistic],null_mean=float(group[statistic].mean()),
                null_q95=float(group[statistic].quantile(.95)),exceedances=exceed,replicates=replicates,global_p=p,adjusted_p=min(1.,6*p)))
    return pd.DataFrame(comparison),maxima
