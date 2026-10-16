"""Uncertainty and concentration reports; rare counts are never proof of skill."""
from functools import lru_cache
from math import comb
import json

import numpy as np
import pandas as pd
from scipy.stats import beta, binomtest

from src.backtest.prizes import POOL_SIZES, exact_pool_distribution, pool_metrics, exact_uniform_portfolio
from src.research_seal import assert_open


@lru_cache(maxsize=12)
def bootstrap_indices(n,replicates=2000,seed=42,block=26):
    if min(n,replicates,block)<1: raise ValueError('Positive sample/bootstrap/block sizes required')
    length=min(block,n)
    starts=np.random.default_rng(seed).integers(0,n,size=(replicates,int(np.ceil(n/length))))
    return ((starts[:,:,None]+np.arange(length))%n).reshape(replicates,-1)[:,:n]


def paired_difference(differences,*,seed=42,replicates=2000,block=26):
    values=np.asarray(differences,dtype=float)
    if values.ndim!=1 or not np.isfinite(values).all(): raise ValueError('Finite paired differences required')
    low,high=np.quantile(values[bootstrap_indices(len(values),replicates,seed,block)].mean(axis=1),[.025,.975])
    return float(values.mean()),float(low),float(high)


def binomial_interval(events,n):
    """Clopper-Pearson iid-Bernoulli descriptive interval, including zero counts."""
    return (float(beta.ppf(.025,events,n-events+1)) if events else 0.,
            float(beta.ppf(.975,events+1,n-events)) if events<n else 1.)


def random_portfolio_reference(targets,*,simulations=2000,seed=42):
    rows=[]
    for budget in (1,5,10,20):
        exact=exact_uniform_portfolio(budget)
        distribution=exact.pop('best_match_distribution')
        rng=np.random.default_rng(np.random.SeedSequence([seed,budget,452]))
        counts=rng.multinomial(targets,distribution,size=simulations)
        means=counts@np.arange(7)/targets
        ge5=counts[:,5:].sum(axis=1)
        rows.append(dict(targets=targets,simulations=simulations,seed=seed,**exact,
                         expected_ge5_draws=targets*exact['ge5_draw_probability'],
                         mc_mean_best=float(means.mean()),mc_mean_best95_low=float(np.quantile(means,.025)),
                         mc_mean_best95_high=float(np.quantile(means,.975)),
                         mc_ge5_draws95_low=float(np.quantile(ge5,.025)),mc_ge5_draws95_high=float(np.quantile(ge5,.975))))
    return pd.DataFrame(rows)


def candidate_reports(predictions,*,simulations=2000,bootstraps=2000,seed=42):
    assert_open(predictions,'target_draw')
    if simulations<1: raise ValueError('simulations must be positive')
    records=[]
    for row in predictions.itertuples():
        counts=pool_metrics(json.loads(row.ranking),set(json.loads(row.actual)))
        records.extend(dict(model=row.model,target_draw=row.target_draw,pool_size=k,winners=v) for k,v in counts.items())
    detail=pd.DataFrame(records)
    references={}
    summary=[]
    for (model,k),group in detail.groupby(['model','pool_size'],sort=False):
        group=group.sort_values('target_draw')
        random=detail[(detail.model=='RandomModel')&(detail.pool_size==k)].sort_values('target_draw')
        if group.target_draw.tolist()!=random.target_draw.tolist(): raise ValueError('Candidate target sets must match')
        n=len(group)
        counts=group.winners.to_numpy()
        dist=exact_pool_distribution(int(k))
        if k not in references:
            simulated=np.random.default_rng(np.random.SeedSequence([seed,int(k),91])).hypergeometric(6,39,int(k),size=(simulations,n))
            references[k]={m:(float((simulated>=m).mean()),np.quantile((simulated>=m).mean(axis=1),[.025,.975])) for m in (5,6)}
        row=dict(model=model,pool_size=k,targets=n,mean_pool_winners=float(counts.mean()),
                 possible_six_number_tickets=comb(int(k),6),possible_five_subsets=comb(int(k),5),
                 expected_ge5_events=n*sum(dist[5:]),expected_ge6_events=n*dist[6])
        row.update({f'winners_{j}':int((counts==j).sum()) for j in range(7)})
        for minimum in (3,4,5,6):
            events=int((counts>=minimum).sum())
            low,high=binomial_interval(events,n)
            row.update({f'ge{minimum}_events':events,f'ge{minimum}_rate':events/n,
                        f'ge{minimum}_ci_low':low,f'ge{minimum}_ci_high':high,
                        f'ge{minimum}_exact_random':sum(dist[minimum:])})
            if minimum>=5:
                delta,lower,upper=paired_difference((counts>=minimum).astype(float)-(random.winners.to_numpy()>=minimum),seed=seed,replicates=bootstraps)
                mc,interval=references[k][minimum]
                row.update({f'delta_ge{minimum}_vs_random':delta,f'delta_ge{minimum}_ci_low':lower,f'delta_ge{minimum}_ci_high':upper,
                            f'ge{minimum}_p_random_null':binomtest(events,n,sum(dist[minimum:]),alternative='greater').pvalue,
                            f'ge{minimum}_mc_mean':mc,f'ge{minimum}_mc_run95_low':float(interval[0]),f'ge{minimum}_mc_run95_high':float(interval[1])})
        summary.append(row)
    result=pd.DataFrame(summary)
    # Two primary event thresholds across all prespecified model/pool choices.
    family=2*len(result)
    for minimum in (5,6):
        result[f'ge{minimum}_p_bonferroni']=np.minimum(1,result[f'ge{minimum}_p_random_null']*family)
    return detail,result


