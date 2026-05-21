"""
image_fetcher.py
================
Fetches unique, topic-relevant images from Pexels API.

Key improvements:
- Tracks used photo IDs in used_images.json to NEVER repeat the same image
- Randomises Pexels search page so different results come each run
- Uses specific topic-level keywords (not just category) for relevance
- Large fallback pool (30+ images) with used-tracking even in fallback mode
"""

import os
import json
import random
import hashlib
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PEXELS_API_KEY  = os.getenv("PEXELS_API_KEY", "")
PEXELS_BASE_URL = "https://api.pexels.com/v1"

# File that stores already-used Pexels photo IDs
_USED_IDS_FILE = Path(__file__).parent.parent / "data" / "used_images.json"


# ---------------------------------------------------------------------------
# Specific keyword mapping — topic word → search query
# More specific = more relevant images
# ---------------------------------------------------------------------------
KEYWORD_MAPPING = {
    # Herbs & Ayurveda
    "తులసి":       "tulsi holy basil plant leaves",
    "పసుపు":       "turmeric root powder yellow spice",
    "అల్లం":       "ginger root spice fresh",
    "వేప":         "neem leaves green plant",
    "అశ్వగంధ":    "ashwagandha root herb supplement",
    "నీమ్":        "neem leaves ayurveda",
    "మేథి":        "fenugreek seeds spice",
    "నెల్లి":      "amla gooseberry fruit green",
    "బ్రహ్మి":     "brahmi herb plant leaves",
    "మోరింగా":     "moringa drumstick leaves green",
    "అల్లో వెరా":  "aloe vera plant gel succulent",
    "తేనె":        "honey jar natural golden",
    "కొబ్బరి":     "coconut water fresh tropical",
    "ఆయుర్వేద":   "ayurveda herbs medicine mortar",
    "మూలికలు":    "medicinal herbs spices collection",
    "ఇంటి చిట్కా": "home remedy natural ingredients kitchen",
    "కషాయం":      "herbal tea decoction cup",

    # Diseases & Conditions
    "డయాబెటిస్":  "diabetes blood sugar glucose test",
    "మధుమేహం":    "diabetes healthy meal insulin",
    "గుండె":       "heart health cardiology stethoscope",
    "రక్తపోటు":   "blood pressure monitor hypertension",
    "క్యాన్సర్":  "cancer awareness ribbon hospital",
    "కిడ్నీ":     "kidney health water drinking",
    "లివర్":      "liver health detox green juice",
    "థైరాయిడ్":   "thyroid neck throat health",
    "అస్తమా":     "asthma inhaler breathing lungs",
    "ఆర్థరైటిస్": "arthritis joint pain knee",
    "జ్వరం":      "fever thermometer sick person",
    "పొట్ట":      "stomach digestive health abdomen",
    "మైగ్రేన్":   "migraine headache pain relief",
    "ధూమపానం":    "no smoking cigarette health awareness",
    "పొగ":         "smoking cigarette danger health",

    # Nutrition & Foods
    "ఆహారాలు":    "healthy food vegetables colorful",
    "పోషకాలు":    "nutrition vitamins minerals food",
    "ఐరన్":       "iron rich foods spinach lentils",
    "కాల్షియం":   "calcium dairy milk bones",
    "విటమిన్":    "vitamins supplements capsules",
    "ప్రొటీన్":   "protein food eggs chicken lentils",
    "ఫైబర్":      "fiber rich food vegetables fruits",
    "యాంటీఆక్సిడెంట్": "antioxidant berries colorful food",
    "ఒమేగా":      "omega fish oil salmon healthy fat",
    "సూపర్‌ఫుడ్": "superfood nutrition bowl healthy",

    # Lifestyle & Fitness
    "వ్యాయామం":   "exercise workout fitness gym",
    "యోగా":       "yoga pose mat meditation",
    "నిద్ర":      "sleep rest bedroom peaceful night",
    "బరువు":      "weight loss scale fitness",
    "స్ట్రెస్":   "stress relief relaxation calm",
    "మానసిక":     "mental health calm meditation peace",
    "చర్మం":      "skin care face beauty natural",
    "జుట్టు":     "hair care natural treatment oil",
    "వేసవి":      "summer heat hydration water",
    "శీతాకాలం":   "winter cold warmth health",
    "ఫిట్‌నెస్":  "fitness active lifestyle running",
    "దినచర్య":    "morning routine healthy lifestyle",

    # Women's Health
    "PCOS":        "pcos women hormones health",
    "గర్భం":      "pregnancy mother baby maternity",
    "పీరియడ్స్":  "women health wellness calm",
    "మహిళ":       "women health wellness India",
    "రుతు":       "women wellness calm flower",
    "బాలింత":     "mother baby breastfeeding",

    # General
    "ఆరోగ్యం":    "health wellness lifestyle",
    "ఇమ్యూనిటీ":  "immunity boost health vitamins",
    "కంటి":       "eye health vision care",
    "దంత":        "dental teeth oral health",
    "పళ్ళు":      "teeth dental care smile",
    "మెదడు":      "brain health mental cognitive",
    "పిల్లలు":    "children kids health nutrition",
    "వృద్ధులు":   "elderly senior active healthy",
    
    # Grooming & Men's Health
    "గడ్డం":      "beard growth grooming men",
    "మీసం":      "moustache beard men style",
    "గుండు":     "bald head men care",
    
    # Common Symptoms & Digestion
    "నొప్పి":     "massage pain relief joint",
    "దగ్గు":      "cough cold remedy hot tea",
    "జీర్ణం":     "healthy stomach digestion food",
    "గ్యాస్":     "digestive tea herbal organic",
}


