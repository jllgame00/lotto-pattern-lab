import json
import numpy as np
import pandas as pd
from src.analysis.spatiotemporal import iid_surrogate
from src.backtest.number_space import comparison,load_selection


def test_synthetic_development_freeze_precedes_later_evaluation(tmp_path):
    x=iid_surrogate(130,seed=77);rows=[]
    for i,row in enumerate(x,1):
        nums=(np.flatnonzero(row)+1).tolist();bonus=next(n for n in range(1,46) if n not in nums)
        rows.append(dict(draw_no=i,draw_date=(pd.Timestamp('2002-12-07')+pd.Timedelta(weeks=i-1)),
            **{f'num{k}':v for k,v in enumerate(nums,1)},bonus=bonus))
    root=tmp_path/'reports';root.mkdir()
    comparison(pd.DataFrame(rows),root,start=110,development_end=120,cadence=26,bootstraps=20,progress=None,portfolios=True)
    s=load_selection(root/'selected_configuration.json')
    assert s['development_end']==120 and s['later_start']==121
    audit=pd.read_csv(root/'walk_forward_26/prediction_audit.csv')
    assert (audit.feature_cutoff==audit.target_draw-1).all()
    assert (audit.training_cutoff<audit.target_draw).all()
    assert set(audit[audit.model=='GapNeighborhoodModel'].target_draw)==set(range(110,131))
    assert (root/'walk_forward_26/later_comparison.csv').is_file()
    protocol=json.loads((root/'walk_forward_26/protocol.json').read_text())
    assert len(protocol['input_data_hash'])==64
    paired=pd.read_csv(root/'walk_forward_26/paired.csv')
    assert {'pool_6','pool_8','pool_10','pool_12','pool_15'}<=set(paired.metric)
    tickets=pd.read_csv(root/'walk_forward_26/portfolio_audit.csv')
    assert (tickets.groupby(['target_draw','budget']).size()==7).all()
    for row in tickets.itertuples():
        portfolio=json.loads(row.tickets)
        assert len(portfolio)==row.budget and len(set(map(tuple,portfolio)))==row.budget
    before=(root/'selected_configuration.json').read_bytes()
    comparison(pd.DataFrame(rows),root,start=110,development_end=120,cadence=13,bootstraps=20,progress=None,portfolios=False)
    assert before==(root/'selected_configuration.json').read_bytes()
