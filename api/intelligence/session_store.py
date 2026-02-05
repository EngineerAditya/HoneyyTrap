"""
Session Store - In-Memory Session Intelligence Aggregation

This module stores and aggregates extracted intelligence per session.
Clears when a new conversation starts (empty conversationHistory).

Enhanced Features:
- Dynamic confidence scoring
- Scam type classification
- Rich LLM context generation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from datetime import datetime

from .classifier import ScamClassifier, ScamAnalysis, ScamType, UrgencyLevel


@dataclass
class SessionIntelligence:
    """Aggregated intelligence for a single session."""
    session_id: str
    bank_accounts: Set[str] = field(default_factory=set)
    upi_ids: Set[str] = field(default_factory=set)
    phishing_links: Set[str] = field(default_factory=set)
    phone_numbers: Set[str] = field(default_factory=set)
    suspicious_keywords: Set[str] = field(default_factory=set)
    emails: Set[str] = field(default_factory=set)
    all_links: Set[str] = field(default_factory=set)
    link_reports: List[dict] = field(default_factory=list)  # Detailed link analysis
    message_count: int = 0
    scam_detected: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    # Conversation history for context
    messages: List[dict] = field(default_factory=list)  # [{sender, text, timestamp}]
    
    # Dynamic analysis (updated each message)
    _latest_analysis: Optional[ScamAnalysis] = field(default=None, repr=False)
    
    # Agent State (for State Machine)
    agent_state: str = "INITIAL_CONTACT"
    
    def to_dict(self) -> dict:
        """Convert to dictionary matching GUVI hackathon schema."""
        return {
            "bankAccounts": list(self.bank_accounts),
            "upiIds": list(self.upi_ids),
            "phishingLinks": list(self.phishing_links),
            "phoneNumbers": list(self.phone_numbers),
            "suspiciousKeywords": list(self.suspicious_keywords),
        }
    
    def to_llm_context(self) -> dict:
        """
        Generate rich context for LLM to understand the situation.
        
        This is the PRIMARY output for the LLM to generate responses.
        """
        # Get analysis or create default
        analysis = self._latest_analysis
        
        context = {
            # === CLASSIFICATION ===
            "scamDetected": self.scam_detected,
            "confidence": analysis.confidence if analysis else 0,
            "scamType": analysis.scam_type.value if analysis else ScamType.UNKNOWN.value,
            "urgency": analysis.urgency.value if analysis else UrgencyLevel.LOW.value,
            
            # === WHAT'S HAPPENING ===
            "tactics": {
                "impersonating": analysis.impersonating if analysis else None,
                "threats": analysis.threats if analysis else [],
                "asksFor": analysis.asks_for if analysis else [],
            },
            
            # === EXTRACTED INTEL (Simplified for LLM) ===
            "intel": {
                "upiIds": list(self.upi_ids),
                "phoneNumbers": list(self.phone_numbers),
                "bankAccounts": list(self.bank_accounts),
                "emails": list(self.emails),
                "riskyLinks": self._format_risky_links(),
            },
            
            # === SESSION META ===
            "session": {
                "messageCount": self.message_count,
                "durationSeconds": int((datetime.now() - self.created_at).total_seconds()),
            }
        }
        
        return context
    
    def _format_risky_links(self) -> List[str]:
        """Format risky links with their risk reason for LLM."""
        formatted = []
        for report in self.link_reports:
            if report.get("risk") in ("CRITICAL", "HIGH_RISK", "SUSPICIOUS"):
                reason = report.get("reasons", ["Unknown reason"])[0]
                formatted.append(f"{report['url']} ({report['risk']}: {reason})")
        return formatted
    
    def get_full_conversation_text(self) -> str:
        """Get all message texts concatenated for analysis."""
        return " ".join(msg.get("text", "") for msg in self.messages)
    
    def merge(self, intel: dict) -> None:
        """Merge extracted intelligence into this session."""
        self.bank_accounts.update(intel.get("bankAccounts", []))
        self.upi_ids.update(intel.get("upiIds", []))
        self.phishing_links.update(intel.get("phishingLinks", []))
        self.phone_numbers.update(intel.get("phoneNumbers", []))
        self.suspicious_keywords.update(intel.get("suspiciousKeywords", []))
        self.emails.update(intel.get("emails", []))
        self.all_links.update(intel.get("allLinks", []))
        
        # Merge link reports (avoid duplicates by URL)
        existing_urls = {r["url"] for r in self.link_reports}
        for report in intel.get("linkReports", []):
            if report["url"] not in existing_urls:
                self.link_reports.append(report)
                existing_urls.add(report["url"])
    
    def add_message(self, sender: str, text: str, timestamp: str) -> None:
        """Add a message to conversation history."""
        self.messages.append({
            "sender": sender,
            "text": text,
            "timestamp": timestamp
        })
    
    def update_analysis(self, classifier: 'ScamClassifier') -> ScamAnalysis:
        """Update scam analysis with current intel and messages."""
        full_text = self.get_full_conversation_text()
        intel_dict = {
            "bankAccounts": list(self.bank_accounts),
            "upiIds": list(self.upi_ids),
            "phishingLinks": list(self.phishing_links),
            "phoneNumbers": list(self.phone_numbers),
            "suspiciousKeywords": list(self.suspicious_keywords),
            "linkReports": self.link_reports,
        }
        
        self._latest_analysis = classifier.classify(full_text, intel_dict)
        
        # Update scam_detected based on confidence threshold
        if self._latest_analysis.confidence >= 30:
            self.scam_detected = True
        
        return self._latest_analysis
    
    def has_scam_indicators(self) -> bool:
        """Check if this session has any scam indicators."""
        return bool(
            self.upi_ids or 
            self.phishing_links or 
            self.suspicious_keywords or
            self.bank_accounts
        )
    
    @property
    def confidence(self) -> int:
        """Get current confidence score."""
        return self._latest_analysis.confidence if self._latest_analysis else 0


class SessionStore:
    """
    In-memory store for session intelligence.
    
    Key behaviors:
    - Stores intelligence per sessionId
    - Clears session when new conversation starts (empty history)
    - Aggregates intelligence across multiple messages
    - Maintains conversation history for analysis
    """
    
    def __init__(self):
        self._store: Dict[str, SessionIntelligence] = {}
        self._classifier = ScamClassifier()
    
    def get_or_create(self, session_id: str) -> SessionIntelligence:
        """Get existing session or create new one."""
        if session_id not in self._store:
            self._store[session_id] = SessionIntelligence(session_id=session_id)
        return self._store[session_id]
    
    def clear_session(self, session_id: str) -> None:
        """Clear a session's intelligence (for new conversation start)."""
        if session_id in self._store:
            del self._store[session_id]
        # Create fresh session
        self._store[session_id] = SessionIntelligence(session_id=session_id)
    
    def add_intelligence(
        self, 
        session_id: str, 
        intel: dict,
        message: Optional[dict] = None
    ) -> SessionIntelligence:
        """
        Add extracted intelligence to a session.
        
        Args:
            session_id: The session identifier
            intel: Dictionary of extracted intelligence
            message: Optional message dict {sender, text, timestamp}
            
        Returns:
            Updated SessionIntelligence object
        """
        session = self.get_or_create(session_id)
        session.merge(intel)
        session.message_count += 1
        
        # Add message to history if provided
        if message:
            session.add_message(
                sender=message.get("sender", "unknown"),
                text=message.get("text", ""),
                timestamp=message.get("timestamp", datetime.now().isoformat())
            )
        
        # Update analysis with classifier
        session.update_analysis(self._classifier)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionIntelligence]:
        """Get session intelligence if it exists."""
        return self._store.get(session_id)
    
    def get_llm_context(self, session_id: str) -> dict:
        """Get formatted LLM context for a session."""
        session = self.get_or_create(session_id)
        return session.to_llm_context()
    
    def get_final_payload(self, session_id: str, agent_notes: str = "") -> dict:
        """
        Get the final payload for GUVI callback.
        
        Args:
            session_id: The session identifier
            agent_notes: Summary of scammer behavior
            
        Returns:
            Dictionary matching the GUVI callback schema
        """
        session = self.get_or_create(session_id)
        
        # Auto-generate agent notes if not provided
        if not agent_notes:
            agent_notes = self._generate_agent_notes(session)
        
        return {
            "sessionId": session_id,
            "scamDetected": session.scam_detected,
            "totalMessagesExchanged": session.message_count,
            "extractedIntelligence": session.to_dict(),
            "agentNotes": agent_notes
        }
    
    def backfill_history(self, session_id: str, history: List[dict], extractor: 'IntelligenceExtractor') -> SessionIntelligence:
        """
        Backfill session intelligence from conversation history.
        Crucial for statelessness (server restarts or scaling).
        
        Args:
            session_id: The session identifier
            history: List of message objects from request
            extractor: Instance of IntelligenceExtractor to process past messages
        """
        session = self.get_or_create(session_id)
        
        # If session already has messages, we might not need to backfill
        # But to be safe (in case of restart), we check if history is longer than current session messages
        if len(history) > len(session.messages):
            # We are likely in a fresh session (or lost state)
            # Process strictly the messages that are NOT in our current session store
            # For simplicity in this hackathon context, we can just re-process everything if count mismatches
            # to ensure we capture all intelligence.
            
            # Clear current partial state to avoid duplicates during re-processing
            self.clear_session(session_id)
            session = self.get_or_create(session_id)
            
            for msg in history:
                text = msg.text
                sender = msg.sender
                timestamp = str(msg.timestamp)
                
                # Extract intel from this past message
                # Note: This might be expensive if history is huge, but typically < 20 messages
                intel = extractor.extract(text)
                
                # Add to session
                self.add_intelligence(session_id, intel, message={
                    "sender": sender,
                    "text": text,
                    "timestamp": timestamp
                })
            
            # Deduce State based on message count if we lost it
            # Simple heuristic:
            # 0-2 messages: INITIAL_CONTACT
            # 3-6 messages: ESTABLISH_TRUST
            # 7+ messages: EXTRACTION_UPI (or whatever comes next)
            # Real state will be refined by the next AgentManager call based on intel gaps
            if session.message_count >= 7:
                 session.agent_state = "EXTRACTION_UPI" # Default to beginning of extraction
            elif session.message_count >= 3:
                 session.agent_state = "ESTABLISH_TRUST"
            
        return session

    def _generate_agent_notes(self, session: SessionIntelligence) -> str:
        """Auto-generate agent notes from session analysis."""
        notes = []
        
        analysis = session._latest_analysis
        if analysis:
            notes.append(f"Scam type: {analysis.scam_type.value}")
            notes.append(f"Confidence: {analysis.confidence}%")
            
            if analysis.impersonating:
                notes.append(f"Impersonating: {analysis.impersonating}")
            
            if analysis.threats:
                notes.append(f"Threats used: {', '.join(analysis.threats[:3])}")
            
            if analysis.asks_for:
                notes.append(f"Asked for: {', '.join(analysis.asks_for[:3])}")
        
        return ". ".join(notes) if notes else "No analysis available"


# Global session store instance
session_store = SessionStore()
