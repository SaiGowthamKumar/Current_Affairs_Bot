"""Track sent article URLs to avoid duplicates."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

from config import IST, TRACKER_FILE, TRACKER_RETENTION_DAYS

logger = logging.getLogger(__name__)


class ArticleTracker:
    """Persist sent article URLs with timestamps."""

    def __init__(self, tracker_file: Path | None = None) -> None:
        self.tracker_file = tracker_file or TRACKER_FILE
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.tracker_file.exists():
            self.tracker_file.write_text("{}", encoding="utf-8")

    def _load(self) -> Dict[str, str]:
        try:
            return json.loads(self.tracker_file.read_text(encoding="utf-8") or "{}")
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Falling back to empty tracker store: %s", exc)
            return {}

    def _save(self, data: Dict[str, str]) -> None:
        self.tracker_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    def is_already_sent(self, url: str) -> bool:
        data = self._load()
        cleaned = self.cleanup_old_entries(data)
        return url in cleaned

    def mark_as_sent(self, urls_list: list[str]) -> None:
        data = self._load()
        now = datetime.now(IST).isoformat()
        for url in urls_list:
            if url:
                data[url] = now
        cleaned = self.cleanup_old_entries(data)
        self._save(cleaned)
        logger.info("Tracked %s URLs as sent", len(urls_list))

    def cleanup_old_entries(self, existing_data: Dict[str, str] | None = None) -> Dict[str, str]:
        data = existing_data if existing_data is not None else self._load()
        cutoff = datetime.now(IST) - timedelta(days=TRACKER_RETENTION_DAYS)
        cleaned: Dict[str, str] = {}
        for url, timestamp in data.items():
            try:
                if datetime.fromisoformat(timestamp) >= cutoff:
                    cleaned[url] = timestamp
            except ValueError:
                logger.debug("Dropping malformed tracker entry for %s", url)
        if existing_data is None:
            self._save(cleaned)
        return cleaned
