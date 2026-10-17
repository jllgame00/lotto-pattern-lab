"""H13 chronological selection and frozen later evaluation."""
from functools import partial
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.analysis.recurrence import research_matrix
from src.analysis.modular_space import MODULI,LAGS
from src.models.predictive import rank_numbers
from src.backtest.multiscale import rank_diversity

PRIMARY_MODELS=('ModularResidueModel','DifferenceRelationModel')
OPTIONAL_MODELS=('GapShapeModel','ModularDifferenceConsensus')


def configuration_hash(s):return sha256(json.dumps(s,sort_keys=True,allow_nan=False).encode()).hexdigest()


def candidates():
    specs={}
    for k in MODULI:
        for lag in LAGS:specs[f'mod_k{k}_lag{lag}']=dict(model='ModularResidueModel',modulus=k,lag=lag)
    for lag in LAGS:
        for support in (20,40):specs[f'distance_lag{lag}_support{support}']=dict(model='DifferenceRelationModel',lag=lag,support=support)
    for K in (10,25):
        for sigma in (1,2):specs[f'shape_K{K}_sigma{sigma}']=dict(model='GapShapeModel',K=K,sigma=sigma)
    return specs


def construct(config):
    from src.models.transformed_space import ModularResidueModel,DifferenceRelationModel,GapShapeModel
    c=dict(config);name=c.pop('model')
    return dict(ModularResidueModel=ModularResidueModel,DifferenceRelationModel=DifferenceRelationModel,GapShapeModel=GapShapeModel)[name](**c)


def select_development(rows,*,end=900):
    if rows.empty or rows.target_draw.min()<401 or rows.target_draw.max()>end or rows.duplicated(['candidate','target_draw']).any():
        raise ValueError('Unique development-only targets required')
    groups=list(rows.groupby('candidate',sort=False));targets=sorted(groups[0][1].target_draw)
    if any(sorted(g.target_draw)!=targets for _,g in groups):raise ValueError('Matching development targets required')
    return max(groups,key=lambda item:float(item[1].hits.mean()))[0]


def development_search(x,*,progress=None):
    x=research_matrix(x)
    if len(x)!=900:raise ValueError('Development requires exact1..900')
    specs=candidates();models={n:construct(c) for n,c in specs.items()};rows=[];ranks={}
    for target in range(401,901):
        past=x[:target-1];here={}
        for name,model in models.items():
            ranking=rank_numbers(model.fit(past,cutoff=target-1).score_matrix(past,target=target));here[name]=ranking
            rows.append(dict(candidate=name,model=specs[name]['model'],target_draw=target,hits=int(x[target-1,np.array(ranking[:6])-1].sum())))
        top=rank_numbers(dict(enumerate(past[-26:].mean(0).tolist(),1)))[:6]
        rows.append(dict(candidate='frequency26',model='Frequency26',target_draw=target,hits=int(x[target-1,np.array(top)-1].sum())))
        ranks[target]=here
        if progress and target%25==0:progress(f'Development{target}/900')
    table=pd.DataFrame(rows);selected={};names={}
    for family in (*PRIMARY_MODELS,'GapShapeModel'):
        name=select_development(table[table.model==family]);names[family]=name;selected[family]=specs[name]
    frequency=table[table.candidate=='frequency26'].set_index('target_draw').hits
    shape=table[table.candidate==names['GapShapeModel']].set_index('target_draw').hits
    shape_allowed=shape.mean()>.8 and shape.mean()>frequency.mean() and all(shape.loc[a:b].mean()>.8 for a,b in ((401,650),(651,900)))
    shape_config=selected['GapShapeModel']
    if not shape_allowed:selected.pop('GapShapeModel')
    parents=[table[table.candidate==names[m]].set_index('target_draw').hits for m in PRIMARY_MODELS]
    combo=[]
    for target,rankings in ranks.items():
        ranksum=np.argsort(rankings[names[PRIMARY_MODELS[0]]])+np.argsort(rankings[names[PRIMARY_MODELS[1]]])
        top=np.argsort(ranksum,kind='stable')[:6]
        combo.append(dict(candidate='consensus',model='ModularDifferenceConsensus',target_draw=target,hits=int(x[target-1,top].sum())))
    combo=pd.DataFrame(combo).set_index('target_draw')
    allowed=all(p.mean()>.8 and p.mean()>frequency.mean() for p in parents)
    allowed=allowed and all(combo.hits.mean()>p.mean() for p in parents)
    for a,b in ((401,650),(651,900)):allowed=allowed and all(combo.loc[a:b].hits.mean()>p.loc[a:b].mean() for p in parents)
    s=dict(version='phase15-v1',research_cutoff=1245,development_start=401,development_end=900,later_start=901,
        models=selected,selected_candidates=names,candidate_count=60,shape_allowed=bool(shape_allowed),
        shape_development_candidate=shape_config,consensus_allowed=bool(allowed),selection_metric='meanTop6hits;tiesdeclaredorder',
        modular_shrinkage=50,modular_support=20,difference_shrinkage=100,shape_exclusion=26,
        development_matrix_hash=sha256(x.tobytes()).hexdigest(),draw1246_used=False)
    return s,pd.concat([table,combo.reset_index()],ignore_index=True)


