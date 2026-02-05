import requests
import json
import uuid
import datetime
import sys

# Configuration
API_URL = "http://localhost:8000/honeypot"
API_KEY = "test-api-key-123"  # Matches .env

def print_separator():
    print("-" * 60)

def main():
    print_separator()
    print("Welcome to the HoneyyTrap Interactive Tester")
    print_separator()
    print(f"Target API: {API_URL}")
    print("Type 'exit' or 'quit' to stop.")
    print("Type 'reset' to start a new session.")
    print_separator()

    # Generate a random session ID
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    
    conversation_history = []

    while True:
        # Get input from user (acting as the Scammer from the other LLM)
        try:
            scammer_text = input("\n[SCAMMER/YOU]: ").strip()
        except KeyboardInterrupt:
            print("\nExiting...")
            break

        if not scammer_text:
            continue
            
        if scammer_text.lower() in ["exit", "quit"]:
            print("Exiting...")
            break
            
        if scammer_text.lower() == "reset":
            session_id = str(uuid.uuid4())
            conversation_history = []
            print(f"\n[SYSTEM] New Session Started: {session_id}")
            continue

        # Prepare payload
        timestamp = datetime.datetime.now().isoformat()
        
        current_message = {
            "sender": "scammer",
            "text": scammer_text,
            "timestamp": timestamp
        }

        payload = {
            "sessionId": session_id,
            "message": current_message,
            "conversationHistory": conversation_history,
            "metadata": {
                "channel": "CLI_TEST",
                "language": "English",
                "locale": "IN"
            }
        }

        # Send request
        try:
            headers = {
                "x-api-key": API_KEY,
                "Content-Type": "application/json"
            }
            # print(f"[DEBUG] Sending payload to {API_URL}...")
            response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                agent_reply = data.get("reply", "")
                
                print(f"\n[AGENT]: {agent_reply}")
                
                # Update history
                conversation_history.append(current_message)
                conversation_history.append({
                    "sender": "user",  # The agent acts as the 'user' (victim)
                    "text": agent_reply,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                
            else:
                print(f"\n[ERROR] API returned {response.status_code}: {response.text}")

        except requests.exceptions.ConnectionError:
            print("\n[ERROR] Could not connect to the API. Is the server running?")
            print("Run 'python -m api.main' in a separate terminal.")
        except Exception as e:
            print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    main()
