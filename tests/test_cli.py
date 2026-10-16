import json

from src.cli import main


def test_cli_import_inspect_export_and_backtest(tmp_path, history, capsys):
    incoming = tmp_path/'input.csv'
    canonical = tmp_path/'history.csv'
    history.to_csv(incoming, index=False)
    base = ['--data', str(canonical)]
    assert main(base + ['collect', '--input', str(incoming), '--source-label', 'test fixture']) == 0
    assert main(base + ['validate']) == 0
    assert main(base + ['inspect', '1']) == 0
    assert 'Current gap: 4' in capsys.readouterr().out
    exported = tmp_path/'binary.csv'
    assert main(base + ['export-series', '--output', str(exported)]) == 0
    assert exported.exists()
    report = tmp_path/'run'
    assert main(base + ['backtest', '--min-train', '3', '--tickets','2',
                       '--report', str(report)]) == 0
    summary = json.loads(report.with_suffix('.json').read_text())
    assert summary['total_tickets'] == 18
    assert summary['configuration']['seed'] == 42
    assert summary['dataset_sha256']
    assert report.with_suffix('.csv').exists()
    assert main(base + ['candidates', '--seed','7']) == 0


def test_cli_empty_state_and_errors(tmp_path, capsys):
    path = tmp_path/'missing.csv'
    assert main(['--data', str(path), 'validate']) == 1
    assert 'Error' in capsys.readouterr().err
    assert main(['--data', str(path)]) == 0
    assert 'collect' in capsys.readouterr().out


def test_cli_outputs_cannot_overwrite_inputs_or_provenance(tmp_path, history):
    path = tmp_path/'history.csv'
    history.to_csv(path, index=False)
    metadata = path.with_suffix('.metadata.json')
    metadata.write_text('{"source":"fixture"}')
    provenance = tmp_path/'sources.json'
    provenance.write_text('{"source":"fixture"}')
    before = {p: p.read_bytes() for p in (path,metadata,provenance)}
    attempts = [
        ['export-series', '--output', str(path)],
        ['export-series', '--output', str(metadata)],
        ['export-series', '--output', str(provenance)],
        ['backtest', '--min-train', '3', '--report', str(path.with_suffix(''))],
        ['backtest', '--min-train', '3', '--report', str(metadata)],
    ]
    for args in attempts:
        assert main(['--data', str(path), *args]) == 1
        assert all(p.read_bytes() == content for p,content in before.items())