def portfolio_reports(rows,*,bootstraps=2000,seed=42):
    assert_open(rows,'target_draw')
    keys=['model','pool_size','method','budget']
    replicates=[]
    for labels,group in rows.groupby(keys+['repeat'],sort=False):
        row=dict(zip(keys+['repeat'],labels))
        row.update(targets=len(group),mean_best_match=float(group.best_match.mean()),
                   draws_ge4=int(group.has4.sum()),draws_ge5=int(group.has5.sum()),
                   pool_ge5_draws=int((group.pool_winners>=5).sum()))
        for prize in range(1,6):
            row[f'prize{prize}_tickets']=int(group[f'prize{prize}'].sum())
            row[f'prize{prize}_draws']=int((group[f'prize{prize}']>0).sum())
            row[f'prize{prize}_draw_ci_low'],row[f'prize{prize}_draw_ci_high']=binomial_interval(row[f'prize{prize}_draws'],len(group))
        row['ge5_draw_ci_low'],row['ge5_draw_ci_high']=binomial_interval(row['draws_ge5'],len(group))
        replicates.append(row)
    # Collapse replicates BEFORE resampling target draws: seeds are not new draws.
    metrics=['best_match','has4','has5','pool_winners','five_subset_fraction','six_subset_fraction']
    collapsed=rows.groupby(keys+['target_draw'],sort=False)[metrics].mean().reset_index()
    summary=[]
    for labels,group in collapsed.groupby(keys,sort=False):
        model,k,method,budget=labels
        group=group.sort_values('target_draw')
        baseline=collapsed[(collapsed.model==('Uniform45' if model=='Uniform45' else 'RandomModel'))&
                           (collapsed.pool_size==k)&(collapsed.method==method)&(collapsed.budget==budget)].sort_values('target_draw')
        uniform=collapsed[(collapsed.model=='Uniform45')&(collapsed.budget==budget)].sort_values('target_draw')
        if group.target_draw.tolist()!=baseline.target_draw.tolist(): raise ValueError('Unequal portfolio comparison budgets/targets')
        delta,low,high=paired_difference(group.best_match.to_numpy()-baseline.best_match.to_numpy(),seed=seed,replicates=bootstraps)
        d5,l5,h5=paired_difference(group.has5.to_numpy()-baseline.has5.to_numpy(),seed=seed,replicates=bootstraps)
        selection=rows[(rows.model==model)&(rows.pool_size==k)&(rows.method==method)&(rows.budget==budget)]
        row=dict(zip(keys,labels))
        row.update(targets=len(group),replicates=selection['repeat'].nunique(),mean_best_match=float(group.best_match.mean()),
                   draws_ge4_mean=float(group.has4.sum()),draws_ge5_mean=float(group.has5.sum()),
                   paired_delta_best=delta,paired_best_ci_low=low,paired_best_ci_high=high,
                   paired_delta_ge5=d5,paired_ge5_ci_low=l5,paired_ge5_ci_high=h5,
                   mean_five_subset_fraction=float(group.five_subset_fraction.mean()),
                   mean_six_subset_fraction=float(group.six_subset_fraction.mean()),
                   mean_pool_winners=float(group.pool_winners.mean()))
        if group.target_draw.tolist()==uniform.target_draw.tolist():
            du,lu,hu=paired_difference(group.best_match.to_numpy()-uniform.best_match.to_numpy(),seed=seed,replicates=bootstraps)
            row.update(delta_best_vs_uniform45=du,uniform45_ci_low=lu,uniform45_ci_high=hu)
        for prize in range(1,6):
            row[f'prize{prize}_tickets_across_repeats']=int(selection[f'prize{prize}'].sum())
        summary.append(row)
    return pd.DataFrame(summary),pd.DataFrame(replicates)
