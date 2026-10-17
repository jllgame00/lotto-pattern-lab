"""Transparent joint-state propensity and causal translational models."""
import numpy as np
from src.analysis.joint_state import JointEncoder,LABELS
from src.analysis.joint_search import parent_controls
from src.analysis.frequency_search import conditional_frequency
from src.analysis.spatiotemporal import binary_matrix,aligned,P
from src.models.translation import TranslationModel

def _fit_prefix(x,cutoff,min_history=104):
    x=binary_matrix(x)
    if type(cutoff) is not int or cutoff!=len(x) or not min_history<=cutoff<=1245 or not np.all(x.sum(axis=1)==6):
        raise ValueError('Exact bounded training prefix and six main numbers per row required')
    return x

def _past(model,x,target):
    x=binary_matrix(x)
    if (type(target) is not int or target!=len(x)+1 or target>1246 or target<=model.training_cutoff or
        not np.all(x.sum(axis=1)==6) or not np.array_equal(x[:model.training_cutoff],model.training)):
        raise ValueError('Scoring requires unchanged fitted prefix and observations strictly before target')
    return x,model.encoder.transform(x)

def _chain_training(x,states,config):
    rows=[]
    for dt in range(config.min_dt,config.max_dt+1):
        for dn in range(-config.max_dn,config.max_dn+1):
            if not dn:continue
            a,z=aligned(x,dt,dn,2)
            if not a.size:continue
            offset=max(0,-2*dn);b=x[dt:dt+len(a),offset+dn:offset+dn+a.shape[1]]
            sa=aligned(states,dt,dn,2)[0];sb=states[dt:dt+len(a),offset+dn:offset+dn+a.shape[1]]
            base=a&b&(sa>=0)&(sb>=0);joint=base&(sa==sb)
            n=np.bincount(sb[joint],minlength=9);k=np.bincount(sb[joint&z],minlength=9)
            gap=base&(sa//3==sb//3);frequency=base&(sa%3==sb%3)
            gn=np.bincount(sb[gap]//3,minlength=3);gk=np.bincount(sb[gap&z]//3,minlength=3)
            fn=np.bincount(sb[frequency]%3,minlength=3);fk=np.bincount(sb[frequency&z]%3,minlength=3)
            for state in range(9):
                row=dict(delta_draw=dt,delta_number=dn,state=state,valid_opportunities=int(n[state]),matches=int(k[state]))
                for label,opps,hits in [('unconditional',int(base.sum()),int((base&z).sum())),
                    ('gap',int(gn[state//3]),int(gk[state//3])),('frequency',int(fn[state%3]),int(fk[state%3]))]:
                    row.update({label+'_opportunities':opps,label+'_matches':hits,
                        label+'_shrunk_rate':(hits+config.prior_opportunities*P)/(opps+config.prior_opportunities)})
                rows.append(row)
    return rows

class JointStateTranslationModel(TranslationModel):
    def __init__(self,*,min_support=None,**kwargs):
        super().__init__(**kwargs);self.min_support=(20 if self.chain else 100) if min_support is None else min_support
        if type(self.min_support) is not int or self.min_support<1:raise ValueError('Positive support required')

    def fit(self,x,*,cutoff):
        x=_fit_prefix(x,cutoff,self.config.min_history)
        if cutoff<=self.config.max_dt:raise ValueError('Shift range exceeds training history')
        self.training=x.copy();self.training_cutoff=cutoff;self.encoder=JointEncoder().fit(x,cutoff=cutoff)
        states=self.encoder.transform(x)['joint_state'][:-1];c=self.config
        if self.chain:rows=_chain_training(x,states,c)
        else:rows=parent_controls(conditional_frequency(x,states,state_count=9,max_dt=c.max_dt,max_dn=c.max_dn,
            min_support=self.min_support),prior=c.prior_opportunities,min_support=self.min_support).to_dict('records')
        rules=[]
        for row in rows:
            dt,dn=int(row['delta_draw']),int(row['delta_number']);n,k=int(row['valid_opportunities']),int(row['matches']);state=int(row['state'])
            if not dn or dt<c.min_dt or n<self.min_support or (c.direction=='positive' and dn<0) or (c.direction=='negative' and dn>0):continue
            rate=(k+c.prior_opportunities*P)/(n+c.prior_opportunities)
            if rate<=P:continue
            rule=dict(delta_draw=dt,delta_number=dn,joint_state=state,gap_state=state//3,frequency_state=state%3,
                label=LABELS[state],opportunities=n,matches=k,shrunk_rate=rate,weight=rate-P)
            for label in ('unconditional','gap','frequency'):
                for suffix in ('opportunities','matches','shrunk_rate'):rule[label+'_'+suffix]=row[label+'_'+suffix]
            rule['interaction_lift']=rate/max(rule['gap_shrunk_rate'],rule['frequency_shrunk_rate'])-1
            rules.append(rule)
        self.rules=sorted(rules,key=lambda r:(-r['weight'],r['delta_draw'],r['delta_number'],r['joint_state']))[:c.top_rules]
        return self

    def _support(self,x,states,target):
        numerator=np.zeros(45);denominator=np.zeros(45)
        for rule in self.rules:
            dt,dn,w=rule['delta_draw'],rule['delta_number'],rule['weight'];numbers=np.arange(45);source=numbers-dn
            valid=(source>=0)&(source<45)&(target-dt>=1)
            if self.chain:
                older=numbers-2*dn;valid &= (older>=0)&(older<45)&(target-2*dt>=1)
            indices=numbers[valid]
            if not len(indices):continue
            state=rule['joint_state'];present=x[target-dt-1,source[valid]]&(states[target-dt-1,source[valid]]==state)
            if self.chain:present &= x[target-2*dt-1,older[valid]]&(states[target-2*dt-1,older[valid]]==state)
            numerator[indices]+=w*present;denominator[indices]+=w
        support=np.divide(numerator,denominator,out=np.zeros(45),where=denominator>0)
        return {n+1:float(v) for n,v in enumerate(P+(1-P)*support)},denominator

    def score_matrix(self,x,*,target):
        x,f=_past(self,x,target)
        return self._support(x,f['joint_state'][:-1],target)[0]

    def explain_number(self,number,x,*,target):
        if type(number) is not int or not 1<=number<=45:raise ValueError('Number must be1..45')
        x,f=_past(self,x,target);states=f['joint_state'][:-1];scores,denominator=self._support(x,states,target);rows=[]
        for rule in self.rules:
            dt,dn=rule['delta_draw'],rule['delta_number'];source=number-dn;older=number-2*dn
            if not 1<=source<=45 or target-dt<1:continue
            if self.chain and (not 1<=older<=45 or target-2*dt<1):continue
            active=bool(x[target-dt-1,source-1] and states[target-dt-1,source-1]==rule['joint_state'])
            if self.chain:active &= bool(x[target-2*dt-1,older-1] and states[target-2*dt-1,older-1]==rule['joint_state'])
            rows.append(dict(**rule,source_draw=target-dt,source_number=source,
                active=active,contribution=float((1-P)*rule['weight']*active/denominator[number-1])))
        return dict(number=number,target_draw=target,training_cutoff=self.training_cutoff,score=scores[number],baseline=P,rules=rows)

    def configuration(self):
        return dict(super().configuration(),version='phase9-joint4dstate-v1',window=26,representation='joint_quantile',
            min_support=self.min_support,destination_state_used=False,state_version='pre-draw-joint-v1',
            condition='two same-joint-state observed predecessors' if self.chain else 'observed source pre-draw joint state',
            bin_fit='both training pre-state encoders only; frozen between refits',continuous_4d_search=False)

class JointStateChainModel(JointStateTranslationModel):
    chain=True

class JointStateFrequencyBaseline:
    def __init__(self,*,min_support=100,prior_opportunities=100.):
        if type(min_support) is not int or min_support<1 or not np.isfinite(prior_opportunities) or prior_opportunities<=0:raise ValueError('Positive support/prior required')
        self.min_support=min_support;self.prior=prior_opportunities

    def fit(self,x,*,cutoff):
        x=_fit_prefix(x,cutoff);self.training=x.copy();self.training_cutoff=cutoff;self.encoder=JointEncoder().fit(x,cutoff=cutoff)
        state=self.encoder.transform(x)['joint_state'][:-1];known=state>=0
        self.observations=np.bincount(state[known],minlength=9);self.positives=np.bincount(state[known&x],minlength=9)
        self.posterior=np.where(self.observations>=self.min_support,(self.positives+self.prior*P)/(self.observations+self.prior),P)
        return self

    def score_matrix(self,x,*,target):
        _,f=_past(self,x,target);states=f['joint_state'][-1]
        return {n+1:float(self.posterior[s]) if s>=0 else P for n,s in enumerate(states)}

    def explain_number(self,number,x,*,target):
        if type(number) is not int or not 1<=number<=45:raise ValueError('Number must be1..45')
        _,f=_past(self,x,target);state=int(f['joint_state'][-1,number-1]);score=self.score_matrix(x,target=target)[number]
        return dict(number=number,target_draw=target,training_cutoff=self.training_cutoff,joint_state=state,
            label=LABELS[state] if state>=0 else 'MISSING',observations=int(self.observations[state]) if state>=0 else 0,
            positives=int(self.positives[state]) if state>=0 else 0,score=score)

    def configuration(self):
        return dict(model=type(self).__name__,version='phase9-joint4dstate-v1',window=26,representation='joint_quantile',
            min_history=104,min_support=self.min_support,prior_opportunities=self.prior,state_version='pre-draw-joint-v1',
            condition='current causal joint-state appearance propensity; no translation geometry',
            bin_fit='both training pre-state encoders only; frozen between refits',continuous_4d_search=False)
