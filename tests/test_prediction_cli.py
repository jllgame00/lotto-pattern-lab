import json

import pandas as pd

from src.cli import main
from test_features import extend


def test_compare_and_predict_cli(history,tmp_path,capsys):
    data=tmp_path/'history.csv'
    extend(history,110).to_csv(data,index=False)
    report=tmp_path/'reports'
    assert main(['--data',str(data),'compare-models','--start','107','--end','109',
                 '--models','similarity','--reports-dir',str(report),'--simulations','10','--bootstraps','10',
                 '--no-audit','--neighbors','7','--distance','cityblock'])==0
    assert (report/'comparison.csv').exists()
    metadata=json.loads((report/'experiment.json').read_text())
    config=metadata['model_configurations']['SimilarityModel[full]']
    assert config['k']==7 and config['metric']=='cityblock'
    table=pd.read_csv(report/'feature_sample.csv')
    assert table.feature_cutoff.eq(table.target_draw-1).all()
    assert main(['--data',str(data),'predict-current','--model','similarity'])==0
    assert 'Experimental' in capsys.readouterr().out


def test_explain_cli(history,tmp_path,capsys):
    data=tmp_path/'history.csv'
    extend(history,110).to_csv(data,index=False)
    assert main(['--data',str(data),'explain-number','17','--neighbors','2'])==0
    assert 'neighbors' in capsys.readouterr().out


def test_ablation_reports_ranking_uncertainty():
    from src.prediction_cli import _ablation_differences
    rows=[]
    for target in range(100,140):
        for group,increment in [('frequency_gap',0),('frequency_gap_periodicity',1)]:
            rows.append(dict(model=f'Logistic[{group}]',target_draw=target,hits=increment,
                             mean_winning_rank=23-increment,
                             recall_6=increment/6,recall_10=increment/6,recall_15=increment/6))
    row=_ablation_differences(pd.DataFrame(rows),42,30).iloc[0]
    assert row['delta_mean_winning_rank_ci_low']==row['delta_mean_winning_rank_ci_high']==-1
    assert row['delta_recall_10_ci_low']>0
