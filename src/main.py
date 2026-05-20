"""
main.py
=======
Main orchestrator for AarogyaGuruji automated blogging.
Called by GitHub Actions 3 times per day.

Schedule (IST):
  - 07:00 AM IST (01:30 UTC)  - Morning batch
  - 01:00 PM IST (07:30 UTC)  - Afternoon batch
  - 07:00 PM IST (13:30 UTC)  - Evening batch

Each run publishes ARTICLES_PER_RUN articles (default: 7).
Total: ~21 articles/day.
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Add src dir to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from discover_topics import get_trending_topics
from content_generator import generate_article, inject_image
from image_fetcher import fetch_image
from blogger_publisher import publish_post, get_blog_info
from duplicate_checker import filter_new_topics, mark_as_posted, get_stats

import json

def get_past_urls(count: int = 5) -> list:
    """Fetch the latest published URLs from tracker for internal linking."""
    try:
        tracker_file = Path(__file__).parent.parent / "data" / "posted_topics.json"
        if not tracker_file.exists():
            return []
        with open(tracker_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        posted = data.get("posted", [])
        # Get the latest 'count' posts
        recent = posted[:count] if posted else []
        return [{"title": p["title"], "url": p["url"]} for p in recent]
    except Exception as e:
        log.warning(f"⚠️ Could not load past URLs for internal linking: {e}")
        return []

# ============================================================
# Configuration
# ============================================================
ARTICLES_PER_RUN = int(os.getenv("ARTICLES_PER_RUN", "7"))
BLOG_ID = os.getenv("BLOG_ID", "707690830658262263")
DELAY_BETWEEN_POSTS = 45  # seconds between posts (rate limiting)

# ============================================================
# Logging Setup
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("aarogyaguruji")


def run_batch():
    """Run one batch of article generation and publishing."""
    
    start_time = datetime.utcnow()
    log.info("=" * 65)
    log.info("  🏥 AarogyaGuruji - Auto Publisher Starting")
    log.info(f"  Time: {start_time.strftime('%Y-%m-%d %H:%M UTC')}")
    log.info(f"  Target: {ARTICLES_PER_RUN} articles this run")
    log.info("=" * 65)
    
    # --- Step 1: Verify blog connection ---
    log.info("\n📡 Verifying Blogger API connection...")
    try:
        blog_info = get_blog_info()
        log.info(f"   ✅ Blog: {blog_info['name']} ({blog_info['posts']} posts)")
    except Exception as e:
        log.error(f"   ❌ Blogger connection failed: {e}")
        sys.exit(1)
    
    # --- Step 2: Show statistics ---
    stats = get_stats()
    log.info(f"\n📊 Statistics:")
    log.info(f"   Total posts ever: {stats['total_posts']}")
    log.info(f"   Posts last 30 days: {stats['posts_last_30_days']}")
    
    # --- Step 3: Get topics ---
    log.info(f"\n🎯 Discovering topics (need {ARTICLES_PER_RUN})...")
    candidate_topics = get_trending_topics(count=ARTICLES_PER_RUN * 3)  # 3x buffer for filtering
    fresh_topics = filter_new_topics(candidate_topics)
    
    if not fresh_topics:
        log.warning("⚠️  No fresh topics found! All recent topics already posted.")
        log.info("    Getting more topics from extended pool...")
        candidate_topics = get_trending_topics(count=ARTICLES_PER_RUN * 5)
        fresh_topics = filter_new_topics(candidate_topics)
    
    topics_to_publish = fresh_topics[:ARTICLES_PER_RUN]
    log.info(f"   📋 Publishing {len(topics_to_publish)} topics")
    
    # --- Step 4: Generate & Publish ---
    published = []
    failed = []
    
    for i, topic in enumerate(topics_to_publish, 1):
        log.info(f"\n{'='*50}")
        log.info(f"  Article {i}/{len(topics_to_publish)}: {topic}")
        log.info(f"{'='*50}")
        
        try:
            # Get past URLs for internal linking
            past_urls = get_past_urls(count=5)
            
            # Generate article
            article = generate_article(topic, past_urls=past_urls)
            
            # Fetch image
            try:
                image = fetch_image(topic)
                final_html = inject_image(article["body_html"], image["html"])
            except Exception as img_err:
                log.warning(f"⚠️  Image fetch failed: {img_err} — publishing without image")
                final_html = article["body_html"]
            
            # Publish to Blogger
            result = publish_post(
                title=article["title"],
                body_html=final_html,
                tags=article["tags"],
                draft=False,
                english_slug=article.get("slug")
            )
            
            # Track publication
            mark_as_posted(topic, result["url"], result["title"])
            
            published.append({
                "topic": topic,
                "title": result["title"],
                "url": result["url"],
            })
            
            log.info(f"✅ Published [{i}]: {result['url']}")
            
            # Rate limiting delay (except after last article)
            if i < len(topics_to_publish):
                log.info(f"⏳ Waiting {DELAY_BETWEEN_POSTS}s before next article...")
                time.sleep(DELAY_BETWEEN_POSTS)
        
        except Exception as e:
            log.error(f"❌ Failed [{i}] '{topic}': {e}")
            failed.append({"topic": topic, "error": str(e)})
            # Small delay even on failure
            time.sleep(10)
            continue
    
    # --- Step 5: Final Report ---
    end_time = datetime.utcnow()
    duration = (end_time - start_time).seconds // 60
    
    log.info("\n" + "=" * 65)
    log.info("  📊 Run Complete!")
    log.info("=" * 65)
    log.info(f"  ✅ Published: {len(published)} articles")
    log.info(f"  ❌ Failed:    {len(failed)} articles")
    log.info(f"  ⏱️  Duration: ~{duration} minutes")
    log.info("")
    
    if published:
        log.info("Published articles:")
        for p in published:
            log.info(f"  → {p['url']}")
    
    if failed:
        log.info("\nFailed topics:")
        for f in failed:
            log.info(f"  ✗ {f['topic']}: {f['error']}")
    
    log.info("=" * 65)
    
    # Exit with error code if all failed
    if failed and not published:
        log.error("All articles failed to publish!")
        sys.exit(1)
    
    return published, failed


if __name__ == "__main__":
    run_batch()
