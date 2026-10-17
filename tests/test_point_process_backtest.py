"""H19 development-only selection, causal audit and frozen comparisons."""
from copy import deepcopy
from hashlib import sha256
import importlib
import json

import numpy as np
import pandas as pd
import pytest

from src.analysis.spatiotemporal import iid_surrogate
from src.backtest.ranking import rank_metrics


def harness():
    return importlib.import_module('src.backtest.point_process')


def selection(x, signed=True):
    bt = harness(); specs = bt.candidates()
    names = {model:next(n for n,c in specs.items() if c['model']==model) for model in bt.MODELS}
    metrics = {}
    for name, config in specs.items():
        model = config['model']; loss = dict(zip(bt.MODELS,(.4,.39,.38)))[model]
        own = None if model==bt.RENEWAL else (.4 if signed or model==bt.POSITIVE else .3)
        metrics[name] = dict(logloss=loss,first_logloss=loss,second_logloss=loss,
            mean_hits=.8,self_logloss=own,first_self_logloss=own,second_self_logloss=own)
    return dict(bt.FROZEN,models={m:deepcopy(specs[n]) for m,n in names.items()},
        selected_candidates=names,development_metrics=metrics,development_positive=True,
        signed_allowed=signed,development_matrix_hash=sha256(x[:900].tobytes()).hexdigest())


class PrefixModel:
    calls = []
    def __init__(self, config=None):
        self.config = config or {'model':'Frequency26'}

    def fit(self, past, *, cutoff):
        assert len(past)==cutoff
        self.training_cutoff=cutoff; self.prefix=past.copy()
        self.selected_edges=[dict(source=1,target=2,weight=.5,training_cutoff=cutoff)]
        self.coefficients=np.array([.1,.2]); self.calls.append((self.config['model'],cutoff))
        return self

    def score_matrix(self, past, *, target):
        assert target==len(past)+1 and np.array_equal(past[:self.training_cutoff],self.prefix)
        self.last_diagnostic=[dict(number=n,target_draw=target,training_cutoff=self.training_cutoff,
            source_cutoff=target-1,current_gap=int(not past[-1,n-1])) for n in range(1,46)]
        return dict(enumerate((.05+.8*past[-1]).tolist(),1))

    def self_only_scores(self, past, *, target):
        return {n:6/45 for n in range(1,46)}


def history_frame(x):
    from src.collect.dataset import MAIN_COLUMNS
    numbers=np.array([np.flatnonzero(row)+1 for row in x])
    frame=pd.DataFrame(numbers,columns=MAIN_COLUMNS)
    frame['draw_no']=np.arange(1,len(x)+1)
    frame['draw_date']=pd.date_range('2002-12-07',periods=len(x),freq='7D').strftime('%Y-%m-%d')
    frame['bonus']=[next(n for n in range(1,46) if n not in row) for row in numbers]
    return frame


def ranking_rows(targets=(901,902,903), x=None, signed=True):
    bt=harness(); result=[]
    for target in targets:
        actual=list(range(1,7)) if x is None else (np.flatnonzero(x[target-1])+1).tolist()
        names=(bt.RENEWAL,bt.POSITIVE,*((bt.SIGNED,) if signed else ()),
            'RandomModel','Frequency26','GapLogistic')
        for offset,name in enumerate(names):
            ranking=np.roll(np.arange(1,46),offset).tolist()
            result.append(dict(model=name,target_draw=target,training_cutoff=900,feature_cutoff=target-1,
                ranking=json.dumps(ranking),actual=json.dumps(actual),scores=json.dumps({n:.2 for n in range(1,46)}),
                logloss=.4,self_logloss=.45 if name in (bt.POSITIVE,bt.SIGNED) else np.nan,
                **rank_metrics(ranking,actual),
                **{f'pool_{k}':len(set(ranking[:k])&set(actual)) for k in (6,8,10,12,15)}))
    return pd.DataFrame(result)


def test_frozen_grid_order_and_strict_constructor():
    bt=harness(); specs=bt.candidates()
    assert len(specs)==54
    assert [sum(c['model']==m for c in specs.values()) for m in bt.MODELS]==[6,24,24]
    assert [c['scheme'] for c in list(specs.values())[:6]]==['clipped']*2+['coarse']*2+['relative']*2
    assert list(specs.values())[0]==dict(model=bt.RENEWAL,scheme='clipped',alpha=26)
    for bad in (dict(list(specs.values())[0],alpha=True),dict(model=bt.POSITIVE,kernel='exp2',incoming=2,alpha=26,ridge=1)):
        with pytest.raises(ValueError):bt.construct(bad)


def test_bernoulli_loss_uses_all_45_numbers_and_clips_sparse_probabilities():
    bt=harness(); scores={n:.2 for n in range(1,46)}
    assert bt.logloss(scores,set(range(1,7)))==pytest.approx(-(6*np.log(.2)+39*np.log(.8))/45)
    assert np.isfinite(bt.logloss({n:float(n<=6) for n in range(1,46)},set(range(1,7))))
    for bad in ({1:.2},{n:1.1 for n in range(1,46)},{n:np.nan for n in range(1,46)}):
        with pytest.raises(ValueError):bt.logloss(bad,set(range(1,7)))


