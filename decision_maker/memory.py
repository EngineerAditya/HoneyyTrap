from decision_maker.config import INITIAL_THRESHOLD, MAX_MESSAGES

session_memory = {}

def update_session_state(session_id, is_scam_detected):
    if session_id not in session_memory:
        session_memory[session_id] = {
            "msg_count": 0,
            "threshold": INITIAL_THRESHOLD,  # Starts at 5
            "command": "ENGAGE"
        }
    
    session = session_memory[session_id]
    session["msg_count"] += 1
    
    # Requirement 3: If scam detected, change to EXTRACT and add 3 to threshold
    if is_scam_detected:
        session["command"] = "EXTRACT"
        # Increase threshold but don't exceed 18
        if session["threshold"] < MAX_MESSAGES:
            session["threshold"] = min(session["threshold"] + 3, MAX_MESSAGES)
            
    return session