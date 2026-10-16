"""Walk-forward HMM adapter; model parameters freeze, filtering updates causally."""
from src.models.bayesian import OnlineModel, observation_matrix
from src.models.bernoulli_hmm import BernoulliHMM


class HMMModel(OnlineModel):
    def __init__(self,*,states=2,window=260,max_iter=40,n_init=2,**kwargs):
        super().__init__(**kwargs)
        if window<104: raise ValueError('HMM window must be at least104')
        self.states,self.window,self.max_iter,self.n_init=states,window,max_iter,n_init

    def fit(self,rows,*,cutoff):
        self._training(rows,cutoff)
        if rows.target_draw.max()!=cutoff: raise ValueError('Online fit must end at cutoff')
        self.hmm=BernoulliHMM(states=self.states,max_iter=self.max_iter,n_init=self.n_init,seed=self.seed).fit(observation_matrix(rows)[-self.window:])
        self.observed_cutoff=cutoff
        return self

    def observe(self,y): self.hmm.observe(y)

    def score_rows(self,rows):
        self.advance(rows)
        return dict(zip(range(1,46),self.hmm.next_score().tolist()))

    def configuration(self):
        return dict(super().configuration(),states=self.states,window=self.window,max_iter=self.max_iter,n_init=self.n_init,
                    implementation_version=1,min_history=104,tolerance=1e-5,initial_state='uniform',
                    transition_pseudocounts='8 diagonal,1 off diagonal',emission_pseudocounts=[2,13],
                    state_labels=['cold','hot'] if self.states==2 else ['cold','neutral','hot'])
