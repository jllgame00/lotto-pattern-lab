"""Safe incremental collection, explicit snapshot imports, and provenance."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .dataset import RAW_COLUMNS, DatasetError, load_history, merge_history, missing_draws, validate_history
from .sources import OfficialSource, SourceError


def atomic_write(path: Path, content: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _existing(path: Path) -> pd.DataFrame:
    return load_history(path, False) if path.exists() else pd.DataFrame(columns=RAW_COLUMNS)


def _save(path, data, before, source, end, errors, input_sha256=None):
    path = Path(path)
    if not data.empty:
        csv = data[RAW_COLUMNS].to_csv(index=False, date_format="%Y-%m-%d", lineterminator="\n")
        if not path.exists() or path.read_text(encoding="utf-8") != csv:
            atomic_write(path, csv)
    missing = missing_draws(data, end=end)
    report = dict(source=source, retrieved_at=datetime.now(timezone.utc).isoformat(),
                  rows=len(data), added=len(data) - before,
                  first_draw=None if data.empty else int(data.draw_no.min()),
                  last_draw=None if data.empty else int(data.draw_no.max()),
                  expected_end=end, missing_draws=missing, errors=errors,
                  complete=not missing and not errors and not data.empty,
                  sha256=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
                  input_sha256=input_sha256)
    metadata_path = path.with_suffix(".metadata.json")
    old = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    events = old.get("events", []) + [report.copy()]
    atomic_write(metadata_path, json.dumps({**report, "events": events}, indent=2) + "\n")
    return report


def import_history(path: str | Path, input_path: str | Path, source_label: str) -> dict:
    path, input_path = Path(path), Path(input_path)
    existing = _existing(path)
    incoming = pd.read_csv(input_path)
    combined = merge_history(existing, incoming)
    if combined.empty:
        raise DatasetError("Import contains no draws")
    return _save(path, combined, len(existing), source_label,
                 int(combined.draw_no.max()), [], hashlib.sha256(input_path.read_bytes()).hexdigest())


def collect_history(path: str | Path, end: int | None = None, source=None) -> dict:
    path = Path(path)
    existing = _existing(path)
    source = source or OfficialSource()
    combined, errors = existing, []
    if end is not None and (isinstance(end, bool) or not isinstance(end, int) or end < 1):
        raise ValueError("end must be a positive integer")
    try:
        end = end if end is not None else source.latest_draw()
        for draw in missing_draws(combined, end):
            if not combined.empty and draw in set(combined.draw_no):
                continue
            rows = source.fetch_batch(draw)
            batch = validate_history(pd.DataFrame(rows, columns=RAW_COLUMNS), False)
            if draw not in set(batch.draw_no):
                raise SourceError(f"Requested draw {draw} missing from response")
            batch = batch[batch.draw_no <= end]
            combined = merge_history(combined, batch)
    except (SourceError, DatasetError) as exc:
        errors.append(str(exc))
    return _save(path, combined, len(existing), source.label, end, errors)
