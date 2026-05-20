"""
content_generator.py
====================
Generates Telugu health articles using Google Gemini AI.

Features:
- 1800-2500 word articles in simple, everyday Telugu
- AdSense-friendly HTML structure (clean, no keyword stuffing)
- Styled tables, tip boxes, and info boxes for reader engagement
- Ayurveda content referenced from Atharva Veda and ancient texts
- Human-like writing style (not robotic AI tone)
- Proper subheadings, bullet points, Q&A sections
- Disclaimer and doctor consultation advice
"""

import os
import re
import time
import random

# Fix for protobuf crash on Python 3.14
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize Groq
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Gemini model - Flash 2.5 is fast and free
MODEL_NAME = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.5-flash"


def _get_model():
    """Get configured Gemini model."""
    try:
        return genai.GenerativeModel(MODEL_NAME)
    except Exception:
        return genai.GenerativeModel(FALLBACK_MODEL)


def _build_article_prompt(topic: str, past_urls: list = None) -> str:
    """Build the AdSense-ready, reader-friendly article generation prompt."""

    links_text = ""
    if past_urls:
        links_text = "\nకింది మన పాత ఆర్టికల్స్ లింక్స్ ని వ్యాసంలో ఎక్కడైనా సంబంధం ఉన్నచోట సహజంగా (Natural anchor text) 1 లేదా 2 లింక్స్ గా (HTML <a> tag) వాడండి:\n"
        for url_info in past_urls:
            links_text += f"- {url_info['title']}: {url_info['url']}\n"

    return f"""నువ్వు ఒక అనుభవజ్ఞుడైన తెలుగు ఆరోగ్య రచయిత. నీ పాఠకులు సాధారణ తెలుగు కుటుంబాలు. వారికి అర్థమయ్యే సరళమైన తెలుగులో రాయాలి.

విషయం: {topic}
{links_text}

ముఖ్యమైన నిబంధనలు:
1. భాష: పూర్తిగా తెలుగులో రాయి. ఆంగ్ల పదాలు అవసరమైతే తెలుగు లిప్యంతరీకరణలో రాయి.
2. నిడివి: కనీసం 1800 నుండి 2500 పదాలు ఉండాలి. ప్రతి విభాగాన్ని చాలా వివరంగా, లోతుగా వివరించు.
3. శైలి: 100% సహజంగా, మనిషి రాసినట్లు, సంభాషణ శైలిలో రాయి. నాటకీయమైన AI greetings వాడకు. నేరుగా విషయంలోకి వెళ్ళు.
4. ఆయుర్వేద: అవసరమైన చోట అథర్వ వేద, చరక సంహిత నుండి జ్ఞానం చేర్చు.
5. AdSense నిబంధనలు: కీవర్డ్ స్టఫింగ్ చేయకు, అసలైన విలువైన సమాచారం మాత్రమే రాయి.

మొదటి లైన్‌లో తప్పనిసరిగా URL slug ఇవ్వు:
[SLUG: english-topic-slug-with-hyphens]

HTMLఫార్మాట్ (దీన్ని ఉపయోగించి పూర్తి వ్యాసం రాయి — అన్ని placeholders ని అసలు కంటెంట్‌తో పూరించు):

<article>

<h1>[SEO ముఖ్యపదాలు ఉన్న ఆకర్షణీయమైన శీర్షిక - 60 అక్షరాల లోపు]</h1>

<p style="font-size:1.1em; line-height:1.9; color:#2d2d2d;">[5-6 వాక్యాల బలమైన ముందుమాట. పాఠకుడిని వెంటనే ఆకట్టుకోవాలి. ఈ అంశం ఎందుకు ముఖ్యమో వివరించు.]</p>

{{IMAGE_PLACEHOLDER}}

<h2>[మొదటి విభాగం: మూల అంశం / పరిచయం]</h2>
<p>[కనీసం 250 పదాలతో వివరంగా రాయి. చరిత్ర, శాస్త్రీయ నేపథ్యం, ఎందుకు ముఖ్యమో వివరించు.]</p>
<p>[ఈ అంశంపై పాఠకుడికి పూర్తి అవగాహన కలిగించే అదనపు సమాచారం.]</p>

<h2>[రెండవ విభాగం: ముఖ్య లాభాలు / ఉపయోగాలు]</h2>
<p>[కనీసం 200 పదాలతో లాభాలను వివరించు.]</p>

<!-- పోషక విలువలు లేదా ముఖ్య అంశాల పోలిక పట్టిక -->
<div style="overflow-x:auto; margin:24px 0;">
  <table style="width:100%; border-collapse:collapse; font-family:inherit; font-size:0.97em; border-radius:10px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <thead>
      <tr style="background:linear-gradient(90deg,#1b5e20,#388e3c); color:#fff;">
        <th style="padding:13px 16px; text-align:left; font-weight:600;">[కాలమ్ 1 పేరు]</th>
        <th style="padding:13px 16px; text-align:left; font-weight:600;">[కాలమ్ 2 పేరు]</th>
        <th style="padding:13px 16px; text-align:left; font-weight:600;">[కాలమ్ 3 పేరు]</th>
      </tr>
    </thead>
    <tbody>
      <tr style="background:#f1f8e9;">
        <td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[విలువ 1]</td>
        <td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[విలువ 2]</td>
        <td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[విలువ 3]</td>
      </tr>
      <tr style="background:#fff;">
        <td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[విలువ 4]</td>
        <td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[విలువ 5]</td>
        <td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[విలువ 6]</td>
      </tr>
      <tr style="background:#f1f8e9;">
        <td style="padding:11px 16px;">[విలువ 7]</td>
        <td style="padding:11px 16px;">[విలువ 8]</td>
        <td style="padding:11px 16px;">[విలువ 9]</td>
      </tr>
    </tbody>
  </table>
</div>

<h2>[మూడవ విభాగం: ఎలా ఉపయోగించాలి / మోతాదు]</h2>
<p>[కనీసం 200 పదాలతో వివరంగా రాయి. ఎలా వాడాలో, ఏ మోతాదులో వాడాలో స్పష్టంగా రాయి.]</p>
<ul style="padding-left:22px; line-height:2;">
  <li>[వివరమైన పాయింట్ 1]</li>
  <li>[వివరమైన పాయింట్ 2]</li>
  <li>[వివరమైన పాయింట్ 3]</li>
  <li>[వివరమైన పాయింట్ 4]</li>
</ul>

<!-- చిట్కా బాక్స్ -->
<div style="background:#e8f5e9; border-left:5px solid #43a047; border-radius:8px; padding:18px 22px; margin:24px 0;">
  <p style="margin:0; font-size:1em; line-height:1.8;"><strong>💡 ఆరోగ్య చిట్కా:</strong> [ఒక ముఖ్యమైన, ఆచరణాత్మక చిట్కా రాయి — పాఠకుడు వెంటనే అనుసరించగలిగేది.]</p>
</div>

<h2>[నాలుగవ విభాగం: ఆయుర్వేద దృక్పథం]</h2>
<p>[కనీసం 200 పదాలతో ఆయుర్వేద ఆధారిత వివరాలు రాయి. ప్రాచీన గ్రంథాలను సూచించు.]</p>

<!-- హెచ్చరిక బాక్స్ -->
<div style="background:#fff8e1; border-left:5px solid #f9a825; border-radius:8px; padding:18px 22px; margin:24px 0;">
  <p style="margin:0; font-size:1em; line-height:1.8;"><strong>⚠️ జాగ్రత్త:</strong> [ఎవరు వాడకూడదో, ఏ సందర్భంలో జాగ్రత్త అవసరమో సూటిగా రాయి.]</p>
</div>

<h2>తరచుగా అడిగే ప్రశ్నలు (FAQ)</h2>

<h3>ప్రశ్న 1: [పాఠకులు అడిగే సాధారణ సందేహం]</h3>
<p>[స్పష్టమైన, వివరమైన జవాబు — కనీసం 3-4 వాక్యాలు]</p>

<h3>ప్రశ్న 2: [పాఠకులు అడిగే సాధారణ సందేహం]</h3>
<p>[స్పష్టమైన, వివరమైన జవాబు — కనీసం 3-4 వాక్యాలు]</p>

<h3>ప్రశ్న 3: [పాఠకులు అడిగే సాధారణ సందేహం]</h3>
<p>[స్పష్టమైన, వివరమైన జవాబు — కనీసం 3-4 వాక్యాలు]</p>

<h3>ప్రశ్న 4: [పాఠకులు అడిగే సాధారణ సందేహం]</h3>
<p>[స్పష్టమైన, వివరమైన జవాబు — కనీసం 3-4 వాక్యాలు]</p>

<h2>ముగింపు</h2>
<p>[100-150 పదాలతో బలమైన ముగింపు రాయి. ముఖ్యమైన విషయాలను సంక్షిప్తంగా గుర్తుచేసి, పాఠకుడిని ఉత్సాహపరచు.]</p>

<!-- వైద్య నిరాకరణ -->
<div style="background:#e3f2fd; border-left:5px solid #1976d2; border-radius:8px; padding:18px 22px; margin:28px 0;">
  <p style="margin:0; font-size:0.95em; line-height:1.8; color:#1a237e;"><strong>🏥 వైద్య గమనిక:</strong> ఈ వ్యాసంలో అందించిన సమాచారం కేవలం సాధారణ అవగాహన కోసం మాత్రమే. ఇది వృత్తిపరమైన వైద్య సలహాకు ప్రత్యామ్నాయం కాదు. ఏదైనా ఆరోగ్య సమస్య ఉంటే తప్పకుండా అర్హత కలిగిన వైద్యుడిని సంప్రదించండి.</p>
</div>

</article>

ముఖ్యమైన సూచనలు:
- పై నిర్మాణంలో అన్ని placeholders ని topic కి సంబంధించిన అసలు కంటెంట్‌తో పూరించు.
- పట్టికలో వాస్తవమైన పోషక/వైద్య విలువలు రాయి (ఉదా: పోషకాంశం, మోతాదు, ప్రయోజనం).
- చిట్కా బాక్స్‌లో ఒక ఆచరణాత్మక, వెంటనే అమలు చేయగలిగే సలహా రాయి.
- వ్యాసాన్ని కనీసం 1800 పదాలతో పూర్తి చేయి.

ఇప్పుడు పూర్తి, AdSense-ready వ్యాసాన్ని రాయడం ప్రారంభించు:"""


