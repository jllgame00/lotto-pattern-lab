"""Finite ordered-number-space utilities. No number wrap and no result fetching."""
from functools import lru_cache
from math import comb
import numpy as np
import pandas as pd
from scipy.ndimage import convolve1d
from src.analysis.spatiotemporal import binary_matrix, P

WINDOWS=(10,26,52)
WIDTHS=(3,5,7,9)
PRIMARY_KERNELS=('none','triangular1','triangular2','gaussian2')
KERNELS=PRIMARY_KERNELS+('box1','box2','box3','box4')
METRICS=('minimum_spacing','maximum_spacing','mean_spacing','median_spacing',
    'spacing_variance','consecutive_pairs','draw_range','nearest_mean','gaps_le2',
    'gaps_ge10','clusters_2','clusters_4',*(f'region_{i}' for i in range(5)))


def matrix(x):
    x=binary_matrix(x)
    if len(x)>1245 or not np.all(x.sum(axis=1)==6):
        raise ValueError('Exactly six main points per row; cutoff never above1245')
    return x


def ranges(width):
    if type(width) is not int or width not in WIDTHS:raise ValueError('Predeclared widths3/5/7/9 only')
    starts=np.arange(1,47-width)
    return np.column_stack((starts,starts+width-1))


def rolling_counts(x,window):
    x=matrix(x)
    if type(window) is not int or window not in WINDOWS or len(x)<window:
        raise ValueError('Full predeclared recent window required')
    c=np.vstack((np.zeros((1,45),int),np.cumsum(x,axis=0)))
    return c[window:]-c[:-window]


def range_arrays(x,window,width):
    counts=rolling_counts(x,window);ranges(width)
    c=np.column_stack((np.zeros(len(counts),int),np.cumsum(counts,axis=1)))
    totals=c[:,width:]-c[:,:-width]
    expectation=window*width*P
    variance=window*6*(width/45)*(1-width/45)*39/44
    return totals,(totals-expectation)/np.sqrt(variance)


def range_history(x,*,window,width):
    x=matrix(x);counts,z=range_arrays(x,window,width);r=ranges(width)
    ends=np.arange(window,len(x)+1)
    return pd.DataFrame(dict(end_draw=np.repeat(ends,len(r)),target_draw=np.repeat(ends+1,len(r)),
        window=window,width=width,start_number=np.tile(r[:,0],len(ends)),end_number=np.tile(r[:,1],len(ends)),
        occurrences=counts.ravel(),density=counts.ravel()/(window*width),expected_density=P,
        lift=counts.ravel()/(window*width*P),raw_z=z.ravel(),support_draws=window))


def recent_density(x,*,target,window,width):
    x=matrix(x)
    if type(target) is not int or target!=len(x)+1 or target>1246:
        raise ValueError('Only completed draws strictly before declared target allowed')
    return range_history(x,window=window,width=width).tail(46-width).reset_index(drop=True)


@lru_cache(maxsize=24)
def kernel_matrix(name,neighbor_only=False):
    weights={'none':[1.], 'triangular1':[.5,1,.5],
        'triangular2':[.25,.5,1,.5,.25], 'gaussian2':np.exp(-np.arange(-2,3,dtype=float)**2/2).tolist()}
    if name.startswith('box') and name in KERNELS:weights[name]=[1.]*(2*int(name[-1])+1)
    if name not in weights:raise ValueError('Unknown predeclared kernel')
    w=np.asarray(weights[name]);radius=len(w)//2
    if neighbor_only:
        w=w.copy();w[radius]=0
        if w.sum()==0:raise ValueError('Center-only kernel has no neighbor signal')
    m=np.zeros((45,45))
    for n in range(45):
        for offset,weight in zip(range(-radius,radius+1),w):
            if 0<=n+offset<45:m[n,n+offset]=weight
    m/=m.sum(axis=1,keepdims=True);m.setflags(write=False)
    return m


def smooth(activity,kernel,*,neighbor_only=False):
    a=np.asarray(activity,dtype=float)
    if a.shape[-1:]!=(45,) or not np.isfinite(a).all():raise ValueError('Finite45-number activity required')
    middle=kernel_matrix(kernel,neighbor_only)[22]
    radius=int(np.max(np.abs(np.flatnonzero(middle)-22)))
    weights=middle[22-radius:23+radius]
    return convolve1d(a,weights,axis=-1,mode='constant',cval=0)/convolve1d(np.ones(45),weights,mode='constant',cval=0)


