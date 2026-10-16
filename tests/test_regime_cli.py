import json
import pandas as pd
from src.cli import main
from test_features import extend


def test_hazard_cli(history,tmp_path):
    source=tmp_path/'source.csv'; extend(history,110).to_csv(source,index=False)
    output=tmp_path/'reports'
    assert main(['--data',str(source),'hazard-analysis','--reports-dir',str(output)])==0
    table=pd.read_csv(output/'hazard.csv')
    assert {'exact','gap','ratio','zscore'}==set(table.variable)


def test_regime_cli_small_causal_experiment(history,tmp_path):
    source=tmp_path/'source.csv'; extend(history,218).to_csv(source,index=False)
    output=tmp_path/'reports'
    assert main(['--data',str(source),'compare-regime-models','--start','210','--end','218',
        '--development-end','213','--hmm-iterations','2','--null-repeats','1','--repeats','1',
        '--bootstraps','20','--simulations','20','--skip-robustness','--reports-dir',str(output)])==0
    meta=json.loads((output/'experiment.json').read_text())
    assert meta['research_cutoff']==1244
    later=pd.read_csv(output/'later_audit.csv')
    assert later.target_draw.min()==214
    assert (later.training_cutoff<later.target_draw).all()
    assert (output/'portfolio_summary.csv').exists()
    assert (output/'hmm_null.csv').exists()
    assert {'Top8_5plus','Top15_6of6'}<=set(pd.read_csv(output/'comparison.csv'))
