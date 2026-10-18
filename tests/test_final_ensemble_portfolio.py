"""Historical H17 ticket audits; synthetic fixtures never touch canonical data."""
import hashlib
import json

import numpy as np
import pandas as pd
import pytest


def inputs(n=2):
    rankings = {label: np.tile(np.arange(1, 46), (n, 1)) for label in
                ("SelectedEnsemble", "GapLogistic", "BestSingle")}
    actual = np.zeros((n, 45), dtype=bool)
    actual[:, :6] = True
    return rankings, np.arange(1131, 1131 + n), actual, np.full(n, 45)


def evaluate(*args, **kwargs):
    from src.analysis.final_ensemble_portfolio import evaluate_portfolios
    return evaluate_portfolios(*args, **kwargs)


def test_deterministic_equal_nested_budgets_and_shared_weighted_streams():
    args = inputs()
    result = evaluate(*args, replicates=2)
    again = evaluate(*args, replicates=2)
    pd.testing.assert_frame_equal(result["draws"], again["draws"])
    pd.testing.assert_frame_equal(result["summary"], again["summary"])
    draws = result["draws"]
    assert len(draws) == 2 * 2 * 5 * 4
    assert set(draws.method) == {"SelectedEnsembleWeighted", "SelectedEnsembleCoverage",
                                 "GapLogisticWeighted", "BestSingleWeighted", "UniformRandom"}
    for (_, _, method), group in draws.groupby(["target_draw", "replicate", "method"]):
        assert group.budget.tolist() == [1, 5, 10, 20]
        full = json.loads(group.iloc[-1].tickets)
        assert len({tuple(ticket) for ticket in full}) == 20
        for row in group.itertuples():
            tickets = json.loads(row.tickets)
            assert tickets == full[:row.budget]
            assert row.ticket_count == row.budget
            assert row.tickets_hash == hashlib.sha256(row.tickets.encode("utf-8")).hexdigest()
            assert all(len(set(t)) == 6 and set(t) <= set(range(1, 46)) for t in tickets)
            if method != "UniformRandom":
                assert all(set(t) <= set(range(1, 13)) for t in tickets)
    weighted = draws[draws.method.isin(["SelectedEnsembleWeighted", "GapLogisticWeighted", "BestSingleWeighted"])]
    assert weighted.groupby(["target_draw", "replicate", "budget"]).tickets_hash.nunique().eq(1).all()
    assert draws[draws.budget.eq(20)].groupby(["target_draw", "method"]).tickets_hash.nunique().eq(2).all()


def test_construction_is_outcome_blind_and_bonus_distinguishes_second_third():
    rankings, targets, actual, bonus = inputs(1)
    initial = evaluate(rankings, targets, actual, bonus, replicates=1)
    first = json.loads(initial["draws"].query("method == 'SelectedEnsembleWeighted' and budget == 1").iloc[0].tickets)[0]
    held_out = next(n for n in range(1, 46) if n not in first)
    outcome = np.zeros((1, 45), dtype=bool)
    outcome[0, np.array(first[:5] + [held_out]) - 1] = True
    second = evaluate(rankings, targets, outcome, np.array([first[5]]), replicates=1)
    third_bonus = next(n for n in range(1, 46) if n not in first and n != held_out)
    third = evaluate(rankings, targets, outcome, np.array([third_bonus]), replicates=1)
    for result in (second, third):
        assert result["draws"].tickets.tolist() == initial["draws"].tickets.tolist()
    second_row = second["draws"].query("method == 'SelectedEnsembleWeighted' and budget == 1").iloc[0]
    third_row = third["draws"].query("method == 'SelectedEnsembleWeighted' and budget == 1").iloc[0]
    assert (second_row.best_main, second_row.ge5, second_row.ge6, second_row.prize2, second_row.prize3) == (5, 1, 0, 1, 0)
    assert (third_row.best_main, third_row.prize2, third_row.prize3) == (5, 0, 1)
    outcome[:] = False
    outcome[0, np.array(first) - 1] = True
    jackpot = evaluate(rankings, targets, outcome, np.array([held_out]), replicates=1)
    row = jackpot["draws"].query("method == 'SelectedEnsembleWeighted' and budget == 1").iloc[0]
    assert (row.best_main, row.ge6, row.prize2, row.prize3) == (6, 1, 0, 0)


def test_summary_counts_targets_once_and_reports_seed_event_ranges():
    result = evaluate(*inputs(), replicates=3)
    draws, summary = result["draws"], result["summary"]
    assert summary.n_targets.eq(2).all()
    assert summary.replicates.eq(3).all()
    for row in summary.itertuples():
        group = draws[(draws.method == row.method) & (draws.budget == row.budget)]
        assert row.mean_best_main == pytest.approx(group.groupby("replicate").best_main.mean().mean())
        for event in ("ge4", "ge5", "ge6", "prize2", "prize3"):
            totals = group.groupby("replicate")[event].sum()
            assert getattr(row, f"{event}_mean_count") == pytest.approx(totals.mean())
            assert getattr(row, f"{event}_min_count") == totals.min()
            assert getattr(row, f"{event}_max_count") == totals.max()
    assert result["config"]["pool_size"] == 12
    assert result["config"]["replicates"] == 3


@pytest.mark.parametrize("target", [1130, 1246, 0, 1131.5])
def test_rejects_targets_outside_historical_final_or_noninteger(target):
    rankings, _, actual, bonus = inputs(1)
    with pytest.raises(ValueError):
        evaluate(rankings, np.array([target]), actual, bonus, replicates=1)


@pytest.mark.parametrize("bad", ["duplicate", "out_of_range", "noninteger", "wrong_shape"])
def test_requires_each_ranking_to_be_a_number_permutation(bad):
    rankings, targets, actual, bonus = inputs(1)
    value = rankings["BestSingle"].astype(float)
    if bad == "duplicate":
        value[0, 0] = 2
    elif bad == "out_of_range":
        value[0, 0] = 46
    elif bad == "noninteger":
        value[0, 0] = 1.1
    else:
        value = value[:, :-1]
    rankings["BestSingle"] = value
    with pytest.raises(ValueError):
        evaluate(rankings, targets, actual, bonus, replicates=1)


def test_target_order_does_not_change_shared_streams():
    rankings, targets, actual, bonus = inputs()
    first = evaluate(rankings, targets, actual, bonus, replicates=1)["draws"]
    second = evaluate({k: v[::-1] for k, v in rankings.items()}, targets[::-1], actual[::-1], bonus[::-1], replicates=1)["draws"]
    keys = ["target_draw", "replicate", "method", "budget"]
    pd.testing.assert_frame_equal(first.sort_values(keys).reset_index(drop=True), second.sort_values(keys).reset_index(drop=True))