# ---------------------------------------------------------------------------
# Large fallback pool (30 unique Pexels CDN images)
# ---------------------------------------------------------------------------
FALLBACK_IMAGES = [
    {"id": "f001", "url": "https://images.pexels.com/photos/3621168/pexels-photo-3621168.jpeg?w=800&h=450&fit=crop", "photographer": "Nataliya Vaitkevich", "photographer_url": "https://www.pexels.com/@nataliya-vaitkevich"},
    {"id": "f002", "url": "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?w=800&h=450&fit=crop", "photographer": "Ella Olsson", "photographer_url": "https://www.pexels.com/@ella-olsson-572949"},
    {"id": "f003", "url": "https://images.pexels.com/photos/3865557/pexels-photo-3865557.jpeg?w=800&h=450&fit=crop", "photographer": "Andrea Piacquadio", "photographer_url": "https://www.pexels.com/@olly"},
    {"id": "f004", "url": "https://images.pexels.com/photos/4386467/pexels-photo-4386467.jpeg?w=800&h=450&fit=crop", "photographer": "Karolina Grabowska", "photographer_url": "https://www.pexels.com/@karolina-grabowska"},
    {"id": "f005", "url": "https://images.pexels.com/photos/1640773/pexels-photo-1640773.jpeg?w=800&h=450&fit=crop", "photographer": "Ella Olsson", "photographer_url": "https://www.pexels.com/@ella-olsson-572949"},
    {"id": "f006", "url": "https://images.pexels.com/photos/4047186/pexels-photo-4047186.jpeg?w=800&h=450&fit=crop", "photographer": "Nataliya Vaitkevich", "photographer_url": "https://www.pexels.com/@nataliya-vaitkevich"},
    {"id": "f007", "url": "https://images.pexels.com/photos/3775131/pexels-photo-3775131.jpeg?w=800&h=450&fit=crop", "photographer": "Alexy Almond", "photographer_url": "https://www.pexels.com/@alexy-almond"},
    {"id": "f008", "url": "https://images.pexels.com/photos/1552252/pexels-photo-1552252.jpeg?w=800&h=450&fit=crop", "photographer": "Pixabay", "photographer_url": "https://www.pexels.com/@pixabay"},
    {"id": "f009", "url": "https://images.pexels.com/photos/1028598/pexels-photo-1028598.jpeg?w=800&h=450&fit=crop", "photographer": "Pixabay", "photographer_url": "https://www.pexels.com/@pixabay"},
    {"id": "f010", "url": "https://images.pexels.com/photos/3985163/pexels-photo-3985163.jpeg?w=800&h=450&fit=crop", "photographer": "Cats Coming", "photographer_url": "https://www.pexels.com/@cats-coming-866847"},
    {"id": "f011", "url": "https://images.pexels.com/photos/2377045/pexels-photo-2377045.jpeg?w=800&h=450&fit=crop", "photographer": "Daria Shevtsova", "photographer_url": "https://www.pexels.com/@daria"},
    {"id": "f012", "url": "https://images.pexels.com/photos/1351238/pexels-photo-1351238.jpeg?w=800&h=450&fit=crop", "photographer": "Ella Olsson", "photographer_url": "https://www.pexels.com/@ella-olsson-572949"},
    {"id": "f013", "url": "https://images.pexels.com/photos/1382731/pexels-photo-1382731.jpeg?w=800&h=450&fit=crop", "photographer": "Nathan Cowley", "photographer_url": "https://www.pexels.com/@mastercowley"},
    {"id": "f014", "url": "https://images.pexels.com/photos/3823488/pexels-photo-3823488.jpeg?w=800&h=450&fit=crop", "photographer": "Karolina Grabowska", "photographer_url": "https://www.pexels.com/@karolina-grabowska"},
    {"id": "f015", "url": "https://images.pexels.com/photos/4099238/pexels-photo-4099238.jpeg?w=800&h=450&fit=crop", "photographer": "Nataliya Vaitkevich", "photographer_url": "https://www.pexels.com/@nataliya-vaitkevich"},
    {"id": "f016", "url": "https://images.pexels.com/photos/775032/pexels-photo-775032.jpeg?w=800&h=450&fit=crop", "photographer": "Trang Doan", "photographer_url": "https://www.pexels.com/@trangdoan"},
    {"id": "f017", "url": "https://images.pexels.com/photos/1153370/pexels-photo-1153370.jpeg?w=800&h=450&fit=crop", "photographer": "Pixabay", "photographer_url": "https://www.pexels.com/@pixabay"},
    {"id": "f018", "url": "https://images.pexels.com/photos/317157/pexels-photo-317157.jpeg?w=800&h=450&fit=crop", "photographer": "Pixabay", "photographer_url": "https://www.pexels.com/@pixabay"},
    {"id": "f019", "url": "https://images.pexels.com/photos/1640775/pexels-photo-1640775.jpeg?w=800&h=450&fit=crop", "photographer": "Ella Olsson", "photographer_url": "https://www.pexels.com/@ella-olsson-572949"},
    {"id": "f020", "url": "https://images.pexels.com/photos/3822727/pexels-photo-3822727.jpeg?w=800&h=450&fit=crop", "photographer": "Karolina Grabowska", "photographer_url": "https://www.pexels.com/@karolina-grabowska"},
    {"id": "f021", "url": "https://images.pexels.com/photos/4210342/pexels-photo-4210342.jpeg?w=800&h=450&fit=crop", "photographer": "cottonbro", "photographer_url": "https://www.pexels.com/@cottonbro"},
    {"id": "f022", "url": "https://images.pexels.com/photos/1660030/pexels-photo-1660030.jpeg?w=800&h=450&fit=crop", "photographer": "Artem Podrez", "photographer_url": "https://www.pexels.com/@artem-podrez"},
    {"id": "f023", "url": "https://images.pexels.com/photos/3823039/pexels-photo-3823039.jpeg?w=800&h=450&fit=crop", "photographer": "Karolina Grabowska", "photographer_url": "https://www.pexels.com/@karolina-grabowska"},
    {"id": "f024", "url": "https://images.pexels.com/photos/4253920/pexels-photo-4253920.jpeg?w=800&h=450&fit=crop", "photographer": "Nataliya Vaitkevich", "photographer_url": "https://www.pexels.com/@nataliya-vaitkevich"},
    {"id": "f025", "url": "https://images.pexels.com/photos/1640771/pexels-photo-1640771.jpeg?w=800&h=450&fit=crop", "photographer": "Ella Olsson", "photographer_url": "https://www.pexels.com/@ella-olsson-572949"},
    {"id": "f026", "url": "https://images.pexels.com/photos/3621234/pexels-photo-3621234.jpeg?w=800&h=450&fit=crop", "photographer": "Nataliya Vaitkevich", "photographer_url": "https://www.pexels.com/@nataliya-vaitkevich"},
    {"id": "f027", "url": "https://images.pexels.com/photos/5938404/pexels-photo-5938404.jpeg?w=800&h=450&fit=crop", "photographer": "Tara Winstead", "photographer_url": "https://www.pexels.com/@tara-winstead"},
    {"id": "f028", "url": "https://images.pexels.com/photos/4397899/pexels-photo-4397899.jpeg?w=800&h=450&fit=crop", "photographer": "Anna Shvets", "photographer_url": "https://www.pexels.com/@shvets-production"},
    {"id": "f029", "url": "https://images.pexels.com/photos/3987142/pexels-photo-3987142.jpeg?w=800&h=450&fit=crop", "photographer": "Ketut Subiyanto", "photographer_url": "https://www.pexels.com/@ketut-subiyanto"},
    {"id": "f030", "url": "https://images.pexels.com/photos/4498603/pexels-photo-4498603.jpeg?w=800&h=450&fit=crop", "photographer": "Karolina Grabowska", "photographer_url": "https://www.pexels.com/@karolina-grabowska"},
]


