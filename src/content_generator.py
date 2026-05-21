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


# ---------------------------------------------------------------------------
# Shared HTML snippets reused across all templates
# ---------------------------------------------------------------------------

_FAQ_BLOCK = """<h2>తరచుగా అడిగే ప్రశ్నలు</h2>
<div style="margin:20px 0;">
  <div style="border-bottom:1px solid #e8e8e8; padding:16px 0;">
    <p style="margin:0 0 8px; font-weight:600; color:#1b5e20;">&#9658; [పాఠకులు అడిగే సాధారణ సందేహం 1]</p>
    <p style="margin:0; color:#444; line-height:1.8;">[స్పష్టమైన జవాబు — కనీసం 3-4 వాక్యాలు]</p>
  </div>
  <div style="border-bottom:1px solid #e8e8e8; padding:16px 0;">
    <p style="margin:0 0 8px; font-weight:600; color:#1b5e20;">&#9658; [పాఠకులు అడిగే సాధారణ సందేహం 2]</p>
    <p style="margin:0; color:#444; line-height:1.8;">[స్పష్టమైన జవాబు — కనీసం 3-4 వాక్యాలు]</p>
  </div>
  <div style="border-bottom:1px solid #e8e8e8; padding:16px 0;">
    <p style="margin:0 0 8px; font-weight:600; color:#1b5e20;">&#9658; [పాఠకులు అడిగే సాధారణ సందేహం 3]</p>
    <p style="margin:0; color:#444; line-height:1.8;">[స్పష్టమైన జవాబు — కనీసం 3-4 వాక్యాలు]</p>
  </div>
  <div style="padding:16px 0;">
    <p style="margin:0 0 8px; font-weight:600; color:#1b5e20;">&#9658; [పాఠకులు అడిగే సాధారణ సందేహం 4]</p>
    <p style="margin:0; color:#444; line-height:1.8;">[స్పష్టమైన జవాబు — కనీసం 3-4 వాక్యాలు]</p>
  </div>
</div>"""

_DISCLAIMER_BLOCK = """<div style="background:#e3f2fd; border-left:5px solid #1976d2; border-radius:8px; padding:18px 22px; margin:28px 0;">
  <p style="margin:0; font-size:0.95em; line-height:1.8; color:#1a237e;"><strong>🏥 వైద్య గమనిక:</strong> ఈ వ్యాసంలో అందించిన సమాచారం కేవలం సాధారణ అవగాహన కోసం మాత్రమే. ఇది వృత్తిపరమైన వైద్య సలహాకు ప్రత్యామ్నాయం కాదు. ఏదైనా ఆరోగ్య సమస్య ఉంటే తప్పకుండా అర్హత కలిగిన వైద్యుడిని సంప్రదించండి.</p>
</div>"""

_TIP_BOX = """<div style="background:#e8f5e9; border-left:5px solid #43a047; border-radius:8px; padding:18px 22px; margin:24px 0;">
  <p style="margin:0; font-size:1em; line-height:1.8;"><strong>💡 ముఖ్యమైన చిట్కా:</strong> [పాఠకుడు వెంటనే అనుసరించగలిగే ఒక ఆచరణాత్మక చిట్కా రాయి]</p>
</div>"""

_WARNING_BOX = """<div style="background:#fff8e1; border-left:5px solid #f9a825; border-radius:8px; padding:18px 22px; margin:24px 0;">
  <p style="margin:0; font-size:1em; line-height:1.8;"><strong>⚠️ జాగ్రత్త:</strong> [ఎవరు జాగ్రత్తగా ఉండాలో, ఏ సందర్భంలో వైద్యుడిని వెంటనే కలవాలో సూటిగా రాయి]</p>
</div>"""

_COMMON_RULES = """ముఖ్యమైన నిబంధనలు:
1. భాష: పూర్తిగా తెలుగులో రాయి. ఆంగ్ల పదాలు తప్పనిసరైతే మాత్రమే వాడు — తెలుగు లిప్యంతరీకరణలో (example: " డాక్టర్", "హాస్పిటల్").
2. నిడివి: కనీసం 1800 పదాలు. ప్రతి విభాగాన్ని వివరంగా రాయి.
3. శైలి — చాలా ముఖ్యం:
   - పక్కింటి అన్నయ్య లేదా అక్కయ్య మాట్లాడినట్లు సహజంగా రాయి
   - "నమస్తే", "ఈ వ్యాసంలో", "మీరు తెలుసుకుంటారు" వంటి AI phrases వాడకు
   - వాక్యాలు చిన్నగా, అర్థమయ్యేలా ఉండాలి
   - పండిత భాష వద్దు — వంటింట్లో మాట్లాడినట్లు రాయి
   - నేరుగా విషయంలోకి వెళ్ళు, intro లో time waste వద్దు
4. AdSense: keyword stuffing చేయకు. అసలైన, నిజమైన సమాచారం రాయి.
5. అన్ని placeholders ని నిజమైన content తో పూరించు — ఏ placeholder అయినా article లో కనపడకూడదు.
6. SLUG మాత్రమే మొదటి లైన్‌లో ఇవ్వు — వేరే చోట slug పేర్కొనకు, article లో show అవకూడదు."""


