"""Freeze Phase5's predeclared tracks using unchanged historical model formulas."""
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from io import BytesIO
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
from uuid import uuid4

import numpy as np
import pandas as pd
from src.analysis.features import build_prospective_features,GAP,PERIODICITY,feature_columns
from src.collect.dataset import validate_history
from src.models.predictive import LogisticModel,SimilarityModel
from src.models.bayesian import BayesianModel
from src.models.hazard import GapHazardModel
from src.models.regime import HMMModel
from src.models.ensemble import FrozenEnsemble
from src.models.random_model import RandomModel
from src.models.gap_research import GAP_DEFINITIONS
from src.prediction_scope import ProspectiveScope
from src.freeze_artifacts import prepare_track,publish_freeze,ensure_unfrozen,digest

ROOT=Path(__file__).resolve().parent.parent
COMPONENTS=['GapLogistic','GapHazard','BayesianStatic','BayesianRecent','HMM2','HMM3',
            'SimilarityModel','Frequency52','GapPeriodicityLogistic']
ENSEMBLE_WEIGHTS=[.2]+[.1]*8


def strict_source(path):
    """No read beyond header+1245 rows; reject an unknown suffix via byte size."""
    path=Path(path); before=path.stat(); lines=[]
    with path.open('rb') as stream:
        for _ in range(1246):
            line=stream.readline()
            if not line: break
            if not line.strip(): raise ValueError('Canonical CSV must have one nonempty line per draw')
            lines.append(line)
    raw=b''.join(lines); after=path.stat()
    if len(raw)!=after.st_size: raise ValueError('Source has an unknown suffix; no future row was parsed')
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns): raise ValueError('Source changed during read')
    frame=pd.read_csv(BytesIO(raw))
    if frame.draw_no.tolist()!=list(range(1,len(frame)+1)) or len(frame)>1245:
        raise ValueError('Source must be contiguous1..cutoff, never after1245')
    return validate_history(frame),sha256(raw).hexdigest()


def load_existing_ensemble(path):
    path=Path(path); raw=path.read_bytes(); data=json.loads(raw)
    config=data.get('Ensemble[DevelopmentWeights]',{})
    if (config.get('components')!=COMPONENTS or config.get('weights')!=ENSEMBLE_WEIGHTS or
        config.get('normalization')!='rank' or type(config.get('development_end')) is not int or config['development_end']>900):
        raise ValueError('Cannot match existing development-selected ensemble; refusing replacement or retuning')
    return config,dict(path=str(path.resolve()),sha256=sha256(raw).hexdigest(),raw_json=raw.decode('utf-8'),configuration=config)


def _git(*args):
    try: return subprocess.check_output(['git',*args],cwd=ROOT,text=True,stderr=subprocess.DEVNULL,timeout=5).strip()
    except (OSError,subprocess.SubprocessError): return None


def _fitted_audit(model):
    audit=dict(training_cutoff=model.training_cutoff,training_rows=model.training_rows,
        transformer=dict(columns=model.transformer.columns,names=model.transformer.names,
            medians=model.transformer.medians.tolist(),means=model.transformer.means.tolist(),scales=model.transformer.scales.tolist()))
    if isinstance(model,LogisticModel): audit['coefficients_with_intercept']=model.coef.tolist()
    if isinstance(model,BayesianModel): audit['posteriors']=model.diagnostics().to_dict('records')
    if isinstance(model,GapHazardModel):
        audit.update(counts=model.counts.tolist(),successes=model.successes.tolist(),probabilities=model.probabilities.tolist())
    if isinstance(model,HMMModel):
        h=model.hmm
        audit.update(transitions=h.transitions.tolist(),emissions=h.emissions.tolist(),filtered_state=h.state.tolist(),
            iterations=h.iterations.tolist(),converged=h.converged.tolist(),initializations=h.initializations)
    return audit


