"""Canonical draw schema and strict validation shared by every boundary."""
from __future__ import annotations

import numbers
import re
from pathlib import Path

import numpy as np
import pandas as pd

MAIN_COLUMNS = [f"num{i}" for i in range(1, 7)]
RAW_COLUMNS = ["draw_no", "draw_date", *MAIN_COLUMNS, "bonus"]
FIRST_DRAW_DATE = pd.Timestamp("2002-12-07")


class DatasetError(ValueError):
    """Invalid or incomplete draw history; never silently repair outcomes."""


def missing_draws(frame: pd.DataFrame, end: int | None = None) -> list[int]:
    present = set(frame.draw_no.astype(int)) if not frame.empty else set()
    end = end if end is not None else max(present, default=0)
    return sorted(set(range(1, end + 1)) - present)


def _integer(value, label: str) -> int:
    if isinstance(value, (bool, np.bool_)) or pd.isna(value):
        raise DatasetError(f"{label}: expected an integer, got {value!r}")
    if isinstance(value, str):
        if not re.fullmatch(r"[0-9]+", value.strip()):
            raise DatasetError(f"{label}: expected an integer, got {value!r}")
        return int(value)
    if not isinstance(value, numbers.Real) or not np.isfinite(value) or value != int(value):
        raise DatasetError(f"{label}: expected an integer, got {value!r}")
    return int(value)


def validate_history(frame: pd.DataFrame, require_complete: bool = True) -> pd.DataFrame:
    """Return a sorted copy with calendar fields; strip all untrusted extra features.

    Dates must match Lotto's weekly calendar starting 2002-12-07. Completeness
    means every draw from 1 to the maximum supplied draw is present.
    """
    missing = set(RAW_COLUMNS) - set(frame.columns)
    if missing:
        raise DatasetError(f"Missing columns: {sorted(missing)}")
    if frame.empty:
        raise DatasetError("History is empty")
    rows = []
    for record in frame[RAW_COLUMNS].to_dict("records"):
        draw = _integer(record["draw_no"], "draw_no")
        if not 1 <= draw <= 100000:
            raise DatasetError(f"Invalid draw_no: {draw}")
        nums = [_integer(record[c], f"Draw {draw} {c}") for c in MAIN_COLUMNS]
        if len(set(nums)) != 6 or any(n < 1 or n > 45 for n in nums):
            raise DatasetError(f"Draw {draw}: main numbers must be six unique integers in 1..45")
        bonus = _integer(record["bonus"], f"Draw {draw} bonus")
        if not 1 <= bonus <= 45 or bonus in nums:
            raise DatasetError(f"Draw {draw}: bonus must be 1..45 and separate from main numbers")
        date_text = str(record["draw_date"])
        if isinstance(record["draw_date"], pd.Timestamp):
            date_text = record["draw_date"].isoformat()
            if record["draw_date"] == record["draw_date"].normalize():
                date_text = date_text[:10]
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_text):
                raise ValueError("Expected YYYY-MM-DD")
            date = pd.Timestamp(date_text)
            expected = FIRST_DRAW_DATE + pd.Timedelta(weeks=draw - 1)
            if date != expected:
                raise ValueError(f"expected {expected.date()}")
        except (ValueError, OverflowError) as exc:
            raise DatasetError(f"Draw {draw}: invalid draw_date {date_text!r}: {exc}") from exc
        rows.append(dict(draw_no=draw, draw_date=date,
                         **dict(zip(MAIN_COLUMNS, sorted(nums))), bonus=bonus))
    result = pd.DataFrame(rows).sort_values("draw_no").reset_index(drop=True)
    duplicates = result.loc[result.draw_no.duplicated(), "draw_no"].tolist()
    if duplicates:
        raise DatasetError(f"duplicate draws: {duplicates}")
    gaps = missing_draws(result)
    if require_complete and gaps:
        raise DatasetError(f"Missing draws: {gaps}")
    result["year"] = result.draw_date.dt.year
    result["month"] = result.draw_date.dt.month
    result["iso_week"] = result.draw_date.dt.isocalendar().week.astype(int)
    result["weekday"] = result.draw_date.dt.weekday
    return result


def merge_history(existing: pd.DataFrame, incoming: pd.DataFrame) -> pd.DataFrame:
    normalized = []
    for frame in (existing, incoming):
        if frame.empty:
            continue
        missing = set(RAW_COLUMNS) - set(frame.columns)
        if missing:
            raise DatasetError(f"Missing columns: {sorted(missing)}")
        # Normalize each duplicate draw separately so identical rows can collapse.
        for _, group in frame.groupby("draw_no", sort=False, dropna=False):
            normalized.extend(validate_history(group.iloc[[i]], False)[RAW_COLUMNS]
                              for i in range(len(group)))
    if not normalized:
        return pd.DataFrame(columns=RAW_COLUMNS)
    combined = pd.concat(normalized, ignore_index=True).drop_duplicates()
    conflicts = combined.loc[combined.draw_no.duplicated(False), "draw_no"].unique().tolist()
    if conflicts:
        raise DatasetError(f"Conflicting outcomes for draws: {conflicts}")
    return validate_history(combined, require_complete=False)


def load_history(path: str | Path, require_complete: bool = True) -> pd.DataFrame:
    return validate_history(pd.read_csv(path), require_complete)
