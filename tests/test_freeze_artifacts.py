from copy import deepcopy
import json
import socket
import pandas as pd
import pytest
from hashlib import sha256
from src.analysis.features import feature_columns,GAP,PERIODICITY
from src.models.predictive import LogisticModel,SimilarityModel
from src.models.bayesian import BayesianModel
from src.models.regime import HMMModel
from src.models.hazard import GapHazardModel
from src.regime_cli import FrequencyModel
from src.prediction_scope import ProspectiveScope
from src.freeze_artifacts import prepare_track, publish_freeze, verify_freeze
from src.freeze_evaluator import evaluate_freeze


def payload():
    scores={n:float(46-n) for n in range(1,46)}
    common=dict(seed=42,prediction_scope=ProspectiveScope(210))
    policies=dict(GapLogistic=LogisticModel(columns=GAP,**common),GapHazard=GapHazardModel(**common),
        BayesianStatic=BayesianModel(**common),BayesianRecent=BayesianModel(half_life=52,**common),
        HMM2=HMMModel(states=2,**common),HMM3=HMMModel(states=3,**common),
        SimilarityModel=SimilarityModel(**common),Frequency52=FrequencyModel(**common),
        GapPeriodicityLogistic=LogisticModel(columns=GAP+PERIODICITY,**common))
    components={name:dict(scores=scores,configuration=policy.configuration(),
        fitted=dict(training_cutoff=210,training_rows=4770)) for name,policy in policies.items()}
    ensemble_config=dict(components=list(policies),normalization='rank',weights=[.2]+[.1]*8,development_end=200,selection=[])
    raw_ensemble=json.dumps({'Ensemble[DevelopmentWeights]':ensemble_config})
    models={name:prepare_track(scores,components[name]['configuration'],seed=42,portfolios=name=='GapLogistic')
            for name in ('GapLogistic','BayesianStatic','HMM2','HMM3')}
    models['Ensemble']=prepare_track({n:(45-n)/44 for n in range(1,46)},ensemble_config,portfolios=True)
    models['UniformRandom']=prepare_track({n:6/45 for n in range(1,46)},{},seed=42,uniform=True)
    return dict(schema_version=2,experiment_id='synthetic-211',target_draw=211,training_cutoff=210,
        latest_training_date='2006-12-09',created_at='2026-10-17T07:00:00+09:00',
        canonical_dataset_sha256='a'*64,git_commit='b'*40,git_dirty=True,
        target_result_retrieved=False,target_result_inspected=False,status='FROZEN_UNEVALUATED',
        models=models,environment={},protocol=dict(version='phase5-v1',seed=42,target_draw=211,training_cutoff=210,
            supervised_target_range=[105,210]),feature_definitions=dict(columns=feature_columns(),version='canonical-v1-unchanged'),
        ensemble_source=dict(configuration=ensemble_config,sha256=sha256(raw_ensemble.encode()).hexdigest(),raw_json=raw_ensemble),components=components,
        source_draw_range=[1,210],source_rows=210,
        feature_audit=dict(training_rows=4770,training_target_min=105,training_target_max=210,current_rows=45,current_feature_cutoff=210),
        current_features=[dict({c:0 for c in feature_columns()},number=n,target_draw=211,feature_cutoff=210) for n in range(1,46)],
        implementation_sources={'src/analysis/features.py':'synthetic'},
        implementation_hashes={'src/analysis/features.py':sha256(b'synthetic').hexdigest()})


def test_complete_ranks_ties_budget_controls_and_determinism():
    p=payload()
    assert p==payload()
    for name,m in p['models'].items():
        assert set(m['ranking'])==set(range(1,46)) and len(m['ranking'])==45
        for k in (6,8,10,12,15): assert m['top_k'][str(k)]==m['ranking'][:k]
        for tickets in m['portfolios'].values():
            for budget,group in tickets.items():
                assert len(group)==int(budget)
                assert len(set(tuple(t) for t in group))==len(group)
                assert all(len(set(t))==6 and set(t)<=set(range(1,46)) for t in group)
    assert p['models']['UniformRandom']['tie_groups']==[list(range(1,46))]
    assert p['models']['GapLogistic']['direct_top6']==[1,2,3,4,5,6]


def test_artifact_nonoverwrite_hash_and_registry(tmp_path):
    paths=publish_freeze(payload(),tmp_path)
    snapshot=paths['snapshot']; before=snapshot.read_bytes()
    verified=verify_freeze(snapshot)
    assert verified['status']=='FROZEN_UNEVALUATED'
    registry=pd.read_csv(tmp_path/'registry.csv')
    assert registry.status.tolist()==['FROZEN_UNEVALUATED']
    assert registry.target_draw.tolist()==[211]
    with pytest.raises(ValueError): publish_freeze(payload(),tmp_path)
    assert snapshot.read_bytes()==before
    manifest=paths['manifest']; manifest.write_text(manifest.read_text()+'tampered')
    with pytest.raises(ValueError,match='integrity'): verify_freeze(snapshot)


