import re
from typing import List, Optional, FrozenSet
from datetime import datetime, timedelta
from schemas import RawEmail, ThreadMatchResult, ConfidenceEnum

class MockThread:
    def __init__(self, id: int, conversation_id: str, subject: str, participant_fingerprint: FrozenSet[str], last_activity: datetime):
        self.id = id
        self.conversation_id = conversation_id
        self.subject = subject
        self.participant_fingerprint = participant_fingerprint
        self.last_activity = last_activity

class ThreadingEngine:
    @staticmethod
    def normalize_subject(subject: str) -> str:
        s = subject.strip().lower()
        s = re.sub(r'^(re|fw|fwd)\s*:\s*', '', s)
        s = re.sub(r'^(re|fw|fwd)\s*:\s*', '', s)
        s = re.sub(r'\s+', ' ', s)
        return s.strip()

    @staticmethod
    def participant_fingerprint(addresses: List[str]) -> FrozenSet[str]:
        return frozenset(a.lower().strip() for a in addresses)

    @staticmethod
    def resolve_thread(email: RawEmail, existing_threads: List[MockThread]) -> ThreadMatchResult:
        # Tier 1 - Exact match on Conversation ID
        if email.conversationId:
            for thread in existing_threads:
                if thread.conversation_id == email.conversationId:
                    return ThreadMatchResult(
                        thread_id=thread.id,
                        confidence=ConfidenceEnum.EXACT,
                        matched_via="conversationId",
                        needs_review=False
                    )

        # Tier 2 - Fallback matching
        norm_subj = ThreadingEngine.normalize_subject(email.subject)
        email_participants = ThreadingEngine.participant_fingerprint([email.sender] + email.toRecipients)

        for thread in existing_threads:
            if ThreadingEngine.normalize_subject(thread.subject) == norm_subj:
                # Check participant overlap
                has_overlap = not email_participants.isdisjoint(thread.participant_fingerprint)
                
                # Check time window (e.g. 30 days)
                is_recent = abs((email.receivedDateTime - thread.last_activity).days) <= 30
                
                if has_overlap and is_recent:
                    return ThreadMatchResult(
                        thread_id=thread.id,
                        confidence=ConfidenceEnum.FALLBACK_STRONG,
                        matched_via="subject_participants_time",
                        needs_review=False
                    )
                elif has_overlap and not is_recent:
                    # Weak fallback: good subject & participant, but too old. Create new, but flag.
                    return ThreadMatchResult(
                        thread_id=None,
                        confidence=ConfidenceEnum.FALLBACK_WEAK,
                        matched_via="subject_participants_old",
                        needs_review=True
                    )
                # If no overlap, probably unrelated, continue searching
        
        # No match found
        return ThreadMatchResult(
            thread_id=None,
            confidence=ConfidenceEnum.NO_MATCH,
            matched_via="none",
            needs_review=False
        )
