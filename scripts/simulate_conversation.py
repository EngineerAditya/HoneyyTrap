import requests
import uuid
import sys
import json

API_URL = "http://localhost:8000/honeypot"
API_KEY = "test-api-key-123"

def main():
    print("=== Agentic Honeypot Simulation ===")
    print("You are the Scam Simulator.")
    print("Type your message (or paste from another LLM) and check the Agent's response.")
    print("The goal is to test smooth conversation flow and callback triggering.")
    print("Type 'exit' to quit.\n")
    
    session_id = f"sim-{uuid.uuid4().hex[:8]}"
    history = []
    
    print(f"Session ID: {session_id}")
    
    for i in range(1, 11): # Loop for 10 messages max
        print(f"\n[Turn {i}/10]")
        user_input = input("Scammer (You): ").strip()
        
        if user_input.lower() in ['exit', 'quit']:
            break
            
        if not user_input:
            print("Please enter a message.")
            continue
            
        # Payload
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": user_input,
                "timestamp": "2026-02-04T10:00:00Z"
            },
            "conversationHistory": history
        }
        
        headers = {
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        }
        
        try:
            print("Sending to API...")
            response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                agent_reply = data.get("reply", "")
                print(f"Agent (AI): {agent_reply}")
                
                # Update history
                history.append({"sender": "scammer", "text": user_input})
                history.append({"sender": "user", "text": agent_reply})
                
                # Check visual cues for conclusion
                if "fake_data_leaked" in agent_reply: # Just an example
                    print("[!] Agent seems to have leaked info!")
            else:
                print(f"Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"Connection Error: {e}")
            print("Is the server running? (uvicorn api.main:app --reload)")
            break
            
    print("\nSimulation Session Ended.")
    print("Check your terminal running 'uvicorn' to see if the GUVI Callback was triggered.")

if __name__ == "__main__":
    main()
