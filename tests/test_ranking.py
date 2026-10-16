import json

import numpy as np
import pandas as pd
import pytest

from src.backtest.ranking import evaluate, summarize_rankings, rank_metrics


def test_rank_metrics():
    result=rank_metrics(list(range(1,46)),{1,2,3,4,10,45})
    assert result['hits']==4
    assert result['recall_6']==4/6 and result['recall_10']==5/6 and result['recall_15']==5/6
    assert result['mean_winning_rank']==pytest.approx(65/6)


def test_cadence_cutoffs_and_no_labels(history):
    fits=[]
    predictions=[]
    class Spy:
        def fit(self,rows,*,cutoff):
            assert rows.target_draw.max()==cutoff
            fits.append(cutoff)
            self.training_cutoff=cutoff
            return self
        def score_rows(self,rows):
            assert 'appeared_next' not in rows
            assert rows.target_draw.iloc[0]>self.training_cutoff
            predictions.append(rows.target_draw.iloc[0])
            return {n:float(n) for n in range(1,46)}
        def configuration(self): return {'seed':42}
        def importance(self): return []
    features=pd.DataFrame([dict(target_draw=t,feature_cutoff=t-1,number=n,
                                appeared_next=int(n<=6)) for t in range(2,13) for n in range(1,46)])
    results,importance=evaluate(history,features,{'Spy':Spy},start=5,end=11,cadence=3,seed=42)
    assert fits==[4,7,10]
    spy=results.query("model=='Spy'")
    assert spy.training_cutoff.tolist()==[4,4,4,7,7,7,10]
    row=spy.iloc[0]
    assert len(json.loads(row.scores))==45
    assert json.loads(row.top6)==[45,44,43,42,41,40]
    assert row.feature_cutoff==4
    assert row.actual=='[7, 8, 9, 10, 11, 12]'
    assert spy.feature_cutoff.eq(spy.target_draw-1).all()
    assert set(results.model)=={'RandomModel','Spy'}
    assert importance.empty
    with pytest.raises(ValueError): evaluate(history,features,{'Spy':Spy},start=5,end=12)


def test_random_simulations_and_paired_summary(history):
    features=pd.DataFrame([dict(target_draw=t,feature_cutoff=t-1,number=n,
                                appeared_next=int(n<=6)) for t in range(2,13) for n in range(1,46)])
    results,_=evaluate(history,features,{},start=5,end=11,seed=17)
    a=summarize_rankings(results,simulations=50,bootstraps=80,seed=9,block_length=3)
    b=summarize_rankings(results,simulations=50,bootstraps=80,seed=9,block_length=3)
    pd.testing.assert_frame_equal(a['comparison'],b['comparison'])
    row=a['comparison'].iloc[0]
    assert row.delta_vs_random==0
    assert row.paired_ci_low==row.paired_ci_high==0
    assert a['random_simulations']['theoretical_avg_hits']==.8
    assert len(a['time_blocks'])==3
    assert sum(row[f'hits_{i}'] for i in range(7))==7
