"""H18's development freeze, causal evaluation, and matched rank comparisons."""
from hashlib import sha256
import importlib
import json

import numpy as np
import pandas as pd
import pytest

from src.analysis.spatiotemporal import iid_surrogate
from src.backtest.ranking import rank_metrics


def harness():
    return importlib.import_module('src.backtest.change_point')


def frozen_selection(x, *, combo=False):
    bt = harness()
    name, config = next(iter(bt.candidates().items()))
    return dict(version='phase19-v1', research_cutoff=1245, development_start=401,
        development_end=900, later_start=901, candidate_count=60,
        models={'RegimeFrequencyModel': config}, selected_candidates={'RegimeFrequencyModel': name},
        best_fixed_frequency='Frequency26', combo_allowed=combo,
        selection_metric='meanTop6hits;tiesdeclaredorder',
        combination_rule='equal ranks; regime>.8 overall and both development halves; regime>best fixed overall',
        development_metrics=dict(regime_mean=1.2 if combo else .8,
            regime_first_half=1.1 if combo else .8, regime_second_half=1.3 if combo else .8,
            fixed_means={'Frequency26':.9, 'Frequency52':.8, 'Frequency104':.7}),
        development_matrix_hash=sha256(x[:900].tobytes()).hexdigest(), draw1246_used=False)


class PrefixModel:
    def __init__(self, window=1):
        self.window = window

    def fit(self, past, *, cutoff):
        assert len(past) == cutoff < 1245
        self.training_cutoff = cutoff
        self.prefix = past.copy()
        return self

    def score_matrix(self, past, *, target):
        assert target == len(past)+1
        assert np.array_equal(past[:self.training_cutoff], self.prefix)
        length = min(52, len(past))
        rates = past[-length:].mean(0).tolist()
        self.last_state = dict(last_change_point=len(past)-length, segment_length=length,
            segment_rates=rates, current_rates=rates, training_cutoff=target-1, representation='A')
        return dict(enumerate(past[-self.window:].mean(0).tolist(), 1))


def ranking_rows(targets=(901,902,903)):
    output = []
    actual = list(range(1,7))
    for target in targets:
        for offset, name in enumerate(('RegimeFrequencyModel','RandomModel','Frequency26',
                                        'Frequency52','Frequency104','GapLogistic')):
            ranking = np.roll(np.arange(1,46), offset).tolist()
            output.append(dict(model=name, target_draw=target, training_cutoff=900,
                feature_cutoff=target-1, ranking=json.dumps(ranking), actual=json.dumps(actual),
                **rank_metrics(ranking, actual),
                **{f'pool_{k}':len(set(ranking[:k]) & set(actual)) for k in (6,8,10,12,15)}))
    return pd.DataFrame(output)


def test_grid_and_development_ties_follow_declared_order():
    bt = harness()
    specs = bt.candidates()
    assert len(specs) == 60
    assert {c['representation'] for c in specs.values()} == {'A','B13','B26','B52','C'}
    names = list(specs)
    rows = pd.DataFrame([dict(candidate=name, target_draw=t, hits=1)
        for name in reversed(names) for t in (899,900)])
    assert bt.select_development(rows) == names[0]
    for bad in (rows.assign(target_draw=901), rows.iloc[:-1],
                pd.concat([rows,rows.iloc[:1]]), rows.assign(hits=.5)):
        with pytest.raises(ValueError):
            bt.select_development(bad)
    with pytest.raises(ValueError):
        bt.select_development(rows, end=901)


