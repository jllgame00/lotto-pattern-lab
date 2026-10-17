"""H18: development-only regime selection and frozen historical comparisons.

Model imports are lazy so structural analysis does not depend on a predictive
implementation. The old Gap predictions are read through the verified H16
archive reader; no previous model is constructed or fitted here.
"""
from functools import partial
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.recurrence import research_matrix
from src.backtest.multiscale import rank_diversity
from src.backtest.ranking import rank_metrics
from src.backtest.symmetry import frozen_gap, _decoded_list, _validate_predictions
from src.models.predictive import rank_numbers

REPRESENTATIONS = ('A','B13','B26','B52','C')
MINIMUMS = (26,52,104)
MULTIPLIERS = (1,2)
SHRINKAGES = (26,104)
WINDOWS = (26,52,104)
FIXED = tuple(f'Frequency{w}' for w in WINDOWS)
MODEL = 'RegimeFrequencyModel'
COMBINATION = 'GapRegimeRankAverage'
SELECTION_METRIC = 'meanTop6hits;tiesdeclaredorder'
COMBINATION_RULE = 'equal ranks; regime>.8 overall and both development halves; regime>best fixed overall'


def configuration_hash(selection):
    return sha256(json.dumps(selection,sort_keys=True,allow_nan=False).encode()).hexdigest()


def candidates():
    return {f'regime_{representation}_min{minimum}_p{multiplier}_s{shrinkage}':
        dict(model=MODEL,representation=representation,minimum=minimum,
             multiplier=multiplier,shrinkage=shrinkage)
        for representation in REPRESENTATIONS for minimum in MINIMUMS
        for multiplier in MULTIPLIERS for shrinkage in SHRINKAGES}


def _declared_config(config):
    return (isinstance(config,dict) and config in list(candidates().values()) and
        type(config.get('model')) is str and type(config.get('representation')) is str and
        all(type(config.get(key)) is int for key in ('minimum','multiplier','shrinkage')))


def construct(config):
    if not _declared_config(config):
        raise ValueError('Unknown H18 regime configuration')
    from src.models.change_point import RegimeFrequencyModel
    kwargs = dict(config); kwargs.pop('model')
    return RegimeFrequencyModel(**kwargs)


def construct_baseline(window):
    if type(window) is not int or window not in WINDOWS:
        raise ValueError('Declared fixed window26/52/104 required')
    from src.models.change_point import AdaptiveWindowBaseline
    return AdaptiveWindowBaseline(window=window)


def select_development(rows, *, end=900):
    order = list(candidates()) + list(FIXED)
    if (type(end) is not int or not 401<=end<=900 or rows.empty or
        not {'candidate','target_draw','hits'}<=set(rows)):
        raise ValueError('Unique development-only targets401..900 required')
    try:
        invalid = (not rows.target_draw.between(401,end).all() or
            not np.equal(rows.target_draw,np.floor(rows.target_draw)).all() or
            not rows.hits.between(0,6).all() or
            not np.equal(rows.hits,np.floor(rows.hits)).all() or
            rows.duplicated(['candidate','target_draw']).any() or
            not set(rows.candidate)<=set(order))
    except (TypeError,ValueError):
        invalid = True
    if invalid:
        raise ValueError('Unique declared development candidates and integer hits required')
    groups = {name:g for name,g in rows.groupby('candidate',sort=False)}
    targets = sorted(next(iter(groups.values())).target_draw)
    if any(sorted(g.target_draw)!=targets for g in groups.values()):
        raise ValueError('Matching development targets required')
    return max((name for name in order if name in groups),key=lambda n:float(groups[n].hits.mean()))


def _combo_allowed(metrics):
    return bool(metrics['regime_mean']>.8 and
        metrics['regime_mean']>max(metrics['fixed_means'].values()) and
        metrics['regime_first_half']>.8 and metrics['regime_second_half']>.8)