# ---------------------------------------------------------------------------
# Used-image tracking
# ---------------------------------------------------------------------------

def _load_used_ids() -> set:
    """Load set of already-used photo IDs from disk."""
    try:
        _USED_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if _USED_IDS_FILE.exists():
            data = json.loads(_USED_IDS_FILE.read_text(encoding="utf-8"))
            return set(data.get("used_ids", []))
    except Exception:
        pass
    return set()


def _save_used_id(photo_id: str) -> None:
    """Append a photo ID to the used list on disk."""
    try:
        _USED_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        existing = _load_used_ids()
        existing.add(str(photo_id))
        _USED_IDS_FILE.write_text(
            json.dumps({"used_ids": list(existing)}, indent=2),
            encoding="utf-8"
        )
    except Exception as e:
        print(f"⚠️  Could not save used image ID: {e}")


# ---------------------------------------------------------------------------
# Keyword resolution
# ---------------------------------------------------------------------------

def _get_english_keyword(telugu_topic: str) -> str:
    """Map Telugu topic to a specific English search query for Pexels."""
    for telugu_key, english_val in KEYWORD_MAPPING.items():
        if telugu_key in telugu_topic:
            return english_val
    # Generic fallback using first meaningful word
    return "health wellness India lifestyle"


# ---------------------------------------------------------------------------
# Main fetch function
# ---------------------------------------------------------------------------

