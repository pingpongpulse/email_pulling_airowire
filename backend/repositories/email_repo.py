import json
from models.database import db
from models.models import Email, EmailThread
from schemas import RawEmail, ThreadMatchResult
from services.threading_engine import ThreadingEngine
from datetime import datetime

class EmailRepository:
    @staticmethod
    def get_all_threads():
        return EmailThread.query.order_by(EmailThread.last_activity.desc()).all()

    @staticmethod
    def get_thread_by_id(thread_id):
        return EmailThread.query.get(thread_id)

    @staticmethod
    def save_email(raw_email: RawEmail, match_result: ThreadMatchResult):
        # 1. Get or Create Thread
        if match_result.thread_id:
            thread = EmailThread.query.get(match_result.thread_id)
        else:
            thread = EmailThread(
                conversation_id=raw_email.conversationId,
                subject=raw_email.subject,
                normalized_subject=ThreadingEngine.normalize_subject(raw_email.subject),
                last_activity=raw_email.receivedDateTime
            )
            thread.set_fingerprint(ThreadingEngine.participant_fingerprint([raw_email.sender] + raw_email.toRecipients))
            db.session.add(thread)
            db.session.flush() # Get ID

        # 2. Update Thread Activity & Fingerprint
        if raw_email.receivedDateTime > thread.last_activity:
            thread.last_activity = raw_email.receivedDateTime

        current_fp = thread.get_fingerprint()
        new_fp = ThreadingEngine.participant_fingerprint([raw_email.sender] + raw_email.toRecipients)
        thread.set_fingerprint(current_fp.union(new_fp))

        # 3. Create Email Row
        email_record = Email(
            thread_id=thread.id,
            sender=raw_email.sender,
            to_recipients=json.dumps(raw_email.toRecipients),
            subject=raw_email.subject,
            body=raw_email.body,
            received_date=raw_email.receivedDateTime,
            has_attachments=raw_email.hasAttachments,
            thread_match_confidence=match_result.confidence.value,
            needs_review=match_result.needs_review
        )
        db.session.add(email_record)
        db.session.commit()
        return email_record
