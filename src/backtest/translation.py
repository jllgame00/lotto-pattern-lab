"""Phase6 chronological evaluation, explicitly bounded at1245; old seals unchanged."""
import json
import numpy as np
import pandas as pd
from scipy.stats import hypergeom, binomtest
from src.analysis.spatiotemporal import lotto_matrix
from src.backtest.ranking import rank_metrics,_seed,summarize_rankings
from src.models.predictive import rank_numbers,LogisticModel
from src.models.random_model import RandomModel
from src.models.translation import combine_scores
from src.analysis.features import GAP
from src.prediction_scope import ProspectiveScope


def walk_forward(history,factories,*,start=401,end=None,cadence=26,seed=42,
                 gap_features=None,combined=True,progress=None):
    x=lotto_matrix(history,cutoff=len(history)); end=len(x) if end is None else end
    if (type(start) is not int or type(end) is not int or type(cadence) is not int or
        cadence<1 or not 105<=start<=end<=len(x) or end>1245): raise ValueError('Invalid bounded walk-forward protocol')
    if {'RandomModel','GapLogistic','Combined2D'}&set(factories): raise ValueError('Reserved model name')
    fitted={}; rows=[]; gap=None
    for target in range(start,end+1):
        past=x[:target-1].copy()
        if (target-start)%cadence==0:
            fitted={name:factory().fit(past,cutoff=target-1) for name,factory in factories.items()}
            if gap_features is not None:
                # Only past labels and causal canonical gap columns reach fit.
                training=gap_features[gap_features.target_draw<target].copy()
                gap=LogisticModel(columns=GAP,prediction_scope=ProspectiveScope(target-1)).fit(training,cutoff=target-1)
            if progress: progress(f'Walk-forward: refit through{target-1}, cadence{cadence}')
        scored={name:model.score_matrix(past,target=target) for name,model in fitted.items()}
        if combined and {'TranslationModel','ChainModel'}<=set(scored):
            scored['Combined2D']=combine_scores(scored['TranslationModel'],scored['ChainModel'])
        if gap is not None:
            # Extend only the permitted scoring context between fits; no refit or scaling.
            gap.prediction_scope=ProspectiveScope(target-1)
            current=gap_features[gap_features.target_draw==target].drop(columns='appeared_next').copy()
            scored['GapLogistic']=gap.score_rows(current)
        target_seed=_seed(seed,target,10)
        chosen=RandomModel().predict(None,seed=target_seed); rng=np.random.default_rng(target_seed)
        random_rank=rng.permutation(chosen).tolist()+rng.permutation([n for n in range(1,46) if n not in chosen]).tolist()
        scored['RandomModel']=RandomModel().score_numbers(None)
        rankings={name:random_rank if name=='RandomModel' else rank_numbers(scores) for name,scores in scored.items()}
        # First access to this target's winning row, strictly AFTER every prediction.
        actual=set((np.flatnonzero(x[target-1])+1).tolist())
        for name,scores in scored.items():
            ranking=rankings[name]
            cutoff=target-1 if name=='RandomModel' else gap.training_cutoff if name=='GapLogistic' else next(iter(fitted.values())).training_cutoff
            row=dict(model=name,target_draw=target,feature_cutoff=target-1,training_cutoff=cutoff,
                seed=target_seed,ranking=json.dumps(ranking),scores=json.dumps(scores,sort_keys=True),
                actual=json.dumps(sorted(actual)),**rank_metrics(ranking,actual))
            row.update({f'pool_{k}':len(set(ranking[:k])&actual) for k in (6,8,10,12,15)})
            rows.append(row)
    return pd.DataFrame(rows)


def pool_report(results, *, bootstraps=2000,seed=42):
    rows=[]; baseline=results[results.model=='RandomModel'].sort_values('target_draw')
    n=len(baseline)
    if not n or baseline.target_draw.duplicated().any(): raise ValueError('Unique paired random targets required')
    rng=np.random.default_rng(seed); length=min(26,n)
    starts=rng.integers(0,n,size=(bootstraps,int(np.ceil(n/length))))
    indices=((starts[:,:,None]+np.arange(length))%n).reshape(bootstraps,-1)[:,:n]
    for name,group in results.groupby('model',sort=False):
        group=group.sort_values('target_draw')
        if group.target_draw.tolist()!=baseline.target_draw.tolist(): raise ValueError('Pool comparisons require matching targets')
        for k in (6,8,10,12,15):
            counts=group[f'pool_{k}'].to_numpy(); n=len(counts)
            row=dict(model=name,pool_size=k,targets=n,mean_winners=float(counts.mean()))
            mean_delta=counts-baseline[f'pool_{k}'].to_numpy()
            low,high=np.quantile(mean_delta[indices].mean(axis=1),[.025,.975])
            row.update(paired_mean_difference=float(mean_delta.mean()),paired_mean_ci_low=float(low),paired_mean_ci_high=float(high))
            row.update({f'winners_{i}':int((counts==i).sum()) for i in range(7)})
            for threshold in (3,4,5,6):
                hits=int((counts>=threshold).sum()); ci=binomtest(hits,n).proportion_ci()
                row.update({f'count_{threshold}plus':hits,f'rate_{threshold}plus':hits/n,
                    f'exact_random_{threshold}plus':float(hypergeom.sf(threshold-1,45,6,k)),
                    f'ci_low_{threshold}plus':float(ci.low),f'ci_high_{threshold}plus':float(ci.high)})
                delta=(counts>=threshold).astype(float)-(baseline[f'pool_{k}'].to_numpy()>=threshold)
                low,high=np.quantile(delta[indices].mean(axis=1),[.025,.975])
                row.update({f'paired_delta_{threshold}plus':float(delta.mean()),
                    f'paired_ci_low_{threshold}plus':float(low),f'paired_ci_high_{threshold}plus':float(high),
                    f'paired_degenerate_{threshold}plus':bool(low==high)})
            rows.append(row)
    return pd.DataFrame(rows)


def summaries(results, *, starts=(401,501,601,701,801,901),bootstraps=2000):
    comparisons=[]; blocks=[]; pools=[]
    for start in starts:
        subset=results[results.target_draw>=start]
        if subset.empty: continue
        tables=summarize_rankings(subset,bootstraps=bootstraps)
        for destination,frame in ((comparisons,tables['comparison']),(blocks,tables['time_blocks']),(pools,pool_report(subset,bootstraps=bootstraps))):
            frame['evaluation_start']=start; destination.append(frame)
    return dict(comparison=pd.concat(comparisons,ignore_index=True),
        time_blocks=pd.concat(blocks,ignore_index=True),pools=pd.concat(pools,ignore_index=True))
