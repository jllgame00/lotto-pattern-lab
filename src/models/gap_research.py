"""Transparent gap rules and exact logistic ranking audit terms."""
import numpy as np

from src.analysis.features import GAP
from src.models.predictive import FittedModel

GAP_DEFINITIONS = dict(
    current_gap='Observed draws since last main-number appearance; 0 if last draw; censored if never seen',
    has_appeared='1 if any main-number appearance observed in the training prefix, otherwise0',
    mean_gap='Mean of complete historical inter-appearance intervals in draws',
    median_gap='Median of complete historical inter-appearance intervals in draws',
    gap_std='Population standard deviation of complete intervals; needs at least2 intervals',
    gap_ratio='current_gap / mean_gap; missing if no complete historical interval')
HEURISTICS = ('largest','smallest','ratio','zscore','mean_reversion')


class GapHeuristic(FittedModel):
    def __init__(self,method='largest',seed=42):
        super().__init__(columns=GAP,seed=seed)
        if method not in HEURISTICS: raise ValueError('Unknown gap heuristic')
        self.method=method

    def fit(self,rows,*,cutoff):
        self._training(rows,cutoff)
        return self

    def score_rows(self,rows):
        self._current(rows)
        x=rows[GAP].to_numpy(dtype=float)
        x=np.where(np.isfinite(x),x,self.transformer.medians)
        gap,mean,std=x[:,0],x[:,2],x[:,4]
        ratio=np.divide(gap,mean,out=np.zeros_like(gap),where=mean>0)
        # Upcoming inter-appearance interval would be current absence +1.
        z=np.divide(gap+1-mean,std,out=np.zeros_like(gap),where=std>0)
        values=dict(largest=gap,smallest=-gap,ratio=ratio,zscore=z,mean_reversion=-np.abs(z))[self.method]
        return dict(zip(rows.number.astype(int),values.tolist()))

    def configuration(self):
        return dict(super().configuration(),method=self.method,z_definition='(current_gap+1-mean_gap)/gap_std',
                    missing='training median; zero score if denominator unsupported')


def coefficient_audit(model):
    scaler=model.transformer
    result=[]
    for i,feature in enumerate(scaler.numeric):
        value=float(model.coef[i])
        result.append(dict(feature=feature,definition=GAP_DEFINITIONS.get(feature,'Causal trailing104-draw periodicity/regime feature'),
                           training_cutoff=model.training_cutoff,training_rows=model.training_rows,
                           coefficient=value,sign=int(np.sign(value)),magnitude=abs(value),
                           raw_coefficient=value/float(scaler.scales[i]),
                           imputation_median=float(scaler.medians[i]),scaling_mean=float(scaler.means[i]),
                           scaling_std=float(scaler.scales[i]),intercept=float(model.coef[-1]),C=model.C))
    return result


def ranking_contributions(model,current):
    """Within-target variation of each additive logit term; no outcome used.

    Common intercept/constant terms cannot change number ranking. Correlated
    terms can cancel: these variabilities must not be added as independent skill.
    """
    terms=model.transformer.transform(current)*model.coef[:-1]
    total=terms.sum(axis=1)
    ranks=np.argsort(np.argsort(-total,kind='stable'),kind='stable')
    return [dict(target_draw=int(current.target_draw.iloc[0]),training_cutoff=model.training_cutoff,
                 feature=feature,cross_number_std=float(terms[:,i].std()),
                 mean_abs_rank_shift_without_term=float(np.abs(ranks-np.argsort(np.argsort(-(total-terms[:,i]),kind='stable'),kind='stable')).mean()),
                 contribution_min=float(terms[:,i].min()),contribution_max=float(terms[:,i].max()))
            for i,feature in enumerate(model.transformer.names)]