def test_development_refits_63_models_on_completed_prefixes_and_freezes_best_fixed(monkeypatch):
    bt = harness()
    x = iid_surrogate(900, seed=19)
    monkeypatch.setattr(bt, 'construct', lambda config: PrefixModel())
    monkeypatch.setattr(bt, 'construct_baseline', lambda window: PrefixModel(window))
    selection, rows = bt.development_search(x)
    assert len(rows) == 31500
    assert set(rows.target_draw) == set(range(401,901))
    assert not rows.duplicated(['candidate','target_draw']).any()
    assert (rows.feature_cutoff == rows.target_draw-1).all()
    assert (rows.training_cutoff == rows.target_draw-1).all()
    # Independent number ordering and window sums, including the declared tie.
    fixed_means = {}
    for window in (26,52,104):
        hits = []
        for target in range(401,901):
            top = sorted(range(45),key=lambda n:(-int(x[target-1-window:target-1,n].sum()),n))[:6]
            hits.append(int(x[target-1,top].sum()))
        fixed_means[f'Frequency{window}'] = float(np.mean(hits))
    assert selection['best_fixed_frequency'] == max(fixed_means,key=fixed_means.get)
    assert selection['development_metrics']['fixed_means'] == fixed_means
    assert selection['models']['RegimeFrequencyModel'] == next(iter(bt.candidates().values()))
    m = selection['development_metrics']
    assert selection['combo_allowed'] == (m['regime_mean']>.8 and
        m['regime_mean']>max(fixed_means.values()) and m['regime_first_half']>.8 and m['regime_second_half']>.8)
    with pytest.raises(ValueError):
        bt.development_search(x[:-1])


@pytest.mark.parametrize('mutation', ['hash','future','grid','boolean','best_fixed','gate','half','extra'])
def test_frozen_selection_rejects_rehashed_schema_grid_and_gate_changes(tmp_path, mutation):
    bt = harness()
    selection = frozen_selection(iid_surrogate(900, seed=19))
    path = tmp_path/'selection.json'
    path.write_text(json.dumps(dict(selection=selection,sha256=bt.configuration_hash(selection))))
    assert bt.load_selection(path) == selection
    if mutation == 'future':selection['development_end'] = 901
    if mutation == 'grid':selection['models']['RegimeFrequencyModel']['minimum'] = 13
    if mutation == 'boolean':selection['models']['RegimeFrequencyModel']['multiplier'] = True
    if mutation == 'best_fixed':selection['best_fixed_frequency'] = 'Frequency104'
    if mutation == 'gate':selection['combo_allowed'] = True
    if mutation == 'half':selection['development_metrics']['regime_first_half'] = 1.8
    if mutation == 'extra':selection['later_weight'] = .7
    digest = '0'*64 if mutation == 'hash' else bt.configuration_hash(selection)
    path.write_text(json.dumps(dict(selection=selection,sha256=digest)))
    with pytest.raises(ValueError):
        bt.load_selection(path)


def test_cutoff_annotations_preserve_outer_schedule():
    rows = harness().annotate_cutoffs(ranking_rows())
    for name in ('RegimeFrequencyModel','Frequency26','Frequency52','Frequency104'):
        group = rows[rows.model==name]
        assert group.training_cutoff.tolist() == [900,901,902]
        assert group.outer_fit_cutoff.tolist() == [900,900,900]
    assert rows[rows.model=='GapLogistic'].training_cutoff.tolist() == [900,900,900]


def history_frame(x):
    from src.collect.dataset import MAIN_COLUMNS
    numbers = np.array([np.flatnonzero(row)+1 for row in x])
    history = pd.DataFrame(numbers, columns=MAIN_COLUMNS)
    history['draw_no'] = np.arange(1,len(x)+1)
    history['draw_date'] = pd.date_range('2002-12-07', periods=len(x), freq='7D').strftime('%Y-%m-%d')
    history['bonus'] = [next(n for n in range(1,46) if n not in row) for row in numbers]
    return history


