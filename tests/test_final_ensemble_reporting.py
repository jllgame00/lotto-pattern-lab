"""Reporting corrections must preserve frozen selection and include numerical ties."""
import numpy as np
import pytest
from src.analysis.final_ensemble_reporting import inclusive_tail


def test_fallback_float_ties_are_included():
    observed = .05072463768116009
    values = np.array([observed - 9.02e-17] * 197 + [-.1, -.2])
    assert inclusive_tail(values, observed) == .99


def test_distinct_rank_gains_and_plus_one_denominator():
    assert inclusive_tail([-.1, 0., .1], 0.) == .75
    assert inclusive_tail([-.1, -.01], 0.) == pytest.approx(1 / 3)


def test_invalid_tail_evidence_rejected():
    for values in ([], [np.nan], [np.inf]):
        with pytest.raises(ValueError):
            inclusive_tail(values, 0.)
    with pytest.raises(ValueError):
        inclusive_tail([0.], np.nan)
