"""Evaluate frozen rankings with outcome-blind ticket construction."""
import json

import numpy as np
import pandas as pd

from src.backtest.portfolios import make_portfolio, uniform_portfolio, combination_coverage
from src.backtest.prizes import classify_prize
from src.collect.dataset import MAIN_COLUMNS, validate_history
from src.research_seal import assert_open


def evaluate_portfolios(history,predictions,*,pool_size=12,repeats=3,budgets=(1,5,10,20),seed=42,progress=None):
    assert_open(history)
    assert_open(predictions,'target_draw')
    if not budgets or tuple(sorted(set(budgets)))!=tuple(budgets) or any(type(b) is not int or b<1 for b in budgets):
        raise ValueError('Budgets must be sorted distinct positive integers')
    if type(repeats) is not int or repeats<1: raise ValueError('Repeats must be positive')
    data=validate_history(history).set_index('draw_no')
    results,events=[],[]
    groups=list(predictions.groupby('model',sort=False))
    groups.append(('Uniform45',predictions[predictions.model=='RandomModel']))
    for model,group in groups:
        for item in group.itertuples():
            if item.target_draw not in data.index: raise ValueError('Prediction target outside open history')
            ranking=json.loads(item.ranking)
            scores={int(n):v for n,v in json.loads(item.scores).items()}
            pool=ranking[:pool_size] if model!='Uniform45' else list(range(1,46))
            methods=('weighted','coverage') if model!='Uniform45' else ('uniform',)
            for method in methods:
                for repeat in range(repeats):
                    ticket_seed=int(np.random.SeedSequence([seed,int(item.target_draw),repeat,751]).generate_state(1)[0])
                    # Constructors receive NO outcomes, bonus, history, or fitted labels.
                    tickets=(uniform_portfolio(max(budgets),seed=ticket_seed) if model=='Uniform45' else
                             make_portfolio(scores,pool,budget=max(budgets),method=method,seed=ticket_seed))
                    actual=set(data.loc[item.target_draw,MAIN_COLUMNS].astype(int))
                    bonus=int(data.loc[item.target_draw,'bonus'])
                    outcomes=[classify_prize(t,actual,bonus) for t in tickets]
                    for i,(ticket,outcome) in enumerate(zip(tickets,outcomes)):
                        if outcome['main_matches']>=5:
                            events.append(dict(model=model,target_draw=item.target_draw,pool_size=len(pool),method=method,
                                               repeat=repeat,seed=ticket_seed,ticket_index=i,first_budget=next(b for b in budgets if b>i),
                                               ticket=json.dumps(ticket),actual=json.dumps(sorted(actual)),bonus=bonus,**outcome))
                    for budget in budgets:
                        selected=outcomes[:budget]
                        best=max(r['main_matches'] for r in selected)
                        results.append(dict(model=model,target_draw=item.target_draw,pool_size=len(pool),method=method,
                                            budget=budget,repeat=repeat,seed=ticket_seed,tickets_generated=budget,
                                            best_match=best,has4=int(best>=4),has5=int(best>=5),pool_winners=len(set(pool)&actual),
                                            **{f'prize{p}':sum(r['prize']==p for r in selected) for p in range(1,6)},
                                            **combination_coverage(tickets[:budget],pool)))
        if progress: progress(f'Portfolios: {model} complete')
    return pd.DataFrame(results),pd.DataFrame(events,columns=['model','target_draw','pool_size','method','repeat','seed',
                                                            'ticket_index','first_budget','ticket','actual','bonus',
                                                            'main_matches','bonus_match','prize'])
