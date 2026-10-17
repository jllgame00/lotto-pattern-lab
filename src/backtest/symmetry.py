"""H16 development-only selection and immutable historical comparisons.

MirrorModel is imported only by construct: descriptive/null work can complete
before the optional historical model implementation exists.
"""
from functools import partial
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.recurrence import research_matrix
from src.backtest.multiscale import rank_diversity
from src.backtest.ranking import rank_metrics
from src.models.predictive import rank_numbers

WINDOWS=(10,26,52)
LAGS=(1,2,3,4,8,13,26,52)
FROZEN_DIRECTORY=Path('reports/transformed_space')
SELECTION_METRIC='meanTop6hits;tiesdeclaredorder'


def configuration_hash(selection):
    return sha256(json.dumps(selection,sort_keys=True,allow_nan=False).encode()).hexdigest()


def candidates():
    return {f'mirror_W{w}_lag{lag}_shrink{shrink}':dict(model='MirrorModel',window=w,
        lag=lag,shrinkage=shrink,support=20) for w in WINDOWS for lag in LAGS for shrink in (50,200)}


def construct(config):
    if not _declared_config(config):raise ValueError('Unknown H16 configuration')
    from src.models.symmetry import MirrorModel
    kwargs=dict(config);kwargs.pop('model')
    return MirrorModel(**kwargs)


def _declared_config(config):
    return (isinstance(config,dict) and config in list(candidates().values()) and
        type(config.get('model')) is str and
        all(type(config.get(key)) is int for key in ('window','lag','shrinkage','support')))


def select_development(rows,*,end=900):
    if (type(end) is not int or not 401<=end<=900 or rows.empty or
        not {'candidate','target_draw','hits'}<=set(rows) or
        not rows.target_draw.between(401,end).all() or
        not np.equal(rows.target_draw,np.floor(rows.target_draw)).all() or
        rows.duplicated(['candidate','target_draw']).any() or
        not rows.hits.between(0,6).all()):
        raise ValueError('Unique development-only targets401..900 required')
    groups={name:g for name,g in rows.groupby('candidate',sort=False)}
    targets=sorted(next(iter(groups.values())).target_draw)
    if any(sorted(g.target_draw)!=targets for g in groups.values()):
        raise ValueError('Matching development targets required')
    # Grid order is a declared tie breaker even when input rows are shuffled.
    order=[name for name in candidates() if name in groups]
    order.extend(name for name in groups if name not in order)
    return max(order,key=lambda name:float(groups[name].hits.mean()))


def development_search(x,*,progress=None):
    x=research_matrix(x)
    if len(x)!=900:raise ValueError('Development requires exact draws1..900')
    specs=candidates();models={name:construct(config) for name,config in specs.items()};rows=[]
    for target in range(401,901):
        past=x[:target-1].copy()
        for name,model in models.items():
            ranking=rank_numbers(model.fit(past,cutoff=target-1).score_matrix(past,target=target))
            rows.append(dict(candidate=name,model='MirrorModel',target_draw=target,
                feature_cutoff=target-1,training_cutoff=target-1,
                hits=int(x[target-1,np.array(ranking[:6])-1].sum())))
        ranking=rank_numbers(dict(enumerate(past[-26:].mean(0).tolist(),1)))
        rows.append(dict(candidate='frequency26',model='Frequency26',target_draw=target,
            feature_cutoff=target-1,training_cutoff=target-1,
            hits=int(x[target-1,np.array(ranking[:6])-1].sum())))
        if progress and target%25==0:progress(f'Development {target}/900')
    table=pd.DataFrame(rows);name=select_development(table[table.model=='MirrorModel'])
    selection=dict(version='phase18-v1',research_cutoff=1245,development_start=401,
        development_end=900,later_start=901,models={'MirrorModel':specs[name]},
        selected_candidates={'MirrorModel':name},candidate_count=48,pair_model_allowed=False,
        support=20,selection_metric=SELECTION_METRIC,
        development_matrix_hash=sha256(x.tobytes()).hexdigest(),draw1246_used=False)
    return selection,table


