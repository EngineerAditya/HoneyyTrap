
import json
from api.intelligence.session_store import SessionStore, SessionIntelligence

def check_format():
    store = SessionStore()
    session_id = "test-session-123"
    
    # Simulate a session
    store.add_intelligence(session_id, {
        "bankAccounts": ["1234567890"],
        "upiIds": ["scammer@okicici"],
        "phishingLinks": ["http://fake.com"],
        "phoneNumbers": ["+919876543210"],
        "suspiciousKeywords": ["urgent", "verify"]
    })
    
    # Get payload
    payload = store.get_final_payload(session_id, agent_notes="Test notes")
    
    print(json.dumps(payload, indent=2))
    
    # Validate Keys
    required_keys = {"sessionId", "scamDetected", "totalMessagesExchanged", "extractedIntelligence", "agentNotes"}
    payload_keys = set(payload.keys())
    
    missing = required_keys - payload_keys
    if missing:
        print(f"FAILED: Missing top-level keys: {missing}")
    else:
        print("SUCCESS: Top-level keys match.")
        
    # Validate Extracted Intelligence Keys
    intel_keys = {"bankAccounts", "upiIds", "phishingLinks", "phoneNumbers", "suspiciousKeywords"}
    extracted_keys = set(payload["extractedIntelligence"].keys())
    
    missing_intel = intel_keys - extracted_keys
    if missing_intel:
         print(f"FAILED: Missing extractedIntelligence keys: {missing_intel}")
    else:
         print("SUCCESS: ExtractedIntelligence keys match.")

if __name__ == "__main__":
    check_format()
