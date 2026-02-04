from collections import defaultdict

# session_id -> list of predictions
conversation_state = {}


def update_type(session_id, predicted_class, confidence):
    if session_id not in conversation_state:
        conversation_state[session_id] = []

    conversation_state[session_id].append({
        "type": predicted_class,
        "conf": confidence
    })


def aggregate_type(session_id):
    votes = defaultdict(float)

    history = conversation_state.get(session_id, [])
    for item in history:
        votes[item["type"]] += item["conf"]

    if not votes:
        return "unknown", 0.0

    final_type = max(votes, key=votes.get)
    strength = votes[final_type] / sum(votes.values())

    return final_type, round(strength, 3)


def detect_shift(session_id):
    history = conversation_state.get(session_id, [])
    if len(history) < 3:
        return False

    last = history[-1]["type"]
    prev = [h["type"] for h in history[-4:-1]]

    return last not in prev