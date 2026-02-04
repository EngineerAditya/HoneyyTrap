"""
Honeypot API - Main FastAPI Application

This is the entry point for the scam detection honeypot.
The API accepts messages from suspected scammers and returns agent responses.
"""

import os
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .models import HoneypotRequest, HoneypotResponse, ErrorResponse
from .intelligence import IntelligenceExtractor, session_store
import json
from .agent.manager import AgentManager
from .agent.states import AgentState
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor


# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("HONEYPOT_API_KEY", "test-api-key-change-me")

# Initialize FastAPI app
app = FastAPI(
    title="Honeypot Scam Detection API",
    description="AI-powered honeypot for detecting scams and extracting intelligence",
    version="1.0.0"
)

# Add CORS middleware (needed for web-based testing tools)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Intelligence Extractor
extractor = IntelligenceExtractor()

# Initialize Agent Manager
agent = AgentManager()


# ============== API KEY AUTHENTICATION ==============

def verify_api_key(x_api_key: str = Header(..., description="API key for authentication")):
    """
    Validates the API key from the request header.
    Raises 401 if invalid, returns the key if valid.
    """
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return x_api_key


# ============== HEALTH CHECK ==============

@app.get("/health")
def health_check():
    """
    Simple health check endpoint.
    Use this to verify the API is running.
    """
    return {"status": "healthy", "message": "Honeypot API is running"}


# ============== MAIN HONEYPOT ENDPOINT ==============

@app.post(
    "/honeypot",
    response_model=HoneypotResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)
def process_message(
    request: HoneypotRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Main endpoint for processing scam messages.
    
    This endpoint:
    1. Receives a message from the evaluation system
    2. Validates the request format
    3. Extracts intelligence (UPI, phones, links, etc.)
    4. Analyzes links for phishing indicators
    5. (TODO) Generates agent response
    6. Returns the response
    
    Headers Required:
        x-api-key: Your API key
        Content-Type: application/json
    """
    
    # Log the incoming request (for debugging)
    print(f"\n[SESSION: {request.sessionId}] Received message from {request.message.sender}")
    print(f"[SESSION: {request.sessionId}] Message: {request.message.text}")
    print(f"[SESSION: {request.sessionId}] History length: {len(request.conversationHistory)}")
    
    # ============== INTELLIGENCE EXTRACTION ==============
    
    # Check if this is a new conversation (empty history = fresh start)
    if len(request.conversationHistory) == 0:
        print(f"[SESSION: {request.sessionId}] New conversation - clearing session data")
        session_store.clear_session(request.sessionId)
    
    # Extract intelligence from the current message
    current_intel = extractor.extract(request.message.text)
    
    # Log extracted intelligence
    if any(current_intel.get(k) for k in ["upiIds", "phoneNumbers", "phishingLinks", "bankAccounts"]):
        print(f"[SESSION: {request.sessionId}] Extracted: {extractor.get_summary(current_intel)}")
    
    # Add to session store
    session = session_store.add_intelligence(request.sessionId, current_intel)
    
    # Log aggregated session intelligence
    print(f"[SESSION: {request.sessionId}] Session scam detected: {session.scam_detected}")
    print(f"[SESSION: {request.sessionId}] Total messages: {session.message_count}")
    
    # Get aggregated intelligence for LLM context
    llm_context = session.to_llm_context()
    print(f"[SESSION: {request.sessionId}] Aggregated intelligence: {llm_context}")
    
    # ============== RESPONSE GENERATION ==============
    
    # ============== RESPONSE GENERATION ==============
    
    # Generate Agent Response
    ai_reply = agent.generate_response(request.sessionId, request.message.text)
    
    # Check for Callback Trigger
    # Trigger if:
    # 1. Scam Detected AND
    # 2. Agent decided to CONCLUDE (meaning we got what we wanted) OR
    # 3. We have critical info (Bank Account/UPI) and confidence is high
    
    session = session_store.get_session(request.sessionId)
    if session and session.scam_detected:
        # Check if we should send callback
        should_report = False
        
        # Condition A: Agent says we are done
        if session.agent_state == AgentState.CONCLUDE.value:
            should_report = True
            
        # Condition B: robust extraction fallback
        elif len(session.bank_accounts) > 0 or len(session.upi_ids) > 0:
             # We have money mule info, report it!
             should_report = True
             
        if should_report:
            # Run callback in background to not block response
            # Using a simple thread pool for now or just calling it if it's fast. 
            # Requests is blocking, better to be safe.
            # For simplicity in this sync API, we'll just call it.
            try:
                send_callback(request.sessionId)
            except Exception as e:
                print(f"Callback Error: {e}")

    return HoneypotResponse(
        status="success",
        reply=ai_reply
    )

def send_callback(session_id: str):
    """Sends the final result to GUVI endpoint."""
    payload = session_store.get_final_payload(session_id, agent_notes="Auto-generated by Agentic Honeypot")
    
    print("\n" + "="*50)
    print(" [CALLBACK TRIGGERED] FINAL PAYLOAD ")
    print("="*50)
    print(json.dumps(payload, indent=2))
    print("="*50 + "\n")
    
    url = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    try:
        resp = requests.post(url, json=payload, timeout=5)
        print(f"[CALLBACK] Response: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"[CALLBACK] Failed: {e}")



# ============== RUN SERVER ==============

if __name__ == "__main__":
    import uvicorn
    # Run on port 8000, accessible from all network interfaces
    uvicorn.run(app, host="0.0.0.0", port=8000)
