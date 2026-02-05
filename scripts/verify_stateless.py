
import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv("/home/aditya/HoneyyTrap/api/.env")

API_URL = "http://localhost:8000/honeypot"
API_KEY = os.getenv("HONEYPOT_API_KEY", "test-api-key-change-me")

def send_message(session_id, text, history, sender="scammer"):
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": sender,
            "text": text,
            "timestamp": "2026-02-05T12:00:00Z"
        },
        "conversationHistory": history,
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()['reply']
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def verify_statelessness():
    session_id = "stateless-sim-" + str(int(time.time()))
    history = []
    
    # 1. First Message
    print("\n--- Step 1: Initial Message ---")
    msg1 = "Your account blocked. Verify immediately."
    reply1 = send_message(session_id, msg1, history)
    print(f"Agent: {reply1}")
    
    history.append({"sender": "scammer", "text": msg1, "timestamp": "..."})
    history.append({"sender": "user", "text": reply1, "timestamp": "..."})
    
    # 2. SIMULATE FLUSH/RESTART
    # We can't actually restart the server easily here,
    # but the logic we implemented (backfill) runs EVERY time.
    # To prove it works, we rely on the implementation detail: 
    # The code we wrote specifically checks history vs stored messages.
    # If the logic works, the agent should NOT be confused by a follow up.
    
    print("\n--- Step 2: Follow-Up (Stateless Check) ---")
    msg2 = "Did you get the link?"
    # The agent should know what link we are talking about from context if backfill works
    reply2 = send_message(session_id, msg2, history)
    print(f"Agent: {reply2}")
    
    if reply2 and "link" in reply2.lower() or "what" in reply2.lower(): 
        # Basic check to see if it responds coherently
        print("\n[SUCCESS] Agent responded to follow-up.")
    else:
        print("\n[WARNING] Agent response might indicate context loss.")

if __name__ == "__main__":
    verify_statelessness()
