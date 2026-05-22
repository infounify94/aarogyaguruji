"""
content_generator.py
====================
Generates Hindi health articles using Google Gemini AI.

Features:
- 1800-2500 word articles in simple, everyday Hindi
- AdSense-friendly HTML structure (clean, no keyword stuffing)
- Styled tables, tip boxes, and info boxes for reader engagement
- Ayurveda content referenced from Atharva Veda and ancient texts
- Human-like writing style (not robotic AI tone)
- Proper subheadings, bullet points, Q&A sections
- Disclaimer and doctor consultation advice
"""

import os
import re
import sys
import time
import random

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

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

_FAQ_BLOCK = """<h2>अक्सर पूछे जाने वाले प्रश्न (FAQ)</h2>
<div style="margin:20px 0;">
  <div style="border-bottom:1px solid #e8e8e8; padding:16px 0;">
    <p style="margin:0 0 8px; font-weight:600; color:#1b5e20;">&#9658; [पाठकों द्वारा पूछा जाने वाला सामान्य प्रश्न 1]</p>
    <p style="margin:0; color:#444; line-height:1.8;">[स्पष्ट उत्तर — कम से कम 3-4 वाक्य]</p>
  </div>
  <div style="border-bottom:1px solid #e8e8e8; padding:16px 0;">
    <p style="margin:0 0 8px; font-weight:600; color:#1b5e20;">&#9658; [पाठकों द्वारा पूछा जाने वाला सामान्य प्रश्न 2]</p>
    <p style="margin:0; color:#444; line-height:1.8;">[स्पष्ट उत्तर — कम से कम 3-4 वाक्य]</p>
  </div>
  <div style="border-bottom:1px solid #e8e8e8; padding:16px 0;">
    <p style="margin:0 0 8px; font-weight:600; color:#1b5e20;">&#9658; [पाठकों द्वारा पूछा जाने वाला सामान्य प्रश्न 3]</p>
    <p style="margin:0; color:#444; line-height:1.8;">[स्पष्ट उत्तर — कम से कम 3-4 वाक्य]</p>
  </div>
</div>"""

_DISCLAIMER_BLOCK = """<div style="background:#e3f2fd; border-left:5px solid #1976d2; border-radius:8px; padding:18px 22px; margin:28px 0;">
  <p style="margin:0; font-size:0.95em; line-height:1.8; color:#1a237e;"><strong>🏥 मेडिकल अस्वीकरण:</strong> इस लेख में दी गई जानकारी केवल सामान्य जागरूकता के लिए है। यह पेशेवर चिकित्सा सलाह का विकल्प नहीं है। किसी भी स्वास्थ्य समस्या के मामले में, कृपया हमेशा एक योग्य डॉक्टर से परामर्श लें।</p>
</div>"""

_TIP_BOX = """<div style="background:#e8f5e9; border-left:5px solid #43a047; border-radius:8px; padding:18px 22px; margin:24px 0;">
  <p style="margin:0; font-size:1em; line-height:1.8;"><strong>💡 महत्वपूर्ण टिप:</strong> [एक व्यावहारिक टिप जिसे पाठक तुरंत अपना सकें]</p>
</div>"""

_WARNING_BOX = """<div style="background:#fff8e1; border-left:5px solid #f9a825; border-radius:8px; padding:18px 22px; margin:24px 0;">
  <p style="margin:0; font-size:1em; line-height:1.8;"><strong>⚠️ सावधानी:</strong> [यहाँ स्पष्ट रूप से बताएं कि किसे सावधान रहना चाहिए या डॉक्टर से कब मिलना चाहिए]</p>
</div>"""

