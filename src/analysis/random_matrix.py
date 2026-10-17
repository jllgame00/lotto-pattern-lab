"""Constrained Lotto correlation/covariance and spectral geometry.

The structural direction of a correlation matrix is sample std, not ones.
All historical builders validate the complete supplied prefix before slicing.
"""
from numbers import Integral
import numpy as np
from .recurrence import research_matrix

WINDOWS=(104,208,416,624)
RANKS=(1,2,3,5)
LAGS=(1,2,4,8,13)
DEGENERATE_GAP=.05


def canonical_signs(vectors):
    v=np.asarray(vectors,float).copy()
    if v.ndim!=2 or not np.isfinite(v).all():
        raise ValueError('Finite column vectors required')
    if v.shape[1]:
        pivots=np.argmax(abs(v),axis=0)
        signs=np.where(v[pivots,np.arange(v.shape[1])]<0,-1.,1.)
        v*=signs
    return v


def participation(vectors):
    v=np.asarray(vectors,float)
    if v.ndim==1:v=v[:,None]
    if v.ndim!=2 or not np.isfinite(v).all():raise ValueError('Finite vectors required')
    norm=np.linalg.norm(v,axis=0)
    unit=np.divide(v,norm,out=np.zeros_like(v),where=norm>0)
    ipr=np.sum(unit**4,axis=0);ipr=np.where(norm>0,ipr,np.nan)
    return dict(ipr=ipr,pr=np.divide(1.,ipr,out=np.full_like(ipr,np.nan),where=ipr>0))


def spectrum_summary(eigenvalues):
    a=np.asarray(eigenvalues,float)
    if a.ndim!=1 or not np.isfinite(a).all() or (a < -1e-9).any():
        raise ValueError('Finite nonnegative spectrum required')
    a=np.maximum(a,0.);total=float(a.sum())
    p=a/total if total>0 else np.zeros_like(a)
    positive=p>0;entropy=float(-np.sum(p[positive]*np.log(p[positive])))
    return dict(entropy=entropy,effective_rank=float(np.exp(entropy)) if total>0 else 0.,
                cumulative_variance=np.cumsum(p),spacings=np.diff(np.sort(a)),trace=total)


def _basis(direction,active):
    """45-coordinate orthonormal basis perpendicular to the structural mode."""
    indices=np.flatnonzero(active);d=len(indices)
    if d<2:return np.empty((45,0))
    q=np.asarray(direction)[indices];q=q/np.linalg.norm(q)
    v=q.copy();v[0]+=1. # Positive constraint coordinates: stable Householder.
    householder=np.eye(d)-2*np.outer(v,v)/(v@v)
    b=np.zeros((45,d-1));b[indices]=householder[:,1:]
    return b


def _scaler(x):
    values=np.asarray(x,float);mean=values.mean(axis=0);centered=values-mean
    covariance=centered.T@centered/(len(values)-1)
    std=np.sqrt(np.maximum(np.diag(covariance),0.));active=std>1e-12
    standardized=np.divide(centered,std,out=np.zeros_like(centered),where=active)
    return mean,std,active,covariance,standardized


def fit_matrix(x,kind='correlation',cutoff=None):
    x=research_matrix(x)
    if cutoff is not None and (isinstance(cutoff,(bool,np.bool_)) or not isinstance(cutoff,Integral) or cutoff!=len(x)):
        raise ValueError('cutoff must equal the exact supplied historical prefix')
    if kind not in ('correlation','covariance'):raise ValueError('Only correlation/covariance are declared')
    mean,std,active,covariance,z=_scaler(x)
    matrix=z.T@z/(len(x)-1) if kind=='correlation' else covariance
    direction=std.copy() if kind=='correlation' else active.astype(float)
    norm=np.linalg.norm(direction);direction=direction/norm if norm else direction
    basis=_basis(direction,active)
    if basis.shape[1]:
        values,vectors=np.linalg.eigh(basis.T@matrix@basis)
        values=np.maximum(values[::-1],0.)
        vectors=canonical_signs(basis@vectors[:,::-1])
    else:values=np.empty(0);vectors=np.empty((45,0))
    return dict(kind=kind,draws=len(x),mean=mean,std=std,active=active,matrix=matrix,
        structural_direction=direction,structural_residual=float(np.linalg.norm(matrix@direction)),
        excluded_inactive=int((~active).sum()),nontrivial_dimension=len(values),
        eigenvalues=values,eigenvectors=vectors,**participation(vectors),**spectrum_summary(values))


def degenerate_groups(eigenvalues,tolerance=DEGENERATE_GAP):
    a=np.asarray(eigenvalues,float)
    if a.ndim!=1 or not np.isfinite(a).all() or tolerance<0:raise ValueError('Finite ordered values required')
    cuts=[0]
    for i in range(1,len(a)):
        if abs(a[i-1]-a[i])>tolerance*max(abs(a[i-1]),abs(a[i]),1e-15):cuts.append(i)
    cuts.append(len(a))
    return [(a,b) for a,b in zip(cuts,cuts[1:]) if b>a]


