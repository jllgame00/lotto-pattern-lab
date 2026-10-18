"""Exchangeable peer-only normalization and empirically calibrated meta-scores.

The pool consists of real+199 null histories. Every scored row references the
OTHER199: real sees all nulls, each null sees real+198 other nulls. No row sees
itself; this symmetric transformation permits Monte Carlo ranking of meta-scores.
"""
import numpy as np
from scipy.stats import rankdata

SCORES=('FamilyMax','SumOfAnomalies','HigherCriticism')


def leave_self_out(values,orientations):
    a=np.asarray(values,float)
    if a.ndim!=2 or len(a)<4 or a.shape[1]!=len(orientations) or not np.isfinite(a).all():
        raise ValueError('At least4 finite history vectors and matching orientations required')
    directions=np.asarray(orientations)
    if not np.isin(directions,['upper','lower','two_sided']).all():raise ValueError('Unknown anomaly orientation')
    centers=np.empty_like(a);scales=np.empty_like(a);z=np.empty_like(a)
    for i in range(len(a)):
        peers=np.concatenate((a[:i],a[i+1:]),axis=0)
        center=np.median(peers,axis=0);mad=1.4826*np.median(abs(peers-center),axis=0)
        std=peers.std(axis=0,ddof=1)
        scale=np.where(mad>1e-12,mad,np.where(std>1e-12,std,1.))
        signed=(a[i]-center)/scale
        z[i]=np.where(directions=='two_sided',abs(signed),np.where(directions=='lower',-signed,signed))
        centers[i]=center;scales[i]=scale
    # Inclusive ranks equal (1+peer tail count)/pool_size. Max/min ranks handle
    # all ties conservatively and retain equal reference sizes for every row.
    upper=(len(a)-rankdata(a,axis=0,method='min')+1)/len(a)
    lower=rankdata(a,axis=0,method='max')/len(a)
    p=np.where(directions[None,:]=='two_sided',np.minimum(1.,2*np.minimum(upper,lower)),
        np.where(directions[None,:]=='lower',lower,upper))
    return dict(z=z,p=p,center=centers,scale=scales,pool_size=len(a),peer_count=len(a)-1,
        method='Augmented exchangeable pool, leave scored row out; inclusive conservative ranks')


def family_weights(families):
    families=np.asarray(families)
    if families.ndim!=1 or not len(families):raise ValueError('Nonempty family labels required')
    names=list(dict.fromkeys(families.tolist()))
    counts={name:int(np.sum(families==name)) for name in names}
    return np.array([1/(len(names)*counts[f]) for f in families])


def sum_anomalies(z,families):
    return float(np.dot(family_weights(families),np.clip(np.asarray(z)-1,0,4)))


def higher_criticism(p,weights=None):
    p=np.asarray(p,float)
    if p.ndim!=1 or not len(p) or not np.isfinite(p).all() or np.any((p<=0)|(p>1)):
        raise ValueError('Empirical p-values in(0,1] required')
    w=np.full(len(p),1/len(p)) if weights is None else np.asarray(weights,float)
    if w.shape!=p.shape or np.any(w<=0) or not np.isclose(w.sum(),1):raise ValueError('Normalized positive unit weights required')
    order=np.argsort(p,kind='stable');sorted_p=p[order];cdf=np.cumsum(w[order])
    # Entire mass of tied p is included before evaluating its empirical CDF.
    eligible=np.r_[sorted_p[:-1]!=sorted_p[1:],True]&(sorted_p<=.5)
    pp=sorted_p[eligible];ff=cdf[eligible];effective=1/np.sum(w*w)
    curve=np.sqrt(effective)*(ff-pp)/np.sqrt(pp*(1-pp))
    winner=int(np.argmax(curve)) if len(curve) else None
    score=max(0.,float(curve[winner])) if winner is not None else 0.
    return dict(score=score,threshold=float(pp[winner]) if winner is not None and score>0 else None,
        effective_units=float(effective),p_grid=pp,cdf=ff,curve=curve)


def meta_scores(z,p,families):
    z=np.asarray(z,float);p=np.asarray(p,float);families=np.asarray(families)
    if z.shape!=p.shape or z.ndim!=2 or z.shape[1]!=len(families):raise ValueError('Matching history/unit arrays required')
    names=list(dict.fromkeys(families.tolist()));weights=family_weights(families)
    family_max=np.column_stack([z[:,families==name].max(1) for name in names])
    scores=np.empty((len(z),3));hc=[]
    scores[:,0]=family_max.max(1)
    scores[:,1]=np.clip(z-1,0,4)@weights
    for i in range(len(z)):
        found=higher_criticism(p[i],weights);hc.append(found);scores[i,2]=found['score']
    return dict(scores=scores,score_names=list(SCORES),family_names=names,family_max=family_max,
        weights=weights,hc=hc,threshold=1.,cap=4.)


def compare_scores(scores):
    scores=np.asarray(scores,float)
    if scores.ndim!=2 or scores.shape[1]!=3 or not np.isfinite(scores).all():raise ValueError('Three finite omnibus columns required')
    out=[]
    for j,name in enumerate(SCORES):
        null=scores[1:,j];observed=scores[0,j]
        p=(1+int(np.sum(null>=observed)))/len(scores)
        out.append(dict(score=name,real=float(observed),null_median=float(np.median(null)),
            global_p=p,track_adjusted_p=min(1.,3*p),overall_adjusted_p=min(1.,6*p),replicates=len(null)))
    return out


def leave_one_family_out(z,p,families):
    families=np.asarray(families);names=list(dict.fromkeys(families.tolist()));out={}
    for name in names:
        mask=families!=name
        m=meta_scores(np.asarray(z)[:,mask],np.asarray(p)[:,mask],families[mask]);comparison=compare_scores(m['scores'])
        for row in comparison:row['leaveout_scan_adjusted_p']=min(1.,3*len(names)*row['global_p'])
        out[name]=dict(scores=m['scores'],comparison=comparison,remaining_families=m['family_names'])
    return out


def scientific_status(comparison):
    full=[r for r in comparison if r.get('scope')=='full']
    if any(r['overall_adjusted_p']<=.05 and r['track']=='fixed_margins' for r in full):
        return 'EVIDENCE OF TEMPORAL/RELATIONAL STRUCTURE'
    if any(r['overall_adjusted_p']<=.05 and r['track']=='iid' for r in full):return 'EVIDENCE AGAINST IID RANDOMNESS'
    return 'TESTED / INCONCLUSIVE'