def test_registry_supports_later_experiment_without_changing_first(tmp_path):
    p=payload(); a=publish_freeze(p,tmp_path); before=a['snapshot'].read_bytes()
    p=deepcopy(p); p.update(target_draw=212,training_cutoff=211,experiment_id='synthetic-212')
    p['source_draw_range']=[1,211]; p['source_rows']=211
    p['protocol'].update(target_draw=212,training_cutoff=211,supervised_target_range=[105,211])
    p['feature_audit'].update(training_rows=4815,training_target_max=211,current_feature_cutoff=211)
    for row in p['current_features']: row.update(target_draw=212,feature_cutoff=211)
    for component in p['components'].values():
        component['configuration']['prospective_scope']=dict(cutoff=211,target=212)
        component['fitted'].update(training_cutoff=211,training_rows=4815)
    for name in ('GapLogistic','BayesianStatic','HMM2','HMM3'):
        p['models'][name]['configuration']=p['components'][name]['configuration']
    b=publish_freeze(p,tmp_path)
    assert a['snapshot']!=b['snapshot'] and a['snapshot'].read_bytes()==before
    assert len(pd.read_csv(tmp_path/'registry.csv'))==2


def test_synthetic_evaluator_no_network_and_no_mutation(tmp_path,monkeypatch):
    monkeypatch.setattr(socket.socket,'connect',lambda *a,**k:pytest.fail('network forbidden'))
    paths=publish_freeze(payload(),tmp_path); snapshot=paths['snapshot']
    original={p:p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
    result=tmp_path/'synthetic-result.json'
    result.write_text(json.dumps(dict(draw_no=211,main_numbers=[1,2,3,4,5,45],bonus=6)))
    evaluated=evaluate_freeze(snapshot,result)
    gap=evaluated['models']['GapLogistic']
    assert gap['top6_hits']==5 and gap['direct_top6']['prize']==2
    assert gap['pools']['8']['winners']==5 and gap['pools']['8']['ge5']
    assert gap['pools']['15']['ge6'] is False
    for method,by_budget in gap['portfolios'].items():
        for budget,metrics in by_budget.items():
            assert metrics['tickets']==int(budget)
            assert 'delta_best_vs_uniform' in metrics
    assert all(p.read_bytes()==content for p,content in original.items())
    result.write_text(json.dumps(dict(draw_no=212,main_numbers=[1,2,3,4,5,45],bonus=6)))
    with pytest.raises(ValueError,match='target'): evaluate_freeze(snapshot,result)


def test_snapshot_invariant_validation_before_write(tmp_path):
    p=payload(); p['models']['GapLogistic']['top_k']['8']=[1]*8
    with pytest.raises(ValueError): publish_freeze(p,tmp_path)
    assert not list(tmp_path.glob('*.json'))
    p=payload(); p['target_draw']=210
    with pytest.raises(ValueError): publish_freeze(p,tmp_path)


def test_failed_publication_permanently_reserves_target(tmp_path,monkeypatch):
    import src.freeze_artifacts as module
    def broken(*a): raise OSError('Simulated disk write failure')
    monkeypatch.setattr(module,'manifest_text',broken)
    with pytest.raises(OSError): publish_freeze(payload(),tmp_path)
    p=payload(); p['experiment_id']='retry-new-id'
    with pytest.raises(ValueError,match='reserv|frozen'): publish_freeze(p,tmp_path)


@pytest.mark.parametrize('mutation',[
    lambda p:p['models']['HMM2']['configuration'].update(states=3),
    lambda p:p['current_features'][0].update(appeared_next=1),
    lambda p:p['feature_audit'].update(training_target_max=211),
    lambda p:p['implementation_hashes'].update({'src/analysis/features.py':'0'*64}),
    lambda p:p['components']['GapLogistic']['fitted'].update(training_cutoff=211),
    lambda p:p['ensemble_source']['configuration'].update(weights=[1]+[0]*8),
])
def test_reject_malformed_provenance(tmp_path,mutation):
    p=payload(); mutation(p)
    with pytest.raises(ValueError): publish_freeze(p,tmp_path)


def test_registry_metadata_tamper_is_rejected(tmp_path):
    paths=publish_freeze(payload(),tmp_path)
    registry=tmp_path/'registry.csv'
    frame=pd.read_csv(registry); frame.loc[0,'target_draw']=999
    frame.to_csv(registry,index=False)
    with pytest.raises(ValueError,match='Registry'): verify_freeze(paths['snapshot'])


def test_evaluation_never_regenerates_frozen_tickets(tmp_path,monkeypatch):
    paths=publish_freeze(payload(),tmp_path)
    def forbidden(*args,**kwargs): pytest.fail('Frozen tickets must not be regenerated')
    monkeypatch.setattr('src.freeze_artifacts.make_portfolio',forbidden)
    monkeypatch.setattr('src.freeze_artifacts.uniform_portfolio',forbidden)
    result=tmp_path/'result.json'; result.write_text(json.dumps(dict(draw_no=211,main_numbers=[1,2,3,4,5,45],bonus=6)))
    assert evaluate_freeze(paths['snapshot'],result)['models']['GapLogistic']['top6_hits']==5
    result.write_text(json.dumps(dict(draw_no=211,main_numbers=[1,2,3,4,5,45],bonus=5)))
    with pytest.raises(ValueError): evaluate_freeze(paths['snapshot'],result)
