"""Outcome-blind fixed-budget unique tickets, separate from ranking."""
from functools import lru_cache
from itertools import combinations
from math import comb

import numpy as np

from src.models.predictive import _scores


@lru_cache(maxsize=10)
def _structure(k):
    tickets=np.array(list(combinations(range(k),6)),dtype=int)
    five_index={s:i for i,s in enumerate(combinations(range(k),5))}
    pair_index={s:i for i,s in enumerate(combinations(range(k),2))}
    fives=np.array([[five_index[s] for s in combinations(t,5)] for t in tickets])
    pairs=np.array([[pair_index[s] for s in combinations(t,2)] for t in tickets])
    return tickets,fives,pairs


def make_portfolio(scores,pool,*,budget=20,method='weighted',seed=42):
    _scores(scores)
    pool=sorted(pool)
    k=len(pool)
    if k<6 or k>15 or len(set(pool))!=k or not set(pool)<=set(range(1,46)):
        raise ValueError('Candidate pool must have6..15 distinct numbers in1..45')
    if type(budget) is not int or budget<1 or budget>comb(k,6):
        raise ValueError('Budget exceeds available unique tickets or is not positive')
    if method not in ('weighted','coverage'): raise ValueError('Unknown portfolio method')
    tickets,fives,pairs=_structure(k)
    values=np.array([scores[n] for n in pool],dtype=float)
    values-=min(0.,values.min())  # documented shift for negative heuristic scores
    values=values/values.max() if values.max()>0 else np.ones(k)
    probabilities=.999*values/values.sum()+.001/k
    log_weights=np.log(probabilities)[tickets].sum(axis=1)
    rng=np.random.default_rng(seed)
    # Gumbel ordering = weighted sampling without replacement over combinations.
    priority=log_weights+rng.gumbel(size=len(tickets))
    if method=='weighted':
        order=np.argsort(-priority,kind='stable')[:budget]
    else:
        covered5=np.zeros(comb(k,5),dtype=bool)
        covered2=np.zeros(comb(k,2),dtype=bool)
        used=np.zeros(len(tickets),dtype=bool)
        order=[]
        for _ in range(budget):
            new5=(~covered5[fives]).sum(axis=1)
            new2=(~covered2[pairs]).sum(axis=1)
            new5[used]=-1
            choice=int(np.lexsort((priority,new2,new5))[-1])
            order.append(choice)
            used[choice]=True
            covered5[fives[choice]]=True
            covered2[pairs[choice]]=True
    return [[pool[i] for i in tickets[index]] for index in order]


def uniform_portfolio(budget,*,seed=42):
    if type(budget) is not int or not 1<=budget<=10000: raise ValueError('Uniform budget must be1..10000')
    rng=np.random.default_rng(seed)
    tickets=[]
    seen=set()
    while len(tickets)<budget:
        ticket=tuple(sorted(rng.choice(np.arange(1,46),6,replace=False).tolist()))
        if ticket not in seen:
            seen.add(ticket)
            tickets.append(list(ticket))
    return tickets


def combination_coverage(tickets,pool):
    k=len(pool)
    fives={part for ticket in tickets for part in combinations(sorted(ticket),5)}
    pairs={part for ticket in tickets for part in combinations(sorted(ticket),2)}
    return dict(possible_tickets=comb(k,6),six_subset_fraction=len(tickets)/comb(k,6),
                covered_five_subsets=len(fives),five_subset_fraction=len(fives)/comb(k,5),
                covered_pairs=len(pairs),pair_fraction=len(pairs)/comb(k,2))
