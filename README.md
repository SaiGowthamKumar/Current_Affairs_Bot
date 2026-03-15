# News Agent for UPSC and TSPSC

This project builds a fully automated current affairs digest for UPSC, TSPSC, Group-1, Group-2, and Telangana state exam preparation. It pulls fresh articles from national, Telangana-specific, governance, economy, and science sources every day, summarizes them with Groq, and emails a structured revision digest each morning.

## What This Project Does

- Scrapes RSS feeds and selected HTML pages from Indian news and government sources
- Filters out old and already-sent articles using a JSON tracker
- Categorizes articles into exam-relevant buckets
- Summarizes each article with Groq using a rigid exam-focused JSON format
- Builds a styled HTML digest with Telangana emphasis, glossary terms, and practice questions
- Sends the digest by Gmail SMTP
- Runs on demand with `--test` or automatically every day at `06:00 AM` IST
- Writes logs to `logs/daily_YYYY-MM-DD.log`
- Stops slow sources after a per-source time budget and retries failed requests a limited number of times

## Project Structure

```text
news_agent/
├── main.py
├── scraper.py
├── summarizer.py
├── email_sender.py
├── tracker.py
├── config.py
├── .env
├── sent_articles.json
├── requirements.txt
├── logs/
└── README.md
```

## Setup

1. Open a terminal inside the project folder:

```bash
cd "c:\Users\Shashi\Desktop\C++\Current Affairs\news_agent"
```

2. Create and activate a virtual environment if you want isolation:

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Fill in the `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GMAIL_SENDER_EMAIL=your_gmail@gmail.com
GMAIL_APP_PASSWORD=your_16_digit_gmail_app_password
RECIPIENT_EMAIL=your_email@gmail.com
SEND_TIME=06:00
```

Optional scraper tuning values:

```env
SOURCE_TIME_BUDGET_SECONDS=45
REQUEST_RETRY_ATTEMPTS=2
REQUEST_RETRY_BACKOFF_SECONDS=1
RSS_MAX_ENTRIES_PER_SOURCE=8
RSS_FULL_ARTICLE_FETCH_LIMIT=3
HTML_MAX_ARTICLES_PER_SOURCE=6
```

## Gmail App Password Setup

You must use a Gmail App Password, not your normal Gmail password.

1. Sign in to your Google account.
2. Go to `Google Account -> Security`.
3. Turn on `2-Step Verification` if it is not already enabled.
4. Return to the `Security` page.
5. Open `App passwords`.
6. Choose `Mail` as the app.
7. Choose your device or select `Other`.
8. Click `Generate`.
9. Copy the 16-character password Google shows.
10. Paste that value into `GMAIL_APP_PASSWORD` in `.env`.

## Run Manually for Testing

Use the manual mode first so you can verify scraping, summarization, and email delivery.

```bash
python main.py --test
```

Expected flow:

- `[1/4] Fetching news from all sources...`
- `[2/4] Summarizing with Groq AI...`
- `[3/4] Building email digest...`
- `[4/4] Sending email...`

If something fails, inspect the latest file in the `logs/` folder.

## Run in Production

Scheduled mode keeps the process alive and runs the digest every day at the configured time.

```bash
python main.py
```

Default schedule is `06:00 AM` IST. Change `SEND_TIME` in `.env` if needed.

## Free Deployment Options

### Railway.app

- Create a new project from your Git repo
- Set the start command to `python main.py`
- Add the `.env` values in Railway variables
- Keep the service running continuously so APScheduler stays alive

### Render.com

- Create a new `Background Worker`
- Point it to this repository
- Use build command: `pip install -r requirements.txt`
- Use start command: `python main.py`
- Add all environment variables in the dashboard

Note: free tiers can sleep or stop background jobs depending on plan limits. If that happens, use a cron-style service or an always-on VPS.

## GitHub Actions Deployment

This project includes a GitHub Actions workflow at `.github/workflows/daily-current-affairs-digest.yml`.

It is configured to:

- run every day at `06:00 AM IST`
- support manual runs through `workflow_dispatch`
- install dependencies on Python `3.11`
- execute `python main.py --test` so the job runs once and exits
- cache `sent_articles.json` so duplicate links are still tracked across runs

### Required GitHub Secrets

Add these secrets in your GitHub repository under `Settings -> Secrets and variables -> Actions`:

- `GROQ_API_KEY`
- `GROQ_MODEL`
- `GMAIL_SENDER_EMAIL`
- `GMAIL_APP_PASSWORD`
- `RECIPIENT_EMAIL`

Optional tuning secrets:

- `SOURCE_TIME_BUDGET_SECONDS`
- `REQUEST_RETRY_ATTEMPTS`
- `REQUEST_RETRY_BACKOFF_SECONDS`
- `RSS_MAX_ENTRIES_PER_SOURCE`
- `RSS_FULL_ARTICLE_FETCH_LIMIT`
- `HTML_MAX_ARTICLES_PER_SOURCE`

### GitHub Setup Steps

1. Push this `news_agent` folder to its own GitHub repository root.
2. Ensure the workflow file is present at `.github/workflows/daily-current-affairs-digest.yml`.
3. Add the required repository secrets.
4. Open the `Actions` tab and run the workflow once manually.
5. Verify that the digest email is sent correctly.

Schedule note:

- `06:00 AM IST` is `00:30 UTC`
- GitHub Actions cron uses UTC, so the workflow uses `30 0 * * *`

## Customization

To add more news sources:

1. Open `config.py`
2. Add another dictionary in `NEWS_SOURCES`
3. Use `type: "rss"` where possible
4. For HTML sources, add `listing_selectors` that match article links
5. If needed, expand `CATEGORY_KEYWORDS` so categorization improves

Example source entry:

```python
{
    "name": "Example Source",
    "url": "https://example.com/feed.xml",
    "type": "rss",
    "category": "CURRENT AFFAIRS GENERAL",
}
```

## Troubleshooting

### `GROQ_API_KEY is not configured`

- Check that `.env` exists in the project root
- Confirm the key name is exactly `GROQ_API_KEY`
- Restart the process after editing `.env`

### Gmail authentication fails

- Confirm you used an App Password, not your Gmail password
- Make sure 2FA is enabled
- Re-generate the App Password if needed

### No articles found

- Some sites may have changed RSS endpoints or HTML structure
- Inspect the log file in `logs/`
- Update `listing_selectors` in `config.py` for affected HTML sources

### Scraping is too slow

- Reduce `SOURCE_TIME_BUDGET_SECONDS` to cut off slow sources faster
- Reduce `REQUEST_RETRY_ATTEMPTS` if you want the run to fail fast on weak sites
- Lower `DELAY_BETWEEN_REQUESTS` carefully if you want more speed, but keep requests respectful

### Articles are skipped

- Some URLs may already exist in `sent_articles.json`
- Groq failures are skipped intentionally so one bad article does not stop the run
- Paywalled articles fall back to title and meta description where possible

### Scheduler did not run

- Keep the process alive with `python main.py`
- Verify your host machine or server stayed online
- Confirm `SEND_TIME` uses `HH:MM` 24-hour format

## Notes

- RSS is preferred over HTML scraping to reduce load and improve stability
- Scrapers use a polite user-agent and delays between requests
- The sent article tracker keeps only the last 7 days of URLs
- This digest is for preparation support and should be reviewed before high-stakes exam use
