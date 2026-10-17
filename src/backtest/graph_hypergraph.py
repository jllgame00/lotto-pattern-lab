"""H12 development-only selection, controls and later ranking evaluation."""
from functools import partial
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.analysis.recurrence import research_matrix
from src.analysis.graph_structure import WINDOWS
from src.models.predictive import rank_numbers
from src.backtest.multiscale import rank_diversity

PRIMARY_MODELS=('GraphStructureModel','HypergraphModel')


def configuration_hash(selection):
    return sha256(json.dumps(selection,sort_keys=True,allow_nan=False).encode()).hexdigest()


def candidates():
    result={}
    for W in WINDOWS:
        for feature in ('neighbor','clustering'):
            result[f'graph_W{W}_{feature}']=dict(model='GraphStructureModel',window=W,feature=feature,communities=2)
        for feature in ('community','neighbor_community'):
            for K in (2,3):result[f'graph_W{W}_{feature}_K{K}']=dict(model='GraphStructureModel',window=W,feature=feature,communities=K)
    for W in WINDOWS:
        for support in (2,3):
            for shrink in (5,10):
                result[f'hyper_W{W}_support{support}_shrink{shrink}']=dict(model='HypergraphModel',window=W,support=support,shrinkage=shrink)
    return result


def construct(config):
    from src.models.graph_hypergraph import GraphStructureModel,HypergraphModel
    c=dict(config);name=c.pop('model')
    return dict(GraphStructureModel=GraphStructureModel,HypergraphModel=HypergraphModel)[name](**c)


def select_development(rows,*,end=900):
    if rows.empty or rows.target_draw.min()<401 or rows.target_draw.max()>end or rows.duplicated(['candidate','target_draw']).any():
        raise ValueError('Unique development-only targets required')
    groups=list(rows.groupby('candidate',sort=False));targets=sorted(groups[0][1].target_draw)
    if any(sorted(g.target_draw)!=targets for _,g in groups):raise ValueError('Matching development targets required')
    return max(groups,key=lambda item:float(item[1].hits.mean()))[0]


def development_search(x,*,progress=None):
    x=research_matrix(x)
    if len(x)!=900:raise ValueError('Development requires exact draws1..900')
    specs=candidates();models={n:construct(c) for n,c in specs.items()};rows=[];ranks={}
    for target in range(401,901):
        past=x[:target-1];ranking_here={}
        for name,model in models.items():
            ranking=rank_numbers(model.fit(past,cutoff=target-1).score_matrix(past,target=target));ranking_here[name]=ranking
            rows.append(dict(candidate=name,model=specs[name]['model'],target_draw=target,
                hits=int(x[target-1,np.array(ranking[:6])-1].sum())))
        freq=rank_numbers(dict(enumerate(past[-26:].mean(0).tolist(),1)))
        rows.append(dict(candidate='frequency26',model='Frequency26',target_draw=target,hits=int(x[target-1,np.array(freq[:6])-1].sum())))
        ranks[target]=ranking_here
        if progress and target%25==0:progress(f'Development {target}/900')
    table=pd.DataFrame(rows);selected={};names={}
    for family in PRIMARY_MODELS:
        name=select_development(table[table.model==family]);names[family]=name;selected[family]=specs[name]
    combination=[]
    for target,rankings in ranks.items():
        ranksum=np.argsort(rankings[names['GraphStructureModel']])+np.argsort(rankings[names['HypergraphModel']])
        top=np.argsort(ranksum,kind='stable')[:6]
        combination.append(dict(candidate='consensus',model='GraphHypergraphConsensus',target_draw=target,hits=int(x[target-1,top].sum())))
    combo=pd.DataFrame(combination).set_index('target_draw');parents=[table[table.candidate==names[m]].set_index('target_draw').hits for m in names]
    frequency=table[table.candidate=='frequency26'].set_index('target_draw').hits
    allowed=all(p.mean()>.8 and p.mean()>frequency.mean() for p in parents)
    allowed=allowed and all(combo.hits.mean()>p.mean() for p in parents)
    for a,b in ((401,650),(651,900)):allowed=allowed and all(combo.loc[a:b].hits.mean()>p.loc[a:b].mean() for p in parents)
    s=dict(version='phase14-v1',research_cutoff=1245,development_start=401,development_end=900,later_start=901,
        models=selected,selected_candidates=names,candidate_count=30,consensus_allowed=bool(allowed),
        consensus_rule='bothparents>0.8andFrequency26; equalrankstrictlybetterthanbothparentsoverallandbothdevelopmenthalves',
        selection_metric='meanTop6hits; tiesdeclaredorder',graph_threshold=2,frequency_control='within-windowintercept+frequencyOLS',
        development_matrix_hash=sha256(x.tobytes()).hexdigest(),draw1246_used=False)
    return s,pd.concat([table,combo.reset_index()],ignore_index=True)


def load_selection(path):
    payload=json.loads(Path(path).read_text(encoding='utf-8'));s=payload['selection']
    if (payload['sha256']!=configuration_hash(s) or s['version']!='phase14-v1' or s['research_cutoff']!=1245 or
        s['development_end']!=900 or s['later_start']!=901 or s['candidate_count']!=30):raise ValueError('Frozen H12 configuration integrity mismatch')
    specs=list(candidates().values())
    if set(s['models'])!=set(PRIMARY_MODELS) or any(c not in specs for c in s['models'].values()):raise ValueError('Unknown H12 model configuration')
    return s


