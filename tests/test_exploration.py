import json

import pandas as pd

from src.analysis.exploration import analyze_history, write_reports
from src.analysis.plots import plot_number
from src.analysis.periodicity import PeriodicityConfig
from src.cli import main
from test_temporal import long_history


def test_reports_null_scopes_and_plot(history,tmp_path):
    full=long_history(history,60)
    analysis=analyze_history(full,numbers=[1,17],windows=[26],permutations=9,seed=12)
    tables=analysis['tables']
    assert len(tables['yearly_number_stats']) == 6  # Dec 2002, 2003, Jan 2004
    assert len(tables['monthly_number_stats']) == 24
    null=tables['periodicity_null']
    assert len(null)==4
    assert set(null.scope)=={'full_history','latest_26'}
    assert (null.family_size==90).all()
    tested=null[null.status=='ok']
    assert (tested.p_bonferroni == (tested.p_value*90).clip(upper=1)).all()
    assert tables['appearance_history'].query('number == 17').empty
    paths=write_reports(analysis,tmp_path)
    assert all(p.exists() for p in paths)
    metadata=json.loads((tmp_path/'temporal_analysis.json').read_text())
    assert metadata['cutoff_draw']==60 and metadata['warnings']
    assert metadata['runtime_seconds']['total']>0
    png=plot_number(full,1,analysis,tmp_path/'plots',PeriodicityConfig())
    assert png.read_bytes().startswith(b'\x89PNG')


def test_cli_exploration_short_data_and_validation(tmp_path,history,capsys):
    path=tmp_path/'history.csv'
    history.to_csv(path,index=False)
    out=tmp_path/'analysis'
    assert main(['--data',str(path),'inspect','17','--reports-dir',str(out),'--no-plots','--permutations','0'])==0
    text=capsys.readouterr().out
    assert 'insufficient' in text.lower() and 'recurrence' in text.lower()
    assert (out/'number_17'/'temporal_analysis.json').exists()
    assert main(['--data',str(path),'analyze-all','--reports-dir',str(out),'--permutations','0'])==0
    assert len(pd.read_csv(out/'yearly_number_stats.csv'))==90
    assert main(['--data',str(path),'inspect','0','--no-plots'])==1
    assert main(['--data',str(path),'analyze-all','--max-lag','0'])==1


def test_cli_aggregate_refuses_to_overwrite_source(tmp_path,history):
    path=tmp_path/'yearly_number_stats.csv'
    history.to_csv(path,index=False)
    before=path.read_bytes()
    assert main(['--data',str(path),'analyze-all','--reports-dir',str(tmp_path),'--permutations','0'])==1
    assert path.read_bytes()==before


def test_cli_formats_nonempty_unsupported_rolling_scores(tmp_path,history,capsys):
    path=tmp_path/'history.csv'
    history.to_csv(path,index=False)
    assert main(['--data',str(path),'inspect','45','--windows','2','--no-plots','--permutations','0'])==0
    text=capsys.readouterr().out
    assert 'unavailable' in text and 'insufficient_observations' in text
