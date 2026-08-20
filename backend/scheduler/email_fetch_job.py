from datetime import datetime, timezone
import os
from services.mail_source.mock_source import MockMailSource
from services.filter_engine import FilterEngine
from services.threading_engine import ThreadingEngine, MockThread
from repositories.email_repo import EmailRepository
from models.database import db
from models.models import Mailbox, KeywordFilter, EmailThread

def fetch_emails_job(app):
    with app.app_context():
        print(f"[{datetime.now()}] Running email fetch job...")
        
        # In a real app we'd fetch active mailboxes
        mailboxes = Mailbox.query.filter_by(is_active=True).all()
        if not mailboxes:
            print("No active mailboxes found. Skipping.")
            return

        keywords = [k.keyword for k in KeywordFilter.query.all()]
        if not keywords:
            # Provide some defaults if empty
            keywords = ['invoice', 'bill', 'receipt']

        source = MockMailSource(os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'mock_emails.json'))

        for mailbox in mailboxes:
            raw_emails = source.fetch_messages(mailbox.email_address, mailbox.last_synced_time)
            if not raw_emails:
                continue
                
            for raw_email in raw_emails:
                if FilterEngine.matches_filters(raw_email, keywords):
                    # Load existing threads for resolution
                    # In a real app we might only load recent threads or query directly
                    db_threads = EmailRepository.get_all_threads()
                    mock_threads = [MockThread(
                        id=t.id,
                        conversation_id=t.conversation_id,
                        subject=t.subject,
                        participant_fingerprint=t.get_fingerprint(),
                        last_activity=t.last_activity
                    ) for t in db_threads]

                    match_result = ThreadingEngine.resolve_thread(raw_email, mock_threads)
                    
                    EmailRepository.save_email(raw_email, match_result)
                    
            # Update mailbox last synced time
            mailbox.last_synced_time = datetime.utcnow()
            db.session.commit()
        
        print(f"[{datetime.now()}] Email fetch job completed.")
