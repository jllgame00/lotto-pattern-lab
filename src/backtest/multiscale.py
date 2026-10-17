"""Development-only model choice and causal later H10 evaluation."""
import json
from hashlib import sha256
from pathlib import Path
from functools import partial
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from src.analysis.recurrence import research_matrix
from src.models.multiscale import (WaveletPhaseModel,SSAModel,MultiscaleConsensusModel,SCALE_SETS)
from src.analysis.ssa import WINDOWS
from src.models.predictive import rank_numbers


def configuration_hash(selection):
    return sha256(json.dumps(selection,sort_keys=True,allow_nan=False).encode()).hexdigest()


def select_development(rows,*,end=900):
    if rows.empty or rows.target_draw.min()<401 or rows.target_draw.max()>end or rows.duplicated(['candidate','target_draw']).any():
        raise ValueError('Unique development-only targets required')
    groups=list(rows.groupby('candidate',sort=False));targets=sorted(groups[0][1].target_draw)
    if any(sorted(g.target_draw)!=targets for _,g in groups):raise ValueError('Matching development targets required')
    return max(groups,key=lambda item:float(item[1].hits.mean()))[0]


def candidates():
    result={}
    for i,periods in enumerate(SCALE_SETS):
        for cycles in (2,3):result[f'wavelet_s{i}_c{cycles}']=dict(model='WaveletPhaseModel',periods=list(periods),min_cycles=cycles)
    for length in WINDOWS:
        for rule in ('leading2','supported_pair'):result[f'ssa_L{length}_{rule}']=dict(model='SSAModel',length=length,rule=rule)
    return result


def construct(config):
    c=dict(config);name=c.pop('model')
    return {'WaveletPhaseModel':WaveletPhaseModel,'SSAModel':SSAModel}[name](**c)


def development_search(x,*,progress=None):
    x=research_matrix(x)
    if len(x)!=900:raise ValueError('Selection requires exact draws1..900')
    specs=candidates();rows=[];ranks={};models={n:construct(c) for n,c in specs.items()}
    for target in range(401,901):
        past=x[:target-1];rankings={}
        for name,model in models.items():
            scores=model.fit(past,cutoff=target-1).score_matrix(past,target=target)
            ranking=rank_numbers(scores);rankings[name]=ranking
            rows.append(dict(candidate=name,model=specs[name]['model'],target_draw=target,
                hits=int(x[target-1,np.array(ranking[:6])-1].sum())))
        ranks[target]=rankings
        if progress and target%25==0:progress(f'Development {target}/900')
    table=pd.DataFrame(rows);selected={};names={}
    for family in ('WaveletPhaseModel','SSAModel'):
        name=select_development(table[table.model==family]);names[family]=name;selected[family]=specs[name]
    consensus=[]
    for target,rankings in ranks.items():
        score=-(np.argsort(rankings[names['WaveletPhaseModel']])+np.argsort(rankings[names['SSAModel']]))/2
        ranking=rank_numbers(dict(enumerate(score.tolist(),1)))
        consensus.append(dict(candidate='consensus',model='MultiscaleConsensusModel',target_draw=target,
            hits=int(x[target-1,np.array(ranking[:6])-1].sum())))
    combo=pd.DataFrame(consensus)
    parents=[table[table.candidate==names[m]].set_index('target_draw').hits for m in names]
    combo_hits=combo.set_index('target_draw').hits
    allowed=all(combo_hits.mean()>p.mean() for p in parents)
    for a,b in ((401,650),(651,900)):
        allowed=allowed and combo_hits.loc[a:b].mean()>max(p.loc[a:b].mean() for p in parents)
    selection=dict(version='phase12-v1',research_cutoff=1245,development_start=401,development_end=900,
        later_start=901,training_window=416,models=selected,selected_candidates=names,
        consensus_allowed=bool(allowed),consensus_rule='equal ranks; strictly better than both parents overall and both development halves',
        development_matrix_hash=sha256(x.tobytes()).hexdigest(),candidate_count=12,
        selection_metric='mean Top6 hits; ties declared order',draw1246_used=False)
    return selection,pd.concat([table,combo],ignore_index=True)


def load_selection(path):
    payload=json.loads(Path(path).read_text(encoding='utf-8'));s=payload['selection']
    if (payload['sha256']!=configuration_hash(s) or s['research_cutoff']!=1245 or
        s['development_end']!=900 or s['later_start']!=901 or s['candidate_count']!=12):
        raise ValueError('Frozen H10 configuration integrity mismatch')
    specs=list(candidates().values())
    if set(s['models'])!={'WaveletPhaseModel','SSAModel'} or any(c not in specs for c in s['models'].values()):
        raise ValueError('Unknown model configuration')
    return s


