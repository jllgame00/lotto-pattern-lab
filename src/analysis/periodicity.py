"""Guarded descriptive periodicity diagnostics, not probabilities or predictors."""
from dataclasses import dataclass
from numbers import Integral

import numpy as np
from scipy.signal import periodogram


@dataclass(frozen=True)
class PeriodicityConfig:
    max_lag: int = 52
    min_observations: int = 20
    min_appearances: int = 4
    min_absences: int = 4
    min_cycles: int = 3
    min_overlap: int = 12

    def __post_init__(self):
        for name, lower in [('max_lag',1),('min_observations',8),('min_appearances',4),
                            ('min_absences',4),('min_cycles',2),('min_overlap',4)]:
            value = getattr(self,name)
            if isinstance(value,bool) or not isinstance(value,Integral) or value < lower:
                raise ValueError(f'{name} must be an integer >= {lower}')


def _binary(values):
    x = np.asarray(values,dtype=float)
    if x.ndim != 1 or not np.isin(x,[0,1]).all():
        raise ValueError('Expected a finite one-dimensional binary sequence')
    return x


def _status(x, config):
    if len(x) < config.min_observations:
        return 'insufficient_observations'
    if x.sum() < config.min_appearances:
        return 'insufficient_appearances'
    if len(x)-x.sum() < config.min_absences:
        return 'insufficient_absences'
    return 'ok'


def autocorrelation_analysis(values, config=None):
    """Demeaned biased ACF, excluding lag zero; overlap guards apply per lag.

    r(k)=sum((x[t]-mean)*(x[t+k]-mean))/sum((x-mean)^2).
    Long lags are attenuated by this estimator. Lag 1 can indicate persistence,
    not a cycle; all returned candidates are exploratory correlations.
    """
    config = config or PeriodicityConfig()
    x = _binary(values)
    result = dict(status=_status(x,config), lags=[], correlations=[], candidates=[],
                  dominant_lag=None, strength=None)
    if result['status'] != 'ok':
        return result
    n = len(x)
    maximum = min(config.max_lag, n//config.min_cycles, n-config.min_overlap)
    if maximum < 1:
        result['status'] = 'insufficient_overlap'
        return result
    lags = np.arange(1,maximum+1)
    centered = x-x.mean()
    raw = np.correlate(centered,centered,mode='full')[n:n+maximum] / np.dot(centered,centered)
    sums = np.r_[0,np.cumsum(x)]
    left = sums[n-lags]
    right = sums[n]-sums[lags]
    eligible = (left>=2)&(right>=2)&(n-lags-left>=2)&(n-lags-right>=2)
    raw = np.where(eligible, raw, np.nan)
    result.update(lags=lags.tolist(), correlations=[float(v) if np.isfinite(v) else None for v in raw])
    if not eligible.any():
        result['status'] = 'insufficient_overlap_classes'
        return result
    order = sorted((i for i,v in enumerate(raw) if np.isfinite(v) and v>0),
                   key=lambda i:(-raw[i],lags[i]))[:3]
    candidates = [dict(lag=int(lags[i]),correlation=float(raw[i])) for i in order]
    result.update(candidates=candidates, dominant_lag=candidates[0]['lag'] if candidates else None,
                  strength=candidates[0]['correlation'] if candidates else 0.0)
    return result


def spectral_analysis(values, config=None):
    """Hann periodogram, no zero padding, periods 2..n/min_cycles draws.

    Concentration uses all non-DC power in the denominator, even power outside
    the allowed period range. Neighboring peak bins/harmonics are not independent.
    """
    config = config or PeriodicityConfig()
    x = _binary(values)
    result = dict(status=_status(x,config), periods=[], powers=[], candidates=[],
                  dominant_period=None, dominant_power=None, strength=None)
    if result['status'] != 'ok':
        return result
    frequencies,powers = periodogram(x,fs=1.0,window='hann',detrend='constant',scaling='spectrum')
    frequencies,powers = frequencies[1:],powers[1:]
    periods = 1/frequencies
    eligible = (periods>=2)&(periods<=len(x)/config.min_cycles+1e-10)
    total = powers.sum()
    if not eligible.any() or total <= np.finfo(float).eps:
        result['status'] = 'insufficient_spectral_support'
        return result
    periods,power = periods[eligible],powers[eligible]
    order = np.argsort(-power,kind='stable')[:3]
    candidates = [dict(period=float(periods[i]),power=float(power[i])) for i in order if power[i]>0]
    if not candidates:
        result['status'] = 'insufficient_spectral_support'
        return result
    peak = candidates[0]
    result.update(periods=periods.tolist(),powers=power.tolist(),candidates=candidates,
                  dominant_period=peak['period'],dominant_power=peak['power'],
                  strength=float(np.clip(peak['power']/total,0,1)))
    return result


def periodicity_metrics(values, config=None):
    """Score = .4 ACF+ + .4 concentration + .2/(1+gap_CV^2), in [0,1]."""
    config = config or PeriodicityConfig()
    x = _binary(values)
    acf = autocorrelation_analysis(x,config)
    spectrum = spectral_analysis(x,config)
    gaps = np.diff(np.flatnonzero(x))
    result = dict(status=acf['status'] if acf['status']!='ok' else spectrum['status'],
                  periodicity_score=None, acf_strength=acf['strength'],dominant_lag=acf['dominant_lag'],
                  dominant_period=spectrum['dominant_period'],dominant_power=spectrum['dominant_power'],
                  spectral_strength=spectrum['strength'],gap_stability=None)
    if result['status'] != 'ok':
        return result
    stability = float(1/(1+(np.std(gaps)/np.mean(gaps))**2))
    result.update(gap_stability=stability,
                  periodicity_score=float(np.clip(.4*acf['strength']+.4*spectrum['strength']+.2*stability,0,1)))
    return result


def permutation_comparison(values, config=None, permutations=199, seed=42):
    """Upper-tail conditional shuffle comparison; repeats all lag/bin scans.

    Tests order conditional on appearance count, not count fairness. The p-value
    concerns this fixed sequence/scope, not a selected rolling peak or regime.
    """
    for name,value in [('permutations',permutations),('seed',seed)]:
        if isinstance(value,bool) or not isinstance(value,Integral) or value<0:
            raise ValueError(f'{name} must be a nonnegative integer')
    x = _binary(values)
    observed = periodicity_metrics(x,config)
    result = dict(status=observed['status'],observed_score=observed['periodicity_score'],
                  observations=len(x),appearance_count=int(x.sum()),permutations=permutations,seed=int(seed),
                  exceedances=None,p_value=None,p_resolution=1/(permutations+1) if permutations else None,
                  null_mean=None,null_q95=None,monte_carlo_se=None)
    if permutations==0:
        result['status']='skipped'
        return result
    if result['status']!='ok':
        return result
    rng=np.random.default_rng(seed)
    null=np.array([periodicity_metrics(rng.permutation(x),config)['periodicity_score']
                   for _ in range(permutations)],dtype=float)
    if not np.isfinite(null).all():
        result['status']='unsupported_null_permutation'
        return result
    exceedances=int(np.sum(null>=observed['periodicity_score']-1e-12))
    p=(1+exceedances)/(permutations+1)
    result.update(exceedances=exceedances,p_value=p,null_mean=float(null.mean()),
                  null_q95=float(np.quantile(null,.95)),monte_carlo_se=float(np.sqrt(p*(1-p)/(permutations+1))))
    return result
