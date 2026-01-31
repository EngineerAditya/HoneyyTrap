"""
Pydantic models for the Honeypot API.
These models exactly match the input/output format specified in the hackathon requirements.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============== INPUT MODELS ==============

class Message(BaseModel):
    """
    Represents a single message in the conversation.
    
    Fields:
        sender: Either "scammer" or "user"
        text: The message content
        timestamp: ISO-8601 formatted timestamp
    """
    sender: str = Field(..., description="Either 'scammer' or 'user'")
    text: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="ISO-8601 format timestamp")


class Metadata(BaseModel):
    """
    Optional metadata about the conversation context.
    
    Fields:
        channel: SMS / WhatsApp / Email / Chat
        language: Language used in conversation
        locale: Country or region code (e.g., "IN")
    """
    channel: Optional[str] = Field(None, description="SMS / WhatsApp / Email / Chat")
    language: Optional[str] = Field(None, description="Language used")
    locale: Optional[str] = Field(None, description="Country or region")


class HoneypotRequest(BaseModel):
    """
    Main request body for the honeypot API.
    
    This is what the GUVI evaluation system will send to our endpoint.
    
    Fields:
        sessionId: Unique identifier for the conversation session
        message: The latest incoming message from the scammer
        conversationHistory: All previous messages in this session (empty for first message)
        metadata: Optional context about the channel/language
    """
    sessionId: str = Field(..., description="Unique session identifier")
    message: Message = Field(..., description="Latest incoming message")
    conversationHistory: List[Message] = Field(
        default=[], 
        description="Previous messages in conversation. Empty for first message."
    )
    metadata: Optional[Metadata] = Field(None, description="Optional conversation metadata")


# ============== OUTPUT MODELS ==============

class HoneypotResponse(BaseModel):
    """
    Response format expected by the evaluation system.
    
    Fields:
        status: "success" or "error"
        reply: The agent's response to continue the conversation
    """
    status: str = Field(..., description="'success' or 'error'")
    reply: str = Field(..., description="Agent's reply to the scammer")


class ErrorResponse(BaseModel):
    """
    Error response for failed requests.
    """
    status: str = Field(default="error")
    detail: str = Field(..., description="Error description")