def _validate_selection(s):
    expected=dict(version='phase18-v1',research_cutoff=1245,development_start=401,
        development_end=900,later_start=901,candidate_count=48,pair_model_allowed=False,
        support=20,selection_metric=SELECTION_METRIC,draw1246_used=False)
    if not isinstance(s,dict) or any(key not in s or type(s[key]) is not type(value) or s[key]!=value for key,value in expected.items()):
        raise ValueError('Frozen H16 configuration integrity mismatch')
    specs=candidates();models=s.get('models');names=s.get('selected_candidates')
    if (not isinstance(models,dict) or set(models)!={'MirrorModel'} or
        not isinstance(names,dict) or set(names)!={'MirrorModel'} or
        names['MirrorModel'] not in specs or models['MirrorModel']!=specs[names['MirrorModel']] or
        not _declared_config(models['MirrorModel']) or
        not isinstance(s.get('development_matrix_hash'),str) or
        len(s['development_matrix_hash'])!=64 or
        any(c not in '0123456789abcdef' for c in s['development_matrix_hash'])):
        raise ValueError('Unknown H16 model configuration or source hash')
    return s


def load_selection(path):
    try:
        payload=json.loads(Path(path).read_text(encoding='utf-8'));selection=payload['selection']
        if payload['sha256']!=configuration_hash(selection):raise ValueError('Frozen H16 hash mismatch')
        return _validate_selection(selection)
    except (KeyError,TypeError,json.JSONDecodeError) as exc:
        raise ValueError('Invalid H16 selection schema') from exc


def factories(selection):
    _validate_selection(selection)
    from src.models.graph_hypergraph import RollingFrequencyControl
    return {'MirrorModel':partial(construct,selection['models']['MirrorModel']),
        'Frequency26':partial(RollingFrequencyControl,window=26)}


def annotate_cutoffs(rows):
    rows=rows.copy();rows['outer_fit_cutoff']=rows.training_cutoff
    fresh=rows.model.isin(['MirrorModel','Frequency26'])
    rows.loc[fresh,'training_cutoff']=rows.loc[fresh,'feature_cutoff']
    rows['mirror_training_cutoff']=pd.array(np.where(rows.model=='MirrorModel',rows.feature_cutoff,np.nan),dtype='Int64')
    return rows


def _decoded_list(value):
    result=json.loads(value) if isinstance(value,str) else value
    if not isinstance(result,list) or any(type(n) is not int for n in result):
        raise ValueError('Integer ranking/actual lists required')
    return result


def _validate_predictions(rows,*,targets=None,x=None):
    required={'target_draw','training_cutoff','feature_cutoff','ranking','actual'}
    if rows.empty or not required<=set(rows) or rows.target_draw.duplicated().any():
        raise ValueError('Unique matched frozen targets required')
    if targets is not None and sorted(rows.target_draw)!=list(targets):
        raise ValueError('Frozen paired target mismatch')
    for row in rows.itertuples():
        t=row.target_draw
        if (isinstance(t,bool) or not isinstance(t,(int,np.integer)) or not 901<=t<=1245 or
            row.feature_cutoff!=t-1 or not 0<=row.training_cutoff<t or
            not float(row.training_cutoff).is_integer()):
            raise ValueError('Frozen causal cutoff mismatch')
        ranking=_decoded_list(row.ranking);actual=_decoded_list(row.actual)
        if sorted(ranking)!=list(range(1,46)) or len(actual)!=6 or len(set(actual))!=6 or not set(actual)<=set(range(1,46)):
            raise ValueError('Invalid complete ranking or actual numbers')
        if x is not None and actual!=sorted((np.flatnonzero(x[t-1])+1).tolist()):
            raise ValueError('Frozen actual/source prefix mismatch')
        metrics=rank_metrics(ranking,set(actual))
        metrics.update({f'pool_{k}':len(set(ranking[:k])&set(actual)) for k in (6,8,10,12,15)})
        for key,value in metrics.items():
            if key not in rows or not np.isclose(getattr(row,key),value,rtol=0,atol=1e-12):
                raise ValueError('Frozen ranking metric integrity mismatch')
    return rows.sort_values('target_draw').copy()


