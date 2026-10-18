"""H17 historical-final portfolio audit using fixed, outcome-blind construction.

Random seeds are construction replicates, not additional observed lottery draws.
Event summaries average per-replicate draw counts and retain their seed ranges.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd

from src.backtest.portfolios import make_portfolio, uniform_portfolio
from src.backtest.prizes import classify_prize


BUDGETS = (1, 5, 10, 20)
POOL_SIZE = 12
LABELS = ("SelectedEnsemble", "GapLogistic", "BestSingle")
STRATEGIES = (
    ("SelectedEnsembleWeighted", "SelectedEnsemble", "weighted"),
    ("SelectedEnsembleCoverage", "SelectedEnsemble", "coverage"),
    ("GapLogisticWeighted", "GapLogistic", "weighted"),
    ("BestSingleWeighted", "BestSingle", "weighted"),
)
EVENTS = ("ge4", "ge5", "ge6", "prize2", "prize3")


def evaluate_portfolios(rankings, targets, actual, bonus, *, seed=270500, replicates=10):
    """Evaluate five methods at equal nested budgets on targets 1131..1245.

    ``rankings`` maps each required label to an N-by-45 ordered permutation of
    numbers 1..45. ``actual`` is an N-by-45 boolean main-number indicator;
    ``bonus`` contains N separate bonus numbers. Synthetic bounded subsets are
    accepted. No files, future data, fitting, or network access are involved.

    Draw rows contain one portfolio per target/replicate/method/budget. ``geK``
    and ``prize2``/``prize3`` are indicators that at least one ticket qualifies.
    The latter also have separate ``prizeK_tickets`` counts. Ticket order is
    retained in JSON and its SHA-256, permitting exact prefix/budget audits.
    """
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if type(replicates) is not int or replicates < 1:
        raise ValueError("replicates must be a positive integer")
    targets = np.asarray(targets)
    if (targets.ndim != 1 or not len(targets)
            or not np.issubdtype(targets.dtype, np.number)
            or not np.isfinite(targets).all()
            or not np.equal(targets, np.floor(targets)).all()
            or (targets < 1131).any() or (targets > 1245).any()
            or len(np.unique(targets)) != len(targets)):
        raise ValueError("Unique integer historical-final targets in 1131..1245 required")
    targets = targets.astype(int)
    n = len(targets)
    if not isinstance(rankings, dict) or set(rankings) != set(LABELS):
        raise ValueError("rankings must contain SelectedEnsemble, GapLogistic, BestSingle")
    validated = {}
    for label in LABELS:
        ranking = np.asarray(rankings[label])
        if (ranking.shape != (n, 45) or not np.issubdtype(ranking.dtype, np.number)
                or not np.array_equal(np.sort(ranking, axis=1), np.tile(np.arange(1, 46), (n, 1)))):
            raise ValueError(f"{label} must contain N-by-45 permutations of numbers 1..45")
        validated[label] = ranking.astype(int)

    generated = []
    for index, target in enumerate(targets):
        score_pools = {}
        for label in LABELS:
            order = validated[label][index].tolist()
            scores = {number: (46 - rank) / 45 for rank, number in enumerate(order, 1)}
            score_pools[label] = (scores, order[:POOL_SIZE], tuple(order))
        for replicate in range(replicates):
            # Fresh identical SeedSequences make streams comparable across methods.
            # Existing make_portfolio caches the 924 Top-12 combination structures.
            cache = {}
            for method, label, construction in STRATEGIES:
                scores, pool, order = score_pools[label]
                key = (construction, order)
                if key not in cache:
                    cache[key] = make_portfolio(
                        scores, pool, budget=20, method=construction,
                        seed=np.random.SeedSequence([seed, replicate, int(target)]),
                    )
                generated.append((index, replicate, method, cache[key]))
            generated.append((index, replicate, "UniformRandom", uniform_portfolio(
                20, seed=np.random.SeedSequence([seed, replicate, int(target)]))))

    # No actual/bonus values are accessed until every portfolio has been built.
    actual, bonus = np.asarray(actual), np.asarray(bonus)
    if actual.shape != (n, 45) or actual.dtype != np.bool_ or not (actual.sum(axis=1) == 6).all():
        raise ValueError("actual must be an N-by-45 boolean array with six main numbers per row")
    if (bonus.shape != (n,) or not np.issubdtype(bonus.dtype, np.number)
            or not np.isfinite(bonus).all() or not np.equal(bonus, np.floor(bonus)).all()
            or (bonus < 1).any() or (bonus > 45).any()):
        raise ValueError("bonus must contain N integer numbers in 1..45")
    bonus = bonus.astype(int)
    if actual[np.arange(n), bonus - 1].any():
        raise ValueError("Bonus must be separate from main numbers")
    outcomes = [(np.flatnonzero(row) + 1).tolist() for row in actual]
    rows = []
    for index, replicate, method, tickets in generated:
        classified = [classify_prize(ticket, outcomes[index], int(bonus[index])) for ticket in tickets]
        for budget in BUDGETS:
            subset = classified[:budget]
            best = max(result["main_matches"] for result in subset)
            serialized = json.dumps(tickets[:budget], separators=(",", ":"))
            prize_counts = {prize: sum(item["prize"] == prize for item in subset) for prize in (2, 3)}
            rows.append(dict(
                target_draw=int(targets[index]), replicate=replicate, seed=seed,
                seed_entropy=json.dumps([seed, replicate, int(targets[index])], separators=(",", ":")),
                method=method, budget=budget, ticket_count=len(tickets[:budget]),
                tickets=serialized, tickets_hash=hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
                best_main=best, ge4=int(best >= 4), ge5=int(best >= 5), ge6=int(best >= 6),
                prize2=int(prize_counts[2] > 0), prize3=int(prize_counts[3] > 0),
                prize2_tickets=prize_counts[2], prize3_tickets=prize_counts[3],
            ))
    draws = pd.DataFrame(rows)
    summaries = []
    for (method, budget), group in draws.groupby(["method", "budget"], sort=False):
        by_seed = group.groupby("replicate")
        row = dict(method=method, budget=int(budget), n_targets=n, replicates=replicates,
                   mean_best_main=float(by_seed.best_main.mean().mean()))
        for event in EVENTS:
            counts = by_seed[event].sum()
            row.update({f"{event}_mean_count": float(counts.mean()),
                        f"{event}_min_count": int(counts.min()),
                        f"{event}_max_count": int(counts.max())})
        for prize in (2, 3):
            counts = by_seed[f"prize{prize}_tickets"].sum()
            row[f"prize{prize}_mean_ticket_count"] = float(counts.mean())
        summaries.append(row)
    config = dict(
        seed=seed, replicates=replicates, budgets=list(BUDGETS), pool_size=POOL_SIZE,
        pool_combinations=924, historical_final_bounds=[1131, 1245], n_targets=n,
        target_start=int(targets.min()), target_end=int(targets.max()),
        score_transform="(46 - rank) / 45; rank is 1-based",
        seed_scheme="SeedSequence([seed, replicate, target_draw]); replicate is 0-based",
        construction="Generate 20 unique tickets once, then take budget prefixes",
        event_unit="Target with at least one qualifying ticket",
        summary_unit="Mean event count across construction replicates; targets are not replicated observations",
    )
    return dict(draws=draws, summary=pd.DataFrame(summaries), config=config)
