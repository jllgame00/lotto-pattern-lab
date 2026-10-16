"""Offline evaluation of an integrity-verified freeze and explicit result input."""
import json
from pathlib import Path
from src.freeze_artifacts import verify_freeze,digest
from src.backtest.prizes import pool_metrics,classify_prize
from src.backtest.ranking import rank_metrics
from src.models.base import validate_ticket


def evaluate_freeze(snapshot,result_file):
    payload=verify_freeze(snapshot)
    result=json.loads(Path(result_file).read_text(encoding='utf-8'))
    if type(result.get('draw_no')) is not int or result['draw_no']!=payload['target_draw']:
        raise ValueError('Result target does not match frozen target')
    actual=set(validate_ticket(result['main_numbers'])); bonus=result['bonus']
    classify_prize(list(actual),actual,bonus)  # validates separate bonus before evaluation
    control=payload['models']['UniformRandom']
    control_direct=classify_prize(control['direct_top6'],actual,bonus)
    control_best={b:max(classify_prize(t,actual,bonus)['main_matches'] for t in tickets)
                  for b,tickets in control['portfolios']['uniform'].items()}
    models={}
    for name,model in payload['models'].items():
        counts=pool_metrics(model['ranking'],actual)
        direct=classify_prize(model['direct_top6'],actual,bonus)
        ranking=rank_metrics(model['ranking'],actual)
        report=dict(top6_hits=ranking['hits'],mean_winning_rank=ranking['mean_winning_rank'],
            recall_6=ranking['recall_6'],recall_10=ranking['recall_10'],recall_15=ranking['recall_15'],
            pools={str(k):dict(winners=v,**{f'ge{m}':v>=m for m in (3,4,5,6)}) for k,v in counts.items()},
            direct_top6=direct,delta_top6_vs_uniform=direct['main_matches']-control_direct['main_matches'],portfolios={})
        for method,budgets in model['portfolios'].items():
            report['portfolios'][method]={}
            for budget,tickets in budgets.items():
                outcomes=[dict(ticket=t,**classify_prize(t,actual,bonus)) for t in tickets]
                best=max(outcome['main_matches'] for outcome in outcomes)
                report['portfolios'][method][budget]=dict(tickets=len(tickets),best_main_matches=best,
                    delta_best_vs_uniform=best-control_best[budget],draw_ge4=best>=4,draw_ge5=best>=5,
                    prize_counts={str(p):sum(o['prize']==p for o in outcomes) for p in range(6)},ticket_outcomes=outcomes)
        models[name]=report
    return dict(experiment_id=payload['experiment_id'],target_draw=payload['target_draw'],training_cutoff=payload['training_cutoff'],
        evaluation_status='EVALUATED_FROM_EXPLICIT_LOCAL_INPUT',snapshot_sha256=digest(snapshot),
        result_sha256=digest(result_file),result=result,models=models,
        warning='One prospective draw cannot establish predictive advantage. Original freeze and registry are unchanged.')
