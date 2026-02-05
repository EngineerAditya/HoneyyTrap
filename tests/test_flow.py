import sys
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv(os.path.join(os.getcwd(), 'api', '.env'))

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from api.agent.manager import AgentManager
    from api.intelligence.session_store import session_store
    print("Imports successful!")
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_agent():
    print("Initializing Agent...")
    try:
        agent = AgentManager()
        print("Agent Initialized.")
    except Exception as e:
        print(f"Agent Init Failed: {e}")
        return

    session_id = "test-session-123"
    user_msg = "Your bank account is blocked. Verify KYC immediately."
    
    print(f"Sending message: {user_msg}")
    
    # We might fail if no API key, but let's see
    if not os.getenv("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY not set. Expect failure or mock behavior.")
    
    try:
        reply = agent.generate_response(session_id, user_msg)
        print(f"Agent Reply: {reply}")
        
        session = session_store.get_session(session_id)
        print(f"Session State: {session.agent_state}")
        print(f"Scam Detected: {session.scam_detected}")
        
    except Exception as e:
        print(f"Generation Failed: {e}")

if __name__ == "__main__":
    test_agent()