def freeze_experiment(source,directory,*,ensemble_path=None,expected_target=1246,seed=42,progress=None):
    if type(seed) is not int or seed!=42: raise ValueError('Phase5 fixes seed42; no seed search permitted')
    ensure_unfrozen(directory,expected_target)
    data,dataset_hash=strict_source(source)
    scope=ProspectiveScope(len(data)); scope.history(data)
    if scope.target!=expected_target: raise ValueError('Source cutoff does not match declared next target')
    if len(data)<208: raise ValueError('HMM needs104 supervised observations starting at105')
    ensemble_path=ensemble_path or ROOT/'reports/regime_research/ensemble_weights.json'
    config,ensemble_source=load_existing_ensemble(ensemble_path)
    if expected_target==1246 and config['development_end']!=900:
        raise ValueError('Actual1246 requires existing development cutoff900')
    if config['development_end']>=scope.target: raise ValueError('Ensemble selection must precede prospective target')
    features=build_prospective_features(data,scope=scope,progress=progress)
    training=features[features.target_draw<=scope.cutoff].copy()
    current=features[features.target_draw==scope.target].drop(columns='appeared_next').copy()
    if not features[features.target_draw==scope.target].appeared_next.isna().all():
        raise ValueError('Prospective target must be unlabeled')
    # All formulas and defaults are the existing Phase4 policies. Only the
    # explicitly scoped cutoff and once-at-freeze refit differ from backtesting.
    from src.regime_cli import FrequencyModel
    common=dict(seed=seed,prediction_scope=scope)
    models={'GapLogistic':LogisticModel(columns=GAP,**common),'GapHazard':GapHazardModel(**common),
        'BayesianStatic':BayesianModel(**common),'BayesianRecent':BayesianModel(half_life=52,**common),
        'HMM2':HMMModel(states=2,**common),'HMM3':HMMModel(states=3,**common),
        'SimilarityModel':SimilarityModel(**common),'Frequency52':FrequencyModel(**common),
        'GapPeriodicityLogistic':LogisticModel(columns=GAP+PERIODICITY,**common)}
    components={}; rows=[]
    for name,model in models.items():
        model.fit(training,cutoff=scope.cutoff)
        scores=model.score_rows(current)
        components[name]=dict(scores=scores,configuration=model.configuration(),fitted=_fitted_audit(model))
        rows.append(dict(model=name,target_draw=scope.target,scores=json.dumps(scores)))
        if progress: progress(f'Fitted {name} through{scope.cutoff}; prospective scores prepared')
    ensemble=FrozenEnsemble(COMPONENTS,method='rank',weights=config['weights'],
        development_end=config['development_end'],prediction_scope=scope)
    ensemble_scores=ensemble.score(pd.DataFrame(rows))
    tracks={name:prepare_track(components[name]['scores'],components[name]['configuration'],seed=seed,
                portfolios=name=='GapLogistic') for name in ('GapLogistic','BayesianStatic','HMM2','HMM3')}
    tracks['Ensemble']=prepare_track(ensemble_scores,ensemble.configuration(),seed=seed,portfolios=True)
    tracks['UniformRandom']=prepare_track(RandomModel().score_numbers(None),
        dict(model='RandomModel',appearance_score=6/45,ranking='uniform seeded permutation',portfolio='uniform unique6-from45'),
        seed=seed,uniform=True)
    # Capture exact local implementation because this phase is intentionally uncommitted.
    sources={p.relative_to(ROOT).as_posix():p.read_text(encoding='utf-8') for p in sorted((ROOT/'src').rglob('*.py'))}
    now=datetime.now(timezone(timedelta(hours=9)))
    identifier=f'draw_{scope.target}_{now.strftime("%Y%m%dT%H%M%S%f%z")}_{uuid4().hex[:8]}'
    # Plus sign in timezone is omitted only from the filesystem identifier.
    identifier=identifier.replace('+','')
    status=_git('status','--porcelain')
    payload=dict(schema_version=2,experiment_id=identifier,target_draw=scope.target,training_cutoff=scope.cutoff,
        latest_training_date=str(data.draw_date.iloc[-1].date()),created_at=now.isoformat(),
        canonical_dataset_sha256=dataset_hash,source_path=str(Path(source).resolve()),
        source_draw_range=[1,scope.cutoff],source_rows=len(data),git_commit=_git('rev-parse','HEAD'),
        git_dirty=None if status is None else bool(status),git_status=status,
        status='FROZEN_UNEVALUATED',target_result_retrieved=False,target_result_inspected=False,
        environment=dict(python=sys.version,executable=sys.executable,platform=platform.platform(),
            packages={name:importlib.metadata.version(name) for name in ('numpy','scipy','pandas')}),
        protocol=dict(version='phase5-v1',seed=seed,target_draw=scope.target,training_cutoff=scope.cutoff,
            retraining='Refit each existing component once through cutoff; no later update to this experiment',
            supervised_target_range=[105,scope.cutoff],minimum_feature_history=104,
            ensemble_selection='Reuse existing development weights without selection or fitting',
            portfolios='Top12 weighted/coverage, one seed per method; nested1/5/10/20 prefixes; directTop6 separate',
            random_controls='Uniform45 portfolios at identical budgets; random rankTop6 controls directTop6',
            hypotheses={'models':['GapLogistic','Ensemble'],'pool_sizes':[8,10,12,15],'thresholds':[3,4,5,6]},
            no_alternative_portfolio_search=True,
            interpretation='No demonstrated predictive advantage; one draw cannot establish predictability',
            generation_audit='One early CLI wiring test produced an unregistered legacy-v1 snapshot in pytest scratch space; cleanup removed it. No scores/rankings were displayed or inspected. No policies changed in response.',
            provenance='Draw1245 is training data, not a pristine holdout; target not retrieved or inspected in this session'),
        feature_definitions=dict(version='canonical-v1-unchanged',columns=feature_columns(),gap=GAP_DEFINITIONS,
            frequency='Counts and count/window at5,10,26,52,104; rate10/rate104; consecutive last2 appearances',
            periodicity='Existing104-draw score/ACF/spectral features; past-only expanding90th percentile with52 prior scores and3 high confirmations',
            calendar='Month/week sine/cosine from next scheduled weekly date; no target outcome',
            missing_values='Existing training-median imputation and training population scaling',
            exact_implementation='Embedded implementation_sources: src/analysis/features.py and periodicity.py'),
        feature_audit=dict(training_rows=len(training),training_target_min=int(training.target_draw.min()),
            training_target_max=int(training.target_draw.max()),current_rows=len(current),current_feature_cutoff=scope.cutoff),
        current_features=json.loads(current.to_json(orient='records',date_format='iso')),
        ensemble_source=ensemble_source,components=components,models=tracks,implementation_sources=sources,
        implementation_hashes={name:sha256(text.encode('utf-8')).hexdigest() for name,text in sources.items()})
    _,after_hash=strict_source(source)
    if after_hash!=dataset_hash: raise ValueError('Canonical source changed during generation; aborting freeze')
    if digest(ensemble_path)!=ensemble_source['sha256']: raise ValueError('Ensemble source changed during generation')
    return publish_freeze(payload,directory)