# ---------------------------------------------------------------------------
# Topic-type detection
# ---------------------------------------------------------------------------

def _detect_topic_type(topic: str) -> str:
    """Detect which article template best fits the topic."""
    t = topic.lower()

    herb_keywords = [
        "తులసి", "పసుపు", "అశ్వగంధ", "నీమ్", "వేప", "అల్లం", "మేథి", "చింత",
        "ఆయుర్వేద", "మూలికలు", "ఔషధ", "ఇంటి చిట్కా", "చిట్కాలు", "కషాయం",
        "నెల్లి", "బ్రహ్మి", "శతావరి", "త్రిఫల", "గిలోయ్", "మోరింగా",
        "tulsi", "turmeric", "neem", "ginger", "herb"
    ]
    nutrition_keywords = [
        "ఆహారాలు", "ఆహారం", "విటమిన్", "ఐరన్", "కాల్షియం", "ప్రొటీన్",
        "పోషకాలు", "పోషణ", "సూపర్‌ఫుడ్", "ఫుడ్స్", "డైట్", "తినాలి",
        "nutrition", "food", "diet", "vitamin", "mineral", "protein"
    ]
    women_keywords = [
        "pcos", "గర్భం", "పీరియడ్స్", "రుతు", "మహిళ", "ఋతుక్రమం",
        "రొమ్ము", "ప్రెగ్నెన్సీ", "గర్భిణి", "బాలింత", "రజస్వల",
        "women", "pregnancy", "period", "menstrual"
    ]
    disease_keywords = [
        "డయాబెటిస్", "మధుమేహం", "గుండె", "రక్తపోటు", "bp", "క్యాన్సర్",
        "కిడ్నీ", "మూత్రపిండాలు", "లివర్", "కాలేయం", "థైరాయిడ్", "అస్తమా",
        "ఆర్థరైటిస్", "వ్యాధి", "సమస్య", "జ్వరం", "కరోనా", "సంక్రమణ",
        "diabetes", "cancer", "disease", "disorder", "fever", "infection"
    ]
    lifestyle_keywords = [
        "వ్యాయామం", "యోగా", "నిద్ర", "బరువు", "స్ట్రెస్", "మానసిక",
        "చర్మం", "జుట్టు", "వేసవి", "శీతాకాలం", "వర్షాకాలం", "సంరక్షణ",
        "అలవాట్లు", "దినచర్య", "ఫిట్‌నెస్",
        "yoga", "sleep", "weight", "stress", "skin", "hair", "fitness"
    ]

    for kw in herb_keywords:
        if kw in t:
            return "herb"
    for kw in women_keywords:
        if kw in t:
            return "women"
    for kw in nutrition_keywords:
        if kw in t:
            return "nutrition"
    for kw in disease_keywords:
        if kw in t:
            return "disease"
    for kw in lifestyle_keywords:
        if kw in t:
            return "lifestyle"
    return "disease"   # sensible default


# ---------------------------------------------------------------------------
# Template 1 — Disease / Condition  🏥
# ---------------------------------------------------------------------------

