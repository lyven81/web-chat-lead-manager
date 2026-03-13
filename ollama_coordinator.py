"""
ollama_coordinator.py — Ollama Lead Intelligence Coordinator
Web Chat Lead Manager

Two functions:
  classify_pending_leads() — background task: scores + categorises new leads
  generate_chat_reply()    — real-time: returns Jason's next chat message
"""

import json
import sqlite3
from datetime import datetime

import requests

# ── Configuration ──────────────────────────────────────────────────────────────

DB_PATH = "leads.db"
OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
OLLAMA_MODEL = "llama3:latest"
APP_BASE_URL = "http://localhost:8000"

# ── Jason System Prompt ────────────────────────────────────────────────────────

JASON_SYSTEM_PROMPT = """You are Jason, the AI assistant for Pau Analytics — a data analytics consulting firm in Malaysia that helps F&B, retail, and e-commerce SME owners make sense of their business data.

Your job is to have a warm, helpful conversation with business owners who want to know more about what Pau Analytics can do for them. You are the first point of contact — a friendly face, not a salesperson.

## Who you are
- You speak like a smart, trustworthy friend who knows data — not like a consultant trying to impress anyone.
- You are warm, direct, and plain-spoken. You never use jargon.
- You genuinely care whether the visitor's business grows.

## Language rules
- Always match the visitor's language exactly — if they write in English, reply in English; Bahasa Malaysia in BM; Mandarin (简体中文) in Mandarin.
- Use short sentences. One idea per sentence.
- Never say: leverage, synergies, actionable insights, end-to-end, holistic, algorithm, ML, AI, cohort, KPI, metrics, deliverables.
- Always say: your numbers, find out, make sense of your data, stop guessing, clear answers, results.

## What you can and cannot do
- You can: listen to their business problem, ask a follow-up question to understand it better, explain briefly how Pau Analytics works, invite them to book a free chat.
- You cannot: quote prices, make promises about specific results, commit to a timeline, or represent that you are a human.
- If asked for prices, say something like: "That depends on what you need — but the easiest thing is to have a quick chat so we can give you a proper number. No commitment needed."

## Conversation flow
1. First reply: acknowledge what they shared, show you understood it, ask one follow-up question.
2. Second reply: respond to their answer, give them a brief sense of how we could help (no jargon, keep it practical), invite them to book a free 20-minute call.
3. Third reply onwards: if they haven't booked yet, keep it warm and simple. Gently suggest a call. Do not repeat the same invitation word-for-word.
4. Never push hard. If they go quiet or seem unsure, make it easy for them: "No rush — happy to answer more questions here too."

## Booking CTA (use from reply 2 onwards)
"If you'd like to talk through your numbers properly, you can book a free 20-minute call here: https://tidycal.com/pauanalytics/discovery"

## Important
- Keep replies short: 2–4 sentences maximum. This is a chat window, not an email.
- Never mention that you are built on any specific AI model.
- Never say you are "just an AI" in a way that dismisses the visitor. You are here to help.
"""

# ── Database ───────────────────────────────────────────────────────────────────

def get_pending_leads():
    """Return all New leads not yet classified by Ollama."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT * FROM leads
        WHERE status IN ('Qualified', 'New')
        AND (notes IS NULL OR notes = '' OR notes NOT LIKE '[AUTO]%')
        ORDER BY id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Ollama ─────────────────────────────────────────────────────────────────────

def is_ollama_available():
    """Return True if the Ollama server is reachable."""
    try:
        resp = requests.get("http://localhost:11434", timeout=3)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def classify_lead_with_ollama(lead: dict) -> dict | None:
    """
    Score and categorise a lead's challenge.
    Returns dict with keys: category, score, opener.
    Returns None if challenge is empty or API call fails.
    """
    challenge = (lead.get("challenge") or "").strip()
    source = lead.get("source", "")
    blog_slug = lead.get("blog_slug", "")

    if not challenge or challenge.lower() == "unknown":
        return None

    blog_context = (
        f"They came to us after reading our blog post: '{blog_slug}'."
        if blog_slug else ""
    )

    prompt = f"""You are a lead intelligence assistant for Pau Analytics, a data analytics consulting firm in Malaysia that helps SME business owners in F&B and retail make sense of their business data.

A lead has shared this business challenge:
"{challenge}"

Source: {source}. {blog_context}