def align_modes(reference,candidate,eigenvalues):
    """Sign-align isolated vectors, Procrustes-align near-degenerate blocks.

    Use this only for displaying comparable bases. Inferential comparisons use
    projectors/principal angles; IPR of individual degenerate vectors depends
    on the numerical basis, so its signs/components have no semantic meaning.
    """
    a=np.asarray(reference,float);b=np.asarray(candidate,float)
    if a.ndim!=2 or a.shape!=b.shape or a.shape[1]!=len(eigenvalues) or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Aligned finite bases and spectrum required')
    out=b.copy()
    for start,end in degenerate_groups(eigenvalues):
        u,_,vt=np.linalg.svd(b[:,start:end].T@a[:,start:end],full_matrices=False)
        out[:,start:end]=b[:,start:end]@(u@vt)
    return out


def subspace_comparison(a,b,r):
    """Fixed-r geometry; degeneracy crossing the r/r+1 boundary can rotate it.

    Rotation inside the selected span and all sign flips leave this unchanged.
    Boundary degeneracy is a limitation, not proof of temporal instability.
    """
    a=np.asarray(a,float);b=np.asarray(b,float)
    if (a.ndim!=2 or b.ndim!=2 or a.shape[0]!=b.shape[0]
            or isinstance(r,(bool,np.bool_)) or not isinstance(r,Integral)
            or not 1<=r<=min(a.shape[1],b.shape[1])
            or not np.isfinite(a).all() or not np.isfinite(b).all()):
        raise ValueError('Supported rank and finite equal-coordinate bases required')
    qa=np.linalg.qr(a[:,:r],mode='reduced')[0];qb=np.linalg.qr(b[:,:r],mode='reduced')[0]
    singular=np.clip(np.linalg.svd(qa.T@qb,compute_uv=False),0.,1.)
    squared=float(np.sum(singular**2));overlap=float(np.clip(squared/r,0.,1.))
    return dict(rank=int(r),overlap=overlap,principal_angles=np.arccos(singular),
                projection_distance=float(np.sqrt(max(0.,2*r-2*squared))),
                aligned_leading_correlation=float(abs(qa[:,0]@qb[:,0])))


def rolling_endpoints(n,window,stride=104):
    if (isinstance(n,(bool,np.bool_)) or not isinstance(n,Integral) or not 2<=n<=1245
            or isinstance(window,(bool,np.bool_)) or not isinstance(window,Integral)
            or window not in WINDOWS or n<window or isinstance(stride,(bool,np.bool_))
            or not isinstance(stride,Integral) or stride<1):
        raise ValueError('Declared supported rolling window and historical cutoff required')
    ends=np.arange(window,n+1,stride,dtype=int)
    return np.append(ends,n) if ends[-1]!=n else ends


def lagged_spectrum(x,lag):
    x=research_matrix(x)
    if isinstance(lag,(bool,np.bool_)) or not isinstance(lag,Integral) or lag not in LAGS or len(x)-lag<3:
        raise ValueError('Declared lag and at least three aligned pairs required')
    lm,ls,la,_,left=_scaler(x[:-lag]);rm,rs,ra,_,right=_scaler(x[lag:])
    matrix=left.T@right/(len(left)-1)
    lb=_basis(ls,la);rb=_basis(rs,ra)
    if min(lb.shape[1],rb.shape[1]):
        u,s,vt=np.linalg.svd(lb.T@matrix@rb,full_matrices=False)
        u=lb@u;v=rb@vt.T
        signed=canonical_signs(u)
        flips=np.where(np.sum(signed*u,axis=0)<0,-1.,1.)
        u=signed;v=v*flips
    else:s=np.empty(0);u=np.empty((45,0));v=u.copy()
    return dict(lag=int(lag),pairs=len(left),matrix=matrix,singular_values=s,
        left_vectors=u,right_vectors=v,left_ipr=participation(u)['ipr'],right_ipr=participation(v)['ipr'],
        left_mean=lm,right_mean=rm,left_std=ls,right_std=rs,
        squared_concentration=np.array([float(np.sum(s[:r]**2)/np.sum(s**2)) if len(s)>=r and np.sum(s**2)>0 else np.nan for r in RANKS]))


def mp_reference(n,dimension,variance=1.,points=256):
    """Descriptive MP curve; no theoretical threshold is a significance test."""
    if n<2 or not 0<dimension<n or variance<=0:raise ValueError('Supported effective aspect ratio required')
    q=dimension/(n-1);low=variance*(1-np.sqrt(q))**2;high=variance*(1+np.sqrt(q))**2
    grid=np.linspace(low,high,points)
    density=np.divide(np.sqrt(np.maximum((high-grid)*(grid-low),0)),2*np.pi*q*variance*grid,
                      out=np.zeros_like(grid),where=grid>0)
    return dict(aspect_ratio=q,lower=float(low),upper=float(high),grid=grid,density=density,descriptive_only=True)
