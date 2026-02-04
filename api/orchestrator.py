from fastapi import FastAPI, Header, HTTPException
from agents import AgentManager
from extractor import IntelligenceExtractor
import requests
import os
import google.generativeai as genai

# --------------------------------------------------
# App + Core Objects
# --------------------------------------------------
app = FastAPI()

agent_manager = AgentManager()
extractor = IntelligenceExtractor()

API_KEY = "YOUR_SECRET_API_KEY"
GUVI_ENDPOINT = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# --------------------------------------------------
# Gemini Setup
# --------------------------------------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-1.5-flash")


# --------------------------------------------------
# LLM REPLY GENERATOR (GEMINI ONLY)
# --------------------------------------------------
def generate_llm_reply(text, intent_output, history=None):
    prompt = f"""
You are a cautious but cooperative user.
You NEVER share OTP, PIN, UPI, passwords, or card details.
You ask clarifying questions and delay actions.

Scam context:
- Scam Category: {intent_output.get("scamCategory")}
- Risk Score: {intent_output.get("riskScore")}
- Tactics: {intent_output.get("tacticalIntents")}

Incoming message:
"{text}"

Respond naturally to keep the conversation going.
"""

    response = gemini_model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 100
        }
    )

    return response.text.strip()


# --------------------------------------------------
# FASTAPI ENDPOINT
# --------------------------------------------------
@app.post("/api/honey-pot")
async def orchestrator(data: dict, x_api_key: str = Header(None)):

    # --------------------------------------------------
    # 1. Auth
    # --------------------------------------------------
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # --------------------------------------------------
    # 2. Validate input
    # --------------------------------------------------
    try:
        text = data["message"]["text"]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input format")

    session_state = data.get("sessionState")
    session_id = (
        session_state.get("sessionId")
        if session_state
        else data.get("sessionId")
    )

    # --------------------------------------------------
    # 3. Load agents
    # --------------------------------------------------
    agents = agent_manager.get_agents()

    intent_analyst = agents["intent"]
    decision_maker = agents["decision"]

    # --------------------------------------------------
    # 4. INTENT ANALYST (YOUR MODEL)
    # --------------------------------------------------
    try:
        intent_output = intent_analyst.predict(text, session_state)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Intent analyst failed: {str(e)}"
        )

    if not isinstance(intent_output, dict):
        raise HTTPException(
            status_code=500,
            detail="Intent analyst must return a dict"
        )

    # --------------------------------------------------
    # 5. DECISION MAKER (FRIEND'S MODEL – CORRECT CALL)
    # --------------------------------------------------
    try:
        decision = decision_maker.run(
            text,
            intent_output["mlPrediction"],
            intent_output["sessionState"]["sessionId"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Decision maker failed: {str(e)}"
        )

    command = decision.get("command", "ENGAGE")

    # --------------------------------------------------
    # 6. INTELLIGENCE EXTRACTION
    # --------------------------------------------------
    extracted_intel = {}

    if command == "EXTRACT":
        try:
            extracted_intel = extractor.extract(text)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Extractor failed: {str(e)}"
            )

    # --------------------------------------------------
    # 7. GEMINI REPLY (ONLY TALKING, NOT DECIDING)
    # --------------------------------------------------
    reply = None
    if command in ["ENGAGE", "EXTRACT"]:
        reply = generate_llm_reply(
            text,
            intent_output,
            data.get("conversationHistory", [])
        )

    # --------------------------------------------------
    # 8. STOP → GUVI CALLBACK
    # --------------------------------------------------
    if command == "STOP":
        try:
            requests.post(
                GUVI_ENDPOINT,
                json={
                    "sessionId": intent_output["sessionState"]["sessionId"],
                    "scamDetected": intent_output["sessionState"]["scamDetected"],
                    "totalMessagesExchanged": intent_output["sessionState"]["message_count"],
                    "extractedIntelligence": intent_output["sessionState"]["extracted"],
                    "agentNotes": " | ".join(intent_output["sessionState"]["agentNotes"])
                },
                timeout=5
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"GUVI callback failed: {str(e)}"
            )

    # --------------------------------------------------
    # 9. FINAL API RESPONSE
    # --------------------------------------------------
    return {
        "sessionId": intent_output["sessionState"]["sessionId"],
        "intent": intent_output,
        "decision": decision,
        "extractedIntelligence": extracted_intel,
        "reply": reply,
        "sessionState": intent_output["sessionState"]
    }