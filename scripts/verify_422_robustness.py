
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv("/home/aditya/HoneyyTrap/api/.env")

API_URL = "http://localhost:8000/honeypot"
API_KEY = os.getenv("HONEYPOT_API_KEY", "test-api-key-change-me")

def test_payload(name, payload, expected_status=422):
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=2)
        print(f"[{name}] Status: {response.status_code}")
        if response.status_code == expected_status:
            print("   ✅ Passed (Got expected error/success)")
        else:
            print(f"   ❌ FAILED! Expected {expected_status}, got {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"[{name}] ❌ Exception: {e}")

def run_tests():
    print("--- Starting 422 Robustness Checks ---")
    
    # 1. Valid Request (Control)
    test_payload("Valid Request", {
        "sessionId": "test-1",
        "message": {"sender": "scammer", "text": "hi"}
    }, expected_status=200)

    # 2. Missing Required Field (sessionId)
    test_payload("Missing sessionId", {
        "message": {"sender": "scammer", "text": "hi"}
    }, expected_status=422)

    # 3. Missing Required Field (message)
    test_payload("Missing message", {
        "sessionId": "test-2"
    }, expected_status=422)

    # 4. Null conversationHistory (Potentially Dangerous)
    # The model defines it as List[Message] = []. Explicit null might fail.
    test_payload("Explicit Null History", {
        "sessionId": "test-3",
        "message": {"sender": "scammer", "text": "hi"},
        "conversationHistory": None
    }, expected_status=422) 
    # NOTE: Pydantic might default this to None if Optional, but it is NOT Optional in the model, just has a default. 
    # If this returns 422, it is strictly correct but maybe annoying for some clients.

    # 5. Wrong Type in History (Dict instead of List)
    test_payload("Wrong Type History", {
        "sessionId": "test-4",
        "message": {"sender": "scammer", "text": "hi"},
        "conversationHistory": {"sender": "user", "text": "oops"} 
    }, expected_status=422)

    # 6. Malformed Message (Missing text)
    test_payload("Malformed Message Object", {
        "sessionId": "test-5",
        "message": {"sender": "scammer"} # missing text
    }, expected_status=422)

if __name__ == "__main__":
    run_tests()
