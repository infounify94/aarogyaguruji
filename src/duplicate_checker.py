"""
duplicate_checker.py
====================
Prevents duplicate article posting by tracking published topics.
Stores published topic slugs with dates in data/posted_topics.json.
Topics are blocked for 45 days before they can be reposted.
"""

import json
import hashlib
import re
from datetime import datetime, timedelta
import os
from pathlib import Path

# Use TRACKER_FILE env var if set, otherwise default to posted_topics.json
_tracker_filename = os.getenv("TRACKER_FILE", "posted_topics.json")
DATA_FILE = Path(__file__).parent.parent / "data" / _tracker_filename
COOLDOWN_DAYS = 45  # Days before a topic can be reposted


def _slugify(text: str) -> str:
    """Convert topic to a stable slug for comparison."""
    text = text.lower().strip()
    # Remove special chars, keep alphanumeric and spaces
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:100]  # limit length


def _load_data() -> dict:
    """Load the posted topics tracker file."""
    if not DATA_FILE.exists():
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        return {"posted": [], "last_updated": None, "total_posts": 0}
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_data(data: dict):
    """Save tracker data back to file."""
    data["last_updated"] = datetime.utcnow().isoformat()
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_duplicate(topic: str) -> bool:
    """
    Check if a topic was recently published.
    Returns True if topic was posted within COOLDOWN_DAYS.
    """
    data = _load_data()
    slug = _slugify(topic)
    cutoff = datetime.utcnow() - timedelta(days=COOLDOWN_DAYS)
    
    for entry in data["posted"]:
        if entry.get("slug") == slug:
            posted_at = datetime.fromisoformat(entry["posted_at"])
            if posted_at > cutoff:
                return True  # Recently posted - skip
    
    return False


def mark_as_posted(topic: str, url: str, title: str = ""):
    """Record a topic as successfully published."""
    data = _load_data()
    slug = _slugify(topic)
    
    # Remove any old entries for this slug
    data["posted"] = [e for e in data["posted"] if e.get("slug") != slug]
    
    # Add new entry
    data["posted"].append({
        "slug": slug,
        "topic": topic,
        "title": title,
        "url": url,
        "posted_at": datetime.utcnow().isoformat(),
    })
    
    data["total_posts"] = len(data["posted"])
    _save_data(data)
    print(f"✅ Tracked: '{topic}' → {url}")


def get_all_posted_slugs() -> set:
    """Return set of all posted slugs (regardless of cooldown)."""
    data = _load_data()
    return {entry["slug"] for entry in data["posted"]}


def filter_new_topics(topics: list) -> list:
    """Filter out duplicate topics from a list, return only fresh ones."""
    fresh = []
    for topic in topics:
        if not is_duplicate(topic):
            fresh.append(topic)
        else:
            print(f"⏭️  Skipping (recently posted): {topic}")
    return fresh


def get_stats() -> dict:
    """Return posting statistics."""
    data = _load_data()
    total = len(data["posted"])
    cutoff = datetime.utcnow() - timedelta(days=30)
    recent = sum(
        1 for e in data["posted"]
        if datetime.fromisoformat(e["posted_at"]) > cutoff
    )
    return {
        "total_posts": total,
        "posts_last_30_days": recent,
        "last_updated": data.get("last_updated"),
    }


if __name__ == "__main__":
    stats = get_stats()
    print(f"📊 Total posts tracked: {stats['total_posts']}")
    print(f"📊 Posts in last 30 days: {stats['posts_last_30_days']}")
