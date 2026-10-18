import numpy as np


def test_evidence_map_separates_structure_prediction_and_candidate_bookkeeping():
    from src.analysis.randomness_diagnostics import evidence_map
    ledger={'hypotheses':[dict(id=f'H{i}',status='DEFERRED' if i==7 else 'BACKLOG' if i==17 else 'TESTED / INCONCLUSIVE') for i in range(1,26)]}
    ids,values=evidence_map(ledger,'TESTED / INCONCLUSIVE')
    assert values[ids.index('H10')].tolist()==[2,0,0]
    assert values[ids.index('H12')].tolist()==[1,0,2]
    assert values[ids.index('H11')].tolist()==[0,0,0]  # MI point estimate is not a promotion.
    assert values[ids.index('H17')].tolist()==[-1,-1,-1]
