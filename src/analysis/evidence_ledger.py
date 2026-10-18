"""Validate and render an explicit descriptive research ledger, without data access.

Run ``python -m src.analysis.evidence_ledger --check`` for read-only verification;
omit --check to regenerate the two Markdown views from the canonical JSON.
No fitting, null simulation, p-value aggregation, or prospective access occurs.
"""
import argparse
import json
import math
from pathlib import Path, PurePosixPath


def validate_ledger(data, root):
    """Reject incomplete provenance and invalid metrics; never infer decisions."""
    serialized = json.dumps(data, ensure_ascii=False)
    if '\ufffd' in serialized or '??' in serialized:
        raise ValueError('Unicode transcription loss detected')
    if data.get('schema_version') != 1 or data.get('statistical_combination') is not False:
        raise ValueError('Only descriptive schema version 1 is supported')
    hypotheses = data['hypotheses']
    ids = [h['id'] for h in hypotheses]
    if len(ids) != len(set(ids)) or set(ids) != {f'H{i}' for i in range(1, 26)}:
        raise ValueError('Each hypothesis H1..H25 must occur once')
    references = []
    for h in hypotheses:
        for field in ('phase', 'method', 'status', 'corrected_null_evidence',
                      'predictive_model_status', 'later_avg_top6', 'ensemble_status'):
            if not h.get(field):
                raise ValueError(f'Missing hypothesis field: {field}')
        references.extend(h['sources'])
    candidate_ids = [c['id'] for c in data['candidates']]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError('Duplicate candidate')
    for c in data['candidates']:
        for field in ('source_phase', 'history', 'configuration', 'robustness',
                      'null_evidence', 'rank_diversity', 'ensemble_status', 'decision_reason'):
            if not c.get(field):
                raise ValueError(f'Missing candidate field: {field}')
        value = c['avg_top6']
        if not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 <= value <= 6:
            raise ValueError('Invalid avg_top6')
        for interval in c['paired_intervals']:
            low, high = interval['ci95']
            if not all(math.isfinite(n) for n in (low, high, interval['difference'])) or low > high:
                raise ValueError('Invalid paired interval')
        for metric in c['rank_diversity_metrics']:
            if not -1 <= metric['spearman'] <= 1 or any(
                    not 0 <= metric[f'top{k}_overlap'] <= k for k in (6, 10, 15)):
                raise ValueError('Invalid rank diversity metric')
        references.extend(c['sources'])
        references.extend(c['artifacts'])
    root = Path(root).resolve()
    for ref in references:
        path = PurePosixPath(ref['path'])
        if path.is_absolute() or '..' in path.parts or '\\' in ref['path'] or ':' in ref['path']:
            raise ValueError('References must be repository-relative paths')
        exists = (root / path).is_file()
        status = ref['availability']
        if status == 'AVAILABLE' and not exists:
            raise ValueError(f"AVAILABLE reference missing: {path}")
        if status == 'HISTORICAL_UNAVAILABLE' and exists:
            raise ValueError(f'Availability inventory must be updated: {path}')
        if status not in ('AVAILABLE', 'HISTORICAL_UNAVAILABLE'):
            raise ValueError('Unknown availability')
    return data


def _source(ref):
    path = ref['path']
    if ref['availability'] == 'AVAILABLE':
        return f'[{path}](../{path})'
    return f'`{path}` — HISTORICAL_UNAVAILABLE'


def _cell(value):
    return str(value).replace('|', '\\|').replace('\n', '<br>')


