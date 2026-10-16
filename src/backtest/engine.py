"""Walk-forward and checkpoint evaluation with restricted model inputs."""
from __future__ import annotations

from collections.abc import Callable
from numbers import Integral

import numpy as np
import pandas as pd

from src.collect.dataset import MAIN_COLUMNS, RAW_COLUMNS, validate_history
from src.models.base import NumberModel, TargetDrawContext, validate_ticket


def _positive(value, name):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def run_backtest(history: pd.DataFrame, model_factory: Callable[[], NumberModel], *,
                 mode: str = "walk-forward", min_train: int = 299, seed: int = 42,
                 tickets: int = 1, repeats: int = 1, checkpoints: int = 100,
                 start: int | None = None, end: int | None = None) -> pd.DataFrame:
    """Evaluate only unseen targets; never pass globally derived features to models.

    The factory must create a new unfitted model without external training data.
    Checkpoint selection is fixed across repetitions; ticket RNG streams differ.
    Distinct tickets may coincide by chance, but each contains six unique numbers.
    """
    for name, value in (("min_train", min_train), ("tickets", tickets), ("repeats", repeats)):
        _positive(value, name)
    if isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if mode not in ("walk-forward", "checkpoints"):
        raise ValueError("mode must be walk-forward or checkpoints")
    data = validate_history(history)[RAW_COLUMNS]
    start = min_train + 1 if start is None else start
    end = int(data.draw_no.max()) if end is None else end
    _positive(start, "start")
    _positive(end, "end")
    if start <= min_train or start > end or end > int(data.draw_no.max()):
        raise ValueError("Target range must be present in history and strictly after min_train")
    targets = np.arange(start, end + 1)
    if mode == "checkpoints":
        _positive(checkpoints, "checkpoints")
        if checkpoints > len(targets):
            raise ValueError(f"Requested {checkpoints} checkpoints but only {len(targets)} eligible targets")
        sampling_rng = np.random.default_rng(np.random.SeedSequence([int(seed), 0]))
        targets = np.sort(sampling_rng.choice(targets, size=checkpoints, replace=False))
    results = []
    for target in targets:
        target = int(target)
        # All rows are continuous from draw 1, but filter explicitly by draw number.
        prefix = data.loc[data.draw_no < target, RAW_COLUMNS].copy(deep=True)
        if len(prefix) < min_train or int(prefix.draw_no.max()) != target - 1:
            raise ValueError(f"Incomplete training history before target {target}")
        context = TargetDrawContext(target, prefix.iloc[-1].draw_date + pd.Timedelta(days=7))
        for repeat in range(repeats):
            for ticket_index in range(tickets):
                ticket_seed = int(np.random.SeedSequence(
                    [int(seed), target, repeat, ticket_index, 1]).generate_state(1)[0])
                model = model_factory()
                prediction = validate_ticket(model.predict(prefix.copy(deep=True), context=context,
                                                             k=6, seed=ticket_seed))
                # The outcome is accessed only after prediction has returned.
                actual = data.loc[data.draw_no == target, MAIN_COLUMNS].iloc[0].astype(int).tolist()
                results.append(dict(model=type(model).__name__, target_draw=target,
                                    target_date=context.draw_date.strftime("%Y-%m-%d"),
                                    train_start=1, train_end=target - 1, training_draws=len(prefix),
                                    repeat=repeat, ticket_index=ticket_index, ticket_seed=ticket_seed,
                                    prediction=prediction, actual=actual,
                                    matches=len(set(prediction) & set(actual))))
    return pd.DataFrame(results)
