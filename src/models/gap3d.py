"""Causal source-gap conditioning of the unchanged Phase6 model assumptions."""
import numpy as np
from src.analysis.gap3d import causal_states, GapEncoder
from src.analysis.gap3d_search import conditional_scores
from src.analysis.spatiotemporal import binary_matrix, aligned, P
from src.models.translation import TranslationModel


class GapConditionedTranslationModel(TranslationModel):
    def __init__(self, *, representation='quantile', min_support=None, **kwargs):
        super().__init__(**kwargs)
        if representation not in ('quantile', 'clipped', 'relative'):
            raise ValueError('Unknown predeclared gap representation')
        self.representation = representation
        self.min_support = (20 if self.chain else 100) if min_support is None else min_support
        if type(self.min_support) is not int or self.min_support < 1:
            raise ValueError('Positive integer support required')

    def fit(self, x, *, cutoff):
        x = binary_matrix(x); c = self.config
        if (type(cutoff) is not int or cutoff != len(x) or not c.min_history <= cutoff <= 1245 or
                cutoff <= c.max_dt or not np.all(x.sum(axis=1) == 6)):
            raise ValueError('Fit requires exactly the permitted training prefix')
        self.training = x.copy(); self.training_cutoff = cutoff
        g, _, r = causal_states(x)
        self.encoder = GapEncoder().fit(g[:-1], r[:-1], cutoff=cutoff)
        states = self.encoder.transform(g[:-1], r[:-1], self.representation)
        count = self.encoder.count(self.representation)
        if not self.chain:
            rows = conditional_scores(x, states, state_count=count, max_dt=c.max_dt,
                                      max_dn=c.max_dn, min_support=self.min_support).to_dict('records')
        else:
            rows = []
            for dt in range(c.min_dt, c.max_dt + 1):
                for dn in range(-c.max_dn, c.max_dn + 1):
                    if dn == 0: continue
                    a, z = aligned(x, dt, dn, 2)
                    if not a.size: continue
                    offset = max(0, -2 * dn)
                    b = x[dt:dt + len(a), offset + dn:offset + dn + a.shape[1]]
                    state = states[dt:dt + len(a), offset + dn:offset + dn + a.shape[1]]
                    eligible = a & b & (state >= 0)
                    opportunities = np.bincount(state[eligible], minlength=count)
                    matches = np.bincount(state[eligible & z], minlength=count)
                    rows.extend(dict(delta_draw=dt, delta_number=dn, gap_state=s,
                        valid_opportunities=int(opportunities[s]), matches=int(matches[s])) for s in range(count))
        candidates = []
        for row in rows:
            dt, dn = int(row['delta_draw']), int(row['delta_number'])
            if dt < c.min_dt or (c.direction == 'positive' and dn < 0) or (c.direction == 'negative' and dn > 0): continue
            opportunities, matches = int(row['valid_opportunities']), int(row['matches'])
            if opportunities < self.min_support: continue
            rate = (matches + c.prior_opportunities * P) / (opportunities + c.prior_opportunities)
            if rate > P:
                candidates.append(dict(delta_draw=dt, delta_number=dn, gap_state=int(row['gap_state']),
                    opportunities=opportunities, matches=matches, shrunk_rate=rate, weight=rate-P))
        self.rules = sorted(candidates, key=lambda r: (-r['weight'], r['delta_draw'], r['delta_number'], r['gap_state']))[:c.top_rules]
        return self

    def _context(self, x, target):
        x = binary_matrix(x)
        if (type(target) is not int or target != len(x)+1 or target > 1246 or target <= self.training_cutoff or
                not np.all(x.sum(axis=1) == 6) or not np.array_equal(x[:self.training_cutoff], self.training)):
            raise ValueError('Scoring requires unchanged fit prefix and strictly past observations')
        g, _, r = causal_states(x)
        return x, g, self.encoder.transform(g[:-1], r[:-1], self.representation)

    def _support(self, x, states, target):
        numerator = np.zeros(45); denominator = np.zeros(45)
        for rule in self.rules:
            dt, dn, w = rule['delta_draw'], rule['delta_number'], rule['weight']
            numbers = np.arange(45); source = numbers-dn
            valid = (source >= 0) & (source < 45) & (target-dt >= 1)
            if self.chain:
                older = numbers-2*dn
                valid &= (older >= 0) & (older < 45) & (target-2*dt >= 1)
            indices = numbers[valid]
            if not len(indices): continue
            present = x[target-dt-1, source[valid]] & (states[target-dt-1, source[valid]] == rule['gap_state'])
            if self.chain: present &= x[target-2*dt-1, older[valid]]
            numerator[indices] += w*present; denominator[indices] += w
        support = np.divide(numerator, denominator, out=np.zeros(45), where=denominator > 0)
        return {n+1: float(s) for n, s in enumerate(P+(1-P)*support)}, denominator

    def score_matrix(self, x, *, target):
        x, _, states = self._context(x, target)
        return self._support(x, states, target)[0]

    def explain_number(self, number, x, *, target):
        if type(number) is not int or not 1 <= number <= 45: raise ValueError('Number must be1..45')
        x, gaps, states = self._context(x, target)
        scores, denominator = self._support(x, states, target); diagnostics = []
        for rule in self.rules:
            dt, dn = rule['delta_draw'], rule['delta_number']; source = number-dn
            if not 1 <= source <= 45 or target-dt < 1: continue
            older = number-2*dn
            if self.chain and (not 1 <= older <= 45 or target-2*dt < 1): continue
            state = int(states[target-dt-1, source-1])
            active = bool(x[target-dt-1, source-1] and state == rule['gap_state'])
            if self.chain: active &= bool(x[target-2*dt-1, older-1])
            value = gaps[target-dt-1, source-1]
            diagnostics.append(dict(**rule, source_draw=target-dt, source_number=source,
                source_gap=None if np.isnan(value) else float(value), source_state=state, active=active,
                contribution=float((1-P)*rule['weight']*active/denominator[number-1])))
        return dict(number=number, target_draw=target, training_cutoff=self.training_cutoff,
                    score=scores[number], baseline=P, rules=diagnostics)

    def configuration(self):
        return dict(super().configuration(), version='phase7-gap3d-v1', representation=self.representation,
            min_support=self.min_support, destination_state_used=False,
            condition='most recent observed source pre-draw gap; never-seen excluded',
            state_version='pre-draw-gap-v1', bin_fit='training pre-states only; frozen between refits')


class GapConditionedChainModel(GapConditionedTranslationModel):
    chain = True
