"""One-time offline Phase10 freeze from a strictly bounded canonical prefix."""
from datetime import datetime,timezone,timedelta
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
from uuid import uuid4
import numpy as np
import scipy
from src.prospective_experiment import ROOT,strict_source,_git,_fitted_audit
from src.phase6_freeze import CANONICAL_HASH
from src.freeze_artifacts import prepare_track,digest
from src.phase10_artifacts import ensure_new,verify_prior,publish,verify_number_space,FLAGS
from src.backtest.number_space import load_selection,configuration_hash


def validate_historical_provenance(data,dataset_hash,selection,analysis,protocols):
    prefix_hash=sha256(data.iloc[:900].to_csv(index=False).encode()).hexdigest()
    full_hash=sha256(data.to_csv(index=False).encode()).hexdigest()
    if (len(data)!=1245 or selection.get('development_start')!=401 or selection.get('development_end')!=900 or
        selection.get('later_start')!=901 or selection.get('development_data_hash')!=prefix_hash):
        raise ValueError('Historical development selection does not match canonical prefix')
    if analysis.get('cutoff')!=1245 or analysis.get('dataset_hash')!=dataset_hash:
        raise ValueError('Historical descriptive analysis does not match canonical dataset')
    if len(protocols)!=2:raise ValueError('Both cadence protocols required')
    for protocol in protocols:
        if (protocol.get('input_data_hash')!=full_hash or protocol.get('start')!=401 or protocol.get('end')!=1245 or
            protocol.get('development_end')!=900 or protocol.get('later_start')!=901 or
            protocol.get('selected_configuration_hash')!=configuration_hash(selection)):
            raise ValueError('Historical evaluation does not match canonical dataset/selection')


def freeze_number_space(source,directory,*,expected_target=1246,protected=None,selection=None):
    directory=Path(directory);ensure_new(directory,expected_target)
    data,h=strict_source(source)
    if type(expected_target) is not int or len(data)+1!=expected_target:raise ValueError('Dataset cutoff/target mismatch')
    real=expected_target==1246
    if real and (h!=CANONICAL_HASH or directory.resolve()!=(ROOT/'reports/prospective/phase10').resolve()):
        raise ValueError('Actual Phase10 requires canonical hash and separate phase10 namespace')
    report=ROOT/'reports/number_space'
    if protected is None:protected=json.loads((report/'prior_prospective_hashes.json').read_text(encoding='utf-8'))
    verify_prior(directory.parent,protected)
    historical={}
    if real:
        if selection is not None:raise ValueError('Actual freeze must load the already frozen development selection')
        for name in ('analysis_metadata.json','global_null_comparison.csv','selected_configuration.json',
                     'walk_forward_26/protocol.json','walk_forward_13/protocol.json','walk_forward_26/portfolio_comparison.csv'):
            q=report/name
            if not q.is_file():raise ValueError('Complete historical Phase10 analysis before publication: '+name)
            historical[name]=digest(q)
        selection=load_selection(report/'selected_configuration.json')
        analysis=json.loads((report/'analysis_metadata.json').read_text(encoding='utf-8'))
        protocols=[json.loads((report/f'walk_forward_{cadence}/protocol.json').read_text()) for cadence in (26,13)]
        validate_historical_provenance(data,h,selection,analysis,protocols)
    if selection is None or selection['development_end']>=expected_target:raise ValueError('Prior development selection required')
    from src.analysis.spatiotemporal import lotto_matrix
    from src.analysis.number_space import rolling_counts,WINDOWS
    from src.analysis.features import build_prospective_features,GAP
    from src.prediction_scope import ProspectiveScope
    from src.models.number_space import RangeDensityModel,NeighborhoodModel,GapNeighborhoodModel
    x=lotto_matrix(data,cutoff=len(data));features=build_prospective_features(data,scope=ProspectiveScope(len(data)))
    training=features[features.target_draw<=len(data)].copy()
    current=features[features.target_draw==expected_target].drop(columns='appeared_next').copy()
    models=dict(RangeDensityModel=RangeDensityModel(**selection['range']).fit(x,cutoff=len(x)),
        NeighborhoodModel=NeighborhoodModel(**selection['neighborhood']).fit(x,cutoff=len(x)),
        GapNeighborhoodModel=GapNeighborhoodModel(**selection['neighborhood'],gap_weight=selection['gap_weight']).fit(x,cutoff=len(x),feature_rows=training))
    scores={name:m.score_matrix(x,target=expected_target,**(dict(current_rows=current) if name=='GapNeighborhoodModel' else {})) for name,m in models.items()}
    now=datetime.now(timezone(timedelta(hours=9)));identity=f'draw{expected_target}_phase10_numberspace_{now.strftime("%Y%m%dT%H%M%S%f")}_{uuid4().hex[:8]}'
    sources={q.relative_to(ROOT).as_posix():q.read_text(encoding='utf-8') for q in sorted((ROOT/'src').rglob('*.py'))}
    p=dict(schema_version='phase10-number-space-v1',phase=10,experiment_id=identity,target_draw=expected_target,
        training_cutoff=len(data),latest_training_date=str(data.iloc[-1].draw_date.date()),created_at=now.isoformat(),
        dataset_hash=h,git_sha=_git('rev-parse','HEAD'),git_dirty=bool(_git('status','--porcelain')),git_status=_git('status','--short'),
        status='FROZEN_UNEVALUATED',seed=42,**{k:False for k in FLAGS},
        feature_version='phase10-pre-draw-number-space-v1; W10/26/52 main-only activity; finite number axis; gap features unchanged',
        selection=selection,selection_hash=configuration_hash(selection),historical_report_hashes=historical,
        retraining='Fit Gap Logistic through included cutoff once; selected kernel/width/weight frozen from development only',
        protocol=(ROOT/'docs/superpowers/plans/2026-10-17-phase10.md').read_text(encoding='utf-8'),
        environment=dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,scipy=scipy.__version__),
        sources=sources,source_hashes={name:sha256(text.encode()).hexdigest() for name,text in sources.items()},
        fitted=dict(training_cutoff=len(data),feature_cutoff=len(data),recent_counts={str(w):rolling_counts(x,w)[-1].tolist() for w in WINDOWS},
            gap=_fitted_audit(models['GapNeighborhoodModel'].gap),current_gap_features=current[GAP].replace({np.nan:None}).to_numpy().tolist()),
        models={name:prepare_track(scores[name],m.configuration(),seed=42,portfolios=True) for name,m in models.items()})
    return publish(p,directory,protected=protected)
