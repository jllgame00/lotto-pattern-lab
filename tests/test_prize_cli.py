import json
import pandas as pd

from src.cli import main
from test_features import extend


def test_small_prize_cli(history,tmp_path,capsys):
    path=tmp_path/'input.csv'
    extend(history,110).to_csv(path,index=False)
    root=tmp_path/'prize'
    assert main(['--data',str(path),'prize-eval','--starts','107','--primary-start','107','--end','109',
                 '--reports-dir',str(root),'--core-only','--repeats','1','--bootstraps','20','--simulations','20'])==0
    metadata=json.loads((root/'experiment.json').read_text())
    assert metadata['sealed_from']==1245
    assert metadata['source_last_draw']==110
    assert metadata['configuration']['end']==109
    audit=pd.read_csv(root/'coefficient_audit.csv')
    assert {'scaling_mean','scaling_std','coefficient','sign','definition'}<=set(audit)
    assert pd.read_csv(root/'portfolio_summary.csv').targets.eq(3).all()
    assert 'exploratory' in capsys.readouterr().out.lower()
