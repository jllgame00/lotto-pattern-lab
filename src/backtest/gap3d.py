"""Paired identical-target comparisons of a gap-conditioned model and its2D parent."""
import numpy as np
import pandas as pd


def paired_comparisons(results,*,starts=(401,501,601,701,801,901),replicates=2000,seed=42):
    if results.target_draw.max()>1245 or results.duplicated(['model','target_draw']).any():
        raise ValueError('Unique historical model/target rows through1245 required')
    if type(replicates) is not int or replicates<1: raise ValueError('Positive replication count required')
    rows=[]
    names=[name for name in results.model.unique() if name.startswith('GapConditioned')]
    for start in starts:
        subset=results[results.target_draw>=start]
        if subset.empty: continue
        for name in names:
            current=subset[subset.model==name].sort_values('target_draw')
            parent='TranslationModel' if 'Translation' in name else 'ChainModel'
            for reference in ('RandomModel',parent):
                baseline=subset[subset.model==reference].sort_values('target_draw')
                if current.empty or current.target_draw.tolist()!=baseline.target_draw.tolist():
                    raise ValueError('Paired model comparisons require identical targets')
                n=len(current); block=min(26,n); rng=np.random.default_rng(seed)
                offsets=rng.integers(n,size=(replicates,int(np.ceil(n/block))))
                indices=((offsets[:,:,None]+np.arange(block))%n).reshape(replicates,-1)[:,:n]
                metrics={key:(current[key].to_numpy(),baseline[key].to_numpy()) for key in
                    ('hits','mean_winning_rank','recall_6','recall_10','recall_15')}
                for k in (8,10,12,15):
                    a,b=current[f'pool_{k}'].to_numpy(),baseline[f'pool_{k}'].to_numpy()
                    metrics[f'pool_{k}_mean']=(a,b)
                    for threshold in (5,6): metrics[f'pool_{k}_{threshold}plus']=((a>=threshold).astype(int),(b>=threshold).astype(int))
                for metric,(a,b) in metrics.items():
                    difference=a-b; ci=np.quantile(difference[indices].mean(axis=1),[.025,.975])
                    rows.append(dict(model=name,reference=reference,evaluation_start=start,targets=n,metric=metric,
                        difference=float(difference.mean()),ci_low=float(ci[0]),ci_high=float(ci[1]),
                        direction='negative favors new model' if metric=='mean_winning_rank' else 'positive favors new model',
                        bootstrap_replicates=replicates,block_length=block,degenerate=bool(ci[0]==ci[1]),
                        warning='Unadjusted exploratory interval; degenerate rare-event intervals do not rule out events'))
    return pd.DataFrame(rows)
