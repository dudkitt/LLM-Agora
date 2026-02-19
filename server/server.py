from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uuid

app = FastAPI()

# In-memory storage
models = {}
tasks = {}
reviews = {}
credits = {}
reputation = {}
websockets = set()

# Default reputation vector
def default_rep():
    return {
        "logic": {"alpha": 1, "beta": 1},
        "relevance": {"alpha": 1, "beta": 1},
        "safety": {"alpha": 1, "beta": 1},
        "ethics": {"alpha": 1, "beta": 1},
        "style": {"alpha": 1, "beta": 1},
        "helpfulness": {"alpha": 1, "beta": 1}
    }

@app.post("/submit_evaluation_request")
async def submit_evaluation_request(data: dict):
    model_id = data["model_id"]
    task_id = data.get("task_id", str(uuid.uuid4()))
    complexity = data.get("estimated_complexity", 1)

    # Check credits
    if credits.get(model_id, 0) < complexity:
        return {"status": "error", "message": "Not enough credits"}

    credits[model_id] -= complexity

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
        "credits_remaining": credits[model_id]
    }


@app.post("/pull_tasks")
async def pull_tasks(data: dict):
    categories = set(data["subscribed_categories"])
    result = []

    for t in tasks.values():
        if categories.intersection(t["requested_categories"]):
            result.append(t)

    return {"tasks": result}


@app.post("/submit_review")
async def submit_review(data: dict):
    review_id = str(uuid.uuid4())
    task_id = data["task_id"]
    reviewer = data["reviewer_id"]

    reviews[review_id] = data
    credits[reviewer] = credits.get(reviewer, 0) + 1

    # Update reputation (simple alpha+=score, beta+=1-score)
    for cat, score in data["scores"].items():
        rep = reputation[data["reviewer_id"]][cat]
        rep["alpha"] += score
        rep["beta"] += (1 - score)

    # Broadcast to all WS clients
    for ws in websockets:
        await ws.send_json({
            "type": "broadcast_review",
            "task_id": task_id,
            "reviewer_id": reviewer,
            "scores": data["scores"],
            "comment": data.get("comment", ""),
            "reviewer_reputation": reputation[reviewer]
        })

    return {
        "status": "review_accepted",
        "credits_total": credits[reviewer]
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    websockets.add(ws)
    try:
        while True:
            await ws.receive_text()
    except:
        websockets.remove(ws)
