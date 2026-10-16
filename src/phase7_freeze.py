"""Generate the two predeclared Phase7 tracks from a bounded local CSV only."""
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
from uuid import uuid4
import numpy as np
import scipy
from src.analysis.spatiotemporal import lotto_matrix
from src.models.gap3d import GapConditionedTranslationModel, GapConditionedChainModel
from src.prospective_experiment import ROOT, strict_source, _git
from src.phase6_freeze import CANONICAL_HASH
from src.freeze_artifacts import prepare_track, digest
from src.phase7_artifacts import ensure_new, verify_prior, publish_gap3d


def freeze_gap3d(source, directory, *, expected_target=1246, protected=None):
    directory=Path(directory)
    ensure_new(directory,expected_target)
    data,dataset_hash=strict_source(Path(source))
    if type(expected_target) is not int or len(data)+1!=expected_target:
        raise ValueError('Dataset cutoff does not match declared next target')
    if expected_target==1246 and dataset_hash!=CANONICAL_HASH:
        raise ValueError('Canonical dataset hash changed; refusing publication')
    if protected is None:
        protected=json.loads((ROOT/'reports/spatiotemporal3d/prior_prospective_hashes.json').read_text(encoding='utf-8'))
    verify_prior(directory.parent,protected)
    historical_hashes={}
    if expected_target==1246:
        if directory.resolve()!=(ROOT/'reports/prospective/phase7').resolve():
            raise ValueError('Real Phase7 experiment requires its distinct canonical phase7 directory')
        # Publication follows completed historical analysis, never replaces it.
        for relative in ('analysis_metadata.json','global_null_comparison.csv',
                         'walk_forward_26/protocol.json','walk_forward_26/comparison.csv',
                         'walk_forward_13/protocol.json','walk_forward_13/comparison.csv'):
            path=ROOT/'reports/spatiotemporal3d'/relative
            if not path.is_file(): raise ValueError('Complete historical analysis before prospective freeze: '+relative)
            historical_hashes[relative]=digest(path)
    x=lotto_matrix(data,cutoff=len(data))
    models={cls.__name__:cls().fit(x,cutoff=len(x)) for cls in
            (GapConditionedTranslationModel,GapConditionedChainModel)}
    now=datetime.now(timezone(timedelta(hours=9)))
    identity=f'draw{expected_target}_phase7_gap3d_{now.strftime("%Y%m%dT%H%M%S%f")}_{uuid4().hex[:8]}'
    code={str(p.relative_to(ROOT)):p.read_text(encoding='utf-8') for p in sorted((ROOT/'src').rglob('*.py'))}
    payload=dict(schema_version='phase7-gap3d-v1',phase=7,experiment_id=identity,
        target_draw=expected_target,training_cutoff=len(data),latest_training_date=str(data.iloc[-1].draw_date.date()),
        created_at=now.isoformat(),dataset_hash=dataset_hash,git_sha=_git('rev-parse','HEAD'),
        git_dirty=bool(_git('status','--porcelain')),git_status=_git('status','--short'),
        status='FROZEN_UNEVALUATED',future_result_accessed=False,seed=42,
        target_result_retrieved=False,target_result_inspected=False,target_result_imported=False,target_result_evaluated=False,
        feature_version='pre-draw-gap-v1; gap[t,n]=t-1-last_appearance; missing excluded; bonus excluded',
        protocol=(ROOT/'docs/superpowers/plans/2026-10-17-phase7.md').read_text(encoding='utf-8'),
        historical_report_hashes=historical_hashes,
        retraining='Fit once through included cutoff; all gap thresholds learned from training pre-states; frozen thereafter',
        environment=dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,scipy=scipy.__version__),
        sources=code,source_hashes={name:sha256(text.encode()).hexdigest() for name,text in code.items()},
        fitted_models={name:dict(training_cutoff=m.training_cutoff,configuration=m.configuration(),
            encoder=m.encoder.configuration(),rules=m.rules) for name,m in models.items()},
        models={name:prepare_track(m.score_matrix(x,target=expected_target),m.configuration(),seed=42,portfolios=True)
                for name,m in models.items()})
    return publish_gap3d(payload,directory,protected=protected)