_COMMON_RULES = """महत्वपूर्ण नियम (VERY IMPORTANT):
1. भाषा और शैली (Natural Mix of Hindi & English terms):
   - लेख सरल, स्पष्ट और आकर्षक हिंदी में होना चाहिए।
   - रोज़मर्रा की बातचीत में इस्तेमाल होने वाले सामान्य अंग्रेज़ी शब्दों का प्रयोग ब्रैकेट में या सीधे हिंदी लिप्यंतरण (transliteration) में अवश्य करें। उदाहरण के लिए: "एनाजेन फेज (Anagen Phase)", "हार्मोन (Hormones)", "हेयर फॉलिकल्स (Hair Follicles)", "ब्लड सर्कुलेशन (Blood Circulation)", "डाइट प्लान (Diet Plan)", "ऑक्सीजन (Oxygen)"। इससे पाठकों को पढ़ने में बहुत सहजता होगी।
2. डायनामिक लेख संरचना (CRITICAL - Dynamic layouts per topic):
   - सभी लेख एक जैसे उबाऊ लेआउट में नहीं होने चाहिए। विषय के अनुसार लेआउट को डायनामिक बनाएं।
   - आवश्यकतानुसार डाइट टेबल्स, तुलना तालिकाओं (comparison tables), या साप्ताहिक शेड्यूल (weekly schedules) के लिए सुंदर HTML तालिकाओं (`<table>` टैग्स) का उपयोग करें।
   - HTML तालिकाओं को नीचे दी गई शैली में सुंदर ढंग से डिज़ाइन करें (हरे रंग की थीम, पैडिंग और बॉर्डर के साथ):
     <table style="width:100%; border-collapse:collapse; margin:20px 0; border:1px solid #e0e0e0; border-radius:8px; overflow:hidden; font-size:15px; text-align:left;">
       <thead>
         <tr style="background-color:#2e7d32; color:white;">
           <th style="padding:12px; font-weight:600;">चरण / विधि (Stage)</th>
           <th style="padding:12px; font-weight:600;">विवरण (Description)</th>
         </tr>
       </thead>
       <tbody>
         <tr style="border-bottom:1px solid #e0e0e0;">
           <td style="padding:12px; font-weight:600; color:#2e7d32;">एनाजेन फेज (Anagen Phase)</td>
           <td style="padding:12px; color:#444;">यह बालों के सक्रिय रूप से बढ़ने का चरण है...</td>
         </tr>
       </tbody>
     </table>
3. स्वरूपण नियम (CRITICAL - No Raw Markdown):
   - **किसी भी परिस्थिति में डबल एस्टरिस्क (** दोनों तरफ) या मार्कडाउन हेडर (#, ##, ###) का उपयोग न करें!** ये ब्लॉग पर ठीक से नहीं दिखते हैं।
   - बोल्ड करने के लिए केवल HTML टैग्स `<strong>` या `<b>` का ही उपयोग करें।
   - शीर्षकों (headings) के लिए केवल `<h2>`, `<h3>` टैग्स का उपयोग करें।
4. पैराग्राफ और सूची प्रारूप (Separate paragraphs for readability):
   - एक ही बड़े पैराग्राफ में कई बिंदु या चरण (जैसे: 1, 2, 3) मिलाकर न लिखें।
   - प्रत्येक बिंदु या चरण को अलग से एक स्वतंत्र पैराग्राफ (`<p>` टैग) में या शीर्षक और पैराग्राफ के रूप में लिखें।
5. लंबाई: कम से कम 1800 शब्द। प्रत्येक अनुभाग (section) को बहुत विस्तार से लिखें।
6. शैली — बहुत महत्वपूर्ण:
   - ऐसे लिखें जैसे पड़ोस का कोई भाई या बहन बात कर रहा हो।
   - "नमस्ते", "इस लेख में", "आप जानेंगे" जैसे कृत्रिम AI वाक्यांशों का उपयोग न करें।
   - सीधे विषय पर आएं, परिचय में समय बर्बाद न करें।
7. इमेज प्लेसहोल्डर:
   - पहला पैराग्राफ पूरा होने के तुरंत बाद एक नई लाइन में {{IMAGE_PLACEHOLDER}} अवश्य लिखें। इसे पैराग्राफ के बीच में या किसी अन्य टैग के अंदर न छिपाएं।
8. AdSense: कीवर्ड स्टफिंग न करें। पाठकों के लिए वास्तव में उपयोगी होने के लिए लिखें।
9. सभी प्लेसहोल्डर्स को वास्तविक जानकारी से भरें — कोई भी प्लेसहोल्डर लेख में दिखाई नहीं देना चाहिए।
10. SLUG केवल पहली लाइन में दें — लेख में कहीं और स्लग का उल्लेख न करें।"""


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
    return f"""నువ్వు ఒక అనుభవజ్ఞుడైన हिंदी स्वास्थ्य लेखक (Hindi Health Writer). సాధారణ తెలుగు కుటుంబాలకు అర్థమయ్యే సరళమైన భాషలో రాయాలి.

విషయం: {topic}
{links_text}
{_COMMON_RULES}

మొదటి లైన్‌లో తప్పనిసరిగా ఇవ్వు: [SLUG: write-topic-name-in-english-words-with-hyphens] (ఉదాహరణకు: [SLUG: health-benefits-of-tulasi])

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

మొదటి లైన్‌లో తప్పనిసరిగా ఇవ్వు: [SLUG: write-topic-name-in-english-words-with-hyphens] (ఉదాహరణకు: [SLUG: health-benefits-of-tulasi])

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

మొదటి లైన్‌లో తప్పనిసరిగా ఇవ్వు: [SLUG: write-topic-name-in-english-words-with-hyphens] (ఉదాహరణకు: [SLUG: health-benefits-of-tulasi])

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

మొదటి లైన్‌లో తప్పనిసరిగా ఇవ్వు: [SLUG: write-topic-name-in-english-words-with-hyphens] (ఉదాహరణకు: [SLUG: health-benefits-of-tulasi])

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

మొదటి లైన్‌లో తప్పనిసరిగా ఇవ్వు: [SLUG: write-topic-name-in-english-words-with-hyphens] (ఉదాహరణకు: [SLUG: health-benefits-of-tulasi])

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
<p>[100-120 పదాలు. నీ स्वास्थ्य (Health) నీ చేతిలోనే ఉందని, సకాలంలో శ్రద్ధ తీసుకోమని ఆప్యాయంగా చెప్పు.]</p>

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
    base_tags = ["Hindi", "AarogyaGuruji"]
    
    tag_map = {
        "ఆయుర్వేద": ["आयुर्वेद", "Ayurveda"],
        "అయుర్వేద": ["आयुर्वेद", "Ayurveda"],
        "డయాబెటిస్": ["मधुमेह", "Diabetes"],
        "మధుమేహం": ["मधुमेह", "Diabetes"],
        "గుండె": ["हृदय स्वास्थ्य", "Heart Health"],
        "రక్తపోటు": ["BP", "Blood Pressure", "रक्तचाप"],
        "కిడ్నీ": ["किडनी स्वास्थ्य", "Kidney Health"],
        "లివర్": ["लिवर स्वास्थ्य", "Liver Health"],
        "క్యాన్సర్": ["कैंसर", "Cancer Awareness"],
        "యోగ": ["योग", "Yoga", "व्यायाम"],
        "మానసిక": ["मानसिक स्वास्थ्य", "Mental Health"],
        "ఆహారం": ["पोषण", "Nutrition", "आहार"],
        "చర్మం": ["स्किन केयर", "Skin Care"],
        "జుట్టు": ["हेयर केयर", "Hair Care"],
        "నిద్ర": ["नींद का स्वास्थ्य", "Sleep Health"],
        "PCOS": ["PCOS", "महिला स्वास्थ्य", "Women Health"],
        "బరువు": ["वजन घटाना", "Weight Loss"],
        "ఇమ్యూనిటీ": ["इम्युनिटी", "Immunity"],
        "తులసి": ["जड़ी-बूटियां", "Herbs", "घरेलू नुस्खे"],
        "పసుపు": ["जड़ी-बूटियां", "Herbs"],
    }
    
    extra_tags = []
    for key, tags in tag_map.items():
        if key in topic:
            extra_tags.extend(tags)
    
    all_tags = list(set(base_tags + extra_tags))
    return all_tags[:15]  # Blogger supports up to 20 labels


def _clean_markdown(content: str) -> str:
    """Clean up markdown code blocks, bolding, and headings from LLM output."""
    # Clean up markdown code blocks if present
    content = re.sub(r"```html\s*", "", content)
    content = re.sub(r"```\s*$", "", content)
    content = content.strip()
    
    # Automatically convert raw markdown bold (**text**) to HTML strong (<strong>text</strong>)
    content = re.sub(r"\*\*([^*]+?)\*\*", r"<strong>\1</strong>", content)
    content = re.sub(r"__([^_]+?)__", r"<strong>\1</strong>", content)
    
    # Automatically convert markdown headings (e.g. ### Heading) to HTML headings at the start of lines
    content = re.sub(r"^\s*###\s+(.*?)\s*#*$", r"<h3>\1</h3>", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*##\s+(.*?)\s*#*$", r"<h2>\1</h2>", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*#\s+(.*?)\s*#*$", r"<h1>\1</h1>", content, flags=re.MULTILINE)
    
    # Clean up markdown headings that might be wrapped in paragraph tags (e.g. <p>### Heading</p>)
    content = re.sub(r"<p>\s*###\s+(.*?)\s*</p>", r"<h3>\1</h3>", content, flags=re.IGNORECASE)
    content = re.sub(r"<p>\s*##\s+(.*?)\s*</p>", r"<h2>\1</h2>", content, flags=re.IGNORECASE)
    content = re.sub(r"<p>\s*#\s+(.*?)\s*</p>", r"<h1>\1</h1>", content, flags=re.IGNORECASE)
    
    # Strip leading/trailing hashes/asterisks inside heading and strong tags
    content = re.sub(r"(<h[1-6][^>]*>)\s*#+\s*", r"\1", content, flags=re.IGNORECASE)
    content = re.sub(r"\s*#+\s*(</h[1-6]>)", r"\1", content, flags=re.IGNORECASE)
    content = re.sub(r"(<strong[^>]*>|<b[^>]*>)\s*\*+\s*", r"\1", content, flags=re.IGNORECASE)
    content = re.sub(r"\s*\*+\s*(</strong>|</b>)", r"\1", content, flags=re.IGNORECASE)
    
    # Clean up any leftover double asterisks entirely just in case
    content = content.replace("**", "")
    
    return content.strip()


def generate_article(topic: str, past_urls: list = None) -> dict:
    """
    Generate a full Hindi health article using Gemini AI.
    
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
            content = _clean_markdown(content)
            
            # ---------------------------------------------------------------
            # Extract Slug — catch ALL formats the AI might use:
            # ---------------------------------------------------------------
            slug = "health-article"
            slug_patterns = [
                r"\[SLUG:\s*([^\]\n]+)\]",
                r"(?:English\s+Topic\s+)?Slug:\s*([a-z0-9][a-z0-9\-]*)",
                r"slug[:\s]+([a-z0-9][a-z0-9\-]{3,60})",
            ]
            for pat in slug_patterns:
                m = re.search(pat, content, re.IGNORECASE)
                if m:
                    extracted = m.group(1).strip().lower()
                    # Clean up the slug
                    extracted = re.sub(r'[^a-z0-9\s-]', '', extracted)
                    extracted = re.sub(r'[\s]+', '-', extracted)
                    extracted = extracted.strip('-')
                    if extracted and len(extracted) > 3:
                        slug = extracted
                        break

            invalid_slugs = [
                "health-article", "english-slug-here", 
                "write-topic-name-in-english-words-with-hyphens", 
                "write-topic-name-in-english-words"
            ]
            
            if slug in invalid_slugs or not slug:
                try:
                    # Fallback: Ask Gemini to just translate the topic to a slug
                    slug_prompt = f"Translate this Hindi health topic to a short English URL slug (lowercase, hyphens only, no numbers if possible, 3-6 words). Topic: '{topic}'. Output ONLY the slug."
                    slug_response = model.generate_content(slug_prompt)
                    fallback_slug = slug_response.text.strip().lower()
                    fallback_slug = re.sub(r'[^a-z0-9\s-]', '', fallback_slug)
                    fallback_slug = re.sub(r'[\s]+', '-', fallback_slug).strip('-')
                    if fallback_slug:
                        slug = fallback_slug
                except Exception as e:
                    print(f"⚠️ Slug fallback generation failed: {e}")
                    english_parts = re.findall(r'[a-zA-Z]+', topic)
                    if english_parts:
                        slug = "-".join(english_parts).lower()
                    else:
                        slug = "health-tips"

            # Aggressively strip ALL slug-related lines from the content
            content = re.sub(r"\[SLUG:[^\]]*\]", "", content)
            content = re.sub(
                r"(<[^>]*>)?\s*(?:English\s+Topic\s+)?Slug:\s*[a-z0-9\s\-]+\s*(</[^>]*>)?",
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
    # Fallback 2: llama-3.3-70b-versatile (100K tokens/day — best Hindi quality)
    GROQ_MODELS = [
        ("meta-llama/llama-4-scout-17b-16e-instruct", "Llama 4 Scout 17B"),
        ("llama-3.3-70b-versatile",                   "Llama 3.3 70B Versatile"),
    ]

    if not groq_client:
        print("❌ Groq fallback skipped: GROQ_API_KEY not configured.")
        raise Exception(f"Failed to generate article for '{topic}' using both Gemini and Groq.")

    groq_system = (
        "You are an expert Hindi health writer. "
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
                content = _clean_markdown(content)

                # Extract Slug
                slug = "health-article"
                slug_match = re.search(r"\[SLUG:\s*([^\]]+)\]", content)
                if slug_match:
                    extracted = slug_match.group(1).strip().lower()
                    extracted = re.sub(r'[^a-z0-9\s-]', '', extracted)
                    extracted = re.sub(r'[\s]+', '-', extracted).strip('-')
                    if extracted and len(extracted) > 3:
                        slug = extracted
                    content = content.replace(slug_match.group(0), "").strip()

                invalid_slugs = [
                    "health-article", "english-slug-here", 
                    "write-topic-name-in-english-words-with-hyphens", 
                    "write-topic-name-in-english-words"
                ]
                
                if slug in invalid_slugs or not slug:
                    english_parts = re.findall(r'[a-zA-Z]+', topic)
                    if english_parts:
                        slug = "-".join(english_parts).lower()
                    else:
                        slug = "health-tips"

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
    """Inject image HTML after the first paragraph or intro section, replacing all placeholders."""
    # Find all placeholder matches, case-insensitive, with 1 or 2 braces and optional spaces/hyphens/underscores
    pattern = re.compile(r"\{{1,2}\s*IMAGE[-_ ]*PLACEHOLDER\s*\}{1,2}", re.IGNORECASE)
    
    matches = list(pattern.finditer(body_html))
    injected = False
    
    if matches:
        # Replace the first matched placeholder with the image_html
        first_match = matches[0]
        start, end = first_match.span()
        body_html = body_html[:start] + image_html + body_html[end:]
        injected = True
        
        # Now remove any other occurrences of the placeholder
        body_html = pattern.sub("", body_html)
    else:
        # If no placeholder with braces was found, check for raw "IMAGE_PLACEHOLDER" text case-insensitively
        raw_pattern = re.compile(r"\bIMAGE[-_ ]*PLACEHOLDER\b", re.IGNORECASE)
        raw_matches = list(raw_pattern.finditer(body_html))
        if raw_matches:
            first_match = raw_matches[0]
            start, end = first_match.span()
            body_html = body_html[:start] + image_html + body_html[end:]
            injected = True
            body_html = raw_pattern.sub("", body_html)

    if injected:
        return body_html

    # Try to inject after first </p> tag if no placeholder was found
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