def _prompt_disease(topic: str, links_text: str) -> str:
    return f"""నువ్వు ఒక అనుభవజ్ఞుడైన తెలుగు ఆరోగ్య రచయిత. సాధారణ తెలుగు కుటుంబాలకు అర్థమయ్యే సరళమైన భాషలో రాయాలి.

విషయం: {topic}
{links_text}
{_COMMON_RULES}

మొదటి లైన్‌లో తప్పనిసరిగా ఇవ్వు: [SLUG: english-slug-here]

ఇది ఒక వ్యాధి / ఆరోగ్య సమస్య గురించిన వ్యాసం. దిగువ నిర్మాణాన్ని అనుసరించు:

<article>

<h1>[SEO keyword తో ఆకర్షణీయమైన శీర్షిక — 60 అక్షరాల లోపు]</h1>

<p style="font-size:1.1em; line-height:1.9; color:#2d2d2d;">[5-6 వాక్యాల ముందుమాట. ఈ వ్యాధి ఎంత మందిలో వస్తుందో, ఎందుకు శ్రద్ధ అవసరమో వివరించు. పాఠకుడిని వెంటనే ఆకట్టుకో.]</p>

{{IMAGE_PLACEHOLDER}}

<h2>ఈ వ్యాధి అంటే ఏమిటి?</h2>
<p>[కనీసం 200 పదాలు. వ్యాధి స్వభావం, శరీరంలో ఏం జరుగుతుందో, ఎవరికి ఎక్కువగా వస్తుందో వివరించు.]</p>
<p>[వ్యాధి రకాలు లేదా దశలు ఉంటే వివరించు. శాస్త్రీయ నేపథ్యం సరళంగా వివరించు.]</p>

<h2>లక్షణాలు ఏమిటి?</h2>
<p>[100 పదాలు — లక్షణాల గురించి ప్రారంభ వివరణ]</p>
<ul style="padding-left:22px; line-height:2.1;">
  <li style="margin-bottom:8px;">✅ [లక్షణం 1 — వివరంగా]</li>
  <li style="margin-bottom:8px;">✅ [లక్షణం 2 — వివరంగా]</li>
  <li style="margin-bottom:8px;">✅ [లక్షణం 3 — వివరంగా]</li>
  <li style="margin-bottom:8px;">✅ [లక్షణం 4 — వివరంగా]</li>
  <li style="margin-bottom:8px;">✅ [లక్షణం 5 — వివరంగా]</li>
</ul>

{_WARNING_BOX}

<h2>కారణాలు ఏమిటి?</h2>
<p>[కనీసం 200 పదాలు. జీవనశైలి, జన్యు, పర్యావరణ కారణాలు వివరంగా రాయి. ఉదాహరణలతో వివరించు.]</p>

<h2>నివారణ మరియు నిర్వహణ</h2>
<p>[100 పదాలు — ఎందుకు నివారణ సాధ్యమో వివరించు]</p>
<ol style="padding-left:22px; line-height:1.9;">
  <li style="margin-bottom:12px;"><strong>[నివారణ చర్య 1]</strong> — [2-3 వాక్యాల వివరణ]</li>
  <li style="margin-bottom:12px;"><strong>[నివారణ చర్య 2]</strong> — [2-3 వాక్యాల వివరణ]</li>
  <li style="margin-bottom:12px;"><strong>[నివారణ చర్య 3]</strong> — [2-3 వాక్యాల వివరణ]</li>
  <li style="margin-bottom:12px;"><strong>[నివారణ చర్య 4]</strong> — [2-3 వాక్యాల వివరణ]</li>
  <li style="margin-bottom:12px;"><strong>[నివారణ చర్య 5]</strong> — [2-3 వాక్యాల వివరణ]</li>
</ol>

{_TIP_BOX}

<h2>డాక్టర్‌ను ఎప్పుడు కలవాలి?</h2>
<p>[కనీసం 150 పదాలు. ఏ లక్షణాలు వస్తే వెంటనే వైద్యుడిని కలవాలో స్పష్టంగా చెప్పు. ఏ పరీక్షలు చేయించుకోవాలో సూచించు.]</p>

{_FAQ_BLOCK}

<h2>ముగింపు</h2>
<p>[100-120 పదాలు. ముఖ్య అంశాలు సంక్షిప్తంగా గుర్తుచేసి పాఠకుడిని ధైర్యపరచు.]</p>

{_DISCLAIMER_BLOCK}

</article>

ఇప్పుడు పూర్తి వ్యాసాన్ని రాయడం ప్రారంభించు:"""


# ---------------------------------------------------------------------------
# Template 2 — Nutrition / Foods  🥗
# ---------------------------------------------------------------------------