@pytest.mark.parametrize('combo', [False, True])
def test_evaluate_reuses_gap_captures_current_state_and_equal_number_ranks(monkeypatch, combo):
    bt = harness()
    x = iid_surrogate(903, seed=19)
    monkeypatch.setattr(bt,'construct',lambda config:PrefixModel())
    monkeypatch.setattr(bt,'construct_baseline',lambda window:PrefixModel(window))
    gap = ranking_rows()
    gap = gap[gap.model=='GapLogistic'].copy()
    for index, row in gap.iterrows():
        actual = (np.flatnonzero(x[row.target_draw-1])+1).tolist()
        ranking = json.loads(row.ranking)
        gap.loc[index,'actual'] = json.dumps(actual)
        for key,value in rank_metrics(ranking,actual).items():gap.loc[index,key] = value
        for k in (6,8,10,12,15):gap.loc[index,f'pool_{k}'] = len(set(ranking[:k]) & set(actual))
    monkeypatch.setattr(bt,'frozen_gap',lambda matrix,*,cadence:gap.copy())
    result = bt.evaluate(history_frame(x),frozen_selection(x,combo=combo))
    assert len(result) == 3*(7 if combo else 6)
    regime = result[result.model=='RegimeFrequencyModel']
    assert regime.training_cutoff.tolist() == [900,901,902]
    assert regime.outer_fit_cutoff.tolist() == [900,900,900]
    assert regime.source_cutoff.tolist() == [900,901,902]
    assert regime.current_segment_length.tolist() == [52]*3
    assert regime.last_change_point.tolist() == [848,849,850]
    assert regime.diagnostics_available.all()
    for row in regime.itertuples():
        assert json.loads(row.segment_rates) == x[row.target_draw-53:row.target_draw-1].mean(0).tolist()
    if combo:
        for row in result[result.model=='GapRegimeRankAverage'].itertuples():
            a = json.loads(regime[regime.target_draw==row.target_draw].iloc[0].ranking)
            b = json.loads(gap[gap.target_draw==row.target_draw].iloc[0].ranking)
            expected = sorted(range(1,46),key=lambda n:(a.index(n)+b.index(n),n))
            assert json.loads(row.ranking) == expected
            assert row.hits == len(set(expected[:6]) & set(np.flatnonzero(x[row.target_draw-1])+1))
    changed = frozen_selection(x);changed['development_matrix_hash'] = '0'*64
    with pytest.raises(ValueError,match='prefix'):
        bt.evaluate(history_frame(x),changed)


def test_paired_report_uses_development_best_fixed_and_checks_matching_metrics():
    bt = harness()
    rows = ranking_rows((901,1001,1101))
    selection = frozen_selection(iid_surrogate(900,seed=19))
    report = bt.paired_report(rows,selection,replicates=20,block=52)
    assert set(report.reference) == {'RandomModel','Frequency26','GapLogistic'}
    assert set(report.start) == {901,1001,1101}
    assert len(report) == 135
    delta = report[(report.reference=='Frequency26') & (report.metric=='hits')].iloc[0]
    assert delta.difference == 2 and delta.ci_low == 2 and delta.ci_high == 2
    for bad in (rows.iloc[:-1],pd.concat([rows,rows.iloc[:1]]),rows.assign(hits=6)):
        with pytest.raises(ValueError):
            bt.paired_report(bad,selection,replicates=20)


def test_rank_correlation_uses_number_coordinates_and_verified_optional_archives(tmp_path):
    bt = harness()
    rows = ranking_rows()
    report = bt.correlation_report(rows)
    a = json.loads(rows.iloc[0].ranking)
    b = json.loads(rows[rows.model=='GapLogistic'].iloc[0].ranking)
    delta = np.array([a.index(n)-b.index(n) for n in range(1,46)])
    assert report.iloc[0].spearman == pytest.approx(1-6*(delta**2).sum()/(45*(45**2-1)))
    old = rows[rows.model=='GapLogistic'].copy();old['model'] = 'MirrorModel'
    path = tmp_path/'predictions.csv';old.to_csv(path,index=False)
    manifest = dict(research_cutoff=1245,draw1246_used=False,
        artifacts={'predictions.csv':{'sha256':sha256(path.read_bytes()).hexdigest()}})
    (tmp_path/'run_manifest.json').write_text(json.dumps(manifest))
    assert set(bt.correlation_report(rows,mirror_path=path).reference) == {'GapLogistic','Phase18Mirror'}
    path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='hash|integrity'):
        bt.correlation_report(rows,mirror_path=path)


