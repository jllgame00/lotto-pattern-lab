"""One row per draw; a bonus number is never a primary appearance."""
import numpy as np
import pandas as pd

from src.collect.dataset import MAIN_COLUMNS, validate_history


def binary_series(history: pd.DataFrame) -> pd.DataFrame:
    clean = validate_history(history)
    values = np.zeros((len(clean), 45), dtype=np.uint8)
    numbers = clean[MAIN_COLUMNS].to_numpy(dtype=int)
    values[np.arange(len(clean))[:, None], numbers - 1] = 1
    return pd.DataFrame(values, index=pd.Index(clean.draw_no, name="draw_no"),
                        columns=pd.Index(range(1, 46), name="number"))
