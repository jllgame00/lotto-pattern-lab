"""Bounded, non-wrapping 2D searches. Raw z scores are search statistics, not tests.

Only complete-search surrogate maxima supply inferential comparisons. Number
labels form a finite ordered axis, not a circle or a physical coordinate.
"""
from dataclasses import dataclass, asdict
from functools import lru_cache
from math import gcd

import numpy as np
import pandas as pd
from scipy.signal import fftconvolve

from src.collect.dataset import validate_history, MAIN_COLUMNS

P=6/45


@dataclass(frozen=True)
class SearchConfig:
    max_dt: int=52
    max_dn: int=15
    hough_dt: int=12
    hough_dn: int=6
    hough_min_length: int=12

    def __post_init__(self):
        if any(type(v) is not int or v<1 for v in asdict(self).values()):
            raise ValueError('Search bounds must be positive integers')
        if max(self.max_dn,self.hough_dn)>44:
            raise ValueError('Number displacement must be less than45')


def lotto_matrix(history, *, cutoff):
    """Strict contiguous prefix; refuse extra rows rather than silently slice."""
    if type(cutoff) is not int or not 1<=cutoff<=1245:
        raise ValueError('Phase6 cutoff must be1..1245')
    if history.draw_no.tolist()!=list(range(1,cutoff+1)):
        raise ValueError('Matrix requires exactly ordered draws1..cutoff; no future rows')
    data=validate_history(history)
    x=np.zeros((cutoff,45),dtype=bool)
    x[np.arange(cutoff)[:,None],data[MAIN_COLUMNS].to_numpy(dtype=int)-1]=True
    if not np.all(x.sum(axis=1)==6): raise ValueError('Six main points per row required')
    return x


def binary_matrix(x):
    x=np.asarray(x)
    if x.ndim!=2 or x.shape[1]!=45 or len(x)<2 or not np.isin(x,[0,1]).all():
        raise ValueError('Expected a binary draw-by45 matrix with at least2 rows')
    return x.astype(bool,copy=False)


def aligned(x,dt,dn,steps=1):
    """Source and destination views, clipped on BOTH axes; never wrap."""
    time=dt*steps; shift=dn*steps
    if time>=len(x) or abs(shift)>=45: return x[:0,:0],x[:0,:0]
    if shift>=0: return x[:-time,:45-shift],x[time:,shift:]
    return x[:-time,-shift:],x[time:,:45+shift]


def shift_scores(x, *, max_dt=52,max_dn=15):
    x=binary_matrix(x)
    if not 1<=max_dt<len(x) or not 1<=max_dn<=44: raise ValueError('Invalid shift bounds')
    overlap=np.rint(fftconvolve(x[::-1,::-1].astype(float),x.astype(float))).astype(int)
    records=[]
    for dt in range(1,max_dt+1):
        for dn in range(-max_dn,max_dn+1):
            source,_=aligned(x,dt,dn)
            opportunities=int(source.sum()); area=source.size
            matches=int(overlap[len(x)-1+dt,44+dn])
            rate=matches/opportunities if opportunities else np.nan
            z=(matches-opportunities*P)/np.sqrt(opportunities*P*(1-P)) if opportunities else 0.
            records.append(dict(delta_draw=dt,delta_number=dn,overlap_area=area,
                valid_opportunities=opportunities,observed_matches=matches,match_rate=rate,
                joint_rate=matches/area,expected_rate=P,expected_joint_rate=P*P,
                lift=rate/P,raw_z=z))
    return pd.DataFrame(records)


def directional_scores(shifts):
    positive=shifts[shifts.delta_number>0].copy()
    negative=shifts[shifts.delta_number<0].copy(); negative['delta_number']*=-1
    both=positive.merge(negative,on=['delta_draw','delta_number'],suffixes=('_positive','_negative'))
    both['rate_difference']=both.match_rate_positive-both.match_rate_negative
    variance=P*(1-P)*(1/both.valid_opportunities_positive.replace(0,np.nan)+1/both.valid_opportunities_negative.replace(0,np.nan))
    both['raw_z']=both.rate_difference/np.sqrt(variance)
    # Independence approximation only: calibration uses complete-search nulls.
    return both


