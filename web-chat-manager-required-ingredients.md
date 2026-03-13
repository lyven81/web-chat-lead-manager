# Web Chat Lead Manager — Required Ingredients
**Version:** 1.0
**Date:** March 2026
**Replaces:** marketing-lead-required-ingredients.md (WhatsApp/Telegram-based system)

---

## What This System Does

Captures leads from three web channels — Google Ad landing pages (CH-A), blog post CTAs (CH-B), and the website chat widget (CH-W) — and immediately:
1. Logs the lead to a local SQLite database
2. Sends a real-time Gmail alert to the business owner
3. Starts a live chat with the visitor using Jason (Ollama LLM)
4. Scores and categorises the lead in the background

No WhatsApp Business API. No Telegram bot. No third-party AI platform.

---

## What You Still Need

### 1. Google Workspace Gmail Account
- The system sends itself an email alert for every new lead
- Requires a **Gmail App Password** (not your login password)
- To generate: Google Account → Security → 2-Step Verification → App Passwords
- Set on phone to push notifications for instant awareness

### 2. Ollama (Running Locally)
- Already installed and running on `localhost:11434`
- Model: `llama3:latest` — confirmed installed
- Powers two functions:
  - **Lead classification** (background): scores urgency 1–5, assigns category, drafts follow-up opener
  - **Chat replies** (real-time): Jason persona, matches visitor language (EN/BM/ZH)
- No internet connection required — runs entirely on your machine

### 3. Railway (Backend Hosting)
- Free tier is sufficient for current traffic
- Deploys via GitHub push — zero manual steps after setup
- Environment variables set in Railway dashboard (GMAIL_USER, GMAIL_APP_PASSWORD)
- Auto-restarts on crash

### 4. GitHub (pinnacles-learning-website)
- Hosts the frontend: chatbot-widget.js, chatbot-config.js, blog posts, landing pages
- Single config variable `window.pauChatbotConfig.backendUrl` points all forms to the Railway backend
- Deploying a change = `git push` → GitHub Pages live in ~1 minute

---

## What You No Longer Need

| Removed | Replaced By |
|---|---|
| Meta WhatsApp Business API | Web chat widget (Jason) |
| Separate WhatsApp Business number | Existing +6014-920 7099 (manual follow-up only) |
| Telegram bot | Gmail App Password alert |
| Dify.AI (cloud LLM for chat) | Ollama local LLM |
| Google Sheet (manual lead log) | SQLite dashboard at Railway URL |
| WABA monthly subscription fee | Free (Ollama + Railway free tier) |

---

## Environment Variables

Set these in Railway before deploying:

```
GMAIL_USER=you@yourworkspace.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

Optional (if running backend locally for development):
- Copy `.env.example` to `.env` and fill in values

---

## Lead Sources Reference

| Code | Channel | Entry Point | Phone Collected? |
|---|---|---|---|
| CH-A | Google Ad | Landing page form | Yes (required) |
| CH-B | Blog post | Mini-form at end of post | No |
| CH-W | Website | Chat widget (bottom-right) | No |

---

## Backend File Structure

```
Web Chat Lead Manager/
├── app.py                  ← FastAPI app (endpoints + CORS)
├── database.py             ← SQLite schema + all DB operations
├── utils.py                ← Gmail send + HTML email builder
├── ollama_coordinator.py   ← Lead classification + Jason chat replies
├── handlers/
│   ├── __init__.py
│   └── channel_w.py        ← Gmail alert background task
├── templates/
│   └── dashboard.html      ← Lead dashboard UI
├── static/
│   └── style.css           ← Dashboard styles
├── references/             ← Ollama reference files (optional)
├── requirements.txt
├── railway.toml
└── .env.example
```

---

## Monthly Running Costs

| Item | Cost |
|---|---|
| Railway (backend hosting) | Free tier |
| Ollama (local LLM) | Free |
| Gmail alert | Free (Google Workspace already paid) |
| GitHub Pages (frontend) | Free |
| **Total** | **RM 0 / month** |
