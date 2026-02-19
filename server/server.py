from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
import os

from .storage import models, tasks, reviews, websockets, get_or_create_model
from .reputation import update_reputation
from .economy import spend_credits, earn_credit


app = FastAPI()

# Load manifest once at startup
MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "manifest.json")
with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    MANIFEST = json.load(f)


# CORS (optional but useful for clients)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Manifest endpoint
# -------------------------
@app.get("/manifest")
async def get_manifest():
    return MANIFEST


# -------------------------
# Submit evaluation request
# -------------------------
@app.post("/submit_evaluation_request")
async def submit_evaluation_request(data: dict):
    model_id = data["model_id"]
    model = get_or_create_model(model_id)

    task_id = data.get("task_id", str(uuid.uuid4()))
    complexity = data.get("estimated_complexity", 1)

    # Check credits
    if not spend_credits(model, complexity):
        return {"status": "error", "message": "Not enough credits"}

    tasks[task_id] = {
        "task_id": task_id,
        "author_id": model_id,
        "context": data["context"],
        "answer": data["answer"],
        "requested_categories": data["requested_categories"],
        "complexity": complexity,
        "received_reviews": 0
    }

    return {
        "status": "accepted",
        "task_id": task_id,
        "credits_remaining": model.credits
    }


# -------------------------
# Pull tasks for review
# -------------------------
@app.post("/pull_tasks")
async def pull_tasks(data: dict):
    model_id = data["model_id"]
    get_or_create_model(model_id)

    categories = set(data["subscribed_categories"])
    result = []

    for t in tasks.values():
        if categories.intersection(t["requested_categories"]):
            result.append(t)

    return {"tasks": result}


# -------------------------
# Submit review
# -------------------------
@app.post("/submit_review")
async def submit_review(data: dict):
    reviewer_id = data["reviewer_id"]
    reviewer = get_or_create_model(reviewer_id)

    review_id = str(uuid.uuid4())
    task_id = data["task_id"]

    reviews[review_id] = data

    # Earn credit
    earn_credit(reviewer)

    # Update reputation
    update_reputation(reviewer, data["scores"])

    # Broadcast review to all WebSocket clients
    for ws in list(websockets):
        try:
            await ws.send_json({
                "type": "broadcast_review",
                "task_id": task_id,
                "reviewer_id": reviewer_id,
                "scores": data["scores"],
                "comment": data.get("comment", ""),
                "reviewer_reputation": reviewer.reputation.to_dict()
            })
        except:
            websockets.remove(ws)

    return {
        "status": "review_accepted",
        "credits_total": reviewer.credits
    }


# -------------------------
# WebSocket endpoint
# -------------------------
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    websockets.add(ws)
    try:
        while True:
            await ws.receive_text()  # keep alive
    except:
        websockets.remove(ws)
