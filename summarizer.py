"""Groq-based news summarization for exam preparation."""

from __future__ import annotations

import json
import logging
import re
import time
from collections import defaultdict
from typing import Any

from groq import Groq

from config import (
    DELAY_BETWEEN_API_CALLS,
    GROQ_429_BACKOFF_SECONDS,
    GROQ_API_KEY,
    GROQ_MAX_SUMMARIES_PER_RUN,
    GROQ_MIN_SECONDS_BETWEEN_CALLS,
    GROQ_MODEL,
    SUMMARIZER_MAX_RETRIES,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert content summarizer specifically for Indian Civil Services Examination preparation (UPSC, TSPSC, State PSC exams).

Your job is to read a news article and extract only what is relevant and useful for exam preparation.

Return ONLY a valid JSON object with this exact structure:
{
  "headline": "string",
  "one_liner": "string",
  "key_points": ["string", "string", "string", "string"],
  "exam_relevance": "string",
  "important_terms": ["string", "string"],
  "possible_question": "string",
  "category": "string"
}"""


class NewsSummarizer:
    """Summarize articles using Groq."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or GROQ_API_KEY
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self._last_call_at: float | None = None

    def _throttle(self) -> None:
        now = time.monotonic()
        if self._last_call_at is None:
            self._last_call_at = now
            return

        elapsed = now - self._last_call_at
        if elapsed < GROQ_MIN_SECONDS_BETWEEN_CALLS:
            time.sleep(GROQ_MIN_SECONDS_BETWEEN_CALLS - elapsed)
        self._last_call_at = time.monotonic()

    def _extract_json(self, raw_text: str) -> dict[str, Any]:
        raw_text = raw_text.strip()
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        payload = match.group(0) if match else raw_text
        data = json.loads(payload)

        key_points = data.get("key_points") or []
        important_terms = data.get("important_terms") or []
        normalized = {
            "headline": str(data.get("headline", "")).strip(),
            "one_liner": str(data.get("one_liner", "")).strip(),
            "key_points": [str(item).strip() for item in key_points][:5],
            "exam_relevance": str(data.get("exam_relevance", "")).strip(),
            "important_terms": [str(item).strip() for item in important_terms][:3],
            "possible_question": str(data.get("possible_question", "")).strip(),
            "category": str(data.get("category", "")).strip(),
        }
        if len(normalized["key_points"]) < 4:
            raise ValueError("Groq returned fewer than 4 key points")
        return normalized

    def summarize_article(self, article: dict[str, Any]) -> dict[str, Any] | None:
        if self.client is None:
            raise RuntimeError("GROQ_API_KEY is not configured")

        user_prompt = (
            f"Article Title: {article['title']}\n"
            f"Source: {article['source_name']}\n"
            f"Content: {article['content'][:4500]}\n\n"
            "Summarize this for civil services exam preparation."
        )

        for attempt in range(1, SUMMARIZER_MAX_RETRIES + 1):
            try:
                self._throttle()
                response = self.client.chat.completions.create(
                    model=GROQ_MODEL,
                    temperature=0.1,
                    max_tokens=450,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                content = response.choices[0].message.content or "{}"
                summary = self._extract_json(content)
                summary["source_name"] = article["source_name"]
                summary["url"] = article["url"]
                summary["original_title"] = article["title"]
                summary["published"] = article.get("published", "")
                summary["category"] = summary["category"] or article["category"]
                time.sleep(DELAY_BETWEEN_API_CALLS)
                return summary
            except Exception as exc:  # noqa: BLE001
                message = str(exc)
                logger.warning(
                    "Groq summarization failed for '%s' on attempt %s/%s: %s",
                    article["title"],
                    attempt,
                    SUMMARIZER_MAX_RETRIES,
                    exc,
                )
                if "429" in message or "Too Many Requests" in message:
                    time.sleep(GROQ_429_BACKOFF_SECONDS)
                elif "json_validate_failed" in message or "Failed to generate JSON" in message:
                    time.sleep(GROQ_MIN_SECONDS_BETWEEN_CALLS)
                if attempt < SUMMARIZER_MAX_RETRIES:
                    time.sleep(attempt * 2)
        logger.error("Skipping article after repeated Groq failures: %s", article["title"])
        return None

    def summarize_all_articles(self, articles: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        attempted = 0
        for article in articles:
            if attempted >= GROQ_MAX_SUMMARIES_PER_RUN:
                logger.info(
                    "Stopping after %s Groq summaries to stay within the free-tier budget",
                    GROQ_MAX_SUMMARIES_PER_RUN,
                )
                break
            attempted += 1
            summary = self.summarize_article(article)
            if summary:
                grouped[summary["category"]].append(summary)
        return dict(grouped)