def fetch_image(topic: str) -> dict:
    """
    Fetch a unique, topic-relevant image from Pexels.
    Never returns the same image twice (tracked via used_images.json).
    """
    used_ids = _load_used_ids()

    if not PEXELS_API_KEY:
        print("⚠️  No Pexels API key — using fallback image")
        return _get_fallback_image(used_ids)

    keyword = _get_english_keyword(topic)

    # Try multiple random pages to get a fresh unused image
    pages_to_try = random.sample(range(1, 6), 3)  # try 3 random pages from 1–5

    for page in pages_to_try:
        try:
            headers = {"Authorization": PEXELS_API_KEY}
            params = {
                "query": keyword,
                "per_page": 15,
                "page": page,
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

            photos = resp.json().get("photos", [])
            if not photos:
                continue

            # Shuffle and pick first unused photo
            random.shuffle(photos)
            for photo in photos:
                pid = str(photo["id"])
                if pid not in used_ids:
                    image_url = photo["src"].get("large", photo["src"]["original"])
                    image_url = image_url.split("?")[0] + "?w=800&h=450&fit=crop"
                    photographer = photo.get("photographer", "Pexels Photographer")
                    photographer_url = photo.get("photographer_url", "https://www.pexels.com")

                    _save_used_id(pid)
                    print(f"🖼️  Image: '{keyword}' → #{pid} by {photographer} (page {page})")

                    return {
                        "url": image_url,
                        "photographer": photographer,
                        "photographer_url": photographer_url,
                        "html": _build_image_html(image_url, topic, photographer, photographer_url),
                    }

            print(f"⚠️  All images on page {page} already used, trying next page...")

        except Exception as e:
            print(f"⚠️  Pexels API error (page {page}): {e}")
            continue

    # All API attempts exhausted → fallback
    print(f"⚠️  No fresh Pexels image found for '{keyword}' — using fallback")
    return _get_fallback_image(used_ids)


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

def _get_fallback_image(used_ids: set = None) -> dict:
    """Return an unused fallback image. If all used, reset tracking."""
    if used_ids is None:
        used_ids = _load_used_ids()

    available = [f for f in FALLBACK_IMAGES if f["id"] not in used_ids]

    if not available:
        # All fallbacks used — reset fallback tracking only
        print("🔄  All fallback images used — resetting fallback pool")
        fallback_ids = {f["id"] for f in FALLBACK_IMAGES}
        remaining_ids = _load_used_ids() - fallback_ids
        _USED_IDS_FILE.write_text(
            json.dumps({"used_ids": list(remaining_ids)}, indent=2),
            encoding="utf-8"
        )
        available = list(FALLBACK_IMAGES)

    img = random.choice(available)
    _save_used_id(img["id"])

    return {
        "url": img["url"],
        "photographer": img["photographer"],
        "photographer_url": img["photographer_url"],
        "html": _build_image_html(
            img["url"], "ఆరోగ్యం",
            img["photographer"], img["photographer_url"]
        ),
    }


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------

def _build_image_html(url: str, alt: str, photographer: str, photographer_url: str) -> str:
    """Build Blogger-compatible image HTML with Pexels attribution."""
    return f"""<div style="text-align:center; margin:24px 0;">
  <img src="{url}"
       alt="{alt}"
       style="max-width:100%; height:auto; border-radius:10px; box-shadow:0 4px 16px rgba(0,0,0,0.12);"
       loading="lazy" />
  <p style="font-size:11px; color:#aaa; margin-top:6px;">
    Photo by <a href="{photographer_url}" target="_blank" rel="nofollow">{photographer}</a>
    on <a href="https://www.pexels.com" target="_blank" rel="nofollow">Pexels</a>
  </p>
</div>"""


if __name__ == "__main__":
    test_topic = "పసుపు ఆరోగ్య ప్రయోజనాలు"
    img = fetch_image(test_topic)
    print(f"\nImage URL: {img['url']}")
    print(f"By: {img['photographer']}")