def _extract_title(html_content: str) -> str:
    """Extract title from H1 tag."""
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html_content, re.IGNORECASE | re.DOTALL)
    if match:
        title = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        return title
    return ""


def _build_tags(topic: str) -> list:
    """Generate relevant Blogger tags/labels."""
    base_tags = ["ఆరోగ్యం", "Telugu Health", "AarogyaGuruji"]
    
    tag_map = {
        "ఆయుర్వేద": ["ఆయుర్వేదం", "Ayurveda", "వేద వైద్యం"],
        "అయుర్వేద": ["ఆయుర్వేదం", "Ayurveda"],
        "డయాబెటిస్": ["మధుమేహం", "Diabetes", "చక్కెర వ్యాధి"],
        "మధుమేహం": ["మధుమేహం", "Diabetes"],
        "గుండె": ["గుండె ఆరోగ్యం", "Heart Health"],
        "రక్తపోటు": ["BP", "Blood Pressure", "రక్తపోటు"],
        "కిడ్నీ": ["మూత్రపిండాలు", "Kidney Health"],
        "లివర్": ["కాలేయం", "Liver Health"],
        "క్యాన్సర్": ["క్యాన్సర్", "Cancer Awareness"],
        "యోగ": ["యోగా", "Yoga", "వ్యాయామం"],
        "మానసిక": ["మానసిక ఆరోగ్యం", "Mental Health"],
        "ఆహారం": ["పోషణ", "Nutrition", "ఆహారం"],
        "చర్మం": ["చర్మ సంరక్షణ", "Skin Care"],
        "జుట్టు": ["జుట్టు సంరక్షణ", "Hair Care"],
        "నిద్ర": ["నిద్ర ఆరోగ్యం", "Sleep Health"],
        "PCOS": ["PCOS", "మహిళల ఆరోగ్యం", "Women Health"],
        "బరువు": ["బరువు తగ్గించడం", "Weight Loss"],
        "ఇమ్యూనిటీ": ["రోగ నిరోధకత", "Immunity"],
        "తులసి": ["ఔషధ మొక్కలు", "Herbs", "ఇంటి చిట్కాలు"],
        "పసుపు": ["ఔషధ మొక్కలు", "Herbs"],
    }
    
    extra_tags = []
    for key, tags in tag_map.items():
        if key in topic:
            extra_tags.extend(tags)
    
    all_tags = list(set(base_tags + extra_tags))
    return all_tags[:15]  # Blogger supports up to 20 labels


