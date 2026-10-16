"""Small independent Bernoulli HMMs, batched across numbers for speed.

Scaled forward/backward EM with fixed uniform initial probabilities. Transition
pseudocounts (8 diagonal,1 elsewhere) and emission pseudocounts (2,13) regularize
MAP fitting. Predictive state estimates always use forward filtering, not smoothing.
"""
import numpy as np


def _forward(x,a,p,pi):
    emission=np.where(x[:,:,None]==1,p[None,:,:],1-p[None,:,:])
    filtered=np.empty_like(emission); scales=np.empty(x.shape)
    for t in range(len(x)):
        prior=pi if t==0 else np.einsum('ni,nij->nj',filtered[t-1],a)
        value=prior*emission[t]
        scales[t]=value.sum(axis=1)
        filtered[t]=value/scales[t,:,None]
    return filtered,scales,emission


def forward_filter(sequence,transition,emissions,initial=None):
    x=np.asarray(sequence,dtype=float); a=np.asarray(transition,float); p=np.asarray(emissions,float)
    s=len(p); pi=np.full(s,1/s) if initial is None else np.asarray(initial,float)
    if (x.ndim!=1 or not len(x) or not np.isin(x,[0,1]).all() or a.shape!=(s,s) or
            np.any(a<0) or not np.allclose(a.sum(1),1) or np.any((p<=0)|(p>=1)) or
            pi.shape!=(s,) or np.any(pi<0) or not np.isclose(pi.sum(),1)):
        raise ValueError('Invalid Bernoulli HMM inputs')
    f,c,_=_forward(x[:,None],a[None],p[None],pi[None])
    return f[:,0],float(np.log(c).sum())


class BernoulliHMM:
    def __init__(self,*,states=2,max_iter=40,n_init=2,seed=42,min_history=104,tol=1e-5):
        if states not in (2,3) or min(max_iter,n_init,min_history)<1 or tol<=0:
            raise ValueError('Invalid small HMM configuration')
        self.states,self.max_iter,self.n_init,self.seed,self.min_history,self.tol=states,max_iter,n_init,seed,min_history,tol

    def fit(self,sequence):
        x=np.asarray(sequence,dtype=float)
        if x.ndim==1: x=x[:,None]
        if x.ndim!=2 or len(x)<self.min_history or not np.isin(x,[0,1]).all():
            raise ValueError('Insufficient history or non-binary HMM observations')
        n=x.shape[1]; s=self.states; rng=np.random.default_rng(self.seed)
        pi=np.full((n,s),1/s); pseudo=np.ones((s,s))+7*np.eye(s)
        best=np.full(n,-np.inf); self.initializations=[]
        self.transitions=np.empty((n,s,s)); self.emissions=np.empty((n,s))
        self.iterations=np.zeros(n,int); self.converged=np.zeros(n,bool)
        for initialization in range(self.n_init):
            a=np.broadcast_to(pseudo/pseudo.sum(1)[:,None],(n,s,s)).copy()
            base=np.linspace(.05,.25,s)[None,:]
            p=np.clip(base+rng.normal(0,.025,(n,s)),.01,.5)
            previous=None; converged=np.zeros(n,bool)
            for iteration in range(self.max_iter):
                f,c,e=_forward(x,a,p,pi)
                objective=np.log(c).sum(0)+(pseudo*np.log(a)).sum((1,2))+(2*np.log(p)+13*np.log1p(-p)).sum(1)
                if previous is not None:
                    converged=np.abs(objective-previous)<self.tol*(1+np.abs(previous))
                    if converged.all(): break
                previous=objective
                backward=np.ones_like(f); transitions=np.zeros_like(a)
                for t in range(len(x)-2,-1,-1):
                    term=e[t+1]*backward[t+1]
                    backward[t]=np.einsum('nij,nj->ni',a,term)/c[t+1,:,None]
                    transitions+=f[t,:,:,None]*a*term[:,None,:]/c[t+1,:,None,None]
                gamma=f*backward; gamma/=gamma.sum(2,keepdims=True)
                counts=transitions+pseudo
                a=counts/counts.sum(2,keepdims=True)
                p=np.clip((np.einsum('tns,tn->ns',gamma,x)+2)/(gamma.sum(0)+15),1e-6,1-1e-6)
            f,c,_=_forward(x,a,p,pi)
            objective=np.log(c).sum(0)+(pseudo*np.log(a)).sum((1,2))+(2*np.log(p)+13*np.log1p(-p)).sum(1)
            self.initializations.append(dict(initialization=initialization,objective=objective.tolist(),
                log_likelihood=np.log(c).sum(0).tolist(),emissions=np.sort(p,axis=1).tolist(),
                converged=converged.tolist(),iterations=iteration+1))
            for j in range(n):
                if objective[j]>best[j]:
                    order=np.argsort(p[j]); self.emissions[j]=p[j,order]
                    self.transitions[j]=a[j][np.ix_(order,order)]
                    self.iterations[j]=iteration+1; self.converged[j]=converged[j]; best[j]=objective[j]
        self.filtered,c,_=_forward(x,self.transitions,self.emissions,pi)
        self.log_likelihood=np.log(c).sum(0)
        self.state=self.filtered[-1].copy()
        self.objective=best
        return self

    def observe(self,y):
        y=np.asarray(y,float)
        if y.shape!=(len(self.state),) or not np.isin(y,[0,1]).all(): raise ValueError('Invalid observation')
        prior=np.einsum('ni,nij->nj',self.state,self.transitions)
        state=prior*np.where(y[:,None]==1,self.emissions,1-self.emissions)
        self.state=state/state.sum(1,keepdims=True)

    def next_score(self):
        return np.einsum('ni,nij,nj->n',self.state,self.transitions,self.emissions)