def development_search(x, *, progress=None):
    x = research_matrix(x)
    if len(x)!=900:
        raise ValueError('Development requires exact draws1..900')
    specs = candidates()
    models = {name:construct(config) for name,config in specs.items()}
    models.update({name:construct_baseline(window) for name,window in zip(FIXED,WINDOWS)})
    rows = []
    for target in range(401,901):
        past = x[:target-1].copy()
        # Finish every prediction before consulting this target's winning row.
        rankings = {name:rank_numbers(model.fit(past,cutoff=target-1).score_matrix(past,target=target))
            for name,model in models.items()}
        for name,ranking in rankings.items():
            rows.append(dict(candidate=name,model=MODEL if name in specs else name,
                target_draw=target,feature_cutoff=target-1,training_cutoff=target-1,
                hits=int(x[target-1,np.array(ranking[:6])-1].sum())))
        if progress and target%25==0:
            progress(f'Development {target}/900')
    table = pd.DataFrame(rows)
    name = select_development(table[table.model==MODEL])
    best_fixed = select_development(table[table.candidate.isin(FIXED)])
    chosen = table[table.candidate==name]
    metrics = dict(regime_mean=float(chosen.hits.mean()),
        regime_first_half=float(chosen[chosen.target_draw<=650].hits.mean()),
        regime_second_half=float(chosen[chosen.target_draw>=651].hits.mean()),
        fixed_means={n:float(table[table.candidate==n].hits.mean()) for n in FIXED})
    selection = dict(version='phase19-v1',research_cutoff=1245,development_start=401,
        development_end=900,later_start=901,candidate_count=60,
        models={MODEL:specs[name]},selected_candidates={MODEL:name},
        best_fixed_frequency=best_fixed,combo_allowed=_combo_allowed(metrics),
        selection_metric=SELECTION_METRIC,combination_rule=COMBINATION_RULE,
        development_metrics=metrics,development_matrix_hash=sha256(x.tobytes()).hexdigest(),
        draw1246_used=False)
    return _validate_selection(selection),table


def _validate_selection(selection):
    expected = dict(version='phase19-v1',research_cutoff=1245,development_start=401,
        development_end=900,later_start=901,candidate_count=60,
        selection_metric=SELECTION_METRIC,combination_rule=COMBINATION_RULE,draw1246_used=False)
    variable = {'models','selected_candidates','best_fixed_frequency','combo_allowed',
        'development_metrics','development_matrix_hash'}
    if (not isinstance(selection,dict) or set(selection)!=set(expected)|variable or
        any(type(selection[k]) is not type(v) or selection[k]!=v for k,v in expected.items())):
        raise ValueError('Frozen H18 configuration schema integrity mismatch')
    models = selection['models']; names = selection['selected_candidates']; specs = candidates()
    if (not isinstance(models,dict) or set(models)!={MODEL} or
        not isinstance(names,dict) or set(names)!={MODEL} or not isinstance(names[MODEL],str) or
        names[MODEL] not in specs or models[MODEL]!=specs[names[MODEL]] or
        not _declared_config(models[MODEL])):
        raise ValueError('Unknown H18 frozen grid configuration')
    digest = selection['development_matrix_hash']
    if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('Invalid development source hash')
    m = selection['development_metrics']
    if (not isinstance(m,dict) or set(m)!={'regime_mean','regime_first_half','regime_second_half','fixed_means'} or
        not isinstance(m['fixed_means'],dict) or set(m['fixed_means'])!=set(FIXED)):
        raise ValueError('Invalid frozen development metric schema')
    values = [m[k] for k in ('regime_mean','regime_first_half','regime_second_half')]+list(m['fixed_means'].values())
    if (any(type(v) not in (int,float) or not np.isfinite(v) or not 0<=v<=6 for v in values) or
        not np.isclose(m['regime_mean'],(m['regime_first_half']+m['regime_second_half'])/2,rtol=0,atol=1e-12)):
        raise ValueError('Invalid frozen development metric values')
    best = max(FIXED,key=lambda name:m['fixed_means'][name])
    if (selection['best_fixed_frequency']!=best or type(selection['combo_allowed']) is not bool or
        selection['combo_allowed']!=_combo_allowed(m)):
        raise ValueError('Development-only fixed selection or combination gate mismatch')
    return selection


