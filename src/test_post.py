"""
test_post.py
============
Manual test script to verify the entire pipeline works.
Generates and publishes a single test article to your blog.

Usage:
    python src/test_post.py

Requirements:
    - .env file with all credentials (see .env.example)
    - OR environment variables set directly
"""

import os
import sys
import io

# Fix Windows console encoding for Unicode emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', write_through=True)

from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from content_generator import generate_article, inject_image
from image_fetcher import fetch_image
from blogger_publisher import get_blog_info, publish_post
from duplicate_checker import mark_as_posted

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
        recent = posted[:count] if posted else []
        return [{"title": p["title"], "url": p["url"]} for p in recent]
    except Exception as e:
        print(f"   ⚠️ Could not load past URLs for internal linking: {e}")
        return []

# Test article topic
TEST_TOPIC = "తులసి ఆకుల ఔషధ గుణాలు - 10 వ్యాధులకు రామబాణం"

# Blog ID
BLOG_ID = os.getenv("BLOG_ID", "707690830658262263")


def run_test():
    print("=" * 65)
    print("  AarogyaGuruji - Test Post Publisher")
    print("=" * 65)
    print()
    
    # Step 1: Verify blog connection
    print("📡 Step 1: Connecting to Blogger API...")
    try:
        blog_info = get_blog_info()
        print(f"   ✅ Connected to: {blog_info['name']}")
        print(f"   📊 Total posts: {blog_info['posts']}")
        print(f"   🌐 URL: {blog_info['url']}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print()
        print("   Check your .env file has:")
        print("   - GOOGLE_CLIENT_ID")
        print("   - GOOGLE_CLIENT_SECRET")
        print("   - GOOGLE_REFRESH_TOKEN")
        sys.exit(1)
    
    print()
    
    # Step 2: Generate article
    print(f"✍️  Step 2: Generating article...")
    print(f"   Topic: {TEST_TOPIC}")
    try:
        past_urls = get_past_urls(count=5)
        article = generate_article(TEST_TOPIC, past_urls=past_urls)
        print(f"   ✅ Generated: '{article['title']}'")
        print(f"   📝 Length: {len(article['body_html'])} chars")
        print(f"   🏷️  Tags: {', '.join(article['tags'][:5])}...")
    except Exception as e:
        print(f"   ❌ Generation failed: {e}")
        sys.exit(1)
    
    print()
    
    # Step 3: Fetch image
    print("🖼️  Step 3: Fetching Pexels image...")
    try:
        image = fetch_image(TEST_TOPIC)
        print(f"   ✅ Image: {image['url'][:60]}...")
        print(f"   📸 By: {image['photographer']}")
        
        # Inject image into article
        final_html = inject_image(article["body_html"], image["html"])
    except Exception as e:
        print(f"   ⚠️  Image fetch failed (using article without image): {e}")
        final_html = article["body_html"]
    
    print()
    
    # Step 4: Publish
    print("📤 Step 4: Publishing to Blogger...")
    print(f"   Blog ID: {BLOG_ID}")
    try:
        result = publish_post(
            title=article["title"],
            body_html=final_html,
            tags=article["tags"],
            draft=False,  # Change to True to save as draft for testing
            english_slug=article.get("slug")
        )
        
        print()
        print("=" * 65)
        print("  🎉 SUCCESS! Article Published!")
        print("=" * 65)
        print(f"  📌 Title   : {result['title']}")
        print(f"  🌐 URL     : {result['url']}")
        print(f"  🆔 Post ID : {result['id']}")
        print(f"  📅 Published: {result['published']}")
        print()
        
        # Track it
        mark_as_posted(TEST_TOPIC, result["url"], result["title"])
        
        print("✅ Test completed successfully!")
        return result
    
    except Exception as e:
        print(f"   ❌ Publishing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_test()
