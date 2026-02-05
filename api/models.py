from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class Message(BaseModel):
    sender: str
    text: str
    timestamp: Optional[Any] = None

class Metadata(BaseModel):
    channel: Optional[Any] = None
    language: Optional[Any] = None
    locale: Optional[Any] = None

class HoneypotRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: Optional[List[Message]] = None
    metadata: Optional[Metadata] = None

class HoneypotResponse(BaseModel):
    status: str
    reply: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
