"""H24 small interpretable alphabets and causal fixed-depth Markov arithmetic."""
import numpy as np
from .recurrence import research_matrix
from .optimal_transport import draw_positions

ALPHAS=(.5,1.)
LAGS=(1,2,3,4,8,13,26)
FIT_END=200
CONTEXT_SUPPORT=20


def deterministic_symbols(draws):
    a=np.asarray(draws,int)
    low=(a<=22).sum(1);center=(a==23).sum(1)
    bands=np.array([((a>=lo)&(a<=lo+8)).sum(1) for lo in (1,10,19,28,37)]).T
    return dict(parity=(a%2).sum(1),balance=center*7+low,
                band=bands.argmax(1)*2+(bands.max(1)>=3).astype(int))


def encode_all(x):
    x=research_matrix(x)
    if len(x)<=FIT_END:raise ValueError('Symbol analysis starts at201 after200 calibration draws')
    a=draw_positions(x);fixed=deterministic_symbols(a);out={}
    for name,A in [('parity',7),('balance',13),('band',10)]:
        out[name]=dict(symbols=fixed[name][FIT_END:],alphabet=A,boundaries=[],first_draw=201,fit_end=200)
    raw=dict(sum=a.sum(1),range=np.ptp(a,axis=1),spacing=np.var(np.diff(a,axis=1),axis=1))
    for name in ('sum','range'):
        for q in (3,4):
            edges=np.quantile(raw[name][:FIT_END],np.arange(1,q)/q)
            out[f'{name}{q}']=dict(symbols=np.searchsorted(edges,raw[name][FIT_END:],side='right'),
                alphabet=q,boundaries=edges.tolist(),first_draw=201,fit_end=200)
    edges=np.quantile(raw['spacing'][:FIT_END],[1/3,2/3])
    spacing=2*np.searchsorted(edges,raw['spacing'][FIT_END:],side='right')+(np.diff(a[FIT_END:],axis=1)==1).any(1)
    out['spacing']=dict(symbols=spacing.astype(int),alphabet=6,boundaries=edges.tolist(),first_draw=201,fit_end=200)
    return {name:out[name] for name in ('parity','balance','sum3','sum4','range3','range4','spacing','band')}


def valid_sequence(s,A):
    a=np.asarray(s)
    if a.ndim!=1 or not len(a) or type(A) is not int or A<2 or not np.isin(a,np.arange(A)).all():
        raise ValueError('Declared finite alphabet and nonempty integer sequence required')
    return a.astype(int,copy=False)


def entropy_counts(counts):
    c=np.asarray(counts,float);total=c.sum()
    p=c[c>0]/total if total else np.empty(0)
    return float(-np.sum(p*np.log2(p)))


def support_audit(s,A):
    s=valid_sequence(s,A);c=np.bincount(s,minlength=A);H=entropy_counts(c)
    return dict(alphabet_size=A,observed_symbols=int((c>0).sum()),counts=c.tolist(),minimum_support=int(c.min()),
        rare_symbols=np.flatnonzero(c<5).tolist(),marginal_entropy=H,effective_alphabet=float(2**H),
        expected_order0_counts=(len(s)*c/len(s)).tolist(),rare_threshold=5)


def word_codes(s,A,length):
    s=valid_sequence(s,A)
    if not 1<=length<=4 or length>len(s):raise ValueError('Word length1..4 within sequence required')
    code=np.zeros(len(s)-length+1,dtype=int)
    for offset in range(length):code=code*A+s[offset:offset+len(code)]
    return code


def all_words(A,length):
    codes=np.arange(A**length);words=np.empty((len(codes),length),int)
    for j in range(length-1,-1,-1):words[:,j]=codes%A;codes//=A
    return words


def transition_probabilities(s,A,k=1,alpha=1.):
    s=valid_sequence(s,A)
    if k not in (0,1,2,3) or alpha<=0:raise ValueError('Order0..3 and positive smoothing required')
    counts=np.bincount(word_codes(s,A,k+1),minlength=A**(k+1)).reshape(A**k,A)
    return (counts+alpha)/(counts.sum(1,keepdims=True)+alpha*A)


