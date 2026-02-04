from enum import Enum
from typing import Optional, List, Dict
from dataclasses import dataclass

# Import ScanIntent from classifier (we assume it will be available)
# If circular import becomes an issue, we can redefine or import purely for typing
# For now, we'll use string matching for intents to keep modules loosely coupled
# or import at method level.

class AgentState(str, Enum):
    INITIAL_CONTACT = "INITIAL_CONTACT"
    ESTABLISH_TRUST = "ESTABLISH_TRUST"
    EXTRACTION_UPI = "EXTRACTION_UPI"
    EXTRACTION_BANK = "EXTRACTION_BANK"
    EXTRACTION_LINK = "EXTRACTION_LINK"
    PUSHBACK_HANDLING = "PUSHBACK_HANDLING"
    LEAK_FAKE_INFO = "LEAK_FAKE_INFO"
    CONCLUDE = "CONCLUDE"

class StateMachine:
    """
    Manages the transitions between states based on:
    1. Current State
    2. Scammer's Intent (from Classifier)
    3. Extraction Status (what intel we already have)
    """
    
    def __init__(self):
        # Order of extraction goals
        self.extraction_priority = [
            ("upiIds", AgentState.EXTRACTION_UPI),
            # ("phishingLinks", AgentState.EXTRACTION_LINK), # Links often come first/naturally
            ("bankAccounts", AgentState.EXTRACTION_BANK),
        ]

    def get_next_state(self, current_state: AgentState, intent: str, extracted_intel: Dict[str, List]) -> AgentState:
        """
        Determines the next state.
        
        Args:
            current_state: Where we are now.
            intent: "request_info", "provide_info", "refusal", "pushback", "chit_chat"
            extracted_intel: dict of what we found {"upiIds": [], "bankAccounts": []}
        """
        
        # --- PHASE 1: INITIALIZATION ---
        if current_state == AgentState.INITIAL_CONTACT:
            # If they immediately provide info/link, jump to extraction or trust
            if intent == "provide_info":
                 return self._get_next_extraction_goal(extracted_intel)
            return AgentState.ESTABLISH_TRUST

        # --- PHASE 2: HANDLING REFUSALS ---
        if intent in ["refusal", "pushback"]:
            if current_state in [AgentState.PUSHBACK_HANDLING, AgentState.LEAK_FAKE_INFO]:
                # If already handling pushback and they still refuse, maybe switch goal
                return self._get_next_extraction_goal(extracted_intel)
            return AgentState.PUSHBACK_HANDLING

        # --- PHASE 3: RECOVERY FROM PUSHBACK ---
        if current_state == AgentState.PUSHBACK_HANDLING:
            # After apologizing, try to leak info to rebuild trust, or go back to extraction
            return AgentState.LEAK_FAKE_INFO

        if current_state == AgentState.LEAK_FAKE_INFO:
            return self._get_next_extraction_goal(extracted_intel)

        # --- PHASE 4: NORMAL FLOW ---
        
        # If we successfully extracted something in the current state (or intended to), move on
        if current_state == AgentState.EXTRACTION_UPI and extracted_intel.get("upiIds"):
            return self._get_next_extraction_goal(extracted_intel)
            
        if current_state == AgentState.EXTRACTION_BANK and extracted_intel.get("bankAccounts"):
             return self._get_next_extraction_goal(extracted_intel)

        # If we are just chatting, move to extraction
        if current_state == AgentState.ESTABLISH_TRUST:
            return self._get_next_extraction_goal(extracted_intel)

        # Default: Stay in current state (e.g. if we are in EXTRACTION_UPI and haven't got it yet)
        # But apply Puppeteer Rule: Don't ask more than twice? 
        # (For simplicity here, we rely on the Manager/LLM to vary the text, 
        # but we stay in the state until we get it or get pushed back)
        return current_state

    def _get_next_extraction_goal(self, intel: Dict) -> AgentState:
        """Finds the next missing piece of intel."""
        if not intel.get("upiIds"):
            return AgentState.EXTRACTION_UPI
        
        # We handle links flexibly - usually they send them early.
        # If we want to explicitly ask:
        if not intel.get("phishingLinks"):
             return AgentState.EXTRACTION_LINK
            
        if not intel.get("bankAccounts"):
            return AgentState.EXTRACTION_BANK
            
        # If we have everything (or at least UPI and Bank), we can conclude or just chat
        return AgentState.CONCLUDE
