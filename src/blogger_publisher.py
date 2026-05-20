"""
blogger_publisher.py
====================
Authenticates with Blogger API v3 using OAuth2 refresh token
and publishes articles to the specified blog.

No browser interaction needed - uses refresh token only.
"""

import os
from google.oauth2.credentials import Credentials
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


def publish_post(title: str, body_html: str, tags: list = None, draft: bool = False) -> dict:
    """
    Publish a new post to the Blogger blog.
    
    Args:
        title: Post title (Telugu)
        body_html: Full HTML content of the post
        tags: List of label/tag strings
        draft: If True, save as draft instead of publishing
    
    Returns:
        dict with: id, url, title, published
    """
    service = _get_blogger_service()
    
    post_body = {
        "kind": "blogger#post",
        "title": title,
        "content": body_html,
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
