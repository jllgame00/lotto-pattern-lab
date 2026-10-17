"""Frozen H22 point clouds and exact finite H0 via dense Prim, not an H1 engine."""
from dataclasses import dataclass
from numbers import Integral
import numpy as np
from scipy.spatial.distance import pdist,squareform
from .recurrence import research_matrix
from .change_point_representation import shape_vector,SHAPE_FEATURES

WINDOWS=(208,416,624)
H1_STATUS='H1_DEFERRED_DEPENDENCY_LIMITATION'


@dataclass(frozen=True)
class CloudConfig:
    family:str
    metric:str
    window:int=1

    def __post_init__(self):
        if type(self.window) is not int or (self.family,self.metric,self.window) not in (
                ('A','jaccard',1),('A','hamming',1),('B','euclidean',1),('C','euclidean',26),('C','euclidean',52)):
            raise ValueError('Outside the five predeclared cloud configurations')

    @property
    def key(self):
        return f'{self.family}{self.window if self.family=="C" else ""}_{self.metric}'


def configurations():
    return (CloudConfig('A','jaccard'),CloudConfig('A','hamming'),CloudConfig('B','euclidean'),
            CloudConfig('C','euclidean',26),CloudConfig('C','euclidean',52))


def build_cloud(x,config,*,start=1,end=None,cutoff=None):
    x=research_matrix(x);n=len(x)
    if config not in configurations():raise ValueError('Declared cloud config required')
    if cutoff is not None and (isinstance(cutoff,(bool,np.bool_)) or not isinstance(cutoff,Integral) or cutoff!=n):
        raise ValueError('cutoff must equal the complete supplied historical prefix')
    end=n if end is None else end
    if any(isinstance(v,(bool,np.bool_)) or not isinstance(v,Integral) for v in (start,end)) or not 1<=start<end<=n:
        raise ValueError('At least two completed interval draws required')
    local=x[start-1:end];mean=None;std=None;block_starts=None
    if config.family=='A':
        values=local.astype(float);point_draws=np.arange(start,end+1)
        shared=values@values.T
        distances=(12-2*shared)/45 if config.metric=='hamming' else 1-shared/(12-shared)
    elif config.family=='B':
        shape=shape_vector(local);shifted=shape-shape[0];center=shifted.mean(0)
        mean=shape[0]+center;std=shifted.std(0,ddof=0);constant=np.ptp(shape,axis=0)==0
        std=np.where(constant,1.,std);values=(shifted-center)/std;values[:,constant]=0.
        point_draws=np.arange(start,end+1);distances=squareform(pdist(values,'euclidean'))
    else:
        w=config.window;count=len(local)//w
        if not count:raise ValueError('No complete activity block')
        used=local[len(local)-count*w:]
        values=used.reshape(count,w,45).mean(1)
        point_draws=np.arange(end-(count-1)*w,end+1,w);block_starts=point_draws-w+1
        distances=squareform(pdist(values,'euclidean')) if count>1 else np.zeros((1,1))
    np.fill_diagonal(distances,0.)
    return dict(config=config.key,family=config.family,metric=config.metric,activity_window=config.window,
        start=int(start),end=int(end),values=values,distances=distances,point_count=len(values),
        point_draws=point_draws,block_starts=block_starts,mean=mean,std=std,
        shape_features=list(SHAPE_FEATURES) if config.family=='B' else None,
        activity_overlap_within_cloud=0 if config.family=='C' else None)


def _distance_matrix(d):
    d=np.asarray(d,float)
    if (d.ndim!=2 or len(d)==0 or d.shape[0]!=d.shape[1] or not np.isfinite(d).all()
            or (d<0).any() or not np.allclose(d,d.T,atol=1e-12,rtol=1e-12)
            or not np.allclose(np.diag(d),0,atol=1e-12,rtol=0)):
        raise ValueError('Finite symmetric nonnegative zero-diagonal distance matrix required')
    return d


def distance_diagnostics(distances):
    d=_distance_matrix(distances);n=len(d)
    if n==1:
        return dict(point_count=1,median_pairwise=0.,median_nearest=0.,variance=0.,nearest_median_ratio=np.nan,
                    coefficient_variation=np.nan,degenerate=True,concentrated=False,zero_pairs=0)
    pair=d[np.triu_indices(n,1)];copy=d.copy();np.fill_diagonal(copy,np.inf)
    median=float(np.median(pair));nearest=float(np.median(copy.min(1)));variance=float(np.var(pair))
    cv=float(np.sqrt(variance)/median) if median>0 else np.nan
    return dict(point_count=n,median_pairwise=median,median_nearest=nearest,variance=variance,
        nearest_median_ratio=nearest/median if median>0 else np.nan,coefficient_variation=cv,
        degenerate=bool(np.ptp(pair)<=1e-12*max(1.,median)),concentrated=bool(np.isfinite(cv) and cv<.1),
        zero_pairs=int(np.count_nonzero(pair==0)))


def h0_persistence(distances):
    """All VR H0 merges: n-1 finite bars plus one final essential component.

    An edge appears at its distance (not distance/2). Zero edges remain edges.
    Strict improvement and first-index argmin make tied MST output deterministic;
    tied spanning trees/attributions need not be geometrically unique.
    """
    d=_distance_matrix(distances);n=len(d);used=np.zeros(n,bool)
    best=np.full(n,np.inf);parent=np.full(n,-1,int);best[0]=0.;edges=[]
    for step in range(n):
        node=int(np.argmin(best))
        if step:edges.append((int(parent[node]),node,float(best[node])))
        used[node]=True;better=(~used)&(d[node]<best)
        best[better]=d[node,better];parent[better]=node;best[node]=np.inf
    edges=sorted(edges,key=lambda item:(item[2],item[0],item[1]))
    edges=np.asarray(edges,float).reshape(-1,3);deaths=edges[:,2];total=float(deaths.sum())
    positive=deaths[deaths>0]/total if total>0 else np.empty(0)
    entropy=float(-np.sum(positive*np.log(positive)))
    tail_count=max(1,int(np.ceil(.1*len(deaths))))
    return dict(edges=edges,finite_intervals=np.column_stack((np.zeros(len(deaths)),deaths)),
        infinite_components=1,infinite_interval=(0.,np.inf),longest=float(deaths[-1]) if len(deaths) else 0.,
        total=total,entropy=entropy,tail=float(deaths[-tail_count:].sum()/total) if total>0 else 0.,
        tail_count=tail_count if len(deaths) else 0,filtration_max=float(d.max()),h1_status=H1_STATUS)


def rolling_endpoints(n,window,stride=104):
    if (isinstance(n,(bool,np.bool_)) or not isinstance(n,Integral) or not 2<=n<=1245
            or isinstance(window,(bool,np.bool_)) or not isinstance(window,Integral) or window not in WINDOWS or n<window
            or isinstance(stride,(bool,np.bool_)) or not isinstance(stride,Integral) or stride<1):
        raise ValueError('Declared supported rolling window and research cutoff required')
    endpoints=np.arange(window,n+1,stride,dtype=int)
    return np.append(endpoints,n) if endpoints[-1]!=n else endpoints
