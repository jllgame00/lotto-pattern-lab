import math

import pytest

from src.backtest.prizes import classify_prize, pool_metrics, exact_pool_distribution
from src.backtest.portfolios import make_portfolio, combination_coverage, uniform_portfolio
from src.backtest.prizes import exact_uniform_portfolio


@pytest.mark.parametrize('ticket,prize',[
    ([1,2,3,4,5,6],1),([1,2,3,4,5,7],2),([1,2,3,4,5,8],3),
    ([1,2,3,4,8,9],4),([1,2,3,8,9,10],5),([1,2,8,9,10,11],0)])
def test_prize_classification(ticket,prize):
    assert classify_prize(ticket,{1,2,3,4,5,6},7)['prize']==prize


def test_pool_counts_and_exact_expectation():
    result=pool_metrics(list(range(1,46)),{1,2,3,4,10,45})
    assert result[6]==4 and result[8]==4 and result[10]==5 and result[15]==5
    for k in (6,8,10,12,15):
        dist=exact_pool_distribution(k)
        assert sum(dist)==pytest.approx(1)
        assert sum(i*p for i,p in enumerate(dist))==pytest.approx(6*k/45)
        assert dist[6]==pytest.approx(math.comb(k,6)/math.comb(45,6))
    with pytest.raises(ValueError): pool_metrics([1]*45,{1,2,3,4,5,6})


@pytest.mark.parametrize('method',['weighted','coverage'])
def test_portfolios_unique_budget_and_determinism(method):
    scores={n:float(n) for n in range(1,46)}
    pool=list(range(34,46))
    a=make_portfolio(scores,pool,budget=20,method=method,seed=7)
    assert a==make_portfolio(scores,pool,budget=20,method=method,seed=7)
    assert a[:5]==make_portfolio(scores,pool,budget=5,method=method,seed=7)
    assert len(a)==len(set(map(tuple,a)))==20
    assert all(len(set(t))==6 and set(t)<=set(pool) for t in a)
    coverage=combination_coverage(a,pool)
    assert coverage['possible_tickets']==924
    assert coverage['six_subset_fraction']==pytest.approx(20/924)
    assert 6<=coverage['covered_five_subsets']<=120
    if method=='coverage': assert coverage['covered_five_subsets']==120


def test_impossible_budget_and_uniform_baseline():
    with pytest.raises(ValueError): make_portfolio({n:1. for n in range(1,46)},list(range(1,7)),budget=5)
    tickets=uniform_portfolio(20,seed=2)
    assert len(set(map(tuple,tickets)))==20
    assert tickets[:5]==uniform_portfolio(5,seed=2)
    with pytest.raises(ValueError): classify_prize([1]*6,{1,2,3,4,5,6},7)
    with pytest.raises(ValueError): classify_prize([1,2,3,4,5,6],{1,2,3,4,5,6},6)


def test_exact_uniform_portfolio():
    one=exact_uniform_portfolio(1)
    many=exact_uniform_portfolio(20)
    assert one['mean_best_match']==pytest.approx(.8)
    assert sum(one['best_match_distribution'])==pytest.approx(1)
    assert one['prize2_draw_probability']==pytest.approx(6/math.comb(45,6))
    assert many['mean_best_match']>one['mean_best_match']
    assert many['ge5_draw_probability']<20*one['ge5_draw_probability']
    assert many['ge5_draw_probability']>one['ge5_draw_probability']
