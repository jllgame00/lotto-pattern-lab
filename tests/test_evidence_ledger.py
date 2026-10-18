"""Evidence ledger integrity and deterministic, descriptive document generation."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'src/analysis/evidence_ledger.py'


def api():
    assert MODULE.is_file(), 'Evidence ledger validation/generation module is required'
    spec = importlib.util.spec_from_file_location('evidence_ledger', MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ledger():
    return json.loads((ROOT / 'docs/weak-signal-candidates.json').read_text(encoding='utf-8'))


def test_canonical_ledger_covers_completed_and_deferred_hypotheses():
    data = ledger()
    api().validate_ledger(data, ROOT)
    assert {h['id'] for h in data['hypotheses']} == {f'H{i}' for i in range(1, 26)}
    status = {h['id']: h['status'] for h in data['hypotheses']}
    assert status['H7'] == 'DEFERRED'
    assert status['H17'] == 'BACKLOG'
    assert all(status[f'H{i}'] == 'TESTED / INCONCLUSIVE'
               for i in range(1, 25) if i not in (7, 17))
    assert data['statistical_combination'] is False


def test_generation_matches_checked_in_views_without_rewriting():
    module = api()
    outputs = module.render_documents(ledger())
    assert set(outputs) == {'research-evidence-synthesis.md', 'weak-signal-candidates.md'}
    for name, text in outputs.items():
        assert text == (ROOT / 'docs' / name).read_text(encoding='utf-8')
    assert outputs == module.render_documents(ledger())


def test_rejects_duplicate_hypothesis():
    data = ledger()
    data['hypotheses'].append(copy.deepcopy(data['hypotheses'][0]))
    with pytest.raises(ValueError, match='hypothesis'):
        api().validate_ledger(data, ROOT)


def test_rejects_missing_reference_marked_available(tmp_path):
    data = ledger()
    with pytest.raises(ValueError, match='AVAILABLE'):
        api().validate_ledger(data, tmp_path)


def test_rejects_path_escape():
    data = ledger()
    data['candidates'][0]['artifacts'][0]['path'] = '../outside.json'
    with pytest.raises(ValueError, match='relative'):
        api().validate_ledger(data, ROOT)


def test_rejects_unordered_paired_interval():
    data = ledger()
    data['candidates'][0]['paired_intervals'][0]['ci95'] = [1, -1]
    with pytest.raises(ValueError, match='interval'):
        api().validate_ledger(data, ROOT)


def test_missing_metrics_remain_explicit_and_mi_is_not_promoted():
    data = ledger()
    module = api()
    mi = next(c for c in data['candidates'] if c['id'] == 'MI')
    assert mi['ensemble_status'] == 'NOT CURRENTLY JUSTIFIED'
    assert mi['avg_top6'] > .8
    # A positive point estimate or diverse ranks cannot silently alter a decision.
    changed = copy.deepcopy(data)
    candidate = next(c for c in changed['candidates'] if c['id'] == 'MI')
    candidate['avg_top6'] = 1.1
    module.validate_ledger(changed, ROOT)
    assert 'NOT CURRENTLY JUSTIFIED' in module.render_documents(changed)['weak-signal-candidates.md']
    assert any(a['availability'] == 'HISTORICAL_UNAVAILABLE'
               for c in data['candidates'] for a in c['artifacts'])


def test_rejects_claimed_combined_p_value():
    data = ledger()
    data['statistical_combination'] = True
    with pytest.raises(ValueError, match='descriptive'):
        api().validate_ledger(data, ROOT)


def test_rejects_lossy_unicode_transcription():
    data = ledger()
    data['candidates'][0]['robustness'] = '?? encoding loss'
    with pytest.raises(ValueError, match='Unicode'):
        api().validate_ledger(data, ROOT)


def test_rejects_impossible_rank_overlap():
    data = ledger()
    data['candidates'][0]['rank_diversity_metrics'] = [
        {'reference': 'Example', 'spearman': 0, 'top6_overlap': 7,
         'top10_overlap': 2, 'top15_overlap': 5}]
    with pytest.raises(ValueError, match='rank diversity'):
        api().validate_ledger(data, ROOT)
