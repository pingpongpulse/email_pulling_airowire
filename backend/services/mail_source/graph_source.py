import os
import msal
import requests
from typing import List
from datetime import datetime
from .base import MailSourceInterface, SendResult
from schemas import RawEmail
from dotenv import load_dotenv

load_dotenv()

class GraphMailSource(MailSourceInterface):
    def __init__(self):
        self.tenant_id = os.environ.get('AZURE_TENANT_ID')
        self.client_id = os.environ.get('AZURE_CLIENT_ID')
        self.client_secret = os.environ.get('AZURE_CLIENT_SECRET')
        self.authority = f'https://login.microsoftonline.com/{self.tenant_id}'
        self.scopes = ['https://graph.microsoft.com/.default']
        
        # Build MSAL app
        self.app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )

    def _get_access_token(self):
        # The pattern to acquire a token looks up a token in cache first, and gets a new one if needed
        result = self.app.acquire_token_silent(self.scopes, account=None)
        if not result:
            result = self.app.acquire_token_for_client(scopes=self.scopes)
            
        if "access_token" in result:
            return result["access_token"]
        else:
            print(f"Error acquiring token: {result.get('error')} - {result.get('error_description')}")
            return None

    def fetch_messages(self, mailbox: str, since: datetime) -> List[RawEmail]:
        token = self._get_access_token()
        if not token:
            print("Graph API: No access token available. Check credentials.")
            return []

        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }

        # Build Graph query URL (app permissions allow accessing any user's mailbox)
        endpoint = f'https://graph.microsoft.com/v1.0/users/{mailbox}/messages'
        
        # Filter by since date
        if since > datetime.min:
            since_str = since.strftime('%Y-%m-%dT%H:%M:%SZ')
            endpoint += f"?$filter=receivedDateTime ge {since_str}"

        # Fetch messages
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code != 200:
            print(f"Graph API Error: {response.status_code} - {response.text}")
            return []

        data = response.json()
        messages = data.get('value', [])
        
        emails = []
        for msg in messages:
            # Parse recipients
            to_recipients = []
            for recipient in msg.get('toRecipients', []):
                email_address = recipient.get('emailAddress', {}).get('address')
                if email_address:
                    to_recipients.append(email_address)
                    
            sender = msg.get('sender', {}).get('emailAddress', {}).get('address', '')
            
            # Parse body (default to text, or strip HTML if only HTML available)
            body = msg.get('body', {}).get('content', '')

            # Note: attachments requires an additional Graph call per message if hasAttachments is true.
            # Deferred for this phase.
            
            emails.append(RawEmail(
                conversationId=msg.get('conversationId'),
                subject=msg.get('subject', ''),
                sender=sender,
                toRecipients=to_recipients,
                receivedDateTime=datetime.fromisoformat(msg.get('receivedDateTime').replace('Z', '+00:00')).replace(tzinfo=None),
                body=body,
                hasAttachments=msg.get('hasAttachments', False),
                attachments=[] 
            ))
            
        return emails

    def send_message(self, mailbox: str, to: List[str], subject: str, body: str, attachments: List[str]) -> SendResult:
        # Implementation deferred
        return SendResult(success=False, message="Not implemented yet")