def _prompt_nutrition(topic: str, links_text: str) -> str:
    return f"""నువ్వు ఒక అనుభవజ్ఞుడైన తెలుగు ఆహార శాస్త్ర రచయిత. సాధారణ తెలుగు కుటుంబాలకు అర్థమయ్యే సరళమైన భాషలో రాయాలి.

విషయం: {topic}
{links_text}
{_COMMON_RULES}

మొదటి లైన్‌లో తప్పనిసరిగా ఇవ్వు: [SLUG: english-slug-here]

ఇది పోషణ / ఆహారాలకు సంబంధించిన వ్యాసం. దిగువ నిర్మాణాన్ని అనుసరించు:

<article>

<h1>[SEO keyword తో ఆకర్షణీయమైన శీర్షిక — 60 అక్షరాల లోపు]</h1>

<p style="font-size:1.1em; line-height:1.9; color:#2d2d2d;">[5-6 వాక్యాల ముందుమాట. ఈ పోషకం / ఆహారం ఎందుకు ముఖ్యమో, దాని లోపం వల్ల ఏం జరుగుతుందో వివరించు.]</p>

{{IMAGE_PLACEHOLDER}}

<h2>ఇది మన శరీరానికి ఎందుకు అవసరం?</h2>
<p>[కనీసం 200 పదాలు. శరీరంలో ఈ పోషకం పాత్ర ఏమిటో, లోపం వల్ల ఏ సమస్యలు వస్తాయో వివరించు.]</p>
<p>[రోజువారీ అవసరమైన పరిమాణం, వయస్సు వారీగా తేడా వివరించు.]</p>

<h2>ఈ పోషకం అధికంగా ఉన్న ఆహారాలు</h2>
<p>[100 పదాలు — పరిచయం]</p>

<div style="overflow-x:auto; margin:24px 0;">
  <table style="width:100%; border-collapse:collapse; font-family:inherit; font-size:0.97em; border-radius:10px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <thead>
      <tr style="background:linear-gradient(90deg,#1b5e20,#388e3c); color:#fff;">
        <th style="padding:13px 16px; text-align:left; font-weight:600;">ఆహారం</th>
        <th style="padding:13px 16px; text-align:left; font-weight:600;">పోషకం పరిమాణం</th>
        <th style="padding:13px 16px; text-align:left; font-weight:600;">అదనపు లాభం</th>
      </tr>
    </thead>
    <tbody>
      <tr style="background:#f1f8e9;"><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[ఆహారం 1]</td><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[పరిమాణం]</td><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[లాభం]</td></tr>
      <tr style="background:#fff;"><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[ఆహారం 2]</td><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[పరిమాణం]</td><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[లాభం]</td></tr>
      <tr style="background:#f1f8e9;"><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[ఆహారం 3]</td><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[పరిమాణం]</td><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[లాభం]</td></tr>
      <tr style="background:#fff;"><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[ఆహారం 4]</td><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[పరిమాణం]</td><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[లాభం]</td></tr>
      <tr style="background:#f1f8e9;"><td style="padding:11px 16px;">[ఆహారం 5]</td><td style="padding:11px 16px;">[పరిమాణం]</td><td style="padding:11px 16px;">[లాభం]</td></tr>
    </tbody>
  </table>
</div>

<p>[పైన జాబితా చేసిన ప్రతి ఆహారం గురించి 2-3 వాక్యాలు రాయి — దాని ప్రత్యేకత ఏమిటి, ఎలా తినాలి.]</p>

{_TIP_BOX}

<h2>రోజువారీ ఆహారంలో ఎలా చేర్చాలి?</h2>
<p>[కనీసం 150 పదాలు — ఆచరణాత్మక సలహాలు]</p>
<ul style="padding-left:22px; line-height:2;">
  <li>[ఉదయం ఆహారంలో చేర్చే విధం]</li>
  <li>[మధ్యాహ్నం ఆహారంలో చేర్చే విధం]</li>
  <li>[రాత్రి ఆహారంలో చేర్చే విధం]</li>
  <li>[వంట చేసే తీరు — పోషకాలు నష్టపోకుండా]</li>
</ul>

{_WARNING_BOX}

{_FAQ_BLOCK}

<h2>ముగింపు</h2>
<p>[100-120 పదాలు. చిన్న మార్పులు పెద్ద తేడా తెస్తాయని ఉత్సాహంగా చెప్పు.]</p>

{_DISCLAIMER_BLOCK}

</article>

ఇప్పుడు పూర్తి వ్యాసాన్ని రాయడం ప్రారంభించు:"""


# ---------------------------------------------------------------------------
# Template 3 — Herb / Home Remedy  🌿
# ---------------------------------------------------------------------------

