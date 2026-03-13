"""
app.py — Web Chat Lead Manager
FastAPI application: chat endpoints + dashboard server
"""

import os
import shutil
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import init_db, get_all_leads, get_lead_stats, update_lead, insert_lead, insert_chat_message, get_chat_history
from handlers.channel_w import handle_channel_w
from ollama_coordinator import classify_pending_leads, generate_chat_reply

load_dotenv()

REFERENCES_DIR = "references"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    os.makedirs(REFERENCES_DIR, exist_ok=True)
    print("Web Chat Lead Manager started.")
    yield


app = FastAPI(title="Web Chat Lead Manager", lifespan=lifespan)

# CORS — allow requests from pauanalytics.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.pauanalytics.com",
        "https://pauanalytics.com",
        "http://localhost",
        "http://127.0.0.1",
        "null",  # local file:// testing
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ─── Chat Endpoints ───────────────────────────────────────────────────────────

@app.post("/chat/start")
async def chat_start(request: Request, background_tasks: BackgroundTasks):
    """
    Called when a visitor submits their name + challenge.
    Sources: CH-A (landing page), CH-B (blog), CH-W (chat widget).
    Creates a lead record, fires Gmail alert, returns first LLM reply.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    name = (body.get("name") or "").strip() or "Not provided"
    challenge = (body.get("challenge") or "").strip()
    source = (body.get("source") or "CH-W").upper()
    slug = (body.get("slug") or "").strip()
    phone = (body.get("phone") or "").strip()
    page = (body.get("page") or "").strip()

    if not challenge:
        raise HTTPException(status_code=400, detail="Challenge is required")

    # Log lead
    lead_id = insert_lead(
        name=name,
        whatsapp=phone if phone else "via-web",
        challenge=challenge,
        source=source,
        blog_slug=slug,
        status="New"
    )

    # Run channel_w handler (Gmail alert)
    background_tasks.add_task(handle_channel_w, lead_id, name, challenge, source, slug, phone)

    # Run Ollama classification in background
    background_tasks.add_task(classify_pending_leads)

    # Generate first chat reply
    reply = generate_chat_reply(
        lead_id=lead_id,
        user_message=challenge,
        name=name,
        history=[]
    )

    # Store exchange in chat history
    insert_chat_message(lead_id, "user", challenge)
    insert_chat_message(lead_id, "assistant", reply)

    return JSONResponse({
        "lead_id": lead_id,
        "reply": reply
    })


@app.post("/chat/message")
async def chat_message(request: Request):
    """
    Called for every follow-up message in an ongoing chat session.
    Returns Ollama-generated reply in context of full conversation history.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    lead_id = body.get("lead_id")
    message = (body.get("message") or "").strip()

    if not lead_id or not message:
        raise HTTPException(status_code=400, detail="lead_id and message are required")

    # Fetch conversation history from database
    history = get_chat_history(lead_id)

    # Generate reply
    reply = generate_chat_reply(
        lead_id=lead_id,
        user_message=message,
        name=None,
        history=history
    )

    # Store exchange
    insert_chat_message(lead_id, "user", message)
    insert_chat_message(lead_id, "assistant", reply)

    return JSONResponse({"reply": reply})


# ─── Dashboard ───────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    leads = get_all_leads()
    stats = get_lead_stats()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "leads": leads,
        "stats": stats
    })


# ─── API Endpoints ────────────────────────────────────────────────────────────

@app.get("/api/leads")
async def api_get_leads():
    return get_all_leads()


@app.get("/api/stats")
async def api_get_stats():
    return get_lead_stats()


@app.patch("/api/leads/{lead_id}")
async def api_update_lead(lead_id: int, request: Request):
    data = await request.json()
    allowed = {"status", "notes", "name", "challenge"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    update_lead(lead_id, **updates)
    return {"status": "updated", "lead_id": lead_id}


@app.post("/api/upload")
async def api_upload_file(file: UploadFile = File(...)):
    filename = file.filename.replace(" ", "-").lower()
    dest = os.path.join(REFERENCES_DIR, filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"status": "uploaded", "filename": filename}


# ─── Background Jobs ─────────────────────────────────────────────────────────

@app.post("/jobs/ollama-classify")
async def job_ollama_classify(background_tasks: BackgroundTasks):
    background_tasks.add_task(classify_pending_leads)
    return {"status": "classification started"}


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "app": "Web Chat Lead Manager"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
