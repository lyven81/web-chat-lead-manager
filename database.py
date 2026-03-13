"""
database.py — SQLite setup and all database operations
Web Chat Lead Manager
"""

import sqlite3
from datetime import datetime

DB_PATH = "leads.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables on first run. Safe to call on every startup."""
    conn = get_conn()
    c = conn.cursor()

    # Leads table — whatsapp stores phone (CH-A) or 'via-web' (CH-B, CH-W)
    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            name        TEXT DEFAULT 'Unknown',
            whatsapp    TEXT DEFAULT 'via-web',
            challenge   TEXT DEFAULT 'Unknown',
            source      TEXT NOT NULL,
            blog_slug   TEXT DEFAULT '',
            status      TEXT DEFAULT 'New',
            notes       TEXT DEFAULT ''
        )
    """)

    # Chat sessions table — stores full conversation per lead
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id     INTEGER NOT NULL,
            role        TEXT NOT NULL,
            message     TEXT NOT NULL,
            timestamp   TEXT NOT NULL,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)

    conn.commit()
    conn.close()


# ─── Lead Operations ──────────────────────────────────────────────────────────

def insert_lead(name, whatsapp, challenge, source, blog_slug="", status="New"):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO leads (date, name, whatsapp, challenge, source, blog_slug, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M"), name, whatsapp, challenge, source, blog_slug, status))
    lead_id = c.lastrowid
    conn.commit()
    conn.close()
    return lead_id


def update_lead(lead_id, **kwargs):
    allowed = {"name", "challenge", "status", "notes"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    conn = get_conn()
    sets = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE leads SET {sets} WHERE id = ?", (*fields.values(), lead_id))
    conn.commit()
    conn.close()


def get_all_leads():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_lead_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    this_week = conn.execute("""
        SELECT COUNT(*) FROM leads
        WHERE date >= date('now', '-7 days')
    """).fetchone()[0]
    needs_followup = conn.execute("""
        SELECT COUNT(*) FROM leads WHERE status = 'New'
    """).fetchone()[0]
    ch_a = conn.execute("""
        SELECT COUNT(*) FROM leads WHERE source = 'CH-A'
        AND date >= date('now', '-7 days')
    """).fetchone()[0]
    ch_b = conn.execute("""
        SELECT COUNT(*) FROM leads WHERE source = 'CH-B'
        AND date >= date('now', '-7 days')
    """).fetchone()[0]
    ch_w = conn.execute("""
        SELECT COUNT(*) FROM leads WHERE source = 'CH-W'
        AND date >= date('now', '-7 days')
    """).fetchone()[0]
    blog_performance = conn.execute("""
        SELECT blog_slug, COUNT(*) as count FROM leads
        WHERE source = 'CH-B' AND blog_slug != ''
        GROUP BY blog_slug ORDER BY count DESC
    """).fetchall()
    conn.close()
    return {
        "total": total,
        "this_week": this_week,
        "needs_followup": needs_followup,
        "ch_a_week": ch_a,
        "ch_b_week": ch_b,
        "ch_w_week": ch_w,
        "blog_performance": [dict(r) for r in blog_performance]
    }


# ─── Chat Session Operations ──────────────────────────────────────────────────

def insert_chat_message(lead_id, role, message):
    """Store one message in the chat history."""
    conn = get_conn()
    conn.execute("""
        INSERT INTO chat_sessions (lead_id, role, message, timestamp)
        VALUES (?, ?, ?, ?)
    """, (lead_id, role, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def get_chat_history(lead_id):
    """Return conversation history as list of {role, message} dicts."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT role, message FROM chat_sessions
        WHERE lead_id = ?
        ORDER BY id ASC
    """, (lead_id,)).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["message"]} for r in rows]