def load_selection(path):
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(payload,dict) or set(payload)!={'selection','sha256'}:
            raise ValueError('Invalid H18 selection envelope')
        selection = payload['selection']
        if payload['sha256']!=configuration_hash(selection):
            raise ValueError('Frozen H18 hash mismatch')
        return _validate_selection(selection)
    except (KeyError,TypeError,json.JSONDecodeError) as exc:
        raise ValueError('Invalid H18 selection schema') from exc


def factories(selection):
    _validate_selection(selection)
    return {MODEL:partial(construct,dict(selection['models'][MODEL])),
        **{name:partial(construct_baseline,window) for name,window in zip(FIXED,WINDOWS)}}


def annotate_cutoffs(rows):
    rows = rows.copy()
    rows['outer_fit_cutoff'] = rows.training_cutoff
    fresh = rows.model.isin((MODEL,*FIXED))
    rows.loc[fresh,'training_cutoff'] = rows.loc[fresh,'feature_cutoff']
    rows['regime_training_cutoff'] = pd.array(
        np.where(rows.model==MODEL,rows.feature_cutoff,np.nan),dtype='Int64')
    return rows


def _diagnostic(state, scores, past, target, representation):
    if state is None:
        return dict(target_draw=target,diagnostics_available=False)
    try:
        cutoff = state['training_cutoff']; boundary = state['last_change_point']
        length = state['segment_length']; rates = np.asarray(state['segment_rates'],dtype=float)
        current = np.asarray(state.get('current_rates',[scores[n] for n in range(1,46)]),dtype=float)
        if (any(isinstance(v,(bool,np.bool_)) or not isinstance(v,(int,np.integer)) for v in (cutoff,boundary,length)) or
            cutoff!=target-1 or not 0<=boundary<cutoff or length!=cutoff-boundary or
            state['representation']!=representation or rates.shape!=(45,) or current.shape!=(45,) or
            not np.isfinite(rates).all() or not np.isfinite(current).all() or
            not ((rates>=0)&(rates<=1)).all() or not ((current>=0)&(current<=1)).all()):
            raise ValueError('Invalid current segment state')
        if not np.allclose(rates,past[boundary:cutoff].mean(0),rtol=0,atol=1e-12):
            raise ValueError('Current segment audit rates/source prefix mismatch')
        return dict(target_draw=target,diagnostics_available=True,source_cutoff=int(cutoff),
            last_change_point=int(boundary),current_segment_length=int(length),
            segment_rates=json.dumps(rates.tolist()),current_rates=json.dumps(current.tolist()),
            representation=representation)
    except (KeyError,TypeError) as exc:
        raise ValueError('Invalid current segment audit state') from exc


class _CaptureState:
    """Keep the engine's outer fit cutoff while snapshotting adaptive score state."""
    def __init__(self, model, collector, representation):
        self.model = model; self.collector = collector; self.representation = representation

    def fit(self, past, *, cutoff):
        self.model.fit(past,cutoff=cutoff)
        self.training_cutoff = cutoff
        return self

    def score_matrix(self, past, *, target):
        scores = self.model.score_matrix(past,target=target)
        state = getattr(self.model,'last_state',None)
        if state is None and type(self.model).__module__=='src.models.change_point':
            raise ValueError('Canonical regime model must expose current segment audit state')
        self.collector.append(_diagnostic(state,scores,past,target,self.representation))
        return scores


def _combination_rows(regime, gap):
    # Compute the complete rank average before looking at any stored actual.
    parents = {row.target_draw:_decoded_list(row.ranking) for row in gap.itertuples()}
    predictions = []
    for row in regime.itertuples():
        a = _decoded_list(row.ranking); b = parents[row.target_draw]
        scores = {n:-(a.index(n)+b.index(n)+2)/2 for n in range(1,46)}
        predictions.append((row,rank_numbers(scores),scores))
    result = []
    gap_cutoffs = gap.set_index('target_draw').training_cutoff
    for row,ranking,scores in predictions:
        actual = set(_decoded_list(row.actual))
        result.append(dict(model=COMBINATION,target_draw=row.target_draw,
            training_cutoff=row.target_draw-1,feature_cutoff=row.target_draw-1,
            outer_fit_cutoff=row.outer_fit_cutoff,regime_training_cutoff=row.training_cutoff,
            gap_training_cutoff=int(gap_cutoffs.loc[row.target_draw]),
            ranking=json.dumps(ranking),scores=json.dumps(scores,sort_keys=True),actual=json.dumps(sorted(actual)),
            **rank_metrics(ranking,actual),
            **{f'pool_{k}':len(set(ranking[:k])&actual) for k in (6,8,10,12,15)}))
    return pd.DataFrame(result)


