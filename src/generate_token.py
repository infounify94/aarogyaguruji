"""
generate_token.py
=================
One-time OAuth2 token generator for Blogger API.
Run this script ONCE on your local machine to get your REFRESH_TOKEN.
Copy the printed REFRESH_TOKEN into your .env file and GitHub Secrets.

Usage:
    python src/generate_token.py
"""
import sys
import io
# Fix Windows console encoding for Unicode
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Blogger API scope
SCOPES = ["https://www.googleapis.com/auth/blogger"]

# Look for client_secret.json in project root
PROJECT_ROOT = Path(__file__).parent.parent
CLIENT_SECRET_FILES = list(PROJECT_ROOT.glob("client_secret*.json"))


def find_client_secret():
    """Find the client_secret.json file."""
    if CLIENT_SECRET_FILES:
        return str(CLIENT_SECRET_FILES[0])
    
    # Also check for plain client_secret.json
    plain = PROJECT_ROOT / "client_secret.json"
    if plain.exists():
        return str(plain)
    
    raise FileNotFoundError(
        "❌ client_secret.json not found in project root!\n"
        "   Download it from Google Cloud Console:\n"
        "   https://console.cloud.google.com/apis/credentials"
    )


def generate_tokens():
    """Run OAuth2 flow and print tokens."""
    print("=" * 60)
    print("  AarogyaGuruji - OAuth2 Token Generator")
    print("=" * 60)
    print()

    client_secret_path = find_client_secret()
    print(f"[OK] Found credentials: {Path(client_secret_path).name}")
    print()
    print("[*] Opening browser for Google authentication...")
    print("    Please login with the Google account that owns your blog.")
    print()

    # Run the OAuth flow - opens browser automatically
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secret_path,
        scopes=SCOPES,
        redirect_uri="http://localhost"
    )
    
    credentials = flow.run_local_server(
        port=0,
        prompt="consent",
        access_type="offline"
    )

    print()
    print("=" * 60)
    print("  [SUCCESS] Authentication Successful!")
    print("=" * 60)
    print()
    print("ACCESS TOKEN (expires in ~1 hour):")
    print(f"   {credentials.token}")
    print()
    print("REFRESH TOKEN (permanent - COPY THIS!):")
    print(f"   {credentials.refresh_token}")
    print()
    print("CLIENT ID:")
    print(f"   {credentials.client_id}")
    print()
    print("CLIENT SECRET:")
    print(f"   {credentials.client_secret}")
    print()
    print("=" * 60)
    print("  NEXT STEPS:")
    print("=" * 60)
    print()
    print("1. Copy the REFRESH TOKEN above")
    print("2. Add it to your .env file:")
    print("   GOOGLE_REFRESH_TOKEN=<paste the token here>")
    print()
    print("3. Add these GitHub Secrets:")
    print("   GOOGLE_REFRESH_TOKEN = <refresh token>")
    print("   GOOGLE_CLIENT_ID     = <client id>")
    print("   GOOGLE_CLIENT_SECRET = <client secret>")
    print()

    # Save to token.json for local use
    token_path = PROJECT_ROOT / "token.json"
    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": SCOPES
    }
    
    with open(token_path, "w", encoding="utf-8") as f:
        json.dump(token_data, f, indent=2)
    
    print(f"[SAVED] Tokens also saved to: token.json (local use only, gitignored)")
    print()
    print("[!] IMPORTANT: Never share your REFRESH TOKEN publicly!")
    print("=" * 60)


if __name__ == "__main__":
    generate_tokens()