def conditional_entropy(s,A,k):
    s=valid_sequence(s,A)
    if k==0:return entropy_counts(np.bincount(s,minlength=A))
    counts=np.bincount(word_codes(s,A,k+1),minlength=A**(k+1)).reshape(A**k,A)
    row=counts.sum(1);total=row.sum();nz=counts>0
    probs=np.divide(counts,row[:,None],out=np.zeros_like(counts,float),where=row[:,None]>0)
    return float(-np.sum(counts[nz]/total*np.log2(probs[nz])))


def previous_counts(ids):
    # Stable occurrence rank is the count strictly BEFORE each index, even though
    # implemented with a vectorized sort. Appending/changing future cannot affect it.
    ids=np.asarray(ids,int);order=np.argsort(ids,kind='stable');sorted_ids=ids[order]
    index=np.arange(len(ids));starts=np.maximum.accumulate(np.where(np.r_[True,sorted_ids[1:]!=sorted_ids[:-1]],index,0))
    counts=np.empty(len(ids),int);counts[order]=index-starts
    return counts


def prequential_losses(s,A,*,min_support=CONTEXT_SUPPORT):
    s=valid_sequence(s,A);n=len(s);loss=np.empty((n,4,2))
    probabilities=np.empty((n,4,2));counts0=previous_counts(s)
    for ai,alpha in enumerate(ALPHAS):probabilities[:,0,ai]=(counts0+alpha)/(np.arange(n)+alpha*A)
    for k in (1,2,3):
        context=np.zeros(n-k,int)
        for offset in range(k):context=context*A+s[offset:offset+n-k]
        total=previous_counts(context);target=previous_counts(context*A+s[k:])
        probabilities[:,k]=probabilities[:,k-1]
        for ai,alpha in enumerate(ALPHAS):
            candidate=(target+alpha)/(total+alpha*A)
            probabilities[k:,k,ai]=np.where(total>=min_support,candidate,probabilities[k:,k-1,ai])
    loss[:]=-np.log(probabilities)
    return loss


def bic(s,A,k):
    n=len(s)-k;H=conditional_entropy(s,A,k)
    return float(2*n*H*np.log(2)+A**k*(A-1)*np.log(n))


def select_order(s,A,split):
    s=valid_sequence(s,A)
    if not 4<=split<len(s):raise ValueError('Chronological train/validation split required')
    losses=prequential_losses(s,A);means=losses[split:].mean(0);bics=[bic(s[:split],A,k) for k in range(4)]
    # Prefer alpha1 on exact ties, and the simplest order absent clear improvement.
    best_alpha=[min(range(2),key=lambda ai:(means[k,ai],-ALPHAS[ai])) for k in range(4)]
    chosen=0
    for k in (1,2,3):
        if means[chosen,best_alpha[chosen]]-means[k,best_alpha[k]]>.01 and bics[k]<bics[chosen]:chosen=k
    lower=min(means[j,best_alpha[j]] for j in range(chosen)) if chosen else means[0,best_alpha[0]]
    return dict(order=chosen,alpha=ALPHAS[best_alpha[chosen]],loss=float(means[chosen,best_alpha[chosen]]),
        gain_order0=float(means[0,best_alpha[0]]-means[chosen,best_alpha[chosen]]),
        gain_lower=float(lower-means[chosen,best_alpha[chosen]]),bic=bics,
        losses=means.tolist(),split=int(split),validation_rows=len(s)-split)