def _chain_search(x,max_dt,max_dn,details):
    counts=[]; paths=[]; longest=0
    for dt in range(1,max_dt+1):
        for dn in range(-max_dn,max_dn+1):
            if dn==0: continue
            active=x.copy(); lengths=x.astype(np.uint8) if details else None
            maximum=min((len(x)-1)//dt,44//abs(dn))+1
            for length in range(2,maximum+1):
                step=length-1
                source,destination=aligned(x,dt,dn,step)
                tlen,nlen=source.shape
                offset=0 if dn>0 else step*abs(dn)
                following=np.zeros_like(x)
                following[:tlen,offset:offset+nlen]=active[:tlen,offset:offset+nlen]&destination
                active=following; count=int(active.sum())
                if length in (3,4,5):
                    area=(len(x)-step*dt)*(45-step*abs(dn)); expected=area*P**length
                    counts.append(dict(delta_draw=dt,delta_number=dn,chain_length=length,
                        valid_starts=area,count=count,expected_count=expected,
                        raw_z=(count-expected)/np.sqrt(expected*(1-P**length))))
                if count:
                    longest=max(longest,length)
                    if details: lengths[active]=length
                # Continue through length5 even after no matches, for full search.
                elif length>=5: break
            if details:
                predecessor=np.zeros_like(x)
                a,b=aligned(x,dt,dn)
                if dn>0: predecessor[dt:,dn:]=a
                else: predecessor[dt:,:45+dn]=a
                ts,ns=np.where((lengths>=3)&~predecessor)
                for t,n in zip(ts,ns):
                    length=int(lengths[t,n]); geometric=min((len(x)-1-t)//dt,
                        (44-n)//dn if dn>0 else n//(-dn))+1
                    paths.append(dict(start_draw=int(t+1),start_number=int(n+1),
                        end_draw=int(t+1+(length-1)*dt),end_number=int(n+1+(length-1)*dn),
                        delta_draw=dt,delta_number=dn,chain_length=length,
                        geometric_maximum=geometric,observed_chain_score=float(-length*np.log(P))))
    return pd.DataFrame(counts),pd.DataFrame(paths),longest


def chains(x, *, max_dt=52,max_dn=15):
    x=binary_matrix(x)
    if not 1<=max_dt<len(x) or not 1<=max_dn<=44: raise ValueError('Invalid chain bounds')
    return _chain_search(x,max_dt,max_dn,True)[1]


@lru_cache(maxsize=4)
def _hough_geometry(length,max_dt,max_dn,min_length):
    t,n=np.indices((length,45)); geometries=[]
    for dt in range(1,max_dt+1):
        for dn in range(-max_dn,max_dn+1):
            if not dn or gcd(dt,abs(dn))!=1: continue
            intercept=dt*n-dn*t; minimum=int(intercept.min())
            ids=(intercept-minimum).ravel().astype(np.int32)
            size=np.bincount(ids); eligible=np.flatnonzero(size>=min_length)
            geometries.append((dt,dn,minimum,ids,size,eligible))
    return geometries


def hough_lines(x, *, max_dt=12,max_dn=6,min_length=12,limit=50):
    x=binary_matrix(x); values=x.ravel().astype(float); records=[]
    for dt,dn,minimum,ids,size,eligible in _hough_geometry(len(x),max_dt,max_dn,min_length):
        counts=np.bincount(ids,weights=values,minlength=len(size))
        if not len(eligible): continue
        z=(counts[eligible]-size[eligible]*P)/np.sqrt(size[eligible]*P*(1-P))
        selected=np.argsort(-z,kind='stable')[:limit]
        for index in selected:
            line=int(eligible[index]); positions=np.flatnonzero(ids==line)
            first,last=int(positions[0]),int(positions[-1])
            records.append(dict(delta_draw=dt,delta_number=dn,slope=dn/dt,
                intercept_zero_based=line+minimum,support=int(counts[line]),
                line_length=int(size[line]),density=float(counts[line]/size[line]),raw_z=float(z[index]),
                start_draw=first//45+1,start_number=first%45+1,
                end_draw=last//45+1,end_number=last%45+1))
    frame=pd.DataFrame(records)
    return frame.sort_values('raw_z',ascending=False,kind='stable').head(limit).reset_index(drop=True) if len(frame) else frame


def spectrum(x):
    x=binary_matrix(x).astype(float)
    # Axis centering removes number prevalence and the structural six-per-draw DC.
    centered=x-x.mean(axis=0)-x.mean(axis=1)[:,None]+x.mean()
    taper=np.hanning(len(x))[:,None]*np.hanning(45)[None,:]
    power=np.abs(np.fft.fft2(centered*taper))**2
    ft=np.fft.fftfreq(len(x)); fn=np.fft.fftfreq(45)
    mask=(ft[:,None]>0)&(fn[None,:]!=0)
    rows,cols=np.where(mask)
    denominator=float(power[mask].sum())
    normalized=power[mask]/denominator if denominator else np.zeros(len(rows))
    order=np.argsort(-normalized,kind='stable')[:20]
    return pd.DataFrame(dict(temporal_frequency=ft[rows[order]],number_frequency=fn[cols[order]],
        normalized_power=normalized[order],power=power[rows[order],cols[order]]))


def search(x,config=SearchConfig(), *, details=True):
    x=binary_matrix(x)
    shifts=shift_scores(x,max_dt=config.max_dt,max_dn=config.max_dn)
    direction=directional_scores(shifts)
    counts,paths,longest=_chain_search(x,config.max_dt,config.max_dn,details)
    lines=hough_lines(x,max_dt=config.hough_dt,max_dn=config.hough_dn,
        min_length=config.hough_min_length,limit=50 if details else 1)
    spectral=spectrum(x)
    maxima=dict(shift=float(shifts.loc[shifts.delta_number!=0,'raw_z'].max()),
        direction=float(direction.raw_z.abs().fillna(0).max()),
        chain=float(counts.raw_z.max()) if len(counts) else 0.,longest_chain=int(longest),
        hough=float(lines.raw_z.max()) if len(lines) else 0.,
        spectrum=float(spectral.normalized_power.max()))
    return dict(shifts=shifts,direction=direction,chain_counts=counts,chains=paths,
        lines=lines,spectrum=spectral,maxima=maxima)


def iid_surrogate(length, *, seed):
    if type(length) is not int or length<2: raise ValueError('Need at least2 draws')
    rng=np.random.default_rng(seed); x=np.zeros((length,45),bool)
    numbers=np.argpartition(rng.random((length,45)),5,axis=1)[:,:6]
    x[np.arange(length)[:,None],numbers]=True
    return x


def constrained_surrogate(x, *, seed,trades_per_row=20):
    """Curveball trades, independently initialized; exact margins, finite mixing."""
    x=binary_matrix(x).copy()
    if not np.all(x.sum(axis=1)==6) or type(trades_per_row) is not int or trades_per_row<1:
        raise ValueError('Six-per-row input and positive mixing effort required')
    rng=np.random.default_rng(seed)
    for _ in range(trades_per_row*len(x)):
        a,b=rng.choice(len(x),2,replace=False)
        exclusive=np.flatnonzero(x[a]^x[b]); size=len(exclusive)//2
        if not size: continue
        rng.shuffle(exclusive)
        x[a,exclusive]=False; x[b,exclusive]=False
        x[a,exclusive[:size]]=True; x[b,exclusive[size:]]=True
    return x


def compare_nulls(x,config=SearchConfig(), *, replicates=199,seed=60042,progress=None):
    if type(replicates) is not int or replicates<1: raise ValueError('Positive null replication count required')
    x=binary_matrix(x)
    if not np.all(x.sum(axis=1)==6): raise ValueError('Null comparison requires six main numbers per draw')
    observed=search(x,config,details=False)['maxima']; rows=[]
    for kind,code in [('iid',0),('fixed_margins',1)]:
        for i in range(replicates):
            child=int(np.random.SeedSequence([seed,code,i]).generate_state(1)[0])
            surrogate=iid_surrogate(len(x),seed=child) if kind=='iid' else constrained_surrogate(x,seed=child)
            result=search(surrogate,config,details=False)['maxima']
            rows.append(dict(null_model=kind,replicate=i,seed=child,changed_fraction=float((surrogate!=x).mean()),**result))
            if progress and (i+1)%10==0: progress(f'{kind}: complete searches {i+1}/{replicates}')
    null=pd.DataFrame(rows); comparison=[]
    for kind,group in null.groupby('null_model'):
        for statistic,value in observed.items():
            exceed=int((group[statistic]>=value).sum()); p=(1+exceed)/(replicates+1)
            comparison.append(dict(null_model=kind,statistic=statistic,real_max=value,
                null_mean=float(group[statistic].mean()),null_q95=float(group[statistic].quantile(.95)),
                exceedances=exceed,replicates=replicates,global_p=p,family_adjusted_p=min(1,p*len(observed))))
    return pd.DataFrame(comparison),null
