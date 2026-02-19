from typing import Dict, Any

# Beta distribution for reputation
class BetaDistribution:
    def __init__(self, alpha: float = 1.0, beta: float = 1.0):
        self.alpha = alpha
        self.beta = beta

    def to_dict(self) -> Dict[str, float]:
        return {"alpha": self.alpha, "beta": self.beta}


# Multidimensional reputation vector
class ReputationVector:
    def __init__(self):
        self.logic = BetaDistribution()
        self.relevance = BetaDistribution()
        self.safety = BetaDistribution()
        self.ethics = BetaDistribution()
        self.style = BetaDistribution()
        self.helpfulness = BetaDistribution()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "logic": self.logic.to_dict(),
            "relevance": self.relevance.to_dict(),
            "safety": self.safety.to_dict(),
            "ethics": self.ethics.to_dict(),
            "style": self.style.to_dict(),
            "helpfulness": self.helpfulness.to_dict()
        }


# Model (LLM agent)
class Model:
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.credits = 10
        self.reputation = ReputationVector()

    def to_dict(self):
        return {
            "model_id": self.model_id,
            "credits": self.credits,
            "reputation": self.reputation.to_dict()
        }