Respond in JSON format only — no explanation, no markdown:
{{
  "category": "one of: Stock/Inventory | Sales Drop | Marketing Spend | Customer Loss | Pricing | Operations | General",
  "score": <integer 1 to 5>,
  "opener": "a warm, direct 1-2 sentence WhatsApp opening message written in the SAME language as the challenge above"
}}

Scoring guide:
5 = Very specific — mentions numbers, timeframe, or a concrete situation
4 = Specific problem with clear context, no numbers
3 = Clear problem but vague
2 = Somewhat vague, needs more context
1 = Too generic to act on (e.g. "I want to grow my business")

Opener rules:
- Reference what they specifically said — do not use a generic template
- Sound like a real person following up, not a sales script
- Match the language of the challenge exactly (English, Bahasa Malaysia, or Mandarin)
- Do NOT mention Pau Analytics or data analytics by name"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()

        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end == 0:
            print(f"[Ollama] No JSON found for lead {lead['id']}")
            return None

        return json.loads(content[start:end])

    except json.JSONDecodeError as e:
        print(f"[Ollama] JSON parse error for lead {lead['id']}: {e}")
        return None
    except requests.RequestException as e:
        print(f"[Ollama] Request error for lead {lead['id']}: {e}")
        return None


def generate_chat_reply(lead_id: int, user_message: str, name: str | None, history: list) -> str:
    """
    Generate Jason's next reply in a live chat session.

    lead_id      — used for logging only
    user_message — the visitor's latest message
    name         — visitor's name (used on first turn; None for follow-up turns)
    history      — list of {role, content} dicts from get_chat_history()

    Returns the reply string. Falls back to a static message if Ollama is unavailable.
    """
    if not is_ollama_available():
        return (
            "Thanks for reaching out! Our team will get back to you shortly. "
            "You can also book a free call at https://tidycal.com/pauanalytics/discovery"
        )

    messages = [{"role": "system", "content": JASON_SYSTEM_PROMPT}]

    # On first turn, prepend visitor name context
    if name and not history:
        messages.append({
            "role": "system",
            "content": f"The visitor's name is {name}. Greet them by name naturally in your first reply."
        })

    # Add conversation history
    messages.extend(history)

    # Add current message
    messages.append({"role": "user", "content": user_message})

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"].strip()
        print(f"[Jason] Reply generated for lead {lead_id} ({len(reply)} chars)")
        return reply

    except requests.RequestException as e:
        print(f"[Jason] Ollama request failed for lead {lead_id}: {e}")
        return (
            "Sorry, I'm having a moment. You can reach us directly at "
            "https://tidycal.com/pauanalytics/discovery or WhatsApp +6014-920 7099."
        )


# ── App API ────────────────────────────────────────────────────────────────────

def write_classification_to_lead(lead_id: int, result: dict) -> bool:
    """Write Ollama classification to the lead's notes via PATCH endpoint."""
    score = result.get("score", "?")
    category = result.get("category", "Unknown")
    opener = result.get("opener", "")

    notes = (
        f"[AUTO] Category: {category} | Score: {score}/5\n"
        f"Opener: \"{opener}\""
    )

    try:
        resp = requests.patch(
            f"{APP_BASE_URL}/api/leads/{lead_id}",
            json={"notes": notes},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"[Coordinator] Failed to update lead {lead_id}: {e}")
        return False


# ── Main ───────────────────────────────────────────────────────────────────────

def classify_pending_leads():
    """
    Classify all pending leads with Ollama and write results to notes.
    Called as a background task from app.py.
    """
    if not is_ollama_available():
        print("[Coordinator] Ollama is not running — skipping classification.")
        return

    pending = get_pending_leads()
    if not pending:
        print("[Coordinator] No pending leads to classify.")
        return

    print(f"[Coordinator] {len(pending)} lead(s) to classify.")

    for lead in pending:
        print(f"[Coordinator] Processing lead {lead['id']} — {lead.get('name', 'Unknown')}")
        result = classify_lead_with_ollama(lead)
        if result:
            success = write_classification_to_lead(lead["id"], result)
            if success:
                print(
                    f"[Coordinator] Lead {lead['id']} done — "
                    f"{result.get('category')} | Score: {result.get('score')}/5"
                )


if __name__ == "__main__":
    print(f"[Coordinator] Manual run — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    classify_pending_leads()