def transition_diagnostic(s,A):
    s=valid_sequence(s,A);c=np.bincount(word_codes(s,A,2),minlength=A*A).reshape(A,A)
    source=c.sum(1);destination=c.sum(0);expected=source[:,None]*destination[None,:]/c.sum()
    active=(source[:,None]>=20)&(destination[None,:]>=5)&(expected>=5)
    residual=np.divide(c-expected,np.sqrt(expected),out=np.zeros_like(expected),where=expected>0)
    up=np.where(active,residual,-np.inf);down=np.where(active,-residual,-np.inf)
    def leader(v):
        if not active.any():return dict(value=0.,source=None,destination=None,count=0,expected=0.)
        i,j=np.unravel_index(np.argmax(v),v.shape)
        return dict(value=float(v[i,j]),source=int(i),destination=int(j),count=int(c[i,j]),expected=float(expected[i,j]))
    p=transition_probabilities(s,A)
    return dict(counts=c,expected=expected,residual=residual,supported=active,
        positive=leader(up),negative=leader(down),entropy=np.array([entropy_counts(row) for row in c]),
        concentration=p.max(1),probabilities=p)


def word_diagnostic(s,A,length):
    s=valid_sequence(s,A);words=all_words(A,length)
    counts=np.bincount(word_codes(s,A,length),minlength=A**length)
    p=(np.bincount(s,minlength=A)+.5)/(len(s)+.5*A)
    if length==2:prob=np.prod(p[words],axis=1)
    else:
        matrix=transition_probabilities(s,A,1,.5);prob=p[words[:,0]].copy()
        for j in range(1,length):prob*=matrix[words[:,j-1],words[:,j]]
    expected=(len(s)-length+1)*prob
    prefix=np.bincount(word_codes(s,A,length-1)[:-1],minlength=A**(length-1))
    active=(expected>=5)&(prefix[np.arange(A**length)//A]>=10)
    deviance=2*(np.where(counts>0,counts*np.log(np.maximum(counts,1)/np.maximum(expected,1e-12)),0)-(counts-expected))
    residual=np.sign(counts-expected)*np.sqrt(np.maximum(deviance,0))
    missing=active&(counts==0);rare=active&(counts<=1)
    def leader(sign):
        if not active.any():return dict(value=0.,word=[],count=0,expected=0.,lift=0.)
        i=int(np.argmax(np.where(active,sign*residual,-np.inf)))
        return dict(value=float(sign*residual[i]),word=words[i].tolist(),count=int(counts[i]),
            expected=float(expected[i]),lift=float(counts[i]/expected[i]))
    return dict(length=length,words=words,counts=counts,expected=expected,supported=active,residual=residual,
        positive=leader(1),negative=leader(-1),eligible=int(active.sum()),
        missing_max_expected=float(expected[missing].max()) if missing.any() else 0.,
        missing_fraction=float(missing.sum()/active.sum()) if active.any() else 0.,
        rare_max_expected=float(expected[rare].max()) if rare.any() else 0.,
        missing_count=int(missing.sum()),rare_count=int(rare.sum()))


def run_diagnostic(s,A):
    s=valid_sequence(s,A);starts=np.r_[0,np.flatnonzero(s[1:]!=s[:-1])+1];lengths=np.diff(np.r_[starts,len(s)])
    longest=int(lengths.max());p=np.bincount(s,minlength=A)/len(s);stay=np.diag(transition_probabilities(s,A,1,.5))
    m=len(s)-longest
    expected0=np.sum(p**longest*(1+m*(1-p)))
    expected1=np.sum(p*stay**(longest-1)*(1+m*(1-stay)))
    away=float(np.mean(s[1:]!=s[:-1]));away0=1-float(np.sum(p*p))
    return dict(lengths=lengths,longest=longest,order0_surprise=float(-np.log(max(expected0,1e-12))),
        order1_surprise=float(-np.log(max(expected1,1e-12))),away=away,away_expected_order0=away0,
        away_gap=abs(away-away0),expected_runs_order0=float(expected0),expected_runs_order1=float(expected1))


def symbolic_lag(s,A,lag):
    s=valid_sequence(s,A)
    if not 1<=lag<len(s):raise ValueError('Lag outside sequence')
    p=np.bincount(s,minlength=A)/len(s)
    return float(np.mean(s[:-lag]==s[lag:])-np.sum(p*p))
