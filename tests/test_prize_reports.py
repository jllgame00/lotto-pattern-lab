import json

import numpy as np
import pandas as pd
import pytest

from src.backtest.prize_reports import candidate_reports, paired_difference, portfolio_reports
from src.backtest.prize_experiment import evaluate_portfolios


def predictions(history):
    records=[]
    for name in ('RandomModel','GapLogistic'):
        for target in range(4,12):
            records.append(dict(model=name,target_draw=target,ranking=json.dumps(list(range(1,46))),
                                scores=json.dumps({n:1. for n in range(1,46)}),
                                actual=json.dumps([1,2,3,4,5,6]),training_cutoff=3,feature_cutoff=target-1))
    return pd.DataFrame(records)


def test_candidates_and_paired_uncertainty(history):
    rows,summary=candidate_reports(predictions(history),simulations=20,bootstraps=30)
    assert len(rows)==80 and len(summary)==10
    assert summary.ge5_rate.eq(1).all()
    assert summary.ge5_ci_high.eq(1).all()
    assert (summary.ge5_exact_random < 1).all()
    assert summary.delta_ge5_vs_random.eq(0).all()
    assert summary[summary.pool_size==8].possible_six_number_tickets.eq(28).all()
    assert paired_difference(np.zeros(20),seed=42,replicates=50)==(0.,0.,0.)


def test_portfolio_equal_budgets_and_post_evaluation(history):
    rows,events=evaluate_portfolios(history,predictions(history),pool_size=8,repeats=1,budgets=(1,5,10,20))
    assert rows.groupby(['model','method','budget']).size().eq(8).all()
    assert set(rows.budget)=={1,5,10,20}
    assert rows.tickets_generated.eq(rows.budget).all()
    assert set(rows.model)=={'RandomModel','GapLogistic','Uniform45'}
    summary,replicates=portfolio_reports(rows,bootstraps=30)
    assert not summary.empty and not replicates.empty
    assert summary.targets.eq(8).all()
    assert summary.query("model=='RandomModel'").paired_delta_best.eq(0).all()
    assert (replicates.prize1_draw_ci_high>0).all()
    assert (replicates.prize2_draw_ci_high>0).all()
    assert (replicates.prize3_draw_ci_high>0).all()


def test_portfolio_rejects_sealed_and_invalid_budgets(history):
    pred=predictions(history)
    pred.loc[0,'target_draw']=1245
    with pytest.raises(ValueError,match='sealed'): evaluate_portfolios(history,pred)
    with pytest.raises(ValueError): evaluate_portfolios(history,predictions(history),budgets=(1,1))


def test_construction_is_independent_of_target_outcomes(history,monkeypatch):
    import src.backtest.prize_experiment as module
    original=module.make_portfolio
    constructed=[]
    def spy(*args,**kwargs):
        tickets=original(*args,**kwargs)
        constructed.append(tickets)
        return tickets
    monkeypatch.setattr(module,'make_portfolio',spy)
    first,_=evaluate_portfolios(history,predictions(history),repeats=1,budgets=(1,5))
    before=list(constructed)
    constructed.clear()
    changed=history.copy()
    changed[[f'num{i}' for i in range(1,7)]]=[20,21,22,23,24,25]
    changed['bonus']=44
    second,_=evaluate_portfolios(changed,predictions(history),repeats=1,budgets=(1,5))
    assert before==constructed
    assert not first.best_match.equals(second.best_match)
