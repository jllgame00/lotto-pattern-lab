"""H19 development freeze and causal, draw-paired historical evaluation.

Scores are marginal Bernoulli probabilities for 45 number processes. Loss is
their mean pseudo-logloss, with uncertainty resampled at the draw level.
Previous models are read only from verified prediction archives.
"""
from copy import deepcopy
from functools import partial
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.recurrence import research_matrix
from src.backtest.change_point import _verified_archive
from src.backtest.multiscale import rank_diversity
from src.backtest.symmetry import frozen_gap, _decoded_list, _validate_predictions
from src.models.predictive import rank_numbers

RENEWAL = 'RenewalModel'
POSITIVE = 'HawkesInfluenceModel'
SIGNED = 'SignedInfluenceModel'
MODELS = (RENEWAL, POSITIVE, SIGNED)
SCHEMES = ('clipped','coarse','relative')
ALPHAS = (26,104)
KERNELS = ('exp2','exp8','finite')
INCOMING = (1,3)
RIDGES = (1,10)
EPSILON = 1e-9
SELECTION_METRIC = 'meanPerNumberLogloss;tiesdeclaredorder'
METRICS = ('logloss','first_logloss','second_logloss','mean_hits',
           'self_logloss','first_self_logloss','second_self_logloss')
FROZEN = dict(version='phase20-v1',research_cutoff=1245,development_start=401,
    development_end=900,later_start=901,candidate_count=54,development_cadence=26,
    selection_metric=SELECTION_METRIC,draw1246_used=False,
    scheme_grid=list(SCHEMES),alpha_grid=list(ALPHAS),kernel_grid=list(KERNELS),
    incoming_grid=list(INCOMING),ridge_grid=list(RIDGES),minimum_source_support=30,
    minimum_renewal_support=20,structural_smoothing=26,
    positive_comparison='experimental_falsification',probability_epsilon=EPSILON)


def configuration_hash(selection):
    return sha256(json.dumps(selection,sort_keys=True,allow_nan=False).encode()).hexdigest()


def candidates():
    """Declared order is the final tie breaker within each model family."""
    result = {f'renewal_{scheme}_alpha{alpha}':dict(model=RENEWAL,scheme=scheme,alpha=alpha)
        for scheme in SCHEMES for alpha in ALPHAS}
    for model,label in ((POSITIVE,'hawkes'),(SIGNED,'signed')):
        result.update({f'{label}_{kernel}_incoming{incoming}_alpha{alpha}_ridge{ridge}':
            dict(model=model,kernel=kernel,incoming=incoming,alpha=alpha,ridge=ridge)
            for kernel in KERNELS for incoming in INCOMING for alpha in ALPHAS for ridge in RIDGES})
    return result


