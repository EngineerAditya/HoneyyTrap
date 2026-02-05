
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
        print(f"\n[SENDING] {text}")
        response = requests.post(API_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[REPLY] {data['reply']}")
            return data['reply']
        else:
            print(f"[ERROR] Status: {response.status_code}, Body: {response.text}")
            return None
    except Exception as e:
        print(f"[EXCEPTION] {e}")
        return None

def run_simulation():
    session_id = "sim-session-" + str(int(time.time()))
    history = []
    
    # Scene 1: Initial Scam Attempt
    scammer_msg = "Your SBI account is blocked. Update KYC immediately or account will be suspended. Click: http://bit.ly/fake-bank"
    reply = send_message(session_id, scammer_msg, history)
    
    if reply:
        history.append({"sender": "scammer", "text": scammer_msg, "timestamp": "..."})
        history.append({"sender": "user", "text": reply, "timestamp": "..."})
        
    # Scene 2: Follow up
    time.sleep(1)
    scammer_msg = "Yes verify fast. Send your UPI ID."
    reply = send_message(session_id, scammer_msg, history)
    
    if reply:
        history.append({"sender": "scammer", "text": scammer_msg, "timestamp": "..."})
        history.append({"sender": "user", "text": reply, "timestamp": "..."})

    # Scene 3: Try to get info
    time.sleep(1)
    scammer_msg = "Download AnyDesk app and share code."
    reply = send_message(session_id, scammer_msg, history)

if __name__ == "__main__":
    print("Starting Simulation...")
    # Wait a bit for server to start if running via script runner (not handled here)
    run_simulation()
