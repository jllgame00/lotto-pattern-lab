"""Evidence ledger integrity and deterministic, descriptive document generation."""
import copy
import hashlib
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
    assert status['H17'] == 'NO_ENSEMBLE_ADVANTAGE_ESTABLISHED'
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
    with pytest.raises(ValueError, match='historical provenance'):
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


def prior_ledger(data):
    """Reconstruct the unchanged ledger preceding the Phase 27 annotation."""
    prior = copy.deepcopy(data)
    prior.pop('phase27')
    for i, hypothesis in enumerate(prior['hypotheses']):
        if hypothesis['id'] == 'H17':
            prior['hypotheses'][i] = hypothesis['history'][0]
    for candidate in prior['candidates']:
        for field in list(candidate):
            if field.startswith('h17_'):
                candidate.pop(field)
    return prior


def test_phase27_preserves_complete_prior_ledger_and_negative_freeze():
    data = ledger()
    phase = data['phase27']
    h17 = next(h for h in data['hypotheses'] if h['id'] == 'H17')
    assert h17['history'][0]['status'] == 'BACKLOG'
    assert phase['status'] == h17['status'] == 'NO_ENSEMBLE_ADVANTAGE_ESTABLISHED'
    assert phase['validation_passed'] is False
    assert phase['ready_for_1247'] is False
    assert phase['selected']['id'] == 'equal_all'
    assert phase['selected']['weights'] == [.25, .25, .25, .25]
    assert phase['final']['targets'] == [1131, 1245]
    assert phase['final']['avg_top6'] == pytest.approx(.7652173913043478)
    assert phase['final']['mean_winning_rank'] == pytest.approx(23.417391304347827)
    encoded = json.dumps(prior_ledger(data), sort_keys=True, ensure_ascii=False, allow_nan=False).encode('utf-8')
    assert hashlib.sha256(encoded).hexdigest() == phase['prior_ledger_sha256']
    assert phase['prior_ledger_sha256'] == '55ec96e99f405c7bea7bae8a20797722d0089f76f9a1845757159fb49c23c529'
    assert all(c['h17_status'] == 'AUDIT_ONLY' for c in data['candidates'])
    assert {c['id'] for c in data['candidates'] if c['h17_eligible']} == {
        'GapLogistic', 'GraphStructure', 'GapShape', 'Mirror'}
    mi = next(c for c in data['candidates'] if c['id'] == 'MI')
    assert mi['ensemble_status'] == 'NOT CURRENTLY JUSTIFIED'
    assert mi['h17_eligible'] is False


@pytest.mark.parametrize('mutation', ['ready', 'positive_status', 'candidate_promotion',
                                    'mi_eligibility', 'erase_history', 'old_status', 'old_metric'])
def test_negative_freeze_cannot_silently_promote_or_rewrite_history(mutation):
    data = ledger()
    h17 = next(h for h in data['hypotheses'] if h['id'] == 'H17')
    if mutation == 'ready':
        data['phase27']['ready_for_1247'] = True
    elif mutation == 'positive_status':
        data['phase27']['status'] = 'HISTORICAL_ENSEMBLE_ADVANTAGE'
        h17['status'] = 'HISTORICAL_ENSEMBLE_ADVANTAGE'
    elif mutation == 'candidate_promotion':
        data['candidates'][1]['h17_status'] = 'VALIDATED_ENSEMBLE'
    elif mutation == 'mi_eligibility':
        next(c for c in data['candidates'] if c['id'] == 'MI')['h17_eligible'] = True
    elif mutation == 'erase_history':
        h17['history'] = []
    elif mutation == 'old_status':
        data['candidates'][1]['ensemble_status'] = 'VALIDATED_ENSEMBLE'
    else:
        data['candidates'][1]['avg_top6'] = 1.2
    with pytest.raises(ValueError):
        api().validate_ledger(data, ROOT)


def test_phase27_renderer_replaces_current_backlog_claim_but_retains_history():
    data = ledger()
    outputs = api().render_documents(data)
    for text in outputs.values():
        assert 'NO_ENSEMBLE_ADVANTAGE_ESTABLISHED' in text
        assert 'ready_for_1247=false' in text
        assert 'final-ensemble-analysis.md' in text
        assert 'final-ensemble-results.md' in text
        assert 'H17 최종 ensemble은 BACKLOG다' not in text
        assert 'H17은 검증된 최종 조합을 아직 만들지 않은 BACKLOG다' not in text
    assert 'BACKLOG' in outputs['research-evidence-synthesis.md']
    # The renderer remains usable for the preserved pre-Phase27 ledger.
    old_outputs = api().render_documents(prior_ledger(data))
    assert 'H17 최종 ensemble은 BACKLOG다' in old_outputs['weak-signal-candidates.md']
    assert 'NO_ENSEMBLE_ADVANTAGE_ESTABLISHED' not in old_outputs['research-evidence-synthesis.md']