def _strict_equal(a,b):
    if type(a) is not type(b):return False
    if isinstance(a,dict):return set(a)==set(b) and all(_strict_equal(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(_strict_equal(x,y) for x,y in zip(a,b))
    return a==b


def construct(config):
    if not any(_strict_equal(config,c) for c in candidates().values()):
        raise ValueError('Unknown H19 frozen grid configuration')
    from src.models.point_process import RenewalModel, HawkesInfluenceModel, SignedInfluenceModel
    cls = dict(zip(MODELS,(RenewalModel,HawkesInfluenceModel,SignedInfluenceModel)))[config['model']]
    kwargs = dict(config); kwargs.pop('model')
    return cls(**kwargs)


def construct_baseline():
    # Phase19's fixed-window class is pure frequency and does not reselect H18.
    from src.models.change_point import AdaptiveWindowBaseline
    return AdaptiveWindowBaseline(window=26)


def _probabilities(scores):
    if not isinstance(scores,dict):raise ValueError('Complete 45-number probability mapping required')
    try:
        keys = {int(k) for k in scores}
        if keys!=set(range(1,46)) or len(scores)!=45:raise ValueError
        values = np.asarray([scores[n] if n in scores else scores[str(n)] for n in range(1,46)],dtype=float)
    except (ValueError,TypeError,KeyError) as exc:
        raise ValueError('Complete 45-number probability mapping required') from exc
    if not np.isfinite(values).all() or not ((values>=0)&(values<=1)).all():
        raise ValueError('Finite marginal probabilities in [0,1] required')
    return values


def logloss(scores, actual):
    """Draw-mean Bernoulli loss; sparse zero/one estimates use fixed clipping."""
    p = np.clip(_probabilities(scores),EPSILON,1-EPSILON)
    actual = set(actual)
    if len(actual)!=6 or any(type(n) not in (int,np.int64,np.int32) or not 1<=n<=45 for n in actual):
        raise ValueError('Six actual number labels required')
    y = np.array([n in actual for n in range(1,46)],dtype=float)
    return float(-np.mean(y*np.log(p)+(1-y)*np.log1p(-p)))


def _best(metrics, model):
    return min((n for n,c in candidates().items() if c['model']==model),key=lambda n:metrics[n]['logloss'])


def _gates(metrics, names):
    r,p,s = (metrics[names[m]] for m in MODELS)
    positive = (all(p[f'{half}_logloss']<p[f'{half}_self_logloss'] for half in ('first','second'))
        and p['mean_hits']>=r['mean_hits'])
    signed = (all(s[f'{half}_logloss']<p[f'{half}_logloss'] and
        s[f'{half}_logloss']<s[f'{half}_self_logloss'] for half in ('first','second'))
        and s['mean_hits']>=p['mean_hits'])
    return bool(positive),bool(signed)


def _freeze_selection(table, x):
    specs = candidates(); metrics = {}
    for name,config in specs.items():
        group = table[table.candidate==name]
        if group.target_draw.tolist()!=list(range(401,901)):
            raise ValueError('All 54 development candidates require exact targets401..900')
        first = group[group.target_draw<=650]; second = group[group.target_draw>=651]
        own = config['model']!=RENEWAL
        metrics[name] = dict(logloss=float(group.logloss.mean()),mean_hits=float(group.hits.mean()),
            first_logloss=float(first.logloss.mean()),second_logloss=float(second.logloss.mean()),
            self_logloss=float(group.self_logloss.mean()) if own else None,
            first_self_logloss=float(first.self_logloss.mean()) if own else None,
            second_self_logloss=float(second.self_logloss.mean()) if own else None)
    names = {m:_best(metrics,m) for m in MODELS}
    positive,signed = _gates(metrics,names)
    selection = dict(deepcopy(FROZEN),models={m:specs[n] for m,n in names.items()},
        selected_candidates=names,development_metrics=metrics,development_positive=positive,
        signed_allowed=signed,development_matrix_hash=sha256(x.tobytes()).hexdigest())
    return _validate_selection(selection)


def development_search(x, *, progress=None):
    x = research_matrix(x)
    if len(x)!=900:raise ValueError('Development requires exact draws1..900')
    specs = candidates(); models = {n:construct(c) for n,c in specs.items()}; rows = []
    for target in range(401,901):
        past = x[:target-1].copy()
        if (target-401)%26==0:
            for model in models.values():model.fit(past,cutoff=target-1)
        # Materialize every full and nested prediction before reading outcome T.
        predicted = {}
        for name,model in models.items():
            scores = dict(model.score_matrix(past,target=target)); _probabilities(scores)
            own = dict(model.self_only_scores(past,target=target)) if specs[name]['model']!=RENEWAL else None
            if own is not None:_probabilities(own)
            predicted[name] = (scores,rank_numbers(scores),own)
        actual = set((np.flatnonzero(x[target-1])+1).tolist())
        for name,(scores,ranking,own) in predicted.items():
            rows.append(dict(candidate=name,model=specs[name]['model'],target_draw=target,
                training_cutoff=models[name].training_cutoff,feature_cutoff=target-1,
                hits=len(set(ranking[:6])&actual),logloss=logloss(scores,actual),
                self_logloss=logloss(own,actual) if own is not None else np.nan))
        if progress and target%25==0:progress(f'Development {target}/900')
    table = pd.DataFrame(rows)
    return _freeze_selection(table,x),table


def _validate_selection(selection):
    variable = {'models','selected_candidates','development_metrics','development_positive',
                'signed_allowed','development_matrix_hash'}
    if (not isinstance(selection,dict) or set(selection)!=set(FROZEN)|variable or
        any(not _strict_equal(selection[k],v) for k,v in FROZEN.items())):
        raise ValueError('Frozen H19 configuration schema integrity mismatch')
    specs = candidates(); models = selection['models']; names = selection['selected_candidates']
    if (not isinstance(models,dict) or set(models)!=set(MODELS) or
        not isinstance(names,dict) or set(names)!=set(MODELS)):
        raise ValueError('Unknown H19 selected model schema')
    for model in MODELS:
        if (type(names[model]) is not str or names[model] not in specs or
            specs[names[model]]['model']!=model or not _strict_equal(models[model],specs[names[model]])):
            raise ValueError('Unknown H19 frozen grid configuration')
    digest = selection['development_matrix_hash']
    if type(digest) is not str or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('Invalid development source hash')
    metrics = selection['development_metrics']
    if not isinstance(metrics,dict) or set(metrics)!=set(specs):
        raise ValueError('All frozen development candidate metrics required')
    for name,m in metrics.items():
        if not isinstance(m,dict) or set(m)!=set(METRICS):raise ValueError('Invalid development metric schema')
        for key,v in m.items():
            if key.endswith('self_logloss') and specs[name]['model']==RENEWAL:
                if v is not None:raise ValueError('Renewal nested loss must be absent')
            elif type(v) not in (int,float) or not np.isfinite(v) or not 0<=v<=(6 if key=='mean_hits' else -np.log(EPSILON)):
                raise ValueError('Invalid frozen development metric values')
        for key in ('logloss','self_logloss'):
            if m[key] is not None and not np.isclose(m[key],(m['first_'+key]+m['second_'+key])/2,rtol=0,atol=1e-12):
                raise ValueError('Development half loss mismatch')
    if any(names[m]!=_best(metrics,m) for m in MODELS):
        raise ValueError('Development logloss selection or declared tie mismatch')
    positive,signed = _gates(metrics,names)
    if (type(selection['development_positive']) is not bool or type(selection['signed_allowed']) is not bool or
        selection['development_positive']!=positive or selection['signed_allowed']!=signed):
        raise ValueError('Development-only positive or signed gate mismatch')
    return selection


def load_selection(path):
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(payload,dict) or set(payload)!={'selection','sha256'}:raise ValueError('Invalid H19 selection envelope')
        if payload['sha256']!=configuration_hash(payload['selection']):raise ValueError('Frozen H19 hash mismatch')
        return _validate_selection(payload['selection'])
    except (KeyError,TypeError,json.JSONDecodeError) as exc:
        raise ValueError('Invalid H19 selection schema') from exc


def _active(selection):
    return MODELS if selection['signed_allowed'] else MODELS[:2]


def factories(selection):
    _validate_selection(selection)
    return {**{m:partial(construct,deepcopy(selection['models'][m])) for m in _active(selection)},
        'Frequency26':construct_baseline}


def _json(value):
    def convert(v):
        if isinstance(v,np.ndarray):return v.tolist()
        if isinstance(v,np.generic):return v.item()
        raise TypeError(f'Unsupported diagnostic value {type(v).__name__}')
    return json.dumps(value,sort_keys=True,allow_nan=False,default=convert)


class _CaptureState:
    """Snapshot full predictions before nested calls can mutate model diagnostics."""
    def __init__(self, model, name, collector):
        self.model = model; self.name = name; self.collector = collector

    def fit(self, past, *, cutoff):
        self.model.fit(past,cutoff=cutoff); self.training_cutoff = cutoff
        if getattr(self.model,'training_cutoff',None)!=cutoff:
            raise ValueError('Model outer training cutoff mismatch')
        self.frozen_edges = _json(getattr(self.model,'selected_edges',None))
        self.frozen_coefficients = _json(getattr(self.model,'coefficients',None))
        self.frozen_self_coefficient = _json(getattr(self.model,'self_coefficient',None))
        return self

    def score_matrix(self, past, *, target):
        if target!=len(past)+1 or target<=self.training_cutoff:
            raise ValueError('Exact causal target prefix after outer training cutoff required')
        scores = dict(self.model.score_matrix(past,target=target)); _probabilities(scores)
        diagnostics = getattr(self.model,'last_diagnostic',None)
        if diagnostics is not None:
            if (not isinstance(diagnostics,list) or len(diagnostics)!=45 or
                [d.get('number') for d in diagnostics]!=list(range(1,46))):
                raise ValueError('Complete 45-number current causal diagnostics required')
            for d in diagnostics:
                if (d.get('training_cutoff')!=self.training_cutoff or
                    d.get('source_cutoff')!=target-1):
                    raise ValueError('Current diagnostic causal cutoff mismatch')
        if (getattr(self.model,'training_cutoff',None)!=self.training_cutoff or
            _json(getattr(self.model,'selected_edges',None))!=self.frozen_edges or
            _json(getattr(self.model,'coefficients',None))!=self.frozen_coefficients or
            _json(getattr(self.model,'self_coefficient',None))!=self.frozen_self_coefficient):
            raise ValueError('Outer training cutoff edges and coefficients must stay frozen')
        def validate_edges(value):
            if isinstance(value,list):
                for item in value:validate_edges(item)
            elif isinstance(value,dict) and value.get('training_cutoff')!=self.training_cutoff:
                raise ValueError('Selected edge training cutoff mismatch')
        validate_edges(getattr(self.model,'selected_edges',None))
        state = dict(model=self.name,target_draw=target,source_cutoff=target-1,
            outer_fit_cutoff=self.training_cutoff,edge_training_cutoff=self.training_cutoff,
            probabilities=_json(scores),last_diagnostic=_json(diagnostics),
            selected_edges=self.frozen_edges,coefficients=self.frozen_coefficients,
            self_coefficient=getattr(self.model,'self_coefficient',None))
        if self.name in (POSITIVE,SIGNED):
            own = dict(self.model.self_only_scores(past,target=target)); _probabilities(own)
            state['self_scores'] = _json(own)
        self.collector.append(state)
        return scores


def evaluate(history, selection, *, cadence=26, progress=None):
    from src.analysis.spatiotemporal import lotto_matrix
    from src.backtest.translation import walk_forward
    _validate_selection(selection)
    if not 901<=len(history)<=1245 or type(cadence) is not int or cadence not in (13,26):
        raise ValueError('H19 bounded cadence13/26 required')
    x = lotto_matrix(history,cutoff=len(history))
    if sha256(x[:900].tobytes()).hexdigest()!=selection['development_matrix_hash']:
        raise ValueError('Development source prefix mismatch')
    gap = frozen_gap(x,cadence=cadence)
    _validate_predictions(gap,targets=range(901,len(x)+1),x=x)
    makers = factories(selection); collector = []
    for name in _active(selection):
        makers[name] = partial(_CaptureStateFactory,deepcopy(selection['models'][name]),name,collector)
    rows = walk_forward(history,makers,start=901,end=len(history),cadence=cadence,
        gap_features=None,combined=False,progress=progress)
    rows['outer_fit_cutoff'] = rows.training_cutoff
    # Frequency recomputes a causal trailing window; its outer fit is retained.
    rows.loc[rows.model=='Frequency26','training_cutoff'] = rows.loc[rows.model=='Frequency26','feature_cutoff']
    audit = {(r['model'],r['target_draw']):r for r in collector}
    for key in ('source_cutoff','edge_training_cutoff','probabilities','self_scores','last_diagnostic',
                'selected_edges','coefficients','self_coefficient'):
        rows[key] = [audit.get((r.model,r.target_draw),{}).get(key,None) for r in rows.itertuples()]
    rows['logloss'] = np.nan; rows['self_logloss'] = np.nan
    for index,row in rows.iterrows():
        actual = set(_decoded_list(row.actual))
        if row.model in _active(selection):
            p = json.loads(row.probabilities)
        elif row.model=='RandomModel':
            p = {n:6/45 for n in range(1,46)}
        elif row.model=='Frequency26':
            p = json.loads(row.scores)
        else:continue
        rows.at[index,'probabilities'] = _json(p)
        rows.at[index,'logloss'] = logloss(p,actual)
        if row.model in (POSITIVE,SIGNED):rows.at[index,'self_logloss'] = logloss(json.loads(row.self_scores),actual)
    gap = gap.copy(); gap['outer_fit_cutoff'] = gap.training_cutoff
    # Archived Gap scores have ranking semantics; do not invent probabilities.
    gap['logloss'] = np.nan; gap['self_logloss'] = np.nan
    result = pd.concat([rows,gap],ignore_index=True)
    for _,group in result.groupby('model'):_validate_predictions(group,targets=range(901,len(x)+1),x=x)
    return result


def _CaptureStateFactory(config, name, collector):
    return _CaptureState(construct(config),name,collector)


def _bootstrap(n, replicates, block):
    if type(replicates) is not int or replicates<1 or type(block) is not int or block not in (13,26,52):
        raise ValueError('Positive bootstrap count and declared block13/26/52 required')
    rng = np.random.default_rng(200042); length = min(block,n)
    return ((rng.integers(0,n,(replicates,int(np.ceil(n/length))))[:,:,None]+
        np.arange(length))%n).reshape(replicates,-1)[:,:n]


def _groups(rows, selection, required):
    _validate_selection(selection)
    if (not {'model','target_draw'}<=set(rows) or not set(required)<=set(rows.model) or
        rows.duplicated(['model','target_draw']).any() or
        (not selection['signed_allowed'] and SIGNED in set(rows.model))):
        raise ValueError('Unique paired references and frozen signed choice required')
    groups = {m:_validate_predictions(rows[rows.model==m]) for m in required}
    for model,g in groups.items():
        if model=='GapLogistic':continue
        for key,probability_key in (('logloss','probabilities'),('self_logloss','self_scores')):
            if key not in g or (key=='self_logloss' and model not in (POSITIVE,SIGNED)):continue
            values = g[key].to_numpy(dtype=float)
            if not np.isfinite(values).all() or not ((values>=0)&(values<=-np.log(EPSILON))).all():
                raise ValueError('Finite nonnegative matched probability logloss required')
            if probability_key in g:
                for row in g.itertuples():
                    stored = getattr(row,probability_key)
                    if stored is None or (isinstance(stored,float) and np.isnan(stored)):continue
                    scores = json.loads(stored) if isinstance(stored,str) else stored
                    if not np.isclose(getattr(row,key),logloss(scores,set(_decoded_list(row.actual))),rtol=0,atol=1e-12):
                        raise ValueError('Stored probability logloss integrity mismatch')
    targets = groups[required[0]].target_draw.tolist()
    if any(g.target_draw.tolist()!=targets for g in groups.values()):raise ValueError('Paired target mismatch')
    actuals = groups[required[0]].actual.map(_decoded_list).map(set).tolist()
    if any(g.actual.map(_decoded_list).map(set).tolist()!=actuals for g in groups.values()):
        raise ValueError('Paired actual mismatch')
    return groups


def _comparison(model, reference, start, metric, delta, indices, replicates, block):
    delta = np.asarray(delta,dtype=float)
    if delta.ndim!=1 or not len(delta) or not np.isfinite(delta).all():
        raise ValueError('Finite target-aligned paired differences required')
    low,high = np.quantile(delta[indices].mean(1),[.025,.975])
    return dict(model=model,reference=reference,start=start,targets=len(delta),metric=metric,
        difference=float(delta.mean()),ci_low=float(low),ci_high=float(high),block=block,
        replicates=replicates,degenerate=bool(low==high))


def paired_report(rows, selection, *, replicates=2000, block=26):
    _validate_selection(selection)
    models = _active(selection); references = ('RandomModel','GapLogistic',RENEWAL)
    loss_references = ('Frequency26',) if 'model' in rows and 'Frequency26' in set(rows.model) else ()
    groups = _groups(rows,selection,list(dict.fromkeys((*models,*references,*loss_references))))
    _bootstrap(1,replicates,block); output = []
    for start in (901,1001,1101):
        subset = {m:g[g.target_draw>=start] for m,g in groups.items()}; n = len(subset[RENEWAL])
        if not n:continue
        indices = _bootstrap(n,replicates,block)
        for model in models:
            a = subset[model]
            for reference in references:
                if model==reference:continue
                b = subset[reference]
                metrics = {k:(a[k].to_numpy(dtype=float),b[k].to_numpy(dtype=float))
                    for k in ('hits','recall_6','recall_10','recall_15','mean_winning_rank')}
                metrics.update({f'pool_{k}_{threshold}plus':((a[f'pool_{k}']>=threshold).to_numpy(dtype=float),
                    (b[f'pool_{k}']>=threshold).to_numpy(dtype=float))
                    for k in (6,8,10,12,15) for threshold in (5,6)})
                if reference!='GapLogistic' and 'logloss' in a and 'logloss' in b:
                    aa = a.logloss.to_numpy(dtype=float); bb = b.logloss.to_numpy(dtype=float)
                    if np.isfinite(aa).all() and np.isfinite(bb).all():metrics['logloss'] = aa,bb
                for metric,(aa,bb) in metrics.items():
                    output.append(_comparison(model,reference,start,metric,aa-bb,indices,replicates,block))
            for reference in loss_references:
                b = subset[reference]
                if 'logloss' in a and 'logloss' in b:
                    output.append(_comparison(model,reference,start,'logloss',
                        a.logloss.to_numpy(dtype=float)-b.logloss.to_numpy(dtype=float),indices,replicates,block))
    return pd.DataFrame(output)


def conditional_report(rows, selection, *, replicates=2000, block=26):
    """Incoming-added versus separately fitted nested self-only, paired by draw."""
    _validate_selection(selection)
    models = tuple(m for m in _active(selection) if m!=RENEWAL)
    groups = _groups(rows,selection,list(models)); losses = []; summary = []
    _bootstrap(1,replicates,block)
    for model,g in groups.items():
        if not {'logloss','self_logloss'}<=set(g):raise ValueError('Nested matched self-only loss required')
        if not np.isfinite(g[['logloss','self_logloss']].to_numpy(dtype=float)).all():
            raise ValueError('Finite nested matched self-only loss required')
        for row in g.itertuples():
            losses.append(dict(model=model,target_draw=row.target_draw,logloss=float(row.logloss),
                self_logloss=float(row.self_logloss),difference=float(row.logloss-row.self_logloss)))
        for start in (901,1001,1101):
            a = g[g.target_draw>=start]
            if a.empty:continue
            indices = _bootstrap(len(a),replicates,block)
            summary.append(_comparison(model,'nested_self_only',start,'logloss',
                (a.logloss-a.self_logloss).to_numpy(dtype=float),indices,replicates,block))
    return pd.DataFrame(losses),pd.DataFrame(summary)


def correlation_report(rows, selection, *, graph_path=None, shape_path=None, mirror_path=None):
    _validate_selection(selection)
    models = _active(selection)
    groups = _groups(rows,selection,[*models,'GapLogistic'])
    targets = groups[RENEWAL].target_draw.tolist(); references = {'GapLogistic':groups['GapLogistic']}
    for path,name,label in ((graph_path,'GraphStructureModel','Phase14Graph'),
            (shape_path,'GapShapeModel','Phase15GapShape'),(mirror_path,'MirrorModel','Phase18Mirror')):
        if path is None or not Path(path).is_file():continue
        old = _verified_archive(path)
        selected = old[(old.model==name)&old.target_draw.isin(targets)]
        if not selected.empty:references[label] = _validate_predictions(selected)
    output = []
    for model in models:
        for label,reference in references.items():
            indexed = reference.set_index('target_draw')
            for row in groups[model].itertuples():
                if row.target_draw not in indexed.index:continue
                other = indexed.loc[row.target_draw]
                if set(_decoded_list(other.actual))!=set(_decoded_list(row.actual)):
                    raise ValueError('Frozen reference actual mismatch')
                output.append(dict(model=model,target_draw=row.target_draw,reference=label,
                    **rank_diversity(_decoded_list(row.ranking),_decoded_list(other.ranking))))
    return pd.DataFrame(output)
