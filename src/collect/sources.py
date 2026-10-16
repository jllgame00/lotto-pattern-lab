"""Donghaeng website JSON adapter (an undocumented, changeable website endpoint)."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from .dataset import FIRST_DRAW_DATE

RESULTS_URL = "https://www.dhlottery.co.kr/lt645/result"
API_URL = "https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do"


class SourceError(RuntimeError):
    """Retrieval/schema failure, distinct from an unpublished draw."""


def get_json(url: str, timeout: float = 15, retries: int = 2):
    request = urllib.request.Request(url, headers={
        "User-Agent": "lotto-pattern-lab/0.1 (historical statistical research)",
        "Accept": "application/json", "Referer": RESULTS_URL,
        "X-Requested-With": "XMLHttpRequest",
    })
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if "json" not in response.headers.get("Content-Type", "").lower():
                    raise SourceError(f"Non-JSON response from {response.url}; possibly a block/maintenance page")
                try:
                    return json.load(response)
                except (ValueError, UnicodeError) as exc:
                    raise SourceError(f"Malformed JSON from {url}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt == retries:
                raise SourceError(f"Unable to retrieve {url}: {exc}") from exc
            time.sleep(0.5 * 2**attempt)


def parse_official_payload(payload) -> list[dict]:
    try:
        items = payload["data"]["list"]
        if not isinstance(items, list):
            raise TypeError("data.list must be an array")
        return [dict(draw_no=item["ltEpsd"],
                     draw_date=datetime.strptime(str(item["ltRflYmd"]), "%Y%m%d").strftime("%Y-%m-%d"),
                     **{f"num{i}": item[f"tm{i}WnNo"] for i in range(1, 7)},
                     bonus=item["bnsWnNo"]) for item in items]
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceError(f"Official response schema is invalid: {exc}") from exc


class OfficialSource:
    label = API_URL

    def __init__(self, get_json=get_json, delay: float = 0.25):
        self._get_json = get_json
        self.delay = delay
        self._cache = {}

    def fetch_batch(self, draw_no: int) -> list[dict]:
        if draw_no in self._cache:
            return [self._cache[draw_no]]
        if self.delay:
            time.sleep(self.delay)
        rows = parse_official_payload(self._get_json(
            f"{API_URL}?srchDir=center&srchLtEpsd={draw_no}"))
        self._cache.update({int(row["draw_no"]): row for row in rows})
        return rows

    def latest_draw(self) -> int:
        today = datetime.now(timezone(timedelta(hours=9))).date()
        estimate = (today - FIRST_DRAW_DATE.date()).days // 7 + 1
        for draw in (estimate, estimate - 1):
            rows = self.fetch_batch(draw)
            if rows:
                return max(int(row["draw_no"]) for row in rows)
        raise SourceError("Latest published draw could not be established; empty responses")
