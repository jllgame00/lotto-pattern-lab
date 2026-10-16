"""Main-number concentration and bonus-aware POST-prediction classification."""
from math import comb
import numpy as np

from src.models.base import validate_ticket

POOL_SIZES = (6,8,10,12,15)


def pool_metrics(ranking,actual,pool_sizes=POOL_SIZES):
    if len(ranking)!=45 or set(ranking)!=set(range(1,46)):
        raise ValueError('Expected ranking of all45 numbers exactly once')
    actual=set(validate_ticket(list(actual)))
    if any(type(k) is not int or k<6 or k>45 for k in pool_sizes): raise ValueError('Invalid pool size')
    return {k:len(set(ranking[:k]) & actual) for k in pool_sizes}


def exact_pool_distribution(k):
    if type(k) is not int or not 6<=k<=45: raise ValueError('Pool size must be6..45')
    return [comb(6,j)*comb(39,k-j)/comb(45,k) if 0<=k-j<=39 else 0. for j in range(7)]


def classify_prize(ticket,actual,bonus):
    ticket=set(validate_ticket(ticket))
    actual=set(validate_ticket(list(actual)))
    if type(bonus) is not int or not 1<=bonus<=45 or bonus in actual:
        raise ValueError('Bonus must be a separate integer in1..45')
    matches=len(ticket & actual)
    bonus_match=bonus in ticket
    prize=1 if matches==6 else (2 if bonus_match else 3) if matches==5 else 4 if matches==4 else 5 if matches==3 else 0
    return dict(main_matches=matches,bonus_match=bonus_match,prize=prize)


def exact_ticket_prizes():
    denominator=comb(45,6)
    return {1:1/denominator,2:6/denominator,3:6*38/denominator,
            4:comb(6,4)*comb(39,2)/denominator,5:comb(6,3)*comb(39,3)/denominator}


def exact_uniform_portfolio(budget):
    """Exact law for B distinct uniformly sampled tickets from all C(45,6).

    For F favorable combinations, P(any)=1-product(1-F/(M-i)), i=0..B-1.
    This integrates random ticket construction. It is not the null law for an
    arbitrary fixed or coverage-optimized portfolio with a different overlap.
    """
    if type(budget) is not int or not 1<=budget<=10000: raise ValueError('Invalid uniform budget')
    total=comb(45,6)
    denominators=total-np.arange(budget,dtype=float)
    counts=[comb(6,j)*comb(39,6-j) for j in range(7)]
    def any_event(favorable):
        return float(-np.expm1(np.log1p(-favorable/denominators).sum()))
    tails=[1.]+[any_event(sum(counts[j:])) for j in range(1,7)]+[0.]
    distribution=[tails[j]-tails[j+1] for j in range(7)]
    return dict(budget=budget,mean_best_match=sum(tails[1:7]),best_match_distribution=distribution,
                ge4_draw_probability=tails[4],ge5_draw_probability=tails[5],ge6_draw_probability=tails[6],
                prize1_draw_probability=any_event(1),prize2_draw_probability=any_event(6),
                prize3_draw_probability=any_event(6*38))
