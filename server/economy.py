from .models import Model

def update_reputation(model: Model, scores: dict):
    """
    Update Beta distributions for each category.
    score ∈ [0,1]
    alpha += score
    beta  += (1 - score)
    """
    for category, score in scores.items():
        rep = getattr(model.reputation, category, None)
        if rep:
            rep.alpha += score
            rep.beta += (1 - score)
