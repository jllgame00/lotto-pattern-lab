import numpy as np
import pytest

from src.analysis.periodicity import (PeriodicityConfig, autocorrelation_analysis,
    spectral_analysis, periodicity_metrics, permutation_comparison)


def periodic(n=104, period=8):
    x = np.zeros(n); x[::period] = 1
    return x


def test_acf_excludes_zero_and_respects_supported_lags():
    result = autocorrelation_analysis(periodic(), PeriodicityConfig(max_lag=20))
    assert result['status'] == 'ok'
    assert min(result['lags']) == 1 and max(result['lags']) <= 20
    assert result['candidates'][0]['lag'] == 8
    assert result['strength'] == pytest.approx(12/13)
    assert all(c['correlation'] > 0 for c in result['candidates'])
    assert max(autocorrelation_analysis(periodic(26,4))['lags']) <= 8


def test_spectrum_support_and_peak():
    result = spectral_analysis(periodic(120,6))
    assert result['status'] == 'ok'
    assert any(c['period'] == pytest.approx(6) for c in result['candidates'])
    assert all(2 <= p <= 40 for p in result['periods'])
    assert 0 < result['strength'] <= 1
    stricter = spectral_analysis(periodic(120,6),PeriodicityConfig(min_cycles=6))
    assert max(stricter['periods']) <= 20
    # Long-period low-frequency power stays in the concentration denominator.
    x = np.r_[np.zeros(60),np.ones(60)]
    assert spectral_analysis(x)['strength'] < .15


@pytest.mark.parametrize('x',[[], [0]*104,[1]*104,periodic(12,3),np.r_[1,np.zeros(103)]])
def test_insufficient_data_is_null_not_zero_evidence(x):
    assert periodicity_metrics(x)['periodicity_score'] is None
    assert autocorrelation_analysis(x)['status'] != 'ok'
    assert spectral_analysis(x)['status'] != 'ok'


def test_score_formula_and_null_determinism():
    x = periodic()
    m = periodicity_metrics(x)
    assert m['gap_stability'] == 1
    assert m['periodicity_score'] == pytest.approx(.4*m['acf_strength']+.4*m['spectral_strength']+.2)
    assert 0 <= m['periodicity_score'] <= 1
    a = permutation_comparison(x,permutations=19,seed=8)
    b = permutation_comparison(x,permutations=19,seed=8)
    assert a == b
    assert a['p_value'] == pytest.approx((1+a['exceedances'])/20)
    assert a['p_value'] > 0
    assert a['appearance_count'] == 13
    assert permutation_comparison(x,permutations=0)['status'] == 'skipped'
    assert permutation_comparison([0]*26,permutations=9)['status'] != 'ok'


def test_configuration_validation():
    for kwargs in (dict(max_lag=0),dict(min_cycles=1),dict(min_observations=0),dict(min_appearances=1)):
        with pytest.raises(ValueError): PeriodicityConfig(**kwargs)
    with pytest.raises(ValueError): periodicity_metrics([0,1,2])
    with pytest.raises(ValueError): periodicity_metrics([0,float('nan'),1])
    with pytest.raises(ValueError): permutation_comparison(periodic(),permutations=-1)
