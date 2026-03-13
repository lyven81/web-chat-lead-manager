# Web Chat Lead Manager — User Guide
**Version:** 1.0
**Date:** March 2026
**Replaces:** marketing-lead-user-guide.md (WhatsApp/Telegram system)

---

## Overview

The Web Chat Lead Manager captures visitor inquiries from your website and blog in real time. Jason — your AI assistant — chats with visitors directly in the browser, collects their name and business challenge, and alerts you by email. You follow up personally via WhatsApp at your convenience.

---

## How a Lead Enters the System

1. **Visitor lands** on a blog post, landing page, or the main website
2. **They fill in the form** (name + business challenge) or start chatting via the widget
3. **Jason replies instantly** — a warm, personalised response in the visitor's language
4. **You get a Gmail alert** with the lead's name, challenge, source, and phone (if provided)
5. **The lead appears** on your dashboard at your Railway URL
6. **Ollama classifies** the lead in the background: category, urgency score 1–5, suggested opener

---

## Your Gmail Alert

When a new lead arrives, you receive an email that includes:
- Lead name and phone number (if provided)
- Their business challenge (verbatim)
- Source channel (Landing Page / Blog — post name / Chat Widget)
- Date and time
- AI classification: category, urgency score, suggested WhatsApp opener

**Set up Gmail push notifications on your phone** so you see this in real time.

---

## Your Dashboard

Access your lead dashboard at your Railway URL (e.g. `https://web-chat-lead-manager.railway.app`).

### What you can do on the dashboard
- See all leads sorted by most recent
- Search by name or challenge keyword
- Filter by source (CH-A / CH-B / CH-W) or status
- Update lead status: New → Qualifying → Qualified → Follow-up sent → Closed / Lost
- Add notes to any lead
- Export leads to CSV

### Lead statuses explained
| Status | When to use |
|---|---|
| **New** | Just arrived — not yet reviewed |
| **Qualifying** | You've read it, deciding whether to follow up |
| **Qualified** | Good fit — schedule a follow-up call |
| **Follow-up sent** | WhatsApp message sent or call booked |
| **Closed** | Became a paying client |
| **Lost** | Not a fit or stopped responding |

---

## Following Up

All follow-ups are done manually via WhatsApp (+6014-920 7099). The AI does not send WhatsApp messages.

**How to use the AI-suggested opener:**
1. Open the Gmail alert for the lead
2. Copy the "Suggested opener" line from the AI Classification section
3. Paste into WhatsApp and personalise if needed
4. Send within 24 hours for best results

---

## Lead Sources

### CH-A — Google Ad (Landing Page)
- Phone number is collected on the form
- Follow up via WhatsApp directly
- Best for time-sensitive inquiries

### CH-B — Blog Post
- No phone number — contact is via web only
- Lead name + challenge available
- Suggest a free call in your WhatsApp if you find their contact elsewhere, or wait for them to reach out again

### CH-W — Chat Widget
- Visitor interacted directly with Jason on the website
- Full conversation history stored in the database
- They may book a call via the booking link Jason shares

---

## What Jason Does (and Doesn't Do)

**Jason will:**
- Greet the visitor by name
- Acknowledge their specific business challenge
- Ask one follow-up question to understand the problem better
- Briefly explain how Pau Analytics could help
- Invite them to book a free 20-minute call (tidycal.com/pauanalytics/discovery)
- Reply in English, Bahasa Malaysia, or Mandarin — matching the visitor's language

**Jason will not:**
- Quote prices
- Promise specific results
- Claim to be human
- Keep pushing if the visitor goes quiet

---

## Routine Maintenance

| Task | Frequency | How |
|---|---|---|
| Review Gmail alerts | Daily | Check Gmail on phone |
| Update lead statuses | Daily | Dashboard |
| Export CSV backup | Weekly | Dashboard → Export CSV |
| Check Ollama is running | If replies stop working | Open terminal: `ollama list` |
| Restart backend if needed | If dashboard is down | Railway dashboard → Restart |

---

## First-Time Setup Checklist

- [ ] Generate Gmail App Password and add to Railway environment variables
- [ ] Confirm Ollama is running: `curl http://localhost:11434` should return 200
- [ ] Deploy backend to Railway
- [ ] Update `backendUrl` in `chatbot-config.js` to your Railway URL
- [ ] Test the chat widget on the website
- [ ] Test the landing page form submission
- [ ] Test the blog CTA form on one blog post
- [ ] Confirm Gmail alert arrives
- [ ] Confirm lead appears on dashboard

---

## Troubleshooting

| Problem | Check |
|---|---|
| No Gmail alert | GMAIL_USER and GMAIL_APP_PASSWORD set in Railway? Gmail App Password still valid? |
| Chat widget not responding | `backendUrl` in chatbot-config.js correct? Backend deployed and running? |
| Ollama classification not running | Is Ollama running on the server? (not available on Railway free tier — runs on local machine only) |
| Dashboard shows 0 leads | Backend running? SQLite database initialised? Try visiting /health endpoint |
| Jason gives generic reply | Ollama not reachable — fallback message shown. Check Ollama is running |
