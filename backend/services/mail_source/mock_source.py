import json
import os
from typing import List
from datetime import datetime
from .base import MailSourceInterface, SendResult
from schemas import RawEmail

class MockMailSource(MailSourceInterface):
    def __init__(self, fixtures_path: str):
        self.fixtures_path = fixtures_path

    def fetch_messages(self, mailbox: str, since: datetime) -> List[RawEmail]:
        if not os.path.exists(self.fixtures_path):
            return []
        
        with open(self.fixtures_path, 'r') as f:
            data = json.load(f)
            
        emails = []
        for item in data:
            # In a real app we'd filter by 'since' and 'mailbox' here,
            # but for mock we'll just return everything or parse the date.
            item_date = datetime.fromisoformat(item['receivedDateTime'].replace('Z', '+00:00')).replace(tzinfo=None)
            if since and item_date < since:
                continue
                
            emails.append(RawEmail(
                conversationId=item.get('conversationId'),
                subject=item.get('subject'),
                sender=item.get('sender'),
                toRecipients=item.get('toRecipients'),
                receivedDateTime=item_date,
                body=item.get('body'),
                hasAttachments=item.get('hasAttachments', False),
                attachments=item.get('attachments', [])
            ))
            
        return emails
        
    def send_message(self, mailbox: str, to: List[str], subject: str, body: str, attachments: List[str]) -> SendResult:
        # Simulate sending
        print(f"MOCK SEND: from {mailbox} to {to} | {subject}")
        return SendResult(success=True, message="Mock email sent successfully")
