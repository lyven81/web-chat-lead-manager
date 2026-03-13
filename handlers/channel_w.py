"""
handlers/channel_w.py — Web Chat lead handler
Trigger: Lead submitted via web chat widget, landing page form, or blog CTA form
Sources: CH-W (chat widget), CH-A (landing page), CH-B (blog post)
Logic: Send Gmail alert to business owner
No WhatsApp API involved. No auto-reply sent to customer — reply is returned via the API directly.
"""

from datetime import datetime
from utils import send_email_alert, build_lead_alert_html


def handle_channel_w(lead_id: int, name: str, challenge: str, source: str, slug: str, phone: str):
    """
    Called as a background task after a new web lead is created.
    Sends Gmail alert to business owner.
    Returns True if alert sent successfully.
    """
    timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")

    source_labels = {
        "CH-A": "Google Ad (Landing Page)",
        "CH-B": f"Blog — {slug}" if slug else "Blog",
        "CH-W": "Web Chat Widget",
    }
    source_label = source_labels.get(source, source)

    subject = f"🔔 New Lead — {source_label} | {name}"

    html_body = build_lead_alert_html(
        name=name,
        challenge=challenge,
        source=source,
        slug=slug,
        phone=phone,
        timestamp=timestamp
    )

    send_email_alert(subject, html_body)
    return True
