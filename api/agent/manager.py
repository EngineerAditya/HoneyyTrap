import os
import logging
import google.generativeai as genai
from typing import Optional

from ..intelligence.session_store import session_store, SessionIntelligence
from ..intelligence.classifier import ScamClassifier
from .states import StateMachine, AgentState
from .prompts import SYSTEM_PROMPT_TEMPLATE, STATE_INSTRUCTIONS

# Configure Logger
logger = logging.getLogger(__name__)

class AgentManager:
    def __init__(self):
        self.state_machine = StateMachine()
        self.classifier = ScamClassifier()
        
        # Configure Gemini
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables.")
        else:
            genai.configure(api_key=self.api_key)
            
        # Model Configuration
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def generate_response(self, session_id: str, user_text: str) -> str:
        """
        Main entry point for generating a response.
        """
        session = session_store.get_or_create(session_id)
        
        # 1. Detect Intent (Session store already updates analysis when intelligence is added)
        # We assume intelligence has been added BEFORE calling this method in the main loop
        
        intel_dict = session.to_dict()
        latest_analysis = session._latest_analysis
        
        current_intent = "unknown"
        if latest_analysis and latest_analysis.intent:
            current_intent = latest_analysis.intent.value
        
        # 2. Determine Next State
        current_state = AgentState(session.agent_state)
        next_state = self.state_machine.get_next_state(
            current_state, 
            current_intent, 
            intel_dict
        )
        
        # Update Session State
        session.agent_state = next_state.value
        logger.info(f"Session {session_id} transition: {current_state} -> {next_state} (Intent: {current_intent})")
        
        # 3. Construct Prompt
        prompt = self._build_prompt(session, next_state)
        
        # 4. Call LLM
        return self._call_llm(prompt)

    def _call_llm(self, prompt: str) -> str:
        """Calls Gemini API using the SDK."""
        if not self.api_key:
            return "Error: GEMINI_API_KEY not configured."
            
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 150, # Keep replies short
                }
            )
            return response.text.strip()
                
        except Exception as e:
            logger.error(f"LLM API Error: {e}")
            return "sorry network issue... one min..." # Natural fallback

    def _build_prompt(self, session: SessionIntelligence, state: AgentState) -> str:
        """Constructs the full prompt for the LLM."""
        
        # 1. Persona and Context
        persona = {
            "name": "Rajesh Kumar", 
        }
        
        # 2. State Instructions
        state_goal = STATE_INSTRUCTIONS.get(state.value, "Engage cautiously.")
        
        # 3. Context Summary
        conversation_history = "\n".join([f"{msg['sender']}: {msg['text']}" for msg in session.messages])
        
        situation = f"""
        You are in a conversation with a suspected scammer.
        Conversation History:
        {conversation_history}
        """

        full_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            name=persona["name"],
            situation_context=situation,
            current_goal=state_goal
        )
        
        return full_prompt