def _prompt_herb(topic: str, links_text: str) -> str:
    return f"""నువ్వు ఒక అనుభవజ్ఞుడైన తెలుగు ఆయుర్వేద రచయిత. సాధారణ తెలుగు కుటుంబాలకు అర్థమయ్యే సరళమైన భాషలో రాయాలి.

విషయం: {topic}
{links_text}
{_COMMON_RULES}

మొదటి లైన్‌లో తప్పనిసరిగా ఇవ్వు: [SLUG: english-slug-here]

ఇది ఆయుర్వేద మూలిక / ఇంటి చిట్కాకు సంబంధించిన వ్యాసం. దిగువ నిర్మాణాన్ని అనుసరించు:

<article>

<h1>[SEO keyword తో ఆకర్షణీయమైన శీర్షిక — 60 అక్షరాల లోపు]</h1>

<p style="font-size:1.1em; line-height:1.9; color:#2d2d2d;">[5-6 వాక్యాల ముందుమాట. ఈ మూలిక భారతీయ వంటింట్లో ఎంత ముఖ్యమో, ఎందుకు తరతరాలుగా ఉపయోగిస్తున్నారో వివరించు.]</p>

{{IMAGE_PLACEHOLDER}}

<h2>ఆయుర్వేదంలో ప్రాముఖ్యత</h2>
<p>[కనీసం 200 పదాలు. చరక సంహిత, అథర్వ వేదం లేదా సుశ్రుత సంహితలో ఈ మూలిక గురించి ఏమి చెప్పారో సూచించు. చారిత్రక, సాంస్కృతిక నేపథ్యం వివరించు.]</p>

<h2>ముఖ్యమైన ఔషధ గుణాలు</h2>
<p>[100 పదాలు — ఏ రసాయన సమ్మేళనాలు ఉన్నాయో సరళంగా వివరించు]</p>
<ul style="padding-left:22px; line-height:2.1;">
  <li style="margin-bottom:8px;">🌿 <strong>[గుణం 1]</strong> — [వివరణ]</li>
  <li style="margin-bottom:8px;">🌿 <strong>[గుణం 2]</strong> — [వివరణ]</li>
  <li style="margin-bottom:8px;">🌿 <strong>[గుణం 3]</strong> — [వివరణ]</li>
  <li style="margin-bottom:8px;">🌿 <strong>[గుణం 4]</strong> — [వివరణ]</li>
</ul>

<h2>ఎలా తయారు చేయాలి / ఎలా వాడాలి?</h2>
<p>[100 పదాలు — ఎందుకు సరైన తయారీ ముఖ్యమో వివరించు]</p>
<ol style="padding-left:22px; line-height:1.9;">
  <li style="margin-bottom:12px;">[దశ 1 — వివరంగా]</li>
  <li style="margin-bottom:12px;">[దశ 2 — వివరంగా]</li>
  <li style="margin-bottom:12px;">[దశ 3 — వివరంగా]</li>
  <li style="margin-bottom:12px;">[దశ 4 — వివరంగా]</li>
</ol>

<div style="overflow-x:auto; margin:24px 0;">
  <table style="width:100%; border-collapse:collapse; font-family:inherit; font-size:0.97em; border-radius:10px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.08);">
    <thead>
      <tr style="background:linear-gradient(90deg,#1b5e20,#388e3c); color:#fff;">
        <th style="padding:13px 16px; text-align:left; font-weight:600;">వాడే విధం</th>
        <th style="padding:13px 16px; text-align:left; font-weight:600;">పరిమాణం</th>
        <th style="padding:13px 16px; text-align:left; font-weight:600;">ఎవరికి ఉపయోగం</th>
      </tr>
    </thead>
    <tbody>
      <tr style="background:#f1f8e9;"><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[విధం 1]</td><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[పరిమాణం]</td><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[ఉపయోగం]</td></tr>
      <tr style="background:#fff;"><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[విధం 2]</td><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[పరిమాణం]</td><td style="padding:11px 16px; border-bottom:1px solid #e0e0e0;">[ఉపయోగం]</td></tr>
      <tr style="background:#f1f8e9;"><td style="padding:11px 16px;">[విధం 3]</td><td style="padding:11px 16px;">[పరిమాణం]</td><td style="padding:11px 16px;">[ఉపయోగం]</td></tr>
    </tbody>
  </table>
</div>

{_TIP_BOX}

{_WARNING_BOX}

{_FAQ_BLOCK}

<h2>ముగింపు</h2>
<p>[100-120 పదాలు. ప్రకృతి మనకు ఇచ్చిన ఈ వరాన్ని సరిగ్గా ఉపయోగించుకోమని ఉత్సాహంగా చెప్పు.]</p>

{_DISCLAIMER_BLOCK}

</article>

ఇప్పుడు పూర్తి వ్యాసాన్ని రాయడం ప్రారంభించు:"""


# ---------------------------------------------------------------------------
# Template 4 — Lifestyle / Fitness  💪
# ---------------------------------------------------------------------------