def render_documents(data):
    """Return deterministic Markdown views, retaining explicit source decisions."""
    synthesis = [
        '# 연구 증거 종합 — H1–H25', '',
        '이 표는 기존 완료 연구의 **기술적 종합(descriptive synthesis)**이다. 이전 p-value를 수학적으로 결합하거나 '
        '서로 다른 표현을 독립 증거로 세지 않는다. 통합 검정은 별도 H25 결과에만 해당한다.', '',
        '역사 연구의 공통 상한은 본번호 1–1245회다. 초기 Phase3 Gap 연구는 1244회에서 끝난다. '
        '901–1245회는 여러 Phase가 재사용한 역사 구간이므로 pristine holdout·prospective 검증이 아니다. '
        '평균 Top6의 무작위 이론 기대는 0.8이며, 표의 값은 각 원문 protocol의 결과다. '
        '다른 cadence·fit calendar의 Gap 수치를 하나로 합치지 않는다.', '',
        '| 가설 | Phase / 방법 | 상태 | 가장 강한 보정-null 근거 | 예측 모델 상태 | 이후 평균 Top6 | Ensemble 후보 상태 | 근거 |',
        '|---|---|---|---|---|---|---|---|',
    ]
    for h in data['hypotheses']:
        values = [h['id'], f"{h['phase']} / {h['method']}", h['status'],
                  h['corrected_null_evidence'], h['predictive_model_status'],
                  h['later_avg_top6'], h['ensemble_status'], ' · '.join(_source(s) for s in h['sources'])]
        synthesis.append('| ' + ' | '.join(_cell(v) for v in values) + ' |')
    synthesis += ['', 'H7은 실행하지 않은 DEFERRED, H17은 검증된 최종 조합을 아직 만들지 않은 BACKLOG다. '
                  'H22의 H1 persistence는 dependency limitation으로 보류했으며 완료 범위는 H0다. '
                  '구조 보정 통과와 예측 개선은 다른 조건이다. SSA 구조 신호와 Graph의 fixed-margin 경계값을 '
                  '예측 성공으로 승격하지 않는다.', '',
                  '현재 후보의 상세 불확실성·정확한 설정·산출물 가용성은 [후보 원장](weak-signal-candidates.md)에 있다. '
                  'canonical machine-readable 기록은 [JSON](weak-signal-candidates.json)이다. '
                  '현재 checkout에서 없는 과거 산출물의 수치는 원문 문서에서 전사했으며 재계산했다고 주장하지 않는다.', '',
                  '생성·검증: `python -m src.analysis.evidence_ledger --check`. '
                  'JSON 변경 후 `python -m src.analysis.evidence_ledger`로 두 Markdown을 갱신한다. '
                  '원본 결과·동결 archive는 변경하지 않는다.', '']
    candidates = [
        '# Weak-signal 후보 원장', '',
        '약한 역사 점추정치와 다양성을 보존하는 연구용 원장이다. **Validated ensemble이나 미래 예측 우위의 판정이 아니다.** '
        'GraphStructureModel·GapShapeModel·MirrorModel의 ENSEMBLE CANDIDATE는 탐색적 분류이며, '
        'Gap Logistic은 비교 baseline, MI는 NOT CURRENTLY JUSTIFIED로 유지한다. H17 최종 ensemble은 BACKLOG다.', '',
        '범위·수치·판정의 canonical 기록은 [JSON](weak-signal-candidates.json), 가설 전체는 '
        '[증거 종합](research-evidence-synthesis.md)에 있다. 문서에서 전사한 정밀도만 보존한다. '
        'null이나 diversity가 다른 것은 예측력이 있다는 뜻이 아니다. '
        '주요 paired CI는 명목 95% circular block-bootstrap 구간이며 모델·지표·시작점 전체의 동시구간이 아니다. '
        '동일 역사 구간의 비교와 sensitivity를 독립 반복으로 세지 않는다.', '',
        '| 모델 | 출처 Phase | 역사 평가 범위 | 평균 Top6 | 후보 판정 |',
        '|---|---|---|---:|---|',
    ]
    for c in data['candidates']:
        value = format(c['avg_top6'], f".{c['reported_precision']}f")
        candidates.append(f"| {c['name']} | {c['source_phase']} | {c['history']} | {value} | {c['ensemble_status']} |")
    for c in data['candidates']:
        value = format(c['avg_top6'], f".{c['reported_precision']}f")
        candidates += ['', f"## {c['name']}", '', f"**{c['ensemble_status']}** — {c['decision_reason']}", '',
                       f"출처: {' · '.join(_source(s) for s in c['sources'])}.", '',
                       f"역사 범위: {c['history']}. 평균 Top6={value}. {c['metric_note']}", '',
                       f"동결 설정: {c['configuration']}", '',
                       '| Paired 비교 | 범위 / 방법 | 차이 | 95% interval |', '|---|---|---:|---|']
        for p in c['paired_intervals']:
            low, high = p['ci95']
            candidates.append(f"| {p['reference']} | {p['scope']} | {p['difference']:+.6f} | [{low:+.6f}, {high:+.6f}] |")
        candidates += ['', f"강건성·민감도: {c['robustness']}", '',
                       f"보정-null 근거: {c['null_evidence']}", '',
                       f"순위 다양성: {c['rank_diversity']}", '',
                       f"명시적 미확인 값: {c['missing_evidence']}", '', '정확한 설정·출력 경로:', '']
        candidates += [f"- {_source(a)} — {a['role']}" for a in c['artifacts']]
    candidates += ['', 'HISTORICAL_UNAVAILABLE은 현재 checkout에 파일이 없다는 뜻이다. 원문 결과는 존재하지만 '
                   '해당 CSV·동결 설정·manifest의 byte/hash를 이번 원장 작업에서 재검증하지 못했다. '
                   'AVAILABLE은 현재 파일 존재만 확인한 상태이며 자동으로 과거 전체 산출물의 무결성을 보증하지 않는다. '
                   '후보를 재학습하거나 더 좋은 사후 설정으로 교체하지 않았고 실제1246 결과를 사용하지 않았다.', '',
                   '생성·검증: `python -m src.analysis.evidence_ledger --check`.', '']
    return {'research-evidence-synthesis.md': '\n'.join(synthesis),
            'weak-signal-candidates.md': '\n'.join(candidates)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    data = json.loads((root / 'docs/weak-signal-candidates.json').read_text(encoding='utf-8'))
    validate_ledger(data, root)
    for name, text in render_documents(data).items():
        path = root / 'docs' / name
        if args.check:
            if not path.is_file() or path.read_text(encoding='utf-8') != text:
                raise ValueError(f'Stale generated document: {name}')
        else:
            path.write_text(text, encoding='utf-8', newline='\n')
    print('Evidence ledger and generated views verified' if args.check else 'Evidence ledger views generated')


if __name__ == '__main__':
    main()