def load_selection(path):
    payload=json.loads(Path(path).read_text(encoding='utf-8'));s=payload['selection']
    if (payload['sha256']!=configuration_hash(s) or s['version']!='phase15-v1' or s['research_cutoff']!=1245 or
        s['development_end']!=900 or s['later_start']!=901 or s['candidate_count']!=60):raise ValueError('Frozen H13 configuration integrity mismatch')
    allowed=list(candidates().values());expected=set(PRIMARY_MODELS)|({'GapShapeModel'} if s['shape_allowed'] else set())
    if set(s['models'])!=expected or any(c not in allowed or c['model']!=name for name,c in s['models'].items()):raise ValueError('Unknown H13 configuration')
    return s


def factories(selection):
    result={name:partial(construct,c) for name,c in selection['models'].items()}
    from src.models.graph_hypergraph import RollingFrequencyControl
    result['Frequency26']=RollingFrequencyControl
    if selection['consensus_allowed']:
        from src.models.transformed_space import ModularDifferenceConsensus
        result['ModularDifferenceConsensus']=lambda:ModularDifferenceConsensus(*(construct(selection['models'][n]) for n in PRIMARY_MODELS))
    return result


def annotate_cutoffs(rows):
    rows=rows.copy();rows['outer_fit_cutoff']=rows.training_cutoff
    mask=rows.model.isin([*PRIMARY_MODELS,*OPTIONAL_MODELS])
    rows.loc[mask,'training_cutoff']=rows.loc[mask,'feature_cutoff']
    rows['transformed_training_cutoff']=pd.array(np.where(mask,rows.feature_cutoff,np.nan),dtype='Int64')
    return rows


def evaluate(history,selection,*,cadence=26,progress=None):
    from src.analysis.features import build_prospective_features,GAP
    from src.prediction_scope import ProspectiveScope
    from src.analysis.spatiotemporal import lotto_matrix
    from src.backtest.translation import walk_forward
    if len(history)>1245:raise ValueError('H13 cutoff1245')
    x=lotto_matrix(history,cutoff=len(history))
    if sha256(x[:900].tobytes()).hexdigest()!=selection['development_matrix_hash']:raise ValueError('Development prefix mismatch')
    f=build_prospective_features(history,scope=ProspectiveScope(len(history)),progress=progress)
    f=f[f.target_draw<=len(history)][['target_draw','feature_cutoff','number','appeared_next',*GAP]]
    return annotate_cutoffs(walk_forward(history,factories(selection),start=901,end=len(history),cadence=cadence,
        gap_features=f,combined=False,progress=progress))


def paired_report(rows,*,replicates=2000,block=26):
    result=[]
    for start in (901,1001,1101):
        groups={n:g.sort_values('target_draw') for n,g in rows[rows.target_draw>=start].groupby('model')}
        n=len(groups['RandomModel']);rng=np.random.default_rng(150042)
        indices=((rng.integers(0,n,(replicates,int(np.ceil(n/block))))[:,:,None]+np.arange(block))%n).reshape(replicates,-1)[:,:n]
        for name in (*PRIMARY_MODELS,*OPTIONAL_MODELS):
            if name not in groups:continue
            a=groups[name]
            for reference in ('RandomModel','GapLogistic'):
                b=groups[reference]
                if a.target_draw.tolist()!=b.target_draw.tolist():raise ValueError('Paired target mismatch')
                metrics={k:(a[k].to_numpy(),b[k].to_numpy()) for k in ('hits','recall_6','recall_10','recall_15','mean_winning_rank')}
                metrics.update({f'pool_{k}_{v}plus':((a[f'pool_{k}']>=v).astype(int).to_numpy(),(b[f'pool_{k}']>=v).astype(int).to_numpy())
                    for k in (6,8,10,12,15) for v in (5,6)})
                for metric,(aa,bb) in metrics.items():
                    delta=aa-bb;lo,hi=np.quantile(delta[indices].mean(1),[.025,.975])
                    result.append(dict(model=name,reference=reference,start=start,metric=metric,difference=float(delta.mean()),
                        ci_low=float(lo),ci_high=float(hi),block=block,degenerate=bool(lo==hi)))
    return pd.DataFrame(result)


def correlation_report(rows,*,graph_path=None):
    result=[];old=pd.read_csv(graph_path) if graph_path and Path(graph_path).is_file() else None
    for target,g in rows.groupby('target_draw'):
        references={'GapLogistic':json.loads(g[g.model=='GapLogistic'].iloc[0].ranking)}
        if old is not None:
            matched=old[(old.target_draw==target)&(old.model=='GraphStructureModel')]
            if len(matched)==1:references['Phase14Graph']=json.loads(matched.iloc[0].ranking)
        for row in g[g.model.isin([*PRIMARY_MODELS,*OPTIONAL_MODELS])].itertuples():
            for reference,ranking in references.items():result.append(dict(model=row.model,target_draw=target,reference=reference,
                **rank_diversity(json.loads(row.ranking),ranking)))
    return pd.DataFrame(result)


def sensitivity(x,selection,*,progress=None):
    x=research_matrix(x);specs={n:c for n,c in candidates().items() if c['model']!='GapShapeModel' or selection['shape_allowed']}
    rows=[];models={n:construct(c) for n,c in specs.items()}
    for target in range(901,1246):
        past=x[:target-1]
        for name,model in models.items():
            top=rank_numbers(model.fit(past,cutoff=target-1).score_matrix(past,target=target))[:6]
            rows.append(dict(candidate=name,model=specs[name]['model'],target_draw=target,hits=int(x[target-1,np.array(top)-1].sum())))
        if progress and target%25==0:progress(f'Sensitivity{target}/1245')
    return pd.DataFrame(rows)
