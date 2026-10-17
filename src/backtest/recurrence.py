"""Development-only analog selection; later evaluation reuses existing baselines."""
import json
from hashlib import sha256
from pathlib import Path
from dataclasses import asdict
from functools import partial
import numpy as np
import pandas as pd
from src.analysis.recurrence import (research_matrix,configurations,observations,
    embed,fit_scaler,EmbeddingConfig,rank_correlation)
from src.models.recurrence import (trajectory_distances,successor_scores,
    NearestSuccessorBaseline,RecurrenceAnalogModel,RecurrenceContinuationModel)


def select_development(rows, *, end=900):
    if rows.empty or rows.target_draw.max()>end or rows.duplicated(['candidate','target_draw']).any():
        raise ValueError('Only unique development targets may select configuration')
    groups=list(rows.groupby('candidate',sort=False))
    targets=sorted(groups[0][1].target_draw)
    if any(sorted(g.target_draw)!=targets for _,g in groups):
        raise ValueError('Matching development targets required')
    return max(groups,key=lambda item:float(item[1].hits.mean()))[0]


def configuration_hash(selection):
    return sha256(json.dumps(selection,sort_keys=True,allow_nan=False).encode()).hexdigest()


def load_selection(path):
    payload=json.loads(Path(path).read_text(encoding='utf-8'))
    s=payload['selection']
    if payload['sha256']!=configuration_hash(s) or s['development_end']!=900 or s['later_start']!=901 or s['research_cutoff']!=1245:
        raise ValueError('Frozen Phase 11 configuration integrity mismatch')
    return s


def development_search(x, *, progress=None):
    """Only an exact development prefix can enter; batched causal distances per fit."""
    x=research_matrix(x)
    if len(x)!=900: raise ValueError('Selection requires exact draws 1..900; no later outcomes')
    targets=np.arange(401,901); rows=[]; configs={}
    for c in configurations():
        o=observations(x,c)
        specs=[('NearestSuccessorBaseline',1,1,'uniform')]
        specs += [('RecurrenceAnalogModel' if l==1 else 'RecurrenceContinuationModel',l,k,w)
            for l in (1,2,3) for k in (5,10,20,40) for w in ('uniform','inverse')]
        hits=np.empty((len(specs),len(targets)),np.uint8)
        for begin in range(0,len(targets),26):
            batch=targets[begin:begin+26];cutoff=int(batch[0]-1)
            # Transform only a prefix up to the last *completed* state in this batch.
            past=x[:int(batch[-1])-1]
            scaler=fit_scaler(o,cutoff) if c.metric=='euclidean' else None
            e,ends=embed(o[:len(past)],c,scaler)
            for length in (1,2,3):
                d,candidates=trajectory_distances(e,ends,c,batch-1,length)
                order=np.argsort(d,axis=1,kind='stable')[:,:40]
                for index,(model,l,k,w) in enumerate(specs):
                    if l!=length: continue
                    scores=successor_scores(past,candidates,d,k,w,neighbor_order=order)
                    top=np.argsort(-scores,axis=1,kind='stable')[:,:6]
                    # Outcomes accessed only after causal scores have been generated.
                    hits[index,begin:begin+len(batch)]=np.take_along_axis(x[batch-1],top,axis=1).sum(1)
        for index,(model,l,k,w) in enumerate(specs):
            name=f'{c.key}_L{l}_K{k}_{w}'
            configs[name]=dict(model=model,embedding=asdict(c),length=l,k=k,weighting=w)
            rows.append(dict(candidate=name,model=model,mean_hits=float(hits[index].mean()),
                early_dev=float(hits[index,:400].mean()),late_dev=float(hits[index,100:].mean())))
        if progress: progress(c.key)
    table=pd.DataFrame(rows)
    selected,stability=summarize_development(table,configs)
    s=dict(version='phase11-v1',research_cutoff=1245,development_start=401,development_end=900,later_start=901,
        cadence=26,selection_metric='mean Top6 hits; ties declared order',models=selected,
        development_matrix_hash=sha256(x.tobytes()).hexdigest(),candidate_count=len(table))
    return s,table,stability


def summarize_development(table,configs):
    selected={};stability=[]
    for model in ('NearestSuccessorBaseline','RecurrenceAnalogModel','RecurrenceContinuationModel'):
        group=table[table.model==model]
        name=group.loc[group.mean_hits.idxmax(),'candidate'];selected[model]=configs[name]
        for metric in ('mean_hits','early_dev','late_dev'):
            winner=group.loc[group[metric].idxmax()]
            stability.append(dict(model=model,period=metric,candidate=winner.candidate,mean_hits=winner[metric],
                **configs[winner.candidate]['embedding'],k=configs[winner.candidate]['k']))
    return selected,pd.DataFrame(stability)


