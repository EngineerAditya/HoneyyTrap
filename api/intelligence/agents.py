# api/intelligence/agents.py
import pickle
import os


class AgentManager:
    def __init__(self):
        base_path = "api/intelligence"

        # Intent Analyst (YOUR MODEL)
        self.intent_analyst = self._load(
            os.path.join(base_path, "intent_analyst.pkl")
        )

        # Decision Maker (FRIEND'S MODEL)
        self.decision_maker = self._load(
            os.path.join(base_path, "decision_maker.pkl")
        )

    def _load(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model not found at {path}")
        with open(path, "rb") as f:
            return pickle.load(f)

    def get_agents(self):
        return {
            "intent": self.intent_analyst,
            "decision": self.decision_maker
        }