def test_sensitivity_varies_one_adjacent_parameter_and_never_representation(monkeypatch):
    bt = harness()
    x = iid_surrogate(902,seed=19)
    monkeypatch.setattr(bt,'construct',lambda config:PrefixModel())
    selection = frozen_selection(x)
    before = json.dumps(selection,sort_keys=True)
    report = bt.sensitivity(x,selection)
    assert report.diagnostic_only.all()
    assert set(report.target_draw) == {901,902}
    assert report.groupby('candidate').size().eq(2).all()
    chosen = selection['models']['RegimeFrequencyModel']
    for name in report.candidate.unique():
        config = bt.candidates()[name]
        assert config['representation'] == chosen['representation']
        assert sum(config[k]!=chosen[k] for k in ('minimum','multiplier','shrinkage')) <= 1
    assert json.dumps(selection,sort_keys=True) == before


def test_frozen_fixed_ties_and_combination_strict_thresholds(tmp_path):
    bt = harness()
    selection = frozen_selection(iid_surrogate(900,seed=19))
    # Dictionary insertion order cannot change the predeclared window tie.
    selection['development_metrics']['fixed_means'] = {
        'Frequency104':.9,'Frequency52':.9,'Frequency26':.9}
    path = tmp_path/'selection.json'
    for first,second,expected in ((.8,1.2,False),(1.0,1.0,True),(.9,.9,False)):
        selection['development_metrics'].update(regime_first_half=first,
            regime_second_half=second,regime_mean=(first+second)/2)
        selection['combo_allowed'] = expected
        path.write_text(json.dumps(dict(selection=selection,sha256=bt.configuration_hash(selection))))
        assert bt.load_selection(path)['combo_allowed'] == expected
        assert bt.load_selection(path)['best_fixed_frequency'] == 'Frequency26'


def test_factories_are_lazy_and_constructor_rejects_undeclared_configuration(monkeypatch):
    bt = harness()
    selection = frozen_selection(iid_surrogate(900,seed=19))
    called = []
    monkeypatch.setattr(bt,'construct',lambda config:called.append(config) or PrefixModel())
    monkeypatch.setattr(bt,'construct_baseline',lambda window:called.append(window) or PrefixModel(window))
    factories = bt.factories(selection)
    assert not called
    # Frozen factories copy the chosen configuration rather than following later mutation.
    selection['models']['RegimeFrequencyModel']['minimum'] = 104
    factories['RegimeFrequencyModel']()
    assert called[0]['minimum'] == 26


def test_canonical_model_cannot_silently_omit_current_state(monkeypatch):
    bt = harness()
    class MissingState(PrefixModel):
        def score_matrix(self,past,*,target):
            scores = super().score_matrix(past,target=target)
            del self.last_state
            return scores
    # The production model must supply audit evidence; lightweight external
    # test doubles may lack it, and are marked unavailable instead.
    MissingState.__module__ = 'src.models.change_point'
    x = iid_surrogate(901,seed=19)
    collector = []
    model = bt._CaptureState(MissingState(),collector,'A').fit(x[:900],cutoff=900)
    with pytest.raises(ValueError,match='state|audit'):
        model.score_matrix(x[:900],target=901)


def test_captured_raw_segment_rates_must_match_completed_prefix():
    bt = harness()
    class WrongRates(PrefixModel):
        def score_matrix(self,past,*,target):
            scores = super().score_matrix(past,target=target)
            self.last_state['segment_rates'] = [0.0]*45
            return scores
    x = iid_surrogate(901,seed=19)
    model = bt._CaptureState(WrongRates(),[],'A').fit(x[:900],cutoff=900)
    with pytest.raises(ValueError,match='segment|audit'):
        model.score_matrix(x[:900],target=901)
