"""
sitemap_generator.py
====================
Generates a complete XML sitemap for the Blogger blog by fetching
ALL published post URLs via the Blogger API (no 500-post limit).

Saves to: public/sitemap.xml
Hosted via GitHub Pages at:
  https://infounify94.github.io/aarogyaguruji/sitemap.xml

Submit that URL once to Google Search Console — it auto-updates every run.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Fix protobuf crash on Python 3.14
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

BLOG_ID               = os.getenv("BLOG_ID", "707690830658262263")
GOOGLE_CLIENT_ID      = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET  = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN  = os.getenv("GOOGLE_REFRESH_TOKEN", "")
TOKEN_URI             = "https://oauth2.googleapis.com/token"
BLOGGER_SCOPES        = ["https://www.googleapis.com/auth/blogger"]

OUTPUT_PATH = Path(__file__).parent.parent / "sitemap.xml"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def _get_service():
    creds = Credentials(
        token=None,
        refresh_token=GOOGLE_REFRESH_TOKEN,
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        token_uri=TOKEN_URI,
        scopes=BLOGGER_SCOPES,
    )
    creds.refresh(Request())
    return build("blogger", "v3", credentials=creds)


# ---------------------------------------------------------------------------
# Fetch ALL posts (paginated, no limit)
# ---------------------------------------------------------------------------

def fetch_all_posts(service) -> list:
    """
    Fetch every published post URL from the blog.
    Blogger paginates at 500 per page — we loop until no more pages.
    Returns list of dicts: {url, published, updated}
    """
    posts = []
    page_token = None
    page_num = 0

    while True:
        page_num += 1
        params = dict(
            blogId=BLOG_ID,
            status="LIVE",
            maxResults=500,
            fields="nextPageToken,items(url,published,updated)",
            orderBy="PUBLISHED",
        )
        if page_token:
            params["pageToken"] = page_token

        result = service.posts().list(**params).execute()
        items  = result.get("items", [])
        posts.extend(items)

        print(f"  📄 Page {page_num}: fetched {len(items)} posts (total so far: {len(posts)})")

        page_token = result.get("nextPageToken")
        if not page_token:
            break   # no more pages

    return posts


# ---------------------------------------------------------------------------
# Build XML
# ---------------------------------------------------------------------------

def _iso_date(dt_str: str) -> str:
    """Return YYYY-MM-DD from a Blogger ISO datetime string."""
    try:
        return dt_str[:10]
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def build_sitemap_xml(posts: list) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    url_entries = []
    for post in posts:
        url  = post.get("url", "").strip()
        mod  = _iso_date(post.get("updated", post.get("published", today)))
        if not url:
            continue
        url_entries.append(
            f"""  <url>
    <loc>{url}</loc>
    <lastmod>{mod}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>"""
        )

    entries_xml = "\n".join(url_entries)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries_xml}
</urlset>
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_sitemap() -> int:
    """Generate sitemap and save to public/sitemap.xml. Returns post count."""
    print("\n🗺️  Generating sitemap...")

    if not all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN]):
        print("❌  Missing Google credentials — skipping sitemap generation")
        return 0

    try:
        service = _get_service()
        posts   = fetch_all_posts(service)

        if not posts:
            print("⚠️  No posts found — sitemap not updated")
            return 0

        xml = build_sitemap_xml(posts)

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(xml, encoding="utf-8")

        print(f"✅  Sitemap saved: {OUTPUT_PATH}")
        print(f"   Total URLs: {len(posts)}")
        print(f"   GitHub Pages URL: https://infounify94.github.io/aarogyaguruji/sitemap.xml")

        return len(posts)

    except Exception as e:
        print(f"❌  Sitemap generation failed: {e}")
        return 0


if __name__ == "__main__":
    count = generate_sitemap()
    sys.exit(0 if count > 0 else 1)
