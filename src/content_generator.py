"""
content_generator.py
====================
Generates Telugu health articles using Google Gemini AI.

Features:
- 1200-1800 word articles in simple, everyday Telugu
- SEO-optimized HTML structure for Blogger
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
    """Build the article generation prompt."""
    
    links_text = ""
    if past_urls:
        links_text = "\nకింది మన పాత ఆర్టికల్స్ లింక్స్ ని వ్యాసంలో ఎక్కడైనా సంబంధం ఉన్నచోట సహజంగా (Natural anchor text) 1 లేదా 2 లింక్స్ గా (HTML <a> tag) వాడండి:\n"
        for url_info in past_urls:
            links_text += f"- {url_info['title']}: {url_info['url']}\n"

    return f"""నువ్వు ఒక అనుభవజ్ఞుడైన తెలుగు ఆరోగ్య రచయిత. నీ పాఠకులు సాధారణ తెలుగు కుటుంబాలు. వారికి అర్థమయ్యే సరళమైన తెలుగులో రాయాలి.

విషయం: {topic}
{links_text}

కింది నిబంధనలు ఖచ్చితంగా పాటించు:

1. భాష: పూర్తిగా తెలుగులో రాయి. ఆంగ్ల పదాలు అవసరమైతే తెలుగు లిప్యంతరీకరణతో రాయి.
2. పదాలు: సులభమైన, వాడుక తెలుగు పదాలు వాడు. మరీ పెద్ద గ్రాంధిక పదాలు వాడకు.
3. నిడివి: కనీసం 1200 నుండి 1800 పదాలు (Words) ఉండాలి. చాలా వివరంగా, లోతుగా వివరించు. షార్ట్ కట్ లో రాయద్దు. ప్రతి పాయింట్ కి ఉదాహరణలు, లాభాలు, ఎలా ఉపయోగించాలో వివరంగా రాయి.
4. శైలి: సహజంగా, మనిషి రాసినట్లుగా (100% Human-written style) సింపుల్ సంభాషణ శైలిలో (Conversational) రాయి. "అమ్మలారా, అక్కలారా, బామ్మలారా", "రండి తెలుసుకుందాం", "స్వాగతం" లాంటి నాటకీయమైన, అతిశయోక్తి పదాలు (Dramatic AI greetings) అస్సలు వాడొద్దు. సూటిగా, ఆసక్తికరంగా నేరుగా విషయంలోకి వెళ్ళు. ప్రతి ఆర్టికల్ ఒకేలా మొదలవ్వకూడదు.
5. ఆయుర్వేద: వర్తించే చోట అథర్వ వేద, చరక సంహిత, సుశ్రుత సంహిత నుండి జ్ఞానాన్ని సూచించు.

ముఖ్యమైన సూచన: నీ జవాబు యొక్క మొదటి లైన్ లో తప్పనిసరిగా ఈ ఆర్టికల్ కి సరిపోయే ఒక ఆంగ్ల URL slug ని ఈ ఫార్మాట్ లో ఇవ్వు:
[SLUG: english-topic-slug-with-hyphens]

HTML ఫార్మాట్ కోసం మార్గదర్శకత్వం (ఈ నిర్మాణాన్ని ఉపయోగించి పూర్తి వ్యాసాన్ని విస్తరించు):

<article>
<h1>[ఇక్కడ ఆకర్షణీయమైన శీర్షిక రాయి - SEO ముఖ్యపదాలు ఉండాలి]</h1>

<p class="intro">[ఇక్కడ సుమారు 5-6 వాక్యాల ముందుమాట రాయి. పాఠకుడిని ఆకట్టుకోవాలి]</p>

[ముఖ్య చిత్రం ఇక్కడ వస్తుంది - {{IMAGE_PLACEHOLDER}}]

<h2>[ఇక్కడ మొదటి విభాగం శీర్షిక రాయి]</h2>
<p>[ఇక్కడ ఆ అంశం గురించి కనీసం 200 పదాలతో పూర్తి వివరాలు రాయి. ఏది వదిలిపెట్టవద్దు.]</p>
<p>[ఇంకా అదనపు సమాచారం, లాభాలు, లేదా చరిత్ర రాయి]</p>

<h2>[ఇక్కడ రెండవ విభాగం శీర్షిక రాయి - ఉదాహరణకు ఉపయోగాలు]</h2>
<p>[ఇక్కడ కూడా కనీసం 200 పదాలతో వివరంగా రాయి]</p>
<ul style="list-style-type: disc; padding-left: 20px;">
<li>[వివరణాత్మక పాయింట్ 1]</li>
<li>[వివరణాత్మక పాయింట్ 2]</li>
<li>[వివరణాత్మక పాయింట్ 3]</li>
<li>[వివరణాత్మక పాయింట్ 4]</li>
<li>[వివరణాత్మక పాయింట్ 5]</li>
</ul>

<h2>[ఇక్కడ మూడవ విభాగం - ఆయుర్వేద/ఇంటి చిట్కాలు గురించి రాయి]</h2>
<p>[దీనిని కూడా చాలా వివరంగా కనీసం 200 పదాలతో రాయి. ఎలా తయారు చేయాలి, ఎంత మోతాదులో వాడాలో స్పష్టంగా రాయి]</p>

<h2>తరచుగా అడిగే ప్రశ్నలు (FAQ)</h2>
<h3>ప్రశ్న 1: [సాధారణ సందేహం]</h3>
<p>[వివరమైన జవాబు]</p>
<h3>ప్రశ్న 2: [సాధారణ సందేహం]</h3>
<p>[వివరమైన జవాబు]</p>
<h3>ప్రశ్న 3: [సాధారణ సందేహం]</h3>
<p>[వివరమైన జవాబు]</p>

<h2>ముఖ్యమైన జాగ్రత్తలు / ముగింపు</h2>
<p>[ఎవరు వాడకూడదు, ఏ పరిస్థితుల్లో వైద్యుడిని సంప్రదించాలి అనేవి వివరంగా రాయి]</p>

<div style="background: #f0f8ff; border-left: 4px solid #2196F3; padding: 15px; margin: 20px 0; border-radius: 4px;">
<strong>🏥 గమనిక:</strong> ఈ వ్యాసంలో ఇచ్చిన సమాచారం సాధారణ అవగాహన కోసం మాత్రమే. ఆరోగ్య సమస్యలకు తప్పకుండా వైద్యుడిని సంప్రదించండి.
</div>

</article>

అదనపు సూచనలు:
- దయచేసి వ్యాసాన్ని చాలా పెద్దగా, కనీసం 1200 పదాలతో రాయండి. 
- ఉత్తుత్తి టెంప్లేట్ లా కాకుండా, పైన ఇచ్చిన నిర్మాణాన్ని ఉపయోగించి అసలు సమాచారంతో పూర్తి వ్యాసాన్ని పూరించండి.
- హెడ్డింగ్స్ కు తగినట్లుగా చాలా కంటెంట్ రాయండి.

ఇప్పుడు పూర్తి, సుదీర్ఘమైన వ్యాసాన్ని రాయడం ప్రారంభించు:"""


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
                    temperature=0.85,
                    top_p=0.9,
                    max_output_tokens=3000,
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
            
            if len(plain_text_clean) < 2000:
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
                        {"role": "system", "content": "You are an expert Telugu health writer. You always strictly follow formatting instructions."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.7,
                    max_tokens=3000,
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
                
                if len(plain_text_clean) < 1500:
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