def factories(selection,*,sensitivity=False):
    result={name:partial(construct,c) for name,c in selection['models'].items()}
    if selection['consensus_allowed']:
        result['MultiscaleConsensusModel']=lambda:MultiscaleConsensusModel(
            construct(selection['models']['WaveletPhaseModel']),construct(selection['models']['SSAModel']))
    from src.models.number_space import NeighborhoodModel
    result['Frequency26']=partial(NeighborhoodModel,window=26,kernel='none')
    if sensitivity:
        for name,config in candidates().items():result['sensitivity_'+name]=partial(construct,config)
    return result


def rank_diversity(a,b):
    if sorted(a)!=list(range(1,46)) or sorted(b)!=list(range(1,46)):raise ValueError('Complete number rankings required')
    return dict(spearman=float(spearmanr(np.argsort(a),np.argsort(b)).statistic),
        **{f'top{k}_overlap':len(set(a[:k])&set(b[:k])) for k in (6,10,15)})


def correlation_report(rows,*,recurrence_path=None):
    result=[];old=None
    if recurrence_path and Path(recurrence_path).is_file():old=pd.read_csv(recurrence_path)
    for target,group in rows.groupby('target_draw'):
        references={'GapLogistic':json.loads(group[group.model=='GapLogistic'].iloc[0].ranking)}
        if old is not None:
            matched=old[(old.target_draw==target)&(old.model=='RecurrenceAnalogModel')]
            if len(matched)==1:references['Phase11Recurrence']=json.loads(matched.iloc[0].ranking)
        for row in group[group.model.isin(['WaveletPhaseModel','SSAModel','MultiscaleConsensusModel'])].itertuples():
            for ref,ranking in references.items():
                result.append(dict(model=row.model,target_draw=target,reference=ref,
                    **rank_diversity(json.loads(row.ranking),ranking)))
    return pd.DataFrame(result)


def paired_report(rows,*,replicates=2000,block=26):
    output=[]
    for start in (901,1001,1101):
        groups={n:g.sort_values('target_draw') for n,g in rows[rows.target_draw>=start].groupby('model')}
        if 'RandomModel' not in groups:raise ValueError('Random baseline required')
        n=len(groups['RandomModel']);rng=np.random.default_rng(120042)
        idx=((rng.integers(0,n,(replicates,int(np.ceil(n/block))))[:,:,None]+np.arange(block))%n).reshape(replicates,-1)[:,:n]
        for model in ('WaveletPhaseModel','SSAModel','MultiscaleConsensusModel'):
            if model not in groups:continue
            a=groups[model]
            for reference in ('RandomModel','GapLogistic'):
                b=groups[reference]
                if a.target_draw.tolist()!=b.target_draw.tolist():raise ValueError('Paired target mismatch')
                metrics={k:(a[k].to_numpy(),b[k].to_numpy()) for k in ('hits','recall_6','recall_10','recall_15','mean_winning_rank')}
                metrics.update({f'pool_{k}_{threshold}plus':((a[f'pool_{k}']>=threshold).astype(int).to_numpy(),
                    (b[f'pool_{k}']>=threshold).astype(int).to_numpy()) for k in (6,8,10,12,15) for threshold in (5,6)})
                for metric,(aa,bb) in metrics.items():
                    delta=aa-bb;lo,hi=np.quantile(delta[idx].mean(1),[.025,.975])
                    output.append(dict(model=model,reference=reference,start=start,metric=metric,difference=float(delta.mean()),
                        ci_low=float(lo),ci_high=float(hi),block=block,degenerate=bool(lo==hi)))
    return pd.DataFrame(output)


def evaluate(history,selection,*,cadence=26,sensitivity=False,progress=None):
    from src.analysis.features import build_prospective_features,GAP
    from src.prediction_scope import ProspectiveScope
    from src.analysis.spatiotemporal import lotto_matrix
    from src.backtest.translation import walk_forward
    if len(history)>1245:raise ValueError('H10 cutoff1245')
    x=lotto_matrix(history,cutoff=len(history))
    if sha256(x[:900].tobytes()).hexdigest()!=selection['development_matrix_hash']:raise ValueError('Development prefix mismatch')
    f=build_prospective_features(history,scope=ProspectiveScope(len(history)),progress=progress)
    f=f[f.target_draw<=len(history)][['target_draw','feature_cutoff','number','appeared_next',*GAP]]
    return walk_forward(history,factories(selection,sensitivity=sensitivity),start=901,end=len(history),
        cadence=cadence,gap_features=f,combined=False,progress=progress)