def test_development_freezes_fits_on_cadence_and_selects_loss_before_hits(monkeypatch):
    bt=harness(); x=iid_surrogate(900,seed=20); PrefixModel.calls=[]
    monkeypatch.setattr(bt,'construct',lambda config:PrefixModel(config))
    frozen,rows=bt.development_search(x)
    assert len(rows)==54*500
    assert len(PrefixModel.calls)==54*20
    assert set(c for _,c in PrefixModel.calls)==set(range(400,900,26))
    assert (rows.training_cutoff==400+26*((rows.target_draw-401)//26)).all()
    assert (rows.feature_cutoff==rows.target_draw-1).all()
    assert frozen['selected_candidates']=={m:next(n for n,c in bt.candidates().items() if c['model']==m) for m in bt.MODELS}
    assert not frozen['signed_allowed']
    assert frozen['development_matrix_hash']==sha256(x.tobytes()).hexdigest()
    with pytest.raises(ValueError):bt.development_search(x[:-1])
    with pytest.raises(ValueError):bt.development_search(iid_surrogate(901,seed=20))


@pytest.mark.parametrize('mutation',['future','grid','bool','extra','source','gate','half','selected','metric'])
def test_rehashed_selection_still_checks_schema_grids_metrics_and_gates(tmp_path,mutation):
    bt=harness(); s=selection(iid_surrogate(900,seed=20)); path=tmp_path/'selection.json'
    path.write_text(json.dumps(dict(selection=s,sha256=bt.configuration_hash(s))))
    assert bt.load_selection(path)==s
    chosen=s['selected_candidates'][bt.SIGNED]
    if mutation=='future':s['development_end']=901
    if mutation=='grid':s['models'][bt.SIGNED]['incoming']=2
    if mutation=='bool':s['models'][bt.SIGNED]['ridge']=True
    if mutation=='extra':s['later_score']=.1
    if mutation=='source':s['development_matrix_hash']='q'*64
    if mutation=='gate':s['signed_allowed']=False
    if mutation=='half':s['development_metrics'][chosen]['first_logloss']=.9
    if mutation=='selected':s['selected_candidates'][bt.SIGNED]=list(bt.candidates())[-1]
    if mutation=='metric':s['selection_metric']='meanTop6hits'
    path.write_text(json.dumps(dict(selection=s,sha256=bt.configuration_hash(s))))
    with pytest.raises(ValueError):bt.load_selection(path)


def test_signed_gate_requires_each_half_and_nested_own_baseline():
    bt=harness(); x=iid_surrogate(900,seed=20); s=selection(x,signed=False)
    assert bt._validate_selection(s)==s
    assert bt.POSITIVE in bt.factories(s) and bt.SIGNED not in bt.factories(s)
    s=selection(x); name=s['selected_candidates'][bt.SIGNED]
    s['development_metrics'][name].update(first_logloss=.4,second_logloss=.36)
    s['signed_allowed']=False
    assert bt._validate_selection(s)==s


@pytest.mark.parametrize('signed',[False,True])
def test_evaluate_captures_probabilities_state_and_true_outer_fit_cutoff(monkeypatch,signed):
    bt=harness(); x=iid_surrogate(903,seed=20); s=selection(x,signed=signed)
    monkeypatch.setattr(bt,'construct',lambda config:PrefixModel(config))
    monkeypatch.setattr(bt,'construct_baseline',lambda:PrefixModel())
    gap=ranking_rows(x=x,signed=signed); gap=gap[gap.model=='GapLogistic'].copy()
    gap['scores']=json.dumps({n:float(50-n) for n in range(1,46)})
    monkeypatch.setattr(bt,'frozen_gap',lambda matrix,*,cadence:gap.copy())
    result=bt.evaluate(history_frame(x),s)
    assert len(result)==3*(6 if signed else 5)
    assert result[result.model=='GapLogistic'].logloss.isna().all()
    for name in (bt.RENEWAL,bt.POSITIVE,*((bt.SIGNED,) if signed else ())):
        group=result[result.model==name]
        assert group.training_cutoff.tolist()==[900]*3
        assert group.feature_cutoff.tolist()==[900,901,902]
        assert group.source_cutoff.tolist()==[900,901,902]
        for row in group.itertuples():
            assert len(json.loads(row.last_diagnostic))==45
            assert json.loads(row.selected_edges)[0]['training_cutoff']==900
            actual=set(json.loads(row.actual))
            assert row.logloss==pytest.approx(bt.logloss(json.loads(row.probabilities),actual))
            if name!=bt.RENEWAL:
                assert row.self_logloss==pytest.approx(bt.logloss(json.loads(row.self_scores),actual))
    s['development_matrix_hash']='0'*64
    with pytest.raises(ValueError,match='prefix'):bt.evaluate(history_frame(x),s)


def test_paired_and_conditional_reports_pair_draws_and_include_loss():
    bt=harness(); s=selection(iid_surrogate(900,seed=20)); rows=ranking_rows((901,1001,1101))
    report=bt.paired_report(rows,s,replicates=20,block=52)
    assert set(report.reference)=={'RandomModel','GapLogistic',bt.RENEWAL,'Frequency26'}
    assert len(report)==3*(2+3+3)*15+3*(1+2+2+3)
    assert set(report[report.reference=='Frequency26'].metric)=={'logloss'}
    assert not ((report.model==bt.RENEWAL)&(report.reference==bt.RENEWAL)).any()
    assert not ((report.metric=='logloss')&(report.reference=='GapLogistic')).any()
    losses,summary=bt.conditional_report(rows,s,replicates=20,block=13)
    assert len(losses)==6
    assert set(summary.model)=={bt.POSITIVE,bt.SIGNED}
    assert np.allclose(summary.difference,-.05)
    assert (summary.ci_low==summary.ci_high).all()
    for bad in (rows.iloc[:-1],pd.concat([rows,rows.iloc[:1]]),rows.assign(hits=6)):
        with pytest.raises(ValueError):bt.paired_report(bad,s,replicates=20)
    for bad in (rows.assign(logloss=-1),rows.assign(logloss=np.nan)):
        with pytest.raises(ValueError):bt.paired_report(bad,s,replicates=20)


def test_frequency_loss_pairs_targets_despite_disjoint_dataframe_indices():
    bt=harness(); s=selection(iid_surrogate(900,seed=20))
    rows=ranking_rows((901,1001,1101))
    report=bt.paired_report(rows,s,replicates=20,block=26)
    frequency=report[report.reference=='Frequency26']
    assert np.isfinite(frequency[['difference','ci_low','ci_high']].to_numpy()).all()
    for row in frequency.itertuples():
        own=rows[(rows.model==row.model)&(rows.target_draw>=row.start)].sort_values('target_draw')
        fixed=rows[(rows.model=='Frequency26')&(rows.target_draw>=row.start)].sort_values('target_draw')
        assert row.targets==len(own)
        assert row.difference==pytest.approx(np.mean(own.logloss.to_numpy()-fixed.logloss.to_numpy()))


def test_diversity_uses_only_verified_archives_and_number_coordinates(tmp_path):
    bt=harness(); s=selection(iid_surrogate(900,seed=20)); rows=ranking_rows()
    report=bt.correlation_report(rows,s)
    assert set(report.model)==set(bt.MODELS)
    old=rows[rows.model=='GapLogistic'].copy(); old['model']='MirrorModel'
    path=tmp_path/'predictions.csv'; old.to_csv(path,index=False)
    (tmp_path/'run_manifest.json').write_text(json.dumps(dict(research_cutoff=1245,draw1246_used=False,
        artifacts={'predictions.csv':dict(sha256=sha256(path.read_bytes()).hexdigest())})))
    assert 'Phase18Mirror' in set(bt.correlation_report(rows,s,mirror_path=path).reference)
    path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='integrity|hash'):bt.correlation_report(rows,s,mirror_path=path)


def test_loss_selection_beats_top6_hits_and_remains_within_model_family():
    bt=harness(); specs=bt.candidates(); rows=[]
    for index,(name,config) in enumerate(specs.items()):
        for target in range(401,901):
            rows.append(dict(candidate=name,target_draw=target,hits=6-index/10,
                logloss=1-index/100,self_logloss=1.1 if config['model']!=bt.RENEWAL else np.nan))
    frozen=bt._freeze_selection(pd.DataFrame(rows),iid_surrogate(900,seed=20))
    assert frozen['selected_candidates']=={m:next(n for n,c in reversed(specs.items()) if c['model']==m) for m in bt.MODELS}
    assert not frozen['signed_allowed']  # Lower loss alone cannot pass the Top6 gate.


def test_capture_snapshots_main_diagnostics_and_rejects_future_edge_cutoffs():
    bt=harness(); x=iid_surrogate(400,seed=20); collector=[]
    class MutableNested(PrefixModel):
        def self_only_scores(self,past,*,target):
            self.last_diagnostic=[dict(number=999)]
            return super().self_only_scores(past,target=target)
    capture=bt._CaptureState(MutableNested(),bt.POSITIVE,collector).fit(x,cutoff=400)
    capture.score_matrix(x,target=401)
    assert len(json.loads(collector[0]['last_diagnostic']))==45
    capture.model.selected_edges[0]['training_cutoff']=401
    with pytest.raises(ValueError,match='cutoff|training'):
        capture.score_matrix(x,target=401)


def test_capture_rejects_incomplete_or_noncausal_current_diagnostics():
    bt=harness(); x=iid_surrogate(400,seed=20)
    class WrongState(PrefixModel):
        def score_matrix(self,past,*,target):
            scores=super().score_matrix(past,target=target)
            self.last_diagnostic[0]['source_cutoff']=target
            return scores
    capture=bt._CaptureState(WrongState(),bt.RENEWAL,[]).fit(x,cutoff=400)
    with pytest.raises(ValueError,match='cutoff|causal'):
        capture.score_matrix(x,target=401)
