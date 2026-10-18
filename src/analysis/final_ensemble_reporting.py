"""Reporting-only, tie-inclusive correction; never select or re-evaluate models."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def inclusive_tail(values, observed):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all() or not np.isfinite(observed):
        raise ValueError('Finite, nonempty tail evidence required')
    # Rank-gain resolution is >=1/(6*115); 1e-12 only absorbs float roundoff.
    return float((1 + np.count_nonzero(values >= observed - 1e-12)) / (len(values) + 1))


def correction(directory):
    directory = Path(directory).resolve()
    root = Path(__file__).resolve().parents[2]
    if not directory.is_relative_to(root / 'reports' / 'final_ensemble'):
        raise ValueError('H17 report directory required')
    summary_path = directory / 'main_summary.json'
    original = summary_path.read_bytes()
    summary = json.loads(original)
    table = pd.read_csv(directory / 'placebos.csv', float_precision='round_trip')
    raw = {kind: inclusive_tail(group.final_rank_gain, summary['selected_final_rank_gain'])
           for kind, group in table.groupby('kind')}
    payload = dict(
        scope='reporting-only numerical tie correction; no model/selection/evaluation rerun',
        reason='default CSV float parsing shifted 197 identical fallback gains down by about 9e-17 and strict comparison excluded ties',
        original_summary_sha256=hashlib.sha256(original).hexdigest(),
        original_raw_tail_fractions=summary['placebo_comparison']['raw_tail_fractions'],
        corrected_raw_tail_fractions=raw, tolerance=1e-12,
        promotion_tail_fractions=summary['placebo_comparison']['promotion_tail_fractions'],
        status=summary['status'], validation_passed=summary['validation_passed'],
        selection_changed=False, final_evaluation_rerun=False,
        interpretation='Diagnostic exceedance fractions, not calibrated frequentist p-values',
        placebo_sha256=hashlib.sha256((directory / 'placebos.csv').read_bytes()).hexdigest())
    with (directory / 'reporting_correction.json').open('x', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write('\n')
    return payload


if __name__ == '__main__':
    print(json.dumps(correction(Path(__file__).resolve().parents[2] / 'reports/final_ensemble'), indent=2))
