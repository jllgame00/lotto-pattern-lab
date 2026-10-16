"""Ticket metrics and conservative, explicitly approximate uncertainty summaries."""
from math import comb

import numpy as np
import pandas as pd


def random_expectation() -> dict:
    probabilities = {n: comb(6, n) * comb(39, 6-n) / comb(45, 6) for n in range(7)}
    return dict(average_matches=36/45, match_probabilities=probabilities,
                **{f"rate_{k}_plus": sum(probabilities[n] for n in range(k,7)) for k in (3,4,5)})


def summarize(results: pd.DataFrame, seed: int = 42, bootstrap_samples: int = 2000) -> dict:
    if results.empty:
        raise ValueError("Cannot summarize empty results")
    if bootstrap_samples < 100:
        raise ValueError("Use at least 100 bootstrap samples")
    if results.model.nunique() != 1:
        raise ValueError("Summarize one model at a time")
    matches = results.matches
    if not matches.isin(range(7)).all():
        raise ValueError("Match counts must be integers in 0..6")
    per_draw = results.groupby("target_draw").matches.mean().to_numpy()
    warnings = ["Exploratory baseline evaluation; no predictive performance established.",
                "CI resamples target draws, keeping repeated tickets together. It assumes independent draws; "
                "future adaptive strategies may require a temporal block bootstrap.",
                "Best ticket depends on ticket count. Repeated tickets are not additional historical draws."]
    if len(per_draw) < 30:
        warnings.append("Small sample: fewer than 30 unique target draws; confidence interval is unstable.")
    ci = None
    if len(per_draw) >= 2:
        rng = np.random.default_rng(seed)
        means = [float(rng.choice(per_draw, size=len(per_draw), replace=True).mean())
                 for _ in range(bootstrap_samples)]
        ci = [float(x) for x in np.quantile(means, [0.025, 0.975])]
    else:
        warnings.append("At least two target draws are required for a confidence interval.")
    expectation = random_expectation()
    mean = float(matches.mean())
    return dict(model=str(results.model.iloc[0]), total_tickets=len(results),
                target_draws=int(results.target_draw.nunique()),
                target_range=[int(results.target_draw.min()), int(results.target_draw.max())],
                repeats=int(results['repeat'].nunique()), average_matches=mean,
                match_distribution={i:int((matches == i).sum()) for i in range(7)},
                **{f"rate_{k}_plus":float((matches >= k).mean()) for k in (3,4,5)},
                best_result=int(matches.max()), mean_matches_ci95=ci,
                ci_method="percentile bootstrap of target-draw means",
                bootstrap_samples=bootstrap_samples, bootstrap_seed=seed,
                average_matches_by_repeat={int(k):float(v) for k,v in
                                           results.groupby('repeat').matches.mean().items()},
                random_expectation=expectation,
                difference_from_random_expectation=mean - expectation['average_matches'],
                warnings=warnings)
