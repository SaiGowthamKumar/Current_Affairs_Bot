"""Entry point and scheduler setup for the news agent."""

from __future__ import annotations

import argparse
import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config import IST, RECIPIENT_EMAIL, SCHEDULE_TIME, TIMEZONE, setup_logging
from email_sender import NewsEmailSender
from scraper import NewsScraperAgent
from summarizer import NewsSummarizer
from tracker import ArticleTracker

logger = logging.getLogger(__name__)


def run_daily_digest() -> None:
    if not RECIPIENT_EMAIL:
        raise RuntimeError("RECIPIENT_EMAIL is not configured")

    tracker = ArticleTracker()
    scraper = NewsScraperAgent(tracker=tracker)
    summarizer = NewsSummarizer()
    email_sender = NewsEmailSender()
    today = datetime.now(IST)

    print("[1/4] Fetching news from all sources...")
    articles = scraper.fetch_all_news()
    print(f"     Found {len(articles)} new articles")

    print("[2/4] Summarizing with Groq AI...")
    summaries = summarizer.summarize_all_articles(articles)
    total_summaries = sum(len(items) for items in summaries.values())
    print(f"     Summarized {total_summaries} articles")

    if total_summaries == 0:
        logger.warning("No summaries were generated; skipping email send")
        return

    print("[3/4] Building email digest...")
    html = email_sender.build_html_email(summaries, today)

    print("[4/4] Sending email...")
    email_sender.send_email(html, RECIPIENT_EMAIL, today, summaries)

    summarized_urls = [
        item["url"] for category_items in summaries.values() for item in category_items if item.get("url")
    ]
    tracker.mark_as_sent(summarized_urls)
    print("Done! Email sent successfully.")


def start_scheduler() -> None:
    hour, minute = [int(part) for part in SCHEDULE_TIME.split(":", maxsplit=1)]
    scheduler = BlockingScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        run_daily_digest,
        CronTrigger(hour=hour, minute=minute, timezone=TIMEZONE),
        id="daily-current-affairs-digest",
        replace_existing=True,
    )
    next_run = scheduler.get_jobs()[0].next_run_time
    print(f"Scheduler started. Next run at {next_run.astimezone(IST)}")
    scheduler.start()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily current affairs news agent")
    parser.add_argument("--test", action="store_true", help="Run the digest immediately")
    return parser.parse_args()


if __name__ == "__main__":
    log_file = setup_logging()
    logger.info("Logging to %s", log_file)
    args = parse_args()
    if args.test:
        run_daily_digest()
    else:
        start_scheduler()
