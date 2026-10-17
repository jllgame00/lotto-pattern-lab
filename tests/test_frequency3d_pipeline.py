def test_complete_short_history_pipeline_handles_no_rolling_windows(history,tmp_path):
    from test_features import extend
    from src.frequency_cli import analyze
    meta=analyze(extend(history,120),tmp_path/'frequency_reports',replicates=1,progress=None)
    assert not meta['future_result_accessed'] and meta['cutoff']==120
    assert meta['search_space']['conditional']==175708
    assert (tmp_path/'frequency_reports/plots/W26_state_raster.png').is_file()
    assert (tmp_path/'frequency_reports/plots/hot_cold_direction.png').is_file()
    assert (tmp_path/'frequency_reports/global_null_comparison.csv').is_file()