def factories(selection):
    result={name:partial(construct,c) for name,c in selection['models'].items()}
    from src.models.graph_hypergraph import RollingFrequencyControl
    for name,W in [('Frequency26',26),('MatchedGraphFrequency',selection['models']['GraphStructureModel']['window']),
        ('MatchedHypergraphFrequency',selection['models']['HypergraphModel']['window'])]:result[name]=partial(RollingFrequencyControl,window=W)
    if selection['consensus_allowed']:
        from src.models.graph_hypergraph import GraphHypergraphConsensus
        result['GraphHypergraphConsensus']=lambda:GraphHypergraphConsensus(
            construct(selection['models']['GraphStructureModel']),construct(selection['models']['HypergraphModel']))
    return result


def paired_report(rows,*,replicates=2000,block=26):
    result=[];names=[*PRIMARY_MODELS,'GraphHypergraphConsensus']
    for start in (901,1001,1101):
        groups={n:g.sort_values('target_draw') for n,g in rows[rows.target_draw>=start].groupby('model')}
        n=len(groups['RandomModel']);rng=np.random.default_rng(140042)
        indices=((rng.integers(0,n,(replicates,int(np.ceil(n/block))))[:,:,None]+np.arange(block))%n).reshape(replicates,-1)[:,:n]
        for name in names:
            if name not in groups:continue
            a=groups[name]
            references=['RandomModel','Frequency26','GapLogistic']
            if name in PRIMARY_MODELS:references.append('MatchedGraphFrequency' if name=='GraphStructureModel' else 'MatchedHypergraphFrequency')
            for reference in references:
                b=groups[reference]
                if a.target_draw.tolist()!=b.target_draw.tolist():raise ValueError('Paired target mismatch')
                metrics={k:(a[k].to_numpy(),b[k].to_numpy()) for k in ('hits','recall_6','recall_10','recall_15','mean_winning_rank')}
                metrics.update({f'pool_{k}_{threshold}plus':((a[f'pool_{k}']>=threshold).astype(int).to_numpy(),
                    (b[f'pool_{k}']>=threshold).astype(int).to_numpy()) for k in (6,8,10,12,15) for threshold in (5,6)})
                for metric,(aa,bb) in metrics.items():
                    delta=aa-bb;lo,hi=np.quantile(delta[indices].mean(1),[.025,.975])
                    result.append(dict(model=name,reference=reference,start=start,metric=metric,difference=float(delta.mean()),
                        ci_low=float(lo),ci_high=float(hi),block=block,degenerate=bool(lo==hi)))
    return pd.DataFrame(result)


def correlation_report(rows,*,mi_path=None):
    result=[];old=pd.read_csv(mi_path) if mi_path and Path(mi_path).is_file() else None
    for target,g in rows.groupby('target_draw'):
        references={'GapLogistic':json.loads(g[g.model=='GapLogistic'].iloc[0].ranking)}
        if old is not None:
            matched=old[(old.target_draw==target)&(old.model=='MutualInformationModel')]
            if len(matched)==1:references['Phase13MI']=json.loads(matched.iloc[0].ranking)
        for row in g[g.model.isin([*PRIMARY_MODELS,'GraphHypergraphConsensus'])].itertuples():
            for reference,ranking in references.items():result.append(dict(model=row.model,target_draw=target,reference=reference,
                **rank_diversity(json.loads(row.ranking),ranking)))
    return pd.DataFrame(result)


def annotate_cutoffs(rows):
    rows=rows.copy();rows['outer_fit_cutoff']=rows.training_cutoff
    structural=rows.model.isin([*PRIMARY_MODELS,'GraphHypergraphConsensus'])
    rows.loc[structural,'training_cutoff']=rows.loc[structural,'feature_cutoff']
    rows['structural_training_cutoff']=pd.array(np.where(structural,rows.feature_cutoff,np.nan),dtype='Int64')
    return rows


def evaluate(history,selection,*,cadence=26,progress=None):
    from src.analysis.features import build_prospective_features,GAP
    from src.prediction_scope import ProspectiveScope
    from src.analysis.spatiotemporal import lotto_matrix
    from src.backtest.translation import walk_forward
    if len(history)>1245:raise ValueError('H12 cutoff1245')
    x=lotto_matrix(history,cutoff=len(history))
    if sha256(x[:900].tobytes()).hexdigest()!=selection['development_matrix_hash']:raise ValueError('Development prefix mismatch')
    f=build_prospective_features(history,scope=ProspectiveScope(len(history)),progress=progress)
    f=f[f.target_draw<=len(history)][['target_draw','feature_cutoff','number','appeared_next',*GAP]]
    return annotate_cutoffs(walk_forward(history,factories(selection),start=901,end=len(history),cadence=cadence,
        gap_features=f,combined=False,progress=progress))


def sensitivity(x,*,progress=None):
    x=research_matrix(x);rows=[];specs=candidates();models={n:construct(c) for n,c in specs.items()}
    for target in range(901,1246):
        past=x[:target-1]
        for name,model in models.items():
            top=rank_numbers(model.fit(past,cutoff=target-1).score_matrix(past,target=target))[:6]
            rows.append(dict(candidate=name,model=specs[name]['model'],target_draw=target,hits=int(x[target-1,np.array(top)-1].sum())))
        if progress and target%25==0:progress(f'Sensitivity {target}/1245')
    return pd.DataFrame(rows)
