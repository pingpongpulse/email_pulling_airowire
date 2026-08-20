from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class RawEmail(BaseModel):
    conversationId: Optional[str]
    subject: str
    sender: str
    toRecipients: List[str]
    receivedDateTime: datetime
    body: str
    hasAttachments: bool
    attachments: List[str] # Or a more complex type if we need

class ConfidenceEnum(str, Enum):
    EXACT = 'exact'
    FALLBACK_STRONG = 'fallback_strong'
    FALLBACK_WEAK = 'fallback_weak'
    NO_MATCH = 'no_match'

class ThreadMatchResult(BaseModel):
    thread_id: Optional[int] # ID of the existing thread, or None if new
    confidence: ConfidenceEnum
    matched_via: str
    needs_review: bool