def evaluate(history, selection, *, cadence=26, progress=None):
    from src.analysis.spatiotemporal import lotto_matrix
    from src.backtest.translation import walk_forward
    _validate_selection(selection)
    if not 901<=len(history)<=1245 or type(cadence) is not int or cadence not in (13,26):
        raise ValueError('H18 bounded cadence13/26 required')
    x = lotto_matrix(history,cutoff=len(history))
    if sha256(x[:900].tobytes()).hexdigest()!=selection['development_matrix_hash']:
        raise ValueError('Development source prefix mismatch')
    gap = frozen_gap(x,cadence=cadence)
    _validate_predictions(gap,targets=range(901,len(x)+1),x=x)
    makers = factories(selection); collector = []
    config = dict(selection['models'][MODEL])
    makers[MODEL] = lambda:_CaptureState(construct(config),collector,config['representation'])
    rows = annotate_cutoffs(walk_forward(history,makers,start=901,end=len(history),cadence=cadence,
        gap_features=None,combined=False,progress=progress))
    diagnostics = pd.DataFrame(collector).set_index('target_draw')
    for key in ('diagnostics_available','source_cutoff','last_change_point','current_segment_length',
                'segment_rates','current_rates','representation'):
        rows[key] = rows.target_draw.map(diagnostics[key]).astype(object) if key in diagnostics else None
        rows.loc[rows.model!=MODEL,key] = None
    gap['outer_fit_cutoff'] = gap.training_cutoff
    frames = [rows,gap]
    if selection['combo_allowed']:
        frames.append(_combination_rows(rows[rows.model==MODEL],gap))
    result = pd.concat(frames,ignore_index=True)
    for _,group in result.groupby('model'):
        _validate_predictions(group,targets=range(901,len(x)+1),x=x)
    return result


def paired_report(rows, selection, *, replicates=2000, block=26):
    _validate_selection(selection)
    if type(replicates) is not int or replicates<1 or type(block) is not int or block not in (13,26,52):
        raise ValueError('Positive bootstrap count and declared block13/26/52 required')
    references = ('RandomModel',selection['best_fixed_frequency'],'GapLogistic')
    models = (MODEL,COMBINATION) if selection['combo_allowed'] else (MODEL,)
    required = set(models)|set(references)
    if (not required<=set(rows.model) or rows.duplicated(['model','target_draw']).any() or
        (not selection['combo_allowed'] and COMBINATION in set(rows.model))):
        raise ValueError('Unique paired references and frozen combination choice required')
    groups = {name:_validate_predictions(rows[rows.model==name]) for name in required}
    targets = groups[MODEL].target_draw.tolist()
    if any(group.target_draw.tolist()!=targets for group in groups.values()):
        raise ValueError('Paired target mismatch')
    output = []
    for start in (901,1001,1101):
        subgroups = {name:group[group.target_draw>=start] for name,group in groups.items()}
        n = len(subgroups[MODEL])
        if not n:continue
        rng = np.random.default_rng(190042); length = min(block,n)
        indices = ((rng.integers(0,n,(replicates,int(np.ceil(n/length))))[:,:,None]+
                    np.arange(length))%n).reshape(replicates,-1)[:,:n]
        for model in models:
            model_references = references if model==MODEL else (*references,MODEL)
            a = subgroups[model]
            for reference in model_references:
                b = subgroups[reference]
                metrics = {key:(a[key].to_numpy(),b[key].to_numpy()) for key in
                    ('hits','recall_6','recall_10','recall_15','mean_winning_rank')}
                metrics.update({f'pool_{k}_{threshold}plus':
                    ((a[f'pool_{k}']>=threshold).to_numpy(dtype=float),
                     (b[f'pool_{k}']>=threshold).to_numpy(dtype=float))
                    for k in (6,8,10,12,15) for threshold in (5,6)})
                for metric,(aa,bb) in metrics.items():
                    delta = aa-bb; low,high = np.quantile(delta[indices].mean(1),[.025,.975])
                    output.append(dict(model=model,reference=reference,start=start,targets=n,metric=metric,
                        difference=float(delta.mean()),ci_low=float(low),ci_high=float(high),block=block,
                        replicates=replicates,degenerate=bool(low==high),secondary=bool(model==COMBINATION)))
    return pd.DataFrame(output)