def generate_article(topic: str, past_urls: list = None) -> dict:
    """
    Generate a full Telugu health article using Gemini AI.
    
    Returns:
        dict with keys: title, slug, body_html, tags, meta_description, topic
    """
    if not GEMINI_API_KEY and not GROQ_API_KEY:
        raise ValueError("Neither GEMINI_API_KEY nor GROQ_API_KEY environment variables are set!")
    
    print(f"✍️  Generating article: {topic}")
    
    prompt = _build_article_prompt(topic, past_urls)
    model = _get_model()
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.82,
                    top_p=0.92,
                    max_output_tokens=6000,
                )
            )
            
            content = response.text
            
            # Clean up markdown code blocks if present
            content = re.sub(r"```html\s*", "", content)
            content = re.sub(r"```\s*$", "", content)
            content = content.strip()
            
            # Extract Slug
            slug = "health-article"
            slug_match = re.search(r"\[SLUG:\s*([^\]]+)\]", content)
            if slug_match:
                slug = slug_match.group(1).strip().lower().replace(" ", "-")
                # Remove the slug line from content
                content = content.replace(slug_match.group(0), "").strip()
            
            # Extract title
            title = _extract_title(content)
            if not title:
                title = topic  # Fallback to topic as title
            
            # Length validation (Minimum ~2000 chars plain text)
            plain_text = re.sub(r"<[^>]+>", "", content)
            plain_text_clean = re.sub(r"\s+", " ", plain_text).strip()
            
            if len(plain_text_clean) < 2500:
                print(f"⚠️ Generated article is too short ({len(plain_text_clean)} chars). Retrying...")
                raise Exception("Article length validation failed (too short).")
            
            # Generate tags
            tags = _build_tags(topic)
            
            # Build meta description (first 160 chars of plain text)
            plain_text = re.sub(r"<[^>]+>", "", content)
            plain_text = re.sub(r"\s+", " ", plain_text).strip()
            meta_desc = plain_text[:160] + "..." if len(plain_text) > 160 else plain_text
            
            print(f"✅ Article generated: '{title}' ({len(content)} chars)")
            
            return {
                "topic": topic,
                "title": title,
                "slug": slug,
                "body_html": content,
                "tags": tags,
                "meta_description": meta_desc,
            }
        
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                # Always wait for Gemini's rate limits (which are per-minute), 
                # because Groq's limits are per-day and might be exhausted.
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 30
                    print(f"⏳ Gemini rate limit hit, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Gemini exhausted retries due to rate limit.")
            else:
                print(f"❌ Gemini Generation error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
    
    print("🔄 Attempting Groq fallback (llama-3.3-70b-versatile)...")
    if groq_client:
        for groq_attempt in range(3):
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are an expert Telugu health writer. Follow all HTML formatting instructions exactly. Generate long, detailed, AdSense-ready articles with tables, tip boxes, and info boxes as instructed."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.72,
                    max_tokens=5000,
                )
                content = chat_completion.choices[0].message.content
                
                # Clean up markdown code blocks if present
                content = re.sub(r"```html\s*", "", content)
                content = re.sub(r"```\s*$", "", content)
                content = content.strip()
                
                # Extract Slug
                slug = "health-article"
                slug_match = re.search(r"\[SLUG:\s*([^\]]+)\]", content)
                if slug_match:
                    slug = slug_match.group(1).strip().lower().replace(" ", "-")
                    # Remove the slug line from content
                    content = content.replace(slug_match.group(0), "").strip()
                
                # Extract title
                title = _extract_title(content)
                if not title:
                    title = topic  # Fallback to topic as title
            
                # Length validation (Minimum ~3500 chars plain text, Groq relaxed to 2500)
                plain_text = re.sub(r"<[^>]+>", "", content)
                plain_text_clean = re.sub(r"\s+", " ", plain_text).strip()
                
                if len(plain_text_clean) < 2000:
                    print(f"⚠️ Groq generated article is too short ({len(plain_text_clean)} chars). Retrying... ({groq_attempt+1}/3)")
                    if groq_attempt == 2:
                        raise Exception("Groq article length validation failed after 3 attempts.")
                    time.sleep(2)
                    continue
                
                # Generate tags
                tags = _build_tags(topic)
                
                # Build meta description
                meta_desc = plain_text_clean[:160] + "..." if len(plain_text_clean) > 160 else plain_text_clean
                
                print(f"✅ Article generated via Groq: '{title}' ({len(content)} chars)")
                
                return {
                    "topic": topic,
                    "title": title,
                    "slug": slug,
                    "body_html": content,
                    "tags": tags,
                    "meta_description": meta_desc,
                }
            except Exception as groq_e:
                print(f"❌ Groq fallback failed on attempt {groq_attempt+1}: {groq_e}")
                if groq_attempt == 2:
                    break
                time.sleep(2)
    else:
        print("❌ Groq fallback skipped: GROQ_API_KEY not configured.")

    raise Exception(f"Failed to generate article for '{topic}' using both Gemini and Groq.")


def inject_image(body_html: str, image_html: str) -> str:
    """Inject image HTML after the first paragraph or intro section."""
    # Try to inject after {{IMAGE_PLACEHOLDER}} marker
    if "{{IMAGE_PLACEHOLDER}}" in body_html:
        return body_html.replace("{{IMAGE_PLACEHOLDER}}", image_html)
    
    # Try to inject after first </p> tag
    first_p_end = body_html.find("</p>")
    if first_p_end != -1:
        insert_pos = first_p_end + 4
        return body_html[:insert_pos] + "\n" + image_html + "\n" + body_html[insert_pos:]
    
    # Fallback: prepend image
    return image_html + "\n" + body_html


if __name__ == "__main__":
    test_topic = "డయాబెటిస్ నివారణ - ఇంట్లోనే చికిత్స"
    article = generate_article(test_topic)
    print(f"\nTitle: {article['title']}")
    print(f"Tags: {article['tags']}")
    print(f"Body length: {len(article['body_html'])} chars")
