"""H11 causal development, frozen later evaluation and conditional ablation."""
from functools import partial
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.analysis.recurrence import research_matrix
from src.analysis.information import LAGS,HISTORIES
from src.models.information_flow import MutualInformationModel,TransferEntropyModel,TargetHistoryBaseline
from src.models.predictive import rank_numbers
from src.backtest.multiscale import rank_diversity

PRIMARY_MODELS=('MutualInformationModel','TransferEntropyModel')


def configuration_hash(selection):
    return sha256(json.dumps(selection,sort_keys=True,allow_nan=False).encode()).hexdigest()


def candidates():
    result={}
    for lag in LAGS:
        for incoming in (3,5):
            result[f'mi_lag{lag}_K{incoming}']=dict(model='MutualInformationModel',lag=lag,incoming=incoming)
    for lag in LAGS:
        for k,l in HISTORIES:
            for incoming in (3,5):
                result[f'te_lag{lag}_k{k}_l{l}_K{incoming}']=dict(model='TransferEntropyModel',lag=lag,k=k,l=l,incoming=incoming)
    return result


def construct(config):
    c=dict(config);name=c.pop('model')
    return dict(MutualInformationModel=MutualInformationModel,TransferEntropyModel=TransferEntropyModel)[name](**c)


def select_development(rows,*,end=900):
    if rows.empty or rows.target_draw.min()<401 or rows.target_draw.max()>end or rows.duplicated(['candidate','target_draw']).any():
        raise ValueError('Only unique development targets may select configuration')
    groups=list(rows.groupby('candidate',sort=False));targets=sorted(groups[0][1].target_draw)
    if any(sorted(g.target_draw)!=targets for _,g in groups):raise ValueError('Matching development targets required')
    return max(groups,key=lambda item:float(item[1].hits.mean()))[0]


def development_search(x,*,progress=None):
    x=research_matrix(x)
    if len(x)!=900:raise ValueError('Selection requires exact draws1..900')
    specs=candidates();models={n:construct(c) for n,c in specs.items()};rows=[]
    for target in range(401,901):
        past=x[:target-1]
        for name,model in models.items():
            scores=model.fit(past,cutoff=target-1).score_matrix(past,target=target)
            ranking=rank_numbers(scores)
            rows.append(dict(candidate=name,model=specs[name]['model'],target_draw=target,
                hits=int(x[target-1,np.array(ranking[:6])-1].sum())))
        if progress and target%25==0:progress(f'Development {target}/900')
    table=pd.DataFrame(rows);names={};selected={}
    for family in PRIMARY_MODELS:
        name=select_development(table[table.model==family]);names[family]=name;selected[family]=specs[name]
    selection=dict(version='phase13-v1',research_cutoff=1245,development_start=401,development_end=900,
        later_start=901,training_window=624,models=selected,selected_candidates=names,
        candidate_count=70,context_support=20,shrinkage=20,weighting='positive occupied-state MillerMadow information',
        selection_metric='mean Top6 hits; ties declared order',
        development_matrix_hash=sha256(x.tobytes()).hexdigest(),draw1246_used=False)
    return selection,table


def load_selection(path):
    payload=json.loads(Path(path).read_text(encoding='utf-8'));s=payload['selection']
    if (payload['sha256']!=configuration_hash(s) or s['version']!='phase13-v1' or
        s['research_cutoff']!=1245 or s['development_end']!=900 or s['later_start']!=901 or s['candidate_count']!=70):
        raise ValueError('Frozen H11 configuration integrity mismatch')
    specs=list(candidates().values())
    if set(s['models'])!=set(PRIMARY_MODELS) or any(c not in specs for c in s['models'].values()):raise ValueError('Unknown H11 model configuration')
    return s


def factories(selection):
    result={name:partial(construct,c) for name,c in selection['models'].items()}
    from src.models.number_space import NeighborhoodModel
    result['Frequency26']=partial(NeighborhoodModel,window=26,kernel='none')
    c=selection['models']['TransferEntropyModel']
    result['TargetHistoryBaseline']=partial(TargetHistoryBaseline,lag=c['lag'],k=c['k'],l=c['l'])
    return result


def paired_report(rows,*,replicates=2000,block=26):
    result=[]
    for start in (901,1001,1101):
        groups={n:g.sort_values('target_draw') for n,g in rows[rows.target_draw>=start].groupby('model')}
        n=len(groups['RandomModel']);rng=np.random.default_rng(130042)
        indices=((rng.integers(0,n,(replicates,int(np.ceil(n/block))))[:,:,None]+np.arange(block))%n).reshape(replicates,-1)[:,:n]
        for model in PRIMARY_MODELS:
            a=groups[model]
            for reference in ('RandomModel','GapLogistic'):
                b=groups[reference]
                if a.target_draw.tolist()!=b.target_draw.tolist():raise ValueError('Paired target mismatch')
                metrics={k:(a[k].to_numpy(),b[k].to_numpy()) for k in ('hits','recall_6','recall_10','recall_15','mean_winning_rank')}
                metrics.update({f'pool_{k}_{threshold}plus':((a[f'pool_{k}']>=threshold).astype(int).to_numpy(),
                    (b[f'pool_{k}']>=threshold).astype(int).to_numpy()) for k in (6,8,10,12,15) for threshold in (5,6)})
                for metric,(aa,bb) in metrics.items():
                    delta=aa-bb;lo,hi=np.quantile(delta[indices].mean(1),[.025,.975])
                    result.append(dict(model=model,reference=reference,start=start,metric=metric,difference=float(delta.mean()),
                        ci_low=float(lo),ci_high=float(hi),block=block,degenerate=bool(lo==hi)))
    return pd.DataFrame(result)


