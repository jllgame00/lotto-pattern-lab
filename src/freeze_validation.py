"""Version2 provenance contracts independent of future refits or ticket algorithms."""
from hashlib import sha256
import json
import re
import numpy as np

COMPONENTS=['GapLogistic','GapHazard','BayesianStatic','BayesianRecent','HMM2','HMM3',
            'SimilarityModel','Frequency52','GapPeriodicityLogistic']
WEIGHTS=[.2]+[.1]*8


def validate_provenance(p):
    cutoff=p['training_cutoff']; target=p['target_draw']; protocol=p['protocol']
    if (p['source_draw_range']!=[1,cutoff] or p['source_rows']!=cutoff or
        protocol['target_draw']!=target or protocol['training_cutoff']!=cutoff or
        protocol['supervised_target_range']!=[105,cutoff] or protocol['version']!='phase5-v1' or protocol['seed']!=42):
        raise ValueError('Source/protocol cutoff or fixed configuration mismatch')
    if not re.fullmatch('[0-9a-f]{64}',p['canonical_dataset_sha256']): raise ValueError('Invalid source digest')
    audit=p['feature_audit']
    if any(audit[k]!=v for k,v in dict(training_rows=(cutoff-104)*45,training_target_min=105,
        training_target_max=cutoff,current_rows=45,current_feature_cutoff=cutoff).items()):
        raise ValueError('Feature audit exceeds or differs from frozen cutoff')
    rows=p['current_features']; columns=p['feature_definitions']['columns']
    if len(rows)!=45 or {r['number'] for r in rows}!=set(range(1,46)):
        raise ValueError('Exactly45 current feature rows required')
    for row in rows:
        if ('appeared_next' in row or 'bonus' in row or row['target_draw']!=target or
            row['feature_cutoff']!=cutoff or not set(columns)<=set(row)):
            raise ValueError('Current feature rows expose outcomes or incorrect cutoffs/definitions')
    sources=p['implementation_sources']; hashes=p['implementation_hashes']
    if not sources or set(sources)!=set(hashes) or 'src/analysis/features.py' not in sources:
        raise ValueError('Implementation provenance missing')
    for path,text in sources.items():
        if sha256(text.encode('utf-8')).hexdigest()!=hashes[path]: raise ValueError('Implementation hash mismatch')
    components=p['components']
    if set(components)!=set(COMPONENTS): raise ValueError('All nine frozen ensemble components required')
    configurations={
        'GapLogistic':dict(model='LogisticModel',C=1.),
        'GapPeriodicityLogistic':dict(model='LogisticModel',C=1.),
        'BayesianStatic':dict(model='BayesianModel',alpha=2.,beta=13.,half_life=None),
        'BayesianRecent':dict(model='BayesianModel',alpha=2.,beta=13.,half_life=52),
        'HMM2':dict(model='HMMModel',states=2,window=260,max_iter=40,n_init=2),
        'HMM3':dict(model='HMMModel',states=3,window=260,max_iter=40,n_init=2),
        'GapHazard':dict(model='GapHazardModel',kind='gap',prior_strength=75),
        'SimilarityModel':dict(model='SimilarityModel',k=30,metric='euclidean',weighting='distance'),
        'Frequency52':dict(model='FrequencyModel',features=['rate_52'])}
    for name,component in components.items():
        config=component['configuration']; fitted=component['fitted']
        if any(config.get(k)!=v for k,v in configurations[name].items()): raise ValueError('Model configuration mismatch')
        if (config.get('seed')!=42 or config['prospective_scope']!=dict(cutoff=cutoff,target=target) or
            fitted['training_cutoff']!=cutoff or fitted['training_rows']!=audit['training_rows']):
            raise ValueError('Fitted component cutoff/configuration mismatch')
        scores={int(k):v for k,v in component['scores'].items()}
        if set(scores)!=set(range(1,46)) or not np.isfinite(list(scores.values())).all(): raise ValueError('Invalid component scores')
    for name in ('GapLogistic','BayesianStatic','HMM2','HMM3'):
        track=p['models'][name]; component=components[name]
        if track['configuration']!=component['configuration'] or track['scores']!=component['scores']:
            raise ValueError('Independent track differs from corresponding frozen component')
    source=p['ensemble_source']; config=source['configuration']; ensemble=p['models']['Ensemble']
    if (config['components']!=COMPONENTS or config['weights']!=WEIGHTS or config['normalization']!='rank' or
        not 0<config['development_end']<target or config['development_end']>900 or
        (target==1246 and config['development_end']!=900)):
        raise ValueError('Existing ensemble provenance/configuration mismatch')
    raw=source['raw_json']
    if (sha256(raw.encode('utf-8')).hexdigest()!=source['sha256'] or
        json.loads(raw).get('Ensemble[DevelopmentWeights]')!=config):
        raise ValueError('Frozen ensemble source hash/configuration mismatch')
    for key in ('components','weights','normalization','development_end'):
        if ensemble['configuration'].get(key)!=config[key]: raise ValueError('Frozen ensemble track configuration mismatch')
    normalized=[]
    for name in COMPONENTS:
        scores={int(k):v for k,v in components[name]['scores'].items()}
        x=np.array([scores[n] for n in range(1,46)])
        normalized.append(np.full(45,.5) if np.ptp(x)<1e-12 else
            np.array([(np.sum(x<v)+.5*(np.sum(x==v)-1))/44 for v in x]))
    expected=np.array(WEIGHTS)@np.array(normalized)
    scores={int(k):v for k,v in ensemble['scores'].items()}
    if not np.allclose([scores[n] for n in range(1,46)],expected,rtol=1e-12,atol=1e-12):
        raise ValueError('Ensemble scores disagree with frozen rank-average components')