def _prompt_lifestyle(topic: str, links_text: str) -> str:
    return f"""నువ్వు ఒక అనుభవజ్ఞుడైన తెలుగు ఆరోగ్య జీవనశైలి రచయిత. సాధారణ తెలుగు కుటుంబాలకు అర్థమయ్యే సరళమైన భాషలో రాయాలి.

విషయం: {topic}
{links_text}
{_COMMON_RULES}

మొదటి లైన్‌లో తప్పనిసరిగా ఇవ్వు: [SLUG: english-slug-here]

ఇది జీవనశైలి / ఆరోగ్య అలవాట్లకు సంబంధించిన వ్యాసం. దిగువ నిర్మాణాన్ని అనుసరించు:

<article>

<h1>[SEO keyword తో ఆకర్షణీయమైన శీర్షిక — 60 అక్షరాల లోపు]</h1>

<p style="font-size:1.1em; line-height:1.9; color:#2d2d2d;">[5-6 వాక్యాల ముందుమాట. చాలా మంది ఈ విషయంలో ఎందుకు చిన్న మార్పు కూడా చేయలేకపోతున్నారో, ఇది నేర్చుకుంటే ఎంత మేలో వివరించు.]</p>

{{IMAGE_PLACEHOLDER}}

<h2>చాలా మంది చేసే సాధారణ తప్పులు</h2>
<p>[కనీసం 200 పదాలు. నిజాయితీగా, ఆసక్తికరంగా రాయి. పాఠకుడు "అవును ఇది నేనే చేస్తున్నాను" అనుకునేలా రాయి.]</p>

<h2>సరైన విధానం ఏమిటి?</h2>
<p>[కనీసం 200 పదాలు. శాస్త్రీయ ఆధారాలతో, సరళంగా వివరించు.]</p>

<h2>రోజువారీ దినచర్యలో మార్పులు — అడుగు అడుగుగా</h2>
<p>[100 పదాలు — ఈ మార్పులు ఎందుకు సాధ్యమో వివరించు]</p>
<ol style="padding-left:22px; line-height:1.9;">
  <li style="margin-bottom:16px;"><strong>[మార్పు 1]</strong><br>[3-4 వాక్యాలు — ఎందుకు ముఖ్యమో, ఎలా మొదలుపెట్టాలో వివరించు]</li>
  <li style="margin-bottom:16px;"><strong>[మార్పు 2]</strong><br>[3-4 వాక్యాలు]</li>
  <li style="margin-bottom:16px;"><strong>[మార్పు 3]</strong><br>[3-4 వాక్యాలు]</li>
  <li style="margin-bottom:16px;"><strong>[మార్పు 4]</strong><br>[3-4 వాక్యాలు]</li>
  <li style="margin-bottom:16px;"><strong>[మార్పు 5]</strong><br>[3-4 వాక్యాలు]</li>
</ol>

{_TIP_BOX}

<h2>ఇవి తప్పకుండా గుర్తుంచుకో</h2>
<ul style="padding-left:22px; line-height:2.1;">
  <li style="margin-bottom:8px;">📌 [గుర్తుంచుకోవాల్సిన విషయం 1]</li>
  <li style="margin-bottom:8px;">📌 [గుర్తుంచుకోవాల్సిన విషయం 2]</li>
  <li style="margin-bottom:8px;">📌 [గుర్తుంచుకోవాల్సిన విషయం 3]</li>
  <li style="margin-bottom:8px;">📌 [గుర్తుంచుకోవాల్సిన విషయం 4]</li>
</ul>

{_WARNING_BOX}

{_FAQ_BLOCK}

<h2>ముగింపు</h2>
<p>[100-120 పదాలు. చిన్న మొదలే పెద్ద విజయం — పాఠకుడిని ఉత్సాహంగా చేర్చు.]</p>

{_DISCLAIMER_BLOCK}

</article>

ఇప్పుడు పూర్తి వ్యాసాన్ని రాయడం ప్రారంభించు:"""


# ---------------------------------------------------------------------------
# Template 5 — Women's Health  👩
# ---------------------------------------------------------------------------

