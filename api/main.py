"""
Honeypot API - Main FastAPI Application

This is the entry point for the scam detection honeypot.
The API accepts messages from suspected scammers and returns agent responses.
"""

import os
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import HoneypotRequest, HoneypotResponse, ErrorResponse
from intelligence import IntelligenceExtractor, session_store


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
    
    # TODO: Step 3 - Add AI agent response generation here
    # The llm_context can be passed to the LLM for context-aware responses
    
    # For now, return a placeholder response
    # This proves the API structure is working correctly
    placeholder_reply = "I received your message. Can you tell me more about this?"
    
    return HoneypotResponse(
        status="success",
        reply=placeholder_reply
    )



# ============== RUN SERVER ==============

if __name__ == "__main__":
    import uvicorn
    # Run on port 8000, accessible from all network interfaces
    uvicorn.run(app, host="0.0.0.0", port=8000)