def factories(selection):
    result={}
    for name,c in selection['models'].items():
        config=EmbeddingConfig(**c['embedding'])
        cls={'NearestSuccessorBaseline':NearestSuccessorBaseline,'RecurrenceAnalogModel':RecurrenceAnalogModel,
            'RecurrenceContinuationModel':RecurrenceContinuationModel}[name]
        result[name]=partial(cls,config,**({} if name=='NearestSuccessorBaseline' else
            dict(k=c['k'],weighting=c['weighting'],length=c['length'])))
    from src.models.number_space import NeighborhoodModel
    result['Frequency26']=partial(NeighborhoodModel,window=26,kernel='none')
    return result


def paired_report(rows, *, replicates=2000,block=26):
    output=[]
    for start in (901,1001,1101):
        groups={n:g.sort_values('target_draw') for n,g in rows[rows.target_draw>=start].groupby('model')}
        n=len(groups['RandomModel']);rng=np.random.default_rng(110042)
        indices=((rng.integers(0,n,(replicates,int(np.ceil(n/block))))[:,:,None]+np.arange(block))%n).reshape(replicates,-1)[:,:n]
        for model in ('NearestSuccessorBaseline','RecurrenceAnalogModel','RecurrenceContinuationModel'):
            a=groups[model]
            for reference in ('RandomModel','GapLogistic'):
                b=groups[reference]
                if a.target_draw.tolist()!=b.target_draw.tolist(): raise ValueError('Paired target mismatch')
                metrics={k:(a[k].to_numpy(),b[k].to_numpy()) for k in ('hits','recall_6','recall_10','recall_15','mean_winning_rank')}
                metrics.update({f'pool_{k}_{threshold}plus':((a[f'pool_{k}']>=threshold).astype(int).to_numpy(),
                    (b[f'pool_{k}']>=threshold).astype(int).to_numpy()) for k in (6,8,10,12,15) for threshold in (5,6)})
                for metric,(aa,bb) in metrics.items():
                    delta=aa-bb;lo,hi=np.quantile(delta[indices].mean(1),[.025,.975])
                    output.append(dict(model=model,reference=reference,start=start,metric=metric,
                        difference=float(delta.mean()),ci_low=float(lo),ci_high=float(hi),block=block))
    return pd.DataFrame(output)


def correlation_report(rows):
    result=[]
    for target,group in rows.groupby('target_draw'):
        ref=group[group.model=='GapLogistic'].iloc[0];gr=json.loads(ref.ranking);gs=json.loads(ref.scores)
        for row in group[group.model.str.contains('Recurrence|Nearest')].itertuples():
            ranking=json.loads(row.ranking);scores=json.loads(row.scores)
            # Rank vectors aligned by number, not by sorted position.
            a=np.argsort(ranking);b=np.argsort(gr)
            av=np.array([scores[str(n)] for n in range(1,46)]);bv=np.array([gs[str(n)] for n in range(1,46)])
            result.append(dict(model=row.model,target_draw=target,spearman=rank_correlation(a,b),
                score_spearman=rank_correlation(av,bv),
                **{f'top{k}_overlap':len(set(ranking[:k])&set(gr[:k])) for k in (6,10,15)}))
    return pd.DataFrame(result)


def evaluate(history,selection, *, cadence=26,progress=None):
    from src.analysis.features import build_prospective_features,GAP
    from src.prediction_scope import ProspectiveScope
    from src.analysis.spatiotemporal import lotto_matrix
    from src.backtest.translation import walk_forward
    if len(history)>1245: raise ValueError('Phase 11 research cutoff is 1245')
    x=lotto_matrix(history,cutoff=len(history))
    if sha256(x[:900].tobytes()).hexdigest()!=selection['development_matrix_hash']:
        raise ValueError('Development prefix mismatch')
    f=build_prospective_features(history,scope=ProspectiveScope(len(history)),progress=progress)
    f=f[f.target_draw<=len(history)][['target_draw','feature_cutoff','number','appeared_next',*GAP]]
    return walk_forward(history,factories(selection),start=901,end=len(history),cadence=cadence,
        gap_features=f,combined=False,progress=progress)
