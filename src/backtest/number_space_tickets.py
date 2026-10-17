"""Outcome-blind range-aware proposals and equal-budget post-prediction scoring."""
from math import comb
import json
import numpy as np
import pandas as pd
from src.backtest.portfolios import _structure,make_portfolio,uniform_portfolio,combination_coverage
from src.backtest.prizes import classify_prize,exact_uniform_portfolio
from src.backtest.prize_reports import paired_difference,binomial_interval
from src.analysis.number_space import recent_density,strong_zones,group_zones
from src.models.predictive import _scores
from src.analysis.spatiotemporal import lotto_matrix


def range_portfolio(scores,pool,zones,*,budget=20,seed=42):
    _scores(scores);pool=sorted(pool);k=len(pool);zones=group_zones(zones)
    if not 6<=k<=15 or len(set(pool))!=k or not set(pool)<=set(range(1,46)) or type(budget) is not int or not 1<=budget<=min(20,comb(k,6)):
        raise ValueError('Unique finite pool6..15 and budget1..20 required')
    tickets,fives,pairs=_structure(k)
    values=np.array([scores[n] for n in pool],float);values-=min(0.,values.min())
    probabilities=values/values.sum() if values.sum()>0 else np.ones(k)/k
    probabilities=.999*probabilities+.001/k
    priority=np.log(probabilities)[tickets].sum(axis=1)+np.random.default_rng(seed).gumbel(size=len(tickets))
    proposal=np.argsort(-priority,kind='stable')[:min(len(tickets),20*64)]
    memberships=np.array([[a<=n<=b for a,b in zones] for n in pool],bool).reshape(k,len(zones))
    memberships=np.column_stack((memberships,~memberships.any(axis=1)))
    represented=memberships[tickets].any(axis=1)
    covered5=np.zeros(comb(k,5),bool);covered2=np.zeros(comb(k,2),bool);covered_zones=np.zeros(represented.shape[1],bool)
    used=np.zeros(len(tickets),bool);order=[]
    for slot in range(min(20,len(tickets))):
        options=proposal[slot*64:(slot+1)*64];options=options[~used[options]]
        if not len(options):options=np.flatnonzero(~used)
        new5=(~covered5[fives[options]]).sum(axis=1);new2=(~covered2[pairs[options]]).sum(axis=1)
        newzones=(represented[options]&~covered_zones).sum(axis=1)
        best=int(options[np.lexsort((priority[options],new2,newzones,new5))[-1]])
        order.append(best);used[best]=True;covered5[fives[best]]=True;covered2[pairs[best]]=True;covered_zones|=represented[best]
    return [[pool[i] for i in tickets[index]] for index in order[:budget]]


def evaluate_portfolios(data,results,directory,*,selection,development_end=900,bootstraps=2000):
    x=lotto_matrix(data,cutoff=len(data));rows=[];events=[]
    names=['Frequency26','GapLogistic','NeighborhoodModel','RangeDensityModel','GapNeighborhoodModel']
    for target,group in results.groupby('target_draw',sort=False):
        if target>1245 or target<1:raise ValueError('Historical results only')
        past=x[:target-1]
        density=recent_density(past,target=int(target),**selection['range'])
        _,zones=strong_zones(density)
        methods=[]
        for name in names:
            record=group[group.model==name].iloc[0]
            scores={int(n):v for n,v in json.loads(record.scores).items()};pool=json.loads(record.ranking)[:15]
            methods.append((name,'weighted',make_portfolio(scores,pool,budget=20,method='weighted',seed=42+int(target)),pool))
            if name=='RangeDensityModel':methods.append((name,'range_coverage',range_portfolio(scores,pool,zones,budget=20,seed=42+int(target)),pool))
        methods.append(('Uniform45','uniform',uniform_portfolio(20,seed=42+int(target)),list(range(1,46))))
        # First outcome/bonus access happens after every portfolio is generated.
        actual=set((np.flatnonzero(x[target-1])+1).tolist());bonus=int(data.iloc[target-1].bonus)
        for name,method,tickets,pool in methods:
            classified=[classify_prize(ticket,actual,bonus) for ticket in tickets]
            for budget in (1,5,10,20):
                subset=classified[:budget];best=max(v['main_matches'] for v in subset)
                row=dict(model=name,method=method,target_draw=int(target),budget=budget,seed=42+int(target),
                    tickets=json.dumps(tickets[:budget]),best_match=best,has4=int(best>=4),has5=int(best>=5),
                    pool_winners=len(actual&set(pool)),**combination_coverage(tickets[:budget],pool))
                row.update({f'prize{prize}':sum(v['prize']==prize for v in subset) for prize in range(1,6)})
                rows.append(row)
                if row['prize1']+row['prize2']+row['prize3']:events.append(dict(row,actual=json.dumps(sorted(actual)),bonus=bonus))
    detail=pd.DataFrame(rows);detail.to_csv(directory/'portfolio_audit.csv',index=False)
    pd.DataFrame(events,columns=[*detail.columns,'actual','bonus']).to_csv(directory/'portfolio_prize_events.csv',index=False)
    summaries=[]
    for start in sorted({int(results.target_draw.min()),development_end+1}):
        d=detail[detail.target_draw>=start]
        for (name,method,budget),group in d.groupby(['model','method','budget'],sort=False):
            group=group.sort_values('target_draw');uniform=d[(d.model=='Uniform45')&(d.budget==budget)].sort_values('target_draw')
            if group.target_draw.tolist()!=uniform.target_draw.tolist():raise ValueError('Equal budgets and target sets required')
            delta,lo,hi=paired_difference(group.best_match.to_numpy()-uniform.best_match.to_numpy(),replicates=bootstraps)
            n=len(group);lower,upper=binomial_interval(int(group.has5.sum()),n)
            row=dict(model=name,method=method,budget=int(budget),evaluation_start=start,targets=n,
                mean_best_match=float(group.best_match.mean()),draws_ge4=int(group.has4.sum()),draws_ge5=int(group.has5.sum()),
                ge5_ci_low=lower,ge5_ci_high=upper,delta_best_vs_uniform=delta,paired_ci_low=lo,paired_ci_high=hi,
                mean_pool_winners=float(group.pool_winners.mean()),mean_five_subset_fraction=float(group.five_subset_fraction.mean()),
                mean_six_subset_fraction=float(group.six_subset_fraction.mean()),
                **{f'prize{p}_tickets':int(group[f'prize{p}'].sum()) for p in range(1,6)})
            if method=='range_coverage':
                reference=d[(d.model==name)&(d.method=='weighted')&(d.budget==budget)].sort_values('target_draw')
                dv,l,h=paired_difference(group.best_match.to_numpy()-reference.best_match.to_numpy(),replicates=bootstraps)
                row.update(delta_best_vs_weighted=dv,weighted_ci_low=l,weighted_ci_high=h)
            summaries.append(row)
    summary=pd.DataFrame(summaries);summary.to_csv(directory/'portfolio_comparison.csv',index=False)
    pd.DataFrame([exact_uniform_portfolio(b) for b in (1,5,10,20)]).to_csv(directory/'portfolio_exact_random.csv',index=False)
    return summary
