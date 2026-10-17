import pytest
from src.backtest.number_space_tickets import range_portfolio,evaluate_portfolios
from src.backtest.portfolios import uniform_portfolio
import numpy as np


def test_range_coverage_has_fixed_unique_budgets_and_reproducible_prefixes():
    scores={n:1/n for n in range(1,46)};pool=list(range(1,16));zones=[(1,5),(10,13)]
    a=range_portfolio(scores,pool,zones,budget=20,seed=42)
    assert len(a)==20 and len(set(map(tuple,a)))==20
    assert all(len(t)==6 and len(set(t))==6 and set(t)<=set(pool) for t in a)
    for b in (1,5,10,20):
        assert range_portfolio(scores,pool,zones,budget=b,seed=42)==a[:b]
        assert len(uniform_portfolio(b,seed=42))==b
    with pytest.raises(ValueError):range_portfolio(scores,pool,zones,budget=0)


def test_changing_target_result_cannot_change_any_generated_portfolio(history,tmp_path):
    import json
    import pandas as pd
    from test_features import extend
    data=extend(history,120)
    models=['Frequency26','GapLogistic','NeighborhoodModel','RangeDensityModel','GapNeighborhoodModel']
    records=pd.DataFrame([dict(model=name,target_draw=120,ranking=json.dumps(list(range(1,46))),scores=json.dumps({n:1/n for n in range(1,46)})) for name in models])
    selection=dict(range=dict(window=26,width=5))
    for label,frame in [('a',data),('b',data.copy())]:
        if label=='b':
            frame.loc[frame.index[-1],[f'num{i}' for i in range(1,7)]]=[30,31,32,33,34,35]
            frame.loc[frame.index[-1],'bonus']=36
        p=tmp_path/label;p.mkdir()
        evaluate_portfolios(frame,records,p,selection=selection,development_end=119,bootstraps=20)
    a=pd.read_csv(tmp_path/'a/portfolio_audit.csv');b=pd.read_csv(tmp_path/'b/portfolio_audit.csv')
    assert a.tickets.tolist()==b.tickets.tolist() and a.budget.tolist()==b.budget.tolist()
