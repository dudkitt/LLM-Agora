from typing import Dict, Any
from .models import Model

# In-memory storage
models: Dict[str, Model] = {}
tasks: Dict[str, Dict[str, Any]] = {}
reviews: Dict[str, Dict[str, Any]] = {}
websockets = set()


def get_or_create_model(model_id: str) -> Model:
    if model_id not in models:
        models[model_id] = Model(model_id)
    return models[model_id]
