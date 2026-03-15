"""Scrape RSS feeds and HTML pages for exam-relevant articles."""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

from config import (
    CATEGORY_KEYWORDS,
    CATEGORY_ORDER,
    DELAY_BETWEEN_REQUESTS,
    IST,
    HTML_MAX_ARTICLES_PER_SOURCE,
    MAX_ARTICLE_WORDS,
    MAX_ARTICLES_PER_DAY,
    NEWS_SOURCES,
    REQUEST_RETRY_ATTEMPTS,
    REQUEST_RETRY_BACKOFF_SECONDS,
    REQUEST_TIMEOUT,
    RSS_FULL_ARTICLE_FETCH_LIMIT,
    RSS_MAX_ENTRIES_PER_SOURCE,
    RSS_LOOKBACK_HOURS,
    SOURCE_TIME_BUDGET_SECONDS,
    USER_AGENT,
)
from tracker import ArticleTracker

logger = logging.getLogger(__name__)


class NewsScraperAgent:
    """Collect articles from configured sources."""

    def __init__(self, tracker: ArticleTracker | None = None) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.tracker = tracker or ArticleTracker()

    def _remaining_time(self, deadline: float | None) -> float | None:
        if deadline is None:
            return None
        return deadline - time.monotonic()

    def _sleep(self, seconds: float = DELAY_BETWEEN_REQUESTS, deadline: float | None = None) -> None:
        if seconds <= 0:
            return
        remaining = self._remaining_time(deadline)
        if remaining is not None:
            if remaining <= 0:
                return
            seconds = min(seconds, remaining)
        time.sleep(seconds)

    def _request(self, url: str, deadline: float | None = None) -> requests.Response | None:
        last_error: Exception | None = None
        for attempt in range(1, REQUEST_RETRY_ATTEMPTS + 1):
            remaining = self._remaining_time(deadline)
            if remaining is not None and remaining <= 0:
                logger.warning("Skipping %s because the source time budget was exhausted", url)
                return None

            timeout = REQUEST_TIMEOUT
            if remaining is not None:
                timeout = max(1, min(REQUEST_TIMEOUT, int(remaining)))

            try:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                self._sleep(deadline=deadline)
                return response
            except requests.RequestException as exc:
                last_error = exc
                logger.warning(
                    "Request failed for %s on attempt %s/%s: %s",
                    url,
                    attempt,
                    REQUEST_RETRY_ATTEMPTS,
                    exc,
                )
                if attempt < REQUEST_RETRY_ATTEMPTS:
                    self._sleep(REQUEST_RETRY_BACKOFF_SECONDS * attempt, deadline=deadline)

        logger.warning("Giving up on %s after retries: %s", url, last_error)
        return None

    def _clean_text(self, text: str, max_words: int = 1000) -> str:
        words = re.split(r"\s+", re.sub(r"\s+", " ", text or "").strip())
        return " ".join(words[:max_words]).strip()

    def _extract_meta_description(self, html_text: str) -> str:
        soup = BeautifulSoup(html_text, "html.parser")
        for name in ("description", "og:description", "twitter:description"):
            tag = soup.find("meta", attrs={"name": name}) or soup.find(
                "meta", attrs={"property": name}
            )
            if tag and tag.get("content"):
                return self._clean_text(tag["content"], max_words=120)
        return ""

    def _extract_article_text_from_html(self, html_text: str) -> str:
        soup = BeautifulSoup(html_text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        selectors = [
            "article",
            "main",
            ".article-body",
            ".story-content",
            ".entry-content",
            ".post-content",
            ".storyBody",
            ".field-item",
        ]

        chunks: list[str] = []
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                paragraphs = [p.get_text(" ", strip=True) for p in node.find_all(["p", "li"])]
                chunks = [p for p in paragraphs if len(p.split()) > 5]
                if chunks:
                    break

        if not chunks:
            paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
            chunks = [p for p in paragraphs if len(p.split()) > 5]

        return self._clean_text(" ".join(chunks), max_words=1000)

    def _extract_article_text(self, url: str, deadline: float | None = None) -> str:
        response = self._request(url, deadline=deadline)
        if response is None:
            return ""
        return self._extract_article_text_from_html(response.text)

    def _parse_published(self, entry: Any) -> datetime | None:
        for field in ("published", "updated", "pubDate"):
            value = entry.get(field)
            if not value:
                continue
            try:
                published = parsedate_to_datetime(value)
                if published.tzinfo is None:
                    published = published.replace(tzinfo=IST)
                return published.astimezone(IST)
            except (TypeError, ValueError, IndexError):
                continue
        for field in ("published_parsed", "updated_parsed"):
            parsed = entry.get(field)
            if parsed:
                return datetime(*parsed[:6], tzinfo=IST)
        return None

    def fetch_rss_feed(
        self,
        url: str,
        source_name: str,
        category: str,
        deadline: float | None = None,
        max_entries: int = RSS_MAX_ENTRIES_PER_SOURCE,
        fetch_full_content_limit: int = RSS_FULL_ARTICLE_FETCH_LIMIT,
    ) -> list[dict[str, Any]]:
        articles: list[dict[str, Any]] = []
        try:
            response = self._request(url, deadline=deadline)
            if response is None:
                return []
            feed = feedparser.parse(response.content)
            cutoff = datetime.now(IST) - timedelta(hours=RSS_LOOKBACK_HOURS)
            full_content_fetches = 0

            for entry in feed.entries[:max_entries]:
                if (remaining := self._remaining_time(deadline)) is not None and remaining <= 0:
                    logger.info("Stopping RSS fetch for %s because its time budget expired", source_name)
                    break

                link = entry.get("link", "").strip()
                title = entry.get("title", "").strip()
                published_at = self._parse_published(entry)
                if published_at and published_at < cutoff:
                    continue
                if not title or not link:
                    continue

                summary = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(" ", strip=True)
                content = ""
                # RSS feeds already carry usable summaries; only fetch a few full articles when the feed text is thin.
                if len(summary.split()) < 35 and full_content_fetches < fetch_full_content_limit:
                    content = self._extract_article_text(link, deadline=deadline)
                    if content:
                        full_content_fetches += 1
                article_text = content or summary or title
                articles.append(
                    {
                        "title": title,
                        "url": link,
                        "source_name": source_name,
                        "published": (published_at or datetime.now(IST)).isoformat(),
                        "content": self._clean_text(article_text, max_words=MAX_ARTICLE_WORDS),
                        "summary": self._clean_text(summary, max_words=120),
                        "category": self.categorize_article(title, article_text, default_category=category),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            logger.exception("RSS scraping failed for %s: %s", source_name, exc)
        return articles

    def scrape_html_page(
        self,
        url: str,
        source_name: str,
        category: str,
        listing_selectors: list[str] | None = None,
        deadline: float | None = None,
        max_articles: int = HTML_MAX_ARTICLES_PER_SOURCE,
    ) -> list[dict[str, Any]]:
        articles: list[dict[str, Any]] = []
        try:
            response = self._request(url, deadline=deadline)
            if response is None:
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            selectors = listing_selectors or ["h2 a", "h3 a", "article a", "main a"]
            seen_links: set[str] = set()
            candidates: list[tuple[str, str]] = []

            for selector in selectors:
                for anchor in soup.select(selector):
                    href = anchor.get("href")
                    title = anchor.get_text(" ", strip=True)
                    if not href or not title:
                        continue
                    absolute_url = urljoin(url, href)
                    if absolute_url in seen_links:
                        continue
                    if urlparse(absolute_url).netloc != urlparse(url).netloc:
                        continue
                    seen_links.add(absolute_url)
                    candidates.append((title, absolute_url))
                if len(candidates) >= 12:
                    break

            for title, article_url in candidates[:max_articles]:
                if (remaining := self._remaining_time(deadline)) is not None and remaining <= 0:
                    logger.info("Stopping HTML fetch for %s because its time budget expired", source_name)
                    break

                article_response = self._request(article_url, deadline=deadline)
                if article_response is None:
                    continue
                content = self._extract_article_text_from_html(article_response.text)
                meta_description = self._extract_meta_description(article_response.text)
                article_text = content or meta_description or title
                if len(article_text.split()) < 10:
                    continue
                articles.append(
                    {
                        "title": title,
                        "url": article_url,
                        "source_name": source_name,
                        "published": datetime.now(IST).isoformat(),
                        "content": self._clean_text(article_text, max_words=MAX_ARTICLE_WORDS),
                        "summary": meta_description,
                        "category": self.categorize_article(title, article_text, default_category=category),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            logger.exception("HTML scraping failed for %s: %s", source_name, exc)
        return articles

    def categorize_article(
        self,
        title: str,
        content: str,
        default_category: str = "CURRENT AFFAIRS GENERAL",
    ) -> str:
        combined = f"{title} {content}".lower()
        best_category = default_category
        best_score = 0

        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword.lower() in combined)
            if score > best_score:
                best_category = category
                best_score = score

        return best_category

    def fetch_all_news(self) -> list[dict[str, Any]]:
        combined_articles: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        for source in NEWS_SOURCES:
            source_started = time.monotonic()
            source_budget = source.get("time_budget_seconds", SOURCE_TIME_BUDGET_SECONDS)
            deadline = source_started + source_budget
            try:
                logger.info(
                    "Fetching source: %s with a %ss time budget",
                    source["name"],
                    source_budget,
                )
                if source["type"] == "rss":
                    articles = self.fetch_rss_feed(
                        source["url"],
                        source["name"],
                        source["category"],
                        deadline=deadline,
                        max_entries=source.get("max_entries", RSS_MAX_ENTRIES_PER_SOURCE),
                        fetch_full_content_limit=source.get(
                            "fetch_full_content_limit",
                            RSS_FULL_ARTICLE_FETCH_LIMIT,
                        ),
                    )
                else:
                    articles = self.scrape_html_page(
                        source["url"],
                        source["name"],
                        source["category"],
                        source.get("listing_selectors"),
                        deadline=deadline,
                        max_articles=source.get("max_articles", HTML_MAX_ARTICLES_PER_SOURCE),
                    )
            except Exception as exc:  # noqa: BLE001
                logger.exception("Source fetch crashed for %s: %s", source["name"], exc)
                articles = []
            finally:
                elapsed = round(time.monotonic() - source_started, 2)
                logger.info("Finished source %s in %ss", source["name"], elapsed)

            for article in articles:
                url = article.get("url", "")
                if not url or url in seen_urls or self.tracker.is_already_sent(url):
                    continue
                seen_urls.add(url)
                combined_articles.append(article)

        def sort_key(item: dict[str, Any]) -> tuple[int, str]:
            category = item.get("category", "CURRENT AFFAIRS GENERAL")
            try:
                index = CATEGORY_ORDER.index(category)
            except ValueError:
                index = len(CATEGORY_ORDER)
            return (index, item.get("title", ""))

        combined_articles.sort(key=sort_key)
        final_articles = combined_articles[:MAX_ARTICLES_PER_DAY]
        logger.info("Returning %s new articles after filtering", len(final_articles))
        return final_articles
