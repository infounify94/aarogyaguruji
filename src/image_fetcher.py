"""
image_fetcher.py
================
Fetches health-related images from Pexels API.
Returns image URL and attribution HTML for embedding in articles.
Pexels attribution is included as required by Pexels license.
"""

import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PEXELS_BASE_URL = "https://api.pexels.com/v1"

# Keyword mapping from Telugu topics to English Pexels search terms
KEYWORD_MAPPING = {
    "అయుర్వేద": "ayurveda herbs medicine",
    "ఆయుర్వేద": "ayurveda herbs medicine",
    "యోగ": "yoga meditation wellness",
    "ధ్యాన": "meditation peace mindfulness",
    "గుండె": "heart health cardio",
    "రక్తపోటు": "blood pressure health",
    "డయాబెటిస్": "diabetes healthy food",
    "మధుమేహం": "diabetes healthy food",
    "క్యాన్సర్": "cancer awareness ribbon",
    "కిడ్నీ": "kidney health organs",
    "లివర్": "liver health detox",
    "ఊపిరితిత్తులు": "lungs breathing health",
    "మెదడు": "brain health mental",
    "నిద్ర": "sleep rest bedroom",
    "బరువు": "weight loss fitness",
    "ఆహారం": "healthy food nutrition",
    "వ్యాయామం": "exercise fitness workout",
    "చర్మం": "skin care beauty",
    "జుట్టు": "hair care treatment",
    "కంటి": "eye health vision",
    "దంత": "dental teeth health",
    "పళ్ళు": "dental teeth health",
    "గర్భం": "pregnancy mother health",
    "పిల్లలు": "children kids health",
    "వృద్ధులు": "elderly senior health",
    "మానసిక": "mental health wellness mind",
    "ఒత్తిడి": "stress relief relaxation",
    "ఇమ్యూనిటీ": "immunity health vitamins",
    "రోగనిరోధక": "immunity health vitamins",
    "తులసి": "tulsi basil herb",
    "అల్లం": "ginger herb spice",
    "పసుపు": "turmeric spice yellow",
    "వేప": "neem leaves green",
    "మునగ": "moringa superfood leaves",
    "జీలకర్ర": "cumin spice seeds",
    "నిమ్మ": "lemon citrus health",
    "దానిమ్మ": "pomegranate fruit health",
    "తేనె": "honey natural sweet",
    "కొబ్బరి": "coconut water tropical",
    "అల్లో వెరా": "aloe vera plant gel",
}

# Fallback image URLs (high quality health images from Pexels CDN)
FALLBACK_IMAGES = [
    {
        "url": "https://images.pexels.com/photos/3621168/pexels-photo-3621168.jpeg?w=800",
        "photographer": "Nataliya Vaitkevich",
        "photographer_url": "https://www.pexels.com/@nataliya-vaitkevich",
    },
    {
        "url": "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?w=800",
        "photographer": "Ella Olsson",
        "photographer_url": "https://www.pexels.com/@ella-olsson-572949",
    },
    {
        "url": "https://images.pexels.com/photos/3865557/pexels-photo-3865557.jpeg?w=800",
        "photographer": "Andrea Piacquadio",
        "photographer_url": "https://www.pexels.com/@olly",
    },
    {
        "url": "https://images.pexels.com/photos/4386467/pexels-photo-4386467.jpeg?w=800",
        "photographer": "Karolina Grabowska",
        "photographer_url": "https://www.pexels.com/@karolina-grabowska",
    },
    {
        "url": "https://images.pexels.com/photos/1640773/pexels-photo-1640773.jpeg?w=800",
        "photographer": "Ella Olsson",
        "photographer_url": "https://www.pexels.com/@ella-olsson-572949",
    },
    {
        "url": "https://images.pexels.com/photos/4047186/pexels-photo-4047186.jpeg?w=800",
        "photographer": "Nataliya Vaitkevich",
        "photographer_url": "https://www.pexels.com/@nataliya-vaitkevich",
    },
    {
        "url": "https://images.pexels.com/photos/3775131/pexels-photo-3775131.jpeg?w=800",
        "photographer": "Alexy Almond",
        "photographer_url": "https://www.pexels.com/@alexy-almond",
    },
    {
        "url": "https://images.pexels.com/photos/1552252/pexels-photo-1552252.jpeg?w=800",
        "photographer": "Pixabay",
        "photographer_url": "https://www.pexels.com/@pixabay",
    },
]


def _get_english_keyword(telugu_topic: str) -> str:
    """Map Telugu topic to English keyword for Pexels search."""
    for telugu_key, english_val in KEYWORD_MAPPING.items():
        if telugu_key in telugu_topic:
            return english_val
    return "health wellness lifestyle India"


def fetch_image(topic: str) -> dict:
    """
    Fetch a relevant image from Pexels for the given topic.
    
    Returns:
        dict with keys: url, photographer, photographer_url, html
    """
    if not PEXELS_API_KEY:
        print("⚠️  No Pexels API key, using fallback image")
        return _get_fallback_image()
    
    keyword = _get_english_keyword(topic)
    
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        params = {
            "query": keyword,
            "per_page": 15,
            "orientation": "landscape",
            "size": "medium",
        }
        
        resp = requests.get(
            f"{PEXELS_BASE_URL}/search",
            headers=headers,
            params=params,
            timeout=15
        )
        resp.raise_for_status()
        
        data = resp.json()
        photos = data.get("photos", [])
        
        if not photos:
            print(f"⚠️  No Pexels images found for '{keyword}', using fallback")
            return _get_fallback_image()
        
        # Pick a random photo from results
        photo = random.choice(photos[:10])
        image_url = photo["src"].get("large", photo["src"]["original"])
        # Make it width-limited for faster loading
        image_url = image_url.split("?")[0] + "?w=800&h=450&fit=crop"
        
        photographer = photo.get("photographer", "Pexels Photographer")
        photographer_url = photo.get("photographer_url", "https://www.pexels.com")
        
        print(f"🖼️  Pexels image fetched: {keyword} → Photo by {photographer}")
        
        return {
            "url": image_url,
            "photographer": photographer,
            "photographer_url": photographer_url,
            "html": _build_image_html(image_url, topic, photographer, photographer_url),
        }
    
    except Exception as e:
        print(f"⚠️  Pexels API error: {e}")
        return _get_fallback_image()


def _get_fallback_image() -> dict:
    """Return a random fallback image."""
    img = random.choice(FALLBACK_IMAGES)
    return {
        "url": img["url"],
        "photographer": img["photographer"],
        "photographer_url": img["photographer_url"],
        "html": _build_image_html(
            img["url"], "ఆరోగ్యం",
            img["photographer"], img["photographer_url"]
        ),
    }


def _build_image_html(url: str, alt: str, photographer: str, photographer_url: str) -> str:
    """Build Blogger-compatible image HTML with Pexels attribution."""
    return f"""<div style="text-align: center; margin: 20px 0;">
  <img src="{url}" 
       alt="{alt}" 
       style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);"
       loading="lazy" />
  <p style="font-size: 12px; color: #888; margin-top: 8px;">
    Photo by <a href="{photographer_url}" target="_blank" rel="nofollow">{photographer}</a> 
    on <a href="https://www.pexels.com" target="_blank" rel="nofollow">Pexels</a>
  </p>
</div>"""


if __name__ == "__main__":
    test_topic = "అయుర్వేద మూలికలు"
    img = fetch_image(test_topic)
    print(f"\nImage URL: {img['url']}")
    print(f"By: {img['photographer']}")