def _prompt_women(topic: str, links_text: str) -> str:
    return f"""నువ్వు ఒక అనుభవజ్ఞుడైన తెలుగు మహిళల ఆరోగ్య రచయిత. ఆప్యాయంగా, అర్థమయ్యే సరళమైన భాషలో రాయాలి.

విషయం: {topic}
{links_text}
{_COMMON_RULES}

మొదటి లైన్‌లో తప్పనిసరిగా ఇవ్వు: [SLUG: english-slug-here]

ఇది మహిళల ఆరోగ్యానికి సంబంధించిన వ్యాసం. ఆప్యాయంగా, నమ్మకంగా రాయి. దిగువ నిర్మాణాన్ని అనుసరించు:

<article>

<h1>[SEO keyword తో ఆకర్షణీయమైన శీర్షిక — 60 అక్షరాల లోపు]</h1>

<p style="font-size:1.1em; line-height:1.9; color:#2d2d2d;">[5-6 వాక్యాల ఆప్యాయమైన ముందుమాట. చాలా మంది మహిళలు ఈ సమస్యను మౌనంగా భరిస్తారని, ఇది సహజమే కానీ దీని గురించి మాట్లాడటం ముఖ్యమని చెప్పు.]</p>

{{IMAGE_PLACEHOLDER}}

<h2>ఇది అంటే ఏమిటి?</h2>
<p>[కనీసం 200 పదాలు. స్పష్టంగా, అర్థమయ్యే భాషలో వివరించు. శాస్త్రీయ వివరణను సరళంగా చెప్పు.]</p>

<h2>లక్షణాలు మరియు సంకేతాలు</h2>
<p>[100 పదాలు — ఎందుకు లక్షణాలను గుర్తించడం ముఖ్యమో వివరించు]</p>
<ul style="padding-left:22px; line-height:2.1;">
  <li style="margin-bottom:8px;">🔴 [లక్షణం 1 — వివరంగా]</li>
  <li style="margin-bottom:8px;">🔴 [లక్షణం 2 — వివరంగా]</li>
  <li style="margin-bottom:8px;">🔴 [లక్షణం 3 — వివరంగా]</li>
  <li style="margin-bottom:8px;">🔴 [లక్షణం 4 — వివరంగా]</li>
  <li style="margin-bottom:8px;">🔴 [లక్షణం 5 — వివరంగా]</li>
</ul>

<h2>సహజ నివారణ మరియు నిర్వహణ</h2>
<p>[కనీసం 200 పదాలు — ఆహారం, జీవనశైలి, ఒత్తిడి నిర్వహణ వివరంగా రాయి]</p>
<ol style="padding-left:22px; line-height:1.9;">
  <li style="margin-bottom:12px;"><strong>[చర్య 1]</strong> — [2-3 వాక్యాలు]</li>
  <li style="margin-bottom:12px;"><strong>[చర్య 2]</strong> — [2-3 వాక్యాలు]</li>
  <li style="margin-bottom:12px;"><strong>[చర్య 3]</strong> — [2-3 వాక్యాలు]</li>
  <li style="margin-bottom:12px;"><strong>[చర్య 4]</strong> — [2-3 వాక్యాలు]</li>
</ol>

{_TIP_BOX}

{_WARNING_BOX}

<h2>వైద్యుడిని ఎప్పుడు కలవాలి?</h2>
<p>[కనీసం 150 పదాలు. ఏ సంకేతాలు వస్తే వెంటనే వైద్యుడిని కలవాలో స్పష్టంగా చెప్పు. ముందుగా కలవడం వల్ల ఎంత మేలో వివరించు.]</p>

{_FAQ_BLOCK}

<h2>ముగింపు</h2>
<p>[100-120 పదాలు. నీ ఆరోగ్యం నీ చేతిలోనే ఉందని, సకాలంలో శ్రద్ధ తీసుకోమని ఆప్యాయంగా చెప్పు.]</p>

{_DISCLAIMER_BLOCK}

</article>

ఇప్పుడు పూర్తి వ్యాసాన్ని రాయడం ప్రారంభించు:"""


# ---------------------------------------------------------------------------
# Main router — picks the right template based on topic
# ---------------------------------------------------------------------------