def _verified_archive(path):
    path = Path(path)
    try:
        for directory in path.parents:
            manifest_path = directory/'run_manifest.json'
            if not manifest_path.is_file():continue
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            relative = path.relative_to(directory).as_posix(); raw = path.read_bytes()
            if (manifest['research_cutoff']!=1245 or manifest['draw1246_used'] is not False or
                manifest['artifacts'][relative]['sha256']!=sha256(raw).hexdigest()):
                raise ValueError('Frozen diversity artifact hash integrity mismatch')
            return pd.read_csv(BytesIO(raw))
        raise ValueError('Frozen diversity manifest integrity evidence required')
    except (OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        raise ValueError('Invalid frozen diversity artifact integrity evidence') from exc


def correlation_report(rows, *, graph_path=None, shape_path=None, mirror_path=None):
    if rows.duplicated(['model','target_draw']).any():
        raise ValueError('Unique diversity targets required')
    regime = _validate_predictions(rows[rows.model==MODEL])
    targets = regime.target_draw.tolist()
    references = {'GapLogistic':_validate_predictions(rows[rows.model=='GapLogistic'],targets=targets)}
    for path,name,label in ((graph_path,'GraphStructureModel','Phase14Graph'),
            (shape_path,'GapShapeModel','Phase15GapShape'),(mirror_path,'MirrorModel','Phase18Mirror')):
        if path is None or not Path(path).is_file():continue
        old = _verified_archive(path)
        selected = old[(old.model==name)&old.target_draw.isin(targets)]
        if not selected.empty:references[label] = _validate_predictions(selected)
    output = []
    for label,reference in references.items():
        indexed = reference.set_index('target_draw')
        for row in regime.itertuples():
            if row.target_draw not in indexed.index:continue
            other = indexed.loc[row.target_draw]
            if set(_decoded_list(other.actual))!=set(_decoded_list(row.actual)):
                raise ValueError('Frozen diversity actual mismatch')
            output.append(dict(model=MODEL,target_draw=row.target_draw,reference=label,
                **rank_diversity(_decoded_list(row.ranking),_decoded_list(other.ranking))))
    return pd.DataFrame(output)


def sensitivity(x, selection, *, progress=None):
    """One adjacent coordinate at a time; diagnostic only, never reselect."""
    x = research_matrix(x); _validate_selection(selection)
    if len(x)<901:
        raise ValueError('Later diagnostic prefix required')
    if sha256(x[:900].tobytes()).hexdigest()!=selection['development_matrix_hash']:
        raise ValueError('Development source prefix mismatch')
    chosen = selection['models'][MODEL]
    grids = dict(minimum=MINIMUMS,multiplier=MULTIPLIERS,shrinkage=SHRINKAGES)
    def adjacent(config):
        changed = [key for key in grids if config[key]!=chosen[key]]
        return (config['representation']==chosen['representation'] and len(changed)<=1 and
            all(abs(grids[key].index(config[key])-grids[key].index(chosen[key]))==1 for key in changed))
    specs = {name:config for name,config in candidates().items() if adjacent(config)}
    models = {name:construct(config) for name,config in specs.items()}; rows = []
    for target in range(901,len(x)+1):
        past = x[:target-1].copy()
        rankings = {name:rank_numbers(model.fit(past,cutoff=target-1).score_matrix(past,target=target))
            for name,model in models.items()}
        for name,ranking in rankings.items():
            rows.append(dict(candidate=name,model=MODEL,target_draw=target,diagnostic_only=True,
                training_cutoff=target-1,feature_cutoff=target-1,
                hits=int(x[target-1,np.array(ranking[:6])-1].sum())))
        if progress and target%25==0:progress(f'Sensitivity {target}/{len(x)}')
    return pd.DataFrame(rows)
