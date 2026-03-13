"""
utils.py — Shared utility functions
Web Chat Lead Manager
Replaces Telegram alert with Gmail (Google Workspace) alert.
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def send_email_alert(subject: str, html_body: str) -> bool:
    """
    Send an HTML email alert to yourself via Gmail SMTP.
    Uses SSL on port 465 — requires a Gmail App Password (not your login password).

    To generate an App Password:
    Google Account → Security → 2-Step Verification → App Passwords
    """
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("[Gmail] GMAIL_USER or GMAIL_APP_PASSWORD not set — skipping alert.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_USER
        msg["To"] = GMAIL_USER  # sends to yourself
        msg.attach(MIMEText(html_body, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())

        print(f"[Gmail] Alert sent: {subject}")
        return True

    except Exception as e:
        print(f"[Gmail] Failed to send alert: {e}")
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
            View dashboard: <a href="https://web-chat-lead-manager.railway.app">Lead Dashboard</a>
        </p>
    </div>
    """