def _build_article_prompt(topic: str, past_urls: list = None) -> str:
    """Route to the correct template based on detected topic type."""

    links_text = ""
    if past_urls:
        links_text = "\nకింది మన పాత ఆర్టికల్స్ లింక్స్ ని వ్యాసంలో ఎక్కడైనా సంబంధం ఉన్నచోట సహజంగా (Natural anchor text) 1 లేదా 2 లింక్స్ గా (HTML <a> tag) వాడండి:\n"
        for url_info in past_urls:
            links_text += f"- {url_info['title']}: {url_info['url']}\n"

    topic_type = _detect_topic_type(topic)
    template_map = {
        "disease":   _prompt_disease,
        "nutrition": _prompt_nutrition,
        "herb":      _prompt_herb,
        "lifestyle": _prompt_lifestyle,
        "women":     _prompt_women,
    }
    builder = template_map.get(topic_type, _prompt_disease)
    print(f"📋 Article template: {topic_type.upper()} → {topic}")
    return builder(topic, links_text)

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
            
            # ---------------------------------------------------------------
            # Extract Slug — catch ALL formats the AI might use:
            #   [SLUG: some-slug]  /  English Topic Slug: some-slug
            #   **Slug:** some-slug  /  slug: some-slug  (inside any tag)
            # ---------------------------------------------------------------
            slug = "health-article"
            slug_patterns = [
                r"\[SLUG:\s*([^\]\n]+)\]",                          # [SLUG: slug]
                r"(?:English\s+Topic\s+)?Slug:\s*([a-z0-9][a-z0-9\-]*)",  # English Topic Slug: slug
                r"slug[:\s]+([a-z0-9][a-z0-9\-]{3,60})",             # slug: slug (lowercase)
            ]
            for pat in slug_patterns:
                m = re.search(pat, content, re.IGNORECASE)
                if m:
                    slug = m.group(1).strip().lower().replace(" ", "-")
                    break

            # Aggressively strip ALL slug-related lines from the content
            # (handles plain text, inside headings, bold, etc.)
            content = re.sub(r"\[SLUG:[^\]]*\]", "", content)
            content = re.sub(
                r"(<[^>]*>)?\s*(?:English\s+Topic\s+)?Slug:\s*[a-z0-9][a-z0-9\-]*\s*(</[^>]*>)?",
                "", content, flags=re.IGNORECASE
            )
            content = content.strip()
            
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
    
    # --- Groq Fallback Chain ---
    # Fallback 1: llama-4-scout-17b (500K tokens/day — best daily budget)
    # Fallback 2: llama-3.3-70b-versatile (100K tokens/day — best Telugu quality)
    GROQ_MODELS = [
        ("meta-llama/llama-4-scout-17b-16e-instruct", "Llama 4 Scout 17B"),
        ("llama-3.3-70b-versatile",                   "Llama 3.3 70B Versatile"),
    ]

    if not groq_client:
        print("❌ Groq fallback skipped: GROQ_API_KEY not configured.")
        raise Exception(f"Failed to generate article for '{topic}' using both Gemini and Groq.")

    groq_system = (
        "You are an expert Telugu health writer. "
        "Follow all HTML formatting instructions exactly. "
        "Generate long, detailed, AdSense-ready articles with tables, "
        "tip boxes, and info boxes as instructed."
    )

    for model_id, model_label in GROQ_MODELS:
        print(f"🔄 Attempting Groq fallback ({model_label})...")
        for groq_attempt in range(3):
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": groq_system},
                        {"role": "user",   "content": prompt}
                    ],
                    model=model_id,
                    temperature=0.72,
                    max_tokens=5000,
                )
                content = chat_completion.choices[0].message.content

                # Clean up markdown code blocks if present
                content = re.sub(r"```html\s*", "", content)
                content = re.sub(r"```\s*$",   "", content)
                content = content.strip()

                # Extract Slug
                slug = "health-article"
                slug_match = re.search(r"\[SLUG:\s*([^\]]+)\]", content)
                if slug_match:
                    slug = slug_match.group(1).strip().lower().replace(" ", "-")
                    content = content.replace(slug_match.group(0), "").strip()

                # Extract title
                title = _extract_title(content)
                if not title:
                    title = topic

                # Length validation
                plain_text = re.sub(r"<[^>]+>", "", content)
                plain_text_clean = re.sub(r"\s+", " ", plain_text).strip()

                if len(plain_text_clean) < 2000:
                    print(f"⚠️ {model_label} article too short ({len(plain_text_clean)} chars). Retrying... ({groq_attempt+1}/3)")
                    if groq_attempt == 2:
                        raise Exception(f"{model_label} length validation failed after 3 attempts.")
                    time.sleep(2)
                    continue

                # Generate tags & meta description
                tags = _build_tags(topic)
                meta_desc = plain_text_clean[:160] + "..." if len(plain_text_clean) > 160 else plain_text_clean

                print(f"✅ Article generated via {model_label}: '{title}' ({len(content)} chars)")
                return {
                    "topic": topic,
                    "title": title,
                    "slug": slug,
                    "body_html": content,
                    "tags": tags,
                    "meta_description": meta_desc,
                }

            except Exception as groq_e:
                err = str(groq_e)
                # If daily token limit hit, skip immediately to next model
                if "rate_limit" in err.lower() or "429" in err or "quota" in err.lower():
                    print(f"⚠️ {model_label} daily limit hit — trying next model...")
                    break
                print(f"❌ {model_label} failed on attempt {groq_attempt+1}: {groq_e}")
                if groq_attempt == 2:
                    break
                time.sleep(2)

    raise Exception(f"Failed to generate article for '{topic}' using Gemini and all Groq fallbacks.")


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