def smooth_z(activity,kernel,window,*,neighbor_only=False):
    m=kernel_matrix(kernel,neighbor_only)
    variance=P*(1-P)*(45*np.square(m).sum(axis=1)-1)/(44*window)
    return (smooth(activity,kernel,neighbor_only=neighbor_only)-P)/np.sqrt(variance)


def group_zones(intervals):
    groups=[]
    for a,b in sorted(intervals):
        if not 1<=a<=b<=45:raise ValueError('Finite ordered interval required')
        if groups and a<=groups[-1][1]:groups[-1]=(groups[-1][0],max(b,groups[-1][1]))
        else:groups.append((a,b))
    return groups


def strong_zones(density,limit=3):
    top=density[density.raw_z>0].sort_values(['raw_z','start_number'],ascending=[False,True]).head(limit)
    return top,group_zones(list(zip(top.start_number.astype(int),top.end_number.astype(int))))


def _longest(values):
    longest=run=0
    for v in values:
        run=run+1 if v else 0;longest=max(longest,run)
    return longest


def movement(centers,*,width):
    c=np.asarray(centers,dtype=float)
    if c.ndim!=1 or len(c)<1 or not np.isfinite(c).all():raise ValueError('Finite center sequence required')
    d=np.diff(c); identical=1+_longest(d==0)
    sign=np.sign(d); run=best=0;previous=0
    for value,step in zip(sign,d):
        valid=value!=0 and abs(step)<=4
        run=run+1 if valid and value==previous else 1 if valid else 0
        previous=value if valid else 0;best=max(best,run)
    overlap=np.maximum(0,width-np.abs(d))/(width+np.abs(d))
    return dict(identical_run=identical,direction_run=best,mean_abs_movement=float(np.abs(d).mean()) if len(d) else 0.,
        overlap_mean=float(overlap.mean()) if len(d) else 1.,
        **{f'{direction}_{k}_run':_longest(d==sgn*k) for direction,sgn in [('positive',1),('negative',-1)] for k in range(1,5)})


def zone_history(x,*,window,width):
    counts,z=range_arrays(x,window,width);idx=z.argmax(axis=1);end=np.arange(window,len(x)+1)
    starts=idx+1;centers=starts+(width-1)/2;delta=np.r_[np.nan,np.diff(centers)]
    overlap=np.maximum(0,width-np.abs(delta))/(width+np.abs(delta))
    return pd.DataFrame(dict(end_draw=end,target_draw=end+1,window=window,width=width,start_number=starts,
        end_number=starts+width-1,center=centers,raw_z=z[np.arange(len(z)),idx],
        occurrences=counts[np.arange(len(z)),idx],lift=counts[np.arange(len(z)),idx]/(window*width*P),
        center_displacement=delta,previous_overlap=overlap))


def draw_statistics(x,*,details=True):
    x=matrix(x);numbers=np.nonzero(x)[1].reshape(-1,6)+1;g=np.diff(numbers,axis=1)
    nearest=np.column_stack((g[:,0],np.minimum(g[:,:-1],g[:,1:]),g[:,-1]))
    d=dict(minimum_spacing=g.min(axis=1),maximum_spacing=g.max(axis=1),mean_spacing=g.mean(axis=1),
        median_spacing=np.median(g,axis=1),spacing_variance=g.var(axis=1),consecutive_pairs=(g==1).sum(axis=1),
        draw_range=numbers[:,-1]-numbers[:,0],nearest_mean=nearest.mean(axis=1),gaps_le2=(g<=2).sum(axis=1),
        gaps_ge10=(g>=10).sum(axis=1),clusters_2=1+(g>2).sum(axis=1),clusters_4=1+(g>4).sum(axis=1),
        **{f'region_{i}':x[:,i*9:(i+1)*9].sum(axis=1) for i in range(5)})
    if details:d.update(draw_no=np.arange(1,len(x)+1),sorted_numbers=list(numbers.tolist()),adjacent_spacings=list(g.tolist()))
    return pd.DataFrame(d)


def search_space(length):
    if type(length) is not int or not 52<=length<=1245:raise ValueError('Search needs52..1245 completed draws')
    endpoints=sum(length-w+1 for w in WINDOWS)
    return dict(range_density_cells=endpoints*sum(46-w for w in WIDTHS),
        kernel_cells=endpoints*45*(len(KERNELS)*2-1),
        zone_endpoint_cells=endpoints*len(WIDTHS),zone_movement_metrics=12*12,
        spacing_cells=sum(length-w+1 for w in (1,*WINDOWS))*len(METRICS),
        motif_universe=comb(44,5),range_configurations=12,primary_kernel_configurations=12,
        kernel_signal_configurations=45,families=6)
