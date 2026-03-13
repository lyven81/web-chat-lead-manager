"""
utils.py — Shared utility functions
Web Chat Lead Manager
Sends Gmail alerts via Resend HTTP API (Railway blocks SMTP outbound connections).
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
GMAIL_USER = os.getenv("GMAIL_USER")  # used as the "to" address


def send_email_alert(subject: str, html_body: str) -> bool:
    """
    Send an HTML email alert via Resend HTTP API.
    Resend is used because Railway blocks outbound SMTP connections.

    Setup:
      1. Sign up free at resend.com
      2. Create an API key
      3. Set RESEND_API_KEY in Railway environment variables
      4. Set GMAIL_USER to your email address (used as recipient)

    Free tier: 100 emails/day, 3,000/month — sufficient for lead alerts.
    """
    if not RESEND_API_KEY:
        print("[Email] RESEND_API_KEY not set — skipping alert.")
        return False

    to_address = GMAIL_USER or os.getenv("RESEND_TO")
    if not to_address:
        print("[Email] No recipient address set (GMAIL_USER or RESEND_TO) — skipping alert.")
        return False

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": "Pau Analytics Leads <onboarding@resend.dev>",
                "to": [to_address],
                "subject": subject,
                "html": html_body,
            },
            timeout=15,
        )

        if response.status_code in (200, 201):
            print(f"[Email] Alert sent: {subject}")
            return True
        else:
            print(f"[Email] Resend API error {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"[Email] Failed to send alert: {e}")
        return False


def build_lead_alert_html(name, challenge, source, slug, phone, timestamp, score=None, category=None, opener=None):
    """Build a clean HTML email body for a new lead alert."""
    source_label = {
        "CH-A": "Google Ad (Landing Page)",
        "CH-B": f"Blog Post — {slug}" if slug else "Blog Post",
        "CH-W": "Web Chat Widget",
    }.get(source, source)

    contact_line = f"<tr><td><b>Phone</b></td><td>{phone}</td></tr>" if phone and phone != "via-web" else ""

    ollama_section = ""
    if score and category:
        opener_html = f"<p><b>Suggested opener:</b><br><em>{opener}</em></p>" if opener else ""
        ollama_section = f"""
        <hr style="margin:20px 0; border:none; border-top:1px solid #eee;">
        <p><b>AI Classification</b></p>
        <table>
            <tr><td><b>Category</b></td><td>{category}</td></tr>
            <tr><td><b>Urgency Score</b></td><td>{score}/5</td></tr>
        </table>
        {opener_html}
        """

    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
        <h2 style="color:#403B36;border-bottom:2px solid #CBA135;padding-bottom:8px;">
            🔔 New Lead — {source_label}
        </h2>
        <table style="width:100%;border-collapse:collapse;margin-top:16px;">
            <tr><td style="padding:6px 0;color:#666;width:120px;"><b>Name</b></td><td style="padding:6px 0;">{name}</td></tr>
            {contact_line}
            <tr><td style="padding:6px 0;color:#666;"><b>Challenge</b></td><td style="padding:6px 0;">{challenge}</td></tr>
            <tr><td style="padding:6px 0;color:#666;"><b>Source</b></td><td style="padding:6px 0;">{source_label}</td></tr>
            <tr><td style="padding:6px 0;color:#666;"><b>Time</b></td><td style="padding:6px 0;">{timestamp}</td></tr>
        </table>
        {ollama_section}
        <hr style="margin:20px 0; border:none; border-top:1px solid #eee;">
        <p style="color:#888;font-size:0.85em;">
            Follow up today via WhatsApp: <a href="https://wa.me/60149207099">+6014-920 7099</a><br>
            View dashboard: <a href="https://web-chat-lead-manager-production.up.railway.app">Lead Dashboard</a>
        </p>
    </div>
    """
