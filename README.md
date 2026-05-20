# 🏥 AarogyaGuruji - Automated Telugu Health Blog Publisher

Fully automated system that discovers trending health topics, generates professional Telugu articles using Gemini AI, adds Pexels images, and publishes to Blogger — 3 times daily, 7 articles per run (~21 articles/day).

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Folder Structure](#folder-structure)
3. [Prerequisites & API Keys](#prerequisites--api-keys)
4. [Step 1: Install Dependencies](#step-1-install-dependencies)
5. [Step 2: Setup .env File](#step-2-setup-env-file)
6. [Step 3: Generate OAuth2 Refresh Token](#step-3-generate-oauth2-refresh-token)
7. [Step 4: Run Test Post](#step-4-run-test-post)
8. [Step 5: Setup GitHub Actions](#step-5-setup-github-actions)
9. [Adding GitHub Secrets](#adding-github-secrets)
10. [Publish Schedule](#publish-schedule)
11. [Troubleshooting](#troubleshooting)

---

## 📌 Project Overview

| Feature | Detail |
|---|---|
| **Blog** | AarogyaGuruji (Telugu Health Blog) |
| **Blog ID** | 707690830658262263 |
| **Language** | Telugu (తెలుగు) |
| **AI Model** | Gemini 2.0 Flash (Free tier) |
| **Images** | Pexels API |
| **Topic Source** | NewsData.io + 500+ curated health topics |
| **Publishing** | Blogger API v3 via OAuth2 |
| **Schedule** | 3x daily (7AM, 1PM, 7PM IST) |
| **Articles/day** | ~21 articles |
| **Duplicate Check** | 45-day cooldown per topic |

---

## 📁 Folder Structure

```
aarogyaguruji/
│
├── .github/
│   └── workflows/
│       └── auto_publish.yml      # GitHub Actions (runs 3x daily)
│
├── src/
│   ├── generate_token.py         # ← Run this ONCE to get refresh token
│   ├── test_post.py              # ← Test the full pipeline
│   ├── main.py                   # ← Called by GitHub Actions
│   ├── discover_topics.py        # Trending topic discovery
│   ├── content_generator.py      # Gemini AI article writer
│   ├── image_fetcher.py          # Pexels image fetcher
│   ├── duplicate_checker.py      # Prevents re-posting same topic
│   └── blogger_publisher.py      # Blogger API client
│
├── data/
│   └── posted_topics.json        # Tracks published topics (committed to repo)
│
├── client_secret_*.json          # ← Your Google OAuth credentials (gitignored)
├── requirements.txt
├── .env.example                  # Template for your .env file
├── .env                          # ← Your actual secrets (gitignored)
├── .gitignore
└── README.md
```

---

## 🔑 Prerequisites & API Keys

### 1. Gemini API Key (FREE)
- Go to: https://aistudio.google.com/app/apikey
- Click "Create API Key"
- Copy the key

### 2. Google OAuth2 Credentials (FREE)
Already done! Your `client_secret_*.json` is in the folder.
- **Client ID**: `your_google_client_id_here`
- **Client Secret**: In your client_secret.json file

### 3. Pexels API Key (FREE)
- Go to: https://www.pexels.com/api/
- Sign up and get your API key
- Free: 200 requests/hour, 20,000/month

### 4. NewsData.io API Key (FREE)
- Go to: https://newsdata.io/
- Free: 200 credits/day

### 5. GitHub Personal Access Token (PAT)
- Go to: GitHub → Settings → Developer settings → Personal access tokens
- Create token with `repo` permission
- This lets the bot commit the `posted_topics.json` file

---

## 🚀 Step 1: Install Dependencies

```bash
# Windows
cd "d:\blogger automation\blogger-code\aarogyaguruji"
pip install -r requirements.txt

# Or with virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

---

## ⚙️ Step 2: Setup .env File

Copy the example file and fill in your values:

```bash
# Windows PowerShell
Copy-Item .env.example .env
notepad .env

# Linux/Mac
cp .env.example .env
nano .env
```

Your `.env` should look like:

```env
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REFRESH_TOKEN=           ← Fill this after Step 3
BLOG_ID=707690830658262263
GEMINI_API_KEY=your_gemini_api_key_here
PEXELS_API_KEY=your_pexels_api_key_here
NEWSDATA_API_KEY=your_newsdata_api_key_here
ARTICLES_PER_RUN=7
```

---

## 🔐 Step 3: Generate OAuth2 Refresh Token

> ⚠️ **This step must be done ONCE on your local machine.** It opens a browser for Google login.

```bash
python src/generate_token.py
```

**What happens:**
1. Browser opens automatically → Google login page
2. Login with the Gmail that owns your Blogger blog
3. Click "Allow" on the permissions screen
4. Terminal prints your tokens:

```
🔄 REFRESH TOKEN (permanent - save this!):
   1//0gXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Copy the REFRESH TOKEN** and paste it into:
- Your `.env` file: `GOOGLE_REFRESH_TOKEN=1//0gXxx...`
- GitHub Secrets (see Step 5)

---

## 🧪 Step 4: Run Test Post

After filling `.env` with the refresh token:

```bash
python src/test_post.py
```

**Expected output:**
```
📡 Step 1: Connecting to Blogger API...
   ✅ Connected to: AarogyaGuruji

✍️  Step 2: Generating article...
   ✅ Generated: 'తులసి ఆకుల ఔషధ గుణాలు - 10 వ్యాధులకు రామబాణం'

🖼️  Step 3: Fetching Pexels image...
   ✅ Image fetched

📤 Step 4: Publishing to Blogger...

══════════════════════════════════════
  🎉 SUCCESS! Article Published!
══════════════════════════════════════
  🌐 URL: https://aarogyaguruji.blogspot.com/2026/05/...
```

Visit the URL printed — your article is live! 🎉

---

## 🔧 Step 5: Setup GitHub Actions

### 5.1 Push to GitHub

```bash
cd "d:\blogger automation\blogger-code\aarogyaguruji"
git add .
git commit -m "Initial AarogyaGuruji setup"
git push origin main
```

### 5.2 Add GitHub Secrets (IMPORTANT!)

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add each secret:

| Secret Name | Value |
|---|---|
| `GEMINI_API_KEY` | `your_gemini_api_key_here` |
| `GOOGLE_CLIENT_ID` | `your_google_client_id_here` |
| `GOOGLE_CLIENT_SECRET` | `your_google_client_secret_here` |
| `GOOGLE_REFRESH_TOKEN` | *(from Step 3 - your refresh token)* |
| `PEXELS_API_KEY` | `your_pexels_api_key_here` |
| `NEWSDATA_API_KEY` | `your_newsdata_api_key_here` |
| `BLOG_ID` | `707690830658262263` |
| `GH_PAT` | *(GitHub Personal Access Token with `repo` scope)* |

### 5.3 Test Manual Run

After adding secrets:
1. Go to GitHub → **Actions** tab
2. Click **"AarogyaGuruji - Auto Publish Telugu Health Articles"**
3. Click **"Run workflow"** → **"Run workflow"**
4. Watch the logs!

---

## 📅 Publish Schedule

| Time (IST) | Time (UTC) | Articles |
|---|---|---|
| 7:00 AM | 01:30 UTC | 7 articles |
| 1:00 PM | 07:30 UTC | 7 articles |
| 7:00 PM | 13:30 UTC | 7 articles |
| **Total** | | **~21/day** |

---

## 🗂️ Health Topic Categories

The system covers **20+ health categories**:

- 🌿 Ayurveda & Vedic Medicine (Atharva Veda, Charaka)
- 🏠 Home Remedies (Tulsi, Ginger, Turmeric, etc.)
- 💉 Diabetes Management
- ❤️ Heart Health
- 🧠 Mental Health
- 👩 Women's Health (PCOS, Pregnancy)
- 👨 Men's Health
- 👶 Children's Health
- 🦴 Bone & Joint Health
- 👁️ Eye & Ear Health
- 🍽️ Nutrition & Diet
- 🧘 Yoga & Fitness
- 🫁 Respiratory Health
- 🔬 Thyroid & Hormones
- 🦷 Dental Health
- 🩸 Blood & Immunity
- ⚖️ Weight Management
- 😴 Sleep Health
- 🦠 Infectious Diseases
- 🌍 Environmental Health
- 💊 Alternative Medicine

---

## ❗ Troubleshooting

### Error: "Missing OAuth2 credentials"
→ Check your `.env` file has `GOOGLE_REFRESH_TOKEN` filled in
→ Run `python src/generate_token.py` again

### Error: "403 Forbidden" from Blogger API
→ Make sure Blogger API is enabled in Google Cloud Console:
→ https://console.cloud.google.com/apis/library/blogger.googleapis.com

### Error: "invalid_grant" (token expired)
→ Run `python src/generate_token.py` again to get a fresh refresh token
→ Update `.env` and GitHub Secret `GOOGLE_REFRESH_TOKEN`

### Error: "quota exceeded" from Gemini
→ Free tier: 15 requests/minute, 1500/day
→ Reduce `ARTICLES_PER_RUN` or add delay between runs

### GitHub Actions not running?
→ Check repository Settings → Actions → General → "Allow all actions"
→ Verify all 8 secrets are added (Settings → Secrets)

### Articles publishing in English?
→ Check your Gemini prompt in `content_generator.py`
→ The prompt explicitly requests Telugu - try re-running

### Duplicate articles?
→ The 45-day cooldown in `duplicate_checker.py` prevents this
→ View `data/posted_topics.json` to see tracked topics

---

## 📊 Monitoring

View run history: **GitHub → Actions → Auto Publish**

Each run shows:
- How many articles were published
- Which topics were used
- Any errors

---

## 🔒 Security Notes

- ✅ `client_secret*.json` is gitignored - never committed
- ✅ `.env` is gitignored - never committed
- ✅ `token.json` is gitignored - never committed
- ✅ All secrets stored in GitHub Secrets
- ✅ Bot uses minimum required OAuth scopes

---

## 📞 Support

If you encounter issues, check:
1. GitHub Actions logs (Actions → Recent runs → Click run → Click job)
2. The `data/posted_topics.json` to see post history
3. Blogger dashboard to verify posts are appearing

---

*Built with ❤️ for Telugu health community | AarogyaGuruji*
