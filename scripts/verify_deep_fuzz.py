
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv("/home/aditya/HoneyyTrap/api/.env")

API_URL = "http://localhost:8000/honeypot"
API_KEY = os.getenv("HONEYPOT_API_KEY", "test-api-key-change-me")

def test(name, payload, should_pass=True):
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=5)
        status = resp.status_code
        print(f"[{name}] status={status}")
        
        if should_pass and status != 200:
            print(f"   ❌ FAILED (Expected 200) Body: {resp.text}")
        elif not should_pass and status != 422:
            print(f"   ❌ FAILED (Expected 422) Body: {resp.text}")
        else:
            print(f"   ✅ OK")
            
    except Exception as e:
        print(f"[{name}] Exception: {e}")

def run():
    print("--- DEEP FUZZ START ---")
    
    base = {
        "sessionId": "fuzz-1",
        "message": {"sender": "scammer", "text": "hi"}
    }
    
    # 1. Numeric Timestamp (Common failure)
    p = base.copy()
    p["message"] = {"sender": "s", "text": "t", "timestamp": 1678888888}
    test("Numeric Timestamp", p, should_pass=True)
    
    # 2. Boolean Timestamp
    p = base.copy()
    p["message"] = {"sender": "s", "text": "t", "timestamp": False}
    test("Boolean Timestamp", p, should_pass=True) # Should coerce string or fail? Ideally fail 422 if strict, but let's see.
    
    # 3. Extra Fields (Should be ignored)
    p = base.copy()
    p["extra_field"] = "should_ignore"
    test("Extra Root Fields", p, should_pass=True)
    
    p = base.copy()
    p["message"] = {"sender": "s", "text": "t", "extra": "ignore"}
    test("Extra Message Fields", p, should_pass=True)
    
    # 4. Metadata variations
    p = base.copy()
    p["metadata"] = {}
    test("Empty Metadata Dict", p, should_pass=True)
    
    p = base.copy()
    p["metadata"] = "some_string" 
    test("String Metadata (Wrong Type)", p, should_pass=False) # Should be 422
    
    # 5. Conversation History variations
    p = base.copy()
    p["conversationHistory"] = None
    test("Null History", p, should_pass=True)
    
    p = base.copy()
    p["conversationHistory"] = []
    test("Empty List History", p, should_pass=True)
    
    p = base.copy()
    p["conversationHistory"] = [{"sender": "u", "text": "h", "timestamp": None}] # Explicit null timestamp in history
    test("History with Null Timestamp", p, should_pass=True)

if __name__ == "__main__":
    run()
