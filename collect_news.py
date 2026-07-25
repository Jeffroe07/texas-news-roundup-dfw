from __future__ import annotations

import calendar
import hashlib
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus

import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "stories.json"
MAX_STORIES = 250
MAX_AGE_DAYS = 7

DFW_TERMS = (
    "dallas", "fort worth", "arlington", "plano", "frisco", "garland",
    "irving", "mckinney", "denton", "mesquite", "grand prairie",
    "carrollton", "richardson", "lewisville", "grapevine", "tarrant",
    "collin", "denton county", "dallas county", "north texas", "dfw"
)

CATEGORY_RULES = {
    "Weather": ("weather", "storm", "tornado", "hail", "flood", "heat", "freeze", "warning", "watch"),
    "Traffic": ("traffic", "crash", "wreck", "closure", "closed", "interstate", "highway", "freeway", "road"),
    "Police": ("police", "sheriff", "arrest", "shooting", "pursuit", "crime", "officer", "investigation"),
    "Fire": ("fire", "firefighters", "smoke", "explosion", "rescue"),
    "Sports": ("cowboys", "mavericks", "stars", "rangers", "fc dallas", "sports"),
}

GOOGLE_QUERIES = [
    ("Breaking", '("Dallas" OR "Fort Worth" OR "North Texas") when:2d'),
    ("Police", '("Dallas" OR "Fort Worth" OR Arlington OR Plano OR Frisco) (police OR sheriff OR shooting OR arrest OR pursuit) when:3d'),
    ("Traffic", '("Dallas" OR "Fort Worth" OR "North Texas") (traffic OR crash OR closure OR highway) when:2d'),
    ("Fire", '("Dallas" OR "Fort Worth" OR Arlington OR Plano) (fire OR firefighters OR explosion) when:3d'),
    ("Community", '("Dallas" OR "Fort Worth" OR "North Texas") community when:3d'),
    ("Sports", '("Dallas Cowboys" OR Mavericks OR "Texas Rangers" OR "Dallas Stars" OR "FC Dallas") when:3d'),
]

OFFICIAL_FEEDS = [
    {
        "name": "NWS Fort Worth — Significant Weather",
        "url": "https://www.weather.gov/rss_page.php?site_name=fwd",
        "category": "Weather",
        "official": True,
    },
]

def clean_html(value: str | None) -> str:
    return BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)

def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()

def parse_date(entry: dict) -> datetime:
    for key in ("published", "updated", "created"):
        if entry.get(key):
            try:
                dt = dateparser.parse(entry[key])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                pass
    for key in ("published_parsed", "updated_parsed"):
        if entry.get(key):
            try:
                return datetime.fromtimestamp(calendar.timegm(entry[key]), tz=timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)

def infer_category(title: str, summary: str, default: str) -> str:
    text = f"{title} {summary}".lower()
    for category, terms in CATEGORY_RULES.items():
        if any(term in text for term in terms):
            return category
    return default

def is_dfw_relevant(title: str, summary: str) -> bool:
    text = f"{title} {summary}".lower()
    return any(term in text for term in DFW_TERMS)

def source_from_google_title(title: str) -> tuple[str, str]:
    # Google News RSS titles often end with " - Publisher".
    if " - " in title:
        story_title, source = title.rsplit(" - ", 1)
        return story_title.strip(), source.strip()
    return title, "Google News"

def make_caption(story: dict) -> str:
    category_emoji = {
        "Weather": "🌪️",
        "Traffic": "🚧",
        "Police": "🚨",
        "Fire": "🚒",
        "Sports": "🏟️",
        "Community": "📍",
        "Breaking": "🔴",
    }
    emoji = category_emoji.get(story["category"], "📰")
    return (
        f"{emoji} {story['category'].upper()} — DFW\n\n"
        f"{story['title']}\n\n"
        f"Source: {story['source']}\n"
        f"Read more: {story['url']}\n\n"
        f"Texas News Roundup"
    )

def story_id(url: str, title: str) -> str:
    return hashlib.sha256(f"{url}|{title}".encode("utf-8", "ignore")).hexdigest()[:20]

def extract_thumbnail(entry: dict) -> str:
    if entry.get("media_thumbnail"):
        return entry["media_thumbnail"][0].get("url", "")
    if entry.get("media_content"):
        for item in entry["media_content"]:
            if item.get("medium") == "image" or str(item.get("type", "")).startswith("image/"):
                return item.get("url", "")
    return ""

def collect_feed(feed_url: str, default_category: str, source_name: str | None = None, official: bool = False):
    parsed = feedparser.parse(feed_url)
    stories = []
    for entry in parsed.entries[:50]:
        raw_title = normalize_space(clean_html(entry.get("title")))
        summary = normalize_space(clean_html(entry.get("summary") or entry.get("description")))[:800]
        url = entry.get("link", "").strip()
        if not raw_title or not url:
            continue

        if source_name:
            title, source = raw_title, source_name
        else:
            title, source = source_from_google_title(raw_title)

        if not is_dfw_relevant(title, summary) and not official:
            continue

        published = parse_date(entry)
        if published < datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS):
            continue

        story = {
            "id": story_id(url, title),
            "title": title,
            "url": url,
            "source": source,
            "summary": summary,
            "published_at": published.isoformat(),
            "category": infer_category(title, summary, default_category),
            "thumbnail": extract_thumbnail(entry),
            "official": official,
        }
        story["caption"] = make_caption(story)
        stories.append(story)
    return stories

def main():
    all_stories = []

    for category, query in GOOGLE_QUERIES:
        url = (
            "https://news.google.com/rss/search?q="
            + quote_plus(query)
            + "&hl=en-US&gl=US&ceid=US:en"
        )
        all_stories.extend(collect_feed(url, category))
        time.sleep(0.4)

    for feed in OFFICIAL_FEEDS:
        try:
            all_stories.extend(
                collect_feed(
                    feed["url"],
                    feed["category"],
                    source_name=feed["name"],
                    official=feed.get("official", False),
                )
            )
        except Exception as exc:
            print(f"Feed failed: {feed['name']}: {exc}")

    deduped = {}
    for story in all_stories:
        existing = deduped.get(story["id"])
        if not existing or story["published_at"] > existing["published_at"]:
            deduped[story["id"]] = story

    stories = sorted(
        deduped.values(),
        key=lambda item: item["published_at"],
        reverse=True,
    )[:MAX_STORIES]

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(stories),
        "stories": stories,
    }
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(stories)} stories to {DATA_FILE}")

if __name__ == "__main__":
    main()