def correlation_report(rows):
    result=[]
    for target,group in rows.groupby('target_draw'):
        reference=json.loads(group[group.model=='GapLogistic'].iloc[0].ranking)
        for row in group[group.model.isin(PRIMARY_MODELS)].itertuples():
            result.append(dict(model=row.model,target_draw=target,**rank_diversity(json.loads(row.ranking),reference)))
    return pd.DataFrame(result)


def conditional_report(rows,*,block=26,replicates=2000):
    """Compare source-added TE against exactly aligned target-history ablation.

    Loss is averaged over45 numbers per draw; draws are the bootstrap unit.
    These smoothed score probabilities need not sum to six.
    """
    result=[]
    for target,g in rows.groupby('target_draw'):
        own=g[g.model=='TargetHistoryBaseline'].iloc[0];te=g[g.model=='TransferEntropyModel'].iloc[0]
        actual=set(json.loads(te.actual));y=np.array([n in actual for n in range(1,46)],float)
        def loss(row):
            scores=json.loads(row.scores);p=np.clip([scores[str(n)] for n in range(1,46)],1e-6,1-1e-6)
            return float(-np.mean(y*np.log(p)+(1-y)*np.log(1-p)))
        a,b=loss(te),loss(own)
        result.append(dict(target_draw=target,te_logloss=a,target_history_logloss=b,difference=a-b))
    frame=pd.DataFrame(result);summary=[]
    for start in (901,1001,1101):
        delta=frame[frame.target_draw>=start].difference.to_numpy();n=len(delta);rng=np.random.default_rng(130043)
        indices=((rng.integers(0,n,(replicates,int(np.ceil(n/block))))[:,:,None]+np.arange(block))%n).reshape(replicates,-1)[:,:n]
        lo,hi=np.quantile(delta[indices].mean(1),[.025,.975])
        summary.append(dict(start=start,difference=float(delta.mean()),ci_low=float(lo),ci_high=float(hi),block=block,
            interpretation='negative favors source-added TE; nominal paired block interval'))
    return frame,pd.DataFrame(summary)


def annotate_information_cutoffs(rows):
    rows=rows.copy();rows['outer_fit_cutoff']=rows.training_cutoff
    information=rows.model.isin([*PRIMARY_MODELS,'TargetHistoryBaseline'])
    rows.loc[information,'training_cutoff']=rows.loc[information,'feature_cutoff']
    rows['information_training_cutoff']=pd.array(np.where(information,rows.feature_cutoff,np.nan),dtype='Int64')
    return rows


def evaluate(history,selection,*,cadence=26,progress=None):
    from src.analysis.features import build_prospective_features,GAP
    from src.prediction_scope import ProspectiveScope
    from src.analysis.spatiotemporal import lotto_matrix
    from src.backtest.translation import walk_forward
    if len(history)>1245:raise ValueError('H11 research cutoff1245')
    x=lotto_matrix(history,cutoff=len(history))
    if sha256(x[:900].tobytes()).hexdigest()!=selection['development_matrix_hash']:raise ValueError('Development prefix mismatch')
    f=build_prospective_features(history,scope=ProspectiveScope(len(history)),progress=progress)
    f=f[f.target_draw<=len(history)][['target_draw','feature_cutoff','number','appeared_next',*GAP]]
    rows=walk_forward(history,factories(selection),start=901,end=len(history),cadence=cadence,
        gap_features=f,combined=False,progress=progress)
    return annotate_information_cutoffs(rows)


def sensitivity(x,*,progress=None):
    """All predeclared candidates, descriptive only; never updates frozen choice."""
    x=research_matrix(x);rows=[];specs=candidates();models={n:construct(c) for n,c in specs.items()}
    for target in range(901,1246):
        past=x[:target-1]
        for name,model in models.items():
            ranking=rank_numbers(model.fit(past,cutoff=target-1).score_matrix(past,target=target))
            rows.append(dict(candidate=name,model=specs[name]['model'],target_draw=target,
                hits=int(x[target-1,np.array(ranking[:6])-1].sum())))
        if progress and target%25==0:progress(f'Sensitivity {target}/1245')
    return pd.DataFrame(rows)