def frozen_gap(x,*,cadence=26):
    """Read verified Phase15 output, with no feature building or old model fit."""
    x=research_matrix(x)
    if not 901<=len(x)<=1245 or cadence not in (13,26):raise ValueError('Bounded frozen cadence13/26 required')
    directory=Path(FROZEN_DIRECTORY)
    try:
        manifest=json.loads((directory/'run_manifest.json').read_text(encoding='utf-8'))
        if manifest['research_cutoff']!=1245 or manifest['draw1246_used'] is not False:raise ValueError('Frozen source boundary mismatch')
        def verified(relative):
            path=directory/relative;raw=path.read_bytes()
            if sha256(raw).hexdigest()!=manifest['artifacts'][relative]['sha256']:
                raise ValueError('Frozen artifact hash integrity mismatch')
            return raw
        metadata=json.loads(verified('analysis_metadata.json'))
        raw=verified(f'walk_forward_{cadence}/predictions.csv')
        from io import BytesIO
        frozen=pd.read_csv(BytesIO(raw));frozen=frozen[frozen.model=='GapLogistic'].copy()
        frozen=_validate_predictions(frozen,targets=range(901,1246))
        # Current first900 plus the verified archive must reproduce its entire
        # declared source matrix. This also supports a shorter current prefix.
        full=np.zeros((1245,45),dtype=bool);full[:900]=x[:900]
        for row in frozen.itertuples():full[row.target_draw-1,np.array(_decoded_list(row.actual))-1]=True
        if sha256(full.tobytes()).hexdigest()!=metadata['matrix_hash'] or not np.array_equal(full[:len(x)],x):
            raise ValueError('Frozen source prefix hash mismatch')
        return _validate_predictions(frozen[frozen.target_draw<=len(x)],targets=range(901,len(x)+1),x=x)
    except (OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        raise ValueError('Missing or invalid frozen Gap artifact integrity evidence') from exc


def evaluate(history,selection,*,cadence=26,progress=None):
    from src.analysis.spatiotemporal import lotto_matrix
    from src.backtest.translation import walk_forward
    _validate_selection(selection)
    if not 901<=len(history)<=1245 or cadence not in (13,26):raise ValueError('H16 bounded cadence13/26 required')
    x=lotto_matrix(history,cutoff=len(history))
    if sha256(x[:900].tobytes()).hexdigest()!=selection['development_matrix_hash']:
        raise ValueError('Development source prefix mismatch')
    gap=frozen_gap(x,cadence=cadence)
    rows=annotate_cutoffs(walk_forward(history,factories(selection),start=901,end=len(history),cadence=cadence,
        gap_features=None,combined=False,progress=progress))
    gap['outer_fit_cutoff']=gap.training_cutoff
    result=pd.concat([rows,gap],ignore_index=True)
    for name,g in result.groupby('model'):_validate_predictions(g,targets=range(901,len(x)+1),x=x)
    return result


def paired_report(rows,*,replicates=2000,block=26):
    if type(replicates) is not int or replicates<1 or type(block) is not int or block<1:
        raise ValueError('Positive bootstrap count and block required')
    required=('MirrorModel','RandomModel','Frequency26','GapLogistic')
    if not set(required)<=set(rows.model) or rows.duplicated(['model','target_draw']).any():
        raise ValueError('Unique paired references required')
    allgroups={name:rows[rows.model==name].sort_values('target_draw') for name in required}
    targets=allgroups['MirrorModel'].target_draw.tolist()
    if not targets or any(g.target_draw.tolist()!=targets for g in allgroups.values()):raise ValueError('Paired target mismatch')
    if min(targets)<901 or max(targets)>1245:raise ValueError('Later targets901..1245 only')
    result=[]
    for start in (901,1001,1101):
        groups={name:g[g.target_draw>=start] for name,g in allgroups.items()};a=groups['MirrorModel'];n=len(a)
        if not n:continue
        rng=np.random.default_rng(180042);length=min(block,n)
        indices=((rng.integers(0,n,(replicates,int(np.ceil(n/length))))[:,:,None]+np.arange(length))%n).reshape(replicates,-1)[:,:n]
        for reference in required[1:]:
            b=groups[reference]
            metrics={key:(a[key].to_numpy(),b[key].to_numpy()) for key in ('hits','recall_6','recall_10','recall_15','mean_winning_rank')}
            metrics.update({f'pool_{k}_{threshold}plus':((a[f'pool_{k}']>=threshold).to_numpy(dtype=float),
                (b[f'pool_{k}']>=threshold).to_numpy(dtype=float)) for k in (6,8,10,12,15) for threshold in (5,6)})
            for metric,(aa,bb) in metrics.items():
                delta=aa-bb;low,high=np.quantile(delta[indices].mean(1),[.025,.975])
                result.append(dict(model='MirrorModel',reference=reference,start=start,targets=n,metric=metric,
                    difference=float(delta.mean()),ci_low=float(low),ci_high=float(high),block=block,
                    replicates=replicates,degenerate=bool(low==high)))
    return pd.DataFrame(result)


def correlation_report(rows,*,graph_path=None,shape_path=None,mi_path=None):
    if rows.duplicated(['model','target_draw']).any():raise ValueError('Unique diversity targets required')
    result=[];mirror=rows[rows.model=='MirrorModel'].sort_values('target_draw')
    references={'GapLogistic':rows[rows.model=='GapLogistic']}
    for path,name,label in ((graph_path,'GraphStructureModel','Phase14Graph'),
        (shape_path,'GapShapeModel','Phase15GapShape'),(mi_path,'MutualInformationModel','Phase13MI')):
        if path is None:continue
        old=pd.read_csv(path)
        references[label]=old[(old.model==name)&old.target_draw.isin(mirror.target_draw)]
    _validate_predictions(mirror)
    actuals={row.target_draw:set(_decoded_list(row.actual)) for row in mirror.itertuples()}
    for label,reference in references.items():
        if reference.empty:
            if label=='GapLogistic':raise ValueError('Matched Gap reference required')
            continue
        _validate_predictions(reference)
        if label=='GapLogistic' and sorted(reference.target_draw)!=sorted(mirror.target_draw):raise ValueError('Diversity target mismatch')
        indexed=reference.set_index('target_draw')
        for row in mirror.itertuples():
            if row.target_draw not in indexed.index:continue
            other=indexed.loc[row.target_draw]
            if set(_decoded_list(other.actual))!=actuals[row.target_draw]:raise ValueError('Frozen reference actual mismatch')
            result.append(dict(model='MirrorModel',target_draw=row.target_draw,reference=label,
                **rank_diversity(_decoded_list(row.ranking),_decoded_list(other.ranking))))
    return pd.DataFrame(result)


def sensitivity(x,selection,*,progress=None):
    """Predeclared adjacent W/lag cells only; descriptive and never reselect."""
    x=research_matrix(x);_validate_selection(selection)
    if len(x)<901:raise ValueError('Later diagnostic prefix required')
    selected=selection['models']['MirrorModel'];wi=WINDOWS.index(selected['window']);li=LAGS.index(selected['lag'])
    windows=WINDOWS[max(0,wi-1):wi+2];lags=LAGS[max(0,li-1):li+2]
    specs={name:c for name,c in candidates().items() if c['window'] in windows and c['lag'] in lags and c['shrinkage']==selected['shrinkage']}
    models={name:construct(c) for name,c in specs.items()};rows=[]
    for target in range(901,len(x)+1):
        past=x[:target-1]
        for name,model in models.items():
            rank=rank_numbers(model.fit(past,cutoff=target-1).score_matrix(past,target=target))
            rows.append(dict(candidate=name,model='MirrorModel',target_draw=target,diagnostic_only=True,
                hits=int(x[target-1,np.array(rank[:6])-1].sum())))
        if progress and target%25==0:progress(f'Sensitivity {target}/{len(x)}')
    return pd.DataFrame(rows)
