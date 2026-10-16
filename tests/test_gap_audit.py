import numpy as np
import pandas as pd
import pytest

from src.models.gap_research import GapHeuristic, coefficient_audit, ranking_contributions, GAP_DEFINITIONS
from src.models.predictive import LogisticModel, rank_numbers
from src.analysis.features import GAP


@pytest.fixture
def gap_rows():
    return pd.DataFrame([dict(target_draw=t,feature_cutoff=t-1,number=n,
                             current_gap=n-1,has_appeared=1,mean_gap=7.5,median_gap=7,
                             gap_std=2.,gap_ratio=(n-1)/7.5,appeared_next=int(n<=6))
                         for t in range(105,110) for n in range(1,46)])


def current(rows):
    result=rows.tail(45).drop(columns='appeared_next').copy()
    result['target_draw'],result['feature_cutoff']=110,109
    return result


@pytest.mark.parametrize('method,best',[('largest',45),('smallest',1),('ratio',45),('zscore',45),('mean_reversion',7)])
def test_gap_rules(gap_rows,method,best):
    model=GapHeuristic(method=method).fit(gap_rows,cutoff=109)
    scores=model.score_rows(current(gap_rows))
    assert rank_numbers(scores)[0]==best
    with pytest.raises(ValueError): model.score_rows(gap_rows.tail(45))


def test_coefficient_audit_reconstructs_logit(gap_rows):
    model=LogisticModel(columns=GAP).fit(gap_rows,cutoff=109)
    audit=pd.DataFrame(coefficient_audit(model))
    assert audit.feature.tolist()==GAP
    assert audit.training_cutoff.eq(109).all()
    assert set(audit.definition)==set(GAP_DEFINITIONS.values())
    x=current(gap_rows)[GAP].to_numpy()
    logit=((x-audit.scaling_mean.to_numpy())/audit.scaling_std.to_numpy())@audit.coefficient.to_numpy()+audit.intercept.iloc[0]
    scores=model.score_rows(current(gap_rows))
    np.testing.assert_allclose(1/(1+np.exp(-logit)),list(scores.values()))
    assert (audit.coefficient.abs()==audit.magnitude).all()
    terms=ranking_contributions(model,current(gap_rows))
    assert len(terms)==6 and all(row['target_draw']==110 for row in terms)
    assert next(row for row in terms if row['feature']=='has_appeared')['cross_number_std']==0
