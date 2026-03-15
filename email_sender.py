"""Build and send the current affairs email digest."""

from __future__ import annotations

import html
import logging
import smtplib
from collections import defaultdict
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from config import (
    DISPLAY_SECTION_COLORS,
    DISPLAY_SECTION_MAP,
    DISPLAY_SECTION_ORDER,
    GMAIL_APP_PASSWORD,
    GMAIL_SENDER_EMAIL,
    IST,
)

logger = logging.getLogger(__name__)


class NewsEmailSender:
    """Format and send HTML email digests."""

    def _slugify(self, value: str) -> str:
        return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")

    def _build_display_sections(
        self,
        grouped_summaries: dict[str, list[dict[str, Any]]],
    ) -> dict[str, list[dict[str, Any]]]:
        grouped_display: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for category, articles in grouped_summaries.items():
            section = DISPLAY_SECTION_MAP.get(category, "NATIONAL NEWS MAIN POINTS")
            grouped_display[section].extend(articles)
        return dict(grouped_display)

    def _build_plain_text(
        self,
        grouped_summaries: dict[str, list[dict[str, Any]]],
        date: str,
    ) -> str:
        display_sections = self._build_display_sections(grouped_summaries)
        lines = [
            f"Daily Current Affairs Digest - {date}",
            "Main points only",
            "",
        ]
        for section in DISPLAY_SECTION_ORDER:
            entries = display_sections.get(section, [])
            if not entries:
                continue
            lines.append(section)
            lines.append("-" * len(section))
            for item in entries:
                lines.append(item["headline"])
                for point in item.get("key_points", []):
                    lines.append(f"  - {point}")
                lines.append(f"  Source: {item['source_name']}")
                lines.append("")
        return "\n".join(lines)

    def build_html_email(
        self,
        grouped_summaries: dict[str, list[dict[str, Any]]],
        date: datetime,
    ) -> str:
        display_sections = self._build_display_sections(grouped_summaries)
        formatted_date = date.strftime("%A, %d %B %Y")
        total_articles = sum(len(items) for items in display_sections.values())

        summary_pills = []
        category_sections = []
        for section in DISPLAY_SECTION_ORDER:
            items = display_sections.get(section, [])
            if not items:
                continue
            color = DISPLAY_SECTION_COLORS.get(section, "#6b7280")
            anchor = self._slugify(section)
            summary_pills.append(
                f'<a href="#{anchor}" style="text-decoration:none;display:inline-block;background:{color};'
                'color:#ffffff;padding:8px 14px;border-radius:999px;margin:4px;font-size:12px;font-weight:700;">'
                f"{html.escape(section.title())}: {len(items)}</a>"
            )

            article_cards = []
            for item in items:
                bullets = "".join(
                    f'<li style="margin:0 0 8px 0;color:#1f2937;"><span style="color:{color};font-size:18px;">'
                    f'&#8226;</span> {html.escape(point)}</li>'
                    for point in item.get("key_points", [])
                )
                article_cards.append(
                    '<div style="padding:18px 0;border-bottom:1px solid #e5e7eb;">'
                    f'<div style="font-size:14px;font-weight:700;color:#111827;margin-bottom:6px;">{html.escape(item["headline"])}</div>'
                    f'<ul style="padding-left:16px;margin:0 0 14px 0;font-size:12px;line-height:1.6;">{bullets}</ul>'
                    f'<div style="font-size:11px;color:#6b7280;">Source: {html.escape(item["source_name"])} | '
                    f'<a href="{html.escape(item["url"])}" style="color:{color};">Read original</a></div>'
                    "</div>"
                )

            category_sections.append(
                f'<div id="{anchor}" style="background:#ffffff;border:1px solid #e5e7eb;border-left:6px solid {color};'
                'border-radius:16px;padding:20px;margin-bottom:18px;">'
                f'<div style="font-size:18px;font-weight:800;color:#111827;margin-bottom:6px;">{html.escape(section)}</div>'
                f'<div style="font-size:12px;color:#6b7280;margin-bottom:8px;">{len(items)} main stories</div>'
                f'{"".join(article_cards)}'
                "</div>"
            )

        return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Daily Current Affairs Digest</title>
</head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif;color:#111827;">
  <div style="max-width:880px;margin:0 auto;padding:24px 12px;">
    <div style="background:#1a1a3e;border-radius:24px;padding:28px 24px;color:#ffffff;">
      <div style="font-size:28px;font-weight:800;margin-bottom:8px;">Daily Current Affairs Digest</div>
      <div style="font-size:14px;opacity:0.92;margin-bottom:6px;">Newspaper-style brief with only the main points</div>
      <div style="font-size:13px;opacity:0.88;margin-bottom:4px;">{formatted_date}</div>
      <div style="font-size:12px;opacity:0.76;margin-bottom:16px;">International, national, state, sports, business and entertainment at a glance</div>
      <span style="display:inline-block;background:#ffffff;color:#1a1a3e;border-radius:999px;padding:8px 14px;font-size:12px;font-weight:800;">
        Total Articles: {total_articles}
      </span>
    </div>

    <div style="background:#ffffff;border-radius:18px;padding:18px 16px;margin-top:18px;border:1px solid #e5e7eb;">
      <div style="font-size:14px;font-weight:800;color:#111827;margin-bottom:8px;">Quick Summary</div>
      {"".join(summary_pills)}
    </div>

    <div style="margin-top:18px;">
      {"".join(category_sections)}
    </div>

    <div style="font-size:11px;color:#6b7280;text-align:center;padding:18px 8px 8px 8px;line-height:1.7;">
      <div>This digest is auto-generated and formatted as short newspaper-style main points.</div>
      <div>If you no longer want these emails, remove your address from the configured recipient.</div>
      <div>Generated at {datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S %Z")}.</div>
      <div>Sources: The Hindu, Indian Express, PIB, Telangana Today, The Hans India, Sakshi, Deccan Chronicle, MyGov, Ministry of Finance, Economic Times, Business Standard, ISRO, DST.</div>
    </div>
  </div>
</body>
</html>
"""

    def send_email(
        self,
        html_content: str,
        recipient_email: str,
        date: datetime,
        grouped_summaries: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        if not GMAIL_SENDER_EMAIL or not GMAIL_APP_PASSWORD:
            raise RuntimeError("Gmail credentials are not configured")

        subject = f"[Daily Current Affairs] {date.strftime('%d %b %Y')} | UPSC+TSPSC Ready"
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = GMAIL_SENDER_EMAIL
        message["To"] = recipient_email

        plain_text = self._build_plain_text(
            grouped_summaries or {},
            date.strftime("%A, %d %B %Y"),
        )
        message.attach(MIMEText(plain_text, "plain", "utf-8"))
        message.attach(MIMEText(html_content, "html", "utf-8"))

        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                server.starttls()
                server.login(GMAIL_SENDER_EMAIL, GMAIL_APP_PASSWORD)
                server.sendmail(GMAIL_SENDER_EMAIL, [recipient_email], message.as_string())
            logger.info("Email sent successfully to %s", recipient_email)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Email sending failed: %s", exc)
            raise
