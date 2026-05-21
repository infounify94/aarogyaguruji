"""
blogger_publisher.py
====================
Authenticates with Blogger API v3 using OAuth2 refresh token
and publishes articles to the specified blog.

No browser interaction needed - uses refresh token only.
"""

import re
import os
import json
from datetime import datetime


def _build_schema_json(title: str, body_html: str, url_hint: str = "") -> str:
    """
    Build Article + FAQ Schema JSON-LD for Google rich results.
    FAQ Schema makes questions appear as expandable dropdowns in Google Search.
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Extract FAQ Q&A pairs from the article HTML (our card-style FAQ block)
    faq_items = []
    # Match: ► Question text ... answer text
    qa_pairs = re.findall(
        r'&#9658;\s*([^<]+)</p>\s*<p[^>]*>([^<]+)</p>',
        body_html, re.DOTALL
    )
    for question, answer in qa_pairs[:5]:  # max 5 FAQ items for Schema
        q = question.strip()
        a = re.sub(r'<[^>]+>', '', answer).strip()
        if q and a and len(q) > 10:
            faq_items.append({"@type": "Question", "name": q,
                               "acceptedAnswer": {"@type": "Answer", "text": a}})

    schemas = []

    # Article Schema
    article_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title[:110],
        "inLanguage": "te",
        "author": {"@type": "Organization", "name": "AarogyaGuruji",
                   "url": "https://aarogyaguruji.blogspot.com"},
        "publisher": {"@type": "Organization", "name": "AarogyaGuruji",
                      "url": "https://aarogyaguruji.blogspot.com"},
        "datePublished": today,
        "dateModified": today,
    }
    schemas.append(article_schema)

    # FAQ Schema (only if we found Q&A pairs)
    if faq_items:
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_items
        }
        schemas.append(faq_schema)

    blocks = "".join(
        f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False, indent=2)}</script>\n'
        for s in schemas
    )
    return blocks



from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

BLOG_ID = os.getenv("BLOG_ID", "707690830658262263")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN", "")

BLOGGER_SCOPES = ["https://www.googleapis.com/auth/blogger"]
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _get_credentials() -> Credentials:
    """Build OAuth2 credentials from environment variables (no browser)."""
    if not all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN]):
        raise ValueError(
            "Missing OAuth2 credentials! Set these environment variables:\n"
            "  GOOGLE_CLIENT_ID\n"
            "  GOOGLE_CLIENT_SECRET\n"
            "  GOOGLE_REFRESH_TOKEN\n"
            "Run 'python src/generate_token.py' to get your refresh token."
        )
    
    credentials = Credentials(
        token=None,  # Will be refreshed automatically
        refresh_token=GOOGLE_REFRESH_TOKEN,
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        token_uri=TOKEN_URI,
        scopes=BLOGGER_SCOPES,
    )
    
    # Refresh to get a fresh access token
    credentials.refresh(Request())
    return credentials


def _get_blogger_service():
    """Build the Blogger API service client."""
    credentials = _get_credentials()
    service = build("blogger", "v3", credentials=credentials)
    return service


def publish_post(title: str, body_html: str, tags: list = None, draft: bool = False, english_slug: str = None) -> dict:
    """
    Publish a new post to the Blogger blog.
    
    Args:
        title: Post title (Telugu)
        body_html: Full HTML content of the post
        tags: List of label/tag strings
        draft: If True, save as draft instead of publishing
        english_slug: English title to set as temporary title to generate a clean URL
    
    Returns:
        dict with: id, url, title, published
    """
    service = _get_blogger_service()
    
    # If an English slug is provided and we are publishing, use it as the initial title for the URL
    initial_title = english_slug if (english_slug and not draft) else title
    
    # Inject Schema JSON-LD at the very top of the post body
    schema_html = _build_schema_json(title, body_html)
    body_with_schema = schema_html + body_html

    post_body = {
        "kind": "blogger#post",
        "title": initial_title,
        "content": body_with_schema,
    }
    
    if tags:
        post_body["labels"] = tags[:20]  # Max 20 labels in Blogger
    
    try:
        if draft:
            result = service.posts().insert(
                blogId=BLOG_ID,
                body=post_body,
                isDraft=True
            ).execute()
            status = "DRAFT"
        else:
            result = service.posts().insert(
                blogId=BLOG_ID,
                body=post_body,
                isDraft=False,
                fetchBody=False
            ).execute()
            status = "PUBLISHED"
            
            # If we used a temporary English slug, immediately patch it back to the real Telugu title
            if english_slug and initial_title != title:
                post_id = result.get("id")
                print(f"🔄 Updating title from slug '{initial_title}' to '{title}'...")
                result = service.posts().patch(
                    blogId=BLOG_ID,
                    postId=post_id,
                    body={"title": title}
                ).execute()
        
        post_url = result.get("url", "")
        post_id = result.get("id", "")
        published = result.get("published", "")
        
        print(f"✅ Post {status}: {title}")
        print(f"   URL: {post_url}")
        
        return {
            "id": post_id,
            "url": post_url,
            "title": title,
            "published": published,
            "status": status,
        }
    
    except HttpError as e:
        error_content = e.content.decode("utf-8") if e.content else str(e)
        print(f"❌ Blogger API Error: {e.resp.status} - {error_content}")
        raise


def get_blog_info() -> dict:
    """Get basic blog information to verify connection."""
    service = _get_blogger_service()
    blog = service.blogs().get(blogId=BLOG_ID).execute()
    return {
        "name": blog.get("name"),
        "url": blog.get("url"),
        "posts": blog.get("posts", {}).get("totalItems", 0),
        "id": blog.get("id"),
    }


def get_recent_posts(count: int = 10) -> list:
    """Fetch recent post titles for duplicate checking."""
    service = _get_blogger_service()
    result = service.posts().list(
        blogId=BLOG_ID,
        maxResults=count,
        status="live",
        fields="items(title,url,published)"
    ).execute()
    
    return result.get("items", [])


if __name__ == "__main__":
    print("Testing Blogger API connection...")
    info = get_blog_info()
    print(f"Blog: {info['name']}")
    print(f"URL: {info['url']}")
    print(f"Total posts: {info['posts']}")
