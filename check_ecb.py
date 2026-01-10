import os
import json
from pathlib import Path

import feedparser
import requests

SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK_URL"]

ECB_FEEDS = {
    "press": "https://www.ecb.europa.eu/rss/press.html",
    "blog": "https://www.ecb.europa.eu/rss/blog.html",
    "publications": "https://www.ecb.europa.eu/rss/pub.html",
    "statistics": "https://www.ecb.europa.eu/rss/statpress.html",
    "working_papers": "https://www.ecb.europa.eu/rss/wppub.html",
    "operations": "https://www.ecb.europa.eu/rss/operations.html",
}

SEEN_FILE = Path("seen.json")


def load_seen() -> set[str]:
    if not SEEN_FILE.exists():
        return set()
    try:
        data = json.loads(SEEN_FILE.read_text(encoding="utf-8"))
        return set(data) if isinstance(data, list) else set()
    except Exception:
        return set()


def save_seen(seen: set[str]) -> None:
    SEEN_FILE.write_text(json.dumps(sorted(seen)), encoding="utf-8")


def post_slack(title: str, link: str, category: str) -> None:
    payload = {"text": f"*ECB update ({category})*\n<{link}|{title}>"}
    r = requests.post(SLACK_WEBHOOK, json=payload, timeout=20)
    r.raise_for_status()


def entry_uid(entry) -> str:
    # Prefer stable unique IDs if present; otherwise fall back to link
    return entry.get("id") or entry.get("guid") or entry.get("link") or ""


def main() -> None:
    seen = load_seen()
    new_seen = set(seen)

    for category, url in ECB_FEEDS.items():
        feed = feedparser.parse(url)

        # If feed fetch fails, feed.bozo may be True; we keep going anyway.
        for entry in feed.entries:
            uid = entry_uid(entry)
            if not uid:
                continue

            if uid not in seen:
                title = entry.get("title", "(no title)")
                link = entry.get("link", "")
                if link:
                    post_slack(title, link, category)
                new_seen.add(uid)

    if new_seen != seen:
        save_seen(new_seen)


if __name__ == "__main__":
    main()
