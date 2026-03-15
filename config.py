"""Configuration for the current affairs news agent."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
TRACKER_FILE = BASE_DIR / "sent_articles.json"
TIMEZONE = "Asia/Kolkata"
IST = ZoneInfo(TIMEZONE)
USER_AGENT = "Mozilla/5.0 (compatible; NewsBot/1.0)"

MAX_ARTICLES_PER_DAY = 30
MAX_ARTICLE_WORDS = 800
RSS_LOOKBACK_HOURS = 24
SCHEDULE_TIME = os.getenv("SEND_TIME", "06:00")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
DELAY_BETWEEN_REQUESTS = 2
DELAY_BETWEEN_API_CALLS = 1
REQUEST_TIMEOUT = 20
SOURCE_TIME_BUDGET_SECONDS = int(os.getenv("SOURCE_TIME_BUDGET_SECONDS", "45"))
REQUEST_RETRY_ATTEMPTS = int(os.getenv("REQUEST_RETRY_ATTEMPTS", "2"))
REQUEST_RETRY_BACKOFF_SECONDS = float(os.getenv("REQUEST_RETRY_BACKOFF_SECONDS", "1"))
RSS_MAX_ENTRIES_PER_SOURCE = int(os.getenv("RSS_MAX_ENTRIES_PER_SOURCE", "8"))
RSS_FULL_ARTICLE_FETCH_LIMIT = int(os.getenv("RSS_FULL_ARTICLE_FETCH_LIMIT", "3"))
HTML_MAX_ARTICLES_PER_SOURCE = int(os.getenv("HTML_MAX_ARTICLES_PER_SOURCE", "6"))
TRACKER_RETENTION_DAYS = 7
SUMMARIZER_MAX_RETRIES = 3

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GMAIL_SENDER_EMAIL = os.getenv("GMAIL_SENDER_EMAIL", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")

CATEGORY_ORDER = [
    "TELANGANA STATE AFFAIRS",
    "POLITY & GOVERNANCE",
    "ECONOMY & FINANCE",
    "INTERNATIONAL RELATIONS",
    "SCIENCE & TECHNOLOGY",
    "ENVIRONMENT & ECOLOGY",
    "SOCIAL ISSUES",
    "HISTORY & CULTURE",
    "SPORTS",
    "CURRENT AFFAIRS GENERAL",
]

CATEGORY_COLORS = {
    "POLITY & GOVERNANCE": "#3b82f6",
    "ECONOMY & FINANCE": "#10b981",
    "INTERNATIONAL RELATIONS": "#8b5cf6",
    "SCIENCE & TECHNOLOGY": "#06b6d4",
    "ENVIRONMENT & ECOLOGY": "#22c55e",
    "TELANGANA STATE AFFAIRS": "#f59e0b",
    "SOCIAL ISSUES": "#ec4899",
    "HISTORY & CULTURE": "#f97316",
    "SPORTS": "#ef4444",
    "CURRENT AFFAIRS GENERAL": "#6b7280",
}

DISPLAY_SECTION_ORDER = [
    "INTERNATIONAL MAIN POINTS",
    "NATIONAL NEWS MAIN POINTS",
    "STATE NEWS MAIN POINTS",
    "SPORTS NEWS POINTS",
    "BUSINESS POINTS",
    "ENTERTAINMENT POINTS",
]

DISPLAY_SECTION_COLORS = {
    "INTERNATIONAL MAIN POINTS": "#2563eb",
    "NATIONAL NEWS MAIN POINTS": "#1f2937",
    "STATE NEWS MAIN POINTS": "#f59e0b",
    "SPORTS NEWS POINTS": "#dc2626",
    "BUSINESS POINTS": "#059669",
    "ENTERTAINMENT POINTS": "#7c3aed",
}

DISPLAY_SECTION_MAP = {
    "INTERNATIONAL RELATIONS": "INTERNATIONAL MAIN POINTS",
    "POLITY & GOVERNANCE": "NATIONAL NEWS MAIN POINTS",
    "SCIENCE & TECHNOLOGY": "NATIONAL NEWS MAIN POINTS",
    "ENVIRONMENT & ECOLOGY": "NATIONAL NEWS MAIN POINTS",
    "SOCIAL ISSUES": "NATIONAL NEWS MAIN POINTS",
    "CURRENT AFFAIRS GENERAL": "NATIONAL NEWS MAIN POINTS",
    "TELANGANA STATE AFFAIRS": "STATE NEWS MAIN POINTS",
    "ECONOMY & FINANCE": "BUSINESS POINTS",
    "SPORTS": "SPORTS NEWS POINTS",
    "HISTORY & CULTURE": "ENTERTAINMENT POINTS",
}

CATEGORY_KEYWORDS = {
    "POLITY & GOVERNANCE": [
        "parliament",
        "lok sabha",
        "rajya sabha",
        "constitution",
        "supreme court",
        "high court",
        "election",
        "governor",
        "president",
        "prime minister",
        "cabinet",
        "ministry",
        "bill",
        "act",
        "amendment",
        "policy",
        "scheme",
        "yojana",
    ],
    "ECONOMY & FINANCE": [
        "gdp",
        "inflation",
        "rbi",
        "repo rate",
        "budget",
        "fiscal",
        "tax",
        "gst",
        "export",
        "import",
        "trade deficit",
        "rupee",
        "sensex",
        "nifty",
        "sebi",
        "stock market",
        "economy",
    ],
    "TELANGANA STATE AFFAIRS": [
        "telangana",
        "hyderabad",
        "tspsc",
        "kcr",
        "revanth reddy",
        "kaleshwaram",
        "mission bhagiratha",
        "rythu bandhu",
        "ts genco",
        "ghmc",
        "hmda",
        "secunderabad",
        "warangal",
        "nizamabad",
        "karimnagar",
        "khammam",
        "nalgonda",
    ],
    "SCIENCE & TECHNOLOGY": [
        "isro",
        "nasa",
        "satellite",
        "rocket",
        "space",
        "ai",
        "artificial intelligence",
        "chandrayaan",
        "gaganyaan",
        "nuclear",
        "missile",
        "drdo",
        "iit",
        "research",
    ],
    "ENVIRONMENT & ECOLOGY": [
        "climate",
        "pollution",
        "forest",
        "wildlife",
        "tiger",
        "carbon",
        "emissions",
        "solar",
        "renewable",
        "biodiversity",
        "coral reef",
        "glacier",
        "ozone",
        "cop",
        "paris agreement",
    ],
    "INTERNATIONAL RELATIONS": [
        "india-china",
        "india-pakistan",
        "united nations",
        "g20",
        "brics",
        "sco",
        "asean",
        "who",
        "imf",
        "world bank",
        "bilateral",
        "diplomatic",
        "treaty",
        "sanctions",
    ],
    "SOCIAL ISSUES": [
        "health",
        "education",
        "poverty",
        "women",
        "child",
        "nutrition",
        "employment",
        "census",
        "migration",
        "welfare",
    ],
    "HISTORY & CULTURE": [
        "heritage",
        "unesco",
        "culture",
        "festival",
        "archaeology",
        "museum",
        "classical",
        "temple",
        "monument",
        "tradition",
    ],
    "SPORTS": [
        "cricket",
        "olympics",
        "hockey",
        "badminton",
        "football",
        "athletics",
        "sports",
        "medal",
    ],
}

NEWS_SOURCES = [
    {
        "name": "The Hindu",
        "url": "https://www.thehindu.com/feeder/default.rss",
        "type": "rss",
        "category": "CURRENT AFFAIRS GENERAL",
        "time_budget_seconds": 25,
        "max_entries": 6,
        "fetch_full_content_limit": 2,
    },
    {
        "name": "Indian Express",
        "url": "https://indianexpress.com/feed/",
        "type": "rss",
        "category": "CURRENT AFFAIRS GENERAL",
        "time_budget_seconds": 25,
        "max_entries": 6,
        "fetch_full_content_limit": 2,
    },
    {
        "name": "PIB",
        "url": "https://www.pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
        "type": "rss",
        "category": "POLITY & GOVERNANCE",
        "time_budget_seconds": 15,
        "max_entries": 8,
        "fetch_full_content_limit": 0,
    },
    {
        "name": "Hindustan Times",
        "url": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
        "type": "rss",
        "category": "CURRENT AFFAIRS GENERAL",
        "time_budget_seconds": 20,
        "max_entries": 6,
        "fetch_full_content_limit": 1,
    },
    {
        "name": "Telangana Today",
        "url": "https://telanganatoday.com/feed",
        "type": "rss",
        "category": "TELANGANA STATE AFFAIRS",
        "time_budget_seconds": 20,
        "max_entries": 6,
        "fetch_full_content_limit": 1,
    },
    {
        "name": "The Hans India Telangana",
        "url": "https://www.thehansindia.com/telangana",
        "type": "html",
        "category": "TELANGANA STATE AFFAIRS",
        "listing_selectors": ["h2 a", ".section-listing a", ".story-card a", ".news-card a"],
        "time_budget_seconds": 20,
        "max_articles": 5,
    },
    {
        "name": "Sakshi English",
        "url": "https://english.sakshi.com/",
        "type": "html",
        "category": "TELANGANA STATE AFFAIRS",
        "listing_selectors": ["h3 a", "h2 a", ".views-row a", ".story a"],
        "time_budget_seconds": 20,
        "max_articles": 5,
    },
    {
        "name": "Deccan Chronicle Hyderabad",
        "url": "https://www.deccanchronicle.com/nation/",
        "type": "html",
        "category": "TELANGANA STATE AFFAIRS",
        "listing_selectors": ["h3 a", "h2 a", ".card-content a", ".story-card a"],
        "time_budget_seconds": 20,
        "max_articles": 5,
    },
    {
        "name": "MyGov India",
        "url": "https://www.mygov.in/",
        "type": "html",
        "category": "POLITY & GOVERNANCE",
        "listing_selectors": ["h3 a", "h2 a", ".views-row a", ".blog-list a"],
        "time_budget_seconds": 20,
        "max_articles": 4,
    },
    {
        "name": "Ministry of Finance",
        "url": "https://finmin.nic.in/",
        "type": "html",
        "category": "ECONOMY & FINANCE",
        "listing_selectors": ["h3 a", "h2 a", ".view-content a", ".news-event a"],
        "time_budget_seconds": 15,
        "max_articles": 4,
    },
    {
        "name": "Economic Times Economy",
        "url": "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",
        "type": "rss",
        "category": "ECONOMY & FINANCE",
        "time_budget_seconds": 20,
        "max_entries": 6,
        "fetch_full_content_limit": 1,
    },
    {
        "name": "Business Standard",
        "url": "https://www.business-standard.com/rss/home_page_top_stories.rss",
        "type": "rss",
        "category": "ECONOMY & FINANCE",
        "time_budget_seconds": 20,
        "max_entries": 6,
        "fetch_full_content_limit": 1,
    },
    {
        "name": "ISRO News",
        "url": "https://www.isro.gov.in/pressrelease.html",
        "type": "html",
        "category": "SCIENCE & TECHNOLOGY",
        "listing_selectors": [".views-row a", "h3 a", ".press-release a", ".item-list a"],
        "time_budget_seconds": 15,
        "max_articles": 4,
    },
    {
        "name": "DST India",
        "url": "https://dst.gov.in/whats-new/press-release",
        "type": "html",
        "category": "SCIENCE & TECHNOLOGY",
        "listing_selectors": [".view-content a", "h3 a", ".news-item a", ".item-list a"],
        "time_budget_seconds": 15,
        "max_articles": 4,
    },
]


def setup_logging() -> Path:
    """Configure console and daily file logging."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"daily_{datetime.now(IST).strftime('%Y-%m-%d')}.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return log_file